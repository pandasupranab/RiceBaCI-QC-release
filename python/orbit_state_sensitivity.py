#!/usr/bin/env python3
"""Post-hoc state diagnostic for the pooled baseline orbit tolerance.

The predeclared clause uses the pooled 2017 90th percentile of absolute
between-orbit disagreement.  This diagnostic shows how that permissive pooled
threshold compares with state-specific 2017 thresholds.  State thresholds are
not replacements for the frozen pooled rule: Andhra Pradesh has fewer than the
minimum 30 baseline pairs, so its estimate is explicitly underpowered.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lf_output  # noqa: F401

BASELINE = 2017
Q = 0.90
MIN_BASELINE = 30
MARKERS = ("trough", "heading", "harvest")


def build(pairs, states):
    d = pairs.copy()
    d["state"] = d["district"].map(states)
    if d["state"].isna().any():
        missing = sorted(d.loc[d["state"].isna(), "district"].unique())
        raise ValueError("district(s) lack a state mapping: %s" % missing)
    rows = []
    for marker in MARKERS:
        col = "d_" + marker
        pooled_base = d.loc[d["year"] == BASELINE, col].dropna().abs()
        if len(pooled_base) < MIN_BASELINE:
            raise ValueError("pooled baseline has only %d pairs for %s" %
                             (len(pooled_base), marker))
        pooled_t = float(np.quantile(pooled_base, Q))
        for state in sorted(d["state"].unique()):
            base = d[(d["year"] == BASELINE) & (d["state"] == state)][col]
            base = base.dropna().abs()
            later = d[(d["year"] != BASELINE) & (d["state"] == state)][col]
            later = later.dropna().abs()
            state_t = float(np.quantile(base, Q)) if len(base) else np.nan
            rows.append(dict(
                marker=marker, state=state, baseline_year=BASELINE,
                baseline_pairs=len(base), state_specific_tolerance_d=state_t,
                pooled_tolerance_d=pooled_t, later_pairs=len(later),
                later_share_within_state_t=(float((later <= state_t).mean())
                                            if len(later) and np.isfinite(state_t)
                                            else np.nan),
                later_share_within_pooled_t=(float((later <= pooled_t).mean())
                                             if len(later) else np.nan),
                state_threshold_status=("diagnostic_only_underpowered"
                                        if len(base) < MIN_BASELINE else
                                        "diagnostic_only"),
                interpretation=(
                    "post-hoc diagnostic; pooled criterion tests stability "
                    "relative to a noisy pooled baseline and does not establish "
                    "three-state transferability")))
    return pd.DataFrame(rows)


def selftest():
    rows = []
    for state, scale in (("A", 1.0), ("B", 3.0)):
        for i in range(40):
            rows.append(dict(district=state, year=BASELINE,
                             d_trough=scale * i / 4,
                             d_heading=scale * i / 5,
                             d_harvest=scale * i / 3))
        for i in range(40):
            rows.append(dict(district=state, year=2020,
                             d_trough=scale * i / 4,
                             d_heading=scale * i / 5,
                             d_harvest=scale * i / 3))
    out = build(pd.DataFrame(rows), {"A": "A", "B": "B"})
    ok = (len(out) == 6 and out.state_specific_tolerance_d.notna().all()
          and (out.groupby("marker").pooled_tolerance_d.nunique() == 1).all())
    print("rows %d; expected 3 markers x 2 states = 6" % len(out))
    print("[%s] state and pooled tolerances are calculated separately"
          % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main(argv=None):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", default=os.path.join(
        root, "results", "orbit_agreement", "orbit_pairs.csv"))
    ap.add_argument("--exposure", default=os.path.join(
        root, "docs", "district_cyclone_exposure_ibtracs50km.csv"))
    ap.add_argument("--out", default=os.path.join(
        root, "results", "orbit_agreement"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    pairs = pd.read_csv(a.pairs)
    expo = pd.read_csv(a.exposure)
    states = (expo[["district_gadm_name", "state"]].drop_duplicates()
              .set_index("district_gadm_name")["state"].to_dict())
    out = build(pairs, states)
    os.makedirs(a.out, exist_ok=True)
    dest = os.path.join(a.out, "Table_SX_OrbitStateSensitivity.csv")
    out.to_csv(dest, index=False)
    print(out.to_string(index=False))
    print("wrote %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
