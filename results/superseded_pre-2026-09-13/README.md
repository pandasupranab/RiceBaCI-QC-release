# Superseded §3.10 attrition tables — do not cite these numbers

Every file in this directory was produced by an estimator with a defect that was
later found, fixed and logged. They are kept because the decision and deviation logs
quote their numbers when recording what went wrong, and deleting them would break
that record. **Nothing in the manuscript, and no figure, may be drawn from them.**

Moved here on 2026-09-13 from `results/`, where they sat with names indistinguishable
from valid output — one of them called `_final_`.

## What replaces them

| authoritative table | level |
|---|---|
| `results/s310_v2_district/Table_SX_AttritionDiagnostic.csv` | district-season |
| `results/s310_v2_pixel/Table_SX_AttritionDiagnostic.csv` | pixel-season |

## What each file here carries, on the §3.9 placebo cell (β_harv on SOS)

| file | rows | placebo coef | n_obs | p_WCB |
|---|---|---|---|---|
| `Table_SX_AttritionDiagnostic_district.csv` | 206 | +4.7582 | 213 | 0.1242 |
| `Table_SX_AttritionDiagnostic_district_phase.csv` | 308 | +4.7582 | 213 | 0.1242 |
| `Table_SX_AttritionDiagnostic_final_district.csv` | 253 | +4.7582 | 213 | 0.1242 |
| `Table_SX_AttritionDiagnostic_pixel.csv` | 206 | +4.7737 | 76,717 | 0.0010 |
| `Table_SX_AttritionDiagnostic_final_pixel.csv` | 308 | +4.7737 | 76,717 | 0.0010 |

Against the authoritative tables:

| | placebo coef | n_obs |
|---|---|---|
| corrected district | **+5.0010** | **208** |
| corrected pixel | **+7.4384** | **31,741** |

## The two defects these numbers contain

**District: the retained-only defect.** `twfe` was fitted on 213 district-seasons
where only 208 are retained, so five rows that failed the §3 fit criteria entered the
regression. The placebo estimate moves +4.7582 → +5.0010. This was caught by a
self-test that compared the two, and the fix was made inside the function rather than
at the call sites, because a caller can forget.

**Pixel: the QC screen was ignored.** 76,717 pixel-seasons where 31,741 are
retained — **58.6% of the observations in the pixel-level table should not have been
there.** The placebo estimate moves +4.7737 → +7.4384, which is not a rounding
difference but a different result: it is the number §3.9's placebo is rejected on
(p_perm 0.0395), and the smaller, contaminated estimate understated it.

## Why this directory exists at all

`python/make_figures.py` had already recorded, in `fig5`'s docstring, that
`Table_SX_AttritionDiagnostic_district.csv` is the defective table and must not be
plotted — `fig5()` refuses to run without the corrected one. So the defect was known
and the *code* was guarded, while five files carrying the withdrawn numbers stayed in
`results/` under names a reader would trust. One was named `_final_`.

Guarding the code and leaving the artifact is the same mistake as the stale figure 5
itself: the defect was fixed where it was noticed and not where it would next be
read. Recorded as such rather than quietly tidied.

## Also in this repository, and deliberately left in place

`results/s310_v2_*/Table_SX_AttritionDiagnostic.partial.csv` are resume artifacts of
the **corrected** runs, written by `--resume` and committed with them. They are
prefixes of the authoritative tables (district 121 of 253 rows; pixel 176 of 176,
i.e. complete). They carry no withdrawn numbers, so they are not moved here, but they
are not authoritative either — the file without `.partial` is.

---

## The five run logs here, added 2026-09-13

`s310_district.log`, `s310_pixel.log`, `s310_district_phase.log`,
`s310_final_district.log` and `s310_final_pixel.log` are the transcripts of the runs
that produced the tables above. They were moved here in the same pass, one step
later than the tables, because the first pass fixed the artifact that was noticed
and not the class it belonged to.

They carry the withdrawn numbers in plain text. On the §3.9 placebo cell:

    headline:trough:S_harvest_window   beta +4.758 d  (se 3.072)  p_WCB 0.1242   [district]
    headline:trough:S_harvest_window   beta +4.774 d  (se 1.270)  p_WCB 0.0010   [pixel]

against the authoritative +5.0010 and +7.4384. Two of the five were named
`s310_final_*`, so "final" appeared on superseded output twice over — once on a table
and once on its log.

The transcripts of the **corrected** runs are `results/s310_v2_district/run.log`,
`run_resume.log`, `run_balanced.log` and `results/s310_v2_pixel/run.log`,
`run_r1.log`, `run_r2.log`, `run_r3.log`. Those are in place and unchanged.

A log is a weaker hazard than a table — nobody quotes a coefficient from a
transcript in a paper — but `grep` over `results/*.log` for a coefficient would have
returned these with nothing to mark them as retracted, and that is enough.
