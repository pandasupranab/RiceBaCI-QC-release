# Results summary — extension of 10 October 2026 (revision 2, 11 October 2026)

Revision 2 changes only documentation: the universal reading-guide sentence
in §2 is replaced by a pooled-evaluation statement that names the baseline
Andhra Pradesh exceptions (Codex extension review, 11 Oct 2026, required
correction 2); §0 records the fail-closed in-place source validation that
replaced the 2026-10-10 staging block (required correction 1). No number,
table, CSV, calibration or fit file changed; `MANIFEST_sha256.txt` shows the
scientific outputs byte-identical to the 10 October archive.

Everything below is descriptive. No test was run, no threshold applied, no
cause identified, and no published number, table or verdict changed. Both
additions are post-hoc: the published outcomes were known before they were
designed. The frozen plan (`PLAN_FROZEN_2026-10-10.md`) and Codex's review
(`CODEX_PAPER2_STRENGTHENING_REVIEW_2026-10-10.txt`) govern what was computed.
Full tables are the CSV files named in `README.md`; the tables here are
extracts generated from those files.

## 0. Preflight (20 checks, all passed; `preflight/PREFLIGHT_REPORT.json`, `logs/preflight_transcript.txt`; the 10 October run's record is kept in `preflight/original_run_2026-10-10/` and `logs/original_run_2026-10-10/`)

Release sources: `release_src/` holds exactly the recorded 59 files, every git
blob SHA-1 equal to the v1.0.0 tree, no extra file, validated in place without
copying, removing or modifying anything (`scripts/validate_release_src.py`;
the absent/empty/missing/extra/changed/CRLF/symlink/bytecode-cache cases each
stop with exit 2 and leave the copy intact: `preflight/REPLAY_VALIDATION_TESTS.json`,
`logs/replay_validation_tests_transcript.txt`, 25 of 25 cases).
Per-orbit exports: 225 files, 295,007,797 bytes, every SHA-256 equal to the
deposit manifest. G0 cache and released `orbit_pairs.csv`: SHA-256 equal to
the replay-inputs manifest and to the submitted evidence snapshot / ledger.
Structure: 8,515 pairs (798 + 7,717), unique keys, no missing differences;
383 evaluation cells, 342 eligible holding 7,676 rows, 41 singletons, 26
two-row cells, 6,409 A/D + 1,267 same-pass eligible rows, 21 districts;
baseline 47 cells, 41 eligible holding 792 rows; cache 170,321 series,
44,659 retained, 90,000 pixel-seasons, 12 orbits, unique keys; every published
pair joins to retained cache rows with identical markers. Designs: 12,649
free, 4,322 restricted, restricted a subset with identical matrices. The
released lookup returns the district AR(1) value 4.1732 for "free" and the
3.5 fallback for an unknown key; neither is used for G2. The extension's
strict lookup stops on a missing row, a missing key and an absent table; the
fit routine stops on a wrong design count. G0 replay: 6,837 series in 8
export files (2,090 retained, 4,747 rejected, 1,177 bound-touching retained
marker positions) reproduced row for row (flags, reasons and markers exact;
rise and rmse to 1e-9). The released pair builder applied to the cache
reproduces the released `orbit_pairs.csv` in every column.

## 1. Calibration for G2 (`calibration/`)

Grid key `pixel_free`; i.i.d. Gaussian null (rho = 0; the released
pixel-level choice, an assumption of the noise/missingness model); n_valid
14–28; 4,000 draws per cell; seeds 2000 + n_valid; the released
`calibrate_plsm_null.one_cell` called with grid = "free", which dispatches to
`plsm_designs_free()` (12,649 designs). t95 runs from 3.249 (n_valid 27) to
3.401 (n_valid 21) against the released restricted-grid values of about
2.73–2.96: the wider search raises the selection-aware critical value. A
second call with the released 1,500 draws reproduced all 13 released
free-grid rows (n_valid 16–28) exactly, t95 and n_fit. 35.8 min with two
workers (the machine was shared with Addition A for about ten minutes).

## 2. Addition A — different-pixel benchmark on the released pairs (`results/A_shuffled_pair_benchmark/`)

Input: released `orbit_pairs.csv` (SHA-256 1327f06c…). The observed
statistics computed by the extension on the full released sample equal
Table S1 in every scope and column (`A_observed_full_sample_check.csv`).
Eligible sample: 7,676 evaluation rows in 342 cells (41 singleton rows
excluded from both arms; 26 cells have two rows and therefore a single
derangement with no randomisation variation), 21 districts; baseline 792
rows in 41 cells (2 two-row cells), 18 districts. R = 1,000 derangement
draws per cell (seed 20261010; uniform permutations by rejection, 2.68 tries
per accepted draw; the three orbit-b markers travel together). Bootstrap:
2,000 district-cluster replicates (seed 20261011), K = 50 draws inside each,
instance-indexed draws for duplicated districts (maximum multiplicity 7
evaluation, 6 baseline). The Monte Carlo standard error of each benchmark
mean at R = 1,000 is in the CSV (`bench_mc_se`; ≤ 0.005 d for sd(diff)/√2
on the ALL scope) and is separate from the bootstrap intervals; it does not
measure the K = 50 approximation used inside the bootstrap replicates, which
is not separately quantified. Timings:
pool 7.2 s, statistics 4.8 s, bootstrap 558 s (evaluation) and 58 s
(baseline); 631 s in all on a shared machine.

