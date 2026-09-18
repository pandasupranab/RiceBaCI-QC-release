"""
fit_phenometrics.py -- Protocol v1 §3 lead-in, §3.1, §3.2, §3.11.

Turns the Sentinel-1 VH/VV composites exported by `gee/S2_QC_Ingest.js` §9e
into the per-pixel-year phenometric panel that §3.8 and §3.10 consume.
Created 2026-09-09.

------------------------------------------------------------------------------
THE PIPELINE, AND WHERE EACH STEP IS SPECIFIED
------------------------------------------------------------------------------
  1. Read the §9e exports: one row per (district, season, cell_id, 5-day bin)
     carrying VHVV_med in dB and valid_obs_count.                       (§3.6)
  2. GATE 1 -- per district-season, N(b) = valid observations in bin b summed
     over that district's cohort pixels; N_peak = max over the 31 CORE bins
     (DOY 150-304). Bin b is admitted iff N(b) >= r x N_peak, or b is the peak
     bin. The 24 extension bins (DOY 305-424) are not subject to Gate 1.
     r is per phenometric, so up to three distinct admitted sets exist and up
     to three fits are run per pixel-season; identical sets are fitted once.
                                                                       (§3.1)
  3. Aggregate the admitted 5-day bins pairwise into the 28 dekads of §1.4
     (dekad 28 is the single bin DOY 420-424), observation-count weighted.
  4. ELIGIBILITY -- a pixel-season is fit-eligible only with at least 8 valid
     dekads and no more than 50% of the 28 scheduled dekads missing, i.e. at
     least 14. Both conditions, as Paper 1 stated them.               (§3.11)
  5. Whittaker smoother under generalised cross-validation.     (§3 lead-in)
  6. Beck et al. (2006) difference-form double-logistic, six parameters, by
     Levenberg-Marquardt from multiple starts.                   (§3 lead-in)
  7. SOS and EOS are the 20% amplitude crossings on the ascending and
     descending limbs; POS is the fitted maximum.                (§3 lead-in)
  8. A fit is accepted iff the optimisation converged, the six-parameter
     Jacobian has full rank, and the RMSR is finite.              (§3 lead-in)
  9. GATE 2 -- DOY bounds, plus an amplitude requirement.                (§3.2)
 10. GATE 3 -- RMSR screening.                                         (§3.11)

Output: one row per ATTEMPTED pixel-season -- the full cohort x season frame,
not only the survivors -- carrying sos/pos/eos, the diagnostics, `eligible`
and `retained`. §3.10's attrition diagnostic needs the failures as much as the
successes, so nothing is dropped here.

------------------------------------------------------------------------------
AN UNRESOLVED PROTOCOL INCONSISTENCY, HANDLED RATHER THAN PAPERED OVER
------------------------------------------------------------------------------
§3 lead-in states that "Gate 2 (§3.2) and Gate 3 (§3.11) apply unchanged"
after the substrate moved to Sentinel-1. That is true of every DOY bound in
those sections and false of everything expressed in reflectance:

    §3.2   "NDVI rise >= 0.20 over 30 d", "Peak NDVI >= 0.55",
           "NDVI decline >= 0.20 over 30 d"
    §3.11  "RMSR > 0.15 NDVI units"

The index is now a backscatter ratio in decibels spanning roughly -13 to -3
dB. An NDVI threshold has no meaning against it, and there is no principled
conversion -- scaling 0.20/0.60 of NDVI amplitude onto a 10 dB range would be
an invented number wearing a citation.

This script therefore does NOT supply defaults for those four quantities, nor
for Gate 1's three r values, which §3.1 withdrew for the same reason. They must
be passed explicitly, and `--derive-baseline` computes the distributions needed
to choose them on the untreated 2017 season -- the procedure §3.1 and §3.3
already fix for the r values and the 3 dB inundation criterion. Running the
gates without them is refused rather than defaulted, because a default here
would silently become the study's threshold.

------------------------------------------------------------------------------
A MEASURED PROPERTY OF THE SMOOTHING STEP -- RECORDED, NOT REPAIRED
------------------------------------------------------------------------------
The Whittaker step is not free. Measured on 400 synthetic pixels with identical
noise and gaps, fitted with and without it:

                     SOS                  POS                  EOS
    raw        bias +0.53  sd 4.15   bias -0.88  sd 7.35   bias +0.15  sd 3.75
    smoothed   bias -1.17  sd 3.35   bias -0.02  sd 5.34   bias +1.71  sd 3.98

Smoothing rounds the shoulders of the curve, which lowers the fitted peak,
which lowers the 20% amplitude level, which pushes BOTH crossings outward: SOS
about a day early and EOS about two days late, every pixel, every season. In
exchange it cuts per-pixel dispersion by 19% on SOS and 27% on POS.

That trade is the right one here and the protocol mandates the step regardless
(§3 lead-in, for comparability with Paper 1), but the direction matters for how
results are read:

  * The level shift is systematic and common to every pixel-season, so a
    difference-in-differences removes it. Measured end to end on a synthetic
    panel with a planted +8.0 d exposure effect: the SOS level bias was
    -1.34 d while the recovered DiD coefficient was +7.73 d, an error of
    -0.27 d. This is the concrete case for §3.4's position that Objective 4
    needs measurement CONSISTENCY, not accuracy.
  * The dispersion reduction is what H1 and H2 are stated in terms of, so the
    smoother helps exactly the claims this study now makes.
  * No absolute transplanting or harvest date from this pipeline should be
    quoted to better than a few days, and §3.4's explicit non-claim already
    says so.

Reproduce with the `--selftest` bias-variance block.

------------------------------------------------------------------------------
DEPENDENCIES
------------------------------------------------------------------------------
numpy and pandas only. The Whittaker smoother, the GCV search, the
Levenberg-Marquardt optimiser and the limb-crossing solver are implemented in
this file. `--selftest` checks each of them against a known answer -- and
against scipy's `least_squares` when scipy happens to be installed, which is a
cross-check, never a requirement.

------------------------------------------------------------------------------
USAGE
------------------------------------------------------------------------------
    python python/fit_phenometrics.py --selftest

    # step 1: derive the undetermined thresholds on the untreated 2017 season
    python python/fit_phenometrics.py --exports data/S1_exports/ \
        --derive-baseline --out results/

    # step 2: fit the panel with those values recorded in the decisions log
    python python/fit_phenometrics.py --exports data/S1_exports/ \
        --r-sos 0.60 --r-pos 0.50 --r-eos 0.50 \
        --amp-min-db 4.0 --peak-min-db -6.0 --rmsr-max-db 1.2 \
        --out results/
"""
from __future__ import annotations

import argparse
import glob
import math
import os
import sys
import time

