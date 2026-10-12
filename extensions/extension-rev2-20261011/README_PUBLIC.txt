Paper 2 post-hoc extension: shuffled-pair benchmark and wider-search sensitivity
Public-release preparation, 12 October 2026

Creators: Supranab Panda (ORCID 0009-0009-6496-6545) and Sarat Chandra Sahu (ORCID 0000-0002-8048-1910)
Prepared version label: extension-rev2-20261011

This package preserves the accepted scientific contents of Extension_2026-10-11_shuffle_freegrid_rev2. It is a supplementary extension to the original Paper 2 analysis, not a replacement of the original code, results, hypotheses or verdicts. The two additions were designed after the original results were known and are descriptive. They do not establish field accuracy, a biological timing signal or a causal cyclone effect.

The original analysis remains frozen at:
https://github.com/pandasupranab/RiceBaCI-QC-release/tree/a465400e7eb7ec05f7c7d819ab14303cc14146d9
Tag: v1.0.0
Original raw inputs and replay archive: https://doi.org/10.5281/zenodo.22750338
Original archive version: v1.0.0-data-20260918

Contents

PLAN_FROZEN_2026-10-10.md: the post-hoc extension plan frozen before its computation
scripts/: accepted extension code and source-validation checks
release_src/: byte-verified snapshot of 59 original released files
calibration/: wider-grid critical values and calibration identity records
results/: shuffled-pair benchmark, free-grid fits, comparison statistics and pilot outputs
preflight/ and logs/: technical validation and computation records
inputs/: source identities and comparison inputs (the two large external inputs remain in the original public deposit)
RESULTS_SUMMARY.md: descriptive interpretation and limitations of the additions
MANIFEST_PUBLIC_SHA256.txt: SHA-256, bytes and relative path for every other public-package member

Scope of packaging

All scientific source files, calibration tables, result tables, fit caches, frozen plan and technical validation records retained in this public archive are byte-identical to the accepted revision-2 computation package. Its original full-package SHA-256 is:
8e937ed219d08dee13abd9d26a777093c3ce2dc56979e73c768f0a9ed37a61cb

Internal Codex review notes and the internal change log were not included. Their original copies are preserved by the authors. The original internal README/manifest were replaced with this public-facing description and a new public manifest. The public-package hash consequently differs from the original computation-package hash. No scientific calculation or result was changed for publication.

External inputs required for replay

1. 225 per-orbit Sentinel-1 exports, members work/inputs/s1_perorbit/S1_ORBIT_*.csv of Paper2_raw_inputs_2017-2025.zip in the original public deposit. Archive SHA-256:
3de6690fc512bf7cf96994d93df1c191d9ce8e6351160869c53cb1f9ffa3cbf0
Extract to inputs/raw_zip/work/inputs/s1_perorbit/.

2. Restricted-grid fit cache, member reference_inputs/results/orbit_agreement/per_orbit_fits.csv of Paper2_replay_inputs_a465400.zip in the original public deposit. Input-cache SHA-256:
31b96b6ea2521dce7ee4b9adabd32d9870ea34fff88468e20084073e49f089cf
Place at inputs/staged/per_orbit_fits.csv. The replay-input ZIP SHA-256 is:
63f8550ffb21442ede40596e621f3196dc4c965af25ea3a52434c2546c321699

The exact identities of individual raw inputs are retained in inputs/staged/*.manifest.json. Missing inputs are not replaced by placeholders.

Replay

Create an isolated environment with numpy==2.4.4 and pandas==3.0.2. The original extension ran in Linux/Python 3.13.16; the recorded restricted-grid replay and bounded Windows checks are evidence for those checks, not a universal cross-platform guarantee.

From the extracted package root, first validate the frozen sources:
python -I -B scripts/validate_release_src.py
python -I -B scripts/preflight.py

Only after those pass, the original extension computation can be reproduced:
python -I -B scripts/calibrate_pixel_free.py --jobs 2
python -I -B scripts/shuffled_pair_benchmark.py
python -I -B scripts/fit_free_grid.py --jobs 2
python -I -B scripts/grid_sensitivity_compare.py

The computations overwrite their output directories. Use a disposable extracted copy and compare to the delivered manifest. Publication preparation did not rerun these computations.

Licence scope

Author-owned extension code is MIT. Author-created data, result tables and documentation are CC BY 4.0. Existing copyright/licence notices and third-party terms in the frozen source snapshot remain intact. See LICENSE_CODE_MIT.txt and LICENSE_SCOPE.txt. No publisher PDFs or GADM shapefile bundle is included. The large raw inputs are not duplicated; they remain available through the original public deposit.

Archive/repository identifiers for this extension are supplied by the actual publication record, not guessed in this README. A prepared release is not a claim of publication or journal acceptance.
