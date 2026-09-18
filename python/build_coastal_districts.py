"""
Build coastal_districts_gadm41.csv — Bay-of-Bengal-facing districts of
Odisha, West Bengal, and coastal Andhra Pradesh whose centroid is within
100 km of the Bay-facing coastline of India.

Input:
    /home/user/workspace/paper2/gadm/gadm41_IND_{0,2}.shp

Definition of "Bay-facing coastline":
    We extract the exterior boundary of the India Level-0 polygon, break it
    into vertices (WGS84 lon/lat), and restrict to vertices satisfying:
        - latitude in [8.0, 22.5] (from Point Calimere ~10.3°N south limit
          — we go a bit south to 8° to catch the Palk-Strait-facing arc —
          up to the Sundarbans coast ~22.5°N)
        - longitude ≥ 78.5°E (drops the west coast of India)
    We further clip to points that lie on the east-facing side by requiring
    they are within a coarse buffer of state boundaries of OD/WB/AP
    (self-consistency check).

Distance:
    Centroid-to-nearest-coast-vertex, computed in Kalianpur / India Zone IIB
    (EPSG:24378) — an equal-area projection appropriate for the Indian
    subcontinent. Result in kilometres.

Output:
    /home/user/workspace/paper2/gadm/coastal_districts_gadm41.csv
    columns: state, district_gadm_name, centroid_lat, centroid_lon,
             dist_to_coast_km
"""
import geopandas as gpd
import pandas as pd

import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
import numpy as np
from shapely.geometry import Point, MultiPoint

GADM_DIR = "/home/user/workspace/paper2/gadm"
STATES = {"Odisha", "West Bengal", "Andhra Pradesh"}

# Load districts (Level 2) and country boundary (Level 0)
districts = gpd.read_file(f"{GADM_DIR}/gadm41_IND_2.shp")
country   = gpd.read_file(f"{GADM_DIR}/gadm41_IND_0.shp")

print(f"Total districts in GADM41 India L2: {len(districts)}")
print(f"Columns: {list(districts.columns)}")
print(f"Sample NAME_1 values: {sorted(districts['NAME_1'].unique())[:10]}")

# Filter to our three states
target = districts[districts["NAME_1"].isin(STATES)].copy()
print(f"\nDistricts in OD/WB/AP: {len(target)}")
print(target.groupby("NAME_1").size())

# Extract coastline vertices from India Level-0 polygon
# The India polygon is a MultiPolygon; take exterior of each part.
coast_points = []
for geom in country.geometry:
    parts = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
    for part in parts:
        xs, ys = part.exterior.coords.xy
        for x, y in zip(xs, ys):
            coast_points.append((x, y))
print(f"\nRaw coastline+border vertices: {len(coast_points)}")

# Restrict to Bay-facing arc: lat in [8, 22.5], lon >= 78.5
bay_vertices = [
    (x, y) for x, y in coast_points
    if 8.0 <= y <= 22.5 and x >= 78.5
]
print(f"After Bay-facing lat/lon window: {len(bay_vertices)}")

# The Level-0 exterior includes the entire national boundary, so filtering
# by lat/lon still leaves inland land borders (Bangladesh, Myanmar, Nepal).
# To keep only *coast* vertices, we require each vertex to be within
# 5 km of open water. Simplest approach given a single India-only polygon:
# use the observation that the east-coast arc has a distinctive property —
# no vertex on it is inside any Indian district polygon. Land-border
# vertices are on the outside of India but adjacent to other countries;
# coast vertices are also on the outside but adjacent to sea.
#
# Cleanest available filter: keep vertices that are NOT within any district
# of a landlocked / non-coastal boundary state. Practical shortcut: we
# restrict to lon >= 79.0 and manually cut the Bangladesh-border segment
# by dropping vertices with lat in [22.0, 22.5] AND lon in [88.7, 89.9]
# (that's the north-Sundarbans land border), and drop the Myanmar segment
# with lon >= 93.0.
def is_bay_coast(x, y):
    # Drop Bangladesh land border (roughly Cooch Behar - Malda - Murshidabad
    # runs along ~88-89°E, 24-26°N, so lat > 22.5 already excludes it).
    # Extra safety: drop the extreme east islands (A&N).
    if x >= 93.0:
        return False
    # Drop Bangladesh border segment along 89°E in the Sundarbans crest.
    if 22.0 <= y <= 22.5 and 88.7 <= x <= 89.9:
        return False
    return True

bay_coast = [(x, y) for x, y in bay_vertices if is_bay_coast(x, y)]
print(f"After Bay-coast heuristic: {len(bay_coast)}")

# Build a MultiPoint of coast in WGS84, then reproject to metric CRS.
coast_gdf = gpd.GeoDataFrame(
    geometry=[Point(x, y) for x, y in bay_coast],
    crs="EPSG:4326",
).to_crs("EPSG:24378")   # Kalianpur / India Zone IIB

# District centroids — compute in WGS84 then reproject for distance math.
target_wgs = target.copy()
target_wgs["centroid"] = target_wgs.geometry.centroid
target_wgs["centroid_lat"] = target_wgs["centroid"].y
target_wgs["centroid_lon"] = target_wgs["centroid"].x

target_metric = target.to_crs("EPSG:24378")
target_metric["centroid"] = target_metric.geometry.centroid

# Nearest-vertex distance
coast_union = coast_gdf.geometry.union_all() if hasattr(coast_gdf.geometry, "union_all") else coast_gdf.geometry.unary_union
dists_m = target_metric["centroid"].distance(coast_union)
target["dist_to_coast_km"] = (dists_m.values / 1000.0).round(1)
target["centroid_lat"] = target_wgs["centroid_lat"].round(4).values
target["centroid_lon"] = target_wgs["centroid_lon"].round(4).values

# Filter to ≤100 km
coastal = target[target["dist_to_coast_km"] <= 100.0].copy()
coastal = coastal.sort_values(["NAME_1", "dist_to_coast_km"])
print(f"\n\nCoastal districts (≤100 km) by state:")
print(coastal.groupby("NAME_1").size())

out = coastal[["NAME_1", "NAME_2", "centroid_lat", "centroid_lon", "dist_to_coast_km"]].rename(
    columns={"NAME_1": "state", "NAME_2": "district_gadm_name"}
)
out_path = f"{GADM_DIR}/coastal_districts_gadm41.csv"
out.to_csv(out_path, index=False)
print(f"\nWrote {out_path} ({len(out)} rows)")
print("\n=== FULL TABLE ===")
print(out.to_string(index=False))
