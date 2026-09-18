"""
attrition_diagnostics.py -- Protocol v1 §3.10 items 1-3, against the §3.8 A
headline specification.

Referenced by the protocol since 2026-09-07 but never written; created
2026-09-09 as part of protocol revision part 2.

------------------------------------------------------------------------------
WHY THIS EXISTS
------------------------------------------------------------------------------
Extraction failure in this pipeline is not random with respect to treatment.
If the pixels a cyclone disrupts most are also the pixels most likely to fail
QC, the surviving panel is selected on the outcome and a DiD estimated on
survivors is biased by an unknown amount in an unknown direction. §3.10
requires that this be measured first, corrected two ways, and all three
numbers reported side by side. This script is that computation.

  item 1  ATTRITION DIAGNOSTIC. Regress per-pixel-year extraction failure on
          severe exposure with district and season fixed effects, clustered on
          district. Run per severe-exposure class (pre-season, harvest window)
          and independently for each of the six estimable named cyclones
          (Titli, Fani, Bulbul, Amphan, Yaas, Remal). Reported with p_cluster,
          p_WCB and a 95% WCB interval.

  item 2  ZERO-TREATED-SUPPORT RULE. Any stratum with no treated support, or
          for which the bootstrap is not computable, is written out as
          "not_estimable" -- never dropped silently, never imputed.

  item 3a IPSW. Logit Pr(survive) on the pre-declared covariates plus district
          and season fixed effects, estimated on the full attempted frame;
          the TWFE is then weighted by 1/p-hat. Recovers the effect only if
          survival is ignorable given those covariates -- which fails
          precisely when pixels drop out BECAUSE of the outcome. Never
          reported alone.

  item 3c DESCRIPTIVE TWO-SEASON RESTRICTION. Re-estimate on pixels retained
          in both seasons of one cyclone. This changes composition and the time
          window together, so it is not a same-estimand composition check and
          is not a primary robustness estimate. Emits balanced_n_pixels only.

------------------------------------------------------------------------------
WHAT THIS DELIBERATELY DOES NOT DO
------------------------------------------------------------------------------
Lee (2009) trimming bounds are NOT implemented. §3.10 item 3b withdrew them on
2026-09-09: the frozen specification trimmed the wrong group with a formula
that returns a negative proportion under the protocol's own stated
monotonicity, and more fundamentally Lee derives those bounds for a randomised
two-arm design with one post-treatment outcome, which does not transfer to an
observational DiD panel without assumptions these data cannot support. A
corrected but mis-transferred estimator would invite sharper criticism than an
honest absence. Any future revision that reinstates them must first state what
makes the transfer valid here.

------------------------------------------------------------------------------
INFERENCE
------------------------------------------------------------------------------
Fixed effects are absorbed by alternating within-transforms (Frisch-Waugh),
not by dummy columns. Cluster-robust covariance uses the standard
G/(G-1) * (N-1)/(N-K) correction with K counting the absorbed effects.

Wild cluster bootstrap is implemented here directly -- Rademacher weights, one
draw per district, 9,999 replications -- rather than shelled out to `boottest`,
which is Stata/R only. Two variants are run and used for different things, as
they should be: the RESTRICTED (null-imposed) bootstrap gives the p-value; the
UNRESTRICTED bootstrap gives the confidence interval by percentile-t
inversion. Using the null-imposed distribution for an interval is a common
error and is avoided here.

Hard limit, stated rather than papered over: with few treated clusters -- two,
for Bulbul and for Remal -- no bootstrap can reject at conventional levels
whatever the true effect (MacKinnon & Webb, 2018). Those strata are reported
as underpowered, not as null results. The script marks them.

------------------------------------------------------------------------------
DEPENDENCIES
------------------------------------------------------------------------------
numpy and pandas only. No statsmodels, no linearmodels, no R. Everything
statistical here -- within-transform, cluster-robust OLS/WLS, wild cluster
bootstrap, logit by IRLS -- is implemented in this file, so the script runs on
a bare Python install. `--selftest` verifies the absorbed-FE estimator and its
cluster-robust standard errors against a brute-force dummy-variable OLS before
you trust it on real data.

------------------------------------------------------------------------------
USAGE
------------------------------------------------------------------------------
    python python/attrition_diagnostics.py --selftest

    python python/attrition_diagnostics.py \
        --panel   data/panel_phenometrics.csv \
        --exposure docs/district_cyclone_exposure_ibtracs50km.csv \
        --out     results/

Run --selftest first. It checks the absorbed-FE estimator and its
cluster-robust standard errors against a brute-force dummy-variable OLS, the
weighted version against a brute-force WLS, the bootstrap against a known
effect and against pure noise, and the logit against its own DGP. If any of
those fails, nothing this script prints about the real panel is trustworthy.

Runtime at the full frame (25 districts x 9 seasons x 400 pixels = 90,000
pixel-years) with the protocol's 9,999 replications is roughly an hour, almost
all of it in the bootstrap. `--boot 199` runs the same code in about a minute
and is the right setting while checking that a panel loads and the strata
resolve; it is NOT adequate for anything reported, since the smallest p-value
it can return is 1/200.

PANEL SCHEMA (one row per pixel-year of the ATTEMPTED frame, §3.11)
    cell_id     stable per-pixel key (§3.6)
    district    GADM district name, matching the exposure catalogue
    year        season
    retained    1 if the pixel-year survived QC Gates 1-3, else 0
    sos, pos, eos   phenometrics in DOY; may be blank where retained == 0
  optional, used if present:
    cloud_freq_clim, dist_to_track_km, elevation_m   IPSW covariates (§3.10 3a)

The script refuses to guess a column mapping. §3.10's quantities are only
meaningful against the documented schema, and a silently-misread column
produces a plausible-looking number computed on the wrong thing.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import os
import platform
import sys

import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
ROOT = os.environ.get("RICEBACI_ROOT", "/home/claude")


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

# ---------------------------------------------------------------------------
# constants fixed by the protocol
# ---------------------------------------------------------------------------
N_BOOT = 9999
SEED = 42
# Substrate-aware. Paper 1's optical names first, then the radar markers of
# the §3 lead-in. They are NOT synonyms -- the radar markers name the physical
# state they mark (see extract_phenometrics_sar.py) -- so both sets are listed
# and only those actually present in the panel are used. The interval outcomes
# are included because a shift common to the whole season cancels out of them,
# which makes them the sharper test of a phenological effect.
PHENOMETRICS = ["sos", "pos", "eos",
                "trough", "heading", "drainage", "harvest",
                "veg_days", "plateau_days", "fill_days", "season_days",
                "rise_db", "fall_db", "plateau_db"]

# §3.10 3a. NOTE (2026-09-09): this list was frozen against the Sentinel-2
# substrate, where cloud-frequency climatology was the dominant driver of
# survival. Under the Sentinel-1 substrate (§3 lead-in) cloud is not the
# operative mechanism, and the analogous covariates are per-pixel valid
# observation count, incidence angle and relative-orbit count. That
# replacement is an open protocol item, recorded in the deviation log; it is
# NOT made silently here. The script reports which of the declared covariates
# it found and computes IPSW only on the declared set.
IPSW_COVARIATES = ["cloud_freq_clim", "dist_to_track_km", "elevation_m"]

# CLOSED 2026-09-12. The Sentinel-1 replacement for the set above, declared
# here rather than left as an open protocol item. Each entry is the radar
# analogue of what the optical covariate was there for:
#
#   obs_total        total valid Sentinel-1 observations for the pixel-season.
#                    Replaces cloud_freq_clim: it is the measure of how well
#                    the sensor sees this pixel, which on radar is orbit
#                    geometry rather than cloud.
#   n_valid_dekads   dekadal coverage after §1.4 aggregation. Selection into
#                    the retained set runs partly through coverage and §3.11
#                    is a coverage rule, so it belongs in the score.
#   dist_to_track_km district-season minimum distance to the 34-kt wind radius
#                    of that season's catalogued storms (from the exposure
#                    file's min_dist_to_track34kt_km), coded at
#                    NO_STORM_DIST_KM when no storm is catalogued. Carried over
#                    unchanged from the declared set.
#   elevation_m      terrain height.
#   slope_deg        terrain slope. On radar the operative terrain quantity is
#                    local geometry, not height, so slope is declared alongside
#                    elevation rather than instead of it.
#   incidence_deg    mean Sentinel-1 incidence angle over the cell. VH/VV
#                    depends on it, so a pixel's retention does too.
#
# The last three come from a static per-district export (S1_STATIC_COVARIATES)
# which is 25 tasks, not 225, because they do not vary by season. Until that
# export lands the script computes the weights on whatever subset is present,
# labels the result ipsw_partial, and says which covariates were missing. It
# does NOT silently present a partial model as the declared one.
IPSW_COVARIATES_RADAR = ["obs_total", "n_valid_dekads", "dist_to_track_km",
                         "elevation_m", "slope_deg", "incidence_deg"]
NO_STORM_DIST_KM = 500.0

PANEL_REQUIRED = ["cell_id", "district", "year", "retained"]

# §1.1 / §3.10 item 1. Sitrang is excluded: it exposes no roster district.
ESTIMABLE_CYCLONES = ["TITLI", "FANI", "BULBUL", "AMPHAN", "YAAS", "REMAL"]

# MacKinnon & Webb (2018): below this many treated clusters, a null result is
# uninformative and must be labelled as such rather than reported as evidence.
MIN_TREATED_CLUSTERS = 3

# §3.10 3a. Floors below which the selection model is reported as not estimable
# rather than fitted. A logit needs both rows and events; after dropping
# fixed-effect levels that predict the outcome perfectly, a handful of either
# gives a fit whose weights are an artefact of the clip, not of the data.
MIN_IPSW_ROWS = 30
MIN_IPSW_EVENTS = 8

SEVERE_CLASSES = ["pre_season", "harvest_window"]


# ===========================================================================
# fixed-effect absorption
# ===========================================================================
class FEAbsorber:
    """Within-transform on one or more fixed-effect groupings.

    Alternating projections (Frisch-Waugh-Lovell). One pass does not fully
    absorb two-way effects, so it iterates to convergence. Group means are
    weighted when `weights` is supplied, which is what makes the IPSW-weighted
    fit a genuine WLS-with-FE rather than an unweighted transform followed by
    a weighted regression.
    """

    def __init__(self, frame, fe_cols, weights=None):
        self.fe_cols = list(fe_cols)
        n = len(frame)
        self.w = np.ones(n) if weights is None else np.asarray(weights, float)
        if self.w.shape != (n,):
            raise ValueError("weights length does not match frame")
        self.codes, self.wsums = [], []
        for c in self.fe_cols:
            code, _ = pd.factorize(frame[c], sort=False)
            code = np.asarray(code, dtype=np.int64)
            if (code < 0).any():
                raise ValueError(f"fixed-effect column {c!r} contains missing values")
            ng = int(code.max()) + 1
            self.codes.append(code)
            ws = np.bincount(code, weights=self.w, minlength=ng)
            self.wsums.append(np.maximum(ws, 1e-12))
        # parameters absorbed: each grouping costs its levels, minus the
        # (nfe - 1) intercepts that are collinear across groupings.
        self.k_absorbed = sum(len(s) for s in self.wsums) - (len(self.fe_cols) - 1)

    def demean(self, v, tol=1e-10, maxiter=500):
        v = np.array(v, dtype=float, copy=True).ravel()
        if len(self.codes) == 1:
            code, ws = self.codes[0], self.wsums[0]
            m = np.bincount(code, weights=self.w * v, minlength=len(ws)) / ws
            return v - m[code]
        for _ in range(maxiter):
            prev = v.copy()
            for code, ws in zip(self.codes, self.wsums):
                m = np.bincount(code, weights=self.w * v, minlength=len(ws)) / ws
                v -= m[code]
            if np.max(np.abs(v - prev)) < tol:
                break
        return v

    def demean_matrix(self, M):
        M = np.asarray(M, dtype=float)
        if M.ndim == 1:
            M = M[:, None]
        return np.column_stack([self.demean(M[:, j]) for j in range(M.shape[1])])



def _resolve_exposure(path):
    """Where the exposure catalogue actually is, wherever it was named from."""
    return path if os.path.exists(path) else _find_doc(os.path.basename(path))


def _logical_path(path):
    """Repository-relative path when the file sits inside the repo, else its
    basename. NEVER an absolute path.

    An absolute path in the run key made resume machine-local: the same bytes in
    another clone were refused because the directory prefix differed, which is
    the opposite of what the key is for. The key must identify the INPUT, not
    the machine.
    """
    ap = os.path.abspath(path)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    try:
        rel = os.path.relpath(ap, root)
    except ValueError:
        return os.path.basename(ap)
    return rel.replace(os.sep, "/") if not rel.startswith("..") \
        else os.path.basename(ap)


def _content_hash(path):
    """LF-normalised md5 of a file's bytes, or a marker when it is absent.

    Content, not mtime and not size: a resumed run must be refused when the
    INPUT BYTES changed, and accepted when the same bytes sit at a different
    absolute path.
    """
    if not path or not os.path.exists(path):
        return "absent"
    with open(path, "rb") as fh:
        raw = fh.read()
    return hashlib.md5(raw.replace(b"\r\n", b"\n")).hexdigest()


def _build_run_key(args, _helper_paths=None, _runtime_override=None):
    """What must match for a partial table to be resumable.

    THREE THINGS CHANGED HERE ON 2026-09-15, after an audit showed the old key
    was both too weak and not portable.

    (1) PORTABLE. Paths are repository-relative logical paths, so the same bytes
        in another clone resume successfully.
    (2) CONTENT-BASED. Every input is identified by a hash of its BYTES, not by
        its name. Editing the phase-exposure table, the panel or the exposure
        catalogue now refuses the resume; previously only the FILENAME was
        compared, so an edited file with the same name spliced silently.
    (3) CODE AND OPTIONS INCLUDED. The estimator source is hashed, and every
        analysis option that can change a number is recorded. Splicing rows
        computed by a different version of this file used to be undetectable.

    Coverage is part of identity.  A broader or narrower invocation is a
    different resumable run even when the overlapping rows would have the same
    values: otherwise stale extra blocks can survive a narrower request, or an
    incomplete narrow run can masquerade as a completed broad one.
    """
    src = os.path.abspath(__file__)
    helper = os.path.join(os.path.dirname(src), "lf_output.py")
    helper_paths = list(_helper_paths) if _helper_paths is not None else [helper]

    # Record the numerical runtime without embedding machine-specific install
    # paths.  Resume is intentionally conservative: a different numerical
    # stack must start clean rather than splice rows across environments.
    blas = {}
    try:
        cfg = getattr(np.__config__, "CONFIG", {})
        raw = cfg.get("Build Dependencies", {}).get("blas", {})
        for k in ("name", "version", "detection method", "openblas configuration"):
            if k in raw:
                blas[k] = raw[k]
    except Exception:
        blas = {"identity": "unavailable"}

    coverage = {
        "balanced": bool(getattr(args, "balanced", False)),
        "phase": bool(getattr(args, "phase_exposure", None)),
        "blocks": ["diagnostics", "headline", "pretrend"]
                  + (["ipsw"] if args.level == "pixel" else [])
                  + (["balanced"] if getattr(args, "balanced", False) else [])
                  + (["phase", "phase_pretrend"]
                     + (["phase_ipsw"] if args.level == "pixel" else [])
                     if getattr(args, "phase_exposure", None) else []),
    }
    runtime = {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "system": platform.system(),
        "machine": platform.machine(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "blas": blas,
    }
    if _runtime_override is not None:
        runtime = dict(_runtime_override)
    return {
        "schema": 3,
        "level": args.level,
        "panel_path": _logical_path(args.panel),
        "panel_sha": _content_hash(args.panel),
        "exposure_path": _logical_path(_resolve_exposure(args.exposure)),
        "exposure_sha": _content_hash(_resolve_exposure(args.exposure)),
        "phase_exposure_path": (_logical_path(args.phase_exposure)
                                if args.phase_exposure else None),
        "phase_exposure_sha": _content_hash(args.phase_exposure),
        "code_path": _logical_path(src),
        "code_sha": _content_hash(src),
        "local_helpers": {
            _logical_path(path): _content_hash(path) for path in helper_paths
        },
        "runtime": runtime,
        "coverage": coverage,
        "options": {
            "boot": int(args.boot),
            "seed": int(args.seed),
            "min_treated_clusters": int(MIN_TREATED_CLUSTERS),
        },
    }


def _se_from_vce(V):
    """Standard errors from a cluster-robust covariance, refusing to invent one.

    A cluster-robust sandwich is NOT guaranteed positive semi-definite. When
    the per-cluster scores for a coefficient nearly cancel -- few clusters
    carrying any score, which is the balanced-window case -- the estimated
    variance can come out negative by rounding. An earlier version of this
    function wrote `sqrt(maximum(diag(V), 0))`, which turned exactly that
    failure into a standard error of 0.000: the single most dangerous number
    this file could print, because it reads as infinite precision and produces
    a confidence interval of zero width around a point estimate that may be
    fine. Measured on a synthetic balanced window: beta = 7.628 with se
    reported as 0.000, from a variance of -9.4e-18.

    A non-positive variance now becomes NaN, which the callers turn into
    "not estimable" -- the response §3.10 item 2 prescribes when the bootstrap
    is not computable for a stratum.
    """
    d = np.diag(V).astype(float)
    scale = float(np.max(np.abs(V))) if V.size else 0.0
    tol = 1e-12 * max(scale, 1.0)
    return np.where(d > tol, np.sqrt(np.maximum(d, 0.0)), np.nan)


def _cluster_meat(Xd, u, cl_codes, n_clusters):
    """sum_g (X_g' u_g)(X_g' u_g)'  -- u already carries any WLS weight."""
    Xu = Xd * u[:, None]
    sums = np.empty((n_clusters, Xd.shape[1]))
    for j in range(Xd.shape[1]):
        sums[:, j] = np.bincount(cl_codes, weights=Xu[:, j], minlength=n_clusters)
    return sums.T @ sums


