"""validate_release_src.py -- fail-closed, in-place validation of release_src/ (stdlib only).

The extension imports the released code from release_src/, a copy of 59 files
of pandasupranab/RiceBaCI-QC-release tag v1.0.0 (commit
a465400e7eb7ec05f7c7d819ab14303cc14146d9). This module checks that copy IN
PLACE against the recorded expectation and never writes, removes, copies or
chmods anything. It replaces the 2026-10-10 preflight block that read a
duplicate staging directory (inputs/release_zip/), accepted an empty directory
and then replaced release_src/ (Codex extension review, 11 Oct 2026, required
correction 1).

Expectation (both files are delivered in inputs/staged/):
  release_src_expected_blobs.txt   the exact 59 intended paths with their git blob SHA-1
  git_ls_tree_v1.0.0.txt           the full v1.0.0 tree (255 entries); every expected
                                   entry must appear in it with the same blob SHA-1

Validation fails -- and the caller must stop before any released module is
imported or any scientific computation starts -- when release_src/ is absent,
is not a directory, is empty, lacks an expected file, holds any file or
symbolic link that is not expected, or holds a file whose git blob SHA-1
differs from the recorded one, or contains an interpreter bytecode cache
(__pycache__; run the extension with python -I -B). Byte-exact match is required: a file whose only
difference is CRLF line endings is reported as such and still fails (use the
LF bytes of the released tree, e.g. from the GitHub v1.0.0 source archive or
the Zenodo deposit). Nothing is modified on success or failure.

Validation-only entry point (exit 0 = valid, 2 = invalid, 3 = expectation files unusable):

    venv/bin/python -I -B scripts/validate_release_src.py
    venv/bin/python -I -B scripts/validate_release_src.py --release-src PATH --expected PATH --ls-tree PATH --json OUT
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.dirname(HERE)
DEFAULT_RELEASE_SRC = os.path.join(EXT, "release_src")
DEFAULT_EXPECTED = os.path.join(EXT, "inputs", "staged", "release_src_expected_blobs.txt")
DEFAULT_LS_TREE = os.path.join(EXT, "inputs", "staged", "git_ls_tree_v1.0.0.txt")
EXPECTED_COUNT = 59
RELEASE_COMMIT = "a465400e7eb7ec05f7c7d819ab14303cc14146d9"


class ExpectationError(Exception):
    """The expectation files themselves are missing or inconsistent (exit 3)."""


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def read_expected(expected_path: str, ls_tree_path: str) -> dict:
    """Return {path: blob_sha1} for the intended release_src content, anchored to the tree."""
    if not os.path.isfile(expected_path):
        raise ExpectationError(f"expected-blob list missing: {expected_path}")
    if not os.path.isfile(ls_tree_path):
        raise ExpectationError(f"git ls-tree record missing: {ls_tree_path}")
    tree = {}
    with open(ls_tree_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            meta, path = line.split("\t", 1)
            mode, kind, sha = meta.split()
            tree[path] = (kind, sha)
    expected = {}
    with open(expected_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            sha, path = line.split("\t", 1)
            if path in expected:
                raise ExpectationError(f"duplicate expected path: {path}")
            if path not in tree:
                raise ExpectationError(f"expected path not in the v1.0.0 tree record: {path}")
            if tree[path] != ("blob", sha):
                raise ExpectationError(f"expected blob differs from the v1.0.0 tree record: {path}")
            expected[path] = sha
    if len(expected) != EXPECTED_COUNT:
        raise ExpectationError(f"expected-blob list has {len(expected)} entries, not {EXPECTED_COUNT}")
    return expected


def validate(release_src: str = DEFAULT_RELEASE_SRC, expected_path: str = DEFAULT_EXPECTED,
             ls_tree_path: str = DEFAULT_LS_TREE) -> dict:
    """Validate release_src in place. Returns a result dict; never raises for content problems.

    result["ok"] is True only when the set of files equals the expected set exactly and every
    blob SHA-1 matches. result["problems"] lists (path, reason) for every finding.
    """
    expected = read_expected(expected_path, ls_tree_path)
    res = dict(release_src=os.path.abspath(release_src), release_commit=RELEASE_COMMIT,
               expected_count=len(expected), present_count=0, matched=0, problems=[],
               files={}, action="validation only: nothing copied, removed or modified")
    problems = res["problems"]
    if os.path.islink(release_src) or not os.path.isdir(release_src):
        problems.append((".", "release_src is absent or not a directory"))
        res["ok"] = False
        return res
    found = {}
    for dp, dn, fn in os.walk(release_src, followlinks=False):
        for d in list(dn):
            p = os.path.join(dp, d)
            rel_d = os.path.relpath(p, release_src).replace(os.sep, "/")
            if os.path.islink(p):
                problems.append((rel_d, "unexpected symbolic link"))
            elif d == "__pycache__":
                # bytecode written by an interpreter run without -B; not part of the released tree
                problems.append((rel_d, "interpreter bytecode cache present; remove this directory and run the "
                                        "extension with 'python -I -B' so that none is written"))
                dn.remove(d)
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, release_src).replace(os.sep, "/")
            if os.path.islink(p):
                problems.append((rel, "unexpected symbolic link"))
                continue
            found[rel] = p
    res["present_count"] = len(found)
    if not found and not problems:
        problems.append((".", "release_src is empty"))
    for rel in sorted(found):
        if rel not in expected:
            problems.append((rel, "unexpected file (not in the recorded release_src set)"))
    for rel in sorted(expected):
        if rel not in found:
            problems.append((rel, "missing file"))
            continue
        with open(found[rel], "rb") as fh:
            data = fh.read()
        sha = git_blob_sha1(data)
        if sha == expected[rel]:
            res["matched"] += 1
            res["files"][rel] = sha
        elif git_blob_sha1(data.replace(b"\r\n", b"\n")) == expected[rel]:
            problems.append((rel, "blob differs only by CRLF line endings; byte-exact LF release bytes are required"))
        else:
            problems.append((rel, f"blob SHA-1 {sha} differs from recorded {expected[rel]}"))
    res["ok"] = (not problems and res["matched"] == len(expected) == len(found))
    return res


def summary_line(res: dict) -> str:
    if res["ok"]:
        return (f"release_src valid: {res['matched']} of {res['expected_count']} expected files present, "
                f"byte-exact v1.0.0 blobs, no extra files; nothing modified")
    pr = res["problems"]
    shown = "; ".join(f"{p}: {r}" for p, r in pr[:5]) + (f"; ... {len(pr) - 5} more" if len(pr) > 5 else "")
    return (f"release_src INVALID ({len(pr)} problem(s); {res['present_count']} files present, "
            f"{res['matched']} matched of {res['expected_count']} expected): {shown}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--release-src", default=DEFAULT_RELEASE_SRC)
    ap.add_argument("--expected", default=DEFAULT_EXPECTED)
    ap.add_argument("--ls-tree", default=DEFAULT_LS_TREE)
    ap.add_argument("--json", default=None, help="write the result record to this path (outside release_src)")
    a = ap.parse_args(argv)
    try:
        res = validate(a.release_src, a.expected, a.ls_tree)
    except ExpectationError as e:
        print(f"release_src validation NOT PERFORMED: {e}")
        return 3
    print(summary_line(res))
    if a.json:
        if os.path.abspath(a.json).startswith(os.path.abspath(a.release_src) + os.sep):
            print("refusing to write the JSON record inside release_src")
            return 3
        with open(a.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(res, fh, indent=1)
    return 0 if res["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
