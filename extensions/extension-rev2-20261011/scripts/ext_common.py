"""ext_common.py -- shared pieces of the 10 October 2026 extension.

Extension of the verified public release (tag v1.0.0, commit a465400e). The
released modules are imported from `release_src/python`, a verified copy of
the release tree; they are never edited. Everything specific to the
extension lives in `scripts/`.

What this module provides
- paths and the environment record;
- SHA-256 / git-blob hashing helpers;
- a STRICT critical-value lookup for the extension's own grid key
  (`pixel_free`): a missing key or a missing n_valid row raises; there is no
  fallback constant (Codex B2);
- `retain_pixel_free`, the released retention screen with the strict lookup
  in place of `plsm_t_crit`;
- `fit_one_file_ext`, a copy of the released `orbit_agreement.fit_one_file`
  whose only change is that the retention function is a parameter (the
  released code hard-codes grid="pixel"); with the released designs and the
  released retention it must reproduce the released cache, which the
  preflight checks row for row (Codex B1).
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time

import numpy as np
import pandas as pd

EXT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELEASE_SRC = os.path.join(EXT, "release_src")
RELEASE_PY = os.path.join(RELEASE_SRC, "python")
INPUTS = os.path.join(EXT, "inputs")
PERORBIT_DIR = os.path.join(INPUTS, "raw_zip", "work", "inputs", "s1_perorbit")
CACHE_G0 = os.path.join(INPUTS, "staged", "per_orbit_fits.csv")
PAIRS_RELEASED = os.path.join(RELEASE_SRC, "results", "orbit_agreement", "orbit_pairs.csv")
CALIB = os.path.join(EXT, "calibration")
RESULTS = os.path.join(EXT, "results")
LOGS = os.path.join(EXT, "logs")
PREFLIGHT = os.path.join(EXT, "preflight")
NULL_T_PIXEL_FREE = os.path.join(CALIB, "plsm_null_t_pixel_free.csv")

# the released code locates docs/ through this variable (orbit_agreement.py)
os.environ.setdefault("RICEBACI_ROOT", RELEASE_SRC)
os.environ.setdefault("RICEBACI_RESULTS", os.path.join(EXT, "results", "_released_layout_unused"))
if RELEASE_PY not in sys.path:
    sys.path.insert(0, RELEASE_PY)

GRID_KEY = "pixel_free"
FREE_DESIGN_COUNT = 12649       # the released free grid (Codex, verified)
PIXEL_DESIGN_COUNT = 4322       # the released restricted grid


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def environment_record() -> dict:
    return dict(python=sys.version.split()[0], numpy=np.__version__, pandas=pd.__version__,
                platform=platform.platform(), machine=platform.machine(),
                cpu_count=os.cpu_count(), utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))


# ---------------------------------------------------------------------------
# strict critical-value lookup (no fallback)
# ---------------------------------------------------------------------------
class CalibrationMissing(RuntimeError):
    pass


_NULL_CACHE: dict = {}


def load_null_table(path: str = NULL_T_PIXEL_FREE) -> dict:
    """{(grid, n_valid): t95}. Raises if the file is absent."""
    if path in _NULL_CACHE:
        return _NULL_CACHE[path]
    if not os.path.exists(path):
        raise CalibrationMissing(f"critical-value table absent: {path}")
    d = pd.read_csv(path)
    for c in ("grid", "n_valid", "t95", "n_draws", "seed"):
        if c not in d.columns:
            raise CalibrationMissing(f"{path}: column {c!r} missing")
    tab = {(str(r["grid"]), int(r["n_valid"])): float(r["t95"]) for _, r in d.iterrows()}
    _NULL_CACHE[path] = tab
    return tab


def t_crit_strict(grid: str, n_valid: int, path: str = NULL_T_PIXEL_FREE) -> float:
    """The 5% one-sided selection-aware critical value for (grid, n_valid).

    Unlike the released plsm_t_crit, this never substitutes an AR(1) value, a
    neighbouring n_valid or a constant: a missing key or row STOPS the run.
    """
    tab = load_null_table(path)
    key = (str(grid), int(n_valid))
    if key not in tab:
        raise CalibrationMissing(f"no calibration row for grid={grid!r}, n_valid={int(n_valid)} in {path}")
    v = tab[key]
    if not np.isfinite(v):
        raise CalibrationMissing(f"non-finite critical value for {key} in {path}")
    return v


def retain_pixel_free(m: dict, min_rise_db: float = 0.0):
    """The released plsm_retain screen, with the strict pixel_free lookup.

    Body copied from release python/extract_phenometrics_sar.py:plsm_retain
    (v1.0.0); the single change is `t_crit_strict(GRID_KEY, n_valid)` in
    place of `plsm_t_crit(grid, n_valid)`.
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
    tc = t_crit_strict(GRID_KEY, m["n_valid"])
    if t < tc:
        return False, (f"rise not significant: t {t:.2f} below the "
                       f"selection-aware {tc:.2f} ({GRID_KEY} grid, "
                       f"{int(m['n_valid'])} valid dekads)")
    return True, ""


