"""
merge_cohort_exports.py — merge the per-district cohort CSVs exported by gee/S2_QC_Ingest.js §9d
into the single committed cohort file for that cohort id (Protocol v1 §3.6).

Cohort id is read from the filenames rather than hard-coded, so v2 and any
later cohort merge with the same script. v1 (27 districts, drawn from the
RiceAtlas polygon) is retired; v2 draws 400 pixels in each of 25 districts
from the primary rice mask of Protocol §3.5.

The exported files are named S2_COHORT_<cohort_id>_<District_Name>.csv and carry
Earth Engine's own columns (system:index, .geo) alongside the six the protocol
defines. This script keeps the six, sorts deterministically so the committed
file is byte-stable across re-runs, checks for duplicate cell_ids, and prints
the per-district counts actually drawn (fewer than the 400 target only if a
district holds fewer eligible rice-mask pixels).

Usage:
    python python/merge_cohort_exports.py <dir-of-exported-csvs> [out.csv]

Default output: docs/candidate_cohort_<cohort_id>.csv
"""
import sys
import glob
import os
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
SRC = sys.argv[1] if len(sys.argv) > 1 else "."
COLS = ["state", "district", "tile_id", "cell_id", "lon", "lat"]
TARGET = 400
EXPECTED_DISTRICTS = 25          # Protocol §1.3 roster after the 2026-09-09 exclusions

paths = sorted(glob.glob(os.path.join(SRC, "S2_COHORT_*.csv")))
if not paths:
    raise SystemExit(f"no S2_COHORT_*.csv found in {SRC}")

# Cohort id is whatever the exports carry; refuse a mixed folder outright.
ids = {os.path.basename(p).split("_")[2] + "_" + os.path.basename(p).split("_")[3]
       for p in paths}
if len(ids) != 1:
    raise SystemExit(f"folder mixes cohort ids {sorted(ids)} -- merge one cohort at a time")
COHORT_ID = ids.pop()
# COHORT_ID is "cohort_v2"; the committed file is docs/candidate_cohort_v2.csv
# (Protocol §3.6), so strip the redundant prefix rather than doubling it.
_SUFFIX = COHORT_ID[len("cohort_"):] if COHORT_ID.startswith("cohort_") else COHORT_ID
OUT = sys.argv[2] if len(sys.argv) > 2 else f"docs/candidate_cohort_{_SUFFIX}.csv"
print(f"cohort id from filenames: {COHORT_ID}")
print(f"merging {len(paths)} files from {SRC}")

frames = []
for p in paths:
    d = pd.read_csv(p)
    missing = [c for c in COLS if c not in d.columns]
    if missing:
        raise SystemExit(f"{os.path.basename(p)}: missing columns {missing}")
    frames.append(d[COLS])

cohort = pd.concat(frames, ignore_index=True)
cohort = cohort.sort_values(["state", "district", "cell_id"]).reset_index(drop=True)

dupes = cohort[cohort.duplicated(subset=["cell_id"], keep=False)]
if len(dupes):
    raise SystemExit(
        f"{len(dupes)} duplicate cell_id rows — cell_id must be unique across the "
        f"cohort because it is the panel's per-pixel key (Protocol §3.6, §3.10):\n"
        f"{dupes.head(10).to_string(index=False)}")

counts = cohort.groupby(["state", "district"]).size()
print("\npoints drawn per district:")
for (st, dn), n in counts.items():
    flag = "" if n == TARGET else f"   <-- {n} of {TARGET} (district holds fewer eligible pixels)"
    print(f"  {st:15s} {dn:20s} {n:4d}{flag}")

n_dist = len(counts)
if n_dist != EXPECTED_DISTRICTS:
    print(f"\nWARNING: {n_dist} districts present, expected {EXPECTED_DISTRICTS} "
          f"(Protocol §1.3 roster: 28 coastal, minus Kolkata, minus Nellore and "
          f"Prakasam under the minimum-Kharif-rice criterion). Check for a "
          f"missing or failed export task.")

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
cohort.to_csv(OUT, index=False)
print(f"\nwrote {OUT}: {len(cohort)} rows, {n_dist} districts")
print("Next: commit this file, upload the same file to Earth Engine as a table "
      "asset, then set CONFIG.cohortAssetPath in gee/S2_QC_Ingest.js and "
      "CONFIG.buildCohort = false.")
