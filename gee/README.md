# /gee — Google Earth Engine modules

> **HISTORICAL PLANNING FILE.** This table is not the executed Paper 2 design.
> In particular, the planned “Bouvet 2018” witness refers to a bibliographic
> identity that could not be resolved and is withdrawn in
> `docs/LitGap_v0.2.md`. Use `docs/Protocol_v1.md` and the tracked executable
> scripts for current methods.

This folder will host the Earth Engine JavaScript modules that produce the upstream exports for `/python` and `/qc`.

Planned modules (in build order during Week 1–2):

| File | Purpose | Status |
|---|---|---|
| `S2_QC_Ingest.js` | Sentinel-2 L2A SCL + s2cloudless filter; 5-day median composites; export per district × year | planned (Day 3) |
| `HLS_QC_Ingest.js` | Landsat HLS L30 + S30 Fmask; 30 m export for Tier 1 validation | planned (Day 4) |
| `MOD13Q1_District_Median.js` | MODIS 16-day NDVI district medians for Tier 2 coherence | planned (Day 4) |
| `S1_VH_Transplanting.js` | Bouvet 2018 VH local-minimum detection for SAR sanity check | planned (Day 5) |
| `BalancedPixel_Cell_Export.js` | Spatial-balanced pixel selection (carried from Paper 1 Module 04b) | port from Paper 1 |

Each module will export results to `gs://ricebaci-qc/exports/` (private bucket) and to local Drive for offline reproducibility.
