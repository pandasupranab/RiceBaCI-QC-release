#!/usr/bin/env python3
"""Post-hoc sensitivity of H1/H2 clause (a) to the orbit-pair rule.

The declared analysis chooses one retained pair per pixel-season without looking
at breakpoint agreement: prefer ASC/DESC, then maximise total valid dekads. This
module asks whether the pooled agreement verdict depends on that choice. It also
reports (1) a marker-blind lowest-orbit rule and (2) every retained pair, weighted
so each pixel-season contributes total weight one. Each rule fixes its own
tolerance on 2017 and applies it to 2018-2025; the declared tolerance is also
applied to every rule for a common-scale comparison.

This is post-hoc robustness evidence. It cannot establish accuracy or statistical
independence between orbit errors.
"""
from __future__ import annotations

import argparse
import itertools
import os
import sys
import tempfile

import numpy as np
import pandas as pd

import lf_output
lf_output.install()
from orbit_agreement import build_pairs, choose_pair, BASELINE_SEASON, TOL_QUANTILE

MARKERS = ("trough", "heading", "harvest")


def _pair_row(key, a, b, weight=1.0):
    dist, year, cell = key
    row = dict(district=dist, year=int(year), cell_id=cell,
               orbit_a=int(a.orbit), orbit_b=int(b.orbit), weight=float(weight))
    for marker in MARKERS:
        row["d_" + marker] = float(b[marker] - a[marker])
    return row


def lowest_pair(g):
    """Marker-blind alternative: lowest orbit numbers, preferring ASC/DESC."""
    g = g[g.retained == 1].sort_values("orbit")
    if len(g) < 2:
        return None
    asc = g[g.orbit_pass.astype(str).str.startswith("ASC")]
    desc = g[g.orbit_pass.astype(str).str.startswith("DESC")]
    if len(asc) and len(desc):
        return asc.iloc[0], desc.iloc[0]
    return g.iloc[0], g.iloc[1]


def build_rule_pairs(fits, rule):
    rows = []
    for key, group in fits.groupby(["district", "year", "cell_id"], sort=False):
        kept = group[group.retained == 1].sort_values("orbit")
        if len(kept) < 2:
            continue
        if rule == "declared_best_coverage":
            pair = choose_pair(group)
            if pair is None:
                continue
            rows.append(_pair_row(key, pair[0], pair[1]))
        elif rule == "lowest_orbit_marker_blind":
            pair = lowest_pair(group)
            rows.append(_pair_row(key, pair[0], pair[1]))
        elif rule == "all_pairs_unit_weighted":
            combos = list(itertools.combinations(range(len(kept)), 2))
            weight = 1.0 / len(combos)
            for i, j in combos:
                rows.append(_pair_row(key, kept.iloc[i], kept.iloc[j], weight))
        else:
            raise ValueError("unknown rule %r" % rule)
    return pd.DataFrame(rows)


def weighted_quantile(values, weights, q):
    values = np.asarray(values, float)
    weights = np.asarray(weights, float)
    ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values, weights = values[ok], weights[ok]
    if not len(values):
        return np.nan
    order = np.argsort(values, kind="mergesort")
    values, weights = values[order], weights[order]
    # Reproduce the protocol's ordinary linear percentile exactly whenever each
    # row has equal weight. This is the declared and lowest-orbit case. For the
    # all-pairs rule, midpoint weighted interpolation gives every pixel-season
    # total mass one rather than letting pixels with more orbit pairs dominate.
    if np.allclose(weights, weights[0], rtol=0, atol=0):
        return float(np.quantile(values, q, method="linear"))
    cdf = (np.cumsum(weights) - 0.5 * weights) / weights.sum()
    return float(np.interp(q, cdf, values, left=values[0], right=values[-1]))


def weighted_sd(values, weights):
    """Unbiased weighted SD; each pixel-season has total weight one."""
    values = np.asarray(values, float)
    weights = np.asarray(weights, float)
    ok = np.isfinite(values) & np.isfinite(weights) & (weights > 0)
    values, weights = values[ok], weights[ok]
    if len(values) < 2:
        return np.nan
    mean = np.average(values, weights=weights)
    denom = weights.sum() - np.square(weights).sum() / weights.sum()
    if denom <= 0:
        return np.nan
    return float(np.sqrt(np.sum(weights * np.square(values - mean)) / denom))