class WithinModel:
    """(Weighted) least squares on already-absorbed data, cluster-robust VCE.

    The design is fixed and only the outcome varies -- which is exactly the
    shape of a bootstrap loop -- so the cross-product and its inverse are
    formed once in __init__ and reused for every replication. Re-deriving
    them per replication was measurably the largest avoidable cost.
    """

    def __init__(self, Xd, cl_codes, n_clusters, k_absorbed, w=None):
        Xd = np.asarray(Xd, float)
        if Xd.ndim == 1:
            Xd = Xd[:, None]
        n, k = Xd.shape
        self.X = Xd
        self.w = np.ones(n) if w is None else np.asarray(w, float)
        self.Xw = Xd * self.w[:, None]
        self.XtX_inv = np.linalg.pinv(self.Xw.T @ Xd)
        self.cl = cl_codes
        self.G = n_clusters
        self.dof = ((n_clusters / max(n_clusters - 1, 1))
                    * ((n - 1) / max(n - (k + k_absorbed), 1)))

    def fit(self, yd):
        yd = np.asarray(yd, float).ravel()
        beta = self.XtX_inv @ (self.Xw.T @ yd)
        e = yd - self.X @ beta
        meat = _cluster_meat(self.X, self.w * e, self.cl, self.G)
        V = self.XtX_inv @ meat @ self.XtX_inv * self.dof
        return beta, _se_from_vce(V), e

    def score_clusters(self, yd, col):
        """How many clusters actually contribute score variation to `col`.

        The cluster-robust variance of a coefficient is built from G per-cluster
        sums X_g' e_g. If most of those are zero for the column being tested --
        which happens in the two-season balanced windows of §3.10 3c, where the
        exposure indicator is constant within most districts -- the effective G
        for that coefficient is far below the nominal 25, and neither the
        asymptotics nor the bootstrap has the clusters it is assumed to have.
        Reported so that a small effective G is visible rather than implied.
        """
        yd = np.asarray(yd, float).ravel()
        beta = self.XtX_inv @ (self.Xw.T @ yd)
        e = yd - self.X @ beta
        g = np.bincount(self.cl, weights=(self.X[:, col] * self.w * e),
                        minlength=self.G)
        m = np.max(np.abs(g))
        return int(np.sum(np.abs(g) > 1e-8 * max(m, 1.0)))


def within_fit(yd, Xd, cl_codes, n_clusters, k_absorbed, w=None):
    """One-shot convenience wrapper around WithinModel."""
    return WithinModel(Xd, cl_codes, n_clusters, k_absorbed, w).fit(yd)


def wild_cluster_bootstrap(yd, Xd, absorber, cl_codes, n_clusters, test_idx,
                           n_boot=N_BOOT, seed=SEED, w=None):
    """
    Rademacher wild cluster bootstrap, one weight draw per cluster.

    Restricted (null-imposed) resampling gives the p-value; unrestricted
    resampling gives the percentile-t interval. Both are run in the same loop
    on the same weight draws.

    The bootstrap outcome is re-absorbed each replication: multiplying
    residuals by cluster-level weights destroys their orthogonality to the
    fixed effects, so skipping the re-absorption would leave FE variation in
    y* and bias the bootstrap distribution.
    """
    Xd = np.asarray(Xd, float)
    if Xd.ndim == 1:
        Xd = Xd[:, None]
    k_abs = absorber.k_absorbed

    model_full = WithinModel(Xd, cl_codes, n_clusters, k_abs, w)
    beta, se, e_full = model_full.fit(yd)
    if se[test_idx] <= 0 or not np.isfinite(se[test_idx]):
        return dict(coef=float(beta[test_idx]), se=np.nan, t=np.nan,
                    p_wcb=np.nan, ci_lo=np.nan, ci_hi=np.nan, n_boot_ok=0,
                    n_boot_requested=int(n_boot))
    t_obs = beta[test_idx] / se[test_idx]
    fitted_full = Xd @ beta

    keep = [j for j in range(Xd.shape[1]) if j != test_idx]
    if keep:
        Xr = Xd[:, keep]
        b_r, _, e_r = WithinModel(Xr, cl_codes, n_clusters, k_abs, w).fit(yd)
        fitted_r = Xr @ b_r
    else:
        fitted_r = np.zeros_like(yd)
        e_r = np.asarray(yd, float).ravel()

    rng = np.random.default_rng(seed)
    t_r = np.full(n_boot, np.nan)
    t_u = np.full(n_boot, np.nan)
    for b in range(n_boot):
        wt = rng.choice((-1.0, 1.0), size=n_clusters)[cl_codes]
        yr = absorber.demean(fitted_r + e_r * wt)
        bb, ss, _ = model_full.fit(yr)
        if ss[test_idx] > 0:
            t_r[b] = bb[test_idx] / ss[test_idx]
        yu = absorber.demean(fitted_full + e_full * wt)
        bu, su, _ = model_full.fit(yu)
        if su[test_idx] > 0:
            t_u[b] = (bu[test_idx] - beta[test_idx]) / su[test_idx]

    t_r = t_r[np.isfinite(t_r)]
    t_u = t_u[np.isfinite(t_u)]
    if t_r.size == 0 or t_u.size == 0:
        return dict(coef=float(beta[test_idx]), se=float(se[test_idx]),
                    t=float(t_obs), p_wcb=np.nan, ci_lo=np.nan, ci_hi=np.nan,
                    n_boot_ok=int(min(t_r.size, t_u.size)),
                    n_boot_requested=int(n_boot))

    # +1 in numerator and denominator: the observed statistic is one draw from
    # the null distribution, so a bootstrap p-value can never legitimately be 0.
    p_wcb = (1.0 + np.sum(np.abs(t_r) >= abs(t_obs))) / (1.0 + t_r.size)
    q_lo, q_hi = np.percentile(t_u, [2.5, 97.5])
    ci = (beta[test_idx] - q_hi * se[test_idx],
          beta[test_idx] - q_lo * se[test_idx])
    return dict(coef=float(beta[test_idx]), se=float(se[test_idx]),
                t=float(t_obs), p_wcb=float(p_wcb),
                ci_lo=float(ci[0]), ci_hi=float(ci[1]),
                n_boot_ok=int(min(t_r.size, t_u.size)),
                n_boot_requested=int(n_boot))


