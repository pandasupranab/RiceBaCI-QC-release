"""
semivariance.py -- §3.1 / §3.4 Tier 1 spatial coherence.

WHAT §3.4 ASKS FOR, verbatim: "**Spatial coherence.** Within-district dispersion and
the semivariance between neighbouring cohort pixels -- fields close together are
planted at similar times."

WHY IT IS LOAD-BEARING. §3.3 gave up the original SAR falsification of the
phenometrics -- a SAR-derived check on SAR-derived dates compares a measurement
against itself -- and says so: "Verification of the phenometrics now rests on the
internal-consistency measures of §3.4 Tier 1 -- orbit repeatability, inter-seasonal
stability, **spatial coherence** and fit quality -- rather than on a second
instrument." Three of those four were built. This is the fourth, and an external
re-audit on 2026-09-13 found it missing.

WHAT A SEMIVARIOGRAM MEASURES HERE. For pairs of cohort pixels separated by distance
h within one district-season,

    gamma(h) = 1/2 * mean[ (z_i - z_j)^2 ]

Under additive, spatially uncorrelated measurement error of variance sigma^2 on top
of a spatially structured true field,

    gamma(h) = sigma^2 + structured(h)

so the limit as h -> 0 would estimate sigma^2, and the plateau (the **sill**)
would estimate sigma^2 plus the total spatial variance of the field.

WHAT THIS SCRIPT ACTUALLY COMPUTES (stated plainly 2026-09-14, fifth pass, after an
external audit). `nugget_and_sill()` does NOT fit a model and does NOT extrapolate an
intercept at h = 0. It takes the SHORTEST INTERPRETABLE DISTANCE BIN -- the first lag
with at least MIN_PAIRS_PER_LAG pairs, here a bin whose lower edge is above zero. So
the reported "nugget" is a short-lag semivariance, not a fitted zero-distance
intercept, and it is a descriptive MIXTURE of local spatial variation in the true
field and the spatially UNCORRELATED part of the error. Read every use of the word
"nugget" below in that sense.

That makes this test do two things at once:

  1. It answers §3.4's question. If fields close together really are planted at
     similar times, gamma rises with h. If gamma is flat from the shortest lag, the
     pixel-level estimate carries no recoverable spatial signal.
  2. It produces a number that can be COMPARED with orbit_agreement.py's, and
     nothing stronger than compared. That script differences two orbits at the
     same pixel; this one differences two pixels at the same time. The arithmetic
     differs, but THEY ARE NOT THE SAME ESTIMAND: a short-lag spatial
     semivariance mixes local variation in the true field with the spatially
     uncorrelated part of the error, while a between-orbit difference cancels
     whatever the two paths share. There is no reason in principle for the two
     to be equal, and their numerical similarity in this dataset is a
     description of this dataset.

     SO NEITHER VALIDATES THE OTHER. Both read the SAME Sentinel-1 panel through
     the SAME breakpoint estimator, so neither is independent of a defect in the
     other. This module reports that the two values are similar here. It does not
     say the error magnitude is corroborated, confirmed, independently
     established, or validated, and no wording in this repository may say so.

WHAT THE SHORT-LAG VALUE BOUNDS, AND WHAT IT DOES NOT (corrected 2026-09-14, fifth
pass). Under an additive model with signal-independent error, the short-lag
semivariance is an upper bound on the SPATIALLY UNCORRELATED ERROR COMPONENT at the
population level, because genuine local variation in the true field sits inside it.
That is a statement about one component, not about total measurement error:

  * error shared between neighbouring pixels -- orbit geometry, incidence angle,
    local terrain, a district-season atmospheric or phenological common mode -- very
    largely CANCELS from the pixel difference and is therefore MISSING from this
    statistic, not contained in it;
  * a common constant bias cancels completely and is invisible;
  * a finite-sample estimate from a finite number of pairs is not a guaranteed
    numerical bound in any case.

Worked counterexample, checked by simulation on 2026-09-14: let the true field be
constant, let every pixel carry a district-season shared error of sd 25 d plus an
independent error of sd 5 d. The short-lag semivariance root is 5.0 d while each
pixel's TOTAL error sd is sqrt(25^2 + 5^2) = 25.50 d -- the statistic is five times
SMALLER than total error. So "upper bound on measurement error", unqualified, is
false and is withdrawn wherever it appears.

Created 2026-09-13.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.environ.get("RICEBACI_ROOT", "/home/claude")
RESULTS = os.environ.get("RICEBACI_RESULTS", os.path.join(ROOT, "results"))
OUT = os.path.join(RESULTS, "semivariance")

MARKERS = ["trough", "heading", "harvest"]
# Lag edges in km. Fine where the structure would be, coarse where pairs are many.
# The first edge is below the median nearest-neighbour separation (0.9 km) so the
# shortest bin is genuinely "neighbouring pixels" and not a district-scale average.
LAG_EDGES_KM = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 999.0]
MIN_PAIRS_PER_LAG = 200          # below this a lag is reported but not interpreted
EARTH_R_KM = 6371.0


def _find(name):
    here = os.path.dirname(os.path.abspath(__file__))
    for c in (name, os.path.join(here, name), os.path.join(here, "..", "docs", name),
              os.path.join(ROOT, "docs", name), os.path.join(ROOT, name),
              os.path.join(ROOT, "cohort_v2", "docs", name)):
        if os.path.exists(c):
            return c
    raise SystemExit(f"cannot find {name!r}")


def haversine_matrix(lat_deg, lon_deg):
    """Great-circle distance in km between every pair of points.

    Haversine rather than a flat-earth approximation: districts here span up to
    139 km and a planar approximation in degrees would stretch longitude by about
    6% at 20 N, which would bias the lag assignment systematically outward."""
    lat = np.radians(np.asarray(lat_deg, float))
    lon = np.radians(np.asarray(lon_deg, float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = (np.sin(dlat / 2.0) ** 2
         + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2.0) ** 2)
    return 2.0 * EARTH_R_KM * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def semivariogram_cell(lat, lon, z, edges=LAG_EDGES_KM):
    """Per-lag sum of squared differences and pair count for one district-season.

    Returns (sums, counts) rather than gamma, so that pooling across
    district-seasons is a sum of squares over a sum of counts -- the correct
    weighting. Averaging per-cell gammas would weight a cell with 12 pairs equally
    with one carrying 70,000."""
    z = np.asarray(z, float)
    ok = np.isfinite(z)
    if ok.sum() < 2:
        return np.zeros(len(edges) - 1), np.zeros(len(edges) - 1, dtype=np.int64)
    lat = np.asarray(lat, float)[ok]
    lon = np.asarray(lon, float)[ok]
    z = z[ok]
    D = haversine_matrix(lat, lon)
    iu = np.triu_indices(len(z), 1)
    h = D[iu]
    dz2 = (z[iu[0]] - z[iu[1]]) ** 2
    idx = np.digitize(h, edges[1:-1], right=False)
    sums = np.bincount(idx, weights=dz2, minlength=len(edges) - 1)
    cnts = np.bincount(idx, minlength=len(edges) - 1).astype(np.int64)
    return sums[:len(edges) - 1], cnts[:len(edges) - 1]


def pool(panel, cohort, marker, edges=LAG_EDGES_KM, by_district=False):
    """Pooled semivariogram over every district-season of one marker."""
    xy = cohort.set_index("cell_id")[["lat", "lon"]]
    p = panel.merge(xy, left_on="cell_id", right_index=True, how="inner")
    nlag = len(edges) - 1
    groups = {}
    for (dist, yr), g in p.groupby(["district", "year"], sort=True):
        s, c = semivariogram_cell(g["lat"].values, g["lon"].values,
                                  g[marker].values, edges)
        key = dist if by_district else "ALL"
        if key not in groups:
            groups[key] = [np.zeros(nlag), np.zeros(nlag, dtype=np.int64), 0]
        groups[key][0] += s
        groups[key][1] += c
        groups[key][2] += 1
    rows = []
    for key, (s, c, ncells) in groups.items():
        for k in range(nlag):
            rows.append(dict(
                group=key, marker=marker,
                lag_lo_km=edges[k], lag_hi_km=edges[k + 1],
                n_pairs=int(c[k]), n_district_seasons=ncells,
                gamma_d2=(0.5 * s[k] / c[k]) if c[k] else np.nan,
                interpretable=bool(c[k] >= MIN_PAIRS_PER_LAG)))
    t = pd.DataFrame(rows)
    t["rms_d"] = np.sqrt(t["gamma_d2"])
    return t


def nugget_and_sill(t):
    """Nugget from the shortest interpretable lag, sill from the longest."""
    u = t[t["interpretable"]].sort_values("lag_lo_km")
    if u.empty:
        return None
    n, s = u.iloc[0], u.iloc[-1]
    out = dict(
        nugget_lag_km=f"{n.lag_lo_km:g}-{n.lag_hi_km:g}",
        nugget_gamma_d2=float(n.gamma_d2), nugget_rms_d=float(np.sqrt(n.gamma_d2)),
        nugget_pairs=int(n.n_pairs),
        sill_lag_km=f"{s.lag_lo_km:g}-{s.lag_hi_km:g}",
        sill_gamma_d2=float(s.gamma_d2), sill_rms_d=float(np.sqrt(s.gamma_d2)),
        sill_pairs=int(s.n_pairs))
    out["nugget_over_sill"] = (out["nugget_gamma_d2"] / out["sill_gamma_d2"]
                               if out["sill_gamma_d2"] else np.nan)
    # structured variance is what is left once the nugget is removed
    out["structured_d2"] = out["sill_gamma_d2"] - out["nugget_gamma_d2"]
    out["structured_rms_d"] = (np.sqrt(out["structured_d2"])
                               if out["structured_d2"] > 0 else np.nan)
    return out


# ---------------------------------------------------------------------------
def selftest():
    """Plant fields with known structure and check the estimator recovers it."""
    print("=" * 74)
    print("SELF-TEST -- semivariance.py")
    print("=" * 74)
    ok = True

    def check(name, passed, detail=""):
        nonlocal ok
        ok = ok and bool(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))

    rng = np.random.default_rng(20260913)

    # --- haversine against a known great-circle distance --------------------
    d = haversine_matrix([0.0, 0.0], [0.0, 1.0])[0, 1]
    check("haversine: 1 degree of longitude at the equator is ~111.19 km",
          abs(d - 111.19) < 0.2, f"{d:.2f} km")
    d = haversine_matrix([20.0, 20.0], [0.0, 1.0])[0, 1]
    check("haversine shrinks longitude with latitude (20 N -> ~104.5 km)",
          abs(d - 104.5) < 0.5,
          f"{d:.2f} km; a planar degree approximation would have said 111 and "
          f"biased every lag outward")

    # --- PURE NOISE: gamma must be flat at sigma^2 --------------------------
    n = 400
    lat = 20.0 + rng.uniform(-0.5, 0.5, n)
    lon = 86.0 + rng.uniform(-0.5, 0.5, n)
    sigma = 26.0
    z = rng.normal(0.0, sigma, n)
    coh = pd.DataFrame(dict(cell_id=[f"c{i}" for i in range(n)], lat=lat, lon=lon))
    pan = pd.DataFrame(dict(cell_id=coh.cell_id, district="D", year=2017, m=z))
    t = pool(pan, coh, "m")
    st = nugget_and_sill(t)
    check("pure noise: nugget recovers sigma^2",
          abs(st["nugget_rms_d"] - sigma) < 4.0,
          f"nugget rms {st['nugget_rms_d']:.1f} d against planted {sigma:.0f} d")
    check("pure noise: nugget/sill ~ 1, i.e. NO spatial structure claimed",
          abs(st["nugget_over_sill"] - 1.0) < 0.25,
          f"{st['nugget_over_sill']:.3f}; a flat variogram must not be read as "
          f"coherence")

    # --- STRUCTURED FIELD: gamma must rise with h ---------------------------
    # a smooth north-south gradient plus small noise
    z2 = 40.0 * (lat - lat.mean()) / (lat.max() - lat.mean()) + rng.normal(0, 3, n)
    pan2 = pan.assign(m=z2)
    t2 = pool(pan2, coh, "m")
    st2 = nugget_and_sill(t2)
    check("structured field: nugget is far below the sill",
          st2["nugget_over_sill"] < 0.3,
          f"{st2['nugget_over_sill']:.3f}")
    u = t2[t2.interpretable].sort_values("lag_lo_km")
    rising = bool(np.all(np.diff(u.gamma_d2.values) > -1e-9))
    check("structured field: gamma rises monotonically with separation", rising)
    check("structured field: the estimator does NOT invent structure in the noise "
          "case and DOES find it here",
          st["nugget_over_sill"] > 3 * st2["nugget_over_sill"],
          f"{st['nugget_over_sill']:.3f} vs {st2['nugget_over_sill']:.3f}")

    # --- pooling must be pair-weighted, not cell-averaged -------------------
    big = pd.DataFrame(dict(cell_id=coh.cell_id, district="D", year=2018, m=z))
    small = pd.DataFrame(dict(cell_id=coh.cell_id[:3], district="D", year=2019,
                              m=[0.0, 1000.0, -1000.0]))
    tp = pool(pd.concat([big, small], ignore_index=True), coh, "m")
    sill_pooled = tp[tp.interpretable].sort_values("lag_lo_km").iloc[-1].gamma_d2
    sill_big = t[t.interpretable].sort_values("lag_lo_km").iloc[-1].gamma_d2
    check("a 3-pixel outlier cell cannot dominate a 400-pixel one",
          abs(sill_pooled - sill_big) / sill_big < 0.25,
          f"pooled {sill_pooled:.0f} vs large-cell-only {sill_big:.0f} d^2; "
          f"averaging per-cell gammas instead would have let it")

    # --- a lag with too few pairs must be flagged, not silently used --------
    tiny = pd.DataFrame(dict(cell_id=coh.cell_id[:4], district="D", year=2017,
                             m=[1.0, 2.0, 3.0, 4.0]))
    tt = pool(tiny, coh, "m")
    check("a lag below the pair floor is marked not interpretable",
          not tt[tt.n_pairs > 0].interpretable.any(),
          f"max pairs in any lag {int(tt.n_pairs.max())} < {MIN_PAIRS_PER_LAG}")

    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok else "FAILED"))
    print("=" * 74)
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="§3.4 Tier 1 spatial coherence.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--panel", default=os.path.join(RESULTS, "phen_panel_sar.csv"))
    ap.add_argument("--by-district", action="store_true")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    if not os.path.exists(a.panel):
        raise SystemExit(f"panel not found: {a.panel}")
    coh = pd.read_csv(_find("candidate_cohort_v2.csv"))
    pan = pd.read_csv(a.panel, dtype={"cell_id": str},
                      usecols=lambda c: c in (["district", "year", "cell_id",
                                               "retained"] + MARKERS))
    coh["cell_id"] = coh["cell_id"].astype(str)
    pan = pan[pan["retained"].astype(int) == 1]

    print("=" * 78)
    print("§3.4 Tier 1 -- SPATIAL COHERENCE (semivariance between cohort pixels)")
    print("=" * 78)
    print(f"  {len(pan)} retained pixel-seasons, {pan.district.nunique()} districts")

    allt, summ = [], []
    for m in MARKERS:
        t = pool(pan, coh, m, by_district=a.by_district)
        allt.append(t)
        s = nugget_and_sill(t[t.group == "ALL"] if not a.by_district else t)
        if s:
            s = dict(marker=m, **s)
            summ.append(s)
            print(f"\n  {m}")
            u = t[(t.group == 'ALL') if not a.by_district else slice(None)]
            for _, r in u.sort_values("lag_lo_km").iterrows():
                flag = "" if r.interpretable else "   [too few pairs]"
                if np.isfinite(r.gamma_d2):
                    print(f"      {r.lag_lo_km:6.1f}-{r.lag_hi_km:<6.1f} km   "
                          f"gamma {r.gamma_d2:9.1f} d^2   rms {r.rms_d:6.2f} d   "
                          f"n {int(r.n_pairs):>9,}{flag}")
            print(f"      nugget ({s['nugget_lag_km']} km) rms {s['nugget_rms_d']:.2f} d"
                  f"   sill ({s['sill_lag_km']} km) rms {s['sill_rms_d']:.2f} d")
            print(f"      nugget/sill {s['nugget_over_sill']:.3f}"
                  + (f"   structured rms {s['structured_rms_d']:.2f} d"
                     if np.isfinite(s.get('structured_rms_d', np.nan)) else
                     "   no structured variance above the nugget"))

    os.makedirs(a.out, exist_ok=True)
    T = pd.concat(allt, ignore_index=True)
    T.to_csv(os.path.join(a.out, "Table_SX_Semivariance.csv"), index=False,
             float_format="%.12g")
    S = pd.DataFrame(summ)
    S.to_csv(os.path.join(a.out, "Table_SX_Semivariance_Summary.csv"), index=False,
             float_format="%.12g")
    print(f"\n  wrote {a.out}/Table_SX_Semivariance.csv")
    print(f"  wrote {a.out}/Table_SX_Semivariance_Summary.csv")
    print("\n  The short-lag value is a MIXTURE of local spatial variation and the")
    print("  spatially UNCORRELATED part of the error. Under additive "
          "signal-independent\n  error it bounds THAT COMPONENT from above -- not "
          "total measurement error,")
    print("  because error shared between neighbouring pixels (orbit geometry, "
          "incidence\n  angle, terrain, a district-season common mode) cancels from "
          "the difference\n  and is missing from this statistic.")
    print("  It is NOT the same estimand as the between-orbit statistic. Where "
          "the two\n  values are numerically similar that is a description of "
          "this dataset: both\n  read one panel through one estimator, and "
          "neither validates the other.")
    print("  It is the shortest interpretable BIN, not a fitted zero-distance "
          "intercept.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