def summarize(fits, states):
    rules = ("declared_best_coverage", "lowest_orbit_marker_blind",
             "all_pairs_unit_weighted")
    pairsets = {rule: build_rule_pairs(fits, rule) for rule in rules}
    declared = pairsets["declared_best_coverage"]
    declared_t = {}
    for marker in MARKERS:
        base = declared[declared.year == BASELINE_SEASON]
        declared_t[marker] = weighted_quantile(
            base["d_" + marker].abs(), base.weight, TOL_QUANTILE)

    out = []
    for rule, pairs in pairsets.items():
        pairs = pairs.copy()
        pairs["state"] = pairs.district.map(states)
        scopes = [("ALL", pairs)] + [
            (state, pairs[pairs.state == state]) for state in sorted(set(states.values()))
        ]
        for scope, sub in scopes:
            for marker in MARKERS:
                base = sub[sub.year == BASELINE_SEASON]
                later = sub[sub.year != BASELINE_SEASON]
                col = "d_" + marker
                vals = base[col].abs()
                tol = weighted_quantile(vals, base.weight, TOL_QUANTILE)
                signed = later[col].to_numpy(float)
                w = later.weight.to_numpy(float)
                valid = np.isfinite(signed) & np.isfinite(w) & (w > 0)
                signed, w = signed[valid], w[valid]
                d = np.abs(signed)
                share_own = float(np.average(d <= tol, weights=w)) if len(d) and np.isfinite(tol) else np.nan
                dt = declared_t[marker]
                share_declared = float(np.average(d <= dt, weights=w)) if len(d) else np.nan
                out.append(dict(
                    rule=rule, scope=scope, marker=marker,
                    baseline_year=BASELINE_SEASON,
                    baseline_rows=int(len(base)),
                    baseline_pixel_seasons=int(base[["district", "year", "cell_id"]].drop_duplicates().shape[0]),
                    tolerance_own_2017_d=tol,
                    tolerance_declared_2017_d=dt,
                    later_rows=int(len(later)),
                    later_pixel_seasons=int(later[["district", "year", "cell_id"]].drop_duplicates().shape[0]),
                    fraction_within_own_tolerance=share_own,
                    fraction_within_declared_tolerance=share_declared,
                    passes_own_tolerance=(int(share_own >= TOL_QUANTILE)
                                          if np.isfinite(share_own) else ""),
                    median_abs_difference_d=(weighted_quantile(d, w, 0.5)
                                             if len(d) else np.nan),
                    scaled_disagreement_d=(weighted_sd(signed, w) / np.sqrt(2.0)
                                             if len(d) else np.nan),
                    interpretation="post-hoc pair-selection sensitivity; not accuracy and not an error estimate"))
    return pd.DataFrame(out)


def load_state_map(path):
    """Read an explicit district-to-state crosswalk and fail on ambiguity."""
    frame = pd.read_csv(path, usecols=["district", "state"]).drop_duplicates()
    if frame.district.isna().any() or frame.state.isna().any():
        raise ValueError("state map contains a blank district or state")
    if frame.district.duplicated().any():
        raise ValueError("district maps to more than one state")
    return dict(zip(frame.district, frame.state))


def selftest():
    rows = []
    for year in (2017, 2018):
        for orbit, pas, n, tr in ((10, "ASC", 15, 100), (20, "DESC", 25, 110),
                                  (30, "ASC", 30, 130), (40, "DESC", 20, 150)):
            rows.append(dict(district="D", year=year, cell_id="x", orbit=orbit,
                             orbit_pass=pas, n_valid=n, retained=1,
                             trough=tr + year - 2017, heading=tr + 20,
                             harvest=tr + 80))
    fits = pd.DataFrame(rows)
    dec = build_rule_pairs(fits, "declared_best_coverage")
    low = build_rule_pairs(fits, "lowest_orbit_marker_blind")
    allp = build_rule_pairs(fits, "all_pairs_unit_weighted")
    ok1 = (set(dec[["orbit_a", "orbit_b"]].itertuples(index=False, name=None)) == {(30, 20)})
    ok2 = (set(low[["orbit_a", "orbit_b"]].itertuples(index=False, name=None)) == {(10, 20)})
    ok3 = len(allp) == 12 and np.allclose(allp.groupby("year").weight.sum(), 1.0)
    q = weighted_quantile([1, 2, 9], [1, 1, 1], 0.5)
    ok4 = np.isclose(q, 2.0)
    ok4b = np.isclose(weighted_quantile([1, 2, 9, 10], [1, 1, 1, 1], 0.9),
                      np.quantile([1, 2, 9, 10], 0.9, method="linear"))
    with tempfile.TemporaryDirectory() as td:
        state_path = os.path.join(td, "states.csv")
        pd.DataFrame({"district": ["D", "D"],
                      "state": ["Odisha", "Odisha"]}).to_csv(state_path, index=False)
        ok5 = load_state_map(state_path) == {"D": "Odisha"}
        pd.DataFrame({"district": ["D", "D"],
                      "state": ["Odisha", "West Bengal"]}).to_csv(state_path, index=False)
        try:
            load_state_map(state_path)
            ok6 = False
        except ValueError:
            ok6 = True
    for name, ok in (("declared rule", ok1), ("lowest rule", ok2),
                     ("unit-weighted all pairs", ok3), ("weighted quantile", ok4),
                     ("equal-weight quantile matches protocol", ok4b),
                     ("explicit state map", ok5), ("ambiguous state refused", ok6)):
        print("[%s] %s" % ("PASS" if ok else "FAIL", name))
    return 0 if all((ok1, ok2, ok3, ok4, ok4b, ok5, ok6)) else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fits")
    ap.add_argument("--state-map",
                    help="CSV containing an unambiguous district,state crosswalk")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not (a.fits and a.state_map and a.out):
        ap.error("--fits, --state-map and --out are required")
    fits = pd.read_csv(a.fits)
    try:
        states = load_state_map(a.state_map)
    except ValueError as exc:
        raise SystemExit(str(exc))
    missing = sorted(set(fits.district) - set(states))
    if missing:
        raise SystemExit("district(s) missing from state map: %s" % missing)
    result = summarize(fits, states)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "Table_SX_OrbitPairSelectionSensitivity.csv")
    result.to_csv(path, index=False)
    print("wrote %s (%d rows)" % (path, len(result)))
    for _, row in result[(result.scope == "ALL")].iterrows():
        print("  %-27s %-7s T=%5.1f own=%0.4f declaredT=%0.4f n=%d" %
              (row.rule, row.marker, row.tolerance_own_2017_d,
               row.fraction_within_own_tolerance,
               row.fraction_within_declared_tolerance,
               row.later_pixel_seasons))
    return 0


if __name__ == "__main__":
    sys.exit(main())
