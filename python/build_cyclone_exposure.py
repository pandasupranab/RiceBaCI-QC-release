"""
build_cyclone_exposure.py — pre-declared cyclone-exposure tables for Paper 2
(RiceBaCI-QC, Protocol v1 §1.1 / §3.8, stated 2026-09-07).

Everything Objective 4 treats as "treatment" is derived here, from two public
inputs and a fixed rule, before any phenology is extracted:

  1. docs/district_cyclone_exposure_ibtracs50km.csv
     One row per (roster district, season, storm) for every IBTrACS v04r01
     North-Indian-basin storm, seasons 2016-2025, whose >= 34 kt track came
     within 50 km of the district. Columns:
        state, district_gadm_name, season, sid, storm_name,
        max_wind_kt_within_50km   (IMD 3-min wind; JTWC 1-min where IMD missing;
                                   the maximum over all >= 34 kt track segments
                                   within 50 km of the district)
        maxwind_fix_iso_time, maxwind_fix_month
                                  (time/month of the fix opening the segment
                                   that carries that maximum wind)
        maxwind_segment_dist_km   (district-to-segment distance for that segment)
        min_dist_to_track34kt_km  (district-to-track distance over ALL >= 34 kt
                                   segments of the storm; may be smaller)
        timing_class              (from maxwind_fix_month: pre_season Apr-Jul;
                                   mid_season Aug-Sep; harvest_window Oct-Feb of
                                   season+1)
        severity_class            (minor: 34-47 kt = IMD Cyclonic Storm;
                                   severe: >= 48 kt = IMD Severe CS or stronger)
     The district x season exposure used by Protocol §3.8 is the maximum
     severity per timing class over all storms in that row set.

  2. docs/cyclone_footprints_ibtracs50km.csv
     For the six cyclones in the original footprint roster (Fani, Bulbul,
     Amphan, Yaas, Sitrang and Remal): every roster district with
     in_footprint (1 if severe exposure to that storm), fringe (1 if minor
     exposure to that storm), min distance to the storm's >= 34 kt track,
     clean_control (1 if the district has NO >= 48 kt exposure to ANY
     catalogued storm in the +/-1-season window around that cyclone's
     analysis year and is neither footprint nor fringe for it), and
     treated_other_severe_exposure (1 if a footprint district also has
     severe exposure to a DIFFERENT storm in t-1, t or t+1 — Protocol §3.8 B
     reports such stacks as descriptive contrasts conditional on prior/adjacent
     exposure, not as clean single-storm causal effects).

Rule (carried from Paper 1's 50-km IBTrACS exposure buffer, RSASE-D-26-02830
§2.3, and IMD's storm categories):
  * Track segments between consecutive IBTrACS fixes are buffered by 50 km in
    EPSG:7755 (India Lambert Conformal Conic). A segment is attributed the
    larger of its two endpoint winds. A district is exposed to a segment if
    its GADM v4.1 Level-2 polygon intersects the buffered segment.
  * Wind = WMO_WIND (IMD, kt); USA_WIND used only where WMO_WIND is missing.
  * Only fixes with BASIN == "NI" are used (Bulbul is catalogued as the
    trans-basin storm "BULBUL:MATMO"; its West-Pacific fixes are excluded).
  * A storm's season is its IBTrACS SEASON. Jan-Feb fixes therefore belong
    to the previous Kharif's harvest window only when SEASON is that year;
    no catalogued storm in 2016-2025 affects the roster in Jan-Feb.

Inputs (not committed): GADM v4.1 gadm41_IND_2.shp; IBTrACS v04r01 NI-basin
CSV (https://www.ncei.noaa.gov/data/international-best-track-archive-for-
climate-stewardship-ibtracs/v04r01/access/csv/ibtracs.NI.list.v04r01.csv).
Roster: docs/coastal_districts_gadm41.csv (Kolkata is kept in the tables but
is not extracted, per Protocol §1.3).

Usage:
  python python/build_cyclone_exposure.py ROSTER_CSV GADM_L2_SHP IBTRACS_CSV OUT_DIR
"""
import sys
import numpy as np
import pandas as pd

import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
import geopandas as gpd
from shapely.geometry import LineString

ROSTER_CSV, GADM_SHP, IBTRACS_CSV, OUT_DIR = sys.argv[1:5]

