#!/usr/bin/env python3
"""Force LF line endings on every file this project writes. Import me first.

WHY THIS MODULE EXISTS (2026-09-14). Every md5 in every handoff, every
`--verify` in `make_figures.py`, and every reproducibility claim in
`DATA_AVAILABILITY.md` and `docs/verify_masked_panels.md` assumes that
regenerating a committed table gives back the same BYTES. That assumption was
platform-dependent and nobody had noticed, because every run had been on Linux.

`pandas.DataFrame.to_csv(path)` defaults `lineterminator` to **os.linesep**. On
Windows that is CRLF. An external auditor regenerated the three per-unit tables
on Windows and got the same parsed values with **CRLF**: each file 226 bytes
larger (225 rows + header), a different md5, and after normalising line endings
byte-identical. So "byte-identical" was true of Linux and false of Windows, and
**every `to_csv` call in the package** carried the defect, not just the three
tables that happened to be tested. (An earlier draft of this docstring said "65 calls across
22 modules". That count was taken from the author's working copy, which is missing one tracked
module -- `build_coastal_districts.py` -- so it was low, and an external auditor found the gap
by running the gate in the real repository. NEVER HARDCODE THE COUNT: `scan()` derives it from
the directory and the self-test prints it.) Several `json.dump` writes had the same
problem through `open(path, "w")` without a newline argument -- including
`figures/figure_provenance.json`, the file the entire figure-verification story
rests on.

WHAT IT DOES. Importing this module sets the default `lineterminator="\\n"` on
`DataFrame.to_csv` and `Series.to_csv`, so a call site cannot get it wrong by
omission. `open_lf()` is the equivalent for text writes.

WHY A GUARD AND NOT 65 EDITS. Editing 65 call sites fixes today and guarantees
nothing about the next one. `selftest()` below **scans the source of every
sibling module** and fails if a file that calls `.to_csv(` does not import this
one, or if a committed-JSON writer opens its file without pinning the newline.
That is the same discipline the rest of this repository uses: the gate is tested
by making it fail.
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import re
import sys
import tempfile

import pandas as pd

LF = "\n"
_PATCHED = False


def install():
    """Make LF the default line terminator for pandas CSV output. Idempotent."""
    global _PATCHED
    if _PATCHED:
        return
    for cls in (pd.DataFrame, pd.Series):
        orig = cls.to_csv

        def _to_csv(self, *args, _orig=orig, **kw):
            kw.setdefault("lineterminator", LF)
            return _orig(self, *args, **kw)

        _to_csv.__doc__ = orig.__doc__
        _to_csv._lf_wrapped = True
        cls.to_csv = _to_csv
    _PATCHED = True


def open_lf(path, mode="w", **kw):
    """`open` for text writes, with the newline pinned to LF on every platform.

    Python translates "\\n" to os.linesep on write unless `newline` is given, so
    a committed JSON or markdown file written through a bare `open(path, "w")`
    is CRLF on Windows and LF on Linux. Same file, two hashes.
    """
    kw.setdefault("encoding", "utf-8")
    kw.setdefault("newline", LF)
    return io.open(path, mode, **kw)


install()

# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------
# Modules exempt from the to_csv rule: this one, and the two 2026-09-07 one-off
# patch scripts that write no tables and are kept only as history.
_EXEMPT = {"lf_output.py", "apply_round2.py", "apply_round3.py"}
# Files whose json.dump output is committed, so its newline must be pinned.
_JSON_WRITERS = {"make_figures.py", "attrition_diagnostics.py",
                 "orbit_agreement.py", "permutation_test.py"}


def _sources(here=None):
    here = here or os.path.dirname(os.path.abspath(__file__))
    return {os.path.basename(p): io.open(p, encoding="utf-8").read()
            for p in sorted(glob.glob(os.path.join(here, "*.py")))}


def scan(sources):
    """Return (to_csv_offenders, json_offenders). Empty lists mean the gate passes."""
    csv_bad, json_bad = [], []
    for name, src in sorted(sources.items()):
        if name in _EXEMPT:
            continue
        if ".to_csv(" in src and not re.search(r"^\s*import lf_output", src, re.M):
            csv_bad.append(name)
    for name in sorted(_JSON_WRITERS & set(sources)):
        src = sources[name]
        for m in re.finditer(r"open\(([^)]*?)\)", src):
            args = m.group(1)
            if '"w"' not in args and "'w'" not in args:
                continue
            if "newline" in args:
                continue
            # a json.dump / .write() just after the open(), or -- the inline form
            # `json.dump(obj, open(path, "w"))` -- just before it
            tail = src[m.end():m.end() + 200]
            head = src[max(0, m.start() - 80):m.start()]
            if ("json.dump" in tail or ".write(" in tail
                    or "json.dump" in args or "json.dump" in head):
                json_bad.append(f"{name}: open({args.strip()[:60]})")
    return csv_bad, json_bad


def selftest():
    ok = True
    failures = []

    def chk(cond, msg):
        nonlocal ok
        ok = ok and bool(cond)
        if not cond:
            failures.append(msg)
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")

    print("=" * 74)
    print("SELF-TEST -- lf_output.py")
    print("=" * 74)

    chk(getattr(pd.DataFrame.to_csv, "_lf_wrapped", False)
        and getattr(pd.Series.to_csv, "_lf_wrapped", False),
        "install() wrapped to_csv on DataFrame and Series")

    # the behaviour itself: a written CSV must contain no CR, whatever the OS
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "t.csv")
        pd.DataFrame({"a": [1, 2], "b": ["x", "y"]}).to_csv(p, index=False)
        raw = open(p, "rb").read()
        chk(b"\r" not in raw and raw.count(b"\n") == 3,
            f"a written CSV holds no CR and 3 LF ({len(raw)} bytes) -- this is the "
            f"check that fails on Windows without this module")

        # an explicit lineterminator at the call site still wins
        p2 = os.path.join(td, "t2.csv")
        pd.DataFrame({"a": [1]}).to_csv(p2, index=False, lineterminator="\r\n")
        chk(b"\r\n" in open(p2, "rb").read(),
            "an explicit lineterminator at the call site is not overridden")

        p3 = os.path.join(td, "t3.txt")
        with open_lf(p3) as fh:
            fh.write("one\ntwo\n")
        chk(b"\r" not in open(p3, "rb").read(),
            "open_lf() writes LF for text output too (the committed-JSON path)")

    # the gate, against the real sources
    src = _sources()
    csv_bad, json_bad = scan(src)
    n_csv = sum(1 for k, v in src.items() if ".to_csv(" in v and k not in _EXEMPT)
    chk(not csv_bad,
        f"all {n_csv} modules that call to_csv import lf_output"
        + (f" -- MISSING: {csv_bad}" if csv_bad else ""))
    chk(not json_bad,
        "every committed-JSON writer pins its newline"
        + (f" -- UNPINNED: {json_bad}" if json_bad else ""))

    # the gate must FAIL when sabotaged, or it is not a gate
    sab = dict(src)
    sab["fake_module.py"] = "import pandas as pd\npd.DataFrame().to_csv('x.csv')\n"
    c2, _ = scan(sab)
    chk(c2 == ["fake_module.py"],
        "SABOTAGE: a new module calling to_csv without importing lf_output is "
        f"caught ({c2})")
    sab2 = dict(src)
    sab2["make_figures.py"] = 'import json\nwith open(p, "w") as fh:\n    json.dump(d, fh)\n'
    _, j2 = scan(sab2)
    chk(len(j2) == 1,
        f"SABOTAGE: an unpinned json.dump target is caught ({len(j2)} found)")

    print("=" * 74)
    if failures:
        # Restated at the very end on purpose: a runner that prints only the tail of
        # a failing self-test must still show WHAT failed.
        print(f"SELF-TEST FAILED -- {len(failures)} check(s):")
        for m in failures:
            print(f"  FAILED: {m}")
    else:
        print("SELF-TEST PASSED")
    print("=" * 74)
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--scan", action="store_true",
                    help="report offenders and exit non-zero if any")
    a = ap.parse_args(argv)
    if a.scan:
        c, j = scan(_sources())
        for x in c:
            print(f"to_csv without lf_output: {x}")
        for x in j:
            print(f"unpinned newline: {x}")
        print("clean" if not (c or j) else f"{len(c) + len(j)} offender(s)")
        return 1 if (c or j) else 0
    return selftest() if a.selftest else selftest()


if __name__ == "__main__":
    sys.exit(main())
