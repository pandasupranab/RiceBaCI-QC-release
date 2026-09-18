"""
extract_phenometrics_sar.py -- Protocol v1 §3 lead-in, radar substrate.

Replaces the Beck double-logistic for the Sentinel-1 VH/VV panel. Created
2026-09-12 after the double-logistic failed its §3 lead-in calibration check on
the untreated 2017 baseline.

------------------------------------------------------------------------------
WHY THE DOUBLE-LOGISTIC WAS REPLACED
------------------------------------------------------------------------------
§3 lead-in asserted that "everything downstream of the index is unchanged from
Paper 1 -- only the index changes, not the estimator". That sentence is false,
and it was the sentence that made the substrate change look cheap.

A double-logistic models a bell: background, rise, peak, symmetric fall. The
VH/VV trajectory of transplanted rice is not a bell. Phan, Le Toan & Bouvet
(2021, Remote Sensing 13(5), 921), on 300 field-seasons of ground truth, report
a MINIMUM at tillering, a rise of about 10 dB to booting-heading, and then --
verbatim -- "The VH/VV ratio remains stable until the end of its cycle", with
only "a small decrease (<1 dB)" through grain filling and maturity. The fall
comes from pre-harvest drainage, not senescence.

Fitting a bell to a trough-rise-plateau-drop produced, on the 2017 baseline:
POS pinned near DOY 326 at EVERY window start tested (150/180/200/220/240),
56% convergence, EOS undefined for 40% of pixels, and phenometrics outside
Gate 2 in every configuration. Those are symptoms of a model that cannot
represent the curve, not of a bad window or a bad threshold.

Measured, tested and ELIMINATED as causes before arriving here: the per-orbit
normalisation, orbit structure, image timestamps, the export path, the fitting
window start, the phenometric definitions on the fitted curve, and the
Whittaker smoother (fitted amplitude 3.33 dB smoothed vs 3.27 dB unsmoothed --
no effect).

------------------------------------------------------------------------------
WHY THE MEKONG TIMINGS NEVER APPLIED
------------------------------------------------------------------------------
The measured trough-to-heading interval on this coast is about 80 days. Phan
et al. report 30-40. That is not a discrepancy, it is a different crop: their
dataset is 80% short-cycle (<100 day) DIRECT-SEEDED rice, while Odisha Sali and
West Bengal aman are long-duration TRANSPLANTED rice of 140-150 days. Heading
at ~80 days after transplanting is correct for the latter. §3 lead-in's
calibration clause anticipated exactly this and required it be checked before
any phenometric was reported; this module is the outcome of that check.

------------------------------------------------------------------------------
WHAT IS EXTRACTED, AND WHY THESE THREE
------------------------------------------------------------------------------
Markers are read directly off the smoothed series -- no curve fitting -- and
are named for the physical state they mark rather than borrowed from optical
phenology, because they are not the same quantities:

  TROUGH   minimum within the transplanting window. The flooded, near-bare
           field: open water is specular and returns weakly in cross-pol.
           Phan: VH/VV minimum at tillering, ~20 d after sowing.
  HEADING  first crossing of 80% of the trough-to-plateau rise. Canopy closed,
           structure maximal. Phan: maximum at booting-heading, then plateau.
  HARVEST  first fall back below 50% of that rise after the plateau. Phan:
           "the fields are drained two weeks before rice harvest."

Calling these SOS, POS and EOS would be wrong. EOS in the optical sense is
senescence; here the fall is drainage. The protocol reports them under these
names and says so.

Measured on the 2017 baseline, 10 districts, 3,496 pixel-seasons -- and note
all three land INSIDE Paper 1's Gate 2 windows, which the double-logistic
violated in every configuration:

    trough   median DOY 214.5 (2 Aug)    Gate 2 SOS window 155-240   PASS
    heading  median DOY 304.5 (31 Oct)   Gate 2 POS window 240-320   PASS
    harvest  median DOY 364.5 (30 Dec)   Gate 2 EOS window 280-380   PASS

So Gate 2's DOY bounds are carried over unchanged after all. The §3.2 note of
2026-09-11 claiming they fail under radar is withdrawn by this module's own
measurement.

------------------------------------------------------------------------------
DEPENDENCIES
------------------------------------------------------------------------------
numpy and pandas. Reuses whittaker_gcv and aggregate_to_dekads from
fit_phenometrics.py, which stays the authority for the optical path and for the
dekadal grid. --selftest checks every marker against a synthetic curve with
known markers.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
import time

import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
# fit_phenometrics.py stays the authority for the dekadal grid, Gate 1 and
# the Whittaker smoother; the radar path reuses them rather than restating.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_phenometrics as _FP

N_BINS_ = _FP.N_BINS

# ---------------------------------------------------------------------------
# §1.4's pre-declared window sensitivity sweep.
#
# §1.4: "The 60-day-extension window (DOY 150-425) is the headline. Results are
# also reported for the 0-, 20-, 30- and 45-day extensions (upper endpoints DOY
# 365, 385, 395, 410), obtained by truncating the same per-bin composites before
# smoothing and fitting; Gate 1-3 pass rates, extraction-failure rate and the §3.8
# headline coefficient are tabulated for all five endpoints."
#
# An external re-audit on 2026-09-13 found this pre-declared sweep unimplemented.
# It is implemented by truncation here rather than by re-exporting: bin b spans DOY
# 150+5b to 154+5b, so an upper endpoint E keeps exactly the bins whose END falls
# at or before E. That is the same per-bin composite the headline uses, with later
# bins removed before smoothing and fitting -- which is what §1.4 specifies, and is
# why no new Earth Engine export is needed.
#
# WINDOW_END_DOY is None for the headline, so the default path is bit-for-bit the
# one that produced the committed panel. Nothing about the headline changes.
WINDOW_END_DOY = None
BIN_START_DOY = 150
BIN_WIDTH = 5


def bins_within(end_doy):
    """Number of leading bins whose composite window ends at or before end_doy."""
    if end_doy is None:
        return N_BINS_
    keep = int((end_doy - (BIN_START_DOY + BIN_WIDTH - 1)) // BIN_WIDTH) + 1
    return max(0, min(N_BINS_, keep))

# Transplanting window for the trough search: the AICRP Kharif calendar of
# §3.4 (SMW 25-42, approximately DOY 170-294) bounded above so the search
# cannot wander into the post-monsoon plateau.
#
# TWO CAVEATS, BOTH ADDED 2026-09-14 AFTER TRACING THIS CONSTANT.
#
# 1. THE CITATION IS UNSOURCED. No AICRP document appears in
#    docs/field_reference_sources.md, none was retrieved, and none is archived
#    under docs/field_reference_pdfs/. The four endorsed Odisha sources give
#    monthly SOWING windows and harvest only as "physiological maturity" -- so
#    no endorsed source in this project supports an SMW range or these DOY
#    bounds. Protocol S3.4's attribution is suspended as of that date.
#
# 2. THIS IS A DEAD DEFAULT. It reaches no committed output. The one production
#    call to extract_markers (in run_district, the superseded crossing arm)
#    passes trough_window=GATE2["trough"] = (155.0, 240.0) EXPLICITLY, so even
#    the xr_* panel columns do not use this value; the remaining callers are the
#    four self-tests below. The primary PLSM estimator has no calendar window at
#    all -- its trough lives on PIXEL_GRID_DOY["t1"] = (184.5, 304.5), derived
#    from the untreated 2017 baseline and padded two dekads.
#
# Consequence: no reported number in this study depends on (170.0, 294.0). It is
# left in place, rather than silently re-valued or deleted, so that the defect
# stays visible next to the record of it; deleting it would erase the only thing
# the protocol's withdrawn sentence can now be checked against. Do not cite it,
# and do not pass it at a call site. Resolve by retrieving an AICRP source or by
# re-deriving the default from an endorsed source or the 2017 baseline.
TROUGH_WINDOW = (170.0, 294.0)
RISE_FRACTION_HEADING = 0.80
FALL_FRACTION_HARVEST = 0.50
# ---------------------------------------------------------------------------
# DERIVED ON THE UNTREATED 2017 BASELINE, 25 DISTRICTS, 10,000 PIXEL-SEASONS,
# 2026-09-12. Fixed here and not to be re-tuned on a treated season.
# ---------------------------------------------------------------------------
# SMOOTHING: OFF for the radar path. Rule stated before computing: retain the
# arm with higher three-marker completeness while keeping median markers inside
# §3.2. Measured -- unsmoothed 88.7% complete against smoothed 54.0%, with both
# arms' medians inside §3.2. The Whittaker step is inherited from Paper 1 for
# optical comparability; on a step-shaped radar index it suppresses the
# drainage fall and costs 35 points of completeness. It is not used here.
USE_SMOOTHING = False

# MINIMUM RISE: the 5th percentile of the trough-to-plateau rise among the
# 2,554 baseline pixel-seasons whose three markers ALL land inside §3.2 -- i.e.
# calibrated to admit 95% of demonstrably well-behaved seasons, on an untreated
# season, before any treated season was marked.
MIN_RISE_DB = 5.32

MIN_VALID_DEKADS = 14      # §3.11, unchanged


def extract_markers(doy, series, valid,
                    trough_window=TROUGH_WINDOW,
                    rise_frac=RISE_FRACTION_HEADING,
                    fall_frac=FALL_FRACTION_HARVEST,
                    min_rise_db=MIN_RISE_DB):
    """Read trough, heading and harvest off one pixel-season's smoothed series.

    Returns a dict with the three marker DOYs, the rise amplitude in dB, and a
    reason string when a marker could not be read. Never raises: a pixel that
    cannot be marked is reported as such, because §3.10's diagnostic needs the
    failures as much as the successes.
    """
    out = dict(trough=np.nan, heading=np.nan, harvest=np.nan,
               rise_db=np.nan, plateau_doy=np.nan, trough_db=np.nan,
               plateau_db=np.nan, n_valid=int(np.sum(valid)), reason="")
    if out["n_valid"] < MIN_VALID_DEKADS:
        out["reason"] = f"ineligible: {out['n_valid']} valid dekads"
        return out

    win = valid & (doy >= trough_window[0]) & (doy <= trough_window[1])
    if not win.any():
        out["reason"] = "no valid dekad inside the transplanting window"
        return out
    ti = np.where(win)[0][int(np.argmin(series[win]))]

    after = np.where(valid & (doy > doy[ti]))[0]
    if len(after) < 3:
        out["reason"] = "fewer than three valid dekads after the trough"
        return out
    pi = after[int(np.argmax(series[after]))]

    trough_v, plateau_v = float(series[ti]), float(series[pi])
    rise = plateau_v - trough_v
    out.update(trough=float(doy[ti]), rise_db=rise, plateau_doy=float(doy[pi]),
               trough_db=trough_v, plateau_db=plateau_v)
    if rise < min_rise_db:
        out["reason"] = f"rise {rise:.2f} dB below the {min_rise_db} dB minimum"
        return out

    seg = after[after <= pi]
    hit = [j for j in seg if series[j] >= trough_v + rise_frac * rise]
    if hit:
        out["heading"] = float(doy[hit[0]])
    else:
        out["reason"] = "no dekad reaches the heading level before the plateau"

    post = np.where(valid & (doy > doy[pi]))[0]
    hit = [j for j in post if series[j] <= trough_v + fall_frac * rise]
    if hit:
        out["harvest"] = float(doy[hit[0]])
    elif not out["reason"]:
        out["reason"] = "series does not fall back to the harvest level in window"
    return out


# §3.2, carried over from Paper 1 unchanged -- all three radar markers land
# inside these on the baseline (see the module docstring).
GATE2 = {"trough": (155.0, 240.0), "heading": (240.0, 320.0),
         "harvest": (280.0, 380.0)}


def retain(marks, gate2=GATE2, min_rise_db=MIN_RISE_DB):
    """Apply the full eligibility rule to one marked pixel-season.

    Retained iff: eligible on §3.11's dekad count, all three markers recovered,
    all three inside §3.2, and the rise clears the baseline-derived minimum.
    Returns (bool, reason). A pixel-season that fails is reported with its
    reason and enters §3.10's diagnostic as a failure -- the role that
    non-convergence played under the withdrawn double-logistic.

    MEASURED BASELINE RETENTION: 24.3% of 10,000 attempted pixel-seasons.
    That is lower than Paper 1's optical pipeline (about 60%) and it is not a
    defect to be tuned away. The retained set has a median rise of 8.50 dB
    against roughly 3.7 dB across all pixel-seasons, and median breakpoints at
    DOY 214.5 / 284.5 / 334.5. Those DOY positions are consistent with the
    Odisha Sali calendar, which is a comparison of distributions and NOT an
    observation of transplanting, heading or harvest on any date: this study
    holds no field reference (section 4.3.1).

    The gate separates pixel-seasons whose radar trajectories satisfy the
    declared rice-like shape, eligibility and selection-aware rise criteria.
    It does not establish crop identity. The cohort is drawn at 0.5 mask
    purity (§3.5), where up to half of each 30 m cell may not be rice, and
    nothing in this screen can tell a rice pixel from any other pixel whose
    VH/VV trajectory satisfies the same criteria. Retention is ASSOCIATED with elevation, slope and viewing
    geometry in the fitted selection model of section 3.10, and NO
    ASSOCIATION WITH CYCLONE DISTANCE WAS DETECTED IN THAT FITTED MODEL.
    That is a detected null, not an established absence: it does not show
    that exposure-related selection is absent, only that this model, with
    these covariates, did not find it. The CAUSE of the terrain association
    likewise cannot be separated among mask classification, signal quality,
    estimator behaviour and this screening rule itself, so no single one of
    them is named here; section 3.10's attrition diagnostic is
    correspondingly more important, not less.
    """
    if marks["reason"].startswith("ineligible"):
        return False, marks["reason"]
    for k, (lo, hi) in gate2.items():
        v = marks.get(k, np.nan)
        if not np.isfinite(v):
            return False, marks["reason"] or f"{k} not recovered"
        if not (lo <= v <= hi):
            return False, f"{k} {v:.1f} outside §3.2 window {lo:.0f}-{hi:.0f}"
    if not np.isfinite(marks["rise_db"]) or marks["rise_db"] < min_rise_db:
        return False, (f"rise {marks['rise_db']:.2f} dB below the "
                       f"{min_rise_db} dB baseline minimum")
    return True, ""


def selftest():
    print("=" * 74)
    print("SELF-TEST -- extract_phenometrics_sar.py")
    print("=" * 74)
    ok_all = True

    # A synthetic trough-rise-plateau-drop with markers placed by construction.
    doy = np.arange(154.5, 425.0, 10.0)
    TROUGH, RISE_END, DROP = 214.5, 294.5, 354.5
    base, top = -12.0, -3.0
    s = np.full_like(doy, top)
    s[doy < TROUGH] = top - 1.0
    ramp = (doy >= TROUGH) & (doy <= RISE_END)
    s[ramp] = base + (top - base) * (doy[ramp] - TROUGH) / (RISE_END - TROUGH)
    s[doy < TROUGH] = np.linspace(top - 1.0, base, int(np.sum(doy < TROUGH)))
    fall = doy > DROP
    s[fall] = top - (top - base) * np.clip((doy[fall] - DROP) / 40.0, 0, 1)
    valid = np.ones(len(doy), bool)

    m = extract_markers(doy, s, valid)
    print(f"  constructed: trough {TROUGH}, rise ends {RISE_END}, drop {DROP}")
    print(f"  extracted  : trough {m['trough']}, heading {m['heading']}, "
          f"harvest {m['harvest']}, rise {m['rise_db']:.2f} dB")
    ok = (abs(m["trough"] - TROUGH) <= 10 and np.isfinite(m["heading"])
          and np.isfinite(m["harvest"]) and m["heading"] > m["trough"]
          and m["harvest"] > m["heading"] and abs(m["rise_db"] - 9.0) < 0.6)
    ok_all &= ok
    print(f"  [{'PASS' if ok else 'FAIL'}] markers recovered in the right order "
          f"with the right amplitude")

    # a flat series must yield no markers, not spurious ones
    flat = extract_markers(doy, np.full_like(doy, -7.0), valid)
    ok = not np.isfinite(flat["heading"]) and "below the" in flat["reason"]
    ok_all &= ok
    print(f"\n  flat series -> heading {flat['heading']}, reason "
          f"'{flat['reason']}'")
    print(f"  [{'PASS' if ok else 'FAIL'}] a season with no rise is refused, "
          f"not marked")

    # an ineligible pixel is refused on the §3.11 rule, before any marking
    few = np.zeros(len(doy), bool); few[:10] = True
    r = extract_markers(doy, s, few)
    ok = not np.isfinite(r["trough"]) and "ineligible" in r["reason"]
    ok_all &= ok
    print(f"\n  10 valid dekads -> reason '{r['reason']}'")
    print(f"  [{'PASS' if ok else 'FAIL'}] §3.11's >=14 rule is applied first")

    # a truncated series (plateau runs past the window) yields trough and
    # heading but no harvest -- and says so rather than inventing one
    trunc = valid.copy(); trunc[doy > 340] = False
    r = extract_markers(doy, s, trunc)
    ok = (np.isfinite(r["trough"]) and np.isfinite(r["heading"])
          and not np.isfinite(r["harvest"]))
    ok_all &= ok
    print(f"\n  series cut at DOY 340 -> trough {r['trough']}, heading "
          f"{r['heading']}, harvest {r['harvest']}")
    print(f"  [{'PASS' if ok else 'FAIL'}] an unobserved harvest is reported "
          f"missing, never extrapolated")

    # the full retention rule
    good = dict(trough=214.5, heading=284.5, harvest=334.5, rise_db=8.5, reason="")
    ok_g, _ = retain(good)
    late = dict(good, harvest=400.0)
    ok_l, r_l = retain(late)
    weak = dict(good, rise_db=2.0)
    ok_w, r_w = retain(weak)
    ok = ok_g and not ok_l and not ok_w and "outside" in r_l and "below" in r_w
    ok_all &= ok
    print(f"\n  retention rule: baseline-median season retained={ok_g}; "
          f"harvest at DOY 400 -> '{r_l}'; rise 2.0 dB -> '{r_w}'")
    print(f"  [{'PASS' if ok else 'FAIL'}] the rule admits a calendar-correct "
          f"season and refuses an out-of-window and a weak one, with reasons")

    print("=" * 74)
    print("SUPERSEDED-ARM SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    print("")
    ok_all &= selftest_plsm()
    print("")
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


# ===========================================================================
# GATE 1 (§3.1) IS NOT APPLIED ON THE RADAR PATH -- measured, not assumed
# ===========================================================================
# Paper 1's Gate 1 deletes a 5-day bin whose cohort observation count falls
# below r x the season's peak count. Its purpose is specific to optical data:
# a sparse bin means few cloud-free looks, so its dekadal mean is dominated by
# whatever slipped past the cloud mask. Sentinel-1 acquisition is not a weather
# process -- a bin's count is set by which relative orbits cross the tile in
# those five days, which repeats on a 12-day cycle every year. A peak-relative
# density gate therefore deletes bins for a cause that does not operate.
#
# It is also measurably harmful. On the 2017 baseline (25 districts, 10,000
# pixel-seasons), r = 0 against r = 0.50:
#
#                          no gate      r = 0.50
#   median valid dekads       26            24
#   minimum valid dekads      19            10
#   fraction >= 14          1.0000        0.9993
#   retained                0.2426        0.2544
#
# The gate manufactures the only §3.11 ineligibility in the entire untreated
# baseline: with no gate, not one of the 10,000 pixel-seasons falls below the
# >=14 rule. The retention difference is 1.2 points and the retained set's
# median markers are identical to the dekad either way, so the headline does
# not turn on this choice -- but the principled arm is the one that does not
# delete deterministic acquisitions, and it is also the arm on which the closed
# parameters above were derived. Recorded in the deviation log, dated.
GATE1_RATIO_RADAR = 0.0


def read_export(path):
    """One district-season CSV -> (cell_ids, lon, lat, values, counts).

    values and counts are (n_pixels, 55), indexed by §1.4's 5-day bin. Raises
    on a missing column rather than filling: the 2026-09-11 export defect wrote
    97 of 225 files with VHVV_med absent entirely, and a loader that tolerates
    that turns a silent export failure into a silent scientific result.
    """
    df = pd.read_csv(path)
    need = ["district", "year", "cell_id", "lon", "lat", "bin_index",
            "VHVV_med", "valid_obs_count"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise SystemExit(
            f"{os.path.basename(path)}: columns {missing} absent.\n"
            "This is the signature of the Earth Engine header-inference defect "
            "fixed in S2_QC_Ingest v0.7.1 -- Export.table.toDrive infers the "
            "header from the leading features, and an all-null leading block "
            "drops those columns from the whole file. Re-export with an "
            "explicit `selectors` list; do not patch it here.")
    df = df.sort_values(["cell_id", "bin_index"], kind="mergesort")
    cells = df["cell_id"].drop_duplicates().to_numpy()
    idx = {c: i for i, c in enumerate(cells)}
    n = len(cells)
    V = np.full((n, N_BINS_), np.nan)
    C = np.zeros((n, N_BINS_))
    r = df["cell_id"].map(idx).to_numpy()
    b = df["bin_index"].to_numpy(int)
    if b.min() < 0 or b.max() >= N_BINS_:
        raise SystemExit(f"{os.path.basename(path)}: bin_index outside "
                         f"0..{N_BINS_ - 1}")
    V[r, b] = pd.to_numeric(df["VHVV_med"], errors="coerce").to_numpy()
    C[r, b] = pd.to_numeric(df["valid_obs_count"],
                            errors="coerce").fillna(0.0).to_numpy()
    # §1.4 window sweep: drop bins beyond the requested upper endpoint BEFORE any
    # smoothing or fitting. Blanking rather than reshaping keeps every downstream
    # index meaning the same DOY, so a truncated run and the headline run are
    # directly comparable bin for bin.
    _keep = bins_within(WINDOW_END_DOY)
    if _keep < N_BINS_:
        V[:, _keep:] = np.nan
        C[:, _keep:] = 0.0
    lon = np.full(n, np.nan); lat = np.full(n, np.nan)
    lon[r] = pd.to_numeric(df["lon"], errors="coerce").to_numpy()
    lat[r] = pd.to_numeric(df["lat"], errors="coerce").to_numpy()
    district = str(df["district"].iloc[0])
    year = int(df["year"].iloc[0])
    return district, year, cells, lon, lat, V, C


# Failure taxonomy for §3.10. The diagnostic asks whether SURVIVAL correlates
# with exposure; a single pooled failure flag cannot say through which channel,
# so every refusal is classified at the point it is made.
def classify(reason):
    """Map a refusal reason to a channel, for §3.10.

    §3.10 asks whether SURVIVAL correlates with exposure. A single pooled
    failure flag cannot say through which channel, so every refusal is
    classified at the point it is made. PLSM's own reasons come first, then the
    two superseded arms' reasons, which are kept so the robustness arms classify
    with the same function.
    """
    if not reason:
        return "retained"
    r = reason.lower()
    if r.startswith("ineligible"):
        return "ineligible_dekads"
    # --- PLSM, the primary -------------------------------------------------
    if "not significant" in r:
        return "rise_not_significant"
    if "no admissible shape" in r:
        return "no_rise_then_fall"
    if "no breakpoint quadruple" in r:
        return "breakpoints_not_identified"
    if "standard error not estimable" in r or "rise not estimated" in r:
        return "rise_se_not_estimable"
    if "floor" in r:
        return "rise_below_floor"
    # --- the trapezoid arm --------------------------------------------------
    if "no admissible rise" in r:
        return "no_rise_above_base"
    if "no admissible fall" in r:
        return "no_fall_after_heading"
    if "six valid dekads inside the rise" in r:
        return "too_few_dekads_in_rise_window"
    if "four valid dekads after heading" in r:
        return "too_few_dekads_after_heading"
    # --- the crossing arm ---------------------------------------------------
    if "transplanting window" in r or "trough window" in r:
        return "no_dekad_in_trough_window"
    if "three valid dekads after" in r:
        return "too_few_after_trough"
    if "heading level" in r:
        return "no_heading_crossing"
    if "harvest level" in r:
        return "no_harvest_crossing"
    if "outside" in r:
        return "outside_gate2_" + r.split()[0]
    if "below the" in r and " db " in r:
        return "rise_below_minimum"
    if "not recovered" in r or "not identified" in r:
        return "marker_not_recovered"
    return "other"


# ===========================================================================
# THE PIECEWISE-LINEAR (TRAPEZOID) BREAKPOINT ESTIMATOR -- PRIMARY DEFINITION
# ===========================================================================
# Added 2026-09-12, after a split-half reliability test on the untreated 2017
# baseline showed the crossing rule above is the less reliable of the two.
#
# WHY A SECOND ESTIMATOR AT ALL. The crossing rule reads each marker off ONE
# dekad: the first dekad at or above trough + 0.8 x rise, the first back below
# trough + 0.5 x rise. The per-pixel-season dekadal series has a measured noise
# sd of 2.03 dB (median over 10,000 baseline pixel-seasons; sd of second
# differences over sqrt(6), which annihilates any locally linear trend). A rule
# that reads a date off a single noisy point inherits that noise in full.
#
# THE MODEL. base b1 -> linear rise -> plateau p -> linear fall -> base b2.
# This is the shape Phan, Le Toan & Bouvet (2021) describe, written down. The
# four breakpoints ARE the markers, so the 0.80 and 0.50 crossing fractions
# disappear -- two arbitrary constants removed, not re-tuned:
#
#   t1  end of the dark phase        (read as the transplanting trough)
#   t2  end of the rise              (read as heading, canopy maximal)
#   t3  end of the plateau           (read as drainage onset)
#   t4  end of the fall              (read as harvest)
#
# The LEFT column is what the estimator locates: a breakpoint in a VH/VV
# trajectory. The parenthesised right column is the AGRONOMIC READING those
# positions are given, and it is a reading, not a measurement. This study
# holds no field reference (§4.3.1), so no breakpoint here is an observed
# transplanting, heading, drainage or harvest date, and the CSV column names
# -- which keep the agronomic words -- must not be read as asserting one.
#
# Given the breakpoints the model is LINEAR in the three levels, so the levels
# are profiled out by weighted least squares and only the breakpoints are
# searched -- on the dekad grid, and only inside §3.2's own windows, so a
# breakpoint can never be proposed outside the window that would accept it.
# Each marker is then estimated from every dekad in its segment rather than
# from one crossing.
#
# THE SPLIT-HALF TEST THAT CHOSE IT. Each dekad aggregates two 5-day bins
# (§1.4). Building one series from the first bin of every dekad and another
# from the second gives two estimates of the same season from DISJOINT
# observations, on the same grid, with the same orbit mix -- so their
# DISAGREEMENT is what this measures, reported as sd(difference)/sqrt(2). That
# is a scaled disagreement statistic, not a measured error: whatever is common
# to both halves cancels from the difference and is invisible to it. On the 2017 baseline, pixel-seasons with >= 14 valid
# dekads in both halves and all markers recovered in both:
#
#                       crossings           trapezoid
#   trough    sigma      21.9 d              24.5 d
#             |a-b| med  20 d                10 d      within 1 dekad .35 -> .55
#   heading   sigma      35.3 d              26.2 d
#             |a-b| med  30 d                20 d      within 1 dekad .24 -> .41
#   harvest   sigma      40.9 d              25.2 d
#             |a-b| med  40 d                20 d      within 1 dekad .21 -> .39
#
# CORRECTION 2026-09-13: PLSM's own column, which an earlier revision of this
# docstring filled in from the trapezoid's, is measured and is NOT the same --
# trough 33.6 d (.33 within a dekad), heading 23.4 d (.38), drainage 22.5 d
# (.40), harvest 27.8 d (.32), on 3,021 testable pixel-seasons. See the PLSM
# section below and results/splithalf_reliability.csv.
#
# The trapezoid wins on heading and harvest on every statistic, and on the
# trough it halves the median disagreement while carrying a slightly heavier
# tail. Rule stated before the test: adopt the arm with the smaller split-half
# sigma on the markers §3.8 uses. The crossing rule is retained in this module
# and reported as a pre-declared robustness arm, not deleted.
#
# WHAT THE TEST ALSO SAYS, AND IT IS NOT COMFORTABLE. sigma stays near 25 d
# (about 18 d for the full series, which has twice the observations) and does
# NOT fall as the fit gets better: within-one-dekad agreement is flat at
# .55/.41/.39 across every bin of signal-to-noise from below 1 to above 3, and
# flat across every bin of rise amplitude from 3 dB to 12 dB. So NO retention
# threshold on this substrate buys timing precision, and none is claimed to.
# Per-pixel marker dates carry about two dekads of disagreement between disjoint
# halves of the same season. That is reported, not smoothed over, and it is part
# reported alongside §3.8's district-season estimates and §3.10's attrition
# diagnostic. It does NOT determine the primary estimand: §3.8 fixes that by
# DECLARATION -- the breakpoint of the district-mean curve is the quantity the
# hypotheses are about -- and no measured or simulated dispersion, here or
# anywhere, selects the level of estimation after the fact.
#
# NO ERROR MODEL IS ASSERTED FOR IT, and none should be read in. The split-half
# figure is a DISAGREEMENT between two halves of one series, not a measured
# error: whatever is common to both halves cancels from it and is invisible. It
# does not license any statement about how outcome error propagates into a
# difference-in-differences coefficient -- that would need the error to be
# independent of the exposure with zero conditional mean, and the censoring test
# gives direct reason to doubt both, since a late-season backscatter change
# moves a fitted breakpoint months upstream and is driven by the same
# storm-season signal the exposure indicator marks. See analysis/deviation_log.md
# for the dated record of the claim this replaced.
#
# NO WHITTAKER PRE-SMOOTH. A 7-parameter shape model over 28 points is itself a
# smoother; pre-smoothing would pull the breakpoints toward the interior of the
# season. On the crossing arm smoothing was measurably destructive (both-half
# marker completeness 0.336 unsmoothed against 0.091 smoothed).

TZ_LEVEL = 0.05        # the rise must be significantly positive at this level


def _tz_windows():
    t1 = [k for k in range(_FP.N_DEKADS)
          if GATE2["trough"][0] <= _FP.DEKAD_DOY[k] <= GATE2["trough"][1]]
    t2 = [k for k in range(_FP.N_DEKADS)
          if GATE2["heading"][0] <= _FP.DEKAD_DOY[k] <= GATE2["heading"][1]]
    t4 = [k for k in range(_FP.N_DEKADS)
          if GATE2["harvest"][0] <= _FP.DEKAD_DOY[k] <= GATE2["harvest"][1]]
    return t1, t2, t4


TZ_T1, TZ_T2, TZ_T4 = _tz_windows()


def _tz_designs():
    """Precomputed (28 x 2) designs, one per admissible breakpoint pair."""
    n = _FP.N_DEKADS
    rise = {}
    for a in TZ_T1:
        for b in TZ_T2:
            if b - a < 2:          # a ramp needs at least one interior dekad
                continue
            f = np.zeros(n)
            f[a:b + 1] = np.linspace(0.0, 1.0, b - a + 1)
            f[b:] = 1.0
            rise[(a, b)] = np.column_stack([1.0 - f, f])
    fall = {}
    for c in range(min(TZ_T2), n - 2):
        for d in TZ_T4:
            if d <= c:
                continue
            f = np.zeros(n)
            f[c:d + 1] = np.linspace(0.0, 1.0, d - c + 1)
            f[d:] = 1.0
            fall[(c, d)] = np.column_stack([1.0 - f, f])
    return rise, fall


TZ_RISE_X, TZ_FALL_X = _tz_designs()


def _wls2(X, y, w, dof_penalty=4):
    """Two-parameter weighted least squares in closed form.

    Returns (beta, sse, V) with V the 2x2 covariance using sse/(n_eff - 4):
    four, not two, because the breakpoints were also estimated. No pinv and no
    sqrt of a possibly-negative diagonal -- the 2x2 inverse is exact and the
    determinant is checked, so a rank-deficient segment returns None rather
    than a fabricated standard error.
    """
    Xw = X * w[:, None]
    A = X.T @ Xw
    det = A[0, 0] * A[1, 1] - A[0, 1] * A[1, 0]
    if not np.isfinite(det) or abs(det) < 1e-10:
        return None, np.inf, None
    b = Xw.T @ y
    beta = np.array([(A[1, 1] * b[0] - A[0, 1] * b[1]) / det,
                     (A[0, 0] * b[1] - A[1, 0] * b[0]) / det])
    r = y - X @ beta
    sse = float(np.sum(w * r * r))
    n_eff = float(np.sum(w > 0))
    dof = n_eff - dof_penalty
    if dof <= 0:
        return beta, sse, None
    Ainv = np.array([[A[1, 1], -A[0, 1]], [-A[1, 0], A[0, 0]]]) / det
    return beta, sse, (sse / dof) * Ainv


def fit_trapezoid(series, valid, min_valid=MIN_VALID_DEKADS,
                  level=TZ_LEVEL):
    """Fit base-rise-plateau-fall-base to one pixel-season's dekadal series.

    Returns every breakpoint as a DOY, the three levels, the rise and fall in
    dB, the rise's standard error and t statistic, the segment residual RMSEs,
    and a reason string when the shape could not be identified. Never raises:
    §3.10 needs the refusals as much as the fits.
    """
    out = dict(trough=np.nan, heading=np.nan, drainage=np.nan, harvest=np.nan,
               base_db=np.nan, plateau_db=np.nan, post_db=np.nan,
               rise_db=np.nan, fall_db=np.nan, rise_se=np.nan, rise_t=np.nan,
               rmse_rise=np.nan, rmse_fall=np.nan,
               n_valid=int(np.sum(valid)), reason="")
    if out["n_valid"] < min_valid:
        out["reason"] = f"ineligible: {out['n_valid']} valid dekads"
        return out

    y = np.where(valid, series, 0.0)
    w = valid.astype(float)

    # ---- stage 1: base, rise, plateau, on dekads up to the heading bound ---
    w1 = w.copy()
    w1[max(TZ_T2) + 1:] = 0.0
    if w1.sum() < 6:
        out["reason"] = "fewer than six valid dekads inside the rise window"
        return out
    best = (np.inf, None, None, None)
    for key, X in TZ_RISE_X.items():
        beta, sse, V = _wls2(X, y, w1)
        if beta is None or not (beta[1] > beta[0]):
            continue
        if sse < best[0]:
            best = (sse, key, beta, V)
    if best[1] is None:
        out["reason"] = "no admissible rise: no plateau above the base"
        return out
    sse, (a, b), beta, V = best
    n1 = float(np.sum(w1 > 0))
    out.update(trough=float(_FP.DEKAD_DOY[a]), heading=float(_FP.DEKAD_DOY[b]),
               base_db=float(beta[0]), plateau_db=float(beta[1]),
               rise_db=float(beta[1] - beta[0]),
               rmse_rise=float(np.sqrt(sse / max(n1 - 4.0, 1.0))))
    if V is not None:
        var = float(V[0, 0] - 2.0 * V[0, 1] + V[1, 1])
        if var > 0:
            se = float(np.sqrt(var))
            out.update(rise_se=se, rise_t=out["rise_db"] / se)
        elif sse <= 0.0 and out["rise_db"] > 0.0:
            # an exact fit: zero residual variance, so the rise is
            # determined. Recorded as se 0 with an infinite t rather
            # than "not estimable", which is what a naive
            # sqrt(max(var, 0)) would hide.
            out.update(rise_se=0.0, rise_t=np.inf)

    # ---- stage 2: plateau, fall, post-harvest base, from heading onward ----
    w2 = w.copy()
    w2[:b] = 0.0
    if w2.sum() < 4:
        out["reason"] = "fewer than four valid dekads after heading"
        return out
    best = (np.inf, None, None)
    for (c, d), X in TZ_FALL_X.items():
        if c < b:
            continue
        beta2, sse2, _ = _wls2(X, y, w2)
        if beta2 is None or not (beta2[0] > beta2[1]):
            continue
        if sse2 < best[0]:
            best = (sse2, (c, d), beta2)
    if best[1] is None:
        out["reason"] = "no admissible fall: no decline after heading"
        return out
    sse2, (c, d), beta2 = best
    n2 = float(np.sum(w2 > 0))
    out.update(drainage=float(_FP.DEKAD_DOY[c]), harvest=float(_FP.DEKAD_DOY[d]),
               post_db=float(beta2[1]), fall_db=float(beta2[0] - beta2[1]),
               rmse_fall=float(np.sqrt(sse2 / max(n2 - 4.0, 1.0))))
    return out


# Student-t 0.975 critical values, one-sided 0.05 == two-sided 0.10 upper tail
# at 0.95. The screen below is one-sided (a rise is positive or it is not), so
# the 0.95 quantile is what is wanted. Tabulated to avoid a scipy dependency;
# beyond 30 degrees of freedom the normal value is used, which is conservative
# in the direction of admitting fewer pixels.
_T95 = {1: 6.314, 2: 2.920, 3: 2.353, 4: 2.132, 5: 2.015, 6: 1.943, 7: 1.895,
        8: 1.860, 9: 1.833, 10: 1.812, 11: 1.796, 12: 1.782, 13: 1.771,
        14: 1.761, 15: 1.753, 16: 1.746, 17: 1.740, 18: 1.734, 19: 1.729,
        20: 1.725, 21: 1.721, 22: 1.717, 23: 1.714, 24: 1.711, 25: 1.708,
        26: 1.706, 27: 1.703, 28: 1.701, 29: 1.699, 30: 1.697}


def t_crit95(dof):
    dof = int(max(dof, 1))
    return _T95.get(dof, 1.645)


def retain_trapezoid(m, min_rise_db=0.0, level=TZ_LEVEL):
    """Eligibility for a trapezoid-marked pixel-season.

    Retained iff §3.11's dekad count is met, all four breakpoints were
    identified, and the fitted rise is significantly positive at `level` on the
    pixel-season's own residual variance. §3.2's windows are STRUCTURAL here --
    the breakpoint grid is restricted to them -- so no pixel can be refused for
    landing outside a window the search was allowed to enter.

    The significance screen replaces the absolute 5.32 dB floor derived on the
    crossing arm. The reason is measured, not stylistic: split-half reliability
    is FLAT in rise amplitude from 3 dB to 12 dB, so an absolute floor buys no
    precision and only costs sample. What a rise screen can legitimately do is
    exclude pixel-seasons with no rice-like rise AT ALL, and a per-pixel t test
    against that pixel's own noise does exactly that while adapting to how
    noisy each pixel is. It is a screen, not an inferential statement: the
    breakpoints were chosen on the same data, so the nominal level is
    optimistic, and `min_rise_db` is exposed so §3.8 can report the estimates
    across a specification curve of absolute floors as well.
    """
    if m["reason"].startswith("ineligible"):
        return False, m["reason"]
    for k in ("trough", "heading", "drainage", "harvest"):
        if not np.isfinite(m.get(k, np.nan)):
            return False, m["reason"] or f"{k} not identified"
    if not np.isfinite(m["rise_db"]):
        return False, "rise not estimated"
    if m["rise_db"] < min_rise_db:
        return False, (f"rise {m['rise_db']:.2f} dB below the "
                       f"{min_rise_db:.2f} dB floor")
    if m["rise_t"] is None or np.isnan(m["rise_t"]):
        return False, "rise standard error not estimable"
    dof = int(max(m["n_valid"] - 4, 1))
    if m["rise_t"] < t_crit95(dof):
        return False, (f"rise not significant: t {m['rise_t']:.2f} below "
                       f"{t_crit95(dof):.2f} at {int(dof)} dof")
    return True, ""


# ===========================================================================
# THE FIVE-SEGMENT PIECEWISE-LINEAR SEASON MODEL (PLSM) -- PRIMARY, 2026-09-12
# ===========================================================================
# Third and final estimator in this module. The two above are kept because they
# are the record of how this one was arrived at, and because each is reported as
# a pre-declared robustness arm. What forced the change, in order:
#
# (1) THE §3.2 WINDOWS BIND, AND BADLY. Under the trapezoid, 1,783 of 3,303
#     retained baseline pixel-seasons (54%) placed the trough on the LAST dekad
#     inside §3.2's trough window and 1,166 (35%) placed heading on the last
#     dekad inside its heading window. Free the windows and the "all three
#     markers land inside Gate 2" result evaporates: only 35% of troughs and
#     55% of headings remain inside. The earlier claim rested on the MEDIAN of
#     the crossing markers, and the median was inside while the majority of
#     units were pinned to a boundary. Same aggregate-for-unit error as the four
#     already recorded in the deviation log. §3.2's windows come from Paper 1's
#     optical substrate. The radar breakpoint distribution lies LATER than the
#     positions of those bounds -- a separation of roughly 40-60 days,
#     consistent in all three markers -- so the bounds are NOT TRANSFERABLE
#     across these measurands. Nothing here judges the optical windows as
#     wrong for their own sensor; that is a question for Paper 1's optical
#     measurements or an independent field reference.
#
#     WHAT THIS SAYS ABOUT PAPER 1, WHICH IS LESS THAN IT LOOKS. Paper 1's
#     optical calendar bounds do not align with this panel's radar breakpoint
#     distribution: its 240-DOY SOS ceiling sits below the radar trough median
#     of 254.5, so transferring those bounds across sensors would censor many
#     radar estimates. That demonstrates NON-TRANSFERABILITY between two
#     different measurands and nothing more. It does not establish that Paper
#     1's optical SOS bound was mis-specified, identify a true agronomic onset,
#     or reinterpret Paper 1's loss of treated support. Those questions require
#     Paper 1's own optical measurements or an independent field reference,
#     neither of which this module holds.
#
# (2) PER-PIXEL MARKER DATES CARRY ABOUT +/-18 DAYS OF DISAGREEMENT. Two
#     different procedures give similar numbers -- they are not independent of
#     one another, since both read this panel through this estimator:
#     split-half resampling (odd against even 5-day bins,
#     disjoint observations, same orbit mix) gives sigma 22-41 d for the
#     crossing rule, 25-28 d for the trapezoid and 22-34 d for PLSM itself
#     (trough 33.6, heading 23.4, drainage 22.5, harvest 27.8, measured
#     2026-09-13 -- an earlier revision of this file filled PLSM's column from
#     the trapezoid's without running it, which was wrong; see the deviation
#     log's 2026-09-13 second entry), all on HALF the observations, hence
#     roughly 16-24 d on the full series; and a Monte Carlo on a synthetic
#     season at the measured 2.03 dB dekadal noise gives sigma 12-18 d with
#     bias under 5 d. And the reliability does NOT improve with signal: within-
#     one-dekad agreement is flat at .55/.41/.39 across every bin of rise
#     amplitude from 3 dB to 12 dB and every bin of fit signal-to-noise from
#     below 1 to above 3. So no retention threshold buys timing precision, and
#     the 5.32 dB floor derived on 2026-09-12 was buying none. The measured
#     disagreement is reported rather than hidden. No claim is made here about
#     whether other studies report such a figure; Protocol section 1.5.5 carries
#     the literature search of record, and the dated history of a priority claim
#     that was tested and found false is in analysis/deviation_log.md.
#
# (3) SO THE UNIT OF ANALYSIS MOVES TO THE DISTRICT-SEASON. The district-mean
#     dekadal series has a sampling standard error of 0.122 dB (median over all
#     225 district-seasons), against 2.03 dB per pixel. Fed a SYNTHETIC season
#     at that assumed noise level, the archived 80-draw Monte Carlo reports
#     sd 0.00/0.00/2.18/1.90 d for t1/t2/t3/t4 (grid=free), with signed
#     errors 0.000/0.000/-0.500/+0.375 d. See results/montecarlo_precision.csv.
#     That is conditional performance on a simulated trajectory under an assumed
#     noise level: it is not an accuracy, not a field-validated figure, and not a
#     measurement of anything in the real panel, which contains no repeat
#     observation at district scale to check it against. Observed within-district
#     dispersion of heading ACROSS the nine seasons is 5-14 days; the two are
#     different kinds of quantity and no ratio between them is formed or implied.
#     The district-season panel is the primary estimand; the pixel panel is
#     retained, because §3.10's attrition diagnostic is a statement about
#     pixels, and as a robustness arm.
#
# (4) AND THE SHAPE NEEDED A FIFTH SEGMENT. The trapezoid's flat pre-season base
#     is wrong here: the series starts HIGH (previous crop and pre-monsoon
#     cover) and declines into the dark flooded phase. Forcing it flat split the
#     residual between the two and biased both the trough date and the
#     amplitude -- Kendrapara 2019 was fitted with a base of -7.56 dB against an
#     observed -6.05 early and -9.50 at the real trough, rmse 1.02 dB, and it
#     put t1 at DOY 304.5 when the trough is plainly at 254.5. Adding the
#     leading decline costs one parameter and cut the median district-season
#     rmse from 0.397 to 0.316 dB.
#
#       a0 --decline--> b1 --rise--> p --plateau--> p --fall--> b2 --flat-->
#          [start,t1]      [t1,t2]      [t2,t3]       [t3,t4]     [t4,end]
#
# WHICH MARKER IS WEAKEST, AND BY HOW MUCH. Under PLSM the TROUGH is the least
# reliable of the four: split-half sigma 33.6 d and agreement within one dekad of
# only .33, against heading 23.4 d / .38, drainage 22.5 d / .40 and harvest
# 27.8 d / .32. That is the same fact the next paragraph states physically -- a
# puddled flooded field and a dry bare pre-monsoon field are both radar-dark, so
# the dark phase is one long low whose interior break is weakly identified -- and
# it makes `trough`, and the durations built on it (veg_days, season_days), the
# weakest outcomes in §3.8. Per-pixel rise_db carries sigma 2.13 dB against a
# median of 6.1 dB. Whether the district-season panel inherits this weakness is
# NOT established. The archived Monte Carlo at 0.122 dB reports t1/t2/t3/t4
# standard deviations 0.00/0.00/2.18/1.90 d for one on-grid SYNTHETIC trajectory,
# not the previously asserted common 1.3 d recovery. These are properties of
# that simulation, not evidence that the real district panel is unaffected.
#
# WHAT THE BREAKPOINTS ARE, STATED HONESTLY. t2, t3 and t4 mark real transitions
# in the curve. t1 does NOT mark transplanting: a puddled, flooded field and a
# dry bare pre-monsoon field are both radar-dark in VH/VV, so the low phase runs
# from land preparation through early tillering as one long dark stretch whose
# interior minimum is placed by noise. t1 is reported as the ONSET OF CANOPY
# DEVELOPMENT -- the end of the dark phase -- and the interval by which it lags
# transplanting is not resolvable in this data. Measured medians, all 225
# district-seasons: t1 DOY 254.5, t2 314.5, t3 324.5, t4 384.5; rise 2.4 dB.
# Odisha's 108 district-seasons all fit (median rise 2.47 dB); West Bengal's 54
# all fit; 12 of Andhra Pradesh's 63 admit no fit at all and its amplitudes are
# much weaker (Visakhapatnam 0.76 dB, West Godavari 1.15 dB), which is the delta
# double-crop calendar rather than coastal Sali. Those 12 are the district-level
# attrition and §3.10 tests them against exposure like any other; five of the
# twelve fall in the untreated 2017 baseline, so they are not a treated-season
# artefact.
#
# NO PHENOMETRIC WINDOW GATE IN THE PRIMARY SPECIFICATION. The breakpoints are
# searched over the whole 28-dekad grid with only ordering and shape
# admissibility imposed. That is what (1) requires, and it removes the class of
# gate that deleted Paper 1's treated post-period.

# ===========================================================================
# SELECTION-AWARE CRITICAL VALUES FOR THE RISE SCREEN  (2026-09-12)
# ===========================================================================
# The nominal t test is INVALID after breakpoint selection, and the size of the
# error was measured rather than assumed: on pure Gaussian noise with no season
# at all, 28.3% of series passed the nominal 5% one-sided screen on the pixel
# grid. The fit chooses among thousands of shapes, so it finds an apparent rise
# far more often than a fixed-design t test would.
#
# The fix is the null distribution of the SAME statistic under the SAME search.
# It is scale-free -- t = rise / se(rise) and both scale with sigma -- so it
# depends only on the grid and on how many dekads are valid, and can be
# tabulated once. plsm_null_t.csv holds it: 4,000 draws per (grid, n_valid) for
# the pixel grid and 1,500 for the free grid, each draw with a random pattern of
# missing dekads so the table averages over patterns rather than assuming one.
#
# Measured, and nearly flat in n_valid:
#     pixel grid (4,322 designs)   t95 = 2.73-3.01, about 2.90
#     free  grid (12,649 designs)  t95 = 3.23-3.44, about 3.30
# against a nominal t95 near 1.71. Only about 80% of pure-noise draws admit any
# shape at all, so the unconditional false-positive rate of the calibrated
# screen is about 0.04.
#
# THE NULL IS i.i.d. GAUSSIAN, AND THAT CHOICE WAS CHECKED, NOT ASSUMED. The
# lag-1 autocorrelation of the fitted residuals is NEGATIVE at pixel level
# (median -0.22 over 586 baseline pixel-seasons), which is what fitting a
# flexible shape to noise produces and which makes spurious rises LESS likely
# than the i.i.d. null -- so at pixel level the table is conservative. At
# district-mean level it is POSITIVE (median +0.21 over the 25 baseline
# districts), which cuts the other way, so plsm_null_t_ar1.csv carries the same
# table under an AR(1) null at rho = 0.25 and 0.40 and the free grid uses the
# AR(1) value. Both files ship with the repo and both are reproduced by
# python/calibrate_plsm_null.py.
NULL_T_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "plsm_null_t.csv")
NULL_T_AR1_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "plsm_null_t_ar1.csv")
# Fallbacks, used only if the tables are absent. They are the measured plateau
# values, so a missing table degrades to a constant rather than to the invalid
# nominal test.
NULL_T_FALLBACK = {"pixel": 2.95, "free": 4.20}

# Which grids take the AR(1) critical value, and at which rho. Decided by the
# MEASURED sign of the fitted residuals' lag-1 autocorrelation, not by taste:
#   pixel level  median -0.22  -> negative, so the i.i.d. table is already
#                                 conservative and the AR(1) value is not used
#   district     median +0.21  -> positive, so the i.i.d. table is too
#                                 permissive and the AR(1) value is used
# rho = 0.25 is the tabulated value just above the measured district median of
# +0.21; it gives t95 = 4.17 on the free grid against 3.30 i.i.d. The p95 of the
# measured district autocorrelations is +0.47, and rho = 0.40 is tabulated too
# (t95 = 4.98) and is reported as the conservative robustness arm.
NULL_T_RHO = 0.25
NULL_T_AR1_GRIDS = ("free",)
_NULL_T_CACHE = {}


def _load_null_table():
    if "tab" in _NULL_T_CACHE:
        return _NULL_T_CACHE["tab"]
    tab = {}
    try:
        d = pd.read_csv(NULL_T_FILE)
        for _, r in d.iterrows():
            tab[(str(r["grid"]), int(r["n_valid"]))] = float(r["t95"])
    except Exception:
        pass
    ar = {}
    try:
        d = pd.read_csv(NULL_T_AR1_FILE)
        d = d[(d["rho"] - NULL_T_RHO).abs() < 1e-9]
        for g, gg in d.groupby("grid"):
            if str(g) not in NULL_T_AR1_GRIDS:
                continue
            # max over the tabulated n_valid: the table is flat in n_valid, and
            # erring high costs sample rather than credibility
            ar[str(g)] = float(gg["t95"].max())
    except Exception:
        pass
    _NULL_T_CACHE["tab"] = (tab, ar)
    return tab, ar


def plsm_t_crit(grid, n_valid):
    """Selection-aware 5% one-sided critical value for the rise screen.

    `grid` is "pixel" or "free". Prefers the AR(1) value where one is tabulated
    for that grid -- that is the conservative direction at district-mean level,
    where the residuals are positively autocorrelated -- and otherwise the
    i.i.d. table, and otherwise the measured constant.
    """
    tab, ar = _load_null_table()
    if grid in ar:
        return ar[grid]
    n = int(max(n_valid, 1))
    if (grid, n) in tab:
        return tab[(grid, n)]
    same = [v for (g, k), v in tab.items() if g == grid]
    if same:
        return float(max(same))
    return NULL_T_FALLBACK.get(grid, 3.5)


PLSM_MIN_SEGMENT = 2           # dekads; each sloped segment needs an interior


def plsm_build(t1_range=None, t2_range=None, t3_range=None, t4_range=None,
               min_seg=PLSM_MIN_SEGMENT):
    """Precompute one (28 x 4) design per admissible breakpoint quadruple.

    Columns are the weights on (a0, b1, p, b2). Ranges are dekad indices; None
    means the whole grid, which is what the primary district-season fit uses.
    """
    n = _FP.N_DEKADS
    r1 = list(t1_range) if t1_range is not None else list(range(min_seg, n - 5))
    r2 = list(t2_range) if t2_range is not None else list(range(0, n - 2))
    r3 = list(t3_range) if t3_range is not None else list(range(0, n - 1))
    r4 = list(t4_range) if t4_range is not None else list(range(1, n))
    keys, Xs = [], []
    for a in r1:
        g = np.zeros(n)                       # 0 at the start, 1 from t1 on
        g[:a + 1] = np.linspace(0.0, 1.0, a + 1)
        g[a:] = 1.0
        for b in r2:
            if b - a < min_seg:
                continue
            f1 = np.zeros(n)
            f1[a:b + 1] = np.linspace(0.0, 1.0, b - a + 1)
            f1[b:] = 1.0
            for c in r3:
                if c < b:
                    continue
                for d in r4:
                    if d - c < min_seg:
                        continue
                    f2 = np.zeros(n)
                    f2[c:d + 1] = np.linspace(0.0, 1.0, d - c + 1)
                    f2[d:] = 1.0
                    Xs.append(np.column_stack(
                        [1.0 - g, g * (1.0 - f1), f1 * (1.0 - f2), f2]))
                    keys.append((a, b, c, d))
    if not keys:
        raise ValueError("no admissible breakpoint quadruple in the given ranges")
    return keys, np.asarray(Xs)


PLSM_N_PARAM = 8               # four levels + four breakpoints


def plsm_fit(series, valid, designs, min_valid=MIN_VALID_DEKADS):
    """Fit the five-segment model to one dekadal series.

    `designs` is the (keys, Xs) pair from plsm_build. Levels are profiled out by
    weighted least squares over every admissible breakpoint quadruple at once;
    the quadruple with the smallest weighted residual sum of squares wins.
    Admissibility is p > b1 (a rise), p > b2 (a fall) and a0 > b1 (the season
    starts above the dark phase) -- the shape, not the calendar.

    Returns a dict; never raises. `reason` is set when no fit is admissible,
    because §3.10 needs the refusals.
    """
    keys, Xs = designs
    out = dict(trough=np.nan, heading=np.nan, drainage=np.nan, harvest=np.nan,
               pre_db=np.nan, dark_db=np.nan, plateau_db=np.nan, post_db=np.nan,
               rise_db=np.nan, fall_db=np.nan, rise_se=np.nan, rise_t=np.nan,
               rmse=np.nan, n_valid=int(np.sum(valid)), reason="")
    if out["n_valid"] < min_valid:
        out["reason"] = f"ineligible: {out['n_valid']} valid dekads"
        return out
    y = np.where(valid, series, 0.0).astype(float)
    w = valid.astype(float)

    A = np.einsum('mik,i,mil->mkl', Xs, w, Xs)
    b = np.einsum('mik,i,i->mk', Xs, w, y)
    det = np.linalg.det(A)
    good = np.isfinite(det) & (np.abs(det) > 1e-10)
    if not good.any():
        out["reason"] = "no breakpoint quadruple is identified on these dekads"
        return out
    beta = np.full((len(keys), 4), np.nan)
    beta[good] = np.linalg.solve(A[good], b[good][..., None])[..., 0]
    resid = y[None, :] - np.einsum('mik,mk->mi', Xs, np.nan_to_num(beta))
    sse = np.einsum('mi,i,mi->m', resid, w, resid)
    adm = (good & np.isfinite(sse)
           & (beta[:, 2] > beta[:, 1])       # plateau above the dark phase
           & (beta[:, 2] > beta[:, 3])       # and it falls again
           & (beta[:, 0] > beta[:, 1]))      # the season starts above it
    if not adm.any():
        out["reason"] = ("no admissible shape: no rise-then-fall above a dark "
                         "phase")
        return out
    idx = np.where(adm)[0]
    j = int(idx[np.argmin(sse[idx])])
    a_, b_, c_, d_ = keys[j]
    n_eff = float(np.sum(w > 0))
    dof = max(n_eff - PLSM_N_PARAM, 1.0)
    s2 = float(sse[j]) / dof
    rise = float(beta[j, 2] - beta[j, 1])
    out.update(trough=float(_FP.DEKAD_DOY[a_]), heading=float(_FP.DEKAD_DOY[b_]),
               drainage=float(_FP.DEKAD_DOY[c_]), harvest=float(_FP.DEKAD_DOY[d_]),
               pre_db=float(beta[j, 0]), dark_db=float(beta[j, 1]),
               plateau_db=float(beta[j, 2]), post_db=float(beta[j, 3]),
               rise_db=rise, fall_db=float(beta[j, 2] - beta[j, 3]),
               rmse=float(np.sqrt(s2)))
    try:
        Ai = np.linalg.inv(A[j])
    except np.linalg.LinAlgError:
        return out
    var = s2 * float(Ai[1, 1] - 2.0 * Ai[1, 2] + Ai[2, 2])   # var of (p - b1)
    if var > 0:
        se = float(np.sqrt(var))
        out.update(rise_se=se, rise_t=rise / se)
    elif sse[j] <= 0.0 and rise > 0.0:
        out.update(rise_se=0.0, rise_t=np.inf)
    return out


def plsm_retain(m, min_rise_db=0.0, dof_offset=PLSM_N_PARAM, grid="pixel"):
    """Eligibility for a PLSM-fitted series.

    Retained iff §3.11's dekad count is met, an admissible shape was found, and
    the fitted rise is significantly positive at 5% one-sided on the series'
    own residual variance. No calendar window is applied -- see the module note.
    `min_rise_db` is exposed only so §3.8 can report a specification curve over
    an absolute floor; the primary value is 0.
    """
    if m["reason"]:
        return False, m["reason"]
    if not np.isfinite(m["rise_db"]):
        return False, "rise not estimated"
    if m["rise_db"] < min_rise_db:
        return False, (f"rise {m['rise_db']:.2f} dB below the "
                       f"{min_rise_db:.2f} dB floor")
    t = m["rise_t"]
    if t is None or np.isnan(t):
        return False, "rise standard error not estimable"
    tc = plsm_t_crit(grid, m["n_valid"])
    if t < tc:
        return False, (f"rise not significant: t {t:.2f} below the "
                       f"selection-aware {tc:.2f} ({grid} grid, "
                       f"{int(m['n_valid'])} valid dekads)")
    return True, ""


# The pixel-level grid. Derived from the range of the district-mean breakpoints
# on the UNTREATED 2017 baseline, padded by two dekads on each side, so a pixel
# is allowed a season two dekads outside anything any baseline district showed
# and no further. Restricting it is a compute decision -- the free grid is
# 12,649 designs and 90,000 pixel-seasons -- and the padding is what keeps it
# from being a calendar gate in disguise. Baseline district-mean ranges, from
# plsm on the 25 baseline curves: t1 204.5-284.5, t2 294.5-334.5,
# t3 304.5-344.5, t4 344.5-422.0.
PIXEL_GRID_DOY = {"t1": (184.5, 304.5), "t2": (274.5, 354.5),
                  "t3": (284.5, 364.5), "t4": (324.5, 422.0)}


def _dekads_in(lo, hi):
    return [k for k in range(_FP.N_DEKADS) if lo <= _FP.DEKAD_DOY[k] <= hi]


def plsm_designs_pixel():
    g = PIXEL_GRID_DOY
    return plsm_build(_dekads_in(*g["t1"]), _dekads_in(*g["t2"]),
                      _dekads_in(*g["t3"]), _dekads_in(*g["t4"]))


def plsm_designs_free():
    return plsm_build()


def _plsm_synth(t1, t2, t3, t4, a0, b1, p, b2):
    """A five-segment curve on the dekad grid with markers by construction."""
    d = _FP.DEKAD_DOY
    s = np.empty(len(d))
    for i, x in enumerate(d):
        if x <= t1:
            s[i] = a0 + (b1 - a0) * (x - d[0]) / (t1 - d[0])
        elif x <= t2:
            s[i] = b1 + (p - b1) * (x - t1) / (t2 - t1)
        elif x <= t3:
            s[i] = p
        elif x <= t4:
            s[i] = p - (p - b2) * (x - t3) / (t4 - t3)
        else:
            s[i] = b2
    return s


def selftest_plsm():
    """Checks on the primary estimator. Every number here is asserted, not
    printed for decoration: the Monte Carlo lines also RECORD the imprecision
    of a pixel-level marker, which is a result of the paper, not a bug."""
    print("=" * 74)
    print("SELF-TEST -- five-segment PLSM (primary)")
    print("=" * 74)
    ok_all = True
    free = plsm_designs_free()
    pix = plsm_designs_pixel()
    valid = np.ones(_FP.N_DEKADS, bool)

    T = dict(t1=254.5, t2=314.5, t3=324.5, t4=384.5)
    L = dict(a0=-6.3, b1=-9.5, p=-5.2, b2=-8.4)
    s = _plsm_synth(**T, **L)

    for nm, dz in (("free", free), ("pixel", pix)):
        m = plsm_fit(s, valid, dz)
        got = (m["trough"], m["heading"], m["drainage"], m["harvest"])
        want = (T["t1"], T["t2"], T["t3"], T["t4"])
        lev = (abs(m["pre_db"] - L["a0"]) < 1e-6 and abs(m["dark_db"] - L["b1"]) < 1e-6
               and abs(m["plateau_db"] - L["p"]) < 1e-6
               and abs(m["post_db"] - L["b2"]) < 1e-6)
        ok = got == want and lev and m["rmse"] < 1e-9
        ok_all &= ok
        print(f"  {nm:<6s} grid ({len(dz[0]):5d} designs) -> "
              f"{got}  rise {m['rise_db']:.3f} dB  rmse {m['rmse']:.2e}")
        print(f"  [{'PASS' if ok else 'FAIL'}] all four breakpoints and all four "
              f"levels recovered exactly on a noiseless season")

    # the case that forced the fifth segment: a HIGH leading segment. The
    # trapezoid must get t1 wrong here and PLSM must get it right.
    mp_ = plsm_fit(s, valid, free)
    mt = fit_trapezoid(s, valid)
    ok = (mp_["trough"] == T["t1"]
          and (not np.isfinite(mt["trough"]) or mt["trough"] != T["t1"]))
    ok_all &= ok
    print(f"\n  leading-decline season: PLSM trough {mp_['trough']}, trapezoid "
          f"trough {mt['trough']} (truth {T['t1']})")
    print(f"  [{'PASS' if ok else 'FAIL'}] the fifth segment is what recovers "
          f"the trough when the season starts above the dark phase")

    rng = np.random.default_rng(20260912)

    # district-mean noise level, measured at 0.122 dB
    B, S = {}, {}
    draws = [plsm_fit(s + rng.normal(0, 0.122, _FP.N_DEKADS), valid, free)
             for _ in range(120)]
    for k, tr in (("trough", T["t1"]), ("heading", T["t2"]),
                  ("drainage", T["t3"]), ("harvest", T["t4"])):
        v = np.array([d[k] for d in draws], float)
        B[k] = float(np.nanmean(v) - tr); S[k] = float(np.nanstd(v))
    ok = all(abs(B[k]) < 3.0 and S[k] < 5.0 for k in B)
    ok_all &= ok
    print("\n  Monte Carlo at the district-mean noise level (0.122 dB), 120 draws:")
    for k in ("trough", "heading", "drainage", "harvest"):
        print(f"    {k:<9s} bias {B[k]:+6.2f} d   sd {S[k]:5.2f} d")
    print(f"  [{'PASS' if ok else 'FAIL'}] conditional synthetic-recovery check "
          f"passed for planted breakpoints at the assumed 0.122 dB noise level "
          f"(every marker within 3 d of truth, sd under 5 d). This does NOT "
          f"measure the real district panel and does NOT determine the primary "
          f"estimand: the district-season panel is primary because its declared "
          f"estimand is the breakpoint of the district-mean curve (section 3.8)")

    # pixel noise level, measured at 2.03 dB
    B2, S2 = {}, {}
    draws = [plsm_fit(s + rng.normal(0, 2.03, _FP.N_DEKADS), valid, pix)
             for _ in range(120)]
    for k, tr in (("trough", T["t1"]), ("heading", T["t2"]),
                  ("harvest", T["t4"])):
        v = np.array([d[k] for d in draws], float)
        B2[k] = float(np.nanmean(v) - tr); S2[k] = float(np.nanstd(v))
    ok = all(S2[k] > 5.0 for k in S2)      # asserted TO BE large, deliberately
    ok_all &= ok
    print("\n  Monte Carlo at the per-pixel noise level (2.03 dB), 120 draws:")
    for k in ("trough", "heading", "harvest"):
        print(f"    {k:<9s} bias {B2[k]:+6.2f} d   sd {S2[k]:5.2f} d")
    print(f"  [{'PASS' if ok else 'FAIL'}] per-pixel marker sd exceeds 5 d for "
          f"every marker. THIS IS A CONDITIONAL SIMULATION, NOT A MEASUREMENT "
          f"OF THE REAL PANEL: a synthetic season is fitted at an assumed "
          f"noise level and compared with the breakpoints it planted, so the "
          f"number describes the simulation and nothing else. It happens to "
          f"be of the same order as the separately measured split-half "
          f"disagreement (22-34 d on half the observations), which is a "
          f"different quantity again. Neither determines the primary "
          f"estimand, which section 3.8 fixes by declaration")

    # a series with no rise at all must be refused at close to the nominal rate
    kept = [plsm_retain(plsm_fit(rng.normal(-7.0, 2.03, _FP.N_DEKADS), valid,
                                 pix), grid="pixel")[0] for _ in range(400)]
    fp = float(np.mean(kept))
    nom = [plsm_fit(rng.normal(-7.0, 2.03, _FP.N_DEKADS), valid, pix)
           for _ in range(400)]
    fp_nom = float(np.mean([
        (m["rise_t"] is not None and np.isfinite(m["rise_t"])
         and m["rise_t"] >= t_crit95(int(max(m["n_valid"] - 8, 1))))
        for m in nom]))
    ok = fp < 0.08
    ok_all &= ok
    print(f"\n  pure noise, no season: the NOMINAL t test keeps {fp_nom:.3f} of "
          f"400 -- this is why a nominal test cannot be used after breakpoint "
          f"selection")
    print(f"  the selection-aware critical value "
          f"({plsm_t_crit('pixel', 28):.2f}) keeps {fp:.3f}")
    print(f"  [{'PASS' if ok else 'FAIL'}] the calibrated screen holds the "
          f"false-positive rate near its nominal 5%")

    # §3.11 first, and a reason for every refusal
    few = np.zeros(_FP.N_DEKADS, bool); few[:10] = True
    m = plsm_fit(s, few, pix)
    ok1 = "ineligible" in m["reason"] and not np.isfinite(m["trough"])
    okr, why = plsm_retain(m, grid="pixel")
    ok = ok1 and not okr and "ineligible" in why
    ok_all &= ok
    print(f"\n  10 valid dekads -> '{m['reason']}'")
    print(f"  [{'PASS' if ok else 'FAIL'}] §3.11's >=14 rule is applied before "
          f"any fitting, and the refusal carries its reason")

    # the pixel grid must never leave its declared padded window
    lo1, hi1 = PIXEL_GRID_DOY["t1"]; lo4, hi4 = PIXEL_GRID_DOY["t4"]
    keys, _ = pix
    d = _FP.DEKAD_DOY
    ok = all(lo1 <= d[a] <= hi1 and lo4 <= d[dd] <= hi4 for a, b, c, dd in keys)
    ok_all &= ok
    print(f"\n  [{'PASS' if ok else 'FAIL'}] every pixel-grid breakpoint lies "
          f"inside the declared padded baseline window, so the grid cannot "
          f"propose a season it would then refuse")

    # ------------------------------------------------------------------
    # SEMANTIC GUARD, added 2026-09-15 (twelfth pass).
    #
    # Twice now a corrected protocol section has been left contradicted by a
    # string this package PRINTS, and a print statement is read far more often
    # than the section it contradicts. The eleventh pass removed one claim that
    # made a simulation the reason for the primary estimand; the twelfth removed
    # another that called a simulated dispersion a measurement. This test scans
    # the source of EVERY sibling module, in the style of lf_output.py's guard,
    # so a third instance fails the build instead of shipping.
    #
    # Two families are banned:
    #   (a) ESTIMAND SELECTION -- any phrasing that makes a measured or
    #       simulated dispersion the REASON for the level of estimation. The
    #       estimand is fixed by declaration in section 3.8, never by a
    #       dispersion observed or simulated afterwards.
    #   (b) SIMULATION AS MEASUREMENT -- calling a conditional Monte Carlo
    #       result a measurement of the real panel.
    #
    # Source is normalised to single spaces before scanning, so a banned phrase
    # cannot hide by being split across lines inside an f-string.
    import re
    _S = "# SEMANTIC" + " GUARD, added"
    _E = "# GUARD" + "_END"
    BANNED = [
        (r"this is why the (district|pixel)", "estimand selection"),
        (r"(is|are) why .{0,40}(panel|level) is primary", "estimand selection"),
        (r"the reason .{0,30}3\.8 (estimates|clusters)", "estimand selection"),
        (r"why the district-season panel is primary", "estimand selection"),
        (r"so the (district|panel) is primary", "estimand selection"),
        (r"recorded as measured", "simulation as measurement"),
        (r"simulat\w+ (shows|proves|establishes) .{0,30}precision",
         "simulation as measurement"),
        (r"measured precision of the (real )?(district )?panel",
         "simulation as measurement"),
    ]
    _here = os.path.dirname(os.path.abspath(__file__))
    hits, n_mod, n_chars = [], 0, 0
    for _fn in sorted(os.listdir(_here)):
        if not _fn.endswith(".py"):
            continue
        with open(os.path.join(_here, _fn), encoding="utf-8") as _fh:
            _txt = _fh.read()
        _a = _txt.find(_S)
        if _a >= 0:                     # skip this guard's own block
            _b = _txt.find(_E, _a)
            _txt = _txt[:_a] + (_txt[_b:] if _b >= 0 else "")
        _txt = re.sub(r"\s+", " ", _txt)
        n_mod += 1
        n_chars += len(_txt)
        for _pat, _why in BANNED:
            if re.search(_pat, _txt, re.I):
                hits.append((_fn, _pat, _why))
    ok = not hits
    ok_all &= ok
    for _fn, _pat, _why in hits:
        print(f"    BANNED in {_fn} ({_why}): /{_pat}/")
    print(f"\n  scanned {n_chars:,} characters across {n_mod} modules in "
          f"python/ against {len(BANNED)} banned patterns")
    print(f"  [{'PASS' if ok else 'FAIL'}] no estimand-selection or "
          f"simulation-as-measurement claim has returned to any module's "
          f"printed output, docstrings or comments")

    # sabotage check: the guard must actually fire on a planted violation
    _sab = re.sub(r"\s+", " ", "x = 'recorded as measured'")
    ok = any(re.search(_p, _sab, re.I) for _p, _ in BANNED)
    ok_all &= ok
    print(f"  [{'PASS' if ok else 'FAIL'}] the guard fires on a planted "
          f"violation, so a passing scan means the patterns are live")
    # GUARD_END

    print("=" * 74)
    print("PLSM SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return ok_all


def district_mean_curve(V, C, min_coverage=0.5):
    """District-season mean dekadal series, and its sampling standard error.

    A dekad enters the mean only if at least `min_coverage` of the cohort's
    pixels have a valid observation in it. This is the one place §3.1's
    sampling-density idea belongs on the radar path: the mean over a shifting
    subset of pixels is not a time series of the same object, and a dekad
    carried by 6 of 400 pixels (Guntur 2017, DOY 214.5, -11.18 dB against
    -7.8 dB either side) produces a step that is composition, not phenology.
    """
    DV, _ = _FP.aggregate_to_dekads(V, C, np.ones(N_BINS_, dtype=bool))
    n = np.sum(np.isfinite(DV), axis=0).astype(float)
    keep = n >= min_coverage * n.max() if n.max() > 0 else n > 0
    mean = np.full(_FP.N_DEKADS, np.nan)
    sd = np.full(_FP.N_DEKADS, np.nan)
    for k in range(_FP.N_DEKADS):
        if not keep[k]:
            continue
        col = DV[:, k]
        col = col[np.isfinite(col)]
        if col.size:
            mean[k] = float(np.mean(col))
            sd[k] = float(np.std(col, ddof=1)) if col.size > 1 else np.nan
    se = sd / np.sqrt(np.maximum(n, 1.0))
    return mean, sd, se, n, keep


def process_file(path, designs_pixel=None, designs_free=None,
                 gate1_r=GATE1_RATIO_RADAR, smooth=USE_SMOOTHING,
                 min_rise_db=0.0, with_pixels=True):
    """Fit one district-season export at both levels.

    Returns (pixel_rows, district_row, curve_rows). The district row is the
    PRIMARY estimand -- the five-segment fit to the cohort mean curve, free
    breakpoints. The pixel rows carry the same fit on the restricted grid plus
    the two superseded estimators, and exist for §3.10 and for robustness.
    """
    district, year, cells, lon, lat, V, C = read_export(path)

    # ---- primary: the district-season mean curve --------------------------
    mean, sd, se, n_cov, keep = district_mean_curve(V, C)
    valid_d = keep & np.isfinite(mean)
    if designs_free is None:
        designs_free = plsm_designs_free()
    dm = plsm_fit(mean, valid_d, designs_free)
    ok_d, why_d = plsm_retain(dm, min_rise_db=min_rise_db, grid="free")
    drow = dict(district=district, year=year, n_pixels=int(V.shape[0]),
                n_dekads=int(valid_d.sum()),
                se_dekad=(float(np.nanmedian(se[valid_d])) if valid_d.any()
                          else np.nan),
                swing_db=(float(np.nanmax(mean[valid_d])
                                - np.nanmin(mean[valid_d]))
                          if valid_d.any() else np.nan),
                estimable=int(ok_d),
                fail_reason=("" if ok_d else why_d),
                fail_class=classify("" if ok_d else why_d))
    for k in ("trough", "heading", "drainage", "harvest", "pre_db", "dark_db",
              "plateau_db", "post_db", "rise_db", "fall_db", "rise_se",
              "rise_t", "rmse"):
        drow[k] = dm[k]
    drow["veg_days"] = dm["heading"] - dm["trough"]
    drow["plateau_days"] = dm["drainage"] - dm["heading"]
    drow["fill_days"] = dm["harvest"] - dm["heading"]
    drow["season_days"] = dm["harvest"] - dm["trough"]

    curve_rows = [dict(district=district, year=year, dekad=k,
                       doy=float(_FP.DEKAD_DOY[k]), mean_db=mean[k],
                       sd_db=sd[k], se_db=se[k], n_pixels=int(n_cov[k]),
                       used=int(bool(keep[k]))) for k in range(_FP.N_DEKADS)]

    if not with_pixels:
        return [], drow, curve_rows

    # ---- pixel level -----------------------------------------------------
    if gate1_r > 0:
        counts = np.nansum(np.where(np.isfinite(V), C, 0.0), axis=0)
        admitted = _FP.gate1_admitted_bins(counts, gate1_r)
    else:
        admitted = np.ones(N_BINS_, dtype=bool)
    DV, DC = _FP.aggregate_to_dekads(V, C, admitted)
    doy = _FP.DEKAD_DOY
    if designs_pixel is None:
        designs_pixel = plsm_designs_pixel()

    rows = []
    for i in range(DV.shape[0]):
        valid = np.isfinite(DV[i])
        series = np.where(valid, DV[i], 0.0)
        if smooth and valid.sum() >= 4:
            w = np.where(valid, np.maximum(DC[i], 1.0), 0.0)
            series, _, _ = _FP.whittaker_gcv(series, w)

        m = plsm_fit(series, valid, designs_pixel)
        ok, why = plsm_retain(m, min_rise_db=min_rise_db, grid="pixel")
        reason = "" if ok else why

        # superseded arm 1: the trapezoid, §3.2 windows structural
        tz = fit_trapezoid(series, valid)
        tz_ok, _ = retain_trapezoid(tz)
        # superseded arm 2: the crossing rule, searched inside §3.2's own window
        xr = extract_markers(doy, series, valid,
                             trough_window=GATE2["trough"], min_rise_db=0.0)
        xr_ok, _ = retain(xr, min_rise_db=0.0)

        rows.append(dict(
            district=district, year=year, cell_id=cells[i],
            lon=float(lon[i]), lat=float(lat[i]),
            n_valid_dekads=int(m["n_valid"]),
            obs_total=float(np.nansum(np.where(np.isfinite(V[i]), C[i], 0.0))),
            trough=m["trough"], heading=m["heading"], drainage=m["drainage"],
            harvest=m["harvest"], pre_db=m["pre_db"], dark_db=m["dark_db"],
            plateau_db=m["plateau_db"], post_db=m["post_db"],
            rise_db=m["rise_db"], fall_db=m["fall_db"],
            rise_se=m["rise_se"], rise_t=m["rise_t"], rmse=m["rmse"],
            retained=int(ok), fail_reason=reason, fail_class=classify(reason),
            tz_trough=tz["trough"], tz_heading=tz["heading"],
            tz_harvest=tz["harvest"], tz_rise_db=tz["rise_db"],
            tz_retained=int(tz_ok),
            xr_trough=xr["trough"], xr_heading=xr["heading"],
            xr_harvest=xr["harvest"], xr_rise_db=xr["rise_db"],
            xr_retained=int(xr_ok)))
    return rows, drow, curve_rows


# Derived interval outcomes. These are the radar analogue of Paper 1's LOS:
# differences between markers, so a shift common to the whole season (a late
# monsoon, say) cancels out of them.
def add_intervals(df, flag="retained"):
    df["veg_days"] = df["heading"] - df["trough"]
    df["plateau_days"] = df["drainage"] - df["heading"]
    df["fill_days"] = df["harvest"] - df["heading"]
    df["season_days"] = df["harvest"] - df["trough"]
    for c in ("veg_days", "plateau_days", "fill_days", "season_days"):
        df.loc[df[flag] == 0, c] = np.nan
    return df


_WORKER = {}


def _worker_init(min_rise_db, gate1_r, smooth, with_pixels, window_end_doy=None):
    global WINDOW_END_DOY
    WINDOW_END_DOY = window_end_doy      # multiprocessing workers are fresh
    _WORKER["free"] = plsm_designs_free()
    _WORKER["pixel"] = plsm_designs_pixel() if with_pixels else None
    _WORKER["args"] = (gate1_r, smooth, min_rise_db, with_pixels)


def _worker_one(path):
    gate1_r, smooth, min_rise_db, with_pixels = _WORKER["args"]
    return process_file(path, _WORKER["pixel"], _WORKER["free"],
                        gate1_r, smooth, min_rise_db, with_pixels)


def run_panel(exports_dir, out_dir, gate1_r=GATE1_RATIO_RADAR,
              smooth=USE_SMOOTHING, pattern="S1_PHEN_*.csv",
              min_rise_db=0.0, with_pixels=True, jobs=1, window_end_doy=None):
    """Fit every export in a directory; write both panels."""
    files = sorted(glob.glob(os.path.join(exports_dir, pattern)))
    if not files:
        raise SystemExit(f"no {pattern} under {exports_dir}")
    os.makedirs(out_dir, exist_ok=True)
    print(f"panel pass over {len(files)} district-season exports")
    print("  primary   five-segment PLSM on the district-season mean curve, "
          "free breakpoints, no calendar gate")
    print("  pixel arm " + ("PLSM on the padded baseline grid, plus the "
                            "trapezoid and crossing arms" if with_pixels
                            else "skipped"))
    if window_end_doy is not None:
        print(f"  §1.4 WINDOW SWEEP: composites truncated at DOY "
              f"{window_end_doy} -> {bins_within(window_end_doy)} of {N_BINS_} bins")
    print(f"  smoothing={'ON' if smooth else 'OFF'}  gate1_r={gate1_r}  "
          f"rise floor={min_rise_db:.2f} dB  min_dekads={MIN_VALID_DEKADS}  "
          f"jobs={jobs}")

    prows, drows, crows = [], [], []
    t0 = time.time()
    if jobs > 1:
        import multiprocessing as mp
        with mp.Pool(jobs, initializer=_worker_init,
                     initargs=(min_rise_db, gate1_r, smooth,
                               with_pixels, window_end_doy)) as pool:
            for k, (pr, dr, cr) in enumerate(
                    pool.imap(_worker_one, files, chunksize=1), 1):
                prows.extend(pr); drows.append(dr); crows.extend(cr)
                if k % 10 == 0 or k == len(files):
                    print(f"  {k:3d}/{len(files)}  {len(prows):,} pixel-seasons"
                          f"  {time.time() - t0:6.0f}s", flush=True)
    else:
        _worker_init(min_rise_db, gate1_r, smooth, with_pixels, window_end_doy)
        for k, f in enumerate(files, 1):
            pr, dr, cr = _worker_one(f)
            prows.extend(pr); drows.append(dr); crows.extend(cr)
            if k % 10 == 0 or k == len(files):
                print(f"  {k:3d}/{len(files)}  {len(prows):,} pixel-seasons"
                      f"  {time.time() - t0:6.0f}s", flush=True)

    dpan = pd.DataFrame(drows).sort_values(["district", "year"])
    curves = pd.DataFrame(crows).sort_values(["district", "year", "dekad"])
    dpath = os.path.join(out_dir, "phen_panel_district_season.csv")
    cpath = os.path.join(out_dir, "phen_curves_district_season.csv")
    dpan.to_csv(dpath, index=False)
    curves.to_csv(cpath, index=False)

    print("")
    print("=== PRIMARY: district-season panel ===")
    print(f"{len(dpan)} district-seasons | {dpan['district'].nunique()} "
          f"districts | {dpan['year'].min()}-{dpan['year'].max()}")
    print(f"estimable {int(dpan['estimable'].sum())} "
          f"({dpan['estimable'].mean():.4f})")
    e = dpan[dpan["estimable"] == 1]
    print(f"mean-curve sampling se {dpan['se_dekad'].median():.3f} dB | "
          f"fit rmse {e['rmse'].median():.3f} dB | swing "
          f"{dpan['swing_db'].median():.2f} dB")
    for c in ("trough", "heading", "drainage", "harvest", "rise_db",
              "veg_days", "season_days"):
        v = e[c].dropna()
        print(f"  {c:<12s} p5 {v.quantile(.05):7.1f}  med {v.median():7.1f}  "
              f"p95 {v.quantile(.95):7.1f}")
    print("  within-district sd across seasons (the DiD's working variation):")
    for c in ("trough", "heading", "harvest", "rise_db"):
        s = e.groupby("district")[c].std().median()
        print(f"    {c:<10s} {s:.2f}")
    if (dpan["estimable"] == 0).any():
        print("  not estimable:")
        for _, x in dpan[dpan["estimable"] == 0].iterrows():
            print(f"    {x['district']:<20s} {int(x['year'])}  "
                  f"{x['fail_class']}")

    if not with_pixels:
        print("")
        print(f"wrote {dpath}")
        print(f"      {cpath}")
        return dpan, None

    df = add_intervals(pd.DataFrame(prows))
    g = df.groupby("cell_id")[["lon", "lat"]].nunique()
    bad = int(((g > 1).any(axis=1)).sum())
    if bad:
        raise SystemExit(f"{bad} cell_ids carry more than one coordinate; the "
                         "cohort is not stable across seasons")
    ppath = os.path.join(out_dir, "phen_panel_sar.csv")
    df.to_csv(ppath, index=False)
    fails = (df["fail_class"].value_counts(dropna=False)
               .rename_axis("fail_class").reset_index(name="n"))
    fails["share"] = fails["n"] / len(df)
    fpath = os.path.join(out_dir, "phen_panel_sar_failures.csv")
    fails.to_csv(fpath, index=False)

    r = df[df["retained"] == 1]
    print("")
    print("=== pixel arm ===")
    print(f"{len(df):,} pixel-seasons | {df['cell_id'].nunique():,} pixels")
    print(f"valid dekads median {df['n_valid_dekads'].median():.0f}  "
          f"min {df['n_valid_dekads'].min()}  fraction >= "
          f"{MIN_VALID_DEKADS} "
          f"{(df['n_valid_dekads'] >= MIN_VALID_DEKADS).mean():.4f}")
    print(f"retained  PLSM {df['retained'].mean():.4f}  | trapezoid "
          f"{df['tz_retained'].mean():.4f}  | crossings "
          f"{df['xr_retained'].mean():.4f}")
    if len(r):
        for c in ("trough", "heading", "drainage", "harvest", "rise_db",
                  "veg_days", "season_days"):
            print(f"  {c:<12s} median {r[c].median():7.1f}")
    print("why the rest were refused:")
    for _, x in fails.iterrows():
        print(f"  {x['fail_class']:<34s} {int(x['n']):>7,}  {x['share']:.4f}")
    print("")
    print("retention by season:")
    for y, x in df.groupby("year")["retained"].agg(["size", "mean"]).iterrows():
        print(f"  {y}  {int(x['size']):>6,}  {x['mean']:.4f}")
    print("")
    for q in (dpath, cpath, ppath, fpath):
        print(f"wrote {q}")
    return dpan, df

def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Protocol v1 §3 lead-in: radar phenometrics, both panels.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--exports", help="directory of S1_PHEN_<district>_<year>.csv")
    ap.add_argument("--out", help="output directory")
    ap.add_argument("--gate1-r", type=float, default=GATE1_RATIO_RADAR,
                    help="§3.1 sampling-density ratio at pixel level; 0 disables "
                         "the gate, which is the radar default")
    ap.add_argument("--no-pixels", action="store_true",
                    help="fit only the primary district-season panel")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--window-end-doy", type=int, default=None,
                    help="§1.4 window sweep: truncate the per-bin composites at "
                         "this upper endpoint before smoothing and fitting. The "
                         "pre-declared set is 365, 385, 395, 410; omit for the "
                         "425 headline, which is bit-for-bit the committed path.")
    ap.add_argument("--min-rise-db", type=float, default=0.0,
                    help="absolute rise floor in dB for the specification "
                         "curve; 0 leaves the significance screen alone")
    ap.add_argument("--smooth", action="store_true",
                    help="apply the Whittaker smoother; OFF by default")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not (a.exports and a.out):
        ap.error("--exports and --out are both required (or run --selftest)")
    run_panel(a.exports, a.out, a.gate1_r, a.smooth or USE_SMOOTHING,
              min_rise_db=a.min_rise_db, with_pixels=not a.no_pixels,
              window_end_doy=a.window_end_doy,
              jobs=max(1, a.jobs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