def normal_two_sided_p(t):
    """Cluster-robust p under the normal reference, for p_cluster.

    Deliberately not the t(G-1) reference: p_cluster is reported here only as
    the quantity §3.10 item 1 names alongside p_WCB, and the WCB p-value is the
    protocol's headline inference (§3.8). Erf keeps the dependency list at
    numpy + pandas.
    """
    from math import erfc, sqrt
    if not np.isfinite(t):
        return np.nan
    return float(erfc(abs(t) / sqrt(2.0)))


# ===========================================================================
# logit by IRLS (IPSW, §3.10 3a)
# ===========================================================================
def logit_irls(y, X, maxiter=100, tol=1e-10):
    """Logistic regression by iteratively reweighted least squares.

    Two details matter here and both were found by testing rather than by
    reading, so they are recorded:

    * The design is standardised internally. With the §3.10 covariates on
      their natural scales (distance to track in km reaches 300, the fixed-
      effect dummies are 0/1) the raw cross-product has a condition number
      near 1e20, and IRLS stalls around 1e-4 on floating-point noise instead
      of converging. Standardising fixes it; the returned coefficients are
      mapped back to the original scale.
    * Each step is solved by least squares on the sqrt(W)-weighted design
      rather than by forming and inverting X'WX, which squares the condition
      number.

    Returns (beta_original_scale, p_hat, converged). Convergence is judged on
    the linear predictor, not the coefficients: the predictor is what IPSW
    actually consumes, and it stays well-defined when two columns are nearly
    collinear.
    """
    y = np.asarray(y, float).ravel()
    X = np.asarray(X, float)
    n, k = X.shape

    ctr = np.zeros(k)
    scl = np.ones(k)
    for j in range(k):
        col = X[:, j]
        rng_j = col.max() - col.min()
        if rng_j > 0:
            sd = col.std()
            ctr[j] = col.mean()
            scl[j] = sd if sd > 0 else 1.0
    Z = (X - ctr) / scl
    const_cols = np.where((X.max(axis=0) - X.min(axis=0)) == 0)[0]
    for j in const_cols:
        Z[:, j] = X[:, j]

    gamma = np.zeros(k)
    eta = np.zeros(n)
    converged = False
    for _ in range(maxiter):
        p = 1.0 / (1.0 + np.exp(-np.clip(eta, -35.0, 35.0)))
        wv = np.maximum(p * (1.0 - p), 1e-8)
        z = eta + (y - p) / wv
        sw = np.sqrt(wv)
        gamma, *_ = np.linalg.lstsq(Z * sw[:, None], z * sw, rcond=None)
        eta_new = Z @ gamma
        step = np.max(np.abs(eta_new - eta))
        eta = eta_new
        if step < tol:
            converged = True
            break
    p = 1.0 / (1.0 + np.exp(-np.clip(eta, -35.0, 35.0)))

    # unstandardise: eta = sum_j gamma_j (x_j - ctr_j)/scl_j
    beta = gamma / scl
    shift = float(np.sum(gamma * ctr / scl))
    if len(const_cols):
        j0 = int(const_cols[0])
        beta[j0] = gamma[j0] - shift / (X[0, j0] if X[0, j0] != 0 else 1.0)
    return beta, p, converged


# ===========================================================================
# exposure construction (§3.8 A)
# ===========================================================================
def build_exposure_table(exposure, districts, years):
    """District x season indicators S_pre, S_harv, M, plus lags and leads.

    Lags read the catalogue at t-1 and leads at t+1, so a season outside the
    panel but inside the catalogue (2016 for the 2017 lag; 2018 for the 2019
    lag) is used rather than coded as unexposed. Leads for the final catalogue
    season are NaN, not 0 -- §3.8 A requires those observations to be excluded
    from the lead test rather than treated as unexposed.
    """
    exposure = exposure.copy()
    exposure["severity_class"] = exposure["severity_class"].str.strip().str.lower()
    exposure["timing_class"] = exposure["timing_class"].str.strip().str.lower()

    cat_years = sorted(set(exposure["season"].astype(int)))
    span = list(range(min(min(cat_years), min(years)), max(max(cat_years), max(years)) + 1))
    idx = pd.MultiIndex.from_product([sorted(districts), span],
                                     names=["district", "year"])
    tab = pd.DataFrame(index=idx).reset_index()

    sev = exposure[exposure["severity_class"] == "severe"]
    for cls in SEVERE_CLASSES:
        hit = (sev[sev["timing_class"] == cls][["district_gadm_name", "season"]]
               .drop_duplicates())
        hit.columns = ["district", "year"]
        hit["S_" + cls] = 1
        tab = tab.merge(hit, on=["district", "year"], how="left")
        tab["S_" + cls] = tab["S_" + cls].fillna(0).astype(int)

    minor = (exposure[exposure["severity_class"] == "minor"]
             [["district_gadm_name", "season"]].drop_duplicates())
    minor.columns = ["district", "year"]
    minor["M_minor"] = 1
    tab = tab.merge(minor, on=["district", "year"], how="left")
    tab["M_minor"] = tab["M_minor"].fillna(0).astype(int)

    tab = tab.sort_values(["district", "year"]).reset_index(drop=True)
    g = tab.groupby("district")
    last_cat_year = max(cat_years)
    for cls in SEVERE_CLASSES:
        tab["Slag_" + cls] = g["S_" + cls].shift(1)
        tab["Slead_" + cls] = g["S_" + cls].shift(-1)
        # a lead that would need a season beyond the catalogue is unknown
        tab.loc[tab["year"] >= last_cat_year, "Slead_" + cls] = np.nan
    return tab


def _storm_tokens(name):
    """IBTrACS names a storm that crossed basins with a compound label.

    In this catalogue Bulbul is stored as BULBUL:MATMO and Gulab as
    GULAB:SHAHEEN-GU. An exact string match on "BULBUL" therefore finds
    nothing, and Bulbul -- one of the six named cyclones §3.10 item 1
    requires -- would be reported as "not estimable, no treated support":
    a name-matching bug wearing the costume of a data fact. Matching on
    colon-separated tokens fixes it. `assert_cyclones_resolve` below is the
    guard that stops the same class of failure returning silently.
    """
    return {t.strip().upper() for t in str(name).split(":") if t.strip()}


def cyclone_district_seasons(exposure, storm, districts=None):
    """Severe-exposure (district, season) pairs for one named storm.

    With `districts` given, the result is restricted to that roster; without
    it, the whole catalogue. The caller needs both to tell "this storm hits no
    district we extracted" (a fact about §1.3) from "this storm is not in the
    catalogue under that name" (a bug).
    """
    storm = storm.strip().upper()
    e = exposure.copy()
    e["severity_class"] = e["severity_class"].astype(str).str.strip().str.lower()
    mask = e["storm_name"].map(lambda n: storm in _storm_tokens(n))
    hit = e[mask & (e["severity_class"] == "severe")]
    pairs = set(zip(hit["district_gadm_name"], hit["season"].astype(int)))
    if districts is not None:
        ds = set(districts)
        pairs = {(d, y) for d, y in pairs if d in ds}
    return pairs


def assert_cyclones_resolve(exposure):
    """Fail loudly if a protocol-named cyclone does not resolve in the catalogue.

    §3.10 item 2 requires a stratum with no treated support to be reported as
    "not estimable". That rule is only honest if "no treated support" is a
    measurement. A storm that resolves to nothing because its catalogue name
    was not matched is a defect, and must stop the run rather than be written
    into the supplement table as a finding.
    """
    unresolved = [c for c in ESTIMABLE_CYCLONES
                  if not cyclone_district_seasons(exposure, c)]
    if unresolved:
        names = sorted(set(exposure["storm_name"].astype(str)))
        raise SystemExit(
            "these protocol-named cyclones do not resolve to any severe "
            f"exposure in the catalogue: {unresolved}\n"
            f"catalogue storm names: {names}\n"
            "Fix the name matching or the catalogue -- do not let this be "
            "reported as 'not estimable'.")


def warn_unlisted_severe_storms(exposure, districts):
    """Name any severe storm hitting the roster that the protocol does not list.

    ESTIMABLE_CYCLONES is frozen from §1.1/§3.8 B. If the catalogue is ever
    rebuilt with a wider buffer or a later season, a new severe storm could
    enter the roster and go unreported simply because nothing looks for it.
    """
    e = exposure.copy()
    e["severity_class"] = e["severity_class"].astype(str).str.strip().str.lower()
    ds = set(districts)
    sev = e[(e["severity_class"] == "severe")
            & (e["district_gadm_name"].isin(ds))]
    listed = set(ESTIMABLE_CYCLONES)
    extra = set()
    for n in sev["storm_name"]:
        toks = _storm_tokens(n)
        # A compound label whose other half is a listed storm is that storm
        # under its other-basin name (BULBUL:MATMO), not a separate event.
        if toks & listed:
            continue
        extra |= toks
    return sorted(extra - listed)


# ===========================================================================
# §3.10 item 1 -- attrition diagnostic
# ===========================================================================
def attrition_diagnostic(panel, exposure_col, label, n_boot, seed):
    d = panel
    treated_clusters = int(d.loc[d[exposure_col] == 1, "district"].nunique())
    if d[exposure_col].nunique() < 2 or treated_clusters == 0:
        return dict(stratum=label, estimator="attrition_diagnostic",
                    status="not_estimable",
                    reason="no treated support in the extracted frame",
                    n_obs=int(len(d)), n_treated_clusters=treated_clusters)

    fe = FEAbsorber(d, ["district", "year"])
    yd = fe.demean(1.0 - d["retained"].astype(float).values)
    Xd = fe.demean_matrix(d[[exposure_col]].astype(float).values)
    cl, _ = pd.factorize(d["district"], sort=False)
    cl = np.asarray(cl, np.int64)
    G = int(cl.max()) + 1

    model = WithinModel(Xd, cl, G, fe.k_absorbed)
    n_score = model.score_clusters(yd, 0)
    res = wild_cluster_bootstrap(yd, Xd, fe, cl, G, 0, n_boot=n_boot, seed=seed)
    if not np.isfinite(res["se"]):
        return dict(stratum=label, estimator="attrition_diagnostic",
                    status="not_estimable", coef=res["coef"],
                    reason="cluster-robust variance not positive for this "
                           "coefficient, so no t-statistic and no bootstrap "
                           "are computable (§3.10 item 2). The point estimate "
                           "is in `coef`; only inference is unavailable.",
                    n_obs=int(len(d)), n_clusters=G,
                    n_treated_clusters=treated_clusters,
                    n_score_clusters=n_score)
    underpowered = treated_clusters < MIN_TREATED_CLUSTERS
    return dict(
        stratum=label,
        estimator="attrition_diagnostic",
        status="estimated",
        coef=res["coef"], se=res["se"], t=res["t"],
        p_cluster=normal_two_sided_p(res["t"]),
        p_wcb=res["p_wcb"], wcb_ci_lo=res["ci_lo"], wcb_ci_hi=res["ci_hi"],
        n_boot_ok=res["n_boot_ok"],
        n_boot_requested=res.get("n_boot_requested", n_boot),
        n_obs=int(len(d)),
        n_exposed_pixel_years=int(d[exposure_col].sum()),
        n_clusters=G,
        n_treated_clusters=treated_clusters,
        n_score_clusters=n_score,
        underpowered=int(underpowered),
        reason=("fewer than %d treated clusters: a null result here is "
                "uninformative (MacKinnon & Webb 2018)" % MIN_TREATED_CLUSTERS)
        if underpowered else "",
    )


