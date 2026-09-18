# `results/orbit_agreement/` — what is active, what is retired

Written 2026-09-14 (seventh pass), after three external audits of the same material.
It describes the active table beside it, records what was removed from it and why, and
names the files that are no longer part of the active result set.

**One sentence first.** H1 and H2 **clause (b) failed as measured**, and this study's
evidence **does not identify why**.

---

## `Table_SX_DispersionSingleOrbit.csv` — active, observed only

Clause (b) asks whether a pixel's marker moves less between seasons than pixels differ
within a district. Measured on the committed panel the ratio is above 1. That panel's
marker is fitted to all orbits composited together, while the between-orbit statistic is
measured between two single-orbit fits — two estimators, so the two numbers are not
commensurable. `orbit_agreement.single_orbit_dispersion` removes that mismatch by
recomputing the dispersion on **one orbit**: each pixel's best-covered relative orbit
with at least two retained seasons, residuals taken about the district-season mean,
`within` the pooled sd about each pixel's own mean and `between` the sd of the pixel
means.

| column | meaning |
|---|---|
| `marker` | trough / heading / harvest |
| `sigma_single` | between-orbit sd(difference)/√2 on the **paired** sample, carried alongside for reference. A scaled disagreement statistic, **not a measured error** — Protocol §1.5.6 constraint 2 — and never subtracted from anything in this table |
| `n_seasons_mean` | mean retained seasons per pixel on its chosen orbit (4.326265; range two to nine) |
| `within_obs`, `between_obs`, `ratio_obs` | the observed single-orbit dispersion and its ratio |
| `n_pixels`, `n_obs` | 6,602 pixels, 28,562 pixel-seasons |

Every column is observed. Nothing is corrected, decomposed, or labelled true.

**Result.** Observed ratios **1.327845 / 1.577191 / 1.475027** for trough / harvest /
heading, all above the declared criterion of 1. The committed panel's own figures are 1.340
and 1.508, in `results/dispersion/`.

**What that does and does not license.** **All three ratios remain above 1 in the single-orbit sample as well.** That sample is **selected separately** — each pixel's best-covered orbit with at least two retained seasons — from the paired sample the between-orbit statistic uses, and from the committed panel. So the three results sit side by side as observations on three samples, and **no causal statement about why clause (b) failed follows from any of them**. *(Narrowed 2026-09-14, eighth
pass: this section read "So the clause (b) failure is **not** an artefact of the estimator
mismatch." Withdrawn — ruling out a candidate explanation is a causal statement, and the
single-orbit sample is not the paired sample.)*

---

## Retired from this table: four columns and a note field

Until 2026-09-14 the table also carried `within_true`, `between_true`, `ratio_corrected`
and a free-text `note`. Those came from subtracting an assumed error variance —
`within² − σ²` and `between² − σ²/mean(nᵢ)` — and the note read, in all three rows,
"below 1 once error is removed: clause (b) failed on noise".

**The whole calculation is retired as an active analysis**, not qualified. Four defects,
found across three external audits:

1. **The error model was never tested.** It requires additive error independent of the
   true date, equal variance on the two orbit paths, uncorrelated between them,
   independent across seasons within a pixel, and transporting from the paired sample to
   the single-orbit sample. Protocol §1.5.6 constraint 2 declines to grant the third of
   those in the first place, and none of the others is tested anywhere in this study.
2. **The between-pixel factor was wrong.** For independent equal-variance errors a pixel
   mean carries σ²/nᵢ, so the average contribution across *equally weighted* pixel means
   is σ²·mean(1/nᵢ), not σ²/mean(nᵢ). The counts are unbalanced — 6,602 pixels carrying
   two to nine seasons (2:1,385 · 3:1,176 · 4:1,145 · 5:1,084 · 6:869 · 7:586 · 8:265 ·
   9:92) — so 1/mean(nᵢ) = **0.23114628** against mean(1/nᵢ) = **0.28164872**, a 21.85%
   understatement of the error removed, always in that direction.
3. **The residuals are district-year centred** before the pixel means are formed, which
   induces covariance between them that the subtraction ignores. No single factor repairs
   this.
4. **The arithmetic was fragile.** A σ 3.613470% larger drove the trough's implied
   within-variance to zero; a σ 10% smaller lifted two of the three derived ratios above
   1.

It is **not** rescued with a better factor. The manuscript does not use it, and building a
matched uncertainty propagation for the unbalanced, centred estimator would be a new
analysis in service of a calculation nothing depends on — with the untested error and
selection assumptions still untested at the end of it.

The calculation, each defect and the decision to retire it are preserved in
`analysis/deviation_log.md` and `analysis/decisions_log.md`. Git history preserves every
earlier version of the table itself.

---

## Files no longer in the active result set

| file | status |
|---|---|
| `Table_SX_DispersionCorrected.csv` | **removed 2026-09-14.** A first-pass artefact of the retired subtraction, written by a version of `orbit_agreement.py` that no longer exists; no current script produced it and no current script reads it. Git history preserves it |
| `run_full.log` | **archived 2026-09-14** to `superseded_2026-09-14/run_full.log`, unchanged. It is the console transcript of the 2026-09-13 run and prints "true within", "corrected ratio", "failed on noise" and "error decomposition" — wording the code no longer emits. Kept as dated evidence of what was run, not as a current description. It cannot be regenerated without the raw exports (see `DATA_AVAILABILITY.md`) |

`Table_SX_OrbitAgreement.csv`, `Table_SX_ClauseA_byDistrict.csv` and `orbit_pairs.csv` are
unchanged and remain active. `python/gate1_justification.py` reads only `sigma_single`
from the dispersion table and is unaffected by the removed columns.

---

## The semivariogram comparison, since it is often read alongside

`semivariance.py`'s shortest-lag value is 25.68 / 20.57 / 25.30 d against the between-orbit
25.90 / 19.82 / 25.79 d — similar to within 0.8 d. **That similarity is a description of
this dataset and nothing more.** The two are not the same estimand: a short-lag spatial
semivariance mixes local variation in the true field with the spatially *uncorrelated* part
of the error, while a between-orbit difference cancels whatever the two paths share. Both
read the same panel through the same breakpoint estimator, so neither is independent of a
defect in the other and **neither validates the other**. Nothing in this repository calls
the error magnitude corroborated, confirmed or independently established.