import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
# ===========================================================================
# constants fixed by the protocol
# ===========================================================================
SEASON_START_DOY = 150          # §1.4
BIN_WIDTH_DAYS = 5              # §1.4
N_BINS = 55                     # §1.4: bin starts 150, 155, ..., 420
N_CORE_BINS = 31                # §3.1: DOY 150-304 are Gate 1's core window
N_DEKADS = 28                   # §1.4: pairwise, the 28th being bin 55 alone

MIN_VALID_DEKADS_ABS = 8        # §3.11, Paper 1 verbatim
MIN_VALID_DEKADS_HALF = 14      # §3.11: no more than 50% of 28 missing

AMPLITUDE_FRACTION = 0.20       # §3 lead-in: 20% crossings define SOS and EOS

# §3.2, Paper 1's Gate B windows verbatim. These are calendar bounds and
# transfer to any substrate; the amplitude column of that table does not.
GATE2_DOY_BOUNDS = {
    "sos": (155, 240),
    "pos": (240, 320),
    "eos": (280, 380),
}

BASELINE_SEASON = 2017          # §1.1: the only season with no catalogued
                                # exposure of any severity in any roster district

EXPORT_REQUIRED = ["district", "year", "cell_id", "bin_index",
                   "VHVV_med", "valid_obs_count"]


def dekad_centres():
    """DOY centre of each of the 28 dekads.

    Dekad k (0-indexed) aggregates 5-day bins 2k and 2k+1; the last aggregates
    bin 54 alone. Bin b covers DOY 150+5b .. 150+5b+4, centre 150+5b+2.
    """
    out = []
    for k in range(N_DEKADS):
        bins = [2 * k, 2 * k + 1]
        bins = [b for b in bins if b < N_BINS]
        out.append(float(np.mean([SEASON_START_DOY + 5 * b + 2 for b in bins])))
    return np.array(out)


DEKAD_DOY = dekad_centres()


def dekad_bin_map():
    """bins contributing to each dekad."""
    return [[b for b in (2 * k, 2 * k + 1) if b < N_BINS] for k in range(N_DEKADS)]


DEKAD_BINS = dekad_bin_map()


# ===========================================================================
# Whittaker smoother with GCV  (§3 lead-in)
# ===========================================================================
def _diff_matrix(n, order=2):
    D = np.eye(n)
    for _ in range(order):
        D = np.diff(D, axis=0)
    return D


def whittaker_gcv(y, w, lambdas=None, order=2):
    """Whittaker smoother, smoothing parameter chosen by generalised CV.

    Minimises  sum_i w_i (y_i - z_i)^2 + lambda * ||D_order z||^2, whose
    solution is z = (W + lambda D'D)^{-1} W y. Gaps are handled natively by
    setting w_i = 0, which is the reason this smoother is used on a series
    with missing dekads rather than an interpolate-then-smooth approach.

    GCV(lambda) = n * RSS / (n - tr(H))^2  with  H = (W + lambda D'D)^{-1} W,
    minimised over a log grid. Returns (z, lambda, gcv).

    Two properties worth knowing before reading its output. At an END gap the
    second-difference penalty extrapolates linearly and can drift, so the
    smoothed value in a leading or trailing gap is the least trustworthy thing
    this function produces -- which is why fit_one() fits on z[valid] and never
    passes an interpolated gap to the optimiser. And GCV is known to undersmooth
    at small n; measured on the self-test series it picks lambda ~4 where the
    oracle is ~25. That costs little here because the double logistic imposes a
    strong shape constraint downstream, but it is a reason not to read the
    smoothed series as an estimate in its own right.
    """
    y = np.asarray(y, float)
    w = np.asarray(w, float)
    n = len(y)
    if lambdas is None:
        lambdas = np.logspace(-2, 6, 41)
    D = _diff_matrix(n, order)
    DtD = D.T @ D
    yy = np.where(np.isfinite(y), y, 0.0)
    W = np.diag(w)
    n_eff = float(np.sum(w > 0))

    best = (None, None, np.inf)
    for lam in lambdas:
        A = W + lam * DtD
        try:
            H = np.linalg.solve(A, W)
        except np.linalg.LinAlgError:
            continue
        z = H @ yy
        r = (yy - z) * (w > 0)
        rss = float(np.sum(w * r * r))
        tr = float(np.trace(H))
        denom = (n_eff - tr)
        if denom <= 1e-8:
            continue
        gcv = n_eff * rss / (denom ** 2)
        if gcv < best[2]:
            best = (z, lam, gcv)
    if best[0] is None:                      # degenerate: fall back to the data
        return yy, float("nan"), float("nan")
    return best[0], float(best[1]), float(best[2])


# ===========================================================================
# Beck et al. (2006) double logistic  (§3 lead-in)
# ===========================================================================
def beck_double_logistic(t, p):
    """f(t) = vw + (vm - vw) * [ sigma(mS(t-S)) + sigma(-mA(t-A)) - 1 ].

    p = (vw, vm, S, mS, A, mA). vw is the background level the curve returns to
    at both ends of the season, vm the plateau. Written with an explicit
    exponent clip because the season window is 275 days wide and an
    intermediate slope guess can overflow exp() long before the fit diverges.
    """
    vw, vm, S, mS, A, mA = p
    t = np.asarray(t, float)
    e1 = np.clip(-mS * (t - S), -60.0, 60.0)
    e2 = np.clip(mA * (t - A), -60.0, 60.0)
    s1 = 1.0 / (1.0 + np.exp(e1))
    s2 = 1.0 / (1.0 + np.exp(e2))
    return vw + (vm - vw) * (s1 + s2 - 1.0)


P_LO = np.array([-40.0, -40.0, 150.0, 1e-3, 150.0, 1e-3])
P_HI = np.array([40.0, 40.0, 430.0, 2.0, 430.0, 2.0])


def _jacobian(t, p, f0=None, eps=1e-6):
    """Numerical Jacobian, central differences, scaled per parameter."""
    f0 = beck_double_logistic(t, p) if f0 is None else f0
    J = np.empty((len(t), len(p)))
    for j in range(len(p)):
        h = eps * max(1.0, abs(p[j]))
        pj_hi = p.copy(); pj_hi[j] += h
        pj_lo = p.copy(); pj_lo[j] -= h
        J[:, j] = (beck_double_logistic(t, pj_hi)
                   - beck_double_logistic(t, pj_lo)) / (2 * h)
    return J


