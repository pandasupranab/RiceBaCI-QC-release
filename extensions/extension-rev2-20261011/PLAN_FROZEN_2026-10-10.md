# Extension plan — frozen before any computation (10 October 2026)

Extension of the verified public release `pandasupranab/RiceBaCI-QC-release`,
tag v1.0.0, commit a465400e7eb7ec05f7c7d819ab14303cc14146d9, for the two
additions proposed on 10 October 2026 and corrected by Codex's "Independent
review of the strengthening proposal" (same date). Both additions are
post-hoc: the published outcomes were known before they were designed. They
change no published number, table, verdict, source file, release or deposit.
The submitted v3.18 package, the GitHub release and the Zenodo deposit are
read, never written.

This plan incorporates Codex's corrections A1–A4 and B1–B5 verbatim in
effect. It is frozen now; the scripts implement it; any departure found later
is reported, not silently applied.

## What is dropped from the 10 October proposal

- The "information ratio" I and its claimed equality to a within-cell
  correlation (Codex A2: a counterexample shows I = 0.6 at r = 0.5 within one
  cell, and pooled offsets drive I toward 0 with r unchanged). No variance
  component or measurement-error quantity is computed under any name.
- The band-based rules claiming detection or absence of "pixel-specific
  information" (A1). The derangement band is a *random-mismatching reference
  band*, not a confidence interval for a null, and no test is made.
- The binary "robust / sensitive" rule at 2.9 d and 5 percentage points (B3).
  Paired differences and intervals are reported continuously; no threshold.
- Predictions of the outcome, "independent reading", claims about why an
  advantage is weak, and the statement that within-cell correlation must be
  below pooled correlation (A4).
- The padded grid G1, the dispersion rerun, estimator comparisons, exposure
  redesign, Earth Engine exports, field data (scope).
- The statement that the per-orbit exports total 1.07 GB (that is the whole
  raw-input archive; the 225 per-orbit files total 295,007,797 bytes).

## Addition A — descriptive different-pixel benchmark (shuffled pairs)

Input: the released `results/orbit_agreement/orbit_pairs.csv` (8,515 pairs;
byte-identical to the submitted evidence snapshot). Nothing is refitted.

Cells: (district, year, orbit_a, orbit_b) with the orbits in the released
order. Eligible: cells with at least two rows. Singleton cells are excluded
from both the observed and the benchmark arm and counted. Evaluation
(2018–2025) and baseline (2017) are benchmarked separately and never pooled.

Benchmark: within each eligible cell, the complete orbit-b marker vector
(trough_b, heading_b, harvest_b) of each row is reassigned to another row of
the same cell by a uniformly random derangement (no row keeps its own
orbit-b vector); orbit-a values, district, year, the two orbits, pass
directions, n_valid and the pairing stay as released. Uniform derangements
are drawn by rejection sampling of uniform permutations (numpy PCG64,
`default_rng(seed)`, `permutation`, retried until no fixed point). A two-row
cell has exactly one derangement, so its benchmark has no randomisation
variation; the number of such cells is reported. R = 1,000 benchmark draws;
seed recorded.

Statistics, identical on both arms and on the same eligible rows: n, share
within the published fixed tolerance (70/50/60 d for t1/t2/t4), share within
10 d, share within 20 d, mean signed difference, sd(diff), sd(diff)/√2,
median |diff|, Pearson r between the two orbits' markers. Scopes as in Table
S1: ALL, by state, A/D pairs only, same-pass pairs only; plus by year. The
number of contributing districts per scope is recorded.

Reported: the observed value; the benchmark mean and sd over the R draws and
the 2.5th/97.5th percentiles (the random-mismatching reference band); the
difference observed − benchmark mean, in days or percentage points.

Conditional uncertainty: a district-cluster bootstrap (2,000 replicates,
seed recorded) of the observed statistic and of the difference observed −
benchmark mean. Resampled districts carry a draw-instance identifier so that
a district drawn twice forms two separate sets of cells, never one enlarged
cell. Inside each bootstrap replicate the benchmark mean is approximated with
K derangement draws (K recorded); the Monte Carlo standard error of the
benchmark mean at R = 1,000 on the full sample is reported separately so that
sampling uncertainty and Monte Carlo approximation stay distinguishable. A
small pilot is timed before the full run; the actual timings are reported.

No interpretation beyond the numbers: the benchmark describes how the
released pairs compare with random same-cell mismatching under the same
estimator; it is not a randomised experiment, not a test, and identifies no
cause.

## Addition B — free-grid sensitivity of the per-orbit fits (G2 versus G0)