The mean signed difference is identical in both arms by construction (the
derangement preserves each cell's orbit-b mean), so the benchmark isolates
dispersion from the directional offset. "band" = 2.5th–97.5th percentile of
the benchmark over the 1,000 draws (a random-mismatching reference band, not
a confidence interval); "boot 95%" = district-cluster bootstrap percentile
interval of the observed − benchmark-mean difference. By-year scopes are in
the CSV.

### Addition A tables

**evaluation**

| scope | marker | n | sd(diff)/√2 obs / bench [band] | diff (d) [boot 95%] | within 10 d obs / bench (%) | diff (pp) [boot 95%] | within 20 d obs / bench (%) | within fixed T obs / bench (%) | median \|diff\| obs / bench | r obs / bench |
|---|---|---:|---|---|---|---|---|---|---|---|
| ALL | t1 | 7,676 | 25.89 / 29.51 [29.21, 29.82] | -3.62 [-4.13, -3.13] | 38.2 / 28.5 | +9.7 [+8.5, +11.1] | 55.7 / 44.9 | 94.4 / 92.4 | 20 / 30.0 | +0.338 / +0.139 |
| ALL | t2 | 7,676 | 19.82 / 22.14 [21.91, 22.39] | -2.32 [-2.75, -1.98] | 45.3 / 36.5 | +8.8 [+7.3, +10.5] | 64.6 / 56.2 | 93.9 / 91.9 | 20 / 20.0 | +0.289 / +0.112 |
| ALL | t4 | 7,676 | 25.77 / 27.42 [27.12, 27.70] | -1.65 [-2.31, -1.03] | 35.0 / 30.4 | +4.6 [+2.9, +6.4] | 52.1 / 47.0 | 91.2 / 89.5 | 20 / 30.0 | +0.146 / +0.033 |
| Andhra Pradesh | t1 | 186 | 28.06 / 32.87 [31.00, 34.69] | -4.81 [-11.44, 2.04] | 34.9 / 23.1 | +11.9 [+4.7, +16.7] | 51.1 / 39.1 | 94.6 / 89.6 | 20 / 32.2 | +0.227 / -0.061 |
| Andhra Pradesh | t2 | 186 | 21.54 / 22.72 [21.06, 24.23] | -1.18 [-1.67, 1.10] | 45.2 / 37.1 | +8.1 [-25.0, +11.7] | 65.6 / 56.8 | 91.9 / 91.2 | 20 / 20.1 | +0.162 / +0.067 |
| Andhra Pradesh | t4 | 186 | 29.88 / 32.81 [30.71, 34.67] | -2.93 [-7.27, -2.16] | 33.3 / 26.8 | +6.5 [-0.3, +21.6] | 52.7 / 41.6 | 85.5 / 80.3 | 20 / 30.3 | +0.152 / -0.023 |
| Odisha | t1 | 4,637 | 26.75 / 30.06 [29.66, 30.46] | -3.31 [-3.76, -2.70] | 35.9 / 27.4 | +8.4 [+7.1, +10.2] | 52.9 / 43.2 | 94.0 / 92.0 | 20 / 30.0 | +0.288 / +0.100 |
| Odisha | t2 | 4,637 | 20.39 / 22.52 [22.20, 22.83] | -2.12 [-2.48, -1.93] | 43.0 / 35.7 | +7.3 [+6.0, +8.6] | 62.8 / 55.2 | 93.1 / 91.1 | 20 / 20.0 | +0.234 / +0.066 |
| Odisha | t4 | 4,637 | 25.52 / 26.51 [26.15, 26.86] | -0.99 [-1.72, -0.47] | 34.0 / 30.8 | +3.2 [+1.8, +5.0] | 51.0 / 47.8 | 91.9 / 91.1 | 20 / 29.8 | +0.086 / +0.013 |
| West Bengal | t1 | 2,853 | 24.20 / 28.31 [27.78, 28.82] | -4.10 [-5.23, -3.08] | 42.3 / 30.6 | +11.7 [+10.1, +13.8] | 60.6 / 48.0 | 95.1 / 93.3 | 20 / 30.0 | +0.401 / +0.179 |
| West Bengal | t2 | 2,853 | 18.69 / 21.45 [21.08, 21.82] | -2.76 [-3.84, -1.76] | 48.9 / 37.7 | +11.2 [+8.6, +15.0] | 67.5 / 57.7 | 95.3 / 93.2 | 20 / 20.0 | +0.336 / +0.125 |
| West Bengal | t4 | 2,853 | 25.80 / 28.38 [27.86, 28.91] | -2.58 [-3.73, -1.49] | 36.8 / 30.0 | +6.8 [+3.5, +9.2] | 53.8 / 46.2 | 90.3 / 87.4 | 20 / 30.0 | +0.209 / +0.042 |
| ASC/DESC pairs only | t1 | 6,409 | 25.45 / 29.13 [28.78, 29.48] | -3.68 [-4.17, -3.21] | 38.7 / 29.0 | +9.8 [+8.6, +11.2] | 56.6 / 45.5 | 94.6 / 92.7 | 20 / 30.0 | +0.350 / +0.146 |
| ASC/DESC pairs only | t2 | 6,409 | 19.57 / 21.85 [21.58, 22.11] | -2.28 [-2.74, -1.88] | 45.7 / 36.9 | +8.8 [+7.1, +10.7] | 64.9 / 56.7 | 94.2 / 92.3 | 20 / 20.0 | +0.295 / +0.120 |
| ASC/DESC pairs only | t4 | 6,409 | 25.69 / 27.29 [26.95, 27.59] | -1.60 [-2.22, -0.93] | 35.1 / 30.6 | +4.4 [+2.7, +6.1] | 51.9 / 47.1 | 91.3 / 89.6 | 20 / 30.0 | +0.143 / +0.033 |
| same-pass pairs only | t1 | 1,267 | 27.97 / 31.35 [30.63, 31.99] | -3.37 [-4.60, -2.12] | 35.8 / 26.4 | +9.4 [+7.2, +11.5] | 51.4 / 41.8 | 93.5 / 91.1 | 20 / 30.0 | +0.261 / +0.072 |
| same-pass pairs only | t2 | 1,267 | 20.98 / 23.51 [22.89, 24.16] | -2.53 [-3.35, -1.67] | 43.2 / 34.3 | +8.9 [+6.4, +11.6] | 63.1 / 53.7 | 92.3 / 89.9 | 20 / 20.0 | +0.260 / +0.070 |
| same-pass pairs only | t4 | 1,267 | 26.18 / 28.03 [27.33, 28.75] | -1.86 [-3.50, -0.72] | 35.0 / 29.5 | +5.5 [+2.6, +8.9] | 53.0 / 46.5 | 90.7 / 88.7 | 20 / 29.9 | +0.161 / +0.038 |

**baseline**

| scope | marker | n | sd(diff)/√2 obs / bench [band] | diff (d) [boot 95%] | within 10 d obs / bench (%) | diff (pp) [boot 95%] | within 20 d obs / bench (%) | within fixed T obs / bench (%) | median \|diff\| obs / bench | r obs / bench |
|---|---|---:|---|---|---|---|---|---|---|---|
| ALL | t1 | 792 | 27.81 / 31.97 [31.02, 33.01] | -4.16 [-5.01, -3.34] | 35.2 / 27.0 | +8.2 [+5.2, +11.9] | 52.5 / 42.5 | 92.9 / 88.9 | 20 / 30.0 | +0.312 / +0.089 |
| ALL | t2 | 792 | 20.19 / 22.86 [22.10, 23.60] | -2.67 [-3.54, -1.89] | 43.6 / 35.1 | +8.5 [+4.5, +12.0] | 61.9 / 53.3 | 93.4 / 91.5 | 20 / 20.1 | +0.305 / +0.107 |
| ALL | t4 | 792 | 25.95 / 28.55 [27.62, 29.51] | -2.60 [-3.85, -1.45] | 34.2 / 28.4 | +5.8 [+1.6, +10.6] | 50.5 / 42.8 | 90.0 / 87.7 | 20 / 30.0 | +0.228 / +0.065 |
| Andhra Pradesh | t1 | 13 | 26.07 / 33.61 [25.74, 40.88] | -7.55 [-30.00, -5.81] | 46.2 / 18.1 | +28.1 [+23.6, +50.0] | 46.2 / 32.7 | 100.0 / 90.7 | 30 / 35.5 | +0.389 / -0.040 |
| Andhra Pradesh | t2 | 13 | 18.61 / 21.22 [15.95, 25.75] | -2.61 [-3.31, 0.00] | 30.8 / 36.2 | -5.5 [-6.4, +0.0] | 69.2 / 59.4 | 92.3 / 90.4 | 20 / 21.0 | +0.214 / -0.071 |
| Andhra Pradesh | t4 | 13 | 31.50 / 25.43 [17.40, 32.41] | +6.07 [5.12, 10.00] | 23.1 / 37.9 | -14.9 [-50.0, -6.9] | 30.8 / 47.9 | 84.6 / 93.3 | 30 / 25.6 | -0.140 / +0.256 |
| Odisha | t1 | 508 | 29.36 / 33.41 [32.21, 34.66] | -4.06 [-5.17, -2.89] | 31.9 / 25.3 | +6.6 [+2.4, +10.7] | 49.0 / 39.7 | 91.5 / 87.1 | 30 / 31.1 | +0.278 / +0.063 |
| Odisha | t2 | 508 | 21.17 / 23.42 [22.43, 24.41] | -2.25 [-2.84, -1.62] | 40.9 / 33.7 | +7.3 [+2.6, +11.1] | 59.1 / 51.4 | 91.9 / 90.6 | 20 / 22.3 | +0.220 / +0.043 |
| Odisha | t4 | 508 | 25.36 / 27.56 [26.44, 28.71] | -2.21 [-3.86, -0.79] | 33.1 / 28.7 | +4.4 [-0.8, +10.4] | 49.8 / 43.1 | 91.5 / 89.4 | 28 / 30.0 | +0.166 / +0.014 |
| West Bengal | t1 | 271 | 24.69 / 28.94 [27.20, 30.62] | -4.25 [-5.83, -2.79] | 41.0 / 30.6 | +10.4 [+4.8, +20.1] | 59.4 / 48.2 | 95.2 / 92.2 | 20 / 27.5 | +0.377 / +0.143 |
| West Bengal | t2 | 271 | 18.15 / 21.74 [20.55, 22.99] | -3.59 [-6.24, -1.38] | 49.1 / 37.7 | +11.4 [+3.0, +20.1] | 66.8 / 56.4 | 96.3 / 93.3 | 20 / 20.1 | +0.425 / +0.174 |
| West Bengal | t4 | 271 | 26.72 / 30.40 [28.69, 32.10] | -3.68 [-7.07, -1.97] | 36.9 / 27.6 | +9.3 [+3.0, +21.2] | 52.8 / 41.8 | 87.5 / 84.1 | 20 / 30.1 | +0.264 / +0.046 |
| ASC/DESC pairs only | t1 | 666 | 26.28 / 30.78 [29.66, 31.94] | -4.51 [-5.74, -3.48] | 36.2 / 28.0 | +8.1 [+5.4, +11.3] | 54.2 / 44.1 | 93.2 / 89.5 | 20 / 30.0 | +0.354 / +0.113 |
| ASC/DESC pairs only | t2 | 666 | 19.85 / 22.51 [21.73, 23.27] | -2.66 [-3.83, -1.69] | 45.0 / 35.7 | +9.4 [+5.0, +13.1] | 62.6 / 53.8 | 94.1 / 92.1 | 20 / 20.1 | +0.317 / +0.119 |
| ASC/DESC pairs only | t4 | 666 | 26.14 / 28.70 [27.65, 29.73] | -2.56 [-4.07, -1.40] | 34.2 / 28.2 | +6.1 [+1.7, +11.6] | 50.0 / 42.2 | 89.3 / 87.4 | 24 / 30.0 | +0.219 / +0.058 |
| same-pass pairs only | t1 | 126 | 31.43 / 34.49 [31.66, 36.95] | -3.05 [-6.48, -0.43] | 30.2 / 21.5 | +8.6 [-0.6, +17.9] | 43.7 / 34.0 | 91.3 / 86.1 | 30 / 38.0 | +0.154 / -0.025 |
| same-pass pairs only | t2 | 126 | 21.91 / 24.64 [22.75, 26.53] | -2.74 [-3.84, -1.49] | 35.7 / 31.8 | +3.9 [-3.8, +11.5] | 57.9 / 50.2 | 89.7 / 88.2 | 20 / 24.8 | +0.256 / +0.056 |
| same-pass pairs only | t4 | 126 | 24.94 / 27.80 [25.42, 30.01] | -2.86 [-6.44, 0.38] | 34.1 / 29.9 | +4.2 [-4.9, +12.4] | 53.2 / 45.7 | 93.7 / 89.3 | 20 / 28.5 | +0.282 / +0.106 |

Reading guide, nothing more: in the pooled evaluation sample (ALL, 7,676
pairs, 21 districts) the same-pixel pairs have lower scaled disagreement and
larger within-10-day shares than the within-cell different-pixel benchmark
for all three markers; the size of that difference is what the table
reports (3.6 d, 2.3 d and 1.6 d of sd(diff)/√2 for t1, t2 and t4; 9.7, 8.8
and 4.6 percentage points within one dekad). The pattern is not universal
across subgroups: in the baseline Andhra Pradesh scope (13 pairs from two
districts) the observed t4 sd(diff)/√2 is 31.50 d against a benchmark mean of
25.43 d, the observed t4 within-10-day share 23.1% against 37.9%, and the
observed t2 within-10-day share 30.8% against 36.2% (rows kept as computed).
Subgroup rows with few pairs or few districts are shown for completeness,
not as population evidence. Pooled Pearson r is not zero under mismatching
because cells differ in their means. The benchmark is not a randomised
experiment and does not identify why the difference has the size it has
(Codex A1, A4).

## 3. Addition B — free grid G2 against the released restricted grid G0 (`results/B_free_grid/`)

G2 refit: all 170,321 per-orbit series, released `plsm_fit` on the 12,649
free designs through `fit_one_file_ext`, retention by the released screen
with the `pixel_free` table; own done-file; 225 export files in 3,363 s wall
with two workers (sum of per-file times 6,722 s; 39.5 ms per series;
`B_fit_timings.csv`). Pairs under G2 by the released marker-blind rule
(`orbit_pairs_pixel_free.csv`). Comparison 110 s.

**Retention and pairs.** G0: 44,659 of 170,321 series retained (26.2%),
8,515 pairs (798 baseline, 7,717 evaluation). G2: 37,790 retained (22.2%),
6,021 pairs (531 baseline, 5,490 evaluation). Failure reasons (G0 → G2):
ineligible 11,160 → 11,160; no admissible shape 22,196 → 8,147; rise not
significant 92,306 → 113,224. Pairs by year (G0 / G2): 2017 798/531, 2018
1,178/835, 2019 1,292/980, 2020 1,009/795, 2021 761/583, 2022 755/406, 2023
819/528, 2024 827/560, 2025 1,076/803 (`B_retention_accounting.csv`).

**Transitions of the 90,000 pixel-seasons.** Paired in both arms with the
same physical orbit pair (the common sample, a selected population): 5,114
(4,697 evaluation, 417 baseline). Paired in both with a different orbit pair:
249. Paired in G0 only: 3,152. Paired in G2 only: 658. Paired in neither:
80,827 (`B_transitions.csv`, also by year and state).

**Each arm on its own full evaluation sample** (`B_fullsample_stats.csv`).
The own-2017 tolerance is the 0.90 quantile of |diff| on that arm's own 2017
pairs (G0: 70/50/60 d on 798 pairs, as published; G2: 80/70/70 d on 531
pairs). It is reported beside the fixed-tolerance share because a wider
tolerance can conceal larger absolute disagreement (Codex B4); the fixed
70/50/60 d columns are the like-for-like ones.


### Addition B — full-sample statistics per arm (evaluation 2018–2025)

| arm | scope | marker | pairs | within fixed T (%) | own-2017 T (d) | within own T (%) | within 10 d (%) | within 20 d (%) | mean diff (d) | sd(diff)/√2 (d) | median \|diff\| | r |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| G0 | ALL | t1 | 7,717 | 94.4 | 70 | 94.4 | 38.2 | 55.6 | -5.63 | 25.90 | 20 | +0.339 |
| G2 | ALL | t1 | 5,490 | 92.0 | 80 | 94.8 | 37.6 | 54.5 | -5.83 | 28.56 | 20 | +0.338 |
| G0 | ALL | t2 | 7,717 | 93.9 | 50 | 93.9 | 45.3 | 64.6 | -3.64 | 19.82 | 20 | +0.290 |
| G2 | ALL | t2 | 5,490 | 84.2 | 70 | 92.3 | 38.3 | 55.2 | -3.27 | 29.42 | 20 | +0.268 |
| G0 | ALL | t4 | 7,717 | 91.1 | 60 | 91.1 | 35.0 | 52.1 | +1.39 | 25.79 | 20 | +0.147 |
| G2 | ALL | t4 | 5,490 | 87.5 | 70 | 92.0 | 33.1 | 49.9 | +2.32 | 30.64 | 28 | +0.131 |
| G0 | Andhra Pradesh | t1 | 195 | 94.9 | 70 | 94.9 | 34.9 | 50.8 | +1.28 | 27.97 | 20 | +0.240 |
| G2 | Andhra Pradesh | t1 | 159 | 90.6 | 80 | 95.6 | 37.1 | 51.6 | -0.25 | 30.22 | 20 | +0.236 |
| G0 | Andhra Pradesh | t2 | 195 | 91.8 | 50 | 91.8 | 44.6 | 64.1 | -3.44 | 21.75 | 20 | +0.175 |
| G2 | Andhra Pradesh | t2 | 159 | 76.7 | 70 | 87.4 | 32.7 | 51.6 | -3.52 | 35.12 | 20 | +0.206 |
| G0 | Andhra Pradesh | t4 | 195 | 85.6 | 60 | 85.6 | 32.8 | 52.8 | -2.55 | 29.93 | 20 | +0.162 |
| G2 | Andhra Pradesh | t4 | 159 | 79.2 | 70 | 84.3 | 32.7 | 47.2 | -0.47 | 36.85 | 28 | +0.159 |
| G0 | Odisha | t1 | 4,656 | 94.0 | 70 | 94.0 | 35.8 | 52.8 | -6.54 | 26.77 | 20 | +0.288 |
| G2 | Odisha | t1 | 3,230 | 91.2 | 80 | 94.3 | 35.3 | 51.8 | -6.79 | 29.42 | 20 | +0.296 |
| G0 | Odisha | t2 | 4,656 | 93.1 | 50 | 93.1 | 43.1 | 62.9 | -4.32 | 20.40 | 20 | +0.235 |
| G2 | Odisha | t2 | 3,230 | 84.3 | 70 | 92.4 | 37.2 | 54.6 | -3.57 | 29.22 | 20 | +0.223 |
| G0 | Odisha | t4 | 4,656 | 91.9 | 60 | 91.9 | 34.0 | 51.0 | +0.06 | 25.54 | 20 | +0.086 |
| G2 | Odisha | t4 | 3,230 | 89.0 | 70 | 93.2 | 32.6 | 49.7 | +1.44 | 29.78 | 28 | +0.065 |
| G0 | West Bengal | t1 | 2,866 | 95.1 | 70 | 95.1 | 42.3 | 60.6 | -4.62 | 24.21 | 20 | +0.402 |
| G2 | West Bengal | t1 | 2,101 | 93.3 | 80 | 95.5 | 41.3 | 58.8 | -4.77 | 27.03 | 20 | +0.384 |
| G0 | West Bengal | t2 | 2,866 | 95.3 | 50 | 95.3 | 49.0 | 67.6 | -2.55 | 18.67 | 20 | +0.336 |
| G2 | West Bengal | t2 | 2,101 | 84.6 | 70 | 92.5 | 40.2 | 56.3 | -2.80 | 29.27 | 20 | +0.295 |
| G0 | West Bengal | t4 | 2,866 | 90.3 | 60 | 90.3 | 37.0 | 53.9 | +3.82 | 25.80 | 20 | +0.210 |
| G2 | West Bengal | t4 | 2,101 | 86.0 | 70 | 90.8 | 33.8 | 50.5 | +3.88 | 31.41 | 20 | +0.186 |
| G0 | ASC/DESC pairs only | t1 | 6,429 | 94.6 | 70 | 94.6 | 38.7 | 56.5 | -6.08 | 25.46 | 20 | +0.350 |
| G2 | ASC/DESC pairs only | t1 | 4,481 | 92.4 | 80 | 95.1 | 38.3 | 55.7 | -5.97 | 28.17 | 20 | +0.348 |
| G0 | ASC/DESC pairs only | t2 | 6,429 | 94.2 | 50 | 94.2 | 45.7 | 65.0 | -3.96 | 19.56 | 20 | +0.295 |
| G2 | ASC/DESC pairs only | t2 | 4,481 | 85.4 | 70 | 93.2 | 39.4 | 56.1 | -2.51 | 28.47 | 20 | +0.289 |
| G0 | ASC/DESC pairs only | t4 | 6,429 | 91.3 | 60 | 91.3 | 35.1 | 51.9 | +1.69 | 25.69 | 20 | +0.144 |
| G2 | ASC/DESC pairs only | t4 | 4,481 | 88.2 | 70 | 92.8 | 33.2 | 50.1 | +3.23 | 29.91 | 20 | +0.147 |
| G0 | same-pass pairs only | t1 | 1,288 | 93.6 | 70 | 93.6 | 35.6 | 51.3 | -3.39 | 27.97 | 20 | +0.265 |
| G2 | same-pass pairs only | t1 | 1,009 | 90.2 | 80 | 93.6 | 34.4 | 49.4 | -5.20 | 30.25 | 30 | +0.261 |
| G0 | same-pass pairs only | t2 | 1,288 | 92.4 | 50 | 92.4 | 43.0 | 62.9 | -2.05 | 21.01 | 20 | +0.261 |
| G2 | same-pass pairs only | t2 | 1,009 | 78.8 | 70 | 88.3 | 33.0 | 51.3 | -6.64 | 33.23 | 20 | +0.186 |
| G0 | same-pass pairs only | t4 | 1,288 | 90.5 | 60 | 90.5 | 34.9 | 53.1 | -0.12 | 26.24 | 20 | +0.162 |
| G2 | same-pass pairs only | t4 | 1,009 | 84.6 | 70 | 88.6 | 32.4 | 49.3 | -1.74 | 33.57 | 28 | +0.073 |

**Common sample, paired differences** (`B_common_sample_stats.csv`; 4,697
evaluation pairs with the same physical orbit pair under both grids;
district-cluster bootstrap, 2,000 replicates, seed 20261012). The baseline
common sample (417 pairs) is in the CSV: sd(diff)/√2 G0 → G2 28.07 → 28.70
(t1), 19.66 → 23.48 (t2), 26.23 → 28.00 (t4).

### Addition B — common sample, paired differences G2 − G0 (evaluation)

| scope | marker | pairs | statistic | G0 | G2 | G2 − G0 | bootstrap 95% of the difference |
|---|---|---:|---|---:|---:|---:|---|
| ALL | t1 | 4,697 | sd(diff)/√2 (d) | 25.21 | 25.95 | +0.74 | [+0.45, +1.04] |
| ALL | t1 | 4,697 | within 10 d (%) | 38.90 | 38.83 | -0.06 | [-0.71, +0.54] |
| ALL | t1 | 4,697 | within 20 d (%) | 56.91 | 56.40 | -0.51 | [-0.98, +0.00] |
| ALL | t1 | 4,697 | within fixed T (%) | 94.78 | 94.17 | -0.62 | [-0.96, -0.33] |
| ALL | t1 | 4,697 | mean diff (d) | -5.77 | -6.01 | -0.24 | [-0.41, -0.09] |
| ALL | t1 | 4,697 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +0.00] |
| ALL | t2 | 4,697 | sd(diff)/√2 (d) | 19.56 | 24.47 | +4.90 | [+4.39, +5.50] |
| ALL | t2 | 4,697 | within 10 d (%) | 46.48 | 40.77 | -5.71 | [-6.89, -4.76] |
| ALL | t2 | 4,697 | within 20 d (%) | 65.55 | 58.61 | -6.94 | [-8.26, -5.78] |
| ALL | t2 | 4,697 | within fixed T (%) | 94.02 | 88.99 | -5.02 | [-5.70, -4.34] |
| ALL | t2 | 4,697 | mean diff (d) | -3.14 | -3.25 | -0.11 | [-0.56, +0.35] |
| ALL | t2 | 4,697 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +0.00] |
| ALL | t4 | 4,697 | sd(diff)/√2 (d) | 25.89 | 26.83 | +0.94 | [+0.58, +1.45] |
| ALL | t4 | 4,697 | within 10 d (%) | 35.17 | 33.70 | -1.47 | [-2.30, -0.71] |
| ALL | t4 | 4,697 | within 20 d (%) | 52.31 | 51.37 | -0.94 | [-1.86, -0.12] |
| ALL | t4 | 4,697 | within fixed T (%) | 90.97 | 90.53 | -0.45 | [-1.00, +0.04] |
| ALL | t4 | 4,697 | mean diff (d) | 1.56 | 2.36 | +0.80 | [+0.41, +1.32] |
| ALL | t4 | 4,697 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +7.50] |
| Andhra Pradesh | t1 | 134 | sd(diff)/√2 (d) | 27.76 | 28.24 | +0.48 | [-3.89, +1.04] |
| Andhra Pradesh | t1 | 134 | within 10 d (%) | 33.58 | 36.57 | +2.99 | [+0.00, +8.54] |
| Andhra Pradesh | t1 | 134 | within 20 d (%) | 52.99 | 52.99 | +0.00 | [-4.45, +7.77] |
| Andhra Pradesh | t1 | 134 | within fixed T (%) | 94.78 | 92.54 | -2.24 | [-4.76, +0.00] |
| Andhra Pradesh | t1 | 134 | mean diff (d) | 0.60 | -0.37 | -0.97 | [-4.23, -0.14] |
| Andhra Pradesh | t1 | 134 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [-10.00, +10.00] |
| Andhra Pradesh | t2 | 134 | sd(diff)/√2 (d) | 22.63 | 32.23 | +9.60 | [+5.91, +23.34] |
| Andhra Pradesh | t2 | 134 | within 10 d (%) | 46.27 | 33.58 | -12.69 | [-14.29, -10.53] |
| Andhra Pradesh | t2 | 134 | within 20 d (%) | 65.67 | 53.73 | -11.94 | [-19.75, +4.10] |
| Andhra Pradesh | t2 | 134 | within fixed T (%) | 89.55 | 78.36 | -11.19 | [-34.62, -4.76] |
| Andhra Pradesh | t2 | 134 | mean diff (d) | -3.58 | -3.36 | +0.22 | [-5.00, +2.33] |
| Andhra Pradesh | t2 | 134 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +20.00] |
| Andhra Pradesh | t4 | 134 | sd(diff)/√2 (d) | 30.51 | 33.34 | +2.83 | [-2.41, +18.32] |
| Andhra Pradesh | t4 | 134 | within 10 d (%) | 32.84 | 32.09 | -0.75 | [-11.54, +2.22] |
| Andhra Pradesh | t4 | 134 | within 20 d (%) | 54.48 | 48.51 | -5.97 | [-25.00, +2.22] |
| Andhra Pradesh | t4 | 134 | within fixed T (%) | 84.33 | 82.84 | -1.49 | [-8.11, +0.00] |
| Andhra Pradesh | t4 | 134 | mean diff (d) | 1.31 | 3.15 | +1.85 | [-6.97, +7.84] |
| Andhra Pradesh | t4 | 134 | median |diff| (d) | 20.00 | 27.50 | +7.50 | [-5.00, +20.00] |
| Odisha | t1 | 2,805 | sd(diff)/√2 (d) | 26.03 | 26.94 | +0.91 | [+0.49, +1.33] |
| Odisha | t1 | 2,805 | within 10 d (%) | 36.72 | 36.83 | +0.11 | [-0.64, +0.82] |
| Odisha | t1 | 2,805 | within 20 d (%) | 54.58 | 54.05 | -0.53 | [-1.08, +0.09] |
| Odisha | t1 | 2,805 | within fixed T (%) | 94.26 | 93.48 | -0.78 | [-1.21, -0.34] |
| Odisha | t1 | 2,805 | mean diff (d) | -6.83 | -7.11 | -0.28 | [-0.50, -0.04] |
| Odisha | t1 | 2,805 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +0.00] |
| Odisha | t2 | 2,805 | sd(diff)/√2 (d) | 19.94 | 24.46 | +4.51 | [+3.91, +5.22] |
| Odisha | t2 | 2,805 | within 10 d (%) | 44.53 | 39.68 | -4.85 | [-5.99, -3.71] |
| Odisha | t2 | 2,805 | within 20 d (%) | 63.99 | 58.07 | -5.92 | [-7.28, -4.63] |
| Odisha | t2 | 2,805 | within fixed T (%) | 93.58 | 88.95 | -4.63 | [-5.61, -3.68] |
| Odisha | t2 | 2,805 | mean diff (d) | -3.89 | -3.91 | -0.02 | [-0.61, +0.58] |
| Odisha | t2 | 2,805 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +0.00] |
| Odisha | t4 | 2,805 | sd(diff)/√2 (d) | 25.51 | 26.21 | +0.69 | [+0.32, +1.22] |
| Odisha | t4 | 2,805 | within 10 d (%) | 34.22 | 33.23 | -1.00 | [-1.80, -0.26] |
| Odisha | t4 | 2,805 | within 20 d (%) | 51.19 | 50.73 | -0.46 | [-1.31, +0.42] |
| Odisha | t4 | 2,805 | within fixed T (%) | 91.91 | 91.48 | -0.43 | [-1.19, +0.16] |
| Odisha | t4 | 2,805 | mean diff (d) | 0.05 | 1.11 | +1.06 | [+0.52, +1.73] |
| Odisha | t4 | 2,805 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +7.50] |
| West Bengal | t1 | 1,758 | sd(diff)/√2 (d) | 23.58 | 24.05 | +0.47 | [+0.23, +0.67] |
| West Bengal | t1 | 1,758 | within 10 d (%) | 42.78 | 42.21 | -0.57 | [-1.76, +0.20] |
| West Bengal | t1 | 1,758 | within 20 d (%) | 60.92 | 60.41 | -0.51 | [-1.63, +0.18] |
| West Bengal | t1 | 1,758 | within fixed T (%) | 95.62 | 95.39 | -0.23 | [-0.40, -0.08] |
| West Bengal | t1 | 1,758 | mean diff (d) | -4.55 | -4.68 | -0.13 | [-0.34, +0.04] |
| West Bengal | t1 | 1,758 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +0.00] |
| West Bengal | t2 | 1,758 | sd(diff)/√2 (d) | 18.66 | 23.79 | +5.13 | [+4.26, +6.13] |
| West Bengal | t2 | 1,758 | within 10 d (%) | 49.60 | 43.06 | -6.54 | [-9.94, -4.72] |
| West Bengal | t2 | 1,758 | within 20 d (%) | 68.03 | 59.84 | -8.19 | [-11.22, -6.21] |
| West Bengal | t2 | 1,758 | within fixed T (%) | 95.05 | 89.87 | -5.18 | [-5.61, -4.32] |
| West Bengal | t2 | 1,758 | mean diff (d) | -1.91 | -2.19 | -0.28 | [-1.15, +0.57] |
| West Bengal | t2 | 1,758 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +10.00] |
| West Bengal | t4 | 1,758 | sd(diff)/√2 (d) | 26.01 | 27.20 | +1.19 | [+0.53, +2.37] |
| West Bengal | t4 | 1,758 | within 10 d (%) | 36.86 | 34.58 | -2.28 | [-4.50, -0.73] |
| West Bengal | t4 | 1,758 | within 20 d (%) | 53.92 | 52.62 | -1.31 | [-3.68, +0.31] |
| West Bengal | t4 | 1,758 | within fixed T (%) | 89.99 | 89.59 | -0.40 | [-1.50, +0.50] |
| West Bengal | t4 | 1,758 | mean diff (d) | 3.98 | 4.31 | +0.33 | [-0.03, +0.95] |
| West Bengal | t4 | 1,758 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +7.50] |
| ASC/DESC pairs only | t1 | 3,935 | sd(diff)/√2 (d) | 24.72 | 25.49 | +0.77 | [+0.46, +1.13] |
| ASC/DESC pairs only | t1 | 3,935 | within 10 d (%) | 39.67 | 39.52 | -0.15 | [-0.96, +0.53] |
| ASC/DESC pairs only | t1 | 3,935 | within 20 d (%) | 57.94 | 57.41 | -0.53 | [-1.06, -0.03] |
| ASC/DESC pairs only | t1 | 3,935 | within fixed T (%) | 94.97 | 94.43 | -0.53 | [-0.99, -0.17] |
| ASC/DESC pairs only | t1 | 3,935 | mean diff (d) | -6.16 | -6.46 | -0.30 | [-0.53, -0.10] |
| ASC/DESC pairs only | t1 | 3,935 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +0.00] |
| ASC/DESC pairs only | t2 | 3,935 | sd(diff)/√2 (d) | 19.26 | 23.89 | +4.63 | [+4.03, +5.28] |
| ASC/DESC pairs only | t2 | 3,935 | within 10 d (%) | 47.12 | 41.78 | -5.34 | [-6.57, -4.36] |
| ASC/DESC pairs only | t2 | 3,935 | within 20 d (%) | 65.97 | 59.29 | -6.68 | [-8.04, -5.41] |
| ASC/DESC pairs only | t2 | 3,935 | within fixed T (%) | 94.31 | 89.78 | -4.52 | [-5.29, -3.79] |
| ASC/DESC pairs only | t2 | 3,935 | mean diff (d) | -3.36 | -2.93 | +0.43 | [-0.12, +1.02] |
| ASC/DESC pairs only | t2 | 3,935 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +0.00] |
| ASC/DESC pairs only | t4 | 3,935 | sd(diff)/√2 (d) | 25.74 | 26.46 | +0.72 | [+0.32, +1.16] |
| ASC/DESC pairs only | t4 | 3,935 | within 10 d (%) | 35.30 | 33.85 | -1.45 | [-2.33, -0.69] |
| ASC/DESC pairs only | t4 | 3,935 | within 20 d (%) | 52.27 | 51.44 | -0.84 | [-1.73, -0.03] |
| ASC/DESC pairs only | t4 | 3,935 | within fixed T (%) | 91.13 | 90.75 | -0.38 | [-0.91, +0.15] |
| ASC/DESC pairs only | t4 | 3,935 | mean diff (d) | 1.68 | 2.66 | +0.99 | [+0.50, +1.59] |
| ASC/DESC pairs only | t4 | 3,935 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +7.50] |
| same-pass pairs only | t1 | 762 | sd(diff)/√2 (d) | 27.61 | 28.17 | +0.55 | [+0.16, +0.84] |
| same-pass pairs only | t1 | 762 | within 10 d (%) | 34.91 | 35.30 | +0.39 | [-1.00, +1.63] |
| same-pass pairs only | t1 | 762 | within 20 d (%) | 51.57 | 51.18 | -0.39 | [-1.40, +0.68] |
| same-pass pairs only | t1 | 762 | within fixed T (%) | 93.83 | 92.78 | -1.05 | [-1.91, -0.14] |
| same-pass pairs only | t1 | 762 | mean diff (d) | -3.75 | -3.67 | +0.08 | [-0.37, +0.56] |
| same-pass pairs only | t1 | 762 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +10.00] |
| same-pass pairs only | t2 | 762 | sd(diff)/√2 (d) | 21.04 | 27.25 | +6.21 | [+4.99, +7.60] |
| same-pass pairs only | t2 | 762 | within 10 d (%) | 43.18 | 35.56 | -7.61 | [-10.10, -5.31] |
| same-pass pairs only | t2 | 762 | within 20 d (%) | 63.39 | 55.12 | -8.27 | [-10.68, -6.38] |
| same-pass pairs only | t2 | 762 | within fixed T (%) | 92.52 | 84.91 | -7.61 | [-9.50, -5.76] |
| same-pass pairs only | t2 | 762 | mean diff (d) | -1.99 | -4.93 | -2.94 | [-4.46, -1.60] |
| same-pass pairs only | t2 | 762 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +0.00] |
| same-pass pairs only | t4 | 762 | sd(diff)/√2 (d) | 26.65 | 28.65 | +2.00 | [+0.85, +3.47] |
| same-pass pairs only | t4 | 762 | within 10 d (%) | 34.51 | 32.94 | -1.57 | [-3.19, -0.24] |
| same-pass pairs only | t4 | 762 | within 20 d (%) | 52.49 | 51.05 | -1.44 | [-3.61, +0.54] |
| same-pass pairs only | t4 | 762 | within fixed T (%) | 90.16 | 89.37 | -0.79 | [-2.29, +0.48] |
| same-pass pairs only | t4 | 762 | mean diff (d) | 0.96 | 0.81 | -0.14 | [-1.55, +1.35] |
| same-pass pairs only | t4 | 762 | median |diff| (d) | 20.00 | 20.00 | +0.00 | [+0.00, +7.50] |