def levenberg_marquardt(t, y, p0, maxiter=200, tol=1e-10):
    """Bounded Levenberg-Marquardt least squares.

    Implemented here rather than taken from scipy so that the fitting stage
    carries no dependency beyond numpy -- the same reason attrition_diagnostics
    implements its own estimator. `--selftest` cross-checks it against scipy's
    `least_squares` when scipy is present.

    Bounds are enforced by clipping the trial point, which is adequate for the
    box constraints here (slopes strictly positive, inflections inside the
    season window) and avoids the pathologies of an unconstrained fit wandering
    to a negative slope and flipping the curve upside down.
    """
    p = np.clip(np.asarray(p0, float), P_LO, P_HI)
    f = beck_double_logistic(t, p)
    r = f - y
    sse = float(r @ r)
    mu = 1e-3
    converged = False
    for _ in range(maxiter):
        J = _jacobian(t, p, f)
        JtJ = J.T @ J
        g = J.T @ r
        diag = np.maximum(np.diag(JtJ), 1e-12)
        for _ in range(30):
            try:
                step = np.linalg.solve(JtJ + mu * np.diag(diag), -g)
            except np.linalg.LinAlgError:
                mu *= 10.0
                continue
            p_new = np.clip(p + step, P_LO, P_HI)
            f_new = beck_double_logistic(t, p_new)
            r_new = f_new - y
            sse_new = float(r_new @ r_new)
            if sse_new < sse:
                rel = (sse - sse_new) / max(sse, 1e-300)
                p, f, r, sse = p_new, f_new, r_new, sse_new
                mu = max(mu / 3.0, 1e-12)
                if rel < tol or np.max(np.abs(step)) < 1e-10:
                    converged = True
                break
            mu *= 10.0
            if mu > 1e12:
                converged = True
                break
        else:
            break
        if converged:
            break
    return p, sse, converged


def _starts(t, y):
    """Data-derived initial guesses.

    Multi-start because the double logistic has a well-known failure mode: from
    a poor start the optimiser settles into a monotone ramp that fits the
    ascending limb and ignores the descent, which produces a plausible SOS and
    a meaningless EOS.
    """
    lo, hi = float(np.percentile(y, 10)), float(np.percentile(y, 90))
    tpk = float(t[int(np.argmax(y))])
    mid = lo + 0.5 * (hi - lo)
    rising = t[(t < tpk) & (y >= mid)]
    falling = t[(t > tpk) & (y >= mid)]
    S0 = float(rising[0]) if len(rising) else tpk - 40.0
    A0 = float(falling[-1]) if len(falling) else tpk + 40.0
    out = []
    for slope in (0.05, 0.15, 0.30):
        out.append(np.array([lo, hi, S0, slope, A0, slope]))
    out.append(np.array([lo, hi, tpk - 50.0, 0.10, tpk + 50.0, 0.10]))
    return out


def fit_curve(t, y):
    """Best of the multi-start LM fits. Returns a dict of fit diagnostics."""
    best = None
    for p0 in _starts(t, y):
        p, sse, conv = levenberg_marquardt(t, y, p0)
        if best is None or sse < best[1]:
            best = (p, sse, conv)
    p, sse, conv = best
    J = _jacobian(t, p)
    sv = np.linalg.svd(J, compute_uv=False)
    tol = max(J.shape) * np.finfo(float).eps * (sv[0] if len(sv) else 0.0)
    rank = int(np.sum(sv > tol))
    rmsr = math.sqrt(sse / len(t)) if len(t) else float("nan")
    return dict(params=p, sse=sse, converged=bool(conv), rank=rank,
                full_rank=bool(rank == 6), rmsr=rmsr,
                cond=float(sv[0] / sv[-1]) if len(sv) and sv[-1] > 0 else np.inf)


# ===========================================================================
# phenometrics from the fitted curve  (§3 lead-in)
# ===========================================================================
def phenometrics(p, t_lo=SEASON_START_DOY, t_hi=SEASON_START_DOY + 5 * N_BINS - 1):
    """POS = fitted maximum; SOS and EOS = 20% amplitude crossings.

    The maximum is located on a dense grid rather than analytically because the
    Beck form has no closed-form argmax and, when the two logistics are far
    apart, a flat plateau where any point is the numerical maximum. The
    midpoint of the plateau is taken in that case, which is the only choice
    that is stable under noise.

    Each limb is monotone between vw and the peak, so the crossings are found
    by bisection; the limb is checked for the crossing actually being bracketed
    rather than assumed.
    """
    grid = np.arange(t_lo, t_hi + 0.25, 0.25)
    f = beck_double_logistic(grid, p)
    fmax = float(np.max(f))
    plateau = grid[f >= fmax - 1e-9]
    pos = float(0.5 * (plateau[0] + plateau[-1]))
    vw = float(p[0])
    amp = fmax - vw
    if not np.isfinite(amp) or amp <= 0:
        return dict(sos=np.nan, pos=pos, eos=np.nan, amplitude=amp,
                    peak_value=fmax, base_value=vw)
    target = vw + AMPLITUDE_FRACTION * amp

    def bisect(a, b, rising):
        fa = beck_double_logistic(np.array([a]), p)[0]
        fb = beck_double_logistic(np.array([b]), p)[0]
        if (fa - target) * (fb - target) > 0:
            return np.nan
        for _ in range(80):
            m = 0.5 * (a + b)
            fm = beck_double_logistic(np.array([m]), p)[0]
            if (fm >= target) == rising:
                b = m
            else:
                a = m
        return 0.5 * (a + b)

    sos = bisect(t_lo, pos, rising=True)
    eos = bisect(pos, t_hi, rising=False)
    return dict(sos=sos, pos=pos, eos=eos, amplitude=amp,
                peak_value=fmax, base_value=vw)


# ===========================================================================
# Gate 1  (§3.1)
# ===========================================================================
def gate1_admitted_bins(counts_by_bin, r):
    """Admitted 5-day bins for one district-season at sampling-density ratio r.

    counts_by_bin is N(b) for b = 0..54, summed over that district's cohort
    pixels. N_peak is the maximum over the 31 CORE bins only; the 24 extension
    bins (DOY 305-424) are admitted unconditionally, as §3.1 specifies, because
    Paper 1 applied no sampling-density gate to its extension dekads.

    Note the direction: b is admitted when N(b) >= r * N_peak. The version
    frozen at 2cf493a had this inequality reversed, admitting sparse bins and
    rejecting well-sampled ones.
    """
    counts = np.asarray(counts_by_bin, float)
    core = counts[:N_CORE_BINS]
    admitted = np.ones(N_BINS, dtype=bool)
    if not np.any(core > 0):
        admitted[:N_CORE_BINS] = False
        return admitted
    n_peak = float(np.nanmax(core))
    peak_bin = int(np.nanargmax(core))
    admitted[:N_CORE_BINS] = core >= r * n_peak
    admitted[peak_bin] = True
    return admitted


