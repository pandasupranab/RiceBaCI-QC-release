#!/usr/bin/env python3
"""H1 and H2, second clause: within-pixel vs between-pixel dispersion.

§2's H1 has TWO clauses joined by "and":

  (a) radar trough breakpoints fitted separately to Sentinel-1 relative-orbit
      series agree within a pre-declared tolerance, AND
  (b) each pixel's inter-seasonal dispersion about its own mean, after removing
      season effects, is smaller than the between-pixel dispersion within its
      district.

H2 is the same pair for the radar fall-end breakpoint. Clause (a) uses the
completed per-orbit export and is reported by ``orbit_agreement.py``. **Clause
(b) is a different calculation.** It needs only a
per-pixel per-season marker, which the committed panel already has for all 25
districts and all nine seasons. It was blocked on nothing.

WHAT IT MEANS. If a pixel's marker wanders less from season to season than
pixels wander from each other inside the same district, then the estimator is
tracking something stable about that pixel rather than producing a fresh draw
each season. That is a consistency claim -- exactly what §3.4 says Objective 4
requires in place of the accuracy claim H1/H2 used to make -- and it carries no
causal content about cyclones, so the 2026-09-13 amendment (§4.1) leaves it
untouched.

THE DECOMPOSITION. Season effects are removed first, as the clause requires:
r_ps = Y_ps - mean_p(Y_ps) over the season, so a year in which every pixel ran
late does not count as pixel-level wander. Then within each district:

    between  sd of the pixel means m_p = mean_s r_ps
    within   pooled sd of r_ps - m_p, with sum(n_p - 1) degrees of freedom

and the clause is met when within < between. The ratio is reported, not just the
verdict, because a ratio of 0.99 and one of 0.3 are different findings.

TWO ARMS, both reported. All retained pixel-seasons; and only those with no
severe exposure of any timing class. The latter is a descriptive sensitivity on
a different sample; it neither isolates the instrument nor identifies why the
dispersion ratio has its observed value. The first arm is the clause as written,
and both are reported without a causal explanation.

INFERENCE. The statistic is a ratio of dispersions pooled over districts, so its
sampling variation comes from which districts and pixels are in the panel. A
cluster bootstrap over DISTRICTS (the level §3.8 clusters at, 25 of them) gives
the interval. A ratio below 1 whose upper bound is above 1 is reported as not
established, not as met.
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
from attrition_diagnostics import build_exposure_table, load_panel, SEED

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

PANEL = os.path.join(RESULTS, "phen_panel_sar_static.csv")
EXPOSURE = _find_doc("district_cyclone_exposure_ibtracs50km.csv")
OUT = os.path.join(RESULTS, "dispersion")
MARKERS = [("trough", "H1 clause (b): radar trough breakpoint"),
           ("harvest", "H2 clause (b): radar fall-end breakpoint"),
           ("heading", "supplementary: radar rise-end breakpoint")]
MIN_SEASONS = 2          # a within-pixel dispersion needs at least two seasons
N_BOOT = 2000


def decompose(d, col):
    """Within- and between-pixel dispersion of `col`, season effects removed.

    Returns (within_sd, between_sd, n_pixels, n_obs) or None when the district
    has too few pixels with repeat observations to support either quantity.
    """
    d = d.dropna(subset=[col])
    if d.empty:
        return None
    # remove season effects: the clause says "after removing season effects", so
    # a season in which the whole district ran late must not read as pixel wander
    d = d.assign(_r=d[col] - d.groupby("year")[col].transform("mean"))
    g = d.groupby("cell_id")["_r"]
    n = g.size()
    keep = n[n >= MIN_SEASONS].index
    d = d[d["cell_id"].isin(keep)]
    if d["cell_id"].nunique() < 3:
        return None
    m = d.groupby("cell_id")["_r"].transform("mean")
    dev = d["_r"] - m
    dof = len(d) - d["cell_id"].nunique()
    if dof <= 0:
        return None
    within = float(np.sqrt((dev ** 2).sum() / dof))
    between = float(d.groupby("cell_id")["_r"].mean().std(ddof=1))
    return within, between, int(d["cell_id"].nunique()), int(len(d))


def components(panel, col, districts):
    """Per-district (within_var, between_var, n_pixels). Computed ONCE.

    The cluster bootstrap resamples DISTRICTS, and a district's own variance
    components do not change when other districts are drawn alongside it. So they
    are formed once here and the bootstrap re-pools them, instead of rebuilding
    and re-decomposing the panel 2,000 times.
    """
    out = []
    for dist in districts:
        r = decompose(panel[panel["district"] == dist], col)
        if r is None:
            continue
        within, between, npix, _ = r
        if not (np.isfinite(within) and np.isfinite(between)) or between <= 0:
            continue
        out.append((within ** 2, between ** 2, float(npix)))
    return out


def pool(comp):
    """Pool per-district components on the VARIANCE scale, pixel-weighted.

    Weighting by pixels keeps a district with 40 usable pixels from counting as
    much as one with 900.
    """
    if not comp:
        return None
    wv = np.array([c[0] for c in comp])
    bv = np.array([c[1] for c in comp])
    w = np.array([c[2] for c in comp])
    within = float(np.sqrt(np.average(wv, weights=w)))
    between = float(np.sqrt(np.average(bv, weights=w)))
    return within, between, within / between, len(comp), int(w.sum())


def run(arm_label, panel, out_rows, seed=SEED):
    districts = sorted(panel["district"].unique())
    rng = np.random.default_rng(seed)
    print(f"\n{'=' * 78}\n{arm_label}\n{'=' * 78}")
    print(f"  {len(panel)} retained pixel-seasons, {len(districts)} districts")
    for col, label in MARKERS:
        comp = components(panel, col, districts)
        p = pool(comp)
        if p is None:
            print(f"  {label:<44s} not estimable")
            continue
        within, between, ratio, nd, npix = p
        # cluster bootstrap over districts: resample the per-district components
        ratios = []
        idx = np.arange(len(comp))
        for _ in range(N_BOOT):
            pick = rng.choice(idx, size=len(idx), replace=True)
            q = pool([comp[i] for i in pick])
            if q:
                ratios.append(q[2])
        lo, hi = (float(np.quantile(ratios, 0.025)),
                  float(np.quantile(ratios, 0.975))) if ratios else (np.nan,) * 2
        met = ratio < 1.0 and hi < 1.0
        verdict = ("MET" if met else
                   ("ratio < 1 but interval includes 1: NOT ESTABLISHED"
                    if ratio < 1.0 else "NOT MET"))
        print(f"  {label}")
        print(f"    within-pixel sd  {within:7.3f} d     between-pixel sd "
              f"{between:7.3f} d")
        print(f"    ratio {ratio:.4f}   95% CI [{lo:.4f}, {hi:.4f}]   "
              f"{nd} districts, {npix} pixels")
        print(f"    -> {verdict}")
        out_rows.append(dict(arm=arm_label, marker=col, label=label,
                             within_sd=within, between_sd=between, ratio=ratio,
                             ci_lo=lo, ci_hi=hi, n_districts=nd, n_pixels=npix,
                             n_boot=len(ratios), verdict=verdict))


def selftest():
    """Planted variance components must be recovered, in both directions."""
    ok_all = True
    rng = np.random.default_rng(11)
    for tag, sd_pix, sd_season, expect in (("consistent", 10.0, 2.0, True),
                                           ("inconsistent", 2.0, 10.0, False)):
        rows = []
        for di in range(6):
            for p in range(60):
                base = rng.normal(0, sd_pix)
                for yr in range(2017, 2026):
                    rows.append(dict(district=f"D{di}", year=yr,
                                     cell_id=f"D{di}_{p}", retained=1,
                                     trough=200 + base + rng.normal(0, sd_season)
                                            + 3.0 * (yr - 2021)))
        d = pd.DataFrame(rows)
        r = pool(components(d, "trough", sorted(d.district.unique())))
        ok = (r[2] < 1.0) == expect
        ok_all &= ok
        print(f"  planted pixel sd {sd_pix:4.1f}, season-noise sd {sd_season:4.1f}"
              f"  -> within {r[0]:6.3f}  between {r[1]:6.3f}  ratio {r[2]:.3f}")
        print(f"  [{'PASS' if ok else 'FAIL'}] ratio < 1 is {r[2] < 1.0}, "
              f"expected {expect}")
    # a pure season effect must NOT register as pixel wander
    rows = []
    for di in range(4):
        for p in range(50):
            base = rng.normal(0, 8.0)
            for yr in range(2017, 2026):
                rows.append(dict(district=f"D{di}", year=yr,
                                 cell_id=f"D{di}_{p}", retained=1,
                                 trough=200 + base + 25.0 * (yr - 2021)))
    d = pd.DataFrame(rows)
    r = pool(components(d, "trough", sorted(d.district.unique())))
    ok = r[0] < 1e-6
    ok_all &= ok
    print(f"  a 25 d/season common shift and NO pixel noise -> within "
          f"{r[0]:.2e} d")
    print(f"  [{'PASS' if ok else 'FAIL'}] season effects are removed before "
          f"the within-pixel term is formed")
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="H1/H2 clause (b).")
    ap.add_argument("--panel", default=PANEL)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    panel = load_panel(a.panel, "pixel", verbose=False)
    panel = panel[panel["retained"] == 1].copy()
    rows = []
    run("all retained pixel-seasons", panel, rows, a.seed)

    expo = pd.read_csv(EXPOSURE)
    tab = build_exposure_table(expo, sorted(panel["district"].unique()),
                              sorted(panel["year"].unique()))
    p2 = panel.merge(tab, on=["district", "year"], how="left")
    for c in ("S_pre_season", "S_harvest_window"):
        p2[c] = p2[c].fillna(0).astype(int)
    unexposed = p2[(p2["S_pre_season"] == 0) & (p2["S_harvest_window"] == 0)]
    run("no severe exposure of any timing class", unexposed, rows, a.seed)

    os.makedirs(a.out, exist_ok=True)
    dest = os.path.join(a.out, "Table_SX_Dispersion.csv")
    pd.DataFrame(rows).to_csv(dest, index=False)
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