# ---------------------------------------------------------------------------
# the released per-file fit, with the retention function as a parameter
# ---------------------------------------------------------------------------
def fit_one_file_ext(path: str, designs, retain_fn, expected_designs: int | None = None):
    """Copy of release python/orbit_agreement.py:fit_one_file (v1.0.0).

    Changes relative to the release, and nothing else:
      * `retain_fn(m)` replaces `plsm_retain(m, min_rise_db=0.0, grid="pixel")`;
      * `expected_designs`, when given, must equal len(designs[0]) or the
        call raises (explicit dispatch to the intended design matrix).
    GATE1_R, USE_SMOOTHING, N_BINS_, REQUIRED and the aggregation / smoothing /
    fit routines are the released module's own objects.
    """
    import orbit_agreement as OA          # released module (verified copy)
    import fit_phenometrics as _FP        # released module
    from extract_phenometrics_sar import plsm_fit   # released
    if expected_designs is not None and len(designs[0]) != expected_designs:
        raise RuntimeError(f"design matrix has {len(designs[0])} designs, expected {expected_designs}")
    df = OA.read_per_orbit(path)
    district = str(df["district"].iloc[0])
    year = int(df["year"].iloc[0])
    rows = []
    for orbit, s in df.groupby("orbit", sort=True):
        cells = s["cell_id"].drop_duplicates().to_numpy()
        idx = {c: i for i, c in enumerate(cells)}
        V = np.full((len(cells), OA.N_BINS_), np.nan)
        C = np.zeros((len(cells), OA.N_BINS_))
        r = s["cell_id"].map(idx).to_numpy()
        b = s["bin_index"].to_numpy(int)
        V[r, b] = pd.to_numeric(s["VHVV_med"], errors="coerce").to_numpy()
        C[r, b] = pd.to_numeric(s["valid_obs_count"],
                                errors="coerce").fillna(0.0).to_numpy()
        opass = str(s["orbit_pass"].iloc[0])[:4].upper()
        counts = np.nansum(np.where(np.isfinite(V), C, 0.0), axis=0)
        admitted = (_FP.gate1_admitted_bins(counts, OA.GATE1_R)
                    if OA.GATE1_R > 0 else np.ones(OA.N_BINS_, dtype=bool))
        DV, DC = _FP.aggregate_to_dekads(V, C, admitted)
        for i in range(DV.shape[0]):
            valid = np.isfinite(DV[i])
            series = np.where(valid, DV[i], 0.0)
            if OA.USE_SMOOTHING and valid.sum() >= 4:
                w = np.where(valid, np.maximum(DC[i], 1.0), 0.0)
                series, _, _ = _FP.whittaker_gcv(series, w)
            m = plsm_fit(series, valid, designs)
            ok, why = retain_fn(m)
            rows.append(dict(
                district=district, year=year, cell_id=cells[i],
                orbit=int(orbit), orbit_pass=opass,
                n_valid=int(m["n_valid"]), retained=int(ok),
                fail_reason=("" if ok else why),
                **{k: m[k] for k in ("trough", "heading", "harvest",
                                     "rise_db", "rmse")}))
    return rows


def released_retain_pixel():
    """The released retention exactly as fit_one_file calls it (grid='pixel')."""
    from extract_phenometrics_sar import plsm_retain
    return lambda m: plsm_retain(m, min_rise_db=0.0, grid="pixel")


def write_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=1, default=str)
        fh.write("\n")