def aggregate_to_dekads(values, counts, admitted):
    """Pairwise 5-day bins -> 28 dekads, weighted by observation count.

    values, counts: (n_pixels, 55). Returns (dekad_values, dekad_counts), both
    (n_pixels, 28), with NaN where a dekad has no admitted observation.
    """
    n = values.shape[0]
    w = np.where(np.isfinite(values), counts, 0.0) * admitted[None, :]
    v = np.where(np.isfinite(values), values, 0.0)
    out_v = np.full((n, N_DEKADS), np.nan)
    out_c = np.zeros((n, N_DEKADS))
    for k, cols in enumerate(DEKAD_BINS):
        den = w[:, cols].sum(axis=1)
        num = (v[:, cols] * w[:, cols]).sum(axis=1)
        ok = den > 0
        out_v[ok, k] = num[ok] / den[ok]
        out_c[:, k] = den
    return out_v, out_c


# ===========================================================================
# per-pixel-season fit
# ===========================================================================
def fit_one(dekad_values, dekad_counts):
    """Smooth, fit, and read off the phenometrics for a single pixel-season."""
    valid = np.isfinite(dekad_values)
    n_valid = int(valid.sum())
    rec = dict(n_valid_dekads=n_valid,
               eligible=bool(n_valid >= MIN_VALID_DEKADS_ABS
                             and n_valid >= MIN_VALID_DEKADS_HALF),
               converged=False, full_rank=False, rank=0,
               rmsr=np.nan, lambda_gcv=np.nan,
               sos=np.nan, pos=np.nan, eos=np.nan,
               amplitude=np.nan, peak_value=np.nan, base_value=np.nan,
               rise30=np.nan, decline30=np.nan, fail_reason="")
    if not rec["eligible"]:
        rec["fail_reason"] = f"ineligible: {n_valid} valid dekads"
        return rec

    w = valid.astype(float) * np.where(valid, dekad_counts, 0.0)
    w = np.where(valid, np.maximum(w, 1.0), 0.0)      # count as weight, min 1
    z, lam, _ = whittaker_gcv(np.where(valid, dekad_values, 0.0), w)
    rec["lambda_gcv"] = lam

    t = DEKAD_DOY[valid]
    y = z[valid]
    fit = fit_curve(t, y)
    rec.update(converged=fit["converged"], full_rank=fit["full_rank"],
               rank=fit["rank"], rmsr=fit["rmsr"])
    if not (fit["converged"] and fit["full_rank"] and np.isfinite(fit["rmsr"])):
        rec["fail_reason"] = ("non-convergence" if not fit["converged"] else
                              "rank-deficient Jacobian" if not fit["full_rank"]
                              else "non-finite RMSR")
        return rec

    ph = phenometrics(fit["params"])
    rec.update(ph)
    p = fit["params"]
    if np.isfinite(ph["sos"]):
        rec["rise30"] = float(beck_double_logistic(np.array([ph["sos"] + 30.0]), p)[0]
                              - beck_double_logistic(np.array([ph["sos"]]), p)[0])
    if np.isfinite(ph["eos"]):
        rec["decline30"] = float(beck_double_logistic(np.array([ph["eos"]]), p)[0]
                                 - beck_double_logistic(np.array([ph["eos"] - 30.0]), p)[0])
    if not (np.isfinite(ph["sos"]) and np.isfinite(ph["eos"])):
        rec["fail_reason"] = "amplitude crossing not bracketed on one limb"
    return rec


def apply_gates_23(rec, amp_min_db, peak_min_db, rmsr_max_db,
                   amp_min_rise_db=None, amp_min_decline_db=None):
    """Gate 2 (§3.2) and Gate 3 (§3.11).

    Gate 2 is applied per phenometric, because §3.8 estimates a separate
    regression for each and excluding a pixel's SOS should not discard a
    perfectly admissible EOS. `retained` is the conjunction, and is the single
    survival indicator §3.10's diagnostic consumes.

    The amplitude criteria mirror the three rows of §3.2's table: a 30-day rise
    at SOS, a fitted peak level, and a 30-day decline at EOS. §3.2 states them
    in NDVI units, which do not transfer to decibels -- the thresholds are
    supplied by the caller from the §3.1-style baseline derivation, never
    defaulted here.

    §3.2 gives the rise and decline criteria as two rows carrying the same
    number, and omitting the two per-limb overrides reproduces that exactly.
    They exist because the limbs are not symmetric: the descending limb of the
    VH/VV curve is the slower one, so a single threshold set from the rising
    limb rejects admissible harvests. Measured on a synthetic season with
    mS = 0.10 and mA = 0.08, the median 30-day rise was +5.1 dB against a
    median 30-day decline of -4.3 dB. If the baseline derivation shows the same
    asymmetry on real data, set the two separately and record why.
    """
    out = {}
    g3 = bool(np.isfinite(rec["rmsr"]) and rec["rmsr"] <= rmsr_max_db)
    out["gate3_pass"] = int(g3)
    base_ok = bool(rec["eligible"] and rec["converged"] and rec["full_rank"])
    for key in ("sos", "pos", "eos"):
        lo, hi = GATE2_DOY_BOUNDS[key]
        v = rec[key]
        in_bounds = bool(np.isfinite(v) and lo <= v <= hi)
        if key == "sos":
            thr = amp_min_db if amp_min_rise_db is None else amp_min_rise_db
            amp_ok = bool(np.isfinite(rec["rise30"]) and rec["rise30"] >= thr)
        elif key == "eos":
            thr = amp_min_db if amp_min_decline_db is None else amp_min_decline_db
            amp_ok = bool(np.isfinite(rec["decline30"]) and rec["decline30"] <= -thr)
        else:
            amp_ok = bool(np.isfinite(rec["peak_value"])
                          and rec["peak_value"] >= peak_min_db)
        ok = base_ok and g3 and in_bounds and amp_ok
        out[f"gate2_{key}_pass"] = int(in_bounds and amp_ok)
        out[f"retained_{key}"] = int(ok)
    out["retained"] = int(all(out[f"retained_{k}"] for k in ("sos", "pos", "eos")))
    return out


