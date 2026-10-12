"""preflight.py -- the checks that must all pass before any extension result is read.

Run:  venv/bin/python -I -B scripts/preflight.py                          (from the extension root)
      venv/bin/python -I -B scripts/preflight.py --validate-sources-only  (section 1 only; writes nothing)
Writes preflight/PREFLIGHT_REPORT.json and prints a transcript. Exit 0 only if
every check passed. Step numbers follow PLAN_FROZEN_2026-10-10.md.

Revision 2 (11 Oct 2026, Codex extension review, required correction 1):
section 1 validates the shipped release_src/ IN PLACE against the recorded
59-file set and v1.0.0 blob hashes (scripts/validate_release_src.py) before
any released module is imported. A missing, empty, incomplete, extended or
altered release_src/ stops the preflight here with exit 2; nothing is copied,
removed or chmod-ed under any outcome. The 2026-10-10 version read a duplicate
staging directory (inputs/release_zip/, not delivered), accepted zero files
and then replaced release_src/; that block is gone.
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.dont_write_bytecode = True   # never write __pycache__ into release_src/ (also run with python -I -B)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import validate_release_src as VRS  # noqa: E402  (stdlib only; imports nothing from release_src)

VALIDATE_ONLY = "--validate-sources-only" in sys.argv[1:]

# ---------------------------------------------------------------------------
print("=" * 74)
print("PREFLIGHT 1 -- input identities")
print("=" * 74)
# 1a. release_src/ in place, fail-closed, before anything from it is imported
try:
    SRC = VRS.validate()
except VRS.ExpectationError as e:
    print(f"  [STOP] release_src validation not performed: {e}")
    sys.exit(3)
print(f"  [{'PASS' if SRC['ok'] else 'FAIL'}] release_src/ equals the recorded 59-file v1.0.0 set, byte-exact blobs, "
      f"no extra files (validated in place; nothing copied, removed or modified)  -- {VRS.summary_line(SRC)}")
if not SRC["ok"]:
    print("=" * 74)
    print("PREFLIGHT STOPPED: release_src/ is not the verified v1.0.0 copy. No released module was imported, "
          "no file was changed, no report was written. Restore release_src/ as described in README.md.")
    print("=" * 74)
    sys.exit(2)
if VALIDATE_ONLY:
    print("=" * 74)
    print("PREFLIGHT 1a PASSED (--validate-sources-only: no further checks, no report written)")
    print("=" * 74)
    sys.exit(0)

import numpy as np   # noqa: E402
import pandas as pd  # noqa: E402
import ext_common as X  # noqa: E402  (adds release_src/python to sys.path; imports released modules lazily)

REPORT = {"environment": X.environment_record(), "checks": []}
FAILED = []


def check(name, ok, detail=""):
    REPORT["checks"].append(dict(name=name, ok=bool(ok), detail=detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  -- {detail}" if detail else ""))
    if not ok:
        FAILED.append(name)
    return bool(ok)


check("release_src/ equals the recorded 59-file v1.0.0 set (byte-exact git blobs, no missing or extra files; "
      "validated in place, nothing copied/removed/modified)", SRC["ok"],
      f"{SRC['matched']} of {SRC['expected_count']} matched, {SRC['present_count']} present, {len(SRC['problems'])} problems")
REPORT["release_src_files"] = dict(sorted(SRC["files"].items()))
REPORT["release_src_validation"] = dict(mode="in place, fail-closed (scripts/validate_release_src.py)",
                                        expected_list="inputs/staged/release_src_expected_blobs.txt",
                                        tree_record="inputs/staged/git_ls_tree_v1.0.0.txt",
                                        release_commit=SRC["release_commit"], ok=SRC["ok"])

man = json.load(open(os.path.join(X.INPUTS, "staged", "Paper2_raw_inputs_2017-2025.zip.manifest.json"), encoding="utf-8"))
want = {f["path"]: f for f in man["files"] if f["path"].startswith("work/inputs/s1_perorbit/")}
files = sorted(os.listdir(X.PERORBIT_DIR))
tot = 0
mism = []
for f in files:
    p = os.path.join(X.PERORBIT_DIR, f)
    rel = "work/inputs/s1_perorbit/" + f
    h = X.sha256_file(p); n = os.path.getsize(p); tot += n
    w = want.get(rel)
    if w is None or w["sha256"] != h or int(w.get("size", w.get("bytes", n))) != n:
        mism.append(f)
check("225 per-orbit exports match the deposit manifest", len(files) == 225 and len(want) == 225 and not mism,
      f"{len(files)} files, {tot:,} bytes, mismatches {mism[:3]}")
REPORT["perorbit_total_bytes"] = tot

rman = json.load(open(os.path.join(X.INPUTS, "staged", "Paper2_replay_inputs_a465400.zip.manifest.json"), encoding="utf-8"))
cache_want = [f for f in rman["files"] if f["path"].endswith("orbit_agreement/per_orbit_fits.csv")][0]
cache_hash = X.sha256_file(X.CACHE_G0)
check("G0 fit cache matches the replay-inputs manifest", cache_hash == cache_want["sha256"], cache_hash[:16])
REPORT["cache_g0_sha256"] = cache_hash

pairs_hash = X.sha256_file(X.PAIRS_RELEASED)
snap_hash = X.sha256_file(os.path.join(X.INPUTS, "submitted_tables", "orbit_agreement__orbit_pairs.csv"))
sh = pd.read_csv(os.path.join(X.INPUTS, "submitted_tables", "source_hashes.csv"))
row = sh[sh.iloc[:, 0].astype(str).str.contains("orbit_pairs.csv")]
ledger_hash = str(row["sha256"].iloc[0]) if len(row) else ""
check("released orbit_pairs.csv == submitted snapshot == ledger hash",
      pairs_hash == snap_hash and (ledger_hash == pairs_hash or ledger_hash == ""),
      f"{pairs_hash[:16]} ledger={ledger_hash[:16] if ledger_hash else 'n/a'}")
REPORT["pairs_sha256"] = pairs_hash

# ---------------------------------------------------------------------------
print("=" * 74)
print("PREFLIGHT 2 -- structure")
print("=" * 74)
P = pd.read_csv(X.PAIRS_RELEASED)
ev, bl = P[P.year > 2017], P[P.year == 2017]
check("pairs: 8,515 = 798 baseline + 7,717 evaluation", len(P) == 8515 and len(bl) == 798 and len(ev) == 7717)
check("pairs: unique (district, year, cell_id) keys", not P.duplicated(["district", "year", "cell_id"]).any())
check("pairs: no missing marker differences", P[["d_trough", "d_heading", "d_harvest"]].notna().all().all())
cell = ["district", "year", "orbit_a", "orbit_b"]
cs = ev.groupby(cell).size()
elig = ev.merge(cs[cs >= 2].rename("n_cell").reset_index(), on=cell)
check("evaluation cells: 383 total, 342 eligible, 7,676 eligible rows, 41 singletons",
      len(cs) == 383 and (cs >= 2).sum() == 342 and len(elig) == 7676 and (cs == 1).sum() == 41,
      f"{len(cs)} cells, {(cs>=2).sum()} eligible, {len(elig)} rows, {(cs==1).sum()} singletons, {(cs==2).sum()} two-row cells")
check("eligible evaluation pass split 6,409 A/D + 1,267 same-pass",
      int(elig.asc_desc.sum()) == 6409 and int((elig.asc_desc == 0).sum()) == 1267,
      f"{int(elig.asc_desc.sum())} / {int((elig.asc_desc==0).sum())}; districts {elig.district.nunique()}")
csb = bl.groupby(cell).size()
check("baseline cells: 41 eligible, 792 rows", (csb >= 2).sum() == 41 and csb[csb >= 2].sum() == 792,
      f"{len(csb)} cells, {(csb>=2).sum()} eligible, {csb[csb>=2].sum()} rows")

C = pd.read_csv(X.CACHE_G0)
check("cache: 170,321 series, 44,659 retained, 90,000 pixel-seasons, 12 orbits",
      len(C) == 170321 and int(C.retained.sum()) == 44659
      and C.groupby(["district", "year", "cell_id"]).ngroups == 90000 and C.orbit.nunique() == 12)
check("cache: unique (district, year, cell_id, orbit) keys", not C.duplicated(["district", "year", "cell_id", "orbit"]).any())
R = C[C.retained == 1].set_index(["district", "year", "cell_id", "orbit"])
ja = P.merge(R[["trough", "heading", "harvest"]].add_suffix("_ca"), left_on=["district", "year", "cell_id", "orbit_a"], right_index=True, how="left")
jb = ja.merge(R[["trough", "heading", "harvest"]].add_suffix("_cb"), left_on=["district", "year", "cell_id", "orbit_b"], right_index=True, how="left")
mm = 0
for mk in ("trough", "heading", "harvest"):
    mm += int((jb[f"{mk}_a"] != jb[f"{mk}_ca"]).sum() + (jb[f"{mk}_b"] != jb[f"{mk}_cb"]).sum())
check("every published pair joins to retained cache rows with identical markers",
      jb[["trough_ca", "trough_cb"]].notna().all().all() and mm == 0, f"marker mismatches {mm}")

# ---------------------------------------------------------------------------
print("=" * 74)
print("PREFLIGHT 3 -- designs and the released critical-value lookup")
print("=" * 74)
import extract_phenometrics_sar as SAR  # noqa: E402  (released, verified copy)
import orbit_agreement as OA            # noqa: E402
free = SAR.plsm_designs_free(); pix = SAR.plsm_designs_pixel()
fk, pk = set(free[0]), set(pix[0])
check("free grid has 12,649 designs; restricted 4,322; restricted is a subset",
      len(free[0]) == X.FREE_DESIGN_COUNT and len(pix[0]) == X.PIXEL_DESIGN_COUNT and pk <= fk)
fm = {k: i for i, k in enumerate(free[0])}
same = all(np.array_equal(free[1][fm[k]], pix[1][i]) for i, k in enumerate(pix[0]))
check("restricted design matrices equal the corresponding free design matrices", same)
rel_free = SAR.plsm_t_crit("free", 20); rel_unknown = SAR.plsm_t_crit("pixel_free", 20); rel_pix = SAR.plsm_t_crit("pixel", 20)
check("released lookup: 'free' -> district AR(1) 4.1731..., unknown key -> 3.5 fallback (recorded; NOT used for G2)",
      abs(rel_free - 4.173157563070177) < 1e-12 and rel_unknown == 3.5,
      f"free={rel_free:.6f} pixel_free(unknown)={rel_unknown} pixel(n=20)={rel_pix:.6f}")
REPORT["released_lookup"] = dict(free=rel_free, unknown_key=rel_unknown, pixel_n20=rel_pix)
grid_hash = X.git_blob_sha1(json.dumps([list(map(int, k)) for k in free[0]]).encode())
REPORT["free_grid_keys_sha1"] = grid_hash
REPORT["free_grid_dekad_doy"] = [float(x) for x in __import__("fit_phenometrics").DEKAD_DOY]

# strict lookup failure tests (Codex B2): must raise, not fall back
tmp = os.path.join(X.PREFLIGHT, "_tmp_null_table.csv")
pd.DataFrame([dict(grid="pixel_free", n_valid=20, t95=3.0, t99=4.0, t_med=1.0, n_draws=10, n_fit=10, seed=1)]).to_csv(tmp, index=False)
r1 = r2 = r3 = False
try:
    X.t_crit_strict("pixel_free", 21, tmp)
except X.CalibrationMissing:
    r1 = True
try:
    X.t_crit_strict("pixel", 20, tmp)
except X.CalibrationMissing:
    r2 = True
try:
    X.t_crit_strict("pixel_free", 20, os.path.join(X.PREFLIGHT, "_absent.csv"))
except X.CalibrationMissing:
    r3 = True
check("strict lookup stops on a missing n_valid row, a missing grid key and an absent table", r1 and r2 and r3)
os.remove(tmp)
X._NULL_CACHE.clear()
r4 = False
try:
    X.fit_one_file_ext(os.path.join(X.PERORBIT_DIR, "S1_ORBIT_Baleshwar_2017.csv"), pix, X.released_retain_pixel(), expected_designs=X.FREE_DESIGN_COUNT)
except RuntimeError:
    r4 = True
check("fit_one_file_ext stops when the design count is not the expected one", r4)

# ---------------------------------------------------------------------------
print("=" * 74)
print("PREFLIGHT 4 -- G0 replay in this environment (restricted grid, released retention)")
print("=" * 74)
# representative files: three states, early and late seasons, and files that
# hold bound-touching retained fits under the restricted grid
lo = {"trough": 184.5, "heading": 274.5, "harvest": 324.5}
hi = {"trough": 304.5, "heading": 354.5, "harvest": 422.0}
Cr = C[C.retained == 1]
onb = pd.Series(False, index=Cr.index)
for mk in lo:
    onb |= (Cr[mk] == lo[mk]) | (Cr[mk] == hi[mk])
nb = Cr[onb].groupby(["district", "year"]).size().sort_values(ascending=False)
sample = ["S1_ORBIT_Baleshwar_2017.csv", "S1_ORBIT_West_Godavari_2025.csv", "S1_ORBIT_Pashchim_Medinipur_2024.csv",
          "S1_ORBIT_Puri_2019.csv", "S1_ORBIT_Krishna_2021.csv", "S1_ORBIT_Haora_2022.csv"]
# add the two files with the most bound-touching retained fits, if not already present
for (d, y), n in nb.head(4).items():
    f = f"S1_ORBIT_{d.replace(' ', '_')}_{y}.csv"
    if f not in sample and os.path.exists(os.path.join(X.PERORBIT_DIR, f)):
        sample.append(f)
    if len(sample) >= 8:
        break
sample = [f for f in sample if os.path.exists(os.path.join(X.PERORBIT_DIR, f))]
REPORT["g0_replay_files"] = sample
t_pix = []
rows_all = []
for f in sample:
    t0 = time.time()
    rows = X.fit_one_file_ext(os.path.join(X.PERORBIT_DIR, f), pix, X.released_retain_pixel(), expected_designs=X.PIXEL_DESIGN_COUNT)
    t_pix.append((f, len(rows), time.time() - t0))
    rows_all += rows
rep = pd.DataFrame(rows_all)
key = ["district", "year", "cell_id", "orbit"]
cmp = rep.merge(C, on=key, suffixes=("_new", "_cache"), how="left")
n_missing = int(cmp["retained_cache"].isna().sum())
eq_int = (cmp["retained_new"] == cmp["retained_cache"]) & (cmp["n_valid_new"] == cmp["n_valid_cache"]) & (cmp["orbit_pass_new"] == cmp["orbit_pass_cache"])
eq_reason = cmp["fail_reason_new"].fillna("") == cmp["fail_reason_cache"].fillna("")
def feq(a, b, tol=1e-9):
    a = a.astype(float); b = b.astype(float)
    return (a.isna() & b.isna()) | (np.abs(a - b) <= tol * np.maximum(1.0, np.abs(b)))
eq_mk = feq(cmp["trough_new"], cmp["trough_cache"], 0) & feq(cmp["heading_new"], cmp["heading_cache"], 0) & feq(cmp["harvest_new"], cmp["harvest_cache"], 0)
eq_fl = feq(cmp["rise_db_new"], cmp["rise_db_cache"]) & feq(cmp["rmse_new"], cmp["rmse_cache"])
all_eq = eq_int & eq_reason & eq_mk & eq_fl
n_ret = int(cmp["retained_cache"].sum()); n_rej = int((cmp["retained_cache"] == 0).sum())
nb_in = int(sum(((cmp[f"{mk}_cache"] == lo[mk]) | (cmp[f"{mk}_cache"] == hi[mk])) [cmp["retained_cache"] == 1].sum() for mk in lo))
check("G0 replay reproduces the cache row for row (flags, reasons, markers exact; rise/rmse to 1e-9)",
      n_missing == 0 and bool(all_eq.all()),
      f"{len(cmp)} series in {len(sample)} files: {n_ret} retained, {n_rej} rejected, {nb_in} bound-touching retained marker positions; "
      f"mismatches {int((~all_eq).sum())}, missing {n_missing}")
sec_per_series = sum(t for _, _, t in t_pix) / max(1, sum(n for _, n, _ in t_pix))
REPORT["g0_replay_timing"] = dict(files=t_pix, sec_per_series_restricted=sec_per_series)
print(f"  restricted-grid timing: {sec_per_series*1000:.1f} ms per series ({sum(n for _,n,_ in t_pix)} series)")
if not all_eq.all():
    cmp[~all_eq].to_csv(os.path.join(X.PREFLIGHT, "g0_replay_mismatches.csv"), index=False)

# free-grid timing pilot on one file (fits only; retention needs the calibration table, so the released
# pixel retention is used here purely to time the fitting step -- these rows are discarded)
f0 = sample[0]; t0 = time.time()
rows_free = X.fit_one_file_ext(os.path.join(X.PERORBIT_DIR, f0), free, X.released_retain_pixel(), expected_designs=X.FREE_DESIGN_COUNT)
t_free = time.time() - t0
REPORT["free_grid_timing_pilot"] = dict(file=f0, series=len(rows_free), seconds=t_free, sec_per_series=t_free / max(1, len(rows_free)))
print(f"  free-grid timing pilot: {t_free/len(rows_free)*1000:.1f} ms per series on {f0} ({len(rows_free)} series); "
      f"projected full refit {170321 * t_free / len(rows_free) / 60:.0f} min single-process")

# ---------------------------------------------------------------------------
print("=" * 74)
print("PREFLIGHT 5 -- the released pair builder reproduces orbit_pairs.csv from the cache")
print("=" * 74)
pairs_re, not_est = OA.build_pairs(C)
cols = list(P.columns)
a = pairs_re[cols].sort_values(["district", "year", "cell_id"]).reset_index(drop=True)
b = P[cols].sort_values(["district", "year", "cell_id"]).reset_index(drop=True)
same_pairs = len(a) == len(b) and all(np.allclose(a[c].astype(float), b[c].astype(float), equal_nan=True) if pd.api.types.is_numeric_dtype(b[c]) else (a[c].astype(str) == b[c].astype(str)).all() for c in cols)
check("build_pairs(cache) == released orbit_pairs.csv (all columns)", same_pairs, f"{len(a)} rebuilt vs {len(b)} released; not estimable {len(not_est)}")

# ---------------------------------------------------------------------------
REPORT["failed"] = FAILED
REPORT["passed"] = not FAILED
X.write_json(os.path.join(X.PREFLIGHT, "PREFLIGHT_REPORT.json"), REPORT)
print("=" * 74)
print("PREFLIGHT " + ("PASSED" if not FAILED else f"FAILED: {FAILED}"))
print("=" * 74)
sys.exit(0 if not FAILED else 1)