# Buffer and severity threshold are PARAMETERS as of 2026-09-13, with the frozen
# values as defaults, so §3.8 A's declared robustness arms -- "exposure buffer
# 75 km and 100 km in place of 50 km; severity threshold 64 kt (IMD Very Severe
# Cyclonic Storm) in place of 48 kt" -- are produced by THIS rule rather than by
# a second implementation of it. Omitting both arguments reproduces the committed
# exposure catalogue when the source snapshot and environment agree. The
# robustness_arms.py --rebuild gate checks this rather than assuming it.
BUFFER_KM  = float(sys.argv[5]) if len(sys.argv) > 5 else 50.0
SCS_KT     = float(sys.argv[6]) if len(sys.argv) > 6 else 48.0
BUFFER_M   = BUFFER_KM * 1000.0
CS_KT      = 34.0      # IMD Cyclonic Storm, the floor for any exposure at all
# Column names and file names carry the frozen 50 km / 48 kt spelling when the
# defaults are in force, so nothing downstream changes; a variant gets its own
# suffix and its own column name so a variant file can never be mistaken for the
# committed one by a reader or by a script.
FROZEN     = (BUFFER_KM == 50.0 and SCS_KT == 48.0)
WIND_COL   = "max_wind_kt_within_%dkm" % int(round(BUFFER_KM))
DIST_COL   = "min_dist_to_track34kt_km"
SUFFIX     = ("ibtracs50km" if FROZEN
              else "ibtracs%dkm_%dkt" % (int(round(BUFFER_KM)), int(round(SCS_KT))))
CRS_METRIC = "EPSG:7755"
SEASONS    = range(2016, 2026)

NAMED = [  # Protocol §1.1
    ("Fani",    "2019116N02090", 2019),
    ("Bulbul",  "2019302N11118", 2019),
    ("Amphan",  "2020136N10088", 2020),
    ("Yaas",    "2021143N15090", 2021),
    ("Sitrang", "2022295N13093", 2022),
    ("Remal",   "2024145N14087", 2024),
]

def timing(month):
    if 4 <= month <= 7:  return "pre_season"
    if 8 <= month <= 9:  return "mid_season"
    return "harvest_window"      # Oct-Dec, and Jan-Feb of the following year

roster = pd.read_csv(ROSTER_CSV)
gadm = gpd.read_file(GADM_SHP)
g = roster.merge(gadm[["NAME_1", "NAME_2", "geometry"]],
                 left_on=["state", "district_gadm_name"],
                 right_on=["NAME_1", "NAME_2"], how="left")
if g["geometry"].isna().any():
    raise SystemExit("roster/GADM name mismatch: " +
                     str(g[g.geometry.isna()][["state", "district_gadm_name"]].values.tolist()))
g = gpd.GeoDataFrame(g, geometry="geometry", crs=gadm.crs).to_crs(CRS_METRIC).reset_index(drop=True)

ib = pd.read_csv(IBTRACS_CSV, skiprows=[1], low_memory=False)
ib = ib[(ib["BASIN"] == "NI") & (ib["SEASON"].astype(int).isin(SEASONS))].copy()
for c in ("WMO_WIND", "USA_WIND", "LAT", "LON"):
    ib[c] = pd.to_numeric(ib[c], errors="coerce")
ib["wind"] = ib["WMO_WIND"].where(ib["WMO_WIND"].notna(), ib["USA_WIND"])

rows = []
for sid, d in ib.groupby("SID"):
    d = d.sort_values("ISO_TIME").reset_index(drop=True)
    pts = gpd.GeoSeries(gpd.points_from_xy(d["LON"], d["LAT"]), crs="EPSG:4326").to_crs(CRS_METRIC)
    w = d["wind"].values
    best = {}   # district index -> (max wind, iso_time of that segment, dist km)
    mind = {}   # district index -> min distance to any >= 34 kt segment
    for i in range(len(d) - 1):
        if np.isnan(w[i]) and np.isnan(w[i + 1]):
            continue
        ww = np.nanmax([w[i], w[i + 1]])
        if ww < CS_KT:
            continue
        seg = LineString([pts.iloc[i], pts.iloc[i + 1]])
        buf = seg.buffer(BUFFER_M)
        for di in g.index[g.intersects(buf)]:
            dist = g.geometry.iloc[di].distance(seg) / 1000.0
            mind[di] = min(dist, mind.get(di, dist))
            prev = best.get(di)
            if prev is None or ww > prev[0] or (ww == prev[0] and dist < prev[2]):
                best[di] = (ww, d["ISO_TIME"].iloc[i], dist)
    for di, (ww, t, dist) in best.items():
        month = int(t[5:7])
        rows.append({
            "state": g.loc[di, "state"], "district_gadm_name": g.loc[di, "district_gadm_name"],
            "season": int(d["SEASON"].iloc[0]), "sid": sid, "storm_name": d["NAME"].iloc[0],
            WIND_COL: int(ww), "maxwind_fix_iso_time": t,
            "maxwind_fix_month": month, "timing_class": timing(month),
            "severity_class": "severe" if ww >= SCS_KT else "minor",
            "maxwind_segment_dist_km": round(dist, 1),
            "min_dist_to_track34kt_km": round(mind[di], 1),
        })

