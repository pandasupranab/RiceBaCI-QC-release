"""
gate2_state_sensitivity.py -- Protocol §3.2's declared state-specific-bounds
sensitivity, executed in the only form the protocol supports.

§3.2's correction note (2026-09-07) declares: "Paper 1's bounds were predeclared from
the Odisha Kharif calendar; **state-specific bounds for West Bengal (aman) and coastal
Andhra Pradesh are reported as a supplementary sensitivity**, with Paper 1's bounds as
the headline for comparability."

WHY IT CANNOT BE RUN AS LITERALLY WRITTEN, and what is run instead.

The declaration names a sensitivity over state-specific bounds but **never specifies
them** — no numbers for West Bengal, none for coastal Andhra Pradesh, anywhere in the
protocol. Choosing them now, with the panel fitted and the results in hand, would be
exactly the discretion §3 exists to remove: any bounds wide enough to admit this
study's West Bengal markers could be written down in five minutes, and the resulting
"sensitivity" would measure the choice, not the data. Inventing them and labelling the
output a pre-declared sensitivity would be worse than not running it.

What the declaration was *for* is answerable without inventing anything. Its concern is
that Gate 2's single set of DOY bounds comes from the **Odisha** Kharif calendar and is
applied to West Bengal aman and to the Godavari-Krishna delta, so it may screen those
states differentially — deleting real phenology in one state while admitting it in
another. That is a measurable property of the committed panel:

  * the fitted marker distribution per state, against the one set of bounds actually
    applied, with the margin from each bound in days; and
  * the Gate 2 rejection rate per state, decomposed by which bound rejected, over the
    units that reached Gate 2.

If the three states sit comfortably inside the bounds with similar rejection rates, the
single-bounds choice is not distorting anything and the sensitivity is answered in the
negative with a number. If one state is pressed against a bound or rejected far more
often, that is a real finding and the bounds have to be revisited **before** any
state-specific number is quoted — and revisited by declaration, not here.

    python python/gate2_state_sensitivity.py --panel results/phen_panel_sar.csv \\
        --out results/gate2_state
    python python/gate2_state_sensitivity.py --selftest

Created 2026-09-13.
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
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
ROOT = os.environ.get("RICEBACI_ROOT", os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")

CSV_FLOAT = "%.12g"

# §3.2's bounds, Paper 1's verbatim, as applied. Imported from the extractor so the
# two cannot drift; the literals here are only the fallback for a bare checkout.
try:
    from extract_phenometrics_sar import GATE2 as _G2
    GATE2 = dict(_G2)
except Exception:                                            # pragma: no cover
    GATE2 = {"trough": (155.0, 240.0), "heading": (240.0, 320.0),
             "harvest": (280.0, 380.0)}

PRESSED_MARGIN_D = 10.0     # within this of a bound counts as "pressed against" it


def state_map(exposure_path=None):
    """district -> state, from the committed exposure catalogue."""
    if exposure_path is None:
        cands = sorted(glob.glob(os.path.join(
            ROOT, "**", "district_cyclone_exposure_ibtracs50km.csv"), recursive=True))
        if not cands:
            raise SystemExit(
                "district_cyclone_exposure_ibtracs50km.csv not found under "
                f"{ROOT}; pass --exposure. The state labels are not inferred from "
                "district names -- a wrong state assignment would silently "
                "reassign a whole state's markers.")
        exposure_path = cands[0]
    e = pd.read_csv(exposure_path)
    m = (e[["district_gadm_name", "state"]].drop_duplicates()
         .set_index("district_gadm_name")["state"].to_dict())
    return m, exposure_path


def margins(panel, states):
    """Per state x marker: distribution and the margin from each Gate 2 bound."""
    p = panel[panel["retained"].astype(int) == 1].copy()
    p["state"] = p["district"].map(states)
    unknown = sorted(p.loc[p["state"].isna(), "district"].unique())
    if unknown:
        raise SystemExit(
            f"districts absent from the state map: {unknown}. Refusing to guess.")
    rows = []
    for (st, mk), g in ((  # iterate state x marker explicitly
            (st, mk), p[p["state"] == st])
            for st in sorted(p["state"].unique()) for mk in GATE2):
        v = g[mk].astype(float).dropna()
        if not len(v):
            continue
        lo, hi = GATE2[mk]
        rows.append({
            "state": st, "marker": mk, "n": int(len(v)),
            "bound_lo": lo, "bound_hi": hi,
            "p01": float(np.percentile(v, 1)), "p05": float(np.percentile(v, 5)),
            "median": float(np.median(v)),
            "p95": float(np.percentile(v, 95)), "p99": float(np.percentile(v, 99)),
            "margin_from_lo_d": float(np.percentile(v, 5) - lo),
            "margin_from_hi_d": float(hi - np.percentile(v, 95)),
            "share_within_10d_of_lo": float(np.mean(v <= lo + PRESSED_MARGIN_D)),
            "share_within_10d_of_hi": float(np.mean(v >= hi - PRESSED_MARGIN_D)),
        })
    t = pd.DataFrame(rows)
    if len(t):
        t["pressed_against_bound"] = ((t["margin_from_lo_d"] < PRESSED_MARGIN_D)
                                      | (t["margin_from_hi_d"] < PRESSED_MARGIN_D))
    return t


def rejections(panel, states):
    """Gate 2 rejection rate per state, decomposed by which bound rejected.

    The denominator is the units that REACHED Gate 2 -- eligible on §3.11 and carrying
    an admissible shape -- because a rate over all attempted units falls when an
    earlier screen rejects more, which says nothing about Gate 2.
    """
    p = panel.copy()
    p["state"] = p["district"].map(states)
    cls = p["fail_class"].fillna("retained").astype(str)
    reached = ~cls.isin({"ineligible_dekads", "no_rise_then_fall",
                         "breakpoints_not_identified", "rise_not_significant",
                         "rise_se_not_estimable", "rise_below_floor",
                         "rise_below_minimum"})
    p, cls = p[reached], cls[reached]
    rows = []
    for st in sorted(p["state"].dropna().unique()):
        m = p["state"] == st
        c = cls[m]
        n = int(m.sum())
        g2 = c.str.startswith("outside_gate2_") | c.str.endswith("_not_recovered")
        r = {"state": st, "n_reached_gate2": n,
             "n_rejected_by_gate2": int(g2.sum()),
             "gate2_rejection_rate": float(g2.mean()) if n else np.nan}
        for mk in GATE2:
            r[f"rejected_on_{mk}"] = int(c.eq(f"outside_gate2_{mk}").sum())
        rows.append(r)
    return pd.DataFrame(rows)


def verdict(marg, rej, spread_tol=0.10):
    """TWO separate questions, deliberately not conflated into one verdict.

    An earlier version returned a single verdict and got it wrong: it flipped to
    "state-specific bounds may be needed" whenever any marker sat near a bound, even
    though the primary path EXCLUDES NOTHING on those bounds, so nearness carries no
    screening consequence at all. The two questions are:

    Q1 DIFFERENTIAL SCREENING -- does the single set of bounds delete more of one
       state than another? Answered by the Gate 2 rejection rate per state. This is
       what the §3.2 sensitivity was for.

    Q2 CALENDAR PLAUSIBILITY -- do the fitted markers sit inside bounds carried from
       the Odisha Kharif calendar, and does the answer differ by state? Answered by
       the margins. A marker outside them is NOT a screening problem here; it is a
       statement about what the fitted quantity is, which is §4.3.1's subject.
    """
    rates = rej["gate2_rejection_rate"].dropna()
    spread = float(rates.max() - rates.min()) if len(rates) > 1 else np.nan
    excludes = bool(len(rates) and rates.max() > 0)
    q1 = ("no differential screening: Gate 2 excludes nothing on this path, so it "
          "cannot screen one state more than another"
          if not excludes else
          ("no differential screening beyond tolerance"
           if np.isfinite(spread) and spread <= spread_tol
           else "DIFFERENTIAL SCREENING: rejection rate differs across states by "
                f"{spread:.4f} > {spread_tol:.2f}"))
    out_med = (marg[(marg["median"] < marg["bound_lo"])
                    | (marg["median"] > marg["bound_hi"])] if len(marg) else marg)
    over_p95 = marg[marg["margin_from_hi_d"] < 0] if len(marg) else marg
    states_out = sorted(out_med["state"].unique()) if len(out_med) else []
    q2 = ("all state x marker medians inside §3.2's bounds"
          if not len(out_med) else
          f"{len(out_med)} of {len(marg)} state x marker medians lie OUTSIDE "
          f"§3.2's bounds ({', '.join(states_out)})")
    # differential plausibility: does the margin differ much BETWEEN states?
    if len(marg):
        sp = (marg.groupby("marker")["margin_from_hi_d"].max()
              - marg.groupby("marker")["margin_from_hi_d"].min())
        margin_spread = float(sp.max())
    else:
        margin_spread = np.nan
    return {
        "n_state_marker_cells": int(len(marg)),
        "gate2_excludes_anything": excludes,
        "gate2_rejection_rate_min": float(rates.min()) if len(rates) else np.nan,
        "gate2_rejection_rate_max": float(rates.max()) if len(rates) else np.nan,
        "gate2_rejection_rate_spread": spread,
        "spread_tolerance": spread_tol,
        "q1_differential_screening": q1,
        "n_medians_outside_bounds": int(len(out_med)),
        "n_cells_with_p95_above_upper_bound": int(len(over_p95)),
        "max_between_state_margin_spread_d": margin_spread,
        "q2_calendar_plausibility": q2,
    }


def run(panel_path, out_dir, exposure=None):
    os.makedirs(out_dir, exist_ok=True)
    panel = pd.read_csv(panel_path)
    need = ["district", "retained", "fail_class"] + list(GATE2)
    missing = [c for c in need if c not in panel.columns]
    if missing:
        raise SystemExit(f"{panel_path}: missing columns {missing}")
    states, src = state_map(exposure)
    print(f"  state map from {os.path.basename(src)}: "
          f"{len(set(states.values()))} states, {len(states)} districts")
    marg = margins(panel, states)
    rej = rejections(panel, states)
    v = verdict(marg, rej)
    for nm, df in (("Table_SX_Gate2StateMargins.csv", marg),
                   ("Table_SX_Gate2StateRejections.csv", rej),
                   ("Table_SX_Gate2StateVerdict.csv", pd.DataFrame([v]))):
        p = os.path.join(out_dir, nm)
        df.to_csv(p, index=False, float_format=CSV_FLOAT)
        print(f"  wrote {p}  ({len(df)} rows)")
    print()
    print("  Gate 2 rejection rate by state, over units that reached the gate:")
    for _, r in rej.iterrows():
        print(f"    {r['state']:16s} {r['gate2_rejection_rate']:.4f}   "
              f"({int(r['n_rejected_by_gate2'])} of {int(r['n_reached_gate2'])})")
    print(f"  spread {v['gate2_rejection_rate_spread']:.4f} against a tolerance of "
          f"{v['spread_tolerance']:.2f}")
    print()
    print(f"  Q1 differential screening : {v['q1_differential_screening']}")
    print(f"  Q2 calendar plausibility  : {v['q2_calendar_plausibility']}")
    print(f"     cells whose 95th percentile exceeds the upper bound: "
          f"{v['n_cells_with_p95_above_upper_bound']} of "
          f"{v['n_state_marker_cells']}")
    print(f"     largest BETWEEN-STATE difference in upper margin: "
          f"{v['max_between_state_margin_spread_d']:.1f} d "
          f"-- small means the states behave alike against one set of bounds")
    return marg, rej, v


# ---------------------------------------------------------------------------
def selftest():
    print("=" * 74)
    print("SELF-TEST -- gate2_state_sensitivity.py")
    print("=" * 74)
    ok_all = True

    def chk(cond, msg):
        nonlocal ok_all
        ok_all &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")

    chk(GATE2 == {"trough": (155.0, 240.0), "heading": (240.0, 320.0),
                  "harvest": (280.0, 380.0)},
        "the bounds are §3.2's, imported from the extractor rather than restated")

    def mk(n, centres, state_of, fail=None):
        rows = []
        for i in range(n):
            d = f"D{i % len(state_of)}"
            rows.append({"district": d, "year": 2020, "cell_id": i,
                         "retained": 1 if fail is None else 0,
                         "fail_class": fail if fail else "retained",
                         "trough": centres[0], "heading": centres[1],
                         "harvest": centres[2]})
        return pd.DataFrame(rows)

    smap = {"D0": "Odisha", "D1": "West Bengal", "D2": "Andhra Pradesh"}

    # comfortably inside every bound
    good = mk(300, (200.0, 280.0, 330.0), smap)
    m = margins(good, smap)
    chk(len(m) == 9 and not m["pressed_against_bound"].any(),
        "markers mid-range in all three states press against no bound")
    r = rejections(good, smap)
    chk((r["gate2_rejection_rate"] == 0).all(),
        "and no state is rejected by Gate 2")
    v0 = verdict(m, r)
    chk(v0["q1_differential_screening"].startswith("no differential screening")
        and v0["q2_calendar_plausibility"].startswith("all state x marker medians"),
        "both questions answered favourably when markers sit mid-range")
    chk(v0["gate2_excludes_anything"] is False,
        "and it records that Gate 2 excluded nothing, which Q1 depends on")

    # one marker pressed against its upper bound
    tight = mk(300, (200.0, 280.0, 375.0), smap)
    mt = margins(tight, smap)
    chk(bool(mt[mt["marker"] == "harvest"]["pressed_against_bound"].all()),
        "harvest at DOY 375 against a 380 ceiling is flagged pressed")
    chk(not bool(mt[mt["marker"] == "trough"]["pressed_against_bound"].any()),
        "and trough is not, so the flag is per marker and not per panel")
    vt = verdict(mt, rejections(tight, smap))
    # harvest at 375 against a 380 ceiling is PRESSED but its p95 does not exceed the
    # bound, because this synthetic panel has zero spread. Asserting on p95 here was
    # wrong in the first version of this check: pressed and p95-above-bound are
    # different statements and only the first one applies.
    chk(bool(mt[mt["marker"] == "harvest"]["pressed_against_bound"].all())
        and vt["n_cells_with_p95_above_upper_bound"] == 0
        and vt["q1_differential_screening"].startswith("no differential screening"),
        "a marker pressed against a bound is reported under Q2 and does NOT become a "
        "screening finding -- the defect in the first version of this verdict")

    # with real spread the p95 DOES cross, and that is the Q2 statistic
    import numpy as _np
    spread_rows = []
    for i in range(300):
        spread_rows.append({"district": f"D{i % 3}", "year": 2020, "cell_id": i,
                            "retained": 1, "fail_class": "retained",
                            "trough": 200.0, "heading": 280.0,
                            "harvest": 360.0 + (i % 40)})   # up to 399 > 380
    vsp = verdict(margins(pd.DataFrame(spread_rows), smap),
                  rejections(pd.DataFrame(spread_rows), smap))
    chk(vsp["n_cells_with_p95_above_upper_bound"] == 3,
        "a marker whose 95th percentile crosses the upper bound is counted, per state")

    # a median outside the bounds is a Q2 finding, still not a Q1 one
    outside = mk(300, (250.0, 280.0, 330.0), smap)      # trough 250 > 240 ceiling
    vo = verdict(margins(outside, smap), rejections(outside, smap))
    chk(vo["n_medians_outside_bounds"] == 3
        and "OUTSIDE" in vo["q2_calendar_plausibility"]
        and vo["q1_differential_screening"].startswith("no differential screening"),
        "a median beyond a bound is a plausibility finding in all three states, "
        "not differential screening")

    # and genuine differential screening IS caught
    diff = pd.concat([
        mk(100, (200.0, 280.0, 330.0), {"D0": "Odisha"}),
        mk(100, (200.0, 280.0, 330.0), {"D1": "West Bengal"},
           fail="outside_gate2_trough")], ignore_index=True)
    vd = verdict(margins(diff, smap), rejections(diff, smap))
    chk(vd["q1_differential_screening"].startswith("DIFFERENTIAL SCREENING"),
        "one state rejected at 100% and another at 0% IS flagged as differential")

    # the denominator is units that REACHED the gate
    mixed = pd.concat([
        mk(100, (200.0, 280.0, 330.0), smap),
        mk(100, (200.0, 280.0, 330.0), smap, fail="outside_gate2_trough"),
        mk(800, (200.0, 280.0, 330.0), smap, fail="rise_not_significant")],
        ignore_index=True)
    rm = rejections(mixed, smap)
    chk(abs(float(rm["gate2_rejection_rate"].iloc[0]) - 0.5) < 1e-9,
        "Gate 2's rate is 100/200 over units that reached it, not 100/1000 over all")
    chk(int(rm["n_reached_gate2"].sum()) == 200,
        "the 800 rise-significance failures never reached Gate 2 and are excluded")
    chk(int(rm["rejected_on_trough"].sum()) == 100,
        "and the rejection is attributed to the bound that caused it")

    # an unmapped district stops the run rather than being dropped
    try:
        margins(mk(30, (200.0, 280.0, 330.0), {"D0": "Odisha"}), {"Dx": "Odisha"})
        chk(False, "an unmapped district must stop the run")
    except SystemExit as e:
        chk("Refusing to guess" in str(e),
            "an unmapped district stops the run rather than being silently dropped")

    print()
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Protocol §3.2 state-bounds sensitivity, in executable form.")
    ap.add_argument("--panel", default=os.path.join(RESULTS, "phen_panel_sar.csv"))
    ap.add_argument("--exposure", default=None)
    ap.add_argument("--out", default=os.path.join(RESULTS, "gate2_state"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    run(a.panel, a.out, a.exposure)
    return 0


if __name__ == "__main__":
    sys.exit(main())
