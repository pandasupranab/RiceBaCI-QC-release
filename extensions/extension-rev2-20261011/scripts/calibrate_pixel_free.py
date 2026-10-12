"""calibrate_pixel_free.py -- selection-aware critical values for the free grid at pixel level.

Grid key written: `pixel_free`. Null: i.i.d. Gaussian (rho = 0), the released
pixel-level choice, treated as an assumption of the noise/missingness model.
n_valid 14..28 (the released pixel range), 4,000 draws per cell (the released
pixel draw count). The released routine `calibrate_plsm_null.one_cell` is
called unchanged with grid == "free", which is the released code's explicit
dispatch to `plsm_designs_free()` (12,649 designs); the row is then labelled
`pixel_free` here. Seeds follow the released scheme for the free grid
(2000 + n_valid), so a second call with the released 1,500 draws reproduces
the released free-grid rows for n_valid 16..28 as a check of the machinery.

Run:  venv/bin/python scripts/calibrate_pixel_free.py --jobs 2
Writes calibration/plsm_null_t_pixel_free.csv, calibration/calibration_check_vs_release.csv,
       calibration/CALIBRATION_RECORD.json
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ext_common as X  # noqa: E402

import calibrate_plsm_null as CAL        # noqa: E402  released, verified copy
import extract_phenometrics_sar as SAR   # noqa: E402

DRAWS = 4000
CHECK_DRAWS = 1500
N_VALID = list(range(SAR.MIN_VALID_DEKADS, 28 + 1))


def _cell(args):
    grid, nv, rho, draws, seed = args
    t0 = time.time()
    r = CAL.one_cell((grid, nv, rho, draws, seed))
    r["seed"] = seed
    r["seconds"] = time.time() - t0
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args(argv)
    assert SAR.MIN_VALID_DEKADS == 14, SAR.MIN_VALID_DEKADS
    assert len(SAR.plsm_designs_free()[0]) == X.FREE_DESIGN_COUNT
    os.makedirs(X.CALIB, exist_ok=True)
    jobs_main = [("free", nv, 0.0, DRAWS, 2000 + nv) for nv in N_VALID]
    jobs_check = [("free", nv, 0.0, CHECK_DRAWS, 2000 + nv) for nv in N_VALID]
    t0 = time.time()
    if a.jobs > 1:
        import multiprocessing as mp
        with mp.Pool(a.jobs) as pool:
            rows_main = pool.map(_cell, jobs_main)
            rows_check = pool.map(_cell, jobs_check)
    else:
        rows_main = [_cell(j) for j in jobs_main]
        rows_check = [_cell(j) for j in jobs_check]
    elapsed = time.time() - t0

    d = pd.DataFrame(rows_main).sort_values("n_valid")
    d["grid"] = X.GRID_KEY
    d["dispatch"] = "released calibrate_plsm_null.one_cell(grid='free') -> plsm_designs_free(), 12649 designs"
    d = d[["grid", "n_valid", "rho", "n_draws", "n_fit", "t95", "t99", "t_med", "seed", "seconds", "dispatch"]]
    d.to_csv(X.NULL_T_PIXEL_FREE, index=False, lineterminator="\n")

    rel = pd.read_csv(os.path.join(X.RELEASE_PY, "plsm_null_t.csv"))
    rel = rel[rel.grid == "free"].set_index("n_valid")
    c = pd.DataFrame(rows_check).sort_values("n_valid")
    c["released_t95"] = c["n_valid"].map(rel["t95"]) if len(rel) else np.nan
    c["released_n_fit"] = c["n_valid"].map(rel["n_fit"]) if len(rel) else np.nan
    c["match_released"] = (np.isclose(c["t95"], c["released_t95"], rtol=0, atol=1e-12)
                           & (c["n_fit"] == c["released_n_fit"]))
    c["released_row_exists"] = c["n_valid"].isin(rel.index)
    c = c[["grid", "n_valid", "n_draws", "n_fit", "t95", "seed", "released_t95", "released_n_fit", "released_row_exists", "match_released"]]
    c.to_csv(os.path.join(X.CALIB, "calibration_check_vs_release.csv"), index=False, lineterminator="\n")
    n_exist = int(c.released_row_exists.sum()); n_match = int(c.match_released.sum())

    rec = dict(environment=X.environment_record(), grid_key=X.GRID_KEY, null="iid Gaussian, rho=0",
               n_valid=N_VALID, draws=DRAWS, seeds={nv: 2000 + nv for nv in N_VALID},
               check_draws=CHECK_DRAWS, check_rows_with_released_counterpart=n_exist,
               check_rows_matching_release=n_match, elapsed_seconds=elapsed, jobs=a.jobs,
               free_design_count=X.FREE_DESIGN_COUNT,
               table_sha256=X.sha256_file(X.NULL_T_PIXEL_FREE),
               released_table_sha256=X.sha256_file(os.path.join(X.RELEASE_PY, "plsm_null_t.csv")),
               sources_sha256={f: X.sha256_file(os.path.join(X.RELEASE_PY, f)) for f in
                               ("calibrate_plsm_null.py", "extract_phenometrics_sar.py", "fit_phenometrics.py")})
    X.write_json(os.path.join(X.CALIB, "CALIBRATION_RECORD.json"), rec)
    print(d.to_string(index=False))
    print()
    print(c.to_string(index=False))
    print(f"\n1,500-draw check: {n_match} of {n_exist} released free-grid rows reproduced exactly")
    print(f"elapsed {elapsed/60:.1f} min with {a.jobs} job(s); wrote {X.NULL_T_PIXEL_FREE}")
    if n_match != n_exist:
        print("CALIBRATION CHECK FAILED: the released rows were not reproduced; stop.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