exp = pd.DataFrame(rows).sort_values(["season", "sid", "state", "district_gadm_name"])
exp.to_csv(f"{OUT_DIR}/district_cyclone_exposure_{SUFFIX}.csv", index=False)
print(f"buffer {BUFFER_KM:.0f} km, severe >= {SCS_KT:.0f} kt -> suffix {SUFFIX}")
print(f"exposure rows: {len(exp)}  storms: {exp.sid.nunique()}  seasons: {sorted(exp.season.unique())}")

# ---- original six-cyclone footprint roster / fringe / clean controls --------
# Titli entered later when the panel floor moved to 2017. event_study.py derives
# Titli from the full exposure catalogue and verifies the same derivation against
# this file for the five estimable cyclones it contains.
sev = exp[exp["severity_class"] == "severe"]
sev_dy = set(zip(sev["state"], sev["district_gadm_name"], sev["season"]))
sev_dys = set(zip(sev["state"], sev["district_gadm_name"], sev["season"], sev["sid"]))
fp_rows = []
for cyc, sid, ay in NAMED:
    e = exp[exp["sid"] == sid].set_index(["state", "district_gadm_name"])
    for _, r in g.iterrows():
        key = (r["state"], r["district_gadm_name"])
        if key in e.index:
            ww = int(e.loc[key, WIND_COL]); dist = float(e.loc[key, DIST_COL])
        else:
            ww, dist = 0, np.nan
        infp = int(ww >= SCS_KT); fringe = int(CS_KT <= ww < SCS_KT)
        window = [y for y in (ay - 1, ay, ay + 1) if y in SEASONS]
        contaminated = any((key[0], key[1], y) in sev_dy for y in window)
        clean = int(not infp and not fringe and not contaminated)
        other = int(infp and any(st == key[0] and dn == key[1] and y in window and s != sid
                                 for (st, dn, y, s) in sev_dys))
        fp_rows.append({"cyclone": cyc, "ibtracs_sid": sid, "analysis_year": ay,
                        "state": key[0], "district_gadm_name": key[1],
                        WIND_COL: ww, DIST_COL: dist,
                        "in_footprint": infp, "fringe": fringe, "clean_control": clean,
                        "treated_other_severe_exposure": other})
fp = pd.DataFrame(fp_rows)
fp.to_csv(f"{OUT_DIR}/cyclone_footprints_{SUFFIX}.csv", index=False)

print(f"\nNamed cyclones — footprint (>= {SCS_KT:.0f} kt within {BUFFER_KM:.0f} km), fringe ({CS_KT:.0f}-{SCS_KT-1:.0f} kt), clean controls "
      f"(no >= {SCS_KT:.0f} kt exposure to any storm in t-1..t+1); Kolkata excluded from counts:")
for cyc, sid, ay in NAMED:
    s = fp[(fp.cyclone == cyc) & (fp.district_gadm_name != "Kolkata")]
    def by_state(mask):
        return {st: int(((s.state == st) & mask).sum()) for st in ("Odisha", "West Bengal", "Andhra Pradesh")}
    print(f"  {cyc:8s} {ay}: footprint {int(s.in_footprint.sum()):2d} {by_state(s.in_footprint == 1)} | "
          f"fringe {int(s.fringe.sum())} | clean {int(s.clean_control.sum()):2d} {by_state(s.clean_control == 1)}")
    print("             treated:", ", ".join(sorted(s[s.in_footprint == 1].district_gadm_name)) or "(none)")
    print(f"             footprint districts with other severe exposure in t-1..t+1: "
          f"{int(s.treated_other_severe_exposure.sum())}")