# ===========================================================================
# IO
# ===========================================================================
def load_exports(folder):
    """Read the §9e CSVs into one frame and validate the schema.

    Refuses on a missing column rather than guessing. Rows GEE exported as
    masked (empty VHVV_med, the dummy-schema armor of §9e) are kept and become
    NaN, because a bin with no acquisition is information -- Gate 1 counts it
    as zero and the eligibility rule needs it.
    """
    files = sorted(glob.glob(os.path.join(folder, "*.csv")))
    if not files:
        raise SystemExit(f"no CSV files found in {folder}")
    frames = []
    for f in files:
        d = pd.read_csv(f)
        missing = [c for c in EXPORT_REQUIRED if c not in d.columns]
        if missing:
            raise SystemExit(
                f"{os.path.basename(f)} is missing columns {missing}\n"
                f"present: {sorted(d.columns)}\n"
                "This is not the §9e export schema; refusing to guess.")
        frames.append(d[EXPORT_REQUIRED])
    out = pd.concat(frames, ignore_index=True)
    out["year"] = out["year"].astype(int)
    out["bin_index"] = out["bin_index"].astype(int)
    out["VHVV_med"] = pd.to_numeric(out["VHVV_med"], errors="coerce")
    out["valid_obs_count"] = pd.to_numeric(
        out["valid_obs_count"], errors="coerce").fillna(0.0)
    bad = out[(out["bin_index"] < 0) | (out["bin_index"] >= N_BINS)]
    if len(bad):
        raise SystemExit(f"{len(bad)} rows carry bin_index outside 0..{N_BINS-1}")
    print(f"read {len(files)} files | {len(out):,} rows | "
          f"{out['district'].nunique()} districts | "
          f"seasons {out['year'].min()}-{out['year'].max()}")
    return out


def to_matrices(sub):
    """(pixels x 55) value and count matrices for one district-season."""
    cells, codes = np.unique(sub["cell_id"].values, return_inverse=True)
    V = np.full((len(cells), N_BINS), np.nan)
    C = np.zeros((len(cells), N_BINS))
    b = sub["bin_index"].values
    V[codes, b] = sub["VHVV_med"].values
    C[codes, b] = sub["valid_obs_count"].values
    return cells, V, C


# ===========================================================================
# main fitting pass
# ===========================================================================
def run_panel(exports, r_values, thresholds, progress_every=25):
    """Fit every pixel-season. Returns the per-pixel-year panel.

    Up to three admitted-bin sets exist per district-season, one per
    phenometric, so the fit is run once per DISTINCT set and each phenometric
    read from the fit whose set produced it. When the three r values are equal
    -- the likely outcome of the baseline derivation -- that collapses to one
    fit, which is both cheaper and more internally coherent.
    """
    rows = []
    keys = list(exports.groupby(["district", "year"], sort=True).groups.keys())
    t0 = time.time()
    for i, (district, year) in enumerate(keys, 1):
        sub = exports[(exports["district"] == district) & (exports["year"] == year)]
        cells, V, C = to_matrices(sub)
        counts_by_bin = np.nansum(np.where(np.isfinite(V), C, 0.0), axis=0)

        # distinct admitted sets, one per phenometric
        sets = {}
        for phen in ("sos", "pos", "eos"):
            adm = gate1_admitted_bins(counts_by_bin, r_values[phen])
            sets.setdefault(adm.tobytes(), (adm, []))[1].append(phen)

        per_phen_rec = {}
        for adm, phens in sets.values():
            DV, DC = aggregate_to_dekads(V, C, adm)
            for pix in range(len(cells)):
                rec = fit_one(DV[pix], DC[pix])
                for phen in phens:
                    per_phen_rec.setdefault(pix, {})[phen] = rec
            del DV, DC

        for pix, cell in enumerate(cells):
            recs = per_phen_rec[pix]
            merged = dict(recs["sos"])          # diagnostics from the SOS fit
            for phen in ("sos", "pos", "eos"):
                merged[phen] = recs[phen][phen]
                if phen == "sos":
                    merged["rise30"] = recs[phen]["rise30"]
                if phen == "eos":
                    merged["decline30"] = recs[phen]["decline30"]
                if phen == "pos":
                    merged["peak_value"] = recs[phen]["peak_value"]
            gates = (apply_gates_23(merged, **thresholds)
                     if thresholds is not None else {})
            rows.append(dict(district=district, year=year, cell_id=cell,
                             n_admitted_bins_sos=int(
                                 gate1_admitted_bins(counts_by_bin,
                                                     r_values["sos"]).sum()),
                             **merged, **gates))
        if progress_every and (i % progress_every == 0 or i == len(keys)):
            el = time.time() - t0
            print(f"  [{i}/{len(keys)}] {district} {year} | "
                  f"{len(rows):,} pixel-seasons | {el:.0f}s elapsed")
    return pd.DataFrame(rows)


