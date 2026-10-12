"""test_validate_release_src.py -- packaging tests for the fail-closed source check (Codex, 11 Oct 2026, item 5).

Everything happens in a disposable temporary copy; the extension's own
release_src/ is only read, and its 59 files are hashed before and after the
whole run to prove it. For every failure case the disposable copy is hashed
before and after validation to prove the validator modified nothing, and it is
checked that no report file appeared. The documented entry points are
exercised exactly as README.md gives them (python -I -B ... --validate-sources-only).

Run:  venv/bin/python -I -B scripts/test_validate_release_src.py
Writes preflight/REPLAY_VALIDATION_TESTS.json; the transcript is printed (tee it to logs/).
Exit 0 only if every case behaved as required.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import validate_release_src as VRS  # noqa: E402

PY = sys.executable
REAL_SRC = os.path.join(EXT, "release_src")
STAGED = os.path.join(EXT, "inputs", "staged")
RESULTS = []


def tree_hashes(root):
    out = {}
    if not os.path.isdir(root):
        return out
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, root).replace(os.sep, "/")
            if os.path.islink(p):
                out[rel] = "symlink:" + os.readlink(p)
            else:
                out[rel] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    return out


def record(case, required, observed, ok, detail=""):
    RESULTS.append(dict(case=case, required=required, observed=observed, ok=bool(ok), detail=detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {case}: required {required}; observed {observed}" + (f"  -- {detail}" if detail else ""))


def make_ext_copy(tmp, name):
    """A disposable extension root with scripts/, inputs/staged/*.txt and a fresh release_src copy."""
    root = os.path.join(tmp, name)
    os.makedirs(os.path.join(root, "inputs", "staged"))
    os.makedirs(os.path.join(root, "preflight"))
    shutil.copytree(os.path.join(EXT, "scripts"), os.path.join(root, "scripts"))
    for f in ("release_src_expected_blobs.txt", "git_ls_tree_v1.0.0.txt"):
        shutil.copy2(os.path.join(STAGED, f), os.path.join(root, "inputs", "staged", f))
    shutil.copytree(REAL_SRC, os.path.join(root, "release_src"))
    return root


def run_cli(root, args):
    env = dict(os.environ)
    p = subprocess.run([PY, "-I", "-B"] + args, cwd=root, capture_output=True, text=True, env=env)
    return p.returncode, (p.stdout + p.stderr).strip()


def run_case(case, root, sabotage, want_exit, want_substr, entry="validate"):
    """sabotage(root) alters the disposable copy; then validation must give want_exit and leave it untouched."""
    src = os.path.join(root, "release_src")
    sabotage(root)
    before = tree_hashes(src)
    reports_before = set(os.listdir(os.path.join(root, "preflight")))
    if entry == "validate":
        code, out = run_cli(root, [os.path.join(root, "scripts", "validate_release_src.py")])
    else:
        code, out = run_cli(root, [os.path.join(root, "scripts", "preflight.py"), "--validate-sources-only"])
    after = tree_hashes(src)
    reports_after = set(os.listdir(os.path.join(root, "preflight")))
    untouched = before == after
    no_report = reports_before == reports_after
    msg_ok = want_substr in out
    ok = code == want_exit and untouched and no_report and msg_ok
    lines = [ln for ln in out.splitlines() if "release_src" in ln] or out.splitlines() or [""]
    last = lines[-1].strip()
    record(f"{case} [{entry}]", f"exit {want_exit}, message contains '{want_substr}', copy untouched, no report",
           f"exit {code}, message {'found' if msg_ok else 'ABSENT'}, copy {'untouched' if untouched else 'CHANGED'}, "
           f"report {'none' if no_report else 'WRITTEN'}", ok, last[:200])
    return ok


def main():
    t0 = time.time()
    print("=" * 74)
    print("REPLAY VALIDATION TESTS -- fail-closed release_src check in a disposable copy")
    print(f"python {sys.version.split()[0]}  extension root {EXT}")
    print("=" * 74)
    real_before = tree_hashes(REAL_SRC)
    record("real release_src/ has 59 files before the tests", 59, len(real_before), len(real_before) == 59)

    # 0. the documented path on the shipped tree itself (validation only)
    code, out = run_cli(EXT, [os.path.join(EXT, "scripts", "validate_release_src.py")])
    record("documented path: scripts/validate_release_src.py on the shipped release_src/", "exit 0", f"exit {code}", code == 0, out.splitlines()[-1][:200])
    code, out = run_cli(EXT, [os.path.join(EXT, "scripts", "preflight.py"), "--validate-sources-only"])
    record("documented path: scripts/preflight.py --validate-sources-only on the shipped release_src/", "exit 0", f"exit {code}", code == 0, out.splitlines()[-1][:200])

    tmp = tempfile.mkdtemp(prefix="ext_rev2_validation_tests_")
    try:
        for entry in ("validate", "preflight"):
            root = make_ext_copy(tmp, f"intact_{entry}")
            run_case("intact disposable copy", root, lambda r: None, 0, "release_src valid", entry)

            root = make_ext_copy(tmp, f"absent_{entry}")
            run_case("absent release_src/", root, lambda r: shutil.rmtree(os.path.join(r, "release_src")),
                     2, "absent or not a directory", entry)

            root = make_ext_copy(tmp, f"empty_{entry}")
            def _empty(r):
                shutil.rmtree(os.path.join(r, "release_src")); os.makedirs(os.path.join(r, "release_src"))
            run_case("empty release_src/", root, _empty, 2, "release_src is empty", entry)

            root = make_ext_copy(tmp, f"missing_{entry}")
            run_case("missing file (python/orbit_agreement.py removed)", root,
                     lambda r: os.remove(os.path.join(r, "release_src", "python", "orbit_agreement.py")),
                     2, "python/orbit_agreement.py: missing file", entry)

            root = make_ext_copy(tmp, f"extra_{entry}")
            def _extra(r):
                with open(os.path.join(r, "release_src", "python", "json.py"), "w") as fh:
                    fh.write("# planted module\n")
            run_case("extra file (python/json.py planted)", root, _extra, 2, "python/json.py: unexpected file", entry)

            root = make_ext_copy(tmp, f"changed_{entry}")
            def _changed(r):
                p = os.path.join(r, "release_src", "python", "extract_phenometrics_sar.py")
                with open(p, "ab") as fh:
                    fh.write(b"\n# one appended line\n")
            run_case("changed blob (one line appended to extract_phenometrics_sar.py)", root, _changed,
                     2, "python/extract_phenometrics_sar.py: blob SHA-1", entry)

            root = make_ext_copy(tmp, f"crlf_{entry}")
            def _crlf(r):
                p = os.path.join(r, "release_src", "python", "fit_phenometrics.py")
                data = open(p, "rb").read().replace(b"\n", b"\r\n")
                open(p, "wb").write(data)
            run_case("CRLF line endings (fit_phenometrics.py re-encoded)", root, _crlf, 2, "CRLF", entry)

            root = make_ext_copy(tmp, f"symlink_{entry}")
            def _link(r):
                os.symlink("orbit_agreement.py", os.path.join(r, "release_src", "python", "oa_link.py"))
            run_case("unexpected symbolic link inside release_src/", root, _link, 2, "unexpected symbolic link", entry)

            root = make_ext_copy(tmp, f"pycache_{entry}")
            def _pyc(r):
                d = os.path.join(r, "release_src", "python", "__pycache__"); os.makedirs(d)
                with open(os.path.join(d, "orbit_agreement.cpython-313.pyc"), "wb") as fh:
                    fh.write(b"\x00" * 16)
            run_case("interpreter bytecode cache inside release_src/python/", root, _pyc, 2, "bytecode cache present", entry)

            root = make_ext_copy(tmp, f"noexp_{entry}")
            run_case("expectation list missing (inputs/staged/release_src_expected_blobs.txt removed)", root,
                     lambda r: os.remove(os.path.join(r, "inputs", "staged", "release_src_expected_blobs.txt")),
                     3, "NOT PERFORMED" if entry == "validate" else "not performed", entry)

        # API-level: a tampered expectation list must be rejected (anchoring to the tree record)
        root = make_ext_copy(tmp, "tampered_expectation")
        p = os.path.join(root, "inputs", "staged", "release_src_expected_blobs.txt")
        lines = open(p, encoding="utf-8").read().splitlines()
        lines[-1] = "0000000000000000000000000000000000000000\t" + lines[-1].split("\t", 1)[1]
        open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
        try:
            VRS.validate(os.path.join(root, "release_src"), p, os.path.join(root, "inputs", "staged", "git_ls_tree_v1.0.0.txt"))
            record("tampered expectation list (blob differs from tree record)", "ExpectationError", "no error", False)
        except VRS.ExpectationError as e:
            record("tampered expectation list (blob differs from tree record)", "ExpectationError", "ExpectationError", True, str(e)[:120])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    real_after = tree_hashes(REAL_SRC)
    record("real release_src/ byte-identical after the tests", "identical", "identical" if real_after == real_before else "CHANGED",
           real_after == real_before)
    ok = all(r["ok"] for r in RESULTS)
    rec = dict(utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), python=sys.version.split()[0],
               seconds=round(time.time() - t0, 1), cases=RESULTS, all_passed=ok)
    out = os.path.join(EXT, "preflight", "REPLAY_VALIDATION_TESTS.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rec, fh, indent=1)
    print("=" * 74)
    print(f"REPLAY VALIDATION TESTS {'PASSED' if ok else 'FAILED'}: {sum(r['ok'] for r in RESULTS)} of {len(RESULTS)} cases; "
          f"{rec['seconds']} s; record {os.path.relpath(out, EXT)}")
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
