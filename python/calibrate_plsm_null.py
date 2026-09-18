"""
calibrate_plsm_null.py -- selection-aware critical values for the PLSM screen.

Reproduces plsm_null_t.csv and plsm_null_t_ar1.csv, which extract_phenometrics_
sar.py loads. Run it if the breakpoint grid, the season grid or the parameter
count changes; the tables are grid-specific and a stale table is worse than none.

WHY THIS EXISTS. The five-segment model's rise screen is a t test on the fitted
rise. After searching thousands of breakpoint quadruples that t is not a t: on
pure Gaussian noise with no season at all, 29% of series clear the nominal 5%
one-sided value on the pixel grid. The valid critical value is the 95th
percentile of the SAME statistic computed the SAME way under the null, which is
what this script tabulates. The statistic is scale-free -- t = rise / se(rise)
and both scale with sigma -- so one table serves every pixel whatever its noise
level, and it depends only on the grid and on how many dekads are valid.

TWO NULLS, AND WHICH ONE APPLIES WHERE IS A MEASUREMENT. The i.i.d. Gaussian
null is right only if the fitted residuals are serially uncorrelated. They are
not, and the sign differs by level: lag-1 autocorrelation median -0.22 at pixel
level (586 baseline pixel-seasons) and +0.21 at district-mean level (25 baseline
districts). Negative autocorrelation makes a spurious rise LESS likely, so the
i.i.d. table is conservative at pixel level and is used there. Positive
autocorrelation cuts the other way, so the district-mean fit uses the AR(1)
table, at the tabulated rho just above the measured median.

    python python/calibrate_plsm_null.py --out-dir python/ --jobs 2

Created 2026-09-12.
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
import extract_phenometrics_sar as SAR       # noqa: E402
import fit_phenometrics as FP                # noqa: E402

N = FP.N_DEKADS


def ar1_draw(rng, n, rho):
    """Unit-variance AR(1). rho = 0 gives i.i.d. Gaussian."""
    if rho == 0.0:
        return rng.normal(0.0, 1.0, n)
    e = rng.normal(0.0, 1.0, n)
    x = np.empty(n)
    x[0] = e[0] / np.sqrt(1.0 - rho * rho)
    for i in range(1, n):
        x[i] = rho * x[i - 1] + e[i]
    return x


def one_cell(args):
    grid, n_valid, rho, draws, seed = args
    rng = np.random.default_rng(seed)
    designs = (SAR.plsm_designs_free() if grid == "free"
               else SAR.plsm_designs_pixel())
    ts = []
    for _ in range(draws):
        valid = np.zeros(N, dtype=bool)
        valid[rng.choice(N, n_valid, replace=False)] = True
        m = SAR.plsm_fit(ar1_draw(rng, N, rho), valid, designs)
        t = m["rise_t"]
        ts.append(t if (t is not None and np.isfinite(t)) else np.nan)
    ts = np.asarray(ts, float)
    fin = ts[np.isfinite(ts)]
    return dict(grid=grid, n_valid=int(n_valid), rho=float(rho),
                n_draws=int(draws), n_fit=int(len(fin)),
                t95=float(np.percentile(fin, 95)) if len(fin) else np.nan,
                t99=float(np.percentile(fin, 99)) if len(fin) else np.nan,
                t_med=float(np.median(fin)) if len(fin) else np.nan)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tabulate PLSM null critical values.")
    ap.add_argument("--out-dir", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--draws-pixel", type=int, default=4000)
    ap.add_argument("--draws-free", type=int, default=1500)
    a = ap.parse_args(argv)

    iid = ([("pixel", nv, 0.0, a.draws_pixel, 1000 + nv)
            for nv in range(SAR.MIN_VALID_DEKADS, N + 1)]
           + [("free", nv, 0.0, a.draws_free, 2000 + nv)
              for nv in range(16, N + 1)])
    ar = ([("free", nv, rho, a.draws_free, 7000 + nv + int(rho * 100))
           for rho in (0.25, 0.40) for nv in (20, 24, 28)]
          + [("pixel", 24, 0.25, a.draws_pixel, 8025)])

    if a.jobs > 1:
        import multiprocessing as mp
        with mp.Pool(a.jobs) as pool:
            rows_iid = pool.map(one_cell, iid)
            rows_ar = pool.map(one_cell, ar)
    else:
        rows_iid = [one_cell(x) for x in iid]
        rows_ar = [one_cell(x) for x in ar]

    d1 = pd.DataFrame(rows_iid).sort_values(["grid", "n_valid"])
    d2 = pd.DataFrame(rows_ar).sort_values(["grid", "rho", "n_valid"])
    p1 = os.path.join(a.out_dir, "plsm_null_t.csv")
    p2 = os.path.join(a.out_dir, "plsm_null_t_ar1.csv")
    d1.to_csv(p1, index=False)
    d2.to_csv(p2, index=False)
    print(d1.to_string(index=False))
    print()
    print(d2.to_string(index=False))
    print()
    for g, gg in d1.groupby("grid"):
        print(f"i.i.d. {g:<6s} t95 {gg['t95'].min():.2f}-{gg['t95'].max():.2f}"
              f"   admissible shape found in "
              f"{gg['n_fit'].sum() / gg['n_draws'].sum():.3f} of draws")
    print(f"\nwrote {p1}\n      {p2}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