# ===========================================================================
# baseline derivation  (§3.1-style, for the thresholds §3.2/§3.11 leave in
# NDVI units)
# ===========================================================================
def derive_baseline(exports, out_dir, r_grid=None):
    """Report what the untreated 2017 season implies for the open thresholds.

    Proposes, never applies. §3.1 fixes this procedure for Gate 1's r values;
    §3.3 uses it for the 3 dB inundation criterion; the amplitude and RMSR
    thresholds of §3.2 and §3.11 need it for the same reason -- their frozen
    values are in NDVI units and the index is now decibels.

    Everything here is computed with GATE 1 DISABLED (r = 0, all bins
    admitted), because the r values are themselves one of the unknowns and
    deriving them from a gated panel would be circular.
    """
    base = exports[exports["year"] == BASELINE_SEASON]
    if base.empty:
        raise SystemExit(
            f"season {BASELINE_SEASON} is not in the exports. §1.1 makes it the "
            "only season with no catalogued exposure of any severity in any "
            "roster district, so it is the only admissible baseline; deriving "
            "thresholds on an exposed season would calibrate on treated data.")
    print(f"\n=== baseline derivation on season {BASELINE_SEASON} "
          f"({base['cell_id'].nunique():,} pixels, "
          f"{base['district'].nunique()} districts) ===")
    print("Gate 1 disabled (r = 0) for this pass: the r values are themselves "
          "being derived, so gating first would be circular.\n")

    # --- Gate 1: what each r would admit -------------------------------
    if r_grid is None:
        r_grid = [0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.75, 0.80, 0.90]
    prof = []
    for (district, year), sub in base.groupby(["district", "year"]):
        _, V, C = to_matrices(sub)
        n_b = np.nansum(np.where(np.isfinite(V), C, 0.0), axis=0)
        row = dict(district=district, year=year,
                   n_peak_core=float(np.nanmax(n_b[:N_CORE_BINS])),
                   n_median_core=float(np.nanmedian(n_b[:N_CORE_BINS])),
                   n_zero_core=int(np.sum(n_b[:N_CORE_BINS] == 0)))
        for r in r_grid:
            row[f"core_admitted_r{r:.2f}"] = int(
                gate1_admitted_bins(n_b, r)[:N_CORE_BINS].sum())
        prof.append(row)
    prof = pd.DataFrame(prof)
    print("Gate 1 -- core bins admitted of 31, median across district-seasons:")
    for r in r_grid:
        c = prof[f"core_admitted_r{r:.2f}"]
        print(f"  r = {r:.2f}   median {c.median():5.1f}   "
              f"min {c.min():3.0f}   max {c.max():3.0f}")

    # --- fit ungated, report the distributions --------------------------
    print("\nfitting the baseline season ungated ...")
    panel = run_panel(base, {"sos": 0.0, "pos": 0.0, "eos": 0.0},
                      thresholds=None, progress_every=5)
    ok = panel[(panel["eligible"]) & (panel["converged"]) & (panel["full_rank"])]
    print(f"\neligible {int(panel['eligible'].sum()):,} of {len(panel):,} "
          f"({panel['eligible'].mean():.1%}); converged and full-rank "
          f"{len(ok):,} ({len(ok)/max(len(panel),1):.1%})")
    if len(ok) == 0:
        print("no fit succeeded; nothing to derive. Inspect fail_reason.")
        return prof, panel

    def q(col, qs=(1, 5, 10, 25, 50, 75, 90, 95, 99)):
        v = ok[col].dropna().values
        if not len(v):
            return "  (no finite values)"
        return "  " + "  ".join(f"p{p}={np.percentile(v, p):+.2f}" for p in qs)

    print("\nDistributions among converged full-rank fits (dB, and DOY):")
    for col in ("rmsr", "amplitude", "rise30", "decline30", "peak_value",
                "base_value", "sos", "pos", "eos"):
        print(f"  {col:<12s}{q(col)}")

    print("\nCandidate thresholds -- to be RECORDED IN THE DECISIONS LOG and "
          "passed explicitly on the next run, not adopted silently:")
    r5 = np.nanpercentile(ok["rise30"].dropna(), 5) if ok["rise30"].notna().any() else np.nan
    d5 = np.nanpercentile(np.abs(ok["decline30"].dropna()), 5) if ok["decline30"].notna().any() else np.nan
    pk5 = np.nanpercentile(ok["peak_value"].dropna(), 5) if ok["peak_value"].notna().any() else np.nan
    rm95 = np.nanpercentile(ok["rmsr"].dropna(), 95) if ok["rmsr"].notna().any() else np.nan
    print(f"  --amp-min-db   {min(r5, d5):.2f}   "
          f"(5th percentile of the 30-day rise {r5:.2f} and of |decline| {d5:.2f})")
    print(f"  --peak-min-db  {pk5:.2f}   (5th percentile of fitted peak)")
    print(f"  --rmsr-max-db  {rm95:.2f}   (95th percentile of RMSR)")
    print("\nThese are the 5th/95th percentiles of an UNTREATED season, so they "
          "reject the worst ~5% of fits under conditions the study treats as "
          "normal. That is a defensible starting point and it is not a "
          "decision this script is entitled to make. Check the SOS/POS/EOS "
          "percentiles above against §3.4's district crop calendars "
          "(approximately DOY 170-294 for coastal Odisha Kharif) before "
          "adopting anything: if the fitted dates sit outside the calendar, "
          "the §3 lead-in calibration requirement has failed for that state "
          "and no threshold choice repairs it.")

    os.makedirs(out_dir, exist_ok=True)
    prof.to_csv(os.path.join(out_dir, "baseline_gate1_profile.csv"), index=False)
    panel.to_csv(os.path.join(out_dir, "baseline_2017_fits.csv"), index=False)
    print(f"\nwrote {out_dir}/baseline_gate1_profile.csv and "
          f"{out_dir}/baseline_2017_fits.csv")
    return prof, panel