G0: the published restricted search (`PIXEL_GRID_DOY`, 4,322 designs), taken
from the released per-orbit fit cache `per_orbit_fits.csv` (170,321 series;
SHA-256 31b96b6e…) — the historical reference, not refitted.

G2: the free grid of the released `plsm_designs_free()` (12,649 designs;
shape constraints and the two-dekad segment minimum only; the restricted
designs are verified to be a subset). Every per-orbit series of the 225
released exports is refitted with the released `plsm_fit` on the free
designs, through an extension copy of the released `fit_one_file` whose only
change is the retention function; everything else (bin admission,
aggregation, no smoothing, min valid dekads, the marker-blind pair rule,
2017-only tolerance derivation) is the released code, imported from the
verified copy.

Retention on G2: the released screen (reason, finite rise, rise ≥ 0 dB,
finite t, t ≥ critical value) with the critical value from a new table
`plsm_null_t_pixel_free.csv`, grid key `pixel_free`, i.i.d. Gaussian null
(the released pixel-level choice; treated here as an assumption of the
noise/missingness model, not as proven by the residual autocorrelation),
tabulated for every n_valid from 14 to 28 at 4,000 draws each, with the
released `one_cell` calibration routine dispatched explicitly to the
12,649-design matrix; seeds and draws recorded; the table, the grid and the
sources hashed. The extension's lookup is strict: a missing grid key or a
missing n_valid row stops the run (no fallback constant); these failures are
exercised deliberately in the preflight.

Preflight before the full fit (all must pass or the run stops):
1. Input identities: release sources against the v1.0.0 git blob hashes;
   the 225 per-orbit exports against the deposit manifest; the fit cache
   against the replay-inputs manifest; the pairs file against the release and
   the submitted snapshot.
2. Structure: pair counts, cell counts, singleton count, pass split after
   exclusion, district counts; cache counts; every published pair joins to
   retained cache rows with identical markers.
3. Designs: 4,322 restricted designs are a subset of the 12,649 free designs;
   the released lookup behaviour (`free` → AR(1) 4.17; unknown key → 3.5
   fallback) is recorded so that it is never used for G2.
4. G0 replay in this environment: a representative set of export files is
   refitted on the restricted grid with the extension copy of `fit_one_file`
   and the released retention, and compared with the cache row for row
   (retained flag, failure reason, markers, rise, rmse), including retained,
   rejected and bound-touching series.
5. The released pair builder applied to the G0 cache reproduces the released
   `orbit_pairs.csv` exactly.

Outputs: `per_orbit_fits_pixel_free.csv` (same columns as the cache plus the
grid label), its own resumable done-file (no reuse of G0 cache keys);
`orbit_pairs_pixel_free.csv` built with the released rule; per-file timings.

Comparison (all reported, nothing dropped):
- Retention accounting per arm: series retained, pixel-seasons with ≥ 2
  retained orbits, pairs, by year and state.
- Transitions of pixel-seasons between arms: paired in both with the same
  physical (orbit_a, orbit_b) [the common sample, a selected population];
  paired in both with a different pair; paired in G0 only; paired in G2 only.
- Per arm on its own full sample: the Table S1 statistics with the fixed
  70/50/60 d tolerances; and, secondarily, each arm's share within its OWN
  2017-calibrated tolerance (0.90 quantile of |diff| on that arm's 2017
  pairs; never on evaluation years), reported beside the fixed-tolerance
  share because a wider tolerance can conceal larger absolute disagreement.
- On the common sample: both arms' statistics and the paired differences
  G2 − G0 (sd(diff)/√2, shares within 10 d and 20 d and within the fixed
  tolerance, median |diff|, mean signed difference), with district-cluster
  bootstrap percentile intervals (2,000 replicates, seed recorded), by marker
  and scope.
- Grid-limit occupancy per arm (G0: the restricted bounds, reproducing Table
  S24; G2: the free design limits), and, for series retained in both arms,
  the distribution of G2 − G0 marker shifts, split by whether the G0 fit sat
  on a bound, and the share of G2 markers outside the G0 range.
- t4 cannot exceed DOY 422.0 under any grid (the window end). Because the
  four breakpoints are fitted jointly, t4 can move with the other
  constraints; the comparison is reported as sensitivity to the specified
  search-and-retention procedure, not as a test of any one bound and not as
  proof that the published result was or was not an artefact.

## Environment and record

Computation runs in the session's Linux container (recorded: Python, numpy,
pandas versions, CPU count); the G0 replay preflight establishes that this
environment reproduces the released cache before any G2 result is read.
Every script, input hash, calibration row, seed, transcript and timing is
delivered with the results for Codex's bounded review. No manuscript text is
drafted in this pass.