# ===========================================================================
# §3.8 A headline TWFE, and its §3.10 3a / 3c variants
# ===========================================================================
def _screen_regressors(fe, frame, regressors, test_var):
    """Absorb the regressors and drop any that carry no identifying variation.

    Two ways a term dies here. It can be constant in the subsample -- common
    in the two-season balanced windows of §3.10 3c, where a lag term may not
    vary at all. Or it can survive raw but be collinear with the fixed effects
    or with another regressor, so its absorbed column is numerically zero or
    adds no rank.

    Both are dropped explicitly and named in the output rather than left to
    the pseudo-inverse. A pinv on a rank-deficient design returns the
    minimum-norm solution, which silently splits a coefficient across
    collinear columns -- a plausible-looking number that is not the quantity
    §3.10 asks for. `test_var` is screened first so it is never the column
    sacrificed to a collinearity it shares with another term.
    """
    order = [test_var] + [r for r in regressors if r != test_var]
    kept, cols, dropped = [], [], []
    for r in order:
        raw = frame[r].astype(float).values
        if raw.max() - raw.min() == 0:
            dropped.append(f"{r}(constant)")
            continue
        col = fe.demean(raw)
        if np.std(col) < 1e-10 * max(1.0, float(np.std(raw))):
            dropped.append(f"{r}(absorbed by FE)")
            continue
        trial = np.column_stack(cols + [col]) if cols else col[:, None]
        if np.linalg.matrix_rank(trial, tol=1e-9) < trial.shape[1]:
            dropped.append(f"{r}(collinear)")
            continue
        kept.append(r)
        cols.append(col)
    Xd = np.column_stack(cols) if cols else np.empty((len(frame), 0))
    return Xd, kept, dropped


def twfe(panel, phen, regressors, n_boot, seed, test_var, weights=None,
         retained_only=True):
    """Two-way fixed-effect estimate of `test_var` on `phen`.

    RESTRICTS TO retained == 1 BEFORE ESTIMATING. That line was missing until
    2026-09-13 and its absence was the worst defect in this project: §3's screen
    decides which unit-seasons carry a usable phenometric, the panel records the
    decision in `retained`, and this estimator ignored it. `dropna` removed only
    unit-seasons whose breakpoints were never identified; the far larger group
    whose fitted rise failed the selection-aware significance screen kept finite
    breakpoints and entered every "QC-screened" estimate. At district level that
    admitted 5 of 225 rows (213 used against 208 retained); at pixel level it
    admitted 44,976, so 59% of the 76,717 observations in the headline
    regressions had failed the screen the paper is built on. The error messages
    in this function said "retained" throughout, which made it read as if the
    restriction were happening.

    `retained_only` exists only so a caller can deliberately estimate on the
    unscreened panel and say so; nothing in §3.8 or §3.10 does.
    """
    if retained_only and "retained" in panel.columns:
        panel = panel[panel["retained"].astype(int) == 1]
    d = panel.dropna(subset=[phen] + regressors)
    if d.empty:
        return dict(status="not_estimable", reason="no retained observations")
    if d[test_var].nunique() < 2:
        return dict(status="not_estimable",
                    reason="no variation in %s among retained pixels" % test_var)
    treated_clusters = int(d.loc[d[test_var] == 1, "district"].nunique())
    if treated_clusters == 0:
        return dict(status="not_estimable", reason="zero treated support")

    w = None if weights is None else d[weights].astype(float).values
    fe = FEAbsorber(d, ["district", "year"], weights=w)
    Xd, kept, dropped = _screen_regressors(fe, d, regressors, test_var)
    if test_var not in kept:
        return dict(status="not_estimable",
                    reason="%s carries no identifying variation after the "
                           "fixed effects (%s)" % (test_var, "; ".join(dropped)))
    yd = fe.demean(d[phen].astype(float).values)
    cl, _ = pd.factorize(d["district"], sort=False)
    cl = np.asarray(cl, np.int64)
    G = int(cl.max()) + 1
    ti = kept.index(test_var)

    model = WithinModel(Xd, cl, G, fe.k_absorbed, w)
    n_score = model.score_clusters(yd, ti)
    res = wild_cluster_bootstrap(yd, Xd, fe, cl, G, ti,
                                 n_boot=n_boot, seed=seed, w=w)
    if not np.isfinite(res["se"]):
        return dict(status="not_estimable", phenometric=phen,
                    test_var=test_var, coef=res["coef"],
                    reason="cluster-robust variance not positive for %s: only "
                           "%d of %d clusters carry any score for it, so the "
                           "sandwich is degenerate and no bootstrap-t exists "
                           "(§3.10 item 2). The point estimate is in `coef`."
                           % (test_var, n_score, G),
                    n_obs=int(len(d)), n_clusters=G,
                    n_treated_clusters=treated_clusters,
                    n_score_clusters=n_score,
                    regressors_kept="|".join(kept),
                    regressors_dropped="|".join(dropped))
    return dict(
        status="estimated", phenometric=phen, test_var=test_var,
        coef=res["coef"], se=res["se"], t=res["t"],
        p_cluster=normal_two_sided_p(res["t"]),
        p_wcb=res["p_wcb"], wcb_ci_lo=res["ci_lo"], wcb_ci_hi=res["ci_hi"],
        n_boot_ok=res.get("n_boot_ok"),
        n_boot_requested=res.get("n_boot_requested", n_boot),
        n_obs=int(len(d)), n_pixels=int(d["cell_id"].nunique()),
        n_clusters=G, n_treated_clusters=treated_clusters,
        n_score_clusters=n_score,
        underpowered=int(treated_clusters < MIN_TREATED_CLUSTERS),
        regressors_kept="|".join(kept),
        regressors_dropped="|".join(dropped),
    )


# NOTE (2026-09-12). §3.10 3c's balanced arm is indexed by the cyclone's FIRST
# exposed season and by nothing else: it restricts to units retained in both
# t_c-1 and t_c and then regresses on the exposure CLASS, not on the storm. Two
# cyclones in the same season therefore produce identical balanced estimates --
# FANI and BULBUL are both 2019, and their rows are the same number twice. That
# is the frozen design, not a bug, but it must not be read as two independent
# confirmations. The per-storm separation lives in item 1b, which does use a
# storm-specific indicator.
def balanced_cell_ids(panel, pre_year, post_year):
    r = panel[panel["retained"] == 1]
    pre = set(r.loc[r["year"] == pre_year, "cell_id"])
    post = set(r.loc[r["year"] == post_year, "cell_id"])
    return pre & post


# ===========================================================================
# self-test
# ===========================================================================
def _brute_force_ols(y, X, fe_frames, cl_codes, n_clusters):
    """Explicit dummy-variable OLS with cluster-robust VCE.

    Reference implementation for the self-test. Slow and memory-hungry by
    design -- it exists only to prove the absorbed-FE path returns the same
    numbers, which is the one claim in this file that a reader cannot check by
    eye.
    """
    cols = [np.ones((len(y), 1))]
    for f in fe_frames:
        codes, _ = pd.factorize(f, sort=False)
        codes = np.asarray(codes, np.int64)
        ng = codes.max() + 1
        D = np.zeros((len(y), ng))
        D[np.arange(len(y)), codes] = 1.0
        cols.append(D[:, 1:])          # drop one level per grouping
    cols.append(np.asarray(X, float).reshape(len(y), -1))
    XX = np.column_stack(cols)
    XtX_inv = np.linalg.pinv(XX.T @ XX)
    beta = XtX_inv @ (XX.T @ y)
    e = y - XX @ beta
    n, K = XX.shape
    meat = _cluster_meat(XX, e, cl_codes, n_clusters)
    dof = (n_clusters / (n_clusters - 1)) * ((n - 1) / (n - K))
    V = XtX_inv @ meat @ XtX_inv * dof
    se = np.sqrt(np.maximum(np.diag(V), 0.0))
    return beta[-1], se[-1]


