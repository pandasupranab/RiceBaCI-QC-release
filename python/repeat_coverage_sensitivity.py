#!/usr/bin/env python3
"""Post-hoc repeat-coverage sensitivity for H1/H2 clause (b).

The declared dispersion test admits a pixel with only two retained seasons.
Because retention is non-random, this diagnostic repeats the within/between
calculation for every minimum retained-season threshold from 2 through 9.

The primary sensitivity re-estimates year effects *after* applying each
coverage restriction.  A second, explicitly legacy arm centres first and then
restricts pixels; reporting both prevents a hidden change in centring order.
This sensitivity tests robustness to repeat coverage.  It cannot identify why
the within/between criterion fails and carries no causal interpretation.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lf_output  # noqa: F401
from attrition_diagnostics import load_panel

ROOT = os.environ.get("RICEBACI_ROOT", os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
DEFAULT_PANEL = os.path.join(ROOT, "results", "phen_panel_sar_static.csv")
DEFAULT_OUT = os.path.join(ROOT, "results", "dispersion")
MARKERS = ("trough", "heading", "harvest")


def decompose(d, marker, minimum, center_after_restriction=True):
    d = d.dropna(subset=[marker]).copy()
    if d.empty:
        return None
    counts = d.groupby("cell_id")[marker].size()
    keep = counts[counts >= minimum].index
    if center_after_restriction:
        d = d[d["cell_id"].isin(keep)].copy()
        d["_r"] = d[marker] - d.groupby("year")[marker].transform("mean")
    else:
        d["_r"] = d[marker] - d.groupby("year")[marker].transform("mean")
        d = d[d["cell_id"].isin(keep)].copy()
    if d["cell_id"].nunique() < 3:
        return None
    means = d.groupby("cell_id")["_r"].mean()
    dev = d["_r"] - d["cell_id"].map(means)
    dof = len(d) - len(means)
    if dof <= 0:
        return None
    within = float(np.sqrt(float((dev ** 2).sum()) / dof))
    between = float(means.std(ddof=1))
    if not (np.isfinite(within) and np.isfinite(between)) or between <= 0:
        return None
    return dict(within_var=within ** 2, between_var=between ** 2,
                n_pixels=int(len(means)), n_obs=int(len(d)))


def pooled(panel, marker, minimum, center_after_restriction=True):
    comp = []
    for district in sorted(panel["district"].unique()):
        r = decompose(panel[panel["district"] == district], marker, minimum,
                      center_after_restriction)
        if r is not None:
            comp.append(r)
    if not comp:
        return None
    weights = np.array([r["n_pixels"] for r in comp], float)
    within = float(np.sqrt(np.average(
        [r["within_var"] for r in comp], weights=weights)))
    between = float(np.sqrt(np.average(
        [r["between_var"] for r in comp], weights=weights)))
    return dict(within_sd=within, between_sd=between, ratio=within / between,
                n_districts=len(comp), n_pixels=int(weights.sum()),
                n_obs=sum(r["n_obs"] for r in comp))


def build(panel):
    rows = []
    for order, after in (("center_after_restriction", True),
                         ("legacy_center_before_restriction", False)):
        for minimum in range(2, 10):
            for marker in MARKERS:
                r = pooled(panel, marker, minimum, after)
                row = dict(centering_order=order,
                           minimum_retained_seasons=minimum, marker=marker,
                           status="estimated" if r else "not_estimable",
                           interpretation=(
                               "post-hoc repeat-coverage robustness; does not "
                               "identify why the criterion fails"))
                if r:
                    row.update(r)
                rows.append(row)
    return pd.DataFrame(rows)


def selftest():
    rng = np.random.default_rng(20260916)
    rows = []
    for district in ("A", "B", "C"):
        for pixel in range(12):
            n = 9 if pixel < 6 else 3
            for year in range(2017, 2017 + n):
                rows.append(dict(district=district, cell_id=f"{district}_{pixel}",
                                 year=year, retained=1,
                                 trough=200 + pixel + rng.normal(0, 2),
                                 heading=250 + pixel + rng.normal(0, 2),
                                 harvest=300 + pixel + rng.normal(0, 2)))
    d = pd.DataFrame(rows)
    out = build(d)
    expected = 2 * 8 * 3
    strict = out[(out.centering_order == "center_after_restriction") &
                 (out.minimum_retained_seasons == 9)]
    ok = (len(out) == expected and len(strict) == 3 and
          set(strict.n_pixels.astype(int)) == {18} and
          set(out.minimum_retained_seasons.astype(int)) == set(range(2, 10)))
    print("repeat-coverage rows %d (expected %d)" % (len(out), expected))
    print("strict threshold pixels %s" % sorted(set(strict.n_pixels.astype(int))))
    print("[%s] all thresholds, markers and both centring orders are present"
          % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", default=DEFAULT_PANEL)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    panel = load_panel(a.panel, "pixel", verbose=False)
    panel = panel[panel["retained"].astype(int) == 1].copy()
    out = build(panel)
    os.makedirs(a.out, exist_ok=True)
    dest = os.path.join(a.out, "Table_SX_RepeatCoverageSensitivity.csv")
    out.to_csv(dest, index=False)
    print(out[out["centering_order"] == "center_after_restriction"].to_string(
        index=False))
    print("wrote %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
