# /python — Python pipeline

> **HISTORICAL PLANNING FILE — not the current module roster.** The table below
> records an early plan, including modules that were never created. The
> executable source set is the tracked contents of this directory; the current
> self-test roster is derived by `run_all.sh` rather than from this table.

This folder will host the Python pipeline that consumes GEE exports and produces the analysis-ready panel + statistical outputs.

Planned modules (in build order during Week 2):

| File | Purpose | Status |
|---|---|---|
| `panel_build.py` | Join GEE exports into balanced district × year × phenometric panel | planned (Day 6) |
| `gate1_peak_relative.py` | Apply phenometric-aware r-values (0.75 SOS / 0.50 peak / 0.50 EOS) | planned (Day 6) — core contribution |
| `did_estimator.py` | Two-way fixed-effects DiD with wild-cluster bootstrap | planned (Day 7) |
| `event_study.py` | Pre-trend test + dynamic treatment effects | planned (Day 7) |
| `validator_tier1.py` | Sentinel-2 vs. Landsat HLS 30 m pixel-level RMSE | planned (Day 8) |
| `validator_tier2.py` | Sentinel-2 vs. MODIS MOD13Q1 district-level Spearman ρ | planned (Day 8) |
| `sar_witness.py` | Bouvet 2018 SAR transplanting-date detection + agreement table | planned (Day 9) |

Dependencies are recorded at repository root in `requirements.txt`; the
reproducibility harness is the root-level `run_all.sh`. The executable analysis
and figure environment checks pass in the recorded test environment, but the
repository has no lockfile or container image and therefore does not promise
cross-environment byte or pixel identity. That remains a disclosed
reproducibility limitation, not a pending numerical test.
