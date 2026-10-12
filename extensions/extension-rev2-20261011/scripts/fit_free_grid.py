"""fit_free_grid.py -- Addition B, arm G2: refit every per-orbit series on the released free grid.

Uses the released `plsm_designs_free()` (12,649 designs, verified) through the
extension copy of the released per-file routine (`ext_common.fit_one_file_ext`),
with retention by `ext_common.retain_pixel_free` (released screen; strict
lookup in calibration/plsm_null_t_pixel_free.csv). Everything else is the
released pipeline. Resumable per export file with its own done-file; the G0
cache is never written. Per-file timings are recorded.

Run:  venv/bin/python -I scripts/fit_free_grid.py --jobs 2
Writes results/B_free_grid/per_orbit_fits_pixel_free.csv, fit_done_pixel_free.json, B_fit_timings.csv
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ext_common as X  # noqa: E402

OUT_DIR = os.path.join(X.RESULTS, "B_free_grid")
STORE = os.path.join(OUT_DIR, "per_orbit_fits_pixel_free.csv")
DONE = os.path.join(OUT_DIR, "fit_done_pixel_free.json")
TIMES = os.path.join(OUT_DIR, "B_fit_timings.csv")

_DESIGNS = None


def _designs():
    global _DESIGNS
    if _DESIGNS is None:
        import extract_phenometrics_sar as SAR   # released
        _DESIGNS = SAR.plsm_designs_free()
        assert len(_DESIGNS[0]) == X.FREE_DESIGN_COUNT, len(_DESIGNS[0])
    return _DESIGNS


def _one(f):
    t0 = time.time()
    rows = X.fit_one_file_ext(os.path.join(X.PERORBIT_DIR, f), _designs(), X.retain_pixel_free,
                              expected_designs=X.FREE_DESIGN_COUNT)
    return f, rows, time.time() - t0


def run_key():
    h = hashlib.sha256()
    for f in sorted(os.listdir(X.PERORBIT_DIR)):
        h.update(f.encode()); h.update(X.sha256_file(os.path.join(X.PERORBIT_DIR, f)).encode())
    for f in ("extract_phenometrics_sar.py", "fit_phenometrics.py", "orbit_agreement.py"):
        h.update(X.sha256_file(os.path.join(X.RELEASE_PY, f)).encode())
    h.update(X.sha256_file(X.NULL_T_PIXEL_FREE).encode())
    h.update(X.sha256_file(os.path.join(HERE, "ext_common.py")).encode())
    h.update(X.GRID_KEY.encode()); h.update(str(X.FREE_DESIGN_COUNT).encode())
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args(argv)
    os.makedirs(OUT_DIR, exist_ok=True)
    # the calibration table must exist and cover 14..28 before anything is fitted
    tab = X.load_null_table()
    for nv in range(14, 29):
        X.t_crit_strict(X.GRID_KEY, nv)
    key = run_key()
    done = set()
    if os.path.exists(DONE) or os.path.exists(STORE):
        if not (os.path.exists(DONE) and os.path.exists(STORE)):
            raise SystemExit("incomplete cache pair; use a new empty output directory")
        rec = json.load(open(DONE, encoding="utf-8"))
        if rec["run_key"] != key:
            raise SystemExit("existing G2 cache was produced under a different run key; refusing to resume")
        if X.sha256_file(STORE) != rec["store_sha256"]:
            raise SystemExit("existing G2 cache hash does not match its done-file; refusing to resume")
        done = set(rec["done"])
    files = sorted(f for f in os.listdir(X.PERORBIT_DIR) if f.endswith(".csv"))
    todo = [f for f in files if f not in done]
    if a.limit:
        todo = todo[:a.limit]
    print(f"{len(files)} export files, {len(done)} already fitted, {len(todo)} this run; jobs={a.jobs}; run_key {key[:16]}", flush=True)
    t_start = time.time()
    times = []
    if a.jobs > 1:
        import multiprocessing as mp
        pool = mp.Pool(a.jobs)
        it = pool.imap(_one, todo)
    else:
        it = map(_one, todo)
    j = 0
    for f, rows, secs in it:
        j += 1
        df = pd.DataFrame(rows)
        df["grid"] = X.GRID_KEY
        df.to_csv(STORE, mode=("a" if os.path.exists(STORE) else "w"), header=not os.path.exists(STORE),
                  index=False, lineterminator="\n")
        done.add(f)
        times.append(dict(file=f, series=len(rows), retained=int(df["retained"].sum()), seconds=secs))
        store_hash = X.sha256_file(STORE)
        with open(DONE + ".tmp", "w", encoding="utf-8", newline="\n") as fh:
            json.dump(dict(run_key=key, grid=X.GRID_KEY, done=sorted(done), store_sha256=store_hash,
                           environment=X.environment_record()), fh)
        os.replace(DONE + ".tmp", DONE)
        if j % 10 == 0 or j == len(todo):
            el = time.time() - t_start
            print(f"  {j}/{len(todo)}  ({f}: {len(rows)} series, {secs:.1f}s)  elapsed {el/60:.1f} min", flush=True)
    if a.jobs > 1:
        pool.close(); pool.join()
    tdf = pd.DataFrame(times)
    if os.path.exists(TIMES):
        tdf = pd.concat([pd.read_csv(TIMES), tdf], ignore_index=True)
    tdf.to_csv(TIMES, index=False, lineterminator="\n")
    remaining = len(files) - len(done)
    print(f"wrote {STORE}; this run {time.time()-t_start:.0f}s wall for {len(todo)} files; "
          f"{'INCOMPLETE: %d files remain' % remaining if remaining else 'complete'}", flush=True)
    return 3 if remaining else 0


if __name__ == "__main__":
    sys.exit(main())
