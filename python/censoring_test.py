#!/usr/bin/env python3
"""Does the post-landfall part of the series move the PRE-landfall breakpoint?

Protocol §4 declares beta_harv = 0 for the earlier radar trough: a cyclone making
landfall in the harvest window cannot causally alter observations acquired months
earlier. The trough is not treated as a field-observed transplanting date.
The §3.10 run measures +7.438 d, p_WCB 0.0008 at pixel level (9,999 replications,
surviving lead adjustment and IPSW). The placebo fails, so §3.8 A's coefficients
are not reported as causal effects. This post-analysis script tests whether the
association changes when the estimator or fitting window changes. It can show
estimator dependence and demonstrate a possible pathway; it cannot identify the
cause of the observed association.

THE CANDIDATE MECHANISM. PLSM fits FIVE segments to the WHOLE season, profiling
the four levels out by weighted least squares over every admissible breakpoint
quadruple. The winning quadruple minimises residual sum of squares across all 28
dekads at once. A cyclone that flattens or floods a canopy in October lowers the
late-season part of the series. That changes the fitted LEVELS. Changed levels
change which quadruple wins. So a perturbation in October can move t1, which sits
in early September. The estimator is global; the perturbation is local; the
coefficient would then be the fit reshaping, not the plant moving.

THE DESIGN. Two things could produce the +7.4 d and they must be separated:
the five-segment structure, and the post-landfall data. So the trough is measured
three ways on the same pixel-seasons.

  (1) full PLSM, 5 segments, all 28 dekads     -- the committed panel column
  (2) reduced model, 1 breakpoint, all 28      -- changes the MODEL only
  (3) reduced model, 1 breakpoint, dekads 0-12 -- changes the WINDOW too

The reduced model is the V-shape that identifies the trough on its own: a level
a0 falling to b1 at t1, then rising to p_end at the window's close. Three levels,
one breakpoint, fitted by the same profiled WLS over every admissible t1.

Window for (3): dekads 0 to 12, DOY 154.5 to 274.5. Every severe harvest-window
landfall in the 2017-2025 panel is later than this -- the earliest is Titli,
2018-10-10, DOY 283 -- so in (3) NO pixel-season contains a single observation
taken after any severe harvest-window storm. The window is the same for every
row, treated and control alike, so the truncation cannot itself be the treatment.

READING THE RESULT. Arm (2) is the arm the conclusion rests on, because it keeps
all 28 dekads and its breakpoint can land anywhere on the grid. Arm (3) is
CEILING-LIMITED: its window admits no t1 later than DOY 254.5, while the full
PLSM places troughs out to DOY 304.5, so for a late trough arm (3) has no room to
register a delay and a null there is attenuated by construction. That was missed
in the first version of this script and is now measured and printed.

  beta on (1) differs significantly from beta on (2), paired on the same rows
      -> the fitted association is ESTIMATOR-DEPENDENT on the common sample.
         This is not evidence that an agronomic date moved, but it also does not
         identify why the original association appeared or which estimator is
         better.
  beta on (2) ~ 0 while beta on (1) is significantly positive
      -> the same estimator-dependence description from the levels rather than
         the paired difference.
  beta on (2) also ~ +7 d
      -> this diagnostic does not support estimator dependence; the placebo
         failure still requires an explanation.

The last is the outcome specified before the run as incompatible with the
candidate pathway in this diagnostic. Arm (3) is secondary because its ceiling
prevents it from carrying the comparison alone. None of the arms identifies a
real-world causal mechanism.
"""
from __future__ import annotations

import os
import sys
import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_phenometrics as _FP
from extract_phenometrics_sar import (read_export, district_mean_curve,
                                      GATE1_RATIO_RADAR, USE_SMOOTHING,
                                      N_BINS_)
from attrition_diagnostics import (twfe, build_exposure_table, load_panel, SEED)

# --- portable roots ---------------------------------------------------------
# Hard-coded absolute paths made these scripts unrunnable outside the machine
# they were written on. Flagged in an external audit on 2026-09-13 and fixed
# here: one environment variable relocates everything, and the defaults are the
# paths this analysis was actually run with, so nothing silently changes.
ROOT = os.environ.get("RICEBACI_ROOT", "/home/claude")
RESULTS = os.environ.get("RICEBACI_RESULTS", os.path.join(ROOT, "results"))


