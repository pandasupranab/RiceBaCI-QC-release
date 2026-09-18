#!/usr/bin/env python3
"""Fail-closed checker for Paper 2's analysis and figure environments."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.metadata
import io
import json
import os
import platform
import sys


def observed_environment(profile):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec_path = os.path.join(root, "environments", profile + ".json")
    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    packages = {}
    for name in spec["packages"]:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    obs = {
        "profile": profile,
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "packages": packages,
    }
    if profile == "analysis":
        import numpy as np
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            np.show_config()
        config = stream.getvalue().replace("\r\n", "\n")
        obs["blas"] = {
            "policy": "record",
            "show_config_sha256": hashlib.sha256(config.encode()).hexdigest(),
            "show_config": config,
        }
    if profile == "figures":
        import matplotlib.ft2font as ft2font
        from PIL import features
        obs["native"] = {
            "freetype": ft2font.__freetype_version__,
            "zlib": features.version("zlib"),
        }
    return spec, obs


def compare(spec, obs):
    problems = []
    if obs.get("python") != spec.get("python"):
        problems.append("python: expected %s, observed %s" %
                        (spec.get("python"), obs.get("python")))
    if obs.get("implementation") != "CPython":
        problems.append("implementation: expected CPython, observed %s" %
                        obs.get("implementation"))
    for name, expected in spec.get("packages", {}).items():
        actual = obs.get("packages", {}).get(name)
        if actual != expected:
            problems.append("package %s: expected %s, observed %s" %
                            (name, expected, actual))
    for name, expected in spec.get("native", {}).items():
        actual = obs.get("native", {}).get(name)
        if actual != expected:
            problems.append("native %s: expected %s, observed %s" %
                            (name, expected, actual))
    return problems


def selftest():
    spec = {"python": "3.11.15", "packages": {"numpy": "2.4.4"},
            "native": {"zlib": "1.3"}}
    good = {"python": "3.11.15", "implementation": "CPython",
            "packages": {"numpy": "2.4.4"}, "native": {"zlib": "1.3"}}
    ok = not compare(spec, good)
    bad = json.loads(json.dumps(good))
    bad["packages"]["numpy"] = "0"
    bad["native"]["zlib"] = "0"
    bad["python"] = "0"
    problems = compare(spec, bad)
    ok &= len(problems) == 3
    print("[%s] exact matching environment passes" % ("PASS" if not compare(spec, good) else "FAIL"))
    print("[%s] Python, package and native-library drift all fail" %
          ("PASS" if len(problems) == 3 else "FAIL"))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", choices=("analysis", "figures"))
    ap.add_argument("--receipt")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.profile:
        ap.error("--profile is required unless --selftest is used")
    spec, obs = observed_environment(args.profile)
    problems = compare(spec, obs)
    obs["status"] = "PASS" if not problems else "FAIL"
    obs["problems"] = problems
    if args.receipt:
        with open(args.receipt, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obs, fh, indent=2, sort_keys=True)
            fh.write("\n")
    for problem in problems:
        print("[FAIL] " + problem)
    print("environment %s: %s" % (args.profile, obs["status"]))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