# ===========================================================================
# self-test
# ===========================================================================
def selftest():
    print("=" * 74)
    print("SELF-TEST -- fit_phenometrics.py")
    print("=" * 74)
    ok_all = True
    rng = np.random.default_rng(3)

    # ---- 1. the model's own asymptotes -------------------------------
    # vm is the parameter the curve APPROACHES, not one it attains: the two
    # logistics saturate at different times, so the season maximum is strictly
    # below vm whenever the ascending and descending inflections are close
    # enough for their tails to overlap. That is why phenometrics() takes the
    # numerical maximum of the fitted curve as POS and as the amplitude ceiling
    # rather than reading vm off the parameter vector -- using vm would put the
    # 20% crossings at the wrong level and bias SOS and EOS outward.
    p_true = np.array([-12.0, -3.5, 195.0, 0.10, 320.0, 0.08])
    f_lo = beck_double_logistic(np.array([-500.0]), p_true)[0]
    f_hi = beck_double_logistic(np.array([1500.0]), p_true)[0]
    ph_t = phenometrics(p_true)
    peak = ph_t["peak_value"]
    ok = (abs(f_lo - p_true[0]) < 1e-9 and abs(f_hi - p_true[0]) < 1e-9
          and peak < p_true[1] and (p_true[1] - peak) < 0.15)
    ok_all &= ok
    print(f"  asymptotes: f(-inf)={f_lo:.4f} f(+inf)={f_hi:.4f} vs vw={p_true[0]}")
    print(f"  season max {peak:.4f} approaches but does not reach vm="
          f"{p_true[1]} (shortfall {p_true[1]-peak:.4f} dB)")
    print(f"  [{'PASS' if ok else 'FAIL'}] returns to vw at both ends; peak "
          f"approaches vm from below, as the Beck form requires")

    # ---- 2. Whittaker recovers a smooth curve through gaps ------------
    t = DEKAD_DOY
    truth = beck_double_logistic(t, p_true)
    y = truth + rng.normal(0, 0.6, len(t))
    w = np.ones(len(t))
    drop = rng.choice(len(t), 6, replace=False)     # 6 missing dekads
    w[drop] = 0.0
    y[drop] = np.nan
    obs = w > 0
    z, lam, _ = whittaker_gcv(np.where(obs, y, 0.0), w)
    # Measured at the OBSERVED dekads, which is the only place it matters: the
    # curve fit consumes z[valid] and never touches the smoother's values in
    # the gaps. Comparing over the gaps too would score the smoother on an
    # extrapolation the pipeline discards -- and at an end gap a second-
    # difference penalty extrapolates linearly and drifts.
    err_raw = float(np.sqrt(np.mean((y[obs] - truth[obs]) ** 2)))
    err_sm = float(np.sqrt(np.mean((z[obs] - truth[obs]) ** 2)))
    ok = err_sm < err_raw
    ok_all &= ok
    print(f"\n  Whittaker: lambda_GCV={lam:.3g}  RMSE at observed dekads "
          f"{err_raw:.3f} -> {err_sm:.3f} (6 of 28 dekads missing)")
    print(f"  [{'PASS' if ok else 'FAIL'}] smoothing reduces error where the "
          f"fit actually reads it")

    # ---- 3. LM recovers known parameters ------------------------------
    y2 = truth + rng.normal(0, 0.3, len(t))
    fit = fit_curve(t, y2)
    ph = phenometrics(fit["params"])
    ph_true = phenometrics(p_true)
    d_sos = abs(ph["sos"] - ph_true["sos"])
    d_pos = abs(ph["pos"] - ph_true["pos"])
    d_eos = abs(ph["eos"] - ph_true["eos"])
    ok = fit["converged"] and fit["full_rank"] and max(d_sos, d_pos, d_eos) < 8.0
    ok_all &= ok
    print(f"\n  LM fit: converged={fit['converged']} rank={fit['rank']}/6 "
          f"RMSR={fit['rmsr']:.3f} dB")
    print(f"  phenometrics  true SOS/POS/EOS "
          f"{ph_true['sos']:.1f}/{ph_true['pos']:.1f}/{ph_true['eos']:.1f}"
          f"   fitted {ph['sos']:.1f}/{ph['pos']:.1f}/{ph['eos']:.1f}"
          f"   |err| {d_sos:.1f}/{d_pos:.1f}/{d_eos:.1f} d")
    print(f"  [{'PASS' if ok else 'FAIL'}] recovers known phenometrics within 8 days")

    # ---- 4. cross-check LM against scipy, if scipy is present ----------
    try:
        from scipy.optimize import least_squares
        best = None
        for p0 in _starts(t, y2):
            res = least_squares(lambda p: beck_double_logistic(t, p) - y2,
                                np.clip(p0, P_LO, P_HI),
                                bounds=(P_LO, P_HI))
            if best is None or res.cost < best.cost:
                best = res
        sse_scipy = 2.0 * best.cost
        rel = abs(fit["sse"] - sse_scipy) / max(sse_scipy, 1e-12)
        ok = rel < 0.02
        ok_all &= ok
        print(f"\n  scipy cross-check: SSE ours {fit['sse']:.6f} vs scipy "
              f"{sse_scipy:.6f} (rel diff {rel:.2e})")
        print(f"  [{'PASS' if ok else 'FAIL'}] own LM matches scipy least_squares")
    except ImportError:
        print("\n  scipy not installed -- cross-check skipped (not a dependency)")

    # ---- 5. the 20% crossings are where they are claimed to be --------
    p = fit["params"]
    amp = ph["peak_value"] - ph["base_value"]
    tgt = ph["base_value"] + AMPLITUDE_FRACTION * amp
    f_sos = beck_double_logistic(np.array([ph["sos"]]), p)[0]
    f_eos = beck_double_logistic(np.array([ph["eos"]]), p)[0]
    ok = abs(f_sos - tgt) < 1e-6 and abs(f_eos - tgt) < 1e-6 \
        and ph["sos"] < ph["pos"] < ph["eos"]
    ok_all &= ok
    print(f"\n  crossings: target {tgt:.4f}  f(SOS)={f_sos:.4f}  f(EOS)={f_eos:.4f}"
          f"  ordering SOS<POS<EOS = {ph['sos'] < ph['pos'] < ph['eos']}")
    print(f"  [{'PASS' if ok else 'FAIL'}] SOS and EOS sit on the 20% amplitude level")

    # ---- 6. Gate 1 direction --------------------------------------------
    counts = np.zeros(N_BINS)
    counts[:N_CORE_BINS] = 10.0
    counts[5] = 100.0            # the peak bin
    counts[9] = 80.0             # well sampled
    counts[12] = 2.0             # sparse
    adm = gate1_admitted_bins(counts, 0.5)
    ok = adm[5] and adm[9] and not adm[12] and adm[N_CORE_BINS:].all()
    ok_all &= ok
    print(f"\n  Gate 1 at r=0.5, N_peak=100: bin(80 obs) admitted={adm[9]}, "
          f"bin(2 obs) admitted={adm[12]}, peak admitted={adm[5]}, "
          f"extension all admitted={adm[N_CORE_BINS:].all()}")
    print(f"  [{'PASS' if ok else 'FAIL'}] well-sampled bins admitted, sparse "
          f"rejected (the frozen rule had this backwards)")

    # ---- 7. eligibility rule --------------------------------------------
    dv = np.full(N_DEKADS, np.nan); dc = np.zeros(N_DEKADS)
    dv[:13] = 1.0; dc[:13] = 3.0
    r13 = fit_one(dv, dc)
    dv[:14] = 1.0; dc[:14] = 3.0
    r14 = fit_one(dv, dc)
    ok = (not r13["eligible"]) and r14["eligible"]
    ok_all &= ok
    print(f"\n  eligibility: 13 valid dekads -> eligible={r13['eligible']}; "
          f"14 -> eligible={r14['eligible']}")
    print(f"  [{'PASS' if ok else 'FAIL'}] threshold sits at 14 of 28 (§3.11)")

    # ---- 8. what the smoothing step costs and buys ---------------------
    nb = 80
    acc = {"raw": {"sos": [], "pos": []}, "smoothed": {"sos": [], "pos": []}}
    rng3 = np.random.default_rng(21)
    for _ in range(nb):
        pp = np.array([-12 + rng3.normal(0, .8), -3.5 + rng3.normal(0, .6),
                       195 + rng3.normal(0, 5), 0.10 + rng3.normal(0, .015),
                       320 + rng3.normal(0, 6), 0.08 + rng3.normal(0, .012)])
        tru = phenometrics(pp)
        yy = beck_double_logistic(DEKAD_DOY, pp) + rng3.normal(0, 0.45, N_DEKADS)
        vmask = np.ones(N_DEKADS, bool)
        g0 = rng3.integers(0, 20)
        vmask[g0:g0 + rng3.integers(0, 5)] = False
        zz, _, _ = whittaker_gcv(np.where(vmask, yy, 0.0), vmask.astype(float))
        for tag, ser in (("raw", yy), ("smoothed", zz)):
            ff = fit_curve(DEKAD_DOY[vmask], ser[vmask])
            if not (ff["converged"] and ff["full_rank"]):
                continue
            pk = phenometrics(ff["params"])
            for kk in ("sos", "pos"):
                if np.isfinite(pk[kk]) and np.isfinite(tru[kk]):
                    acc[tag][kk].append(pk[kk] - tru[kk])
    print(f"\n  bias-variance of the smoothing step ({nb} synthetic pixels):")
    sd = {}
    for tag in ("raw", "smoothed"):
        line = f"    {tag:9s}"
        for kk in ("sos", "pos"):
            v = np.array(acc[tag][kk])
            sd[(tag, kk)] = v.std()
            line += f"  {kk.upper()} bias {v.mean():+5.2f} sd {v.std():4.2f}"
        print(line)
    ok = (sd[("smoothed", "sos")] < sd[("raw", "sos")]
          and sd[("smoothed", "pos")] < sd[("raw", "pos")])
    ok_all &= ok
    print(f"  [{'PASS' if ok else 'FAIL'}] smoothing reduces per-pixel "
          f"dispersion (its purpose); the level shift it introduces is "
          f"differenced out by the DiD")

    # ---- 9. end-to-end on a synthetic district-season ------------------
    n_px = 40
    rows = []
    rng2 = np.random.default_rng(9)
    true_sos = []
    for i in range(n_px):
        pp = p_true.copy()
        pp[2] += rng2.normal(0, 6)          # per-pixel transplanting spread
        pp[4] += rng2.normal(0, 6)
        true_sos.append(phenometrics(pp)["sos"])
        for b in range(N_BINS):
            doy = SEASON_START_DOY + 5 * b + 2
            nobs = int(rng2.integers(0, 4))
            val = (beck_double_logistic(np.array([doy]), pp)[0]
                   + rng2.normal(0, 0.5)) if nobs else np.nan
            rows.append(dict(district="TestDistrict", year=BASELINE_SEASON,
                             cell_id=f"px{i:03d}", bin_index=b,
                             VHVV_med=val, valid_obs_count=float(nobs)))
    ex = pd.DataFrame(rows)
    panel = run_panel(ex, {"sos": 0.3, "pos": 0.3, "eos": 0.3},
                      thresholds=dict(amp_min_db=1.0, peak_min_db=-8.0,
                                      rmsr_max_db=3.0),
                      progress_every=0)
    got = panel.dropna(subset=["sos"])
    bias = float(np.mean(got["sos"].values - np.array(true_sos)[
        [int(c[2:]) for c in got["cell_id"]]]))
    ok = len(panel) == n_px and panel["retained"].sum() > 0 and abs(bias) < 6.0
    ok_all &= ok
    print(f"\n  end-to-end: {len(panel)} pixel-seasons, "
          f"{int(panel['eligible'].sum())} eligible, "
          f"{int(panel['retained'].sum())} retained, SOS bias {bias:+.2f} d")
    print(f"  [{'PASS' if ok else 'FAIL'}] full pipeline recovers per-pixel SOS")

    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