def _find_doc(name):
    """Locate a committed docs/ file from wherever the script is run.

    The repository keeps the exposure catalogue and footprint table in docs/ while
    the scripts live in python/, so a bare filename resolves only when the working
    directory happens to hold both. An external audit on 2026-09-13 found three
    scripts unrunnable for exactly this reason. Candidates are searched in order
    and the first hit wins; a miss raises with the list, rather than failing later
    inside pandas with a bare filename that says nothing about where it looked.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [name,
             os.path.join(here, name),
             os.path.join(here, "..", "docs", name),
             os.path.join(ROOT, "docs", name),
             os.path.join(ROOT, name)]
    for c in cands:
        if os.path.exists(c):
            return c
    raise SystemExit(
        "cannot find %r. Looked in:\n  %s\nSet RICEBACI_ROOT, or run from a "
        "directory holding it." % (name, "\n  ".join(os.path.abspath(c)
                                                     for c in cands)))

EXPORTS = os.path.join(ROOT, "s1full")
PANEL_PIXEL = os.path.join(RESULTS, "phen_panel_sar_static.csv")
PANEL_DIST = os.path.join(RESULTS, "phen_panel_district_season_static.csv")
EXPOSURE = _find_doc("district_cyclone_exposure_ibtracs50km.csv")
OUT = os.path.join(RESULTS, "censoring_test")

# Earliest severe harvest-window landfall in the 2017-2025 panel: Titli,
# 2018-10-10, DOY 283. Verified against district_cyclone_exposure_ibtracs50km.csv
# by _verify_cut() below, which refuses to run if a severe harvest-window storm
# in the panel years lands at or before the last kept dekad.
CENSOR_DOY = 283.0
KEEP = [k for k in range(_FP.N_DEKADS) if _FP.DEKAD_DOY[k] < CENSOR_DOY]
MIN_VALID_RED = 8          # the reduced model has 4 parameters (3 levels + t1)
MIN_SEG_RED = 2            # each sloped segment needs an interior dekad
BOOT = 9999

REGS = ["S_pre_season", "S_harvest_window", "Slag_pre_season",
        "Slag_harvest_window", "M_minor"]


# ---------------------------------------------------------------------------
def reduced_designs(window):
    """One design matrix per admissible t1, for the V-shape on `window`.

    Columns weight (a0, b1, p_end). Identical in form to PLSM's first two
    segments, so the two estimators differ only in how many segments they fit
    and over how many dekads -- which is the whole point of the comparison.
    """
    n = len(window)
    keys, Xs = [], []
    for a in range(MIN_SEG_RED, n - MIN_SEG_RED):
        g = np.zeros(n)
        g[:a + 1] = np.linspace(0.0, 1.0, a + 1)
        g[a:] = 1.0
        f = np.zeros(n)
        f[a:] = np.linspace(0.0, 1.0, n - a)
        Xs.append(np.column_stack([1.0 - g, g * (1.0 - f), f]))
        keys.append(a)
    return np.asarray(keys), np.asarray(Xs)


def reduced_fit(series, valid, designs, window):
    """Profiled WLS over every admissible t1. Returns the trough DOY or NaN.

    Admissibility is the SHAPE, exactly as plsm_fit requires it and with no
    calendar gate: a0 > b1 (the season starts above its dark phase) and
    p_end > b1 (a rise follows). Refusals return NaN rather than a guess.
    """
    keys, Xs = designs
    s = np.asarray(series, float)[window]
    v = np.asarray(valid, bool)[window]
    if int(v.sum()) < MIN_VALID_RED:
        return np.nan
    y = np.where(v, s, 0.0)
    w = v.astype(float)
    A = np.einsum('mik,i,mil->mkl', Xs, w, Xs)
    b = np.einsum('mik,i,i->mk', Xs, w, y)
    det = np.linalg.det(A)
    good = np.isfinite(det) & (np.abs(det) > 1e-10)
    if not good.any():
        return np.nan
    beta = np.full((len(keys), 3), np.nan)
    beta[good] = np.linalg.solve(A[good], b[good][..., None])[..., 0]
    resid = np.einsum('mik,mk->mi', Xs, np.nan_to_num(beta)) - y[None, :]
    rss = np.einsum('mi,i,mi->m', resid, w, resid)
    a0, b1, pe = beta[:, 0], beta[:, 1], beta[:, 2]
    adm = good & np.isfinite(rss) & (a0 > b1) & (pe > b1)
    if not adm.any():
        return np.nan
    rss = np.where(adm, rss, np.inf)
    return float(_FP.DEKAD_DOY[window[int(keys[int(np.argmin(rss))])]])


# ---------------------------------------------------------------------------
def _verify_cut():
    """Refuse to run unless the window truly precedes every severe landfall."""
    e = pd.read_csv(EXPOSURE)
    hw = e[e.timing_class.astype(str).str.contains("harvest", case=False,
                                                   na=False)
           & e.severity_class.astype(str).str.contains("severe", case=False,
                                                       na=False)].copy()
    hw["season"] = hw["season"].astype(int)
    hw = hw[(hw.season >= 2017) & (hw.season <= 2025)]
    t = pd.to_datetime(hw["maxwind_fix_iso_time"], errors="coerce")
    hw["doy"] = t.dt.dayofyear
    last_kept = float(_FP.DEKAD_DOY[KEEP[-1]])
    bad = hw[hw.doy <= last_kept]
    print(f"censoring window: dekads {KEEP[0]}-{KEEP[-1]}, "
          f"DOY {_FP.DEKAD_DOY[KEEP[0]]:.1f}-{last_kept:.1f} "
          f"({len(KEEP)} dekads)")
    print(f"severe harvest-window landfalls in 2017-2025: {len(hw)} rows, "
          f"earliest DOY {hw.doy.min():.0f} "
          f"({hw.loc[hw.doy.idxmin(), 'storm_name']} "
          f"{hw.loc[hw.doy.idxmin(), 'season']})")
    if len(bad):
        print("\n*** STOP *** a severe harvest-window landfall falls inside the "
              "censoring window, so the window does not precede every storm:")
        print(bad[["storm_name", "season", "maxwind_fix_iso_time",
                   "doy"]].drop_duplicates().to_string(index=False))
        return False
    print(f"  [PASS] every severe harvest-window landfall is later than "
          f"DOY {last_kept:.1f}; no censored series contains a post-storm "
          f"observation")
    return True


def selftest():
    """The reduced estimator must recover a planted trough, and must move it
    when late-season data is added that the truncated window cannot see."""
    ok_all = True
    full_w = list(range(_FP.N_DEKADS))
    d_full, d_cens = reduced_designs(full_w), reduced_designs(KEEP)

    # a clean V with its kink at dekad 9 (DOY 244.5), then a plateau and a fall
    n = _FP.N_DEKADS
    s = np.empty(n)
    s[:10] = np.linspace(-5.0, -12.0, 10)
    s[9:17] = np.linspace(-12.0, -6.0, 8)
    s[16:24] = -6.0
    s[23:] = np.linspace(-6.0, -9.0, n - 23)
    valid = np.ones(n, bool)
    got = reduced_fit(s, valid, d_cens, KEEP)
    ok = abs(got - 244.5) <= 10.0
    ok_all &= ok
    print(f"  planted trough DOY 244.5 -> censored fit {got}")
    print(f"  [{'PASS' if ok else 'FAIL'}] reduced model recovers a planted "
          f"trough inside the censoring window")

    # a possible estimator pathway, demonstrated on one synthetic series: drop the late season by 4 dB,
    # which is what a flattened canopy does, and see the FULL-window fit move
    # while the CENSORED fit cannot.
    s2 = s.copy()
    s2[KEEP[-1] + 1:] -= 4.0
    a_full, b_full = (reduced_fit(s, valid, d_full, full_w),
                      reduced_fit(s2, valid, d_full, full_w))
    a_cen, b_cen = (reduced_fit(s, valid, d_cens, KEEP),
                    reduced_fit(s2, valid, d_cens, KEEP))
    ok = (abs(a_cen - b_cen) < 1e-9) and (abs(a_full - b_full) > 1e-9)
    ok_all &= ok
    print(f"  post-window -4 dB: full-window trough {a_full} -> {b_full}; "
          f"censored trough {a_cen} -> {b_cen}")
    print(f"  [{'PASS' if ok else 'FAIL'}] a purely post-window perturbation "
          f"moves the full-window fit and cannot move the censored fit")
    print(f"  [{'PASS' if _verify_cut() else 'FAIL'}] censoring window verified "
          f"against the exposure catalogue")
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


# ---------------------------------------------------------------------------
def refit(exports=EXPORTS, limit=None):
    """Refit every district-season three ways. Writes the refit panel."""
    files = sorted(f for f in os.listdir(exports) if f.endswith(".csv"))
    if limit:
        files = files[:limit]
    full_w = list(range(_FP.N_DEKADS))
    d_full, d_cens = reduced_designs(full_w), reduced_designs(KEEP)
    prows, drows = [], []
    for j, f in enumerate(files, 1):
        district, year, cells, lon, lat, V, C = read_export(
            os.path.join(exports, f))

        # district level: the same cohort mean curve the primary estimand uses
        mean, sd, se, n_cov, keep = district_mean_curve(V, C)
        vd = keep & np.isfinite(mean)
        drows.append(dict(district=district, year=year,
                          trough_red_full=reduced_fit(mean, vd, d_full, full_w),
                          trough_red_cens=reduced_fit(mean, vd, d_cens, KEEP)))

        # pixel level: identical admission, aggregation and smoothing to
        # process_file, so (1) and (2)/(3) differ only in the model and window
        counts = np.nansum(np.where(np.isfinite(V), C, 0.0), axis=0)
        admitted = (_FP.gate1_admitted_bins(counts, GATE1_RATIO_RADAR)
                    if GATE1_RATIO_RADAR > 0
                    else np.ones(N_BINS_, dtype=bool))
        DV, DC = _FP.aggregate_to_dekads(V, C, admitted)
        for i in range(DV.shape[0]):
            valid = np.isfinite(DV[i])
            series = np.where(valid, DV[i], 0.0)
            if USE_SMOOTHING and valid.sum() >= 4:
                w = np.where(valid, np.maximum(DC[i], 1.0), 0.0)
                series, _, _ = _FP.whittaker_gcv(series, w)
            prows.append(dict(
                district=district, year=year, cell_id=cells[i],
                trough_red_full=reduced_fit(series, valid, d_full, full_w),
                trough_red_cens=reduced_fit(series, valid, d_cens, KEEP)))
        if j % 25 == 0 or j == len(files):
            print(f"  refit {j}/{len(files)} exports", flush=True)
    os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(prows).to_csv(f"{OUT}/refit_pixel.csv", index=False)
    pd.DataFrame(drows).to_csv(f"{OUT}/refit_district.csv", index=False)
    print(f"wrote {OUT}/refit_pixel.csv ({len(prows)} rows) and "
          f"refit_district.csv ({len(drows)} rows)")


def estimate(only_level=None, want_own=False, own_only=False):
    """beta_harv on the trough, measured all three ways, at both levels.

    `only_level` runs one level, so each fits inside a single foreground call;
    each level writes its own table and they are concatenated by --collect.
    """
    out = []
    specs = [("pixel", PANEL_PIXEL, f"{OUT}/refit_pixel.csv",
              ["district", "year", "cell_id"]),
             ("district", PANEL_DIST, f"{OUT}/refit_district.csv",
              ["district", "year"])]
    if only_level:
        specs = [t for t in specs if t[0] == only_level]
    for level, ppath, rpath, keys in specs:
        panel = load_panel(ppath, level)
        refits = pd.read_csv(rpath)
        refits["year"] = refits["year"].astype(int)
        n_before = len(panel)
        panel = panel.merge(refits, on=keys, how="left", validate="one_to_one")
        assert len(panel) == n_before, "the refit merge changed the row count"
        exposure = pd.read_csv(EXPOSURE)
        tab = build_exposure_table(exposure, sorted(panel["district"].unique()),
                                   sorted(panel["year"].unique()))
        panel = panel.merge(tab, on=["district", "year"], how="left")
        for c in ["S_pre_season", "S_harvest_window", "M_minor",
                  "Slag_pre_season", "Slag_harvest_window"]:
            panel[c] = panel[c].fillna(0).astype(int)

        MEAS = (("trough", "full PLSM, 5 segments, 28 dekads"),
                ("trough_red_full", "reduced model, 1 breakpoint, 28 dekads"),
                ("trough_red_cens", f"reduced model, 1 breakpoint, dekads "
                                    f"{KEEP[0]}-{KEEP[-1]}"))
        ret = panel[panel.retained == 1]
        cov = {c: float(ret[c].notna().mean()) for c, _ in MEAS}
        print("\n" + "=" * 78)
        print(f"{level.upper()} LEVEL -- beta_harv on the trough, {BOOT} "
              f"replications")
        print("=" * 78)
        print(f"retained rows {len(ret)};  non-missing share: "
              + ",  ".join(f"{k} {v:.3f}" for k, v in cov.items()))

        # The reduced model refuses a different set of rows from the full one, so
        # comparing the three arms on their own samples compares samples as well
        # as estimators. The COMMON sample -- every retained row all three can
        # measure -- is the only comparison in which the estimator is the sole
        # difference, and it is the one the conclusion rests on. The own-sample
        # arms are reported too, because their sample sizes are evidence as well.
        cols = [c for c, _ in MEAS]
        c_ok = panel[cols].notna().all(axis=1) & (panel["retained"] == 1)
        n_common = int(c_ok.sum())
        print(f"common sample (all three measurable, retained): {n_common} rows "
              f"= {n_common / max(1, len(ret)):.1%} of retained")
        # Order matters: the common sample and the paired test are what the
        # conclusion rests on, so they run first and a killed run still has
        # them. The own-sample arm is context -- its arm (1) is already the
        # §3.10 table's trough:S_harvest_window row.
        for scope, sub in ((("common", panel[c_ok]),) if not own_only else ()):
            print(f"\n  -- {scope} sample --")
            for k, (col, what) in enumerate(MEAS, 1):
                r = twfe(sub, col, REGS, BOOT, SEED, "S_harvest_window")
                lab = f"({k}) {what}"
                if r.get("status") != "estimated":
                    print(f"  {lab:<52s} not estimable -- {r.get('reason','')}")
                    continue
                print(f"  {lab:<52s} {r['coef']:+8.3f} d  (se {r['se']:6.3f})  "
                      f"p_WCB {r['p_wcb']:.4f}  CI [{r['wcb_ci_lo']:+7.2f}, "
                      f"{r['wcb_ci_hi']:+7.2f}]  n={r['n_obs']}")
                out.append(dict(level=level, sample=scope, measure=col,
                                specification=what,
                                **{kk: r.get(kk) for kk in
                                   ("coef", "se", "p_wcb", "wcb_ci_lo",
                                    "wcb_ci_hi", "n_obs", "n_clusters",
                                    "n_treated_clusters")}))

        # THE CEILING, and the arm that is free of it. Arm (3) cannot place a
        # trough later than the last admissible t1 inside its window -- DOY 254.5
        # -- while the full PLSM ranges to DOY 304.5 on these rows. Where the
        # true trough is already at or near that ceiling, arm (3) has no room to
        # register a further delay, so it is attenuated BY CONSTRUCTION and a null
        # there is not evidence. This was not checked before the first version of
        # this script was reported; it is checked here, and it is why the
        # conclusion is carried by arm (2) -- which keeps all 28 dekads and has no
        # ceiling -- and by the paired tests.
        _cs = panel[c_ok]
        cap = float(_cs["trough_red_cens"].max())
        if own_only:
            print("  (common, ceiling and paired arms skipped: --own-only)")
        _skip = own_only
        at_cap = float((_cs["trough_red_cens"] >= cap - 1e-9).mean())
        headroom = _cs["trough"] < cap - 9.0    # a full dekad below the ceiling
        print(f"\n  ceiling on arm (3): latest admissible trough DOY {cap:.1f}; "
              f"{at_cap:.1%} of common rows sit on it")
        print(f"  rows whose full-PLSM trough is at least one dekad below it: "
              f"{int(headroom.sum())} ({headroom.mean():.1%})")
        sub_h = panel[c_ok & (panel["trough"] < cap - 9.0)]
        # NOTE, and it is not a small one: restricting to rows whose full-PLSM
        # trough is below the ceiling conditions on the DEPENDENT VARIABLE. Both
        # coefficients below are attenuated mechanically by that selection, so
        # neither is a valid estimate of beta_harv and a null here is not
        # evidence of a null. What the two lines legitimately show is WHERE in
        # the sample the placebo failure lives -- it is absent among rows whose
        # fitted trough is early, so it is carried by rows whose five-segment fit
        # has placed t1 unusually late, which is itself the signature of a
        # reshaped fit. Descriptive, and labelled so in the output table.
        print("  arms (1) and (3) on those ceiling-free rows only "
              "(DESCRIPTIVE: selects on the outcome, so both are attenuated):")
        for k, col in (() if _skip else ((1, "trough"), (3, "trough_red_cens"))):
            r = twfe(sub_h, col, REGS, BOOT, SEED, "S_harvest_window")
            if r.get("status") != "estimated":
                print(f"    ({k}) not estimable -- {r.get('reason','')}")
                continue
            print(f"    ({k}) {col:<18s} {r['coef']:+8.3f} d  (se {r['se']:6.3f})"
                  f"  p_WCB {r['p_wcb']:.4f}  CI [{r['wcb_ci_lo']:+7.2f}, "
                  f"{r['wcb_ci_hi']:+7.2f}]  n={r['n_obs']}")
            out.append(dict(level=level, sample="common_ceiling_free",
                            measure=col, specification=f"DESCRIPTIVE ONLY -- "
                            f"arm ({k}) on rows with full-PLSM trough at least "
                            f"one dekad below DOY {cap:.1f}; selects on the "
                            f"outcome, so attenuated and not a valid estimate",
                            **{kk: r.get(kk) for kk in
                               ("coef", "se", "p_wcb", "wcb_ci_lo", "wcb_ci_hi",
                                "n_obs", "n_clusters", "n_treated_clusters")}))

        # THE PAIRED TEST. Comparing two coefficients by whether each is
        # separately significant is weak: their intervals can overlap while the
        # difference is real, or vice versa. The difference is directly
        # estimable, because both measures exist on the same rows -- regress the
        # per-row DIFFERENCE between the two troughs on the same exposure. A
        # non-zero coefficient means the two estimators respond differently to
        # harvest-window exposure, which is the claim, tested rather than
        # inferred from two intervals.
        pan = panel.copy()
        pan["d_full_minus_cens"] = pan["trough"] - pan["trough_red_cens"]
        pan["d_full_minus_red"] = pan["trough"] - pan["trough_red_full"]
        print("\n  paired difference in how the estimators respond to exposure "
              "(same rows):")
        for col, what in (() if _skip else (
                ("d_full_minus_cens",
                 "(1) - (3): 5-segment minus censored 1-breakpoint"),
                ("d_full_minus_red",
                 "(1) - (2): 5-segment minus 28-dekad 1-breakpoint"))):
            r = twfe(pan[c_ok], col, REGS, BOOT, SEED, "S_harvest_window")
            if r.get("status") != "estimated":
                print(f"    {what:<50s} not estimable -- {r.get('reason','')}")
                continue
            print(f"    {what:<50s} {r['coef']:+8.3f} d  (se {r['se']:6.3f})  "
                  f"p_WCB {r['p_wcb']:.4f}  CI [{r['wcb_ci_lo']:+7.2f}, "
                  f"{r['wcb_ci_hi']:+7.2f}]  n={r['n_obs']}")
            out.append(dict(level=level, sample="common_paired_difference",
                            measure=col, specification=what,
                            **{kk: r.get(kk) for kk in
                               ("coef", "se", "p_wcb", "wcb_ci_lo", "wcb_ci_hi",
                                "n_obs", "n_clusters", "n_treated_clusters")}))

        # How much do the three measures agree at all? A coefficient difference
        # means little if the measures are barely correlated to begin with.
        cs = panel[c_ok]
        print(f"\n  agreement on the common sample ({len(cs)} rows):")
        for a, b in (("trough", "trough_red_full"),
                     ("trough", "trough_red_cens"),
                     ("trough_red_full", "trough_red_cens")):
            d_ = cs[b] - cs[a]
            print(f"    {b} - {a}:  mean {d_.mean():+7.2f} d   "
                  f"sd {d_.std():6.2f}   r {cs[a].corr(cs[b]):+.3f}")

        # Opt-in with --own. Arm (1) here is literally the §3.10 table's
        # trough:S_harvest_window row, and the conclusion rests on the common
        # sample and the paired test above; running three more 9,999-replication
        # bootstraps by default only risks the run being killed before it writes.
        print("\n  -- own sample (each arm on every row it can measure)"
              + ("" if want_own else " -- skipped, pass --own") + " --")
        for k, (col, what) in (enumerate(MEAS, 1) if want_own else []):
            r = twfe(panel, col, REGS, BOOT, SEED, "S_harvest_window")
            lab = f"({k}) {what}"
            if r.get("status") != "estimated":
                print(f"  {lab:<52s} not estimable -- {r.get('reason','')}")
                continue
            print(f"  {lab:<52s} {r['coef']:+8.3f} d  (se {r['se']:6.3f})  "
                  f"p_WCB {r['p_wcb']:.4f}  CI [{r['wcb_ci_lo']:+7.2f}, "
                  f"{r['wcb_ci_hi']:+7.2f}]  n={r['n_obs']}")
            out.append(dict(level=level, sample="own", measure=col,
                            specification=what,
                            **{kk: r.get(kk) for kk in
                               ("coef", "se", "p_wcb", "wcb_ci_lo", "wcb_ci_hi",
                                "n_obs", "n_clusters", "n_treated_clusters")}))
    df = pd.DataFrame(out)
    os.makedirs(OUT, exist_ok=True)
    dest = (f"{OUT}/Table_SX_CensoringTest.csv" if not only_level
            else f"{OUT}/Table_SX_CensoringTest.{only_level}.csv")
    # Accumulate rather than overwrite. The arms are opt-in and a full run does
    # not fit in one foreground call, so a per-level table is built up across
    # invocations; rows are keyed by (level, sample, measure) and a rerun of an
    # arm replaces its own rows rather than duplicating or deleting the others.
    if os.path.exists(dest) and len(df):
        prev = pd.read_csv(dest)
        KEY = ["level", "sample", "measure"]
        if all(k in prev.columns for k in KEY):
            new_keys = set(map(tuple, df[KEY].astype(str).to_numpy()))
            keep = ~prev[KEY].astype(str).apply(tuple, axis=1).isin(new_keys)
            n_kept = int(keep.sum())
            df = pd.concat([prev[keep], df], ignore_index=True)
            print(f"\n  merged with {os.path.basename(dest)}: kept {n_kept} "
                  f"earlier row(s), replaced/added {len(out)}")
    df = df.sort_values(["level", "sample", "measure"], kind="mergesort")
    df.to_csv(dest, index=False)
    print(f"wrote {dest} ({len(df)} rows)")


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        sys.exit(selftest())
    if not _verify_cut():
        sys.exit(2)
    if "--refit" in a:
        lim = None
        if "--limit" in a:
            lim = int(a[a.index("--limit") + 1])
        refit(limit=lim)
    if "--estimate" in a:
        lv = a[a.index("--level") + 1] if "--level" in a else None
        estimate(only_level=lv, want_own=("--own" in a or "--own-only" in a),
                 own_only="--own-only" in a)
    if "--collect" in a:
        parts = [f"{OUT}/Table_SX_CensoringTest.{lv}.csv"
                 for lv in ("pixel", "district")]
        have = [f for f in parts if os.path.exists(f)]
        if len(have) != len(parts):
            raise SystemExit("--collect needs both per-level tables; missing "
                             + ", ".join(f for f in parts if f not in have))
        df = pd.concat([pd.read_csv(f) for f in have], ignore_index=True)
        df.to_csv(f"{OUT}/Table_SX_CensoringTest.csv", index=False)
        print(f"wrote {OUT}/Table_SX_CensoringTest.csv ({len(df)} rows)")