**Grid-limit occupancy** (`B_grid_limit_occupancy.csv`). Under G0 the
restricted bounds are touched by one fit in 1,630 (21.1%), 2,655 (34.4%) and
1,769 (22.9%) of the 7,717 evaluation pairs for t1, t2 and t4, reproducing
Table S24. Under G2 the free design limits (t1 174.5–374.5, t2 194.5–404.5,
t4 214.5–422.0 DOY; the lower limits follow from the two-dekad segment
minimum and the ordering constraints, the t4 upper limit is the compositing-
window end) are touched in 443 (8.1%), 90 (1.6%) and 1,090 (19.9%) of the
5,490 evaluation pairs; for t4, 1,087 of the 1,090 are at 422.0, the window
end, which no grid lifts (Codex B5).

**Series retained under both grids** (33,705; `B_series_shifts.csv`). The
marker is unchanged in 88.2% (t1), 79.5% (t2) and 86.0% (t4) of them. Where
the G0 fit sat on a G0 bound the shares unchanged are lower (t1 46.1% lower /
70.4% upper bound; t2 42.2% / 44.3%; t4 46.8% / 73.9%), and the G2 marker
lies outside the G0 range in 41.8% / 27.1% (t1), 55.5% / 43.3% (t2) and
41.2% / 0.3% (t4) of those series; the t2 lower-bound series move by a
median of −10 d. Among all G2-retained series the marker lies outside the
published G0 range in 9.6% (t1), 23.3% (t2) and 6.6% (t4).