def selftest():
    print("=" * 74)
    print("SELF-TEST -- absorbed-FE estimator vs brute-force dummy-variable OLS")
    print("=" * 74)
    rng = np.random.default_rng(7)
    n_d, n_y, n_p = 12, 8, 30
    rows = []
    for di in range(n_d):
        for yr in range(2017, 2017 + n_y):
            for p in range(n_p):
                rows.append((f"D{di:02d}", yr, f"c{di:02d}_{p:03d}"))
    df = pd.DataFrame(rows, columns=["district", "year", "cell_id"])
    df["S"] = ((df["district"].str[1:].astype(int) < 4) &
               (df["year"].isin([2019, 2020]))).astype(int)
    a = pd.Series(rng.normal(0, 5, n_d), index=sorted(df.district.unique()))
    g = pd.Series(rng.normal(0, 3, n_y), index=sorted(df.year.unique()))
    TRUE_BETA = 4.0
    df["y"] = (a[df.district].values + g[df.year].values
               + TRUE_BETA * df["S"] + rng.normal(0, 2, len(df)))

    cl, _ = pd.factorize(df["district"], sort=False)
    cl = np.asarray(cl, np.int64)
    G = int(cl.max()) + 1

    fe = FEAbsorber(df, ["district", "year"])
    yd = fe.demean(df["y"].values)
    Xd = fe.demean_matrix(df[["S"]].values)
    b_abs, se_abs, _ = within_fit(yd, Xd, cl, G, fe.k_absorbed)

    b_bf, se_bf = _brute_force_ols(df["y"].values, df[["S"]].values,
                                   [df["district"], df["year"]], cl, G)

    print(f"  true beta            {TRUE_BETA: .6f}")
    print(f"  absorbed-FE beta     {b_abs[0]: .6f}   se {se_abs[0]:.6f}")
    print(f"  dummy-variable beta  {b_bf: .6f}   se {se_bf:.6f}")
    db, ds = abs(b_abs[0] - b_bf), abs(se_abs[0] - se_bf)
    print(f"  |diff| beta {db:.3e}   |diff| se {ds:.3e}")
    ok_pt = db < 1e-8 and ds < 1e-8
    print(f"  [{'PASS' if ok_pt else 'FAIL'}] absorbed FE reproduces dummy-variable OLS")

    # weighted case
    w = rng.uniform(0.5, 2.0, len(df))
    fw = FEAbsorber(df, ["district", "year"], weights=w)
    ydw = fw.demean(df["y"].values)
    Xdw = fw.demean_matrix(df[["S"]].values)
    b_w, se_w, _ = within_fit(ydw, Xdw, cl, G, fw.k_absorbed, w=w)
    sw = np.sqrt(w)
    dfw = df.copy()
    # brute-force WLS: scale y, X and every dummy by sqrt(w)
    cols = [sw[:, None]]
    for f in [dfw["district"], dfw["year"]]:
        codes, _ = pd.factorize(f, sort=False)
        codes = np.asarray(codes, np.int64)
        D = np.zeros((len(df), codes.max() + 1))
        D[np.arange(len(df)), codes] = 1.0
        cols.append(D[:, 1:] * sw[:, None])
    cols.append(df[["S"]].values * sw[:, None])
    XXw = np.column_stack(cols)
    bw_all = np.linalg.pinv(XXw.T @ XXw) @ (XXw.T @ (df["y"].values * sw))
    dbw = abs(b_w[0] - bw_all[-1])
    print(f"  weighted: absorbed {b_w[0]: .6f}  vs brute-force WLS {bw_all[-1]: .6f}"
          f"   |diff| {dbw:.3e}")
    ok_w = dbw < 1e-7
    print(f"  [{'PASS' if ok_w else 'FAIL'}] weighted absorbed FE reproduces WLS")

    # bootstrap sanity: strong effect rejects, pure noise does not
    res_eff = wild_cluster_bootstrap(yd, Xd, fe, cl, G, 0, n_boot=499, seed=1)
    df["y0"] = (a[df.district].values + g[df.year].values
                + rng.normal(0, 2, len(df)))
    yd0 = fe.demean(df["y0"].values)
    res_null = wild_cluster_bootstrap(yd0, Xd, fe, cl, G, 0, n_boot=499, seed=1)
    print(f"  WCB p, true effect  {res_eff['p_wcb']:.4f}   "
          f"CI [{res_eff['ci_lo']:+.3f}, {res_eff['ci_hi']:+.3f}]")
    print(f"  WCB p, pure noise   {res_null['p_wcb']:.4f}   "
          f"CI [{res_null['ci_lo']:+.3f}, {res_null['ci_hi']:+.3f}]")
    ok_b = res_eff["p_wcb"] < 0.05 < res_null["p_wcb"]
    ok_ci = res_eff["ci_lo"] < TRUE_BETA < res_eff["ci_hi"]
    print(f"  [{'PASS' if ok_b else 'FAIL'}] bootstrap separates signal from noise")
    print(f"  [{'PASS' if ok_ci else 'FAIL'}] 95% WCB interval covers the true beta")

    # a non-positive cluster-robust variance must NOT become se = 0
    V_bad = np.array([[-9.4e-18, 0.0, 0.0],
                      [0.0, 4.0, 0.0],
                      [0.0, 0.0, 0.0]])
    se_bad = _se_from_vce(V_bad)
    ok_v = (not np.isfinite(se_bad[0])) and abs(se_bad[1] - 2.0) < 1e-12 \
        and (not np.isfinite(se_bad[2]))
    print(f"\n  degenerate VCE diag(-9.4e-18, 4.0, 0.0) -> se "
          f"({se_bad[0]}, {se_bad[1]:.3f}, {se_bad[2]})")
    print(f"  [{'PASS' if ok_v else 'FAIL'}] non-positive variance becomes NaN, "
          f"never 0.000")

    # and the whole path must route it to "not estimable", point estimate kept
    dfp = df.copy()
    dfp["y_exact"] = fe.demean(df["S"].values) * 3.0   # residuals exactly zero
    res_deg = twfe(dfp.assign(cell_id=dfp["cell_id"], retained=1),
                   "y_exact", ["S"], 99, 1, "S")
    ok_d = (res_deg.get("status") == "not_estimable"
            and np.isfinite(res_deg.get("coef", np.nan)))
    print(f"  perfect-fit stratum -> status={res_deg.get('status')}, "
          f"coef={res_deg.get('coef', float('nan')):.4f} retained in the row")
    print(f"  [{'PASS' if ok_d else 'FAIL'}] degenerate stratum reported as not "
          f"estimable with its point estimate, not as a zero-width interval")
    ok_all_v = ok_v and ok_d

    # logit against a known DGP
    Xl = np.column_stack([np.ones(4000), rng.normal(0, 1, 4000)])
    pl = 1.0 / (1.0 + np.exp(-(0.4 + 1.2 * Xl[:, 1])))
    yl = (rng.uniform(size=4000) < pl).astype(float)
    bl, _, conv = logit_irls(yl, Xl)
    print(f"  logit IRLS  true (0.400, 1.200)  fitted "
          f"({bl[0]:.3f}, {bl[1]:.3f})  converged={conv}")
    ok_l = conv and abs(bl[0] - 0.4) < 0.15 and abs(bl[1] - 1.2) < 0.15
    print(f"  [{'PASS' if ok_l else 'FAIL'}] logit recovers its DGP")

    allok = ok_pt and ok_w and ok_b and ok_ci and ok_l and ok_all_v
    print("=" * 74)

    # ---- the screened-sample leak, which lived undetected until 2026-09-13 --
    # A panel whose UNRETAINED rows carry a large planted effect and whose
    # retained rows carry none. If twfe ever stops restricting to retained == 1,
    # this check fails loudly instead of the contamination showing up as a
    # publishable coefficient. The committed pixel panel had 44,976 unretained
    # rows with finite breakpoints -- 59% of the 76,717 the estimator was
    # using -- and no test noticed.
    rng_l = np.random.default_rng(4242)
    rows_l = []
    for di in range(12):
        dist = "D%d" % di
        for yr in range(2017, 2026):
            trt = 1 if (di < 4 and yr >= 2021) else 0
            for ret in (1, 0):
                rows_l.append(dict(
                    district=dist, year=yr, cell_id="%s_%d" % (dist, ret),
                    retained=ret, S_x=trt,
                    y=rng_l.normal(0.0, 1.0) + (0.0 if ret else 40.0 * trt)))
    pl = pd.DataFrame(rows_l)
    n_ret = int(pl["retained"].sum())
    r_screen = twfe(pl, "y", ["S_x"], 999, 11, "S_x")
    r_leak = twfe(pl, "y", ["S_x"], 999, 11, "S_x", retained_only=False)
    ok = (int(r_screen.get("n_obs", -1)) == n_ret
          and abs(float(r_screen.get("coef", 9e9))) < 1.5
          and int(r_leak.get("n_obs", -1)) == len(pl)
          and float(r_leak.get("coef", 0.0)) > 5.0)
    allok &= ok
    print("\n  panel of %d rows, %d retained; the unretained ones carry a "
          "planted +40 d effect" % (len(pl), n_ret))
    print("  screened   n_obs %s  beta %+.3f" % (r_screen.get("n_obs"),
                                                 r_screen.get("coef", float("nan"))))
    print("  unfiltered n_obs %s  beta %+.3f" % (r_leak.get("n_obs"),
                                                 r_leak.get("coef", float("nan"))))
    print("  [%s] twfe estimates on retained == 1 only; the planted effect in "
          "the screened-out rows does not reach the coefficient" %
          ("PASS" if ok else "FAIL"))

    print("=" * 74)
    # ------------------------------------------------------------------
    # RESUME KEY: PORTABLE AND CONTENT-BASED (2026-09-15).
    #
    # The old key recorded an ABSOLUTE panel path and compared FILENAMES. Two
    # consequences, both demonstrated by an external audit and both fixed:
    #
    #   * the same bytes in another clone were REFUSED, because the directory
    #     prefix differed -- the key identified the machine, not the input;
    #   * an EDITED input with the same name was ACCEPTED, because only the name
    #     was compared -- so rows computed from different data spliced silently.
    #
    # These two cases are the test. A third asserts the estimator source itself
    # is in the key, so rows computed by a different version cannot be spliced.
    # ------------------------------------------------------------------
    import shutil
    import tempfile

    class _A:
        def __init__(self, panel, exposure, phase, boot=9999, seed=SEED,
                     level="district", balanced=False):
            self.panel, self.exposure, self.phase_exposure = panel, exposure, phase
            self.boot, self.seed, self.level = boot, seed, level
            self.balanced = balanced

    with tempfile.TemporaryDirectory() as td:
        clone_a = os.path.join(td, "clone_a", "results")
        clone_b = os.path.join(td, "clone_b", "results")
        os.makedirs(clone_a)
        os.makedirs(clone_b)
        pan_a = os.path.join(clone_a, "panel.csv")
        pha_a = os.path.join(clone_a, "exposure_phase.csv")
        with open(pan_a, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("district,year,y\nD00,2017,1\nD01,2018,2\n")
        with open(pha_a, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("district,year,S_phase_rise\nD00,2017,0\nD01,2018,1\n")
        pan_b = os.path.join(clone_b, "panel.csv")
        pha_b = os.path.join(clone_b, "exposure_phase.csv")
        shutil.copyfile(pan_a, pan_b)
        shutil.copyfile(pha_a, pha_b)
        exp = _find_doc("district_cyclone_exposure_ibtracs50km.csv")

        key_a = _build_run_key(_A(pan_a, exp, pha_a))
        key_b = _build_run_key(_A(pan_b, exp, pha_b))

        # (1) SAME BYTES, DIFFERENT CLONE -> the key must match
        moved_ok = (key_a["panel_sha"] == key_b["panel_sha"]
                    and key_a["phase_exposure_sha"] == key_b["phase_exposure_sha"]
                    and key_a["code_sha"] == key_b["code_sha"]
                    and key_a["options"] == key_b["options"])
        allok &= moved_ok
        print("\n  clone A panel_sha %s" % key_a["panel_sha"][:16])
        print("  clone B panel_sha %s" % key_b["panel_sha"][:16])
        print("  absolute paths differ; logical path recorded: %r"
              % key_a["panel_path"])
        print("  [%s] the SAME INPUT BYTES in ANOTHER CLONE resume successfully: "
              "every hash and option matches, and no absolute path is stored"
              % ("PASS" if moved_ok else "FAIL"))

        # (2) CHANGED PHASE-EXPOSURE BYTES -> the key must differ
        with open(pha_b, "a", encoding="utf-8", newline="\n") as fh:
            fh.write("D02,2019,1\n")
        key_b2 = _build_run_key(_A(pan_b, exp, pha_b))
        refused = key_b2["phase_exposure_sha"] != key_a["phase_exposure_sha"]
        diff = {k for k in key_a if key_a[k] != key_b2[k]}
        allok &= refused and diff == {"phase_exposure_sha"}
        print("\n  appended one row to the phase-exposure table")
        print("  phase_exposure_sha %s -> %s"
              % (key_a["phase_exposure_sha"][:16], key_b2["phase_exposure_sha"][:16]))
        print("  key fields differing: %s" % sorted(diff))
        print("  [%s] CHANGED INPUT BYTES are refused: the content hash moves "
              "while the filename does not, which is exactly the splice the old "
              "name-only key allowed" % ("PASS" if refused else "FAIL"))

        # (3) the estimator source is in the key
        has_code = (key_a.get("code_sha")
                    and key_a["code_sha"] == _content_hash(os.path.abspath(__file__))
                    and key_a["code_path"] == "python/attrition_diagnostics.py")
        allok &= bool(has_code)
        print("\n  code_path %r  code_sha %s"
              % (key_a["code_path"], key_a["code_sha"][:16]))
        print("  [%s] the estimator SOURCE is part of the key, so rows computed "
              "by a different version of this file cannot be spliced in"
              % ("PASS" if has_code else "FAIL"))

        # (4) numerical options and requested block coverage are both in the key
        k999 = _build_run_key(_A(pan_a, exp, pha_a, boot=999))
        kbal = _build_run_key(_A(pan_a, exp, pha_a, balanced=True))
        opt_ok = (k999["options"]["boot"] == 999
                  and k999["options"] != key_a["options"]
                  and kbal["coverage"] != key_a["coverage"]
                  and kbal["coverage"]["balanced"] is True
                  and "python/lf_output.py" in key_a["local_helpers"]
                  and key_a["runtime"]["numpy"] == np.__version__)
        allok &= opt_ok
        print("\n  boot 9999 vs 999 -> options differ: %s"
              % (k999["options"] != key_a["options"]))
        print("  balanced=False vs True -> coverage differs: %s"
              % (kbal["coverage"] != key_a["coverage"]))
        print("  [%s] numerical options, requested block coverage, local helper "
              "hashes and the numerical runtime are all bound into schema 3"
              % ("PASS" if opt_ok else "FAIL"))

        # (5) edit a helper without changing its filename: the key must move.
        helper_copy = os.path.join(td, "lf_output.py")
        with open(helper_copy, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("version one\n")
        kh1 = _build_run_key(_A(pan_a, exp, pha_a),
                             _helper_paths=[helper_copy])
        with open(helper_copy, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("version two\n")
        kh2 = _build_run_key(_A(pan_a, exp, pha_a),
                             _helper_paths=[helper_copy])
        helper_ok = kh1["local_helpers"] != kh2["local_helpers"]
        allok &= helper_ok
        print("  [%s] editing a local helper changes the run key"
              % ("PASS" if helper_ok else "FAIL"))

        # (6) the runtime is identity, not decoration.
        kr1 = _build_run_key(_A(pan_a, exp, pha_a),
                             _runtime_override={"python": "3.11.15"})
        kr2 = _build_run_key(_A(pan_a, exp, pha_a),
                             _runtime_override={"python": "3.12.14"})
        runtime_ok = kr1["runtime"] != kr2["runtime"]
        allok &= runtime_ok
        print("  [%s] changing a runtime field changes the run key"
              % ("PASS" if runtime_ok else "FAIL"))

    print("SELF-TEST " + ("PASSED" if allok else "FAILED"))
    print("=" * 74)
    return 0 if allok else 1


# ===========================================================================
def load_panel(path, level, verbose=True):
    """Read a §3.10 panel and normalise its schema for the given level.

    Extracted from main() on 2026-09-13 so that the focused diagnostic scripts
    load a panel through exactly this code and cannot drift from it. A second
    copy of the district-level column mapping is the kind of duplication that
    silently produces two different samples under one name.
    """
    panel = pd.read_csv(path)
    if level == "district":
        # The district-season panel is the §3 lead-in's PRIMARY estimand. It has
        # one row per district-season, `estimable` where the pixel panel has
        # `retained`, and no cell_id. Mapping is explicit here rather than by
        # guesswork, and the cluster is still the district, so the two levels
        # produce directly comparable standard errors.
        if "estimable" in panel.columns and "retained" not in panel.columns:
            panel["retained"] = panel["estimable"].astype(int)
        if "cell_id" not in panel.columns:
            panel["cell_id"] = panel["district"].astype(str)
        if verbose:
            print("level=district: one row per district-season, retained := "
                  "estimable, cell_id := district")
    missing = [c for c in PANEL_REQUIRED if c not in panel.columns]
    if missing:
        raise SystemExit(
            f"panel is missing required columns {missing}\n"
            f"present: {sorted(panel.columns)}\n"
            "This script will not guess a mapping: §3.10's quantities are only "
            "meaningful against the documented schema.")
    panel["year"] = panel["year"].astype(int)
    panel["retained"] = panel["retained"].astype(int)
    return panel


# ===========================================================================
def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Protocol v1 §3.10 items 1-3 (Lee bounds withdrawn, 3b).")
    ap.add_argument("--panel")
    ap.add_argument("--exposure")
    ap.add_argument("--out")
    ap.add_argument("--boot", type=int, default=N_BOOT)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--resume", action="store_true",
                    help="reuse strata already present in "
                         "Table_SX_AttritionDiagnostic.partial.csv in --out, "
                         "recomputing only what is missing. Refuses if the "
                         "recorded run key (level, panel, exposure, boot, seed, "
                         "arms) differs from this invocation, so a partial "
                         "table from different settings can never be spliced "
                         "into a new one.")
    ap.add_argument("--balanced", action="store_true",
                    help="also run §3.10 3c's descriptive two-season rows. Off by "
                         "default: the per-cyclone event estimates live in "
                         "python/event_study.py, and these rows are a "
                         "descriptive restriction indexed by season, not per-cyclone "
                         "estimates.")
    ap.add_argument("--phase-exposure", default=None,
                    help="output of python/classify_exposure_phase.py. When "
                         "given, a robustness arm is reported in which severe "
                         "exposure is classified against the district's "
                         "BASELINE markers rather than the catalogue's optical "
                         "timing_class. The frozen classes remain the headline.")
    ap.add_argument("--level", choices=["pixel", "district"], default="pixel",
                    help="pixel: the per-pixel-season panel. district: the "
                         "district-season panel, which is the §3 lead-in's "
                         "primary estimand.")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()
    if not (args.panel and args.exposure and args.out):
        ap.error("--panel, --exposure and --out are all required "
                 "(or run --selftest)")

    panel = load_panel(args.panel, args.level)

    # _find_doc, not a bare read: run_all.sh cds into python/ and passes the
    # catalogue by bare filename, but the file lives in docs/, so this call
    # site raised a bare FileNotFoundError and the declared reproducible run
    # could not execute at all. Found 2026-09-15. The same defect class an
    # audit found in three scripts on 2026-09-13, which is why _find_doc
    # exists -- this call site was simply never routed through it.
    exposure = pd.read_csv(_resolve_exposure(args.exposure))
    years = sorted(panel["year"].unique())
    districts = sorted(panel["district"].unique())

    print(f"panel  {len(panel):,} pixel-years | "
          f"{panel['cell_id'].nunique():,} pixels | "
          f"{len(districts)} districts | seasons {years[0]}-{years[-1]}")
    print(f"retained overall: {panel['retained'].mean():.4f}")
    have_phen = [p for p in PHENOMETRICS if p in panel.columns]
    if not have_phen:
        print("WARNING: no phenometric column present -- item 1 (attrition "
              "diagnostic) will run; items 3a/3c need sos/pos/eos and will be "
              "reported as not computable.")

    # Every panel district must resolve to a catalogue district. Without this
    # check a naming difference (underscores in a filename, spaces in the
    # catalogue) silently codes a district as never exposed, which is not an
    # error the output would show -- it would just read as a null result.
    cat_names = set(exposure["district_gadm_name"].astype(str))
    unresolved = [d for d in districts if d not in cat_names]
    if unresolved:
        alt = {d: d.replace("_", " ") for d in unresolved}
        still = [d for d, a in alt.items() if a not in cat_names]
        if still:
            raise SystemExit(
                "these panel districts do not appear in the exposure "
                f"catalogue, under their own name or with underscores replaced "
                f"by spaces: {still}\n"
                f"catalogue districts: {sorted(cat_names)}\n"
                "Refusing to run: an unresolved district would be coded as "
                "never exposed and the result would read as a null, not as an "
                "error.")
        panel["district"] = panel["district"].replace(alt)
        districts = sorted(panel["district"].unique())
        print(f"normalised {len(alt)} district names to the catalogue spelling: "
              f"{sorted(alt.values())}")
    else:
        print(f"all {len(districts)} panel districts resolve in the exposure "
              f"catalogue")

    assert_cyclones_resolve(exposure)
    extra = warn_unlisted_severe_storms(exposure, districts)
    if extra:
        print("\nNOTE: severe storms hitting roster districts that are NOT in "
              f"the protocol's estimable list: {extra}")
        print("  These enter the §3.8 A exposure panel through S_pre/S_harv "
              "but get no per-cyclone row. That is the frozen §3.8 B design "
              "(named-cyclone stacks are the six of §1.1); if the catalogue "
              "has changed, revisit §1.1 before reporting.")

    tab = build_exposure_table(exposure, districts, years)
    panel = panel.merge(tab, on=["district", "year"], how="left")
    for c in ["S_pre_season", "S_harvest_window", "M_minor",
              "Slag_pre_season", "Slag_harvest_window"]:
        panel[c] = panel[c].fillna(0).astype(int)

    rows = []

    # A long run that is killed loses everything it computed unless it writes as
    # it goes. Each block flushes what is finished, so a partial run leaves a
    # partial table naming the strata it completed rather than nothing.
    os.makedirs(args.out, exist_ok=True)
    _partial = os.path.join(args.out, "Table_SX_AttritionDiagnostic.partial.csv")

    def _flush():
        if rows:
            pd.DataFrame(rows).to_csv(_partial, index=False)

    # A resumed run must be the SAME run. A partial table carries no record of
    # the settings that produced it, so one is written beside it and compared:
    # splicing rows computed at --boot 999 into a table labelled 9999, or rows
    # from a different panel, would be undetectable in the output.
    _stamp = os.path.join(args.out, "run_key.json")
    # Schema 3 binds both numerical identity and exact requested coverage.
    # Broader and narrower runs never share a partial table: that is the only
    # fail-closed way to prevent stale extra blocks or incomplete broad output.
    _key = _build_run_key(args)
    _prev = {}
    if args.resume:
        if not (os.path.exists(_stamp) and os.path.exists(_partial)):
            print("--resume: no partial table and run key in %s; starting from "
                  "scratch." % args.out)
        else:
            old_key = json.load(open(_stamp))
            if old_key.get("schema") != _key["schema"]:
                print("\n*** STOP *** --resume refused. The partial table in %s "
                      "carries run-key schema %r; this build writes schema %r. "
                       "An older key does not bind exact block coverage, all "
                       "local helpers and the numerical runtime, so it cannot "
                       "certify that the rows belong to this invocation. Delete the partial "
                      "table and rerun. Nothing was written."
                      % (args.out, old_key.get("schema"), _key["schema"]))
                return 2
            diff = {k: (old_key.get(k), v) for k, v in _key.items()
                    if old_key.get(k) != v}
            if diff:
                print("\n*** STOP *** --resume refused. The partial table in "
                      "%s was computed with different settings:" % args.out)
                for k, (a, b) in sorted(diff.items()):
                    print("    %-15s partial=%r  this run=%r" % (k, a, b))
                print("  Delete the partial table, or point --out somewhere "
                      "else. Nothing was written.")
                return 2
            pv = pd.read_csv(_partial)
            _prev = {r["stratum"]: {k: v for k, v in r.items()
                                    if not (isinstance(v, float) and pd.isna(v))}
                     for r in pv.to_dict("records")}
            print("--resume: %d strata reusable from %s"
                  % (len(_prev), os.path.basename(_partial)))
    with open(_stamp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(_key, fh, indent=2, sort_keys=True)

    _n_reused = [0]

    def _reuse(stratum):
        """True when this stratum is already in the loaded partial table.

        Appends the cached row and reports it, so a resumed run prints the
        whole table and not only the part it recomputed."""
        r = _prev.get(stratum)
        if r is None:
            return False
        rows.append(r)
        _n_reused[0] += 1
        return True

    # ---- §3.10 item 1a: per severe-exposure class -------------------------
    # RESUME VALIDATION, WIDENED 2026-09-15 (fourteenth pass).
    #
    # Until today exactly ONE stratum was recomputed and compared -- a single
    # canary. An audit pointed out what that is worth: it demonstrates that one
    # row reproduces, and nothing about the other 252 or 307. A single agreeing
    # row is consistent with a partial table in which every other row came from
    # somewhere else.
    #
    # EVERY attrition-diagnostic stratum is now recomputed and compared under
    # --resume: all of SEVERE_CLASSES and, below, all of the phase strata. They
    # are the cheap ones -- one regression each on the already-loaded panel --
    # so widening the check from one to all of them costs little.
    #
    # WHAT THIS DOES AND DOES NOT ESTABLISH, stated because the previous comment
    # overstated it. It establishes that every diagnostic row in the partial
    # table reproduces on this panel. It does NOT establish that the
    # `headline:`, `ipsw:`, `balanced:`, `pretrend:` or `phase_*` rows do: those
    # go through `twfe` rather than `attrition_diagnostic`, they are far more
    # expensive, and they are NOT re-verified here. --resume is therefore a
    # CONVENIENCE WITH A SAMPLED PROVENANCE CHECK, not a guarantee that a
    # resumed table equals a clean one.
    #
    # THE TABLES SHIPPED WITH THIS PACKAGE WERE PRODUCED BY CLEAN RUNS WITH NO
    # --resume, precisely because of that gap. Anyone reproducing them for
    # acceptance should do the same.
    _verify_strata = [f"class:{c}" for c in SEVERE_CLASSES]
    _resume_checked, _resume_bad = [], []
    for cls in SEVERE_CLASSES:
        col = "S_" + cls
        sk = f"class:{cls}"
        if sk not in _verify_strata and _reuse(sk):
            continue
        r = attrition_diagnostic(panel, col, sk, args.boot, args.seed)
        if sk in _prev:
            cached = _prev[sk]
            bad = []
            for fld in ("coef", "se", "p_wcb", "n_obs", "n_clusters"):
                a, b = cached.get(fld), r.get(fld)
                if a is None or b is None:
                    continue
                try:
                    if abs(float(a) - float(b)) > 1e-9 * max(1.0, abs(float(b))):
                        bad.append((fld, a, b))
                except (TypeError, ValueError):
                    if str(a) != str(b):
                        bad.append((fld, a, b))
            _resume_checked.append(sk)
            if bad:
                _resume_bad.append((sk, bad))
        # The row is appended for EVERY stratum in this loop, resumed or not.
        # (Bug introduced and caught 2026-09-15: when the resume check was
        # widened, this append was left inside the reporting block that follows
        # the loop, so a clean run emitted NO class:* rows at all. The
        # completeness gate caught it on the first district table produced --
        # 252 rows instead of 253, and a KeyError on class:pre_season. It is
        # exactly the shape the gate exists for, and it was mine.)
        rows.append(r)
        _print_diag(r)
    if _resume_bad:
        print("\n*** STOP *** --resume refused. The partial table in %s carries "
              "a matching run key but does not reproduce on this panel."
              % args.out)
        for sk, bad in _resume_bad:
            print("  %s:" % sk)
            for fld, a, b in bad:
                print("    %-12s partial=%r  recomputed=%r" % (fld, a, b))
        print("  %d of %d recomputed diagnostic strata disagree. The partial "
              "table is not from this panel. Delete it, or point --out "
              "somewhere else. Nothing was written."
              % (len(_resume_bad), len(_resume_checked)))
        return 2
    if _resume_checked:
        print("  --resume provenance check: %d of %d diagnostic strata "
              "recomputed and all reproduce (%s). The twfe-based families "
              "(headline, ipsw, balanced, pretrend, phase) are NOT re-verified "
              "-- resume is a convenience with a sampled check, not a guarantee."
              % (len(_resume_checked), len(_verify_strata),
                 ", ".join(_resume_checked)))

    # ---- §3.10 item 1b: per estimable named cyclone -----------------------
    for storm in ESTIMABLE_CYCLONES:
        pairs = cyclone_district_seasons(exposure, storm, districts)
        col = f"S_{storm}"
        panel[col] = [1 if (d, y) in pairs else 0
                      for d, y in zip(panel["district"], panel["year"])]
        if _reuse(f"cyclone:{storm}"):
            continue
        r = attrition_diagnostic(panel, col, f"cyclone:{storm}",
                                 args.boot, args.seed)
        rows.append(r)
        _print_diag(r)

    # ---- §3.8 A headline, IPSW and descriptive two-season restriction ------
    # Which declared set applies is decided by which one the panel can support,
    # not by preference: the optical set if it is complete, otherwise the radar
    # set declared on 2026-09-12. dist_to_track_km is built here from the
    # exposure file when the panel does not already carry it.
    if "dist_to_track_km" not in panel.columns and \
            "min_dist_to_track34kt_km" in exposure.columns:
        key = ("season" if "season" in exposure.columns else "year")
        dd = (exposure.groupby(["district_gadm_name", key])
              ["min_dist_to_track34kt_km"].min().reset_index())
        dd.columns = ["district_gadm_name", "year", "dist_to_track_km"]
        dd["district"] = dd["district_gadm_name"].str.replace(" ", "_",
                                                             regex=False)
        panel = panel.merge(dd[["district", "year", "dist_to_track_km"]],
                            on=["district", "year"], how="left")
        panel["dist_to_track_km"] = panel["dist_to_track_km"].fillna(
            NO_STORM_DIST_KM)
        print(f"\nbuilt dist_to_track_km from the exposure file: "
              f"{(panel['dist_to_track_km'] < NO_STORM_DIST_KM).mean():.3f} of "
              f"rows have a catalogued 34-kt track, the rest coded at "
              f"{NO_STORM_DIST_KM:.0f} km")

    optical_missing = [c for c in IPSW_COVARIATES if c not in panel.columns]
    if not optical_missing:
        declared, label = IPSW_COVARIATES, "optical"
    else:
        declared, label = IPSW_COVARIATES_RADAR, "radar"
    ipsw_have = [c for c in declared if c in panel.columns]
    ipsw_missing = [c for c in declared if c not in panel.columns]
    w_col = None
    if ipsw_have:
        fe_d = pd.get_dummies(panel["district"], drop_first=True).astype(float)
        fe_y = pd.get_dummies(panel["year"], drop_first=True).astype(float)
        # A covariate that does not vary WITHIN the fixed effects contributes
        # nothing and makes the design singular. The static terrain and geometry
        # covariates are constant within a district by construction, so at
        # district level they are absorbed entirely by the district dummies
        # while at pixel level they vary across pixels and are informative.
        # Screening them here, by name, is the difference between a reported
        # model and a silently rank-deficient one -- the IRLS would otherwise
        # return converged=False and weights pinned at the clip.
        absorbed = []
        keep_cov = []
        for c in ipsw_have:
            v = panel[c].astype(float)
            within = v - v.groupby(panel["district"]).transform("mean")
            within = within - within.groupby(panel["year"]).transform("mean")
            scale = float(np.nanstd(v)) or 1.0
            if float(np.nanstd(within)) <= 1e-8 * scale:
                absorbed.append(c)
            else:
                keep_cov.append(c)
        if absorbed:
            print(f"\nIPSW: {absorbed} have no variation within district and "
                  f"season fixed effects at this level and are absorbed by "
                  f"them. Dropped from the score and named here rather than "
                  f"left to make the design singular.")
        if not keep_cov:
            print("IPSW not computable: every declared covariate is absorbed "
                  "by the fixed effects at this level.")
            ipsw_have = []
        else:
            ipsw_have = keep_cov
    if ipsw_have:
        # SEPARATION. A fixed-effect level whose outcome never varies predicts
        # it perfectly: its dummy drives p to 0 or 1, the IRLS does not
        # converge, and the weights come back pinned at the clip. That is not a
        # fitted model, and reporting it with a warning line underneath invites
        # someone to use it anyway. Such levels carry no information about
        # selection -- a conditional logit drops them too -- so they are dropped
        # here, by name and with a count, and what is left is reported.
        yret_all = panel["retained"].astype(float)
        keep = pd.Series(True, index=panel.index)
        sep_note = []
        for gcol, gname in (("district", "districts"), ("year", "seasons")):
            v = yret_all.groupby(panel[gcol]).transform("nunique")
            const = panel.loc[v <= 1, gcol].nunique()
            if const:
                sep_note.append(f"{const} {gname} whose outcome never varies")
            keep &= (v > 1)
        n_keep = int(keep.sum())
        n_evt = int(min(yret_all[keep].sum(), (1 - yret_all[keep]).sum()))
        if sep_note:
            print(f"\nIPSW: dropping {', '.join(sep_note)} -- they predict "
                  f"retention perfectly and carry no information about "
                  f"selection. {n_keep} of {len(panel)} rows remain, with "
                  f"{n_evt} in the smaller outcome class.")
        if n_keep < MIN_IPSW_ROWS or n_evt < MIN_IPSW_EVENTS:
            print(f"IPSW NOT ESTIMABLE at this level: after dropping "
                  f"perfectly-predicting fixed-effect levels, {n_keep} rows "
                  f"and {n_evt} events remain, below the {MIN_IPSW_ROWS}-row / "
                  f"{MIN_IPSW_EVENTS}-event floor. Reported as not estimable "
                  f"rather than as weights pinned at the clip.")
            ipsw_have = []
    if ipsw_have:
        sub = panel[keep]
        fe_d2 = pd.get_dummies(sub["district"], drop_first=True).astype(float)
        fe_y2 = pd.get_dummies(sub["year"], drop_first=True).astype(float)
        Xl = np.column_stack([np.ones(len(sub)),
                              sub[ipsw_have].astype(float).values,
                              fe_d2.values, fe_y2.values])
        yret = sub["retained"].astype(float).values
        _, phat, conv = logit_irls(yret, Xl)
        # rows outside the fitted subsample get weight 1: they are units whose
        # retention is deterministic given their fixed effect, so reweighting
        # them would be inventing variation the data does not contain
        panel["_ipsw"] = 1.0
        panel.loc[keep, "_ipsw"] = 1.0 / np.clip(phat, 0.01, 1.0)
        w_col = "_ipsw"
        # A correctly fitted logit with an intercept reproduces the sample
        # mean of the outcome exactly. Cheap, independent, and it catches a
        # non-converged or mis-scaled fit that the coefficients would not.
        calib = abs(float(phat.mean()) - float(yret.mean()))
        n_fit, n_all = len(yret), len(panel)
        n_par = Xl.shape[1]
        epv = float(min(yret.sum(), n_fit - yret.sum())) / max(n_par, 1)
        if not conv:
            # A logit that has not converged is not a model. Its weights come
            # back pinned at the clip, which looks like a result and is not one,
            # and a WARNING line under a printed number is read by nobody. The
            # usual cause here is separation that survived the level-dropping
            # above, or simply too few events per parameter.
            print(f"\nIPSW NOT ESTIMABLE at this level: the logit did not "
                  f"converge on {n_fit} rows with {n_par} parameters and "
                  f"{epv:.1f} events per parameter. Weights discarded and no "
                  f"ipsw rows are produced, rather than reporting a fit pinned "
                  f"at the clip. §3.10 3a's reweighted estimate is therefore "
                  f"not available at this level. No same-estimand composition "
                  f"comparator is defined, so a triggered magnitude remains "
                  f"not point-identified under differential attrition.")
            panel.drop(columns=["_ipsw"], inplace=True, errors="ignore")
            w_col = None
            ipsw_have = []
        if ipsw_missing:
            tag = "ipsw_partial"
        elif absorbed:
            tag = "ipsw_absorbed"
        else:
            tag = "ipsw"
    if w_col:
        print(f"\nIPSW ({label} declaration, {tag}): logit on {ipsw_have} + "
              f"district/season FE, fitted on {n_fit} of {n_all} rows, "
              f"{epv:.1f} events per parameter, converged={conv}, weights in "
              f"[{panel['_ipsw'].min():.2f}, {panel['_ipsw'].max():.2f}]")
        if n_fit < n_all:
            src = sorted(panel.loc[keep, "district"].unique())
            print(f"  Identified off {len(src)} districts only: {src}. The "
                  f"weights carry no information about selection in the "
                  f"districts that never fail, so this arm is a check on those "
                  f"{len(src)} rather than a reweighting of the whole panel.")
        if ipsw_missing:
            print(f"  NOT the complete declared model: {ipsw_missing} absent "
                  f"from the panel. Reported as {tag}; the full set closes "
                  f"when the static per-district export "
                  f"(S1_STATIC_COVARIATES, 25 tasks) lands and is joined by "
                  f"python/merge_static_covariates.py. Do not report this as "
                  f"the pre-declared IPSW.")
        elif absorbed:
            print(f"  Every declared covariate is PRESENT; {absorbed} are "
                  f"absorbed by the fixed effects at this level, which is a "
                  f"property of the level and not a gap in the data. Reported "
                  f"as {tag}. The complete declared model is estimable at "
                  f"pixel level, where these vary across pixels within a "
                  f"district.")
        print(f"  calibration |mean(p_hat) - mean(retained)| = {calib:.2e} "
              f"({'OK' if calib < 1e-6 else 'SUSPECT — inspect before using'})")
        if calib >= 1e-6:
            print("  WARNING: the fitted probabilities do not reproduce the "
                  "sample mean of the outcome. Inspect before using these "
                  "weights as the pre-declared estimate.")
    elif not [c for c in declared if c in panel.columns]:
        # only when the covariates were never there; the not-estimable cases
        # above have already said, precisely, why they are not estimable
        print(f"\nIPSW not computable: none of the {label} covariates "
              f"{declared} is present in the panel.")

    regs_main = ["S_pre_season", "S_harvest_window",
                 "Slag_pre_season", "Slag_harvest_window", "M_minor"]
    for phen in have_phen:
        for test_var in ["S_pre_season", "S_harvest_window"]:
            if _reuse(f"headline:{phen}:{test_var}"):
                base = _prev[f"headline:{phen}:{test_var}"]
            else:
                base = twfe(panel, phen, regs_main, args.boot, args.seed,
                            test_var)
                base.update(stratum=f"headline:{phen}:{test_var}",
                            estimator="unbalanced")
                rows.append(base)
                _print_twfe(base)
                _flush()

            if w_col and not _reuse(f"{tag}:{phen}:{test_var}"):
                ip = twfe(panel, phen, regs_main, args.boot, args.seed,
                          test_var, weights=w_col)
                est = tag
                ip.update(stratum=f"{est}:{phen}:{test_var}", estimator=est)
                rows.append(ip)
                _print_twfe(ip)
                _flush()

            # §3.10 3c, per estimable named cyclone. Indexed by the storm's
            # season only -- see the note on balanced_cell_ids: storms sharing a
            # season share the estimate.
            # OFF BY DEFAULT since 2026-09-13: the per-cyclone event-level
            # estimates H4 needs now come from python/event_study.py, which
            # builds the §3.8 B stacks properly. Leaving these rows in a table
            # labelled per-cyclone invited them to be read as those estimates.
            # They remain available with --balanced as a DESCRIPTIVE two-season
            # restriction. They are not a same-estimand composition comparator.
            for storm in (ESTIMABLE_CYCLONES if args.balanced else []):
                if _reuse(f"balanced:{phen}:{test_var}:{storm}"):
                    continue
                pairs = cyclone_district_seasons(exposure, storm, districts)
                if not pairs:
                    continue
                t_c = min(y for _, y in pairs)
                if t_c not in years or (t_c - 1) not in years:
                    rows.append(dict(stratum=f"balanced:{phen}:{test_var}:{storm}",
                                     estimator="balanced", status="not_estimable",
                                     reason=f"season {t_c} or {t_c-1} outside the "
                                            f"extracted panel"))
                    continue
                keep = balanced_cell_ids(panel, t_c - 1, t_c)
                if not keep:
                    rows.append(dict(stratum=f"balanced:{phen}:{test_var}:{storm}",
                                     estimator="balanced", status="not_estimable",
                                     reason="no pixel retained in both seasons "
                                            "(§3.10 item 2)"))
                    continue
                sub = panel[panel["cell_id"].isin(keep)
                            & panel["year"].isin([t_c - 1, t_c])]
                bal = twfe(sub, phen, regs_main, args.boot, args.seed, test_var)
                bal.update(stratum=f"balanced:{phen}:{test_var}:{storm}",
                           estimator="balanced",
                           balanced_n_pixels=len(keep))
                rows.append(bal)
                _print_twfe(bal)

    # ---- §3.9 pre-trend (lead) test -----------------------------------
    # Not a §3.10 quantity, but §3.10's reporting rule presumes parallel
    # trends, the lead columns are already assembled here, and a reviewer will
    # ask. §3.8 A: exposure in season t+1 cannot move phenology in season t,
    # so a non-zero lambda flags a violated parallel-trends assumption. Leads
    # are undefined for the final catalogue season, and those rows drop out
    # through dropna rather than being coded as unexposed.
    regs_lead = regs_main + ["Slead_pre_season", "Slead_harvest_window"]
    for phen in have_phen:
        for lead_var in ["Slead_pre_season", "Slead_harvest_window"]:
            if _reuse(f"pretrend:{phen}:{lead_var}"):
                continue
            pt = twfe(panel, phen, regs_lead, args.boot, args.seed, lead_var)
            pt.update(stratum=f"pretrend:{phen}:{lead_var}",
                      estimator="pretrend_lead")
            rows.append(pt)
            _print_twfe(pt)

    # -----------------------------------------------------------------------
    # ROBUSTNESS ARM (2026-09-13): exposure re-classified against the MEASURED
    # season. Named in the 2026-09-12 (third entry) deviation log and built by
    # python/classify_exposure_phase.py, which classifies each severe storm
    # against the district's BASELINE markers -- the mean over its unexposed
    # estimable seasons -- never against the markers of the season being
    # classified. The frozen §3.8 classes above remain the headline; this is
    # reported alongside, never instead of them.
    #
    # It matters because the catalogue's timing_class is Paper 1's optical
    # calendar: 14 of the 21 severe rows labelled harvest_window actually fall
    # in the RISE phase, before the district's baseline heading.
    if args.phase_exposure:
        ph = pd.read_csv(args.phase_exposure)
        pcols = [c for c in ph.columns if c.startswith(
            ("S_phase_", "Slag_phase_", "Slead_phase_"))]
        if not pcols:
            raise SystemExit(
                f"{args.phase_exposure} carries no S_phase_* columns. It must "
                "be the output of python/classify_exposure_phase.py.")
        before = len(panel)
        panel = panel.merge(ph[["district", "year"] + pcols],
                            on=["district", "year"], how="left")
        if len(panel) != before:
            raise SystemExit("the phase-exposure merge changed the row count; "
                             "it has duplicate district-season keys")
        phases = [c for c in pcols if c.startswith("S_phase_")]
        print("\n" + "=" * 74)
        print("ROBUSTNESS ARM -- exposure classified against the measured season")
        print("=" * 74)
        for c in phases:
            n_ds = int(panel.loc[panel[c] == 1, ["district", "year"]]
                       .drop_duplicates().shape[0])
            n_cl = int(panel.loc[panel[c] == 1, "district"].nunique())
            print(f"  {c:<26s} {n_ds:3d} exposed district-seasons, "
                  f"{n_cl:3d} treated clusters"
                  + ("" if n_cl >= MIN_TREATED_CLUSTERS else
                     f"   BELOW {MIN_TREATED_CLUSTERS}"))

        for c in phases:
            if _reuse(f"phase_attrition:{c}"):
                continue
            r = attrition_diagnostic(panel, c, f"phase_attrition:{c}",
                                     args.boot, args.seed)
            rows.append(r)
            _print_diag(r)

        regs_phase = ([c for c in pcols if c.startswith("S_phase_")]
                      + [c for c in pcols if c.startswith("Slag_phase_")]
                      + (["M_minor"] if "M_minor" in panel.columns else []))
        for phen in have_phen:
            for test_var in phases:
                if not _reuse(f"phase:{phen}:{test_var}"):
                    r = twfe(panel, phen, regs_phase, args.boot, args.seed,
                             test_var)
                    r.update(stratum=f"phase:{phen}:{test_var}",
                             estimator="phase_measured")
                    rows.append(r)
                    _print_twfe(r)
                    _flush()
                if w_col and not _reuse(f"phase_{tag}:{phen}:{test_var}"):
                    est = "phase_" + tag
                    ri = twfe(panel, phen, regs_phase, args.boot, args.seed,
                              test_var, weights=w_col)
                    ri.update(stratum=f"{est}:{phen}:{test_var}",
                              estimator=est)
                    rows.append(ri)
                    _print_twfe(ri)
                    _flush()

        leads = [c for c in pcols if c.startswith("Slead_phase_")]
        regs_phase_lead = regs_phase + leads
        for phen in have_phen:
            for lead_var in leads:
                if _reuse(f"phase_pretrend:{phen}:{lead_var}"):
                    continue
                pt = twfe(panel, phen, regs_phase_lead, args.boot, args.seed,
                          lead_var)
                pt.update(stratum=f"phase_pretrend:{phen}:{lead_var}",
                          estimator="phase_pretrend_lead")
                rows.append(pt)
                _print_twfe(pt)
                _flush()

    out = pd.DataFrame(rows)
    lead = ["stratum", "estimator", "status", "coef", "se", "t",
            "p_cluster", "p_wcb", "wcb_ci_lo", "wcb_ci_hi",
            "balanced_n_pixels",
            "n_obs", "n_pixels", "n_clusters", "n_treated_clusters",
            "n_score_clusters", "underpowered",
            "n_boot_requested", "n_boot_ok", "reason",
            "regressors_kept", "regressors_dropped"]
    cols = [c for c in lead if c in out.columns] + \
           [c for c in out.columns if c not in lead]
    out = out[cols]
    os.makedirs(args.out, exist_ok=True)
    dest = os.path.join(args.out, "Table_SX_AttritionDiagnostic.csv")
    out.to_csv(dest, index=False)
    print(f"\nwrote {dest}  ({len(out)} rows)")
    if _n_reused[0]:
        print(f"  {_n_reused[0]} of those rows were reused from the partial "
              f"table via --resume; {len(out) - _n_reused[0]} were computed "
              f"in this invocation.")

    print("\n" + "-" * 74)
    print("Protocol §3.10 reporting rule -- apply when writing these up:")
    print("  * zero treated support or non-computable bootstrap -> "
          "\"not estimable\"")
    print("  * attrition diagnostic p_WCB < 0.05 -> report the matching "
          "unbalanced estimate and IPSW estimate where estimable; state that "
          "NO same-estimand composition comparator is defined and the "
          "magnitude is NOT POINT-IDENTIFIED under differential attrition")
    print("  * balanced:* rows are descriptive two-season restrictions only; "
          "they change the time window and composition together and cannot "
          "identify either a direction or a composition effect")
    print("  * underpowered == 1 (fewer than %d treated clusters) -> report as "
          "underpowered, NEVER as a null result" % MIN_TREATED_CLUSTERS)
    print("  * an interval containing zero never supports a direction")
    print("  * phase:* rows are the 2026-09-13 robustness arm, exposure "
          "classified against each district's BASELINE markers; the frozen "
          "headline:* rows remain the headline")
    print("  * pretrend rows (§3.9): a lead coefficient distinguishable from "
          "zero invalidates parallel trends for that exposure class; the "
          "corresponding headline coefficient is then not causal")
    print("-" * 74)
    return 0


def _print_diag(r):
    if r.get("status") != "estimated":
        print(f"\n=== {r['stratum']}: NOT ESTIMABLE -- {r.get('reason','')}")
        return
    print(f"\n=== {r['stratum']}  "
          f"({r['n_exposed_pixel_years']:,} exposed pixel-years, "
          f"{r['n_treated_clusters']} treated clusters)")
    print(f"    coef {r['coef']:+.4f} (se {r['se']:.4f})  "
          f"p_cluster {r['p_cluster']:.4f}  p_WCB {r['p_wcb']:.4f}  "
          f"95% WCB CI [{r['wcb_ci_lo']:+.4f}, {r['wcb_ci_hi']:+.4f}]")
    if r.get("underpowered"):
        print(f"    UNDERPOWERED: {r['reason']}")


def _print_twfe(r):
    if r.get("status") != "estimated":
        print(f"    {r.get('stratum','?')}: not estimable -- {r.get('reason','')}")
        return
    line = (f"    {r['stratum']:<44s} beta {r['coef']:+8.3f} d  "
            f"(se {r['se']:.3f})  p_WCB {r['p_wcb']:.4f}  "
            f"CI [{r['wcb_ci_lo']:+.2f}, {r['wcb_ci_hi']:+.2f}]")
    print(line)
    if r.get("underpowered"):
        print("      UNDERPOWERED: fewer than %d treated clusters "
              "(MacKinnon & Webb 2018)" % MIN_TREATED_CLUSTERS)


if __name__ == "__main__":
    sys.exit(main())
