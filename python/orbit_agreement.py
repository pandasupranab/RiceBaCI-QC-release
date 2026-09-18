#!/usr/bin/env python3
"""H1 and H2 clause (a): do separate Sentinel-1 relative orbits agree?

WHAT THIS TESTS, and what it no longer can
------------------------------------------
§2's H1 is a conjunction: radar trough breakpoints fitted SEPARATELY to
relative-orbit series agree within a pre-declared tolerance, AND each pixel's
inter-seasonal dispersion is smaller than the between-pixel dispersion in its
district. H2 is the same pair for the radar fall-end breakpoint.

Clause (b) was run on 2026-09-13 (`python/dispersion_test.py`) and FAILS: ratio
1.340 for trough and 1.508 for fall-end, intervals nowhere near 1. A
conjunction cannot hold when one conjunct is false, so **H1 and H2 are already
not met and this script cannot change that.**

What this script measures is how far apart two relative orbits place the same
marker in the same pixel-season, and what the clause (b) dispersion looks like
when it is computed on a SINGLE orbit, so that the dispersion and the
between-orbit statistic describe one estimator rather than two.

WHAT IT DOES NOT DO, STATED FIRST BECAUSE IT USED TO CLAIM OTHERWISE
--------------------------------------------------------------------
It does NOT identify why clause (b) failed. Candidate explanations point opposite
ways -- a per-pixel marker may wander because it is measured badly, or a
smallholder field's underlying state may really move more year to year than fields differ
from each other -- and this study cannot tell them apart. Separating them would
require an error model: additive error independent of the true date, equal
variance on the two orbit paths, uncorrelated between them, independent across
seasons within a pixel, and transporting from the paired sample to the
single-orbit sample. Not one of those conditions is tested anywhere in this
study, and the between-orbit statistic is blind by construction to anything the
difference cancels, including a shared systematic bias.

An earlier version of this module subtracted an assumed error variance from the
dispersion and reported the remainder as though it settled the question. THAT
CALCULATION IS RETIRED. It is not computed here, not written to any table, and
not reported anywhere in the active result set. The dated record of it, of the
defects found in it, and of the decision to retire it, is kept in
analysis/deviation_log.md and analysis/decisions_log.md.

So the finding this module supports is exactly this much: H1 and H2 clause (b)
FAILED AS MEASURED, and the available evidence does not identify why.

WHAT IS REPORTED, ALL OF IT OBSERVED
------------------------------------
Between-orbit disagreement statistics (median absolute difference, shares within
one and two dekads, mean signed difference, correlation, sd of the difference and
sd(difference)/sqrt(2) reported as a scaled disagreement statistic rather than as
an error); the single-orbit within-pixel and between-pixel dispersion and their
observed ratio; and the sample sizes behind each. No quantity below is corrected,
decomposed, or described as true.

THE TOLERANCE IS FIXED ON 2017 AND NEVER RE-DERIVED
---------------------------------------------------
§2: "Tolerances are fixed on the untreated 2017 baseline season (§1.1) before any
treated season is fitted." So the tolerance T is the TOL_QUANTILE quantile of
|orbit difference| computed on 2017 alone, and clause (a) then asks whether
2018-2025 agree within that same T at least as often as the baseline did. Fixing
T on the pooled panel would make the test circular -- the tolerance would be
defined by the data it is judging. A physical reference is reported alongside but
is not the criterion: one dekad (10 d) is the grid spacing, and 10/sqrt(12) =
2.89 d is the quantisation floor below which no estimator on this grid can agree.

THE ORBIT PAIR IS CHOSEN BY A FIXED RULE, BEFORE ANY AGREEMENT IS COMPUTED
-------------------------------------------------------------------------
A pixel-season can carry two to four fittable orbits, and picking the pair that
agrees best would manufacture the result. The rule, applied blind:

  1. prefer a pair with one ASCENDING and one DESCENDING orbit -- different look
     direction and different incidence angle is the most geometrically distinct
     pairing available, and §4.1.8 records that Andhra Pradesh mostly lacks it;
  2. among candidate pairs, take the one whose two orbits have the most valid
     dekads (sum), breaking ties by the lower orbit number so the choice is
     deterministic;
  3. a pixel-season with fewer than two fittable orbits contributes nothing and
     is counted as not estimable, by district, so the denominator is visible.

REPORTED PER STATE, NEVER POOLED ALONE
--------------------------------------
§4.1.8 measured Andhra Pradesh as having an ascending/descending pair in 2 of 12
district-seasons against 18 of 20 in Odisha and 12 of 12 in West Bengal. Two
descending orbits still differ in incidence angle, date and speckle realisation,
so the agreement test is still a test there -- but they share look direction and
therefore any azimuthal asymmetry in the canopy response (row direction, lodging,
terrain aspect). Pooling would let well-paired Odisha and Bengal rows carry
weakly-paired Andhra rows. Every statistic here is reported by state and by pass
composition as well as pooled.

H2's OPTICAL CROSS-CHECK IS NOT RUN
----------------------------------
§2's H2 asks for "the post-monsoon Sentinel-2 EOS cross-check of §3.4 reported
alongside as a second, partly independent optical estimate". §3.4's 2026-09-09
amendment removed HLS as a substrate and the optical panel is unusable under
monsoon cloud; no Sentinel-2 EOS series exists for these district-seasons. The
cross-check is therefore withdrawn by dated amendment, not silently omitted, and
this script reports its absence in the output so the omission cannot be mistaken
for an oversight.

USAGE
-----
  python python/orbit_agreement.py --selftest
  python python/orbit_agreement.py --fit --exports <dir> [--limit N]   # resumable
  python python/orbit_agreement.py --agree
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fit_phenometrics as _FP
from extract_phenometrics_sar import (plsm_designs_pixel, plsm_fit, plsm_retain,
                                      GATE1_RATIO_RADAR, USE_SMOOTHING, N_BINS_,
                                      MIN_VALID_DEKADS)
from attrition_diagnostics import load_panel, SEED
GATE1_R = GATE1_RATIO_RADAR   # overridden by --gate1-r


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

EXPORTS = os.path.join(ROOT, "s1_perorbit")
OUT = os.path.join(RESULTS, "orbit_agreement")
EXPOSURE = _find_doc("district_cyclone_exposure_ibtracs50km.csv")
PANEL_PIXEL = os.path.join(RESULTS, "phen_panel_sar_static.csv")

BASELINE_SEASON = 2017          # §1.1's untreated baseline; the ONLY season the
                                # tolerance may be derived from
TOL_QUANTILE = 0.90             # T is this quantile of |diff| on the baseline
MARKERS = [("trough", "H1 clause (a): transplanting / onset"),
           ("harvest", "H2 clause (a): harvest"),
           ("heading", "supplementary: heading")]
DEKAD_D = 10.0                  # §1.4 grid spacing
QUANT_FLOOR = DEKAD_D / np.sqrt(12.0)   # 2.887 d, the quantisation floor
REQUIRED = ["district", "year", "cell_id", "orbit", "orbit_pass", "bin_index",
            "VHVV_med", "valid_obs_count"]


# ---------------------------------------------------------------------------
def read_per_orbit(path):
    """One per-orbit export CSV -> long frame, schema checked not guessed.

    The export drops bins with no observation (S1_PER_ORBIT.js design decision
    3), so the (pixel, orbit) series is reconstructed onto the full 55-bin grid
    with NaN elsewhere -- the same reconstruction read_export() does for the
    combined panel, and the reason dropping those rows was safe.
    """
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise SystemExit(
            f"{os.path.basename(path)}: columns {missing} absent.\n"
            "This is the signature of a missing `selectors` list in "
            "Export.table.toDrive -- Earth Engine infers the header from the "
            "leading features and an all-null leading block drops those columns "
            "from the whole file. Re-export; do not patch it here.")
    df["orbit"] = df["orbit"].astype(float).round().astype(int)
    b = df["bin_index"].astype(int)
    if b.min() < 0 or b.max() >= N_BINS_:
        raise SystemExit(f"{os.path.basename(path)}: bin_index outside "
                         f"0..{N_BINS_ - 1}")
    return df


def fit_one_file(path, designs):
    """Fit PLSM separately to every (pixel, orbit) series in one file.

    The pipeline is the COMMITTED one, unchanged: gate-1 bin admission,
    aggregate_to_dekads, whittaker_gcv, plsm_fit on the restricted pixel grid,
    plsm_retain. Admission is computed per (district, season, orbit), which is
    the per-orbit analogue of the combined path's per-district-season admission.
    Any divergence here would make the agreement statistic a comparison of two
    pipelines rather than of two orbits.
    """
    df = read_per_orbit(path)
    district = str(df["district"].iloc[0])
    year = int(df["year"].iloc[0])
    rows = []
    for orbit, s in df.groupby("orbit", sort=True):
        cells = s["cell_id"].drop_duplicates().to_numpy()
        idx = {c: i for i, c in enumerate(cells)}
        V = np.full((len(cells), N_BINS_), np.nan)
        C = np.zeros((len(cells), N_BINS_))
        r = s["cell_id"].map(idx).to_numpy()
        b = s["bin_index"].to_numpy(int)
        V[r, b] = pd.to_numeric(s["VHVV_med"], errors="coerce").to_numpy()
        C[r, b] = pd.to_numeric(s["valid_obs_count"],
                                errors="coerce").fillna(0.0).to_numpy()
        opass = str(s["orbit_pass"].iloc[0])[:4].upper()
        counts = np.nansum(np.where(np.isfinite(V), C, 0.0), axis=0)
        # GATE1_R is module-level so that the §3.1 justification test can run this
        # same code with the gate ON. It defaults to GATE1_RATIO_RADAR (0.0, the
        # measured radar default), so the committed path is unchanged.
        admitted = (_FP.gate1_admitted_bins(counts, GATE1_R)
                    if GATE1_R > 0 else np.ones(N_BINS_, dtype=bool))
        DV, DC = _FP.aggregate_to_dekads(V, C, admitted)
        for i in range(DV.shape[0]):
            valid = np.isfinite(DV[i])
            series = np.where(valid, DV[i], 0.0)
            if USE_SMOOTHING and valid.sum() >= 4:
                w = np.where(valid, np.maximum(DC[i], 1.0), 0.0)
                series, _, _ = _FP.whittaker_gcv(series, w)
            m = plsm_fit(series, valid, designs)
            ok, why = plsm_retain(m, min_rise_db=0.0, grid="pixel")
            rows.append(dict(
                district=district, year=year, cell_id=cells[i],
                orbit=int(orbit), orbit_pass=opass,
                n_valid=int(m["n_valid"]), retained=int(ok),
                fail_reason=("" if ok else why),
                **{k: m[k] for k in ("trough", "heading", "harvest",
                                     "rise_db", "rmse")}))
    return rows


def fit_run_key(exports):
    """Content identity; filenames alone cannot certify a reusable fit cache."""
    def sha(path, source=False):
        with open(path, "rb") as fh:
            data = fh.read()
        if source:
            data = data.replace(b"\r\n", b"\n")
        return hashlib.sha256(data).hexdigest()
    here = os.path.dirname(os.path.abspath(__file__))
    return dict(schema=1, gate1_r=GATE1_R, smoothing=USE_SMOOTHING,
                inputs={f: sha(os.path.join(exports, f)) for f in sorted(os.listdir(exports))
                        if f.endswith(".csv")},
                sources={f: sha(os.path.join(here, f), True) for f in
                         ("orbit_agreement.py", "extract_phenometrics_sar.py", "fit_phenometrics.py")})


def validate_fit_cache(key, receipt, store):
    if not isinstance(receipt, dict) or receipt.get("run_key") != key:
        raise ValueError("legacy/stale orbit fit cache; use a NEW empty output directory")
    done = receipt.get("done")
    if not isinstance(done, list) or len(set(done)) != len(done) or not set(done) <= set(key["inputs"]):
        raise ValueError("invalid completed-file roster in orbit cache")
    with open(store, "rb") as fh:
        observed = hashlib.sha256(fh.read()).hexdigest()
    if receipt.get("store_sha256") != observed:
        raise ValueError("orbit cache changed or append was interrupted; use a NEW empty output directory")
    return set(done)


def fit_all(exports, out_dir, limit=None):
    """Resume only a matching, intact cache; legacy or interrupted caches fail."""
    os.makedirs(out_dir, exist_ok=True)
    store = os.path.join(out_dir, "per_orbit_fits.csv")
    donef = os.path.join(out_dir, "fit_done.json")
    key = fit_run_key(exports)
    done = set()
    if os.path.exists(donef) or os.path.exists(store):
        if not (os.path.exists(donef) and os.path.exists(store)):
            raise SystemExit("incomplete orbit cache pair; use a NEW empty output directory")
        try:
            with open(donef, encoding="utf-8") as fh:
                done = validate_fit_cache(key, json.load(fh), store)
        except (ValueError, OSError) as exc:
            raise SystemExit(str(exc))
    files = sorted(f for f in os.listdir(exports) if f.endswith(".csv"))
    if not files:
        raise SystemExit("no per-orbit exports found; no completed output")
    todo = [f for f in files if f not in done]
    if limit:
        todo = todo[:limit]
    print(f"{len(files)} export files, {len(done)} already fitted, "
          f"{len(todo)} this run")
    designs = plsm_designs_pixel()
    for j, f in enumerate(todo, 1):
        rows = fit_one_file(os.path.join(exports, f), designs)
        pd.DataFrame(rows).to_csv(store, mode=("a" if os.path.exists(store)
                                               else "w"),
                                  header=not os.path.exists(store), index=False)
        done.add(f)
        with open(store, "rb") as fh:
            store_hash = hashlib.sha256(fh.read()).hexdigest()
        with open(donef + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(dict(run_key=key, done=sorted(done), store_sha256=store_hash), fh)
        os.replace(donef + ".tmp", donef)
        if j % 10 == 0 or j == len(todo):
            print(f"  {j}/{len(todo)}  ({f})", flush=True)
    print(f"wrote {store}")
    remaining = len(files) - len(done)
    if remaining:
        print(f"  INCOMPLETE: {remaining} files remain. Rerun to continue.")
    return 3 if remaining else 0


# ---------------------------------------------------------------------------
def choose_pair(g):
    """The declared pair-selection rule. Sees dekad counts and passes only.

    Deliberately blind to the markers: it never looks at trough, heading or
    harvest, so it cannot prefer the pair that happens to agree. Returns the two
    chosen rows, or None.
    """
    g = g[g["retained"] == 1]
    if len(g) < 2:
        return None
    g = g.sort_values(["n_valid", "orbit"], ascending=[False, True])
    asc = g[g["orbit_pass"].str.startswith("ASC")]
    desc = g[g["orbit_pass"].str.startswith("DESC")]
    if len(asc) and len(desc):
        # rule 1: the most geometrically distinct pairing, best dekad sum within it
        best, score = None, -1
        for _, a in asc.iterrows():
            for _, d in desc.iterrows():
                s = a["n_valid"] + d["n_valid"]
                if s > score:
                    best, score = (a, d), s
        return best
    # rule 2: same-pass fallback, most dekads
    return g.iloc[0], g.iloc[1]


def build_pairs(fits):
    """One row per pixel-season: the chosen pair and its marker differences."""
    out, not_est = [], []
    for (dist, yr, cell), g in fits.groupby(["district", "year", "cell_id"],
                                            sort=False):
        p = choose_pair(g)
        if p is None:
            not_est.append(dict(district=dist, year=yr, cell_id=cell,
                                n_retained_orbits=int((g["retained"] == 1).sum())))
            continue
        a, b = p
        row = dict(district=dist, year=yr, cell_id=cell,
                   orbit_a=int(a["orbit"]), orbit_b=int(b["orbit"]),
                   pass_a=a["orbit_pass"], pass_b=b["orbit_pass"],
                   n_valid_a=int(a["n_valid"]), n_valid_b=int(b["n_valid"]),
                   asc_desc=int(a["orbit_pass"][:3] != b["orbit_pass"][:3]))
        for mk, _ in MARKERS:
            row[f"{mk}_a"] = a[mk]
            row[f"{mk}_b"] = b[mk]
            row[f"d_{mk}"] = (b[mk] - a[mk]) if (pd.notna(a[mk])
                                                 and pd.notna(b[mk])) else np.nan
        out.append(row)
    return pd.DataFrame(out), pd.DataFrame(not_est)


def tolerance_from_baseline(pairs, mk):
    """T, from the untreated baseline season ONLY. Never re-derived."""
    base = pairs[pairs["year"] == BASELINE_SEASON][f"d_{mk}"].dropna().abs()
    if len(base) < 30:
        return None, len(base)
    return float(np.quantile(base, TOL_QUANTILE)), len(base)


def agree_stats(dif):
    """Agreement summary and a scaled between-orbit disagreement statistic.

    The legacy column name ``sigma_single`` is retained for table compatibility,
    but its value is only sd(difference)/sqrt(2). It equals either orbit's error
    standard deviation only under equal error variances and zero error covariance.
    Those conditions are not tested; different orbit geometry does not establish
    statistical independence, and shared bias cancels from the difference.
    """
    dif = pd.Series(dif).dropna()
    if not len(dif):
        return None
    return dict(n=int(len(dif)), mean_diff=float(dif.mean()),
                sd_diff=float(dif.std(ddof=1)),
                sigma_single=float(dif.std(ddof=1) / np.sqrt(2.0)),
                median_abs=float(dif.abs().median()),
                corr=np.nan)


def report(pairs, not_est, out_dir, states):
    rows = []
    print("\n" + "=" * 78)
    print("H1 / H2 CLAUSE (a) -- between-orbit agreement")
    print("=" * 78)
    print(f"  pixel-seasons with a usable orbit pair: {len(pairs)}")
    print(f"  pixel-seasons with fewer than two fittable orbits: {len(not_est)}")
    if len(not_est):
        z = (not_est.groupby("district").size().sort_values(ascending=False))
        print("  not estimable, by district (top 8):")
        for d, n in z.head(8).items():
            print(f"      {d:<22s} {n}")
    print(f"  ascending/descending pairs: "
          f"{int(pairs['asc_desc'].sum())} of {len(pairs)} "
          f"({pairs['asc_desc'].mean():.1%})")
    # TWO SENSES OF "USABLE", and conflating them overstates the sample.
    # The inventory's "fittable" means an orbit has >= MIN_VALID_DEKADS dekads,
    # i.e. a fit may be ATTEMPTED. "retained" means the fit passed §3's screens.
    # Clause (a) needs the second, on BOTH orbits, so the rates compound: at
    # ~36% per-orbit retention an independent pair would give ~13%. The observed
    # rate is higher than that, which says retention is positively correlated
    # across orbits -- the screen is responding to pixel quality, not only to
    # noise -- and it is reported because the paired sample is what clause (a)
    # actually rests on, not the fittable-orbit count.
    tot = len(pairs) + len(not_est)
    if tot:
        print(f"  paired rate: {len(pairs)}/{tot} = {len(pairs) / tot:.1%} of "
              f"pixel-seasons offered")
        print(f"    (an orbit is 'fittable' when it has >= {MIN_VALID_DEKADS} "
              f"dekads; it is 'retained' when the fit passes §3's screens.")
        print(f"     Clause (a) needs BOTH orbits retained, so per-orbit "
              f"retention compounds. Do not")
        print(f"     read the inventory's fittable-orbit counts as this "
              f"denominator.)")

    for mk, label in MARKERS:
        T, n_base = tolerance_from_baseline(pairs, mk)
        print(f"\n--- {label} ---")
        if T is None:
            print(f"  tolerance NOT derivable: only {n_base} baseline "
                  f"({BASELINE_SEASON}) pairs, need 30. Clause (a) is not "
                  f"testable for this marker without a baseline tolerance, and "
                  f"deriving T on the pooled panel would make the test circular.")
            rows.append(dict(marker=mk, scope="ALL", status="no_baseline",
                             n_baseline=n_base))
            continue
        print(f"  baseline tolerance T = {T:.2f} d   ({TOL_QUANTILE:.0%} "
              f"quantile of |diff| on {BASELINE_SEASON}, n={n_base}; fixed "
              f"there, never re-derived)")
        print(f"  reference: one dekad = {DEKAD_D:.0f} d; quantisation floor "
              f"{QUANT_FLOOR:.2f} d")
        if T > 3 * DEKAD_D:
            print(f"  *** READ T BEFORE READING ANY VERDICT BELOW. T = "
                  f"{T:.0f} d is {T / DEKAD_D:.0f} dekads, a large fraction of "
                  f"the season itself.")
            print(f"      A tolerance that wide is not an agreement criterion. "
                  f"Because T is the {TOL_QUANTILE:.0%}")
            print(f"      quantile of the baseline's own disagreement, "
                  f"'{TOL_QUANTILE:.0%} within T' is close to")
            print(f"      true by construction, and the column below tests only "
                  f"whether later seasons")
            print(f"      are NO WORSE than the untreated baseline -- a "
                  f"STABILITY check, not agreement.")
            print(f"      The diagnostics are scaled disagreement (legacy "
                  f"column sigma_single), r, and the absolute-tolerance")
            print(f"      columns. §2's wording does fix the tolerance on 2017, "
                  f"and this is what that")
            print(f"      instruction yields on this estimator; it is reported "
                  f"rather than replaced.")
        later = pairs[pairs["year"] != BASELINE_SEASON]
        for scope, sub in ([("ALL", later)]
                           + [(st, later[later["district"].map(states) == st])
                              for st in sorted(set(states.values()))]
                           + [("ASC/DESC pairs only",
                               later[later["asc_desc"] == 1]),
                              ("same-pass pairs only",
                               later[later["asc_desc"] == 0])]):
            s = agree_stats(sub[f"d_{mk}"])
            if s is None:
                print(f"    {scope:<22s} no paired estimates")
                continue
            d = sub[f"d_{mk}"].dropna().abs()
            frac = float((d <= T).mean())
            met = frac >= TOL_QUANTILE
            # ABSOLUTE tolerances, which do not adapt to how poor the estimator
            # is: one dekad is the grid spacing and the finest agreement this
            # grid can express, two dekads a generous alternative. These are the
            # columns to read when T is wide.
            f1 = float((d <= DEKAD_D).mean())
            f2 = float((d <= 2 * DEKAD_D).mean())
            s["corr"] = float(sub[f"{mk}_a"].corr(sub[f"{mk}_b"]))
            print(f"    {scope:<22s} n={s['n']:6d}  "
                  f"within T {frac:5.1%} {'(stable)' if met else '(worse)':<9s}"
                  f"|  <=1 dekad {f1:5.1%}  <=2 dekads {f2:5.1%}  |  "
                  f"scaled disagreement {s['sigma_single']:6.2f} d  "
                  f"mean signed difference {s['mean_diff']:+6.2f} d  "
                  f"r {s['corr']:+.3f}")
            rows.append(dict(marker=mk, scope=scope, tolerance_d=T,
                             frac_within_T=frac, criterion=TOL_QUANTILE,
                             stable_vs_baseline=int(met),
                             frac_within_1_dekad=f1, frac_within_2_dekads=f2,
                             status="estimated", **s))
    dest = os.path.join(out_dir, "Table_SX_OrbitAgreement.csv")
    pd.DataFrame(rows).to_csv(dest, index=False)
    print(f"\nwrote {dest}")
    return pd.DataFrame(rows)


def single_orbit_dispersion(fits, agr, out_dir):
    """Clause (b) dispersion recomputed on a SINGLE orbit. OBSERVED ONLY.

    WHY A SINGLE ORBIT. `dispersion_test.py` measures dispersion on the
    COMMITTED panel, whose marker is fitted to all orbits composited together,
    while the between-orbit statistic here is measured between two SINGLE-orbit
    fits. Those are two different estimators, so the two numbers are not
    commensurable and nothing may be computed from their difference. Recomputing
    the dispersion on one orbit removes that mismatch by construction:

        for each pixel, take the orbit with the most retained seasons
        (>= MIN_SEASONS_DISP of them), form r = Y - season mean within that
        sample, then within = pooled sd of r about each pixel's own mean and
        between = sd of the pixel means.

    WHAT THIS FUNCTION NO LONGER DOES. It used to subtract an assumed error
    variance from both dispersions and report a derived ratio, and its output
    and CSV asserted a cause for the clause (b) failure. All of that is RETIRED
    as an active analysis: the subtraction rested on
    assumptions this study never tested, its between-pixel term used the wrong
    factor for unbalanced season counts, and the residuals are district-year
    centred before the pixel means are formed, which the subtraction ignored.
    Nothing here is corrected, decomposed, or labelled true. The dated history
    is in analysis/deviation_log.md and analysis/decisions_log.md; the columns
    the table used to carry are described in
    results/orbit_agreement/README_DispersionSingleOrbit.md.

    The single-orbit sample is also NOT the paired sample: it takes each pixel's
    best-covered orbit, where the between-orbit statistic requires two orbits to
    have fitted the same pixel-season. The two are reported side by side and
    neither is transported onto the other.
    """
    MIN_SEASONS_DISP = 2
    print("\n" + "=" * 78)
    print("CLAUSE (b) DISPERSION RECOMPUTED ON A SINGLE ORBIT -- OBSERVED ONLY")
    print("no error subtraction and no derived columns")
    print("=" * 78)
    r = fits[fits["retained"] == 1].copy()
    # per pixel, the orbit with the most retained seasons; ties by lower orbit
    cnt = (r.groupby(["district", "cell_id", "orbit"]).size()
             .rename("n_seasons").reset_index()
             .sort_values(["district", "cell_id", "n_seasons", "orbit"],
                          ascending=[True, True, False, True]))
    pick = cnt.groupby(["district", "cell_id"], as_index=False).first()
    pick = pick[pick["n_seasons"] >= MIN_SEASONS_DISP]
    keep = r.merge(pick[["district", "cell_id", "orbit"]],
                   on=["district", "cell_id", "orbit"], how="inner")
    print(f"  pixels with >= {MIN_SEASONS_DISP} retained seasons on one orbit: "
          f"{len(pick)}   pixel-seasons used: {len(keep)}")
    n_seas = float(keep.groupby(["district", "cell_id"]).size().mean())
    print(f"  mean retained seasons per pixel on its chosen orbit: {n_seas:.2f}")
    out = []
    for mk, label in MARKERS:
        d = keep.dropna(subset=[mk]).copy()
        if d.empty:
            continue
        d["_r"] = d[mk] - d.groupby(["district", "year"])[mk].transform("mean")
        pid = d["district"] + "|" + d["cell_id"].astype(str)
        d["_pid"] = pid
        m = d.groupby("_pid")["_r"].transform("mean")
        dof = len(d) - d["_pid"].nunique()
        if dof <= 0:
            continue
        within = float(np.sqrt((((d["_r"] - m) ** 2).sum()) / dof))
        between = float(d.groupby("_pid")["_r"].mean().std(ddof=1))
        a = agr[(agr.marker == mk) & (agr.scope == "ALL")
                & (agr.status == "estimated")]
        sig = float(a.iloc[0]["sigma_single"]) if not a.empty else float("nan")
        obs = within / between if between > 0 else np.nan
        print(f"  {label}")
        print(f"    single-orbit within {within:6.2f} d   between {between:6.2f} d"
              f"   observed ratio {obs:.3f}")
        # sigma_single is carried alongside as the BETWEEN-ORBIT scaled
        # disagreement statistic, on the paired sample. It is reported, never
        # subtracted from anything above: the two samples differ, the estimators
        # differ, and no error model licensing such a subtraction has been
        # tested. See this function's docstring.
        print(f"    between-orbit sd(difference)/sqrt(2) on the paired sample: "
              f"{sig:6.2f} d -- reported alongside, not subtracted")
        out.append(dict(marker=mk, sigma_single=sig, n_seasons_mean=n_seas,
                        within_obs=within, between_obs=between, ratio_obs=obs,
                        n_pixels=int(d["_pid"].nunique()), n_obs=int(len(d))))
    if out:
        dest = os.path.join(out_dir, "Table_SX_DispersionSingleOrbit.csv")
        pd.DataFrame(out).to_csv(dest, index=False)
        print(f"  wrote {dest}")
    print("\n  READ THIS TABLE AS OBSERVED QUANTITIES ONLY.")
    print("  The committed panel's own clause (b) figures stay as reported in")
    print("  results/dispersion/ -- they are the claim as \u00a72 words it, on the")
    print("  committed estimator. The table above is the same comparison made on")
    print("  a single orbit, so that the dispersion and the between-orbit")
    print("  statistic describe one estimator. Neither replaces the other and")
    print("  both are reported.")
    print("\n  H1 and H2 clause (b) FAILED AS MEASURED. The evidence available")
    print("  here does NOT identify why: separating a noisy estimator from real")
    print("  crop variation would need an error model that this study has not")
    print("  tested, and the between-orbit statistic is blind to anything the")
    print("  difference cancels, a shared systematic bias included.")


def note_withdrawals():
    print("\n" + "-" * 78)
    print("NOT RUN, and withdrawn by dated amendment rather than omitted:")
    print("  H2's post-monsoon Sentinel-2 EOS cross-check (§2 H2, §3.4). §3.4's")
    print("  2026-09-09 amendment removed HLS as a substrate and the optical")
    print("  panel is unusable under monsoon cloud, so no Sentinel-2 EOS series")
    print("  exists for these district-seasons. H2 clause (a) is therefore")
    print("  reported on the radar orbit pair alone, with no optical second")
    print("  opinion. See analysis/deviation_log.md.")
    print("-" * 78)


# ---------------------------------------------------------------------------
def selftest():
    ok_all = True
    rng = np.random.default_rng(5)

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        store = os.path.join(td, "fits.csv")
        with open(store, "wb") as fh:
            fh.write(b"synthetic cache\n")
        k = dict(schema=1, inputs={"export.csv": "hash"}, sources={"fit": "source"}, gate1_r=0)
        receipt = dict(run_key=k, done=["export.csv"],
                       store_sha256=hashlib.sha256(b"synthetic cache\n").hexdigest())
        assert validate_fit_cache(k, receipt, store) == {"export.csv"}
        for wrong in (["export.csv"], dict(receipt, run_key=dict(k, gate1_r=.5)),
                      dict(receipt, store_sha256="changed"),
                      dict(receipt, done=["export.csv", "export.csv"])):
            try:
                validate_fit_cache(k, wrong, store)
            except ValueError:
                continue
            raise AssertionError("invalid orbit cache accepted")
    print("  [PASS] matching orbit cache accepted; legacy, option drift, output drift and duplicates refused")

    # 1. the pair rule prefers ASC/DESC, and is blind to the markers
    g = pd.DataFrame([
        dict(orbit=12, orbit_pass="ASCE", n_valid=20, retained=1,
             trough=200.0, heading=300.0, harvest=380.0),
        dict(orbit=48, orbit_pass="DESC", n_valid=18, retained=1,
             trough=260.0, heading=340.0, harvest=420.0),
        dict(orbit=85, orbit_pass="ASCE", n_valid=25, retained=1,
             trough=201.0, heading=301.0, harvest=381.0)])
    a, b = choose_pair(g)
    got = {int(a["orbit"]), int(b["orbit"])}
    ok = got == {85, 48}
    ok_all &= ok
    print(f"  pair chosen {sorted(got)}; ASC/DESC required, best dekad sum "
          f"within it -> [{'PASS' if ok else 'FAIL'}]")
    print(f"  (it did NOT pick 12+85, the two that agree to 1 d, because the "
          f"rule never sees the markers)")

    # 2. same-pass fallback when only one direction exists
    g2 = g[g.orbit_pass == "ASCE"]
    a, b = choose_pair(g2)
    ok = {int(a["orbit"]), int(b["orbit"])} == {12, 85}
    ok_all &= ok
    print(f"  one pass direction only -> falls back to the two best: "
          f"[{'PASS' if ok else 'FAIL'}]")

    # 3. fewer than two retained orbits is not estimable
    ok = choose_pair(g.assign(retained=[1, 0, 0])) is None
    ok_all &= ok
    print(f"  one retained orbit -> not estimable: [{'PASS' if ok else 'FAIL'}]")

    # 4. sigma_single recovers a planted INDEPENDENT-NOISE SCALE under this
    #    self-test's own model: errors equal in variance on the two paths and
    #    uncorrelated between them. That is what makes sd(difference)/sqrt(2)
    #    equal each path's scale HERE. It is a property of the planted model,
    #    not evidence that the real orbit pair satisfies it -- section 1.5.6
    #    constraint 2 declines to assume that.
    true_sig = 12.0
    dif = rng.normal(0, true_sig * np.sqrt(2.0), 4000)
    s = agree_stats(dif)
    ok = abs(s["sigma_single"] - true_sig) < 0.6
    ok_all &= ok
    print(f"  planted independent-noise scale {true_sig:.1f} d -> recovered "
          f"{s['sigma_single']:.2f} d: [{'PASS' if ok else 'FAIL'}]")

    # 5. the tolerance comes from the baseline season and nowhere else
    pr = pd.DataFrame(dict(
        year=([BASELINE_SEASON] * 500 + [2024] * 500),
        d_trough=np.concatenate([rng.normal(0, 5, 500),
                                 rng.normal(0, 50, 500)])))
    T, n = tolerance_from_baseline(pr, "trough")
    T_pooled = float(np.quantile(pr["d_trough"].abs(), TOL_QUANTILE))
    ok = n == 500 and T < 0.5 * T_pooled
    ok_all &= ok
    print(f"  baseline n={n}, T={T:.2f} d; pooled would give {T_pooled:.2f} d "
          f"-> [{'PASS' if ok else 'FAIL'}]")
    print(f"  (a wide 2024 cannot loosen the tolerance it is judged against)")
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="H1/H2 clause (a).")
    ap.add_argument("--exports", default=EXPORTS)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--fit", action="store_true",
                    help="fit PLSM per (pixel, season, orbit). Resumable.")
    ap.add_argument("--limit", type=int, default=None,
                    help="fit at most this many new files, then save")
    ap.add_argument("--agree", action="store_true",
                    help="pair, test the tolerance, report by state")
    ap.add_argument("--gate1-r", type=float, default=None,
                    help="§3.1 density ratio to apply to the per-orbit series. "
                         "Omit for the radar default of 0.0 (gate off, measured "
                         "rather than assumed). Set 0.50 to run the §3.1 "
                         "justification test's orbit-agreement criterion with the "
                         "gate ON.")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.gate1_r is not None:
        global GATE1_R
        GATE1_R = float(a.gate1_r)
        print(f'§3.1 gate on the per-orbit series: r = {GATE1_R}')

    if a.selftest:
        return selftest()
    if a.fit:
        return fit_all(a.exports, a.out, a.limit)
    if a.agree:
        store = os.path.join(a.out, "per_orbit_fits.csv")
        if not os.path.exists(store):
            raise SystemExit(f"{store} absent; run --fit first")
        fits = pd.read_csv(store)
        pairs, not_est = build_pairs(fits)
        os.makedirs(a.out, exist_ok=True)
        pairs.to_csv(os.path.join(a.out, "orbit_pairs.csv"), index=False)
        expo = pd.read_csv(EXPOSURE)
        states = (expo[["district_gadm_name", "state"]].drop_duplicates()
                  .set_index("district_gadm_name")["state"].to_dict())
        agr = report(pairs, not_est, a.out, states)
        single_orbit_dispersion(fits, agr, a.out)
        note_withdrawals()
        return 0
    ap.error("one of --fit, --agree or --selftest is required")


if __name__ == "__main__":
    sys.exit(main())
