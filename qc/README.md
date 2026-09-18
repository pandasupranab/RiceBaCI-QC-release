# /qc — UNUSED. No such stage exists in the current design.

**This directory is empty and produces nothing.**

Rewritten 2026-09-13. The previous version, dated 2026-09-04, described outputs from
`python/gate1_peak_relative.py` and `python/sar_witness.py` — `gate1_admitted_bins.csv`,
`gate2_phenometric_bounds.csv`, `sar_tp_by_district.csv`, `gate_diagnostics.json`.
**Neither script exists and none of those files exists.** They belonged to the
Sentinel-2 design, in which a peak-relative Gate-1 screened optical bins before
phenometrics were fitted.

Under the Sentinel-1 substrate the equivalent screening is inside the estimator
rather than a separate stage: `python/extract_phenometrics_sar.py` applies the fit
criteria and writes `retained` per pixel-season into the panel, with the failures
itemised in `results/phen_panel_sar_failures.csv`. §3.10's attrition diagnostics then
model that retention directly — see `results/s310_v2_district/` and
`results/s310_v2_pixel/`.

The substrate change is dated in `analysis/deviation_log.md`. The directory is kept
so this note has somewhere to live.