**Reading guide, nothing more.** The free search with its own calibration
retains fewer series and pairs; on the common sample the between-orbit
statistics move by under 1 d of sd(diff)/√2 for t1 and t4 and by about 5 d
for t2, with the within-one-dekad shares lower by 0.1, 5.7 and 1.5
percentage points; on each arm's full sample the G2 values are larger for
all three markers, most for t2. These are sensitivities of the specified
search-and-retention procedure, reported continuously with intervals; they
are not a verdict that the published result was or was not an artefact, and
t4 remains limited by the window end under both grids (Codex B3, B5).

## 4. What was not done

No padded grid, no dispersion (clause b) rerun, no estimator comparison, no
exposure redesign, no Earth Engine export, no field data, no manuscript
text, no commit, push, deposit change, journal contact or submission. The
submitted v3.18 package, the public release and the Zenodo deposit were
only read; their hashes were re-verified on the user's machine before the
inputs were staged (archive bcf6a7a3…, release tree HEAD a465400e, deposit
SHA256SUMS).

## 5. Timings (wall clock, this container: 2 CPUs, Python 3.13.16, numpy 2.4.4, pandas 3.0.2)

| step | time |
|---|---|
| preflight (hashes, structure, designs, G0 replay of 8 files, pair rebuild) | 3 min 10 s |
| calibration `pixel_free`, 15 cells × (4,000 + 1,500 check) draws, 2 workers | 35.8 min |
| Addition A (R = 1,000; B = 2,000; K = 50), both arms | 10.5 min (shared CPU) |
| Addition B fit, 170,321 series on 12,649 designs, 2 workers | 56.1 min |
| Addition B comparison and bootstrap | 1 min 50 s |
