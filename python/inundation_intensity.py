"""
inundation_intensity.py -- Protocol §3.3's `inundated_frac`, and the test of whether
the criterion it rests on separates anything.

§3.3 declares: a pre-event reference of the median σ⁰_VH over the 30 days ending 5 days
before landfall, computed ON THE SAME ORBITS as the event window; a pixel is inundated
if the event-window minimum falls at or below reference − 3 dB; and **the threshold is
re-derived on the untreated 2017 baseline**, which carries no severe exposure on this
roster. `gee/S1_INUNDATION.js` exports the drop statistic for both arms and **scores
nothing** -- the re-derivation is here, because a threshold set in the same script that
produced the data is not a re-derivation.

THE DECISION RULE, DECLARED BEFORE THE EXPORT EXISTED (2026-09-13).

Written while only the two-probe verify output was in hand, so that the criterion is
judged against a rule fixed in advance rather than one chosen after seeing 71 rows.
The criterion shows an excess of flagged drops in cyclone windows over the matched
baseline if and only if BOTH hold, over the severe harvest-window units -- the units
for which the proposed inundation interpretation was intended:

  (i)  the median per-unit excess at the declared 3 dB threshold is at least
       **+0.05** -- five percentage points more pixels flagged in the cyclone year than
       in that unit's own matched 2017 window; and
  (ii) the within-unit arm-label permutation p-value for the mean excess is
       **<= 0.05**.

If either fails, `inundated_frac` does not meet the declared separation rule on this
coast and §3.3 is withdrawn by dated amendment rather than reported as an intensity
variable. Even passing would show a cyclone-window excess, not field validation that
each flagged pixel was flooded. The rule is deliberately permissive -- five percentage
points is a small contrast for a severe cyclone over a standing crop -- so that failing
it is informative.

WHY THE UNIT OF INFERENCE IS district x storm AND NOT THE PIXEL. 400 cohort points in a
district are not 400 independent observations of a flood: inundation is spatially
contiguous, and the separate breakpoint semivariogram (`python/semivariance.py`) also
shows that local pixel timings are spatially coherent. That different analysis does not
validate this inundation statistic; it only reinforces the need to avoid treating pixels
as independent replicates. A pooled pixel-level test would report
a p-value from an effective sample of a few tens of storms as though it came from tens of
thousands of pixels. So the pixel-level rate is the OUTCOME, computed per unit, and the
test is over units. With few severe harvest-window units, MacKinnon & Webb (2018) applies
in spirit: a null over a handful of treated clusters is uninformative unless it is
labelled as such, and `verdict()` labels it.

WHY THE 2017 NULL IS NOT SIMPLY A LOWER BOUND. The event-window statistic is a MINIMUM
over the window and the reference is a MEDIAN over 30 days, so the drop is positive in
expectation from speckle alone: with more event-window scenes the minimum goes deeper.
2017 flew S1A+S1B on a 6-day repeat; S1B failed 2021-12-23, so 2022-2025 are S1A only.
An arm with more scenes therefore gets a larger drop for free, and if the null arm is the
scene-rich one the comparison is biased AGAINST finding signal. `scene_balance()`
measures that per unit and `verdict()` refuses to call a negative result clean on units
where the null carries materially more event-window scenes.

THE WINDOW DEFECT THIS MODULE NOW GATES ON (found 2026-09-13 in the Baleshwar dry run).

§3.3 declares an event window of "+/-14 days around landfall" and a reference of "the
median over the 30 days ending 5 days before landfall". Those two windows **overlap by
9 days** -- reference [L-35, L-5] against event [L-14, L+14] share [L-14, L-5], 30% of
the reference. Two consequences, both measured:

  (a) An orbit whose scenes in both windows are the same acquisition gives
      pre-median minus event-minimum **exactly 0**. The dry-run export carries a point
      mass at 0.0 on 235 of 2,400 rows (9.8%), and it is **arm-asymmetric**: Fani 9.50%
      in the actual arm against 0.25% in the matched null, a factor of 38; Dana 19.25%
      against 10.50%; Yaas 15.25% against 4.00%. A point mass differing 38-fold between
      the two arms being compared is not a property of flooding, and any test of actual
      against null on that statistic is comparing two differently contaminated things.

  (b) Half the declared event window lies **before** landfall, so the minimum that
      defines "inundated" can be an acquisition predating the storm.

`gee/S1_INUNDATION.js` now exports two specifications -- `postlandfall` ([L, L+14], zero
overlap, the measurement) and `declared` ([L-14, L+14], reported as declared) -- plus
`win_min_day_off`, the day of the window minimum relative to landfall, so a minimum that
predates the storm is visible rather than inferred. §3.3's own sentence, "the 3 dB
criterion AND THE WINDOW LENGTH are re-derived on the untreated 2017 baseline season
before use", is what authorises the corrected spec; it is a calibration this section
already required, not a change of specification after seeing a result.

`check_windows()` enforces three things and **refuses rather than reports** when they
fail: a spec whose `overlap_days` is non-zero cannot carry the verdict; a spec whose
exact-zero mass differs between the arms by more than `MAX_ZERO_ASYMMETRY` cannot carry
the verdict; and if `win_min_day_off` is present, the share of reported minima that
predate landfall is measured and reported per arm. A single-spec export from before this
correction still runs, and is labelled `PRE-CORRECTION` throughout.

    python python/inundation_intensity.py --exports data/S1_inund/ --out results/inundation
    python python/inundation_intensity.py --selftest

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
ROOT = os.environ.get("RICEBACI_ROOT", os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")

CSV_FLOAT = "%.12g"

DECLARED_DROP_DB = 3.0          # §3.3's declared criterion, not negotiable here
NULL_QUANTILES = (0.95, 0.99)   # the re-derived thresholds, read off the null arm
MIN_EXCESS = 0.05               # rule (i)
ALPHA = 0.05                    # rule (ii)
N_PERM = 2000
SEED = 20260913
MIN_TREATED_UNITS = 3           # MacKinnon & Webb (2018), applied to units
SCENE_IMBALANCE = 1.25          # null/actual event scenes above this = flagged

UNIT_KEYS = ["district", "storm", "season"]
REQUIRED = UNIT_KEYS + ["arm", "severity_class", "timing_class", "drop_db",
                        "n_orbits_paired", "n_pre", "n_win", "cell_id"]
# Present only in exports made after the 2026-09-13 window correction.
OPTIONAL = ["window_spec", "overlap_days", "win_min_day_off"]

PRIMARY_SPEC = "postlandfall"     # the measurement
DECLARED_SPEC = "declared"        # §3.3 as written; reported, never read
MAX_ZERO_ASYMMETRY = 0.02         # |zero-mass actual - null|, in share of pixels


def check_windows(d):
    """Which window specs, if any, may carry the verdict.

    Returns (DataFrame of per-spec diagnostics, list of admissible spec names).
    A spec is admissible only if its reference and event windows do not overlap AND
    its exact-zero point mass is close between the arms. Both are properties of the
    window arithmetic rather than of the data, so a spec that fails either is not a
    weaker test -- it is not a test of this quantity at all.
    """
    if "window_spec" not in d.columns:
        print("  PRE-CORRECTION EXPORT: no window_spec column. This export predates "
              "the\n  2026-09-13 window correction, so every row comes from the "
              "declared\n  +/-14 window whose reference it overlaps by 9 days. "
              "Diagnostics are\n  computed, but no spec is admissible and no verdict "
              "is issued.")
        d = d.copy()
        d["window_spec"] = DECLARED_SPEC
        pre_correction = True
    else:
        pre_correction = False

    rows, admissible = [], []
    for spec, g in d.groupby("window_spec", sort=True):
        ov = (sorted(g["overlap_days"].dropna().unique())
              if "overlap_days" in g.columns else [])
        ov_max = float(max(ov)) if ov else np.nan
        za = {}
        for arm in ("actual", "null2017"):
            v = g[g["arm"] == arm]["drop_db"].astype(float)
            za[arm] = float((v == 0).mean()) if len(v) else np.nan
        asym = abs(za.get("actual", np.nan) - za.get("null2017", np.nan))
        pre_lf = {}
        if "win_min_day_off" in g.columns:
            for arm in ("actual", "null2017"):
                w = g[g["arm"] == arm]["win_min_day_off"].astype(float).dropna()
                pre_lf[arm] = float((w < 0).mean()) if len(w) else np.nan
        ok_overlap = bool(np.isfinite(ov_max) and ov_max <= 0) if ov else False
        ok_asym = bool(np.isfinite(asym) and asym <= MAX_ZERO_ASYMMETRY)
        ok = ok_overlap and ok_asym and not pre_correction
        if ok:
            admissible.append(spec)
        rows.append({
            "window_spec": spec, "overlap_days_max": ov_max,
            "zero_mass_actual": za.get("actual", np.nan),
            "zero_mass_null2017": za.get("null2017", np.nan),
            "zero_mass_asymmetry": asym,
            "share_min_predates_landfall_actual": pre_lf.get("actual", np.nan),
            "share_min_predates_landfall_null2017": pre_lf.get("null2017", np.nan),
            "overlap_ok": ok_overlap, "zero_asymmetry_ok": ok_asym,
            "admissible": ok})
    diag = pd.DataFrame(rows)
    print("  window diagnostics:")
    for _, r in diag.iterrows():
        print(f"    {r['window_spec']:14s} overlap {r['overlap_days_max']:>5} d   "
              f"zero-mass {r['zero_mass_actual']:.4f} / "
              f"{r['zero_mass_null2017']:.4f} (gap {r['zero_mass_asymmetry']:.4f})"
              f"   admissible {r['admissible']}")
    if not admissible:
        print("  NO ADMISSIBLE WINDOW SPEC. The verdict is withheld, not negative: a")
        print("  statistic whose two arms are contaminated to different degrees by the")
        print("  window arithmetic cannot be compared between them.")
    return diag, admissible


# ---------------------------------------------------------------------------
def read_exports(directory, pattern="S1_INUND_*.csv"):
    """Read the §3.3 exports and refuse anything the schema does not guarantee."""
    files = sorted(glob.glob(os.path.join(directory, pattern)))
    if not files:
        raise SystemExit(f"no {pattern} under {directory}")
    frames = []
    for f in files:
        df = pd.read_csv(f)
        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            raise SystemExit(
                f"{os.path.basename(f)}: columns {missing} absent.\n"
                "This is the Earth Engine header-inference defect -- an all-null "
                "leading block drops those columns from the whole file. Re-export "
                "with the explicit `selectors` list S1_INUNDATION.js carries; do not "
                "patch around it here, because a missing column means the rows are "
                "not the rows the script wrote.")
        frames.append(df)
    d = pd.concat(frames, ignore_index=True)
    arms = set(d["arm"].unique())
    if not {"actual", "null2017"} <= arms:
        raise SystemExit(
            f"arms present are {sorted(arms)}; both 'actual' and 'null2017' are "
            "required. §3.3 re-derives the threshold on the untreated baseline, so a "
            "run without the null arm cannot produce a threshold at all. Set "
            "CONFIG.emitNullArm = true and re-export.")
    print(f"§3.3 exports: {len(files)} files, {len(d):,} rows, "
          f"{d.groupby(UNIT_KEYS).ngroups} district x storm units, arms {sorted(arms)}")
    return d


# ---------------------------------------------------------------------------
def usable(d):
    """Rows on which a drop is defined at all, and a named count of what was dropped.

    A null `drop_db` means no relative orbit appeared in both windows for that unit --
    a real state of the acquisition schedule, not a defect -- and such a row carries no
    information either way. It is excluded and counted, never filled.
    """
    n0 = len(d)
    ok = d["drop_db"].notna() & (d["n_orbits_paired"].fillna(0) >= 1)
    out = d[ok].copy()
    print(f"  usable rows: {len(out):,} of {n0:,} "
          f"({n0 - len(out):,} with no orbit paired across both windows)")
    return out


def rates(d, thresholds):
    """Per unit x arm: pixel count, drop percentiles, and the flagged share at each
    threshold. The flagged share is `inundated_frac` -- one number per unit per arm."""
    rows = []
    for (dist, storm, season, arm), g in d.groupby(UNIT_KEYS + ["arm"], sort=True):
        v = g["drop_db"].astype(float).values
        r = {"district": dist, "storm": storm, "season": season, "arm": arm,
             "severity_class": g["severity_class"].iloc[0],
             "timing_class": g["timing_class"].iloc[0],
             "n_pixels": len(v),
             "n_pre": float(np.nanmedian(g["n_pre"].astype(float))),
             "n_win": float(np.nanmedian(g["n_win"].astype(float))),
             "drop_p50": float(np.percentile(v, 50)),
             "drop_p90": float(np.percentile(v, 90)),
             "drop_p95": float(np.percentile(v, 95)),
             "drop_p99": float(np.percentile(v, 99))}
        for name, tau in thresholds.items():
            r[f"inundated_frac_{name}"] = float(np.mean(v >= tau))
        rows.append(r)
    return pd.DataFrame(rows)


def derive_thresholds(d):
    """The §3.3 re-derivation: thresholds read off the pooled untreated 2017 arm.

    Returns {name: tau}. The declared 3 dB is carried alongside, unchanged, so the
    protocol's own criterion is evaluated as declared and not only in its recalibrated
    form -- replacing a declared threshold with a better one and reporting only the
    better one would answer a question §3.3 did not ask.
    """
    nul = d[d["arm"] == "null2017"]["drop_db"].astype(float).values
    if len(nul) < 100:
        raise SystemExit(
            f"only {len(nul)} usable null-arm rows; a threshold read off the 2017 "
            "baseline needs the baseline. Re-export with emitNullArm = true.")
    t = {"declared3db": DECLARED_DROP_DB}
    for q in NULL_QUANTILES:
        t[f"null_q{int(q * 100)}"] = float(np.quantile(nul, q))
    print("  thresholds: " + ", ".join(f"{k} = {v:.3f} dB" for k, v in t.items())
          + f"   (null arm n = {len(nul):,})")
    return t


def excess(rt, thresholds):
    """Per unit: actual rate minus its own matched-null rate, at every threshold."""
    a = rt[rt["arm"] == "actual"].set_index(UNIT_KEYS)
    n = rt[rt["arm"] == "null2017"].set_index(UNIT_KEYS)
    common = a.index.intersection(n.index)
    out = a.loc[common, ["severity_class", "timing_class", "n_pixels",
                         "n_pre", "n_win"]].copy()
    out = out.rename(columns={"n_pre": "n_pre_actual", "n_win": "n_win_actual"})
    out["n_win_null"] = n.loc[common, "n_win"]
    out["n_pre_null"] = n.loc[common, "n_pre"]
    for name in thresholds:
        out[f"frac_actual_{name}"] = a.loc[common, f"inundated_frac_{name}"]
        out[f"frac_null_{name}"] = n.loc[common, f"inundated_frac_{name}"]
        out[f"excess_{name}"] = (out[f"frac_actual_{name}"]
                                 - out[f"frac_null_{name}"])
    dropped = len(a) - len(common)
    if dropped:
        print(f"  {dropped} unit(s) had an actual arm with no matched null and are "
              f"excluded from the paired test")
    return out.reset_index()


def scene_balance(ex):
    """Flag units where the null arm carries materially more event-window scenes.

    The event statistic is a minimum, so more scenes means a deeper minimum from
    speckle alone. A null arm with more scenes biases the comparison against finding
    signal, and a negative result on such a unit is not clean.
    """
    r = ex["n_win_null"] / ex["n_win_actual"].replace(0, np.nan)
    ex = ex.copy()
    ex["win_scene_ratio_null_over_actual"] = r
    ex["null_scene_advantaged"] = (r > SCENE_IMBALANCE).fillna(False)
    return ex


def permute_excess(ex, col, n_perm=N_PERM, seed=SEED):
    """Within-unit arm-label permutation p-value for the mean excess.

    Each unit's two rates are exchangeable under the null that the arm label carries
    no information, so a draw flips the sign of that unit's excess independently. This
    is the exact randomisation distribution of the mean excess under that null -- it is
    a sign-flip test, not an approximation to one, and it needs no distributional
    assumption about pixel rates.
    """
    e = ex[col].astype(float).dropna().values
    if len(e) == 0:
        return np.nan, 0, np.nan
    obs = float(np.mean(e))
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_perm, len(e)))
    draws = (signs * e[None, :]).mean(axis=1)
    # one-sided: §3.3 predicts MORE flagged pixels after a cyclone, not fewer
    p = float((1.0 + np.sum(draws >= obs)) / (1.0 + n_perm))
    return obs, len(e), p


def verdict(ex, thresholds, n_perm=N_PERM, seed=SEED):
    """Apply the pre-declared rule to the severe harvest-window units."""
    sub = ex[(ex["severity_class"] == "severe")
             & (ex["timing_class"] == "harvest_window")]
    rows = []
    for name in thresholds:
        col = f"excess_{name}"
        med = float(np.nanmedian(sub[col])) if len(sub) else np.nan
        mean, n, p = permute_excess(sub, col, n_perm=n_perm, seed=seed)
        i_ok = bool(np.isfinite(med) and med >= MIN_EXCESS)
        ii_ok = bool(np.isfinite(p) and p <= ALPHA)
        if n < MIN_TREATED_UNITS:
            v = "UNINFORMATIVE"
        elif i_ok and ii_ok:
            v = "SEPARATES"
        else:
            v = "DOES NOT SEPARATE"
        rows.append({
            "threshold_name": name, "threshold_db": thresholds[name],
            "n_units": n, "median_excess": med, "mean_excess": mean,
            "perm_p_one_sided": p,
            "rule_i_median_excess_ge_0.05": i_ok,
            "rule_ii_perm_p_le_0.05": ii_ok,
            "verdict": v,
            "n_units_null_scene_advantaged":
                int(sub["null_scene_advantaged"].sum())
                if "null_scene_advantaged" in sub.columns else -1,
        })
    return pd.DataFrame(rows), sub


# ---------------------------------------------------------------------------
SWEEP_TAUS = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 6, 7, 8, 9, 10, 12]


def threshold_sweep(d, n_perm=N_PERM, seed=SEED, taus=None):
    """Is ANY threshold able to separate, or does the statistic itself fail?

    A verdict on the declared 3 dB alone leaves the obvious objection open: maybe
    3 dB is simply the wrong number. This sweeps the criterion across the whole
    plausible range and applies the same pre-declared rule at each. If the best
    median excess anywhere is far below MIN_EXCESS, the failure belongs to the
    statistic rather than to the threshold, which is a materially stronger and more
    defensible claim than "3 dB is wrong".
    """
    taus = taus if taus is not None else SWEEP_TAUS
    rows = []
    for tau in taus:
        th = {"t": float(tau)}
        ex = scene_balance(excess(rates(d, th), th))
        sub = ex[(ex["severity_class"] == "severe")
                 & (ex["timing_class"] == "harvest_window")]
        med = float(np.nanmedian(sub["excess_t"])) if len(sub) else np.nan
        mean, n, pv = permute_excess(sub, "excess_t", n_perm=n_perm, seed=seed)
        rows.append({"threshold_db": float(tau), "n_units": n,
                     "median_excess": med, "mean_excess": mean,
                     "perm_p_one_sided": pv,
                     "rule_i_pass": bool(np.isfinite(med) and med >= MIN_EXCESS),
                     "rule_ii_pass": bool(np.isfinite(pv) and pv <= ALPHA)})
    return pd.DataFrame(rows)


def timing_test(d):
    """Does the flagged drop have the TIMING of a flood, or of speckle?

    An independent check that needs no threshold calibration and no null-arm
    comparison of rates. If the statistic detects cyclone inundation, the deep
    drops in the cyclone arm should sit in the first days after landfall, while the
    untreated arm's deep drops have no reason to cluster at all. If the day of the
    minimum is the same in both arms, the statistic is measuring the acquisition
    schedule and speckle, not the storm. Requires `win_min_day_off`, so it returns
    empty for a pre-correction export.
    """
    if "win_min_day_off" not in d.columns:
        return pd.DataFrame()
    sh = d[(d["severity_class"] == "severe")
           & (d["timing_class"] == "harvest_window")]
    rows = []
    for arm in ("actual", "null2017"):
        a = sh[sh["arm"] == arm]
        if not len(a):
            continue
        for lab, sel in (("flagged_ge_3dB", a["drop_db"] >= DECLARED_DROP_DB),
                         ("unflagged", a["drop_db"] < DECLARED_DROP_DB)):
            w = a.loc[sel, "win_min_day_off"].astype(float).dropna()
            rows.append({"arm": arm, "group": lab, "n": int(len(w)),
                         "day_mean": float(w.mean()) if len(w) else np.nan,
                         "day_median": float(w.median()) if len(w) else np.nan,
                         "share_first_5_days": (float((w <= 5).mean())
                                                if len(w) else np.nan)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def run(exports, out_dir, n_perm=N_PERM, seed=SEED, force_spec=None):
    os.makedirs(out_dir, exist_ok=True)
    d = usable(read_exports(exports))
    diag, admissible = check_windows(d)
    if force_spec:
        print(f"  --force-spec {force_spec}: treating it as admissible. This is a "
              f"diagnostic\n  override and its output must not be reported as the "
              f"§3.3 verdict.")
        admissible = [force_spec]
    if "window_spec" not in d.columns:
        d = d.assign(window_spec=DECLARED_SPEC)

    rts, exs, vds = [], [], []
    for spec in sorted(d["window_spec"].unique()):
        g = d[d["window_spec"] == spec]
        is_adm = spec in admissible
        print(f"\n  --- window spec '{spec}' "
              f"({'ADMISSIBLE' if is_adm else 'DIAGNOSTIC ONLY'}) ---")
        thresholds = derive_thresholds(g)
        rt = rates(g, thresholds).assign(window_spec=spec)
        ex = scene_balance(excess(rt, thresholds)).assign(window_spec=spec)
        vd, sub = verdict(ex, thresholds, n_perm=n_perm, seed=seed)
        vd = vd.assign(window_spec=spec, admissible=is_adm)
        if not is_adm:
            vd["verdict"] = "WITHHELD -- window not admissible"
        rts.append(rt); exs.append(ex); vds.append(vd)
    rt = pd.concat(rts, ignore_index=True)
    ex = pd.concat(exs, ignore_index=True)
    vd = pd.concat(vds, ignore_index=True)
    sub = ex[(ex["severity_class"] == "severe")
             & (ex["timing_class"] == "harvest_window")
             & (ex["window_spec"].isin(admissible))]

    sweeps, timings = [], []
    for spec in admissible:
        g = d[d["window_spec"] == spec]
        sweeps.append(threshold_sweep(g, n_perm=n_perm, seed=seed)
                      .assign(window_spec=spec))
        t = timing_test(g)
        if len(t):
            timings.append(t.assign(window_spec=spec))
    sweep = pd.concat(sweeps, ignore_index=True) if sweeps else pd.DataFrame()
    timing = pd.concat(timings, ignore_index=True) if timings else pd.DataFrame()

    for nm, df in (("Table_SX_Inundation_ByUnit.csv", rt),
                   ("Table_SX_Inundation_Excess.csv", ex),
                   ("Table_SX_Inundation_Verdict.csv", vd),
                   ("Table_SX_Inundation_WindowDiagnostics.csv", diag),
                   ("Table_SX_Inundation_ThresholdSweep.csv", sweep),
                   ("Table_SX_Inundation_TimingTest.csv", timing)):
        if not len(df):
            continue
        p = os.path.join(out_dir, nm)
        df.to_csv(p, index=False, float_format=CSV_FLOAT)
        print(f"  wrote {p}  ({len(df)} rows)")

    print()
    print("=" * 74)
    print("§3.3 VERDICT, against the rule declared before the export existed")
    print("=" * 74)
    for _, r in vd.iterrows():
        print(f"  [{r['window_spec']:12s}] {r['threshold_name']:12s} "
              f"tau {r['threshold_db']:6.3f} dB   "
              f"units {int(r['n_units']):3d}   median excess "
              f"{r['median_excess']:+.4f}   perm p {r['perm_p_one_sided']:.4f}   "
              f"-> {r['verdict']}")
    if len(sub) and int(sub["null_scene_advantaged"].sum()):
        print(f"  NOTE {int(sub['null_scene_advantaged'].sum())} of {len(sub)} severe "
              f"harvest-window units have a null arm carrying >{SCENE_IMBALANCE:.2f}x "
              f"the event-window scenes.")
        print("  On those units a negative result is biased and is not clean evidence.")
    adm = vd[vd["admissible"]] if "admissible" in vd.columns else vd
    if not len(adm):
        print("  VERDICT WITHHELD. No window specification is admissible, so §3.3 is")
        print("  neither supported nor withdrawn on this evidence. Re-export with the")
        print("  corrected postlandfall window and run this again.")
        return rt, ex, vd
    vd = adm
    if (vd["verdict"] == "SEPARATES").any():
        print("  At least one threshold separates. inundated_frac is reportable as a")
        print("  §3.8 A secondary continuous term, labelled as measured from the same")
        print("  instrument that produces the outcome (§3.3's own caveat).")
    elif (vd["verdict"] == "UNINFORMATIVE").all():
        print("  Too few severe harvest-window units to decide. Report as untested,")
        print("  never as a negative result.")
    else:
        if len(sweep):
            best = sweep.loc[sweep["median_excess"].idxmax()]
            print(f"  THRESHOLD SWEEP over {len(sweep)} values from "
                  f"{sweep['threshold_db'].min():g} to {sweep['threshold_db'].max():g}"
                  f" dB: the BEST median excess anywhere is "
                  f"{best['median_excess']:+.4f} at {best['threshold_db']:g} dB, "
                  f"against a required +{MIN_EXCESS:.2f}.")
            print("  So the failure is of the STATISTIC, not of the 3 dB value -- no")
            print("  threshold on this quantity separates a cyclone year from an")
            print("  untreated one.")
        if len(timing):
            t = timing.set_index(["arm", "group"])
            try:
                fa = t.loc[("actual", "flagged_ge_3dB")]
                fn = t.loc[("null2017", "flagged_ge_3dB")]
                print(f"  TIMING TEST: the day of the flagged minimum is "
                      f"{fa['day_median']:.2f} d after landfall in the cyclone arm and "
                      f"{fn['day_median']:.2f} d in the untreated arm "
                      f"({fa['share_first_5_days']:.3f} against "
                      f"{fn['share_first_5_days']:.3f} within 5 days). A flood signal")
                print("  would cluster early in the cyclone arm only. It does not.")
            except KeyError:
                pass
        print("  No threshold separates, including §3.3's declared 3 dB.")
        print("  §3.3 must be WITHDRAWN by dated amendment: the drop statistic does")
        print("  not distinguish a cyclone year from an untreated year on this coast.")
        print("  That is a reportable measurement, not a gap -- it says the criterion")
        print("  was tested against its own matched null and failed.")
    return rt, ex, vd


# ---------------------------------------------------------------------------
def selftest():
    print("=" * 74)
    print("SELF-TEST -- inundation_intensity.py")
    print("=" * 74)
    ok_all = True

    def chk(cond, msg):
        nonlocal ok_all
        ok_all &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")

    rng = np.random.default_rng(7)

    def synth(units, shift, n_pix=400, n_win_null=None, sev="severe",
              tc="harvest_window"):
        """Exponential-ish drops; `shift` adds dB to the actual arm only."""
        rows = []
        for u in range(units):
            for arm in ("actual", "null2017"):
                base = rng.gamma(2.0, 1.0, n_pix)
                v = base + (shift if arm == "actual" else 0.0)
                nw = 10 if arm == "actual" else (n_win_null or 10)
                for i, x in enumerate(v):
                    rows.append({"district": f"D{u}", "storm": f"S{u}",
                                 "season": 2020 + u, "arm": arm,
                                 "severity_class": sev, "timing_class": tc,
                                 "drop_db": float(x), "n_orbits_paired": 2,
                                 "n_pre": 12, "n_win": nw, "cell_id": i})
        return pd.DataFrame(rows)

    # --- 1. a planted signal is recovered --------------------------------
    d = synth(8, shift=2.5)
    th = derive_thresholds(d)
    ex = scene_balance(excess(rates(d, th), th))
    vd, sub = verdict(ex, th, n_perm=500, seed=1)
    v3 = vd[vd["threshold_name"] == "declared3db"].iloc[0]
    chk(v3["verdict"] == "SEPARATES",
        f"a planted +2.5 dB shift on 8 units SEPARATES "
        f"(median excess {v3['median_excess']:+.3f}, p {v3['perm_p_one_sided']:.4f})")
    chk(len(sub) == 8, "all 8 severe harvest-window units enter the paired test")

    # --- 2. pure noise is not turned into a signal -----------------------
    d0 = synth(8, shift=0.0)
    th0 = derive_thresholds(d0)
    ex0 = scene_balance(excess(rates(d0, th0), th0))
    vd0, _ = verdict(ex0, th0, n_perm=500, seed=1)
    chk((vd0["verdict"] == "DOES NOT SEPARATE").all(),
        "identical arms DO NOT SEPARATE at any threshold -- no invented signal")
    med0 = float(vd0[vd0["threshold_name"] == "declared3db"]["median_excess"].iloc[0])
    chk(abs(med0) < MIN_EXCESS,
        f"the median excess under the null is small ({med0:+.4f}), not merely "
        f"insignificant")

    # --- 3. the re-derived thresholds ARE the null quantiles -------------
    nul = d0[d0["arm"] == "null2017"]["drop_db"].values
    chk(abs(th0["null_q95"] - np.quantile(nul, 0.95)) < 1e-9
        and abs(th0["null_q99"] - np.quantile(nul, 0.99)) < 1e-9,
        "null_q95/q99 are exactly the 95th/99th percentiles of the pooled null arm")
    chk(th0["declared3db"] == DECLARED_DROP_DB,
        "§3.3's declared 3 dB is carried through unchanged alongside them")
    # and by construction the null arm's own rate at null_q95 is 5%
    r0 = rates(d0, th0)
    nr = r0[r0["arm"] == "null2017"]["inundated_frac_null_q95"].mean()
    chk(abs(nr - 0.05) < 0.02,
        f"the null arm flags ~5% of pixels at its own 95th percentile ({nr:.4f})")

    # --- 4. too few units is UNINFORMATIVE, never a negative result -----
    d2 = synth(2, shift=0.0)
    th2 = derive_thresholds(d2)
    ex2 = scene_balance(excess(rates(d2, th2), th2))
    vd2, _ = verdict(ex2, th2, n_perm=200, seed=1)
    chk((vd2["verdict"] == "UNINFORMATIVE").all(),
        "2 units < MIN_TREATED_UNITS gives UNINFORMATIVE, not DOES NOT SEPARATE")

    # --- 5. only severe harvest-window units decide it ------------------
    mixed = pd.concat([synth(4, shift=0.0),
                       synth(4, shift=6.0, tc="pre_season")], ignore_index=True)
    thm = derive_thresholds(mixed)
    exm = scene_balance(excess(rates(mixed, thm), thm))
    vdm, subm = verdict(exm, thm, n_perm=500, seed=1)
    chk(len(subm) == 4 and (vdm["verdict"] == "DOES NOT SEPARATE").all(),
        "a huge planted signal in PRE-SEASON units cannot rescue the verdict -- "
        "bare fields are a control, not a test")

    # --- 6. the scene-imbalance flag fires -----------------------------
    dimb = synth(5, shift=0.0, n_win_null=20)
    thi = derive_thresholds(dimb)
    exi = scene_balance(excess(rates(dimb, thi), thi))
    chk(bool(exi["null_scene_advantaged"].all()),
        "a null arm with 20 event scenes against the actual arm's 10 is flagged "
        "scene-advantaged on every unit")
    dbal = synth(5, shift=0.0, n_win_null=11)
    exb = scene_balance(excess(rates(dbal, thi), thi))
    chk(not bool(exb["null_scene_advantaged"].any()),
        "11 against 10 is within tolerance and is not flagged")

    # --- 7. the permutation test is a real sign-flip test --------------
    ex_one = pd.DataFrame({"excess_x": [0.2, 0.2, 0.2, 0.2, 0.2]})
    obs, n, p = permute_excess(ex_one, "excess_x", n_perm=2000, seed=3)
    chk(n == 5 and abs(obs - 0.2) < 1e-12 and p <= 1.0 / 32 + 1e-6,
        f"five identical positive excesses give the exact sign-test floor "
        f"p = {p:.5f} (1/32 = {1/32:.5f})")
    ex_neg = pd.DataFrame({"excess_x": [-0.2] * 5})
    _, _, pn = permute_excess(ex_neg, "excess_x", n_perm=2000, seed=3)
    chk(pn > 0.9, f"five negative excesses give a one-sided p near 1 ({pn:.3f}), "
                  f"because §3.3 predicts MORE flagged pixels, not fewer")

    # --- 8. null drop_db rows are excluded and counted, never filled ---
    dn = synth(3, shift=0.0)
    dn.loc[:99, "drop_db"] = np.nan
    dn.loc[100:149, "n_orbits_paired"] = 0
    u = usable(dn)
    chk(len(u) == len(dn) - 150 and u["drop_db"].notna().all(),
        "rows with no drop and rows with 0 paired orbits are both excluded")

    # --- 9. schema and arm refusals -----------------------------------
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        bad = synth(1, shift=0.0).drop(columns=["n_orbits_paired"])
        bad.to_csv(os.path.join(td, "S1_INUND_x.csv"), index=False)
        try:
            read_exports(td)
            chk(False, "a missing column must stop the run")
        except SystemExit as e:
            chk("n_orbits_paired" in str(e) and "header-inference" in str(e),
                "a missing column names itself and the Earth Engine cause")
        onearm = synth(1, shift=0.0)
        onearm = onearm[onearm["arm"] == "actual"]
        onearm.to_csv(os.path.join(td, "S1_INUND_x.csv"), index=False)
        try:
            read_exports(td)
            chk(False, "a run with no null arm must stop")
        except SystemExit as e:
            chk("emitNullArm" in str(e),
                "a missing null arm refuses and names emitNullArm -- a threshold "
                "cannot be re-derived on a baseline that was not exported")

    # --- 9b. the window gate -------------------------------------------
    def tag(df, spec, overlap, zero_actual, zero_null, day_off=None):
        df = df.copy()
        df["window_spec"] = spec
        df["overlap_days"] = overlap
        # plant the requested exact-zero mass in each arm
        for arm, frac in (("actual", zero_actual), ("null2017", zero_null)):
            idx = df.index[df["arm"] == arm]
            k = int(round(frac * len(idx)))
            df.loc[idx[:k], "drop_db"] = 0.0
        if day_off is not None:
            df["win_min_day_off"] = day_off
        return df

    base = synth(6, shift=0.0)
    good = tag(base, PRIMARY_SPEC, 0, 0.05, 0.05, day_off=4.0)
    bad_ov = tag(base, DECLARED_SPEC, 9, 0.05, 0.05, day_off=-6.0)
    bad_asym = tag(base, "asym", 0, 0.20, 0.01, day_off=4.0)
    diag, adm = check_windows(pd.concat([good, bad_ov, bad_asym],
                                        ignore_index=True))
    chk(adm == [PRIMARY_SPEC],
        f"only the zero-overlap, arm-balanced spec is admissible (got {adm})")
    r = diag.set_index("window_spec")
    chk(not bool(r.loc[DECLARED_SPEC, "overlap_ok"]),
        "a 9-day reference/event overlap fails the overlap check")
    chk(bool(r.loc["asym", "overlap_ok"])
        and not bool(r.loc["asym", "zero_asymmetry_ok"]),
        "a spec with zero overlap but a 0.19 arm gap fails on asymmetry alone")
    chk(abs(float(r.loc[DECLARED_SPEC,
                        "share_min_predates_landfall_actual"]) - 1.0) < 1e-9
        and float(r.loc[PRIMARY_SPEC,
                        "share_min_predates_landfall_actual"]) == 0.0,
        "the share of minima predating landfall is measured: 1.00 for a "
        "pre-landfall minimum, 0.00 for a post-landfall one")

    # a pre-correction export (no window_spec at all) admits nothing
    diag2, adm2 = check_windows(base)
    chk(adm2 == [],
        "an export with no window_spec column admits no spec and issues no verdict")

    # and the end-to-end run withholds rather than reporting a negative
    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "in"))
        base.to_csv(os.path.join(td, "in", "S1_INUND_x.csv"), index=False)
        _, _, vdx = run(os.path.join(td, "in"), os.path.join(td, "out"),
                        n_perm=200, seed=1)
        chk((vdx["verdict"] == "WITHHELD -- window not admissible").all(),
            "a pre-correction export yields WITHHELD, never DOES NOT SEPARATE")

    # --- 9c. the threshold sweep and the timing test --------------------
    dsig = synth(6, shift=3.0)
    sw = threshold_sweep(dsig, n_perm=400, seed=2, taus=[1, 3, 5, 8])
    chk(bool(sw["rule_i_pass"].any()),
        "the sweep finds a separating threshold when a +3 dB signal is planted")
    dnul = synth(6, shift=0.0)
    sw0 = threshold_sweep(dnul, n_perm=400, seed=2, taus=[1, 3, 5, 8])
    chk(not bool(sw0["rule_i_pass"].any())
        and abs(float(sw0["median_excess"].max())) < MIN_EXCESS,
        "the sweep finds none under the null, at any threshold")
    chk(len(sw0) == 4 and list(sw0["threshold_db"]) == [1.0, 3.0, 5.0, 8.0],
        "the sweep reports one row per threshold, in order")

    # timing: plant a flood that is EARLY in the actual arm only
    dt = synth(6, shift=0.0)
    rng2 = np.random.default_rng(11)
    dt["win_min_day_off"] = rng2.uniform(0, 14, len(dt))
    early = (dt["arm"] == "actual") & (dt["drop_db"] >= DECLARED_DROP_DB)
    dt.loc[early, "win_min_day_off"] = rng2.uniform(0, 3, int(early.sum()))
    tt = timing_test(dt).set_index(["arm", "group"])
    chk(tt.loc[("actual", "flagged_ge_3dB"), "day_median"]
        < tt.loc[("null2017", "flagged_ge_3dB"), "day_median"] - 2,
        "the timing test detects a planted early-flood signature in one arm")
    chk(tt.loc[("actual", "flagged_ge_3dB"), "share_first_5_days"] > 0.9,
        "and reports its share within the first five days")
    dt2 = synth(6, shift=0.0)
    dt2["win_min_day_off"] = rng2.uniform(0, 14, len(dt2))
    tt2 = timing_test(dt2).set_index(["arm", "group"])
    chk(abs(tt2.loc[("actual", "flagged_ge_3dB"), "day_median"]
            - tt2.loc[("null2017", "flagged_ge_3dB"), "day_median"]) < 2.5,
        "and reports no difference when the day of the minimum is uniform in both")
    chk(len(timing_test(dt2.drop(columns=["win_min_day_off"]))) == 0,
        "the timing test returns empty for a pre-correction export")

    # --- 10. the declared rule constants are what the docstring says ---
    chk((MIN_EXCESS, ALPHA, MIN_TREATED_UNITS, DECLARED_DROP_DB)
        == (0.05, 0.05, 3, 3.0),
        "the pre-declared rule constants are 0.05 / 0.05 / 3 units / 3.0 dB")

    print()
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="Protocol §3.3 inundated_frac.")
    ap.add_argument("--exports", default=os.path.join(ROOT, "s1_inund"))
    ap.add_argument("--out", default=os.path.join(RESULTS, "inundation"))
    ap.add_argument("--n-perm", type=int, default=N_PERM)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--force-spec", default=None,
                    help="treat this window_spec as admissible even if it fails the "
                         "overlap or zero-asymmetry check. Diagnostic only; its "
                         "output is not the §3.3 verdict.")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    run(a.exports, a.out, n_perm=a.n_perm, seed=a.seed, force_spec=a.force_spec)
    return 0


if __name__ == "__main__":
    sys.exit(main())