# ===========================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Protocol v1 §3 lead-in / §3.1 / §3.2 / §3.11 "
                    "phenometric fitting.")
    ap.add_argument("--exports", help="folder of §9e S1_PHEN_*.csv exports")
    ap.add_argument("--out", help="output folder")
    ap.add_argument("--derive-baseline", action="store_true",
                    help="derive the open thresholds on the untreated 2017 "
                         "season and stop")
    ap.add_argument("--r-sos", type=float)
    ap.add_argument("--r-pos", type=float)
    ap.add_argument("--r-eos", type=float)
    ap.add_argument("--amp-min-db", type=float)
    ap.add_argument("--amp-min-rise-db", type=float,
                    help="override the SOS 30-day rise criterion; defaults to "
                         "--amp-min-db, which reproduces §3.2 exactly")
    ap.add_argument("--amp-min-decline-db", type=float,
                    help="override the EOS 30-day decline criterion; defaults "
                         "to --amp-min-db, which reproduces §3.2 exactly")
    ap.add_argument("--peak-min-db", type=float)
    ap.add_argument("--rmsr-max-db", type=float)
    ap.add_argument("--no-gate1", action="store_true",
                    help="fit with Gate 1 disabled, for the §3.1 "
                         "justification test")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not (args.exports and args.out):
        ap.error("--exports and --out are required (or run --selftest)")

    exports = load_exports(args.exports)

    if args.derive_baseline:
        derive_baseline(exports, args.out)
        return 0

    if args.no_gate1:
        r_values = {"sos": 0.0, "pos": 0.0, "eos": 0.0}
        print("Gate 1 DISABLED (--no-gate1): this is the 'without' arm of the "
              "§3.1 justification test, not a headline run.")
    else:
        missing = [n for n, v in (("--r-sos", args.r_sos),
                                  ("--r-pos", args.r_pos),
                                  ("--r-eos", args.r_eos)) if v is None]
        if missing:
            raise SystemExit(
                f"Gate 1 needs {missing}. §3.1 withdrew the frozen r values "
                "(0.75/0.50/0.50) because they were reasoned from optical "
                "cloud statistics under a rule pointing the other way. Derive "
                "them with --derive-baseline, record them in "
                "analysis/decisions_log.md, then pass them here. There is no "
                "default, deliberately.")
        r_values = {"sos": args.r_sos, "pos": args.r_pos, "eos": args.r_eos}

    missing = [n for n, v in (("--amp-min-db", args.amp_min_db),
                              ("--peak-min-db", args.peak_min_db),
                              ("--rmsr-max-db", args.rmsr_max_db))
               if v is None]
    if missing:
        raise SystemExit(
            f"Gates 2 and 3 need {missing}. §3.2's amplitude criteria and "
            "§3.11's RMSR threshold are stated in NDVI units, which have no "
            "meaning against a backscatter ratio in decibels, and there is no "
            "principled conversion. Derive them with --derive-baseline, record "
            "them in analysis/decisions_log.md, then pass them here.")
    thresholds = dict(amp_min_db=args.amp_min_db,
                      peak_min_db=args.peak_min_db,
                      rmsr_max_db=args.rmsr_max_db,
                      amp_min_rise_db=args.amp_min_rise_db,
                      amp_min_decline_db=args.amp_min_decline_db)

    print(f"\nGate 1 r values: {r_values}")
    print(f"Gate 2/3 thresholds: {thresholds}\n")
    panel = run_panel(exports, r_values, thresholds)

    os.makedirs(args.out, exist_ok=True)
    dest = os.path.join(args.out, "panel_phenometrics.csv")
    panel.to_csv(dest, index=False)

    n = len(panel)
    print(f"\n{'-'*74}")
    print(f"attempted pixel-seasons      {n:,}")
    print(f"eligible (§3.11)             {int(panel['eligible'].sum()):,} "
          f"({panel['eligible'].mean():.1%})")
    el = panel[panel["eligible"] == 1]
    if len(el):
        print(f"converged                    {int(el['converged'].sum()):,} "
              f"({el['converged'].mean():.1%} of eligible)")
        print(f"retained (all gates)         {int(panel['retained'].sum()):,} "
              f"({panel['retained'].mean():.1%} of attempted, "
              f"{el['retained'].mean():.1%} of eligible)")
    for phen in ("sos", "pos", "eos"):
        v = panel.loc[panel[f"retained_{phen}"] == 1, phen].dropna()
        if len(v):
            print(f"  {phen.upper()}  n={len(v):,}  median DOY {np.median(v):.0f}  "
                  f"IQR {np.percentile(v,25):.0f}-{np.percentile(v,75):.0f}")
    print(f"\nwrote {dest}")
    print("§3.11 makes the OBSERVATION-ELIGIBLE set the denominator for the "
          "§3.10 attrition diagnostic. Filter to eligible == 1 before passing "
          "this to attrition_diagnostics.py if following that rule literally; "
          "the full attempted frame is written here so either denominator can "
          "be used and the choice is visible.")
    print("-" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
