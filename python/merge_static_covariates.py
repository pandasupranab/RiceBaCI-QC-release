"""
merge_static_covariates.py -- join the S1 static covariates onto a panel.

Closes §3.10 item 3a's covariate set: elevation_m, slope_deg and incidence_deg
come from S1_STATIC_COVARIATES.js (25 per-district CSVs, season-invariant), and
this joins them onto a pixel-season or district-season panel on cell_id.

Refuses rather than guesses:
  * a static file missing any declared column is named and the run stops, since
    that is the signature of the Earth Engine header-inference defect;
  * a cell_id present in the panel but absent from the static files is counted
    and reported, and the run stops if the miss rate exceeds --max-miss, because
    a silently partial covariate turns IPSW into a different estimator on a
    different subsample;
  * a cell_id carrying two different coordinates across the static files stops
    the run, because the cohort must be one fixed set of points.

For a district-season panel the static covariates are aggregated to the
district mean over that district's cohort points, which is the right level: the
selection being modelled there is whether a DISTRICT-season admits a fit.

    python python/merge_static_covariates.py \
        --static data/S1_static/ --panel results/phen_panel_sar.csv \
        --out results/phen_panel_sar_with_static.csv

Created 2026-09-12.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
STATIC_COLS = ["elevation_m", "slope_deg", "incidence_deg"]
KEY_COLS = ["district", "cell_id", "lon", "lat"]


def read_static(directory, pattern="S1_STATIC_*.csv"):
    files = sorted(glob.glob(os.path.join(directory, pattern)))
    if not files:
        raise SystemExit(f"no {pattern} under {directory}")
    frames = []
    for f in files:
        df = pd.read_csv(f)
        missing = [c for c in KEY_COLS + STATIC_COLS + ["n_angle_images"]
                   if c not in df.columns]
        if missing:
            raise SystemExit(
                f"{os.path.basename(f)}: columns {missing} absent.\n"
                "This is the Earth Engine header-inference defect -- an "
                "all-null leading block drops those columns from the whole "
                "file. Re-export with the explicit `selectors` list that "
                "S1_STATIC_COVARIATES.js already carries; do not patch here.")
        frames.append(df)
    s = pd.concat(frames, ignore_index=True)
    print(f"static covariates: {len(files)} files, {len(s):,} rows, "
          f"{s['cell_id'].nunique():,} distinct cells, "
          f"{s['district'].nunique()} districts")
    dup = s.groupby("cell_id")[["lon", "lat"]].nunique()
    bad = int((dup > 1).any(axis=1).sum())
    if bad:
        raise SystemExit(f"{bad} cell_ids carry more than one coordinate in the "
                         "static files; the cohort is not one fixed set of "
                         "points")
    s = s.drop_duplicates("cell_id")
    for c in STATIC_COLS:
        v = pd.to_numeric(s[c], errors="coerce")
        print(f"  {c:<14s} non-null {v.notna().mean():.4f}  "
              f"p5 {v.quantile(.05):9.2f}  med {v.median():9.2f}  "
              f"p95 {v.quantile(.95):9.2f}")
        s[c] = v
    n = pd.to_numeric(s["n_angle_images"], errors="coerce")
    print(f"  n_angle_images min {n.min():.0f}  median {n.median():.0f}")
    if n.min() < 30:
        print("  WARNING: some cells' incidence mean rests on fewer than 30 "
              "scenes. Inspect before using it in the score.")
    return s


def main(argv=None):
    ap = argparse.ArgumentParser(description="Join S1 static covariates.")
    ap.add_argument("--static", required=True)
    ap.add_argument("--panel", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-miss", type=float, default=0.02,
                    help="stop if more than this share of panel rows get no "
                         "static covariate (default 0.02)")
    a = ap.parse_args(argv)

    s = read_static(a.static)
    p = pd.read_csv(a.panel)
    if "cell_id" in p.columns and p["cell_id"].nunique() > p["district"].nunique():
        level = "pixel"
        merged = p.merge(s[["cell_id"] + STATIC_COLS], on="cell_id", how="left")
    else:
        level = "district"
        agg = s.groupby("district")[STATIC_COLS].mean().reset_index()
        merged = p.merge(agg, on="district", how="left")
    print(f"panel level: {level}  rows {len(p):,} -> {len(merged):,}")
    if len(merged) != len(p):
        raise SystemExit("the join changed the row count; the static files "
                         "contain duplicate keys")

    miss = merged[STATIC_COLS].isna().any(axis=1)
    print(f"rows with no static covariate: {int(miss.sum()):,} "
          f"({miss.mean():.4f})")
    if miss.mean() > a.max_miss:
        byd = (merged.loc[miss, "district"].value_counts().head(10))
        raise SystemExit(
            f"{miss.mean():.4f} of rows have no static covariate, above the "
            f"{a.max_miss:.4f} ceiling. Worst districts:\n{byd.to_string()}\n"
            "Fix the export before weighting on a covariate this incomplete.")
    merged.to_csv(a.out, index=False)
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
