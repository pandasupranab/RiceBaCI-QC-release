# Data availability

**Current release status, 18 September 2026.** The clean public code/results
repository is https://github.com/pandasupranab/RiceBaCI-QC-release. The original
private development history was not published. DOI `10.5281/zenodo.22750338`
has been reserved, but the Zenodo record remains unpublished and its old replay
kit must be refreshed to this release before publication. This paragraph
supersedes dated archive-status statements below; it does not assert public
access to raw exports. Author-created data/results are CC BY 4.0, code is MIT,
and third-party rights remain separate (see the licence and notices files).

What this repository contains, what it does not, and exactly which results a
reader can reproduce without an Earth Engine account. Written because an external
audit on 2026-09-13 flagged the absence of the raw exports, and "the data is
large" is not a data-availability statement.

**Status note, 2026-09-14.** The raw exports are now **uploaded** to an unpublished Zenodo
draft — see *Archive* at the end of this file. They are **not public and carry no DOI**, so
everything below still describes what a reader can do with this repository alone, which is
the only thing that is true today.

Sizes are summed file content, not disk usage: `du` reports more because of block overhead.

## In this repository

| what | where | size | why it is here |
|---|---|---|---|
| **The committed cohort** — 10,000 points, `state, district, tile_id, cell_id, lon, lat` | `docs/candidate_cohort_v2.csv` | 856 KiB | The single fixed input every export is drawn from. `cell_id` is the stable key across every arm. With this and the scripts below, a reader can request new exports under the recorded configuration; byte-identical reconstruction of the historical exports is not promised because the upstream Earth Engine collections and service are outside this repository. |
| **Every Earth Engine export script** | `gee/` (9 files: 8 scripts and a README; the count read 7 until 2026-09-14, before `S1_INUNDATION.js` was added) | — | `s1_block.js` (225 tasks, the panel), `S1_PER_ORBIT.js` (225, H1/H2 clause (a)), `S1_STATIC_COVARIATES.js` (25, §3.10 IPSW), `S1_MASK_FLAG.js` (25, §3.5), `S1_ORBIT_INVENTORY.js` (0 tasks, the go/no-go check), `S1_INUNDATION.js` (25, §3.3), `S2_QC_Ingest.js`, `DIAGNOSTIC_snippet.js`. Each names its task count and its `CONFIG` is the one that was run. |
| **§3.5 mask exports, all 25** | `data/s1_maskflag/` | 441 KiB | Small enough to commit, and committing them makes the §3.5 arm reproducible **with no Earth Engine account at all**: `python/mask_sensitivity.py --selftest` runs its full gate against these files. |
| **§3.10 static covariates, merged** | `results/s1_static_covariates.csv` | 1.2 MiB | elevation, slope, incidence for all 10,000 points. |
| **Every results table** | `results/` | ~9 MiB | Including the §3.9 permutation tables, the five robustness arms, the orbit-agreement and dispersion tables, and the §3.5 mask arm. |
| **The district-season panel and its covariate-merged form** | `results/phen_panel_district_season.csv`, `..._static.csv` | 138 KiB | §3.8 declares the **district** panel as the headline, and these two files are all the district-level estimators need. In the recorded audit environment, `python/permutation_test.py --level district --n-perm 2000` re-estimates the district analogue from this repository with no Earth Engine account and reproduces the accepted `Table_SX_Permutation_district.csv` **byte for byte** (md5 `9db2962e533aa2b23c0ab8eabc159cf3`, clean rerun 2026-09-16). Cross-environment equality is assessed numerically, not promised byte-for-byte. **Correction, 2026-09-13:** an earlier version of this row said these files were added that day and that committing them is what made the headline reproducible. Both are false. `phen_panel_district_season.csv` has been tracked since `be4079e` and the `_static` form since `a59f5fa` — which is the state the external audit examined. The headline was already reproducible from the repository at the audited commit; nobody, including the author, had checked. |
| **The remaining figure inputs** | `results/exposure_phase_storms.csv`, `montecarlo_precision.csv`, `phen_curves_district_season.csv`, `splithalf_reliability.csv` | 527 KiB | Also tracked well before 2026-09-13, contrary to an earlier version of this row. Exactly one figure input is excluded, and it is named below. |
| **Every figure, plus a provenance manifest** | `figures/` | ~1.5 MiB | `figure_provenance.json` records the md5 of the generator, each declared input and every figure file. `make_figures.py --verify` re-hashes those artifacts and exits non-zero on a changed present file. This is an integrity check, not proof of how an artifact was produced; from a clone it is incomplete because one recorded input is absent, as detailed below. |
| **All Python source, with an explicit test registry** | `python/` | — | `run_all.sh selftest` runs 26 registered synthetic/unit checks. Eight named historical migrations, external-input builders/mergers, a long calibration generator and a long result driver have no `--selftest`; the runner registers them explicitly and fails if any new module belongs to neither list. The 26 checks require no research data. |
| **The §3.5 masked district-season panels, both variants** | `results/masked/phen_panel_district_season{,_static}.csv`, `results/masked_noovl/phen_panel_district_season{,_static}.csv` | 274 KiB | *Added 2026-09-14, and the reason is a correction.* §3.5's per-unit arm reads the **intersection-mask district-season panel**, and until this commit that file existed only in the author's working environment — so the arm could not be reproduced from a clone, while the amendment describing it implied it could. Found by an external audit. The four files are small because they are district-level (225 rows each), so they are committed rather than regenerated, and the arm now runs from the repository **with no Earth Engine account**. Their provenance is checkable against files already committed: `results/mask_sensitivity/mask_flag_all.csv` flags **8,085 of 10,000** cohort points, `filter_report_masked.csv` reports `cells_out` **72,765 = 8,085 × 9 seasons**, and each masked district-season row carries `n_pixels` summing to **8,085 per season** — 8,026 and 72,234 for the `_noovl` variant. The masked *pixel* panels (~117 MiB) remain excluded and are not needed by this arm. |
| **The H1 field-reference catalogue and its PDFs** | `docs/field_reference_sources.md`; `docs/field_reference_pdfs/` (9 PDFs) | ~13 MiB | *Added to this table 2026-09-14; it was missing, so a reader using this file as the index would not have known the PDFs were here.* **Presence in `docs/field_reference_pdfs/` is not endorsement.** Of the nine, **three are endorsed** (the ICAR-CRIDA / OUAT Odisha district contingency plans), one is auxiliary and unendorsed (PMFBY), and **five are unendorsed candidates** — two West Bengal plans, two Andhra delta plans, and one ANGRAU document the catalogue explicitly rejects. The one endorsed source that is **not** here is CRRI Technology Bulletin 62 (`icar-nrri.in` unreachable). The catalogue's archive manifest gives each file's status; read it before citing any of them, and read §3.4's amendment of the same date on the suspended AICRP attribution. |

## Not in this repository, and how to regenerate it

| what | volume | how |
|---|---|---|
| 225 panel exports `S1_PHEN_<district>_<year>.csv` | **712 MiB**, 4,950,225 rows | Run `gee/s1_block.js` against the committed cohort asset. It produces exactly these files. |
| 225 per-orbit exports `S1_ORBIT_<district>_<year>.csv` | **281 MiB**, 3,719,836 rows | Run `gee/S1_PER_ORBIT.js`. |
| The fitted per-orbit panel `results/orbit_agreement/per_orbit_fits.csv` | **~25 MiB** | Stage 11 of `run_all.sh` fits the 225 per-orbit exports. It is excluded from Git on size; the declared agreement tables and the post-hoc pair-selection sensitivity table are committed, but regenerating them from a clone requires the archived per-orbit exports. |
| The excluded pixel panels `phen_panel_sar.csv` and `phen_panel_sar_static.csv` | ~36–39 MiB per unmasked panel; ~117 MiB for both masked variants | `python/extract_phenometrics_sar.py --exports <dir> --out <dir>`, then `python/merge_static_covariates.py`. The much smaller district-season panel and its `_static` form are committed and listed above; they are not missing inputs. |
| The masked **pixel** panels for the §3.5 arm | ~117 MiB for both variants | Produced by stage 13 of `run_all.sh`, which filters the 225 raw exports with the committed mask flags and re-runs `extract_phenometrics_sar.py` on the result. **Corrected 2026-09-14:** this row read "from the committed mask flags", which implied the mask flags were sufficient. They are not — stage 13 also needs `$RICEBACI_ROOT/s1full`, the 225 raw exports, which are excluded above. Stage 13 now calls `need()` on both. The masked **district-season** panels, which is what the per-unit arm actually reads, are small and are now committed (see the row in the section above). |
| The 25 §3.3 inundation exports `S1_INUND_<district>.csv` | **~23 MiB**, 113,600 rows | Run `gee/S1_INUNDATION.js` with `verifyOnly = false` and `dryRunDistrict = null`. The verdict tables they produce **are** committed: `results/inundation/`. |
| The §3.1 Gate 1 justification arms `results/gate1_on/` and `results/orbit_gate1_on/` | **~35 MiB + ~26 MiB** | Stage 18 of `run_all.sh`: the panel re-extracted at `--gate1-r 0.50` and the per-orbit fits re-run with the same flag. The comparison tables they produce **are** committed: `results/gate1_justification/`. |
| The five §1.4 window-sweep panels `results/sweep_{control,365,385,395,410}/` | **~180 MiB** | Produced by stage 16 of `run_all.sh` — `python/extract_phenometrics_sar.py --window-end-doy` at each endpoint, and omitting the flag for the control. The tabulated output, which is what §1.4 asks for, **is** committed: `results/window_sweep/`. |

These are excluded from Git because of size. At this review stage the raw exports
have been uploaded only to the **unpublished** Zenodo draft described below, so
they are **not yet available to a reader**. Until that draft is refreshed for the
accepted commit and publicly released, raw-data replay remains incomplete outside
the author's archive. After release, the archive is intended to permit replay
without repeating the Earth Engine exports; the public DOI and its file hashes
must be verified before the manuscript says that this is possible.

## What a reader can verify, by what they have

**With nothing but this repository:**

- Every registered `--selftest` in `python/`, via `bash run_all.sh selftest`
  (**26 modules on 2026-09-16; eight named files explicitly lack a self-test**).
  The runner inventories every Python file and refuses an unregistered one rather
  than relying only on a prose count. These checks test the estimator against synthetic seasons with known breakpoints, and
  each gate is tested by making it **fail** on the defect it exists to catch. One of them,
  `python/lf_output.py`, guards this file's own claims: it pins every committed CSV
  and JSON to LF on Windows and Unix, and its self-test reads the other modules' source and
  fails if any of them can write a platform-dependent file. Without it, every md5 in this
  document and in every handoff was true on Linux and false on Windows.
- The §3.5 mask arm's structural gate, against the 25 committed mask exports.
- **§3.5's per-unit DiD**, from `results/mask_sensitivity/Table_SX_MaskPerUnit_{trough,heading,harvest}.csv`:
  one row per district × cyclone unit, both masks side by side. *Rebuilt 2026-09-14 (second
  pass) after an external audit; the column set changed.* Each estimated row carries the DiD,
  the number of clean control districts **declared** by §3.8 B and the number actually
  **usable** (both seasons estimable — these differ sharply, and that is the arm's most
  important disclosure), the `treated_other_severe_exposure` flag, **and both superseded
  quantities**: the before-after contrast and the withdrawn pixel-average DiD, so the size of
  each error is readable rather than described. `roster_block` separates §3.8 B's six declared
  named cyclones — the §3.5 result — from three additional severe storms reported for
  completeness and excluded from the claim. The arm is a **disclosure of unit-level spread**;
  the claim that mask choice does not move the per-unit estimates is withdrawn (§3.5's
  second-pass amendment). Per-unit inference is unavailable throughout: one treated cluster.
  **These three tables regenerate from committed inputs alone** — verified by running the arm
  against a directory holding only committed files and comparing byte for byte
  (`docs/verify_masked_panels.md`, check 4). The scope of that claim, stated exactly:
  **the per-unit calculation is reproducible from the committed fitted district panels;
  reconstructing those panels still requires the archived raw exports.** The comparison was run in the
  checked environment recorded by `results/analysis-environment.json`; exact requirements and
  a fail-closed checker are under `environments/`. Byte identity is asserted only for
  that environment.
  `python/lf_output.py` removes one source of cross-platform difference — `pandas` writes CRLF
  on Windows by default, which until 2026-09-14 would have changed every committed md5 there —
  but it removes only that one. Float-to-text rendering by the installed `pandas`/`numpy`, and
  the values themselves, can still differ elsewhere: this repository has measured its own two
  containers differing at the 16th significant figure through OpenBLAS reduction order
  (`results/window_sweep/window_sweep_summary.md`). No universal cross-environment
  numeric or byte-identity claim is made; content equality must be tested under an
  explicitly reported tolerance, while byte identity is scoped to the checked environment. *(Scoped 2026-09-15, tenth pass: this
  read "Byte-identity holds **on every platform** only because of `python/lf_output.py`", which
  credited an LF pin with a guarantee it cannot give.)*
- **The withdrawn-comparison side tables** (`results/mask_sensitivity/Table_SX_MaskPerUnit_withdrawnCompare_{trough,heading,harvest}.csv`, 148 KiB): the same rows plus two columns carrying the **withdrawn pixel-average DiD**, which is the evidence for that supersession at unit level rather than only as a summary statistic. **These cannot be regenerated from this repository**: they need the masked *pixel* panels (~117 MiB, excluded). They are committed as a record and are labelled as non-regenerable for that reason — which is why they are a separate file. Carrying those two columns inside the main tables is exactly what made the main tables unreproducible from a clone, found by testing rather than by assuming.
- **The §3.1 Gate 1 verdict**, from `results/gate1_justification/`: every statistic for
  all four declared criteria, on each arm's own retained set and on the pixel-seasons
  retained by both, plus the criterion-level and overall verdicts. The sample-selection
  question — did the gate just delete the noisy pixels? — is answered by reading the two
  samples side by side, without re-running anything.
- **The §3.2 state-bounds question**, from `results/gate2_state/`: the per-state marker
  distributions against §3.2's bounds with the margin from each, the Gate 2 rejection rate
  per state, and the two verdicts. §3.2's amendment explains why the declared
  state-specific-bounds sensitivity is refused rather than run.
- **The §3.3 withdrawal**, from `results/inundation/`: the per-unit rates, the per-unit
  excess against each unit's own matched 2017 null, the verdict table, the window
  diagnostics that mark the declared ±14-day window inadmissible, the 15-point threshold
  sweep, and the timing test. The four lines of evidence in §3.3's amendment are each
  readable off those six tables without re-running anything.
- The whole §1.4 window sweep as a **result**, from `results/window_sweep/`: the Gate
  1–3 pass rates, extraction-failure rates, harvest-identification shares and §3.8
  coefficients at all five endpoints, plus `window_sweep_control_check.csv`, which is
  the column-by-column comparison of the no-truncation arm against the committed
  panel. Re-deriving those tables needs the five panels above; reading and checking
  them internally needs nothing.
> ### Provenance change, 2026-09-15 (eleventh pass) — the pixel panel the figures were drawn from, and the one they are drawn from now
>
> Until this pass `figures/figure_provenance.json` recorded
> `results/phen_panel_sar.csv` = `d0559979df253232c623ba4084b710c5`. **No file with
> that hash exists anywhere the author can still reach it**, so that recorded input
> had become uncheckable rather than merely absent. What does exist is the replayed
> panel from the 2026-09-14 reproducibility run,
> `046d6029b3b131c5a06fb6ca9000d9ad` (35,905,793 bytes, 90,000 rows), and the
> manifest now records that one.
>
> **What the control run tested, stated exactly.** A full `make_figures.py` run at
> the unchanged patch20h code, taking the replayed panel as its only changed
> input, reproduced **all fourteen committed figure files** and the two derived
> tables that `make_figures.py` itself builds from that panel —
> `retention_by_terrain.csv` and `montecarlo_precision.csv` — byte-for-byte.
>
> **So the claim made here is exactly this and no more: the available replayed
> panel regenerates the current derived tables and figure content.** That is the
> scope of what was run.
>
> **Panel equivalence is NOT established, and must not be read in.** *(Narrowed
> 2026-09-15, twelfth pass: this block previously said "Whatever separates the two
> panels does not touch anything this repository derives from them." That
> generalised a test of one script to the whole repository and is withdrawn.)*
> The `d0559979…` panel does not exist anywhere reachable, so the two panels
> **cannot be compared field by field** and no statement about their equality is
> available. The control covered `make_figures.py` only. Other modules read the
> pixel panel — `gate1_justification.py`, `gate2_state_sensitivity.py`,
> `marc_agreement.py`, `mask_sensitivity.py`, `merge_static_covariates.py` and the
> `_static` panel used by `attrition_diagnostics.py` — and **none of those was
> covered by the control run**. A reviewer who wants the original panel cannot
> have it.
>
> The likeliest explanation for the difference is the last-bit floating-point
> variation this repository has already measured between two of its own containers
> (`results/window_sweep/window_sweep_summary.md`, OpenBLAS reduction order, 16th
> significant figure). That is a **candidate, not a finding**.
>
> **Provenance history, preserved.** The hash this manifest recorded before
> 2026-09-15 was `d0559979df253232c623ba4084b710c5`. It is kept here, and in the
> manifest's own `provenance_history` field, so the change is auditable rather
> than silent.
>
> **One standing limitation is lifted by this.** A full figure rebuild is no longer
> impossible: with the replayed panel present, `python/make_figures.py` with no
> `--only` runs to completion and reproduces every committed figure. It remains
> impossible **from a clone alone**, because the panel is still excluded on size.

- **That no committed figure has drifted from the hashes recorded for it** — which
  is a narrower statement than "every figure is reproducible from the committed
  tables", and the narrower one is what `python/make_figures.py --verify`
  supports. *(Narrowed 2026-09-15, fourteenth pass: the wording here used to read
  "every committed figure was produced from the committed tables", which a reader
  could take as a reproducibility guarantee that this repository cannot give while
  one input is excluded.)*

  `--verify` compares the generator, every input present and every output against
  recorded hashes. **It re-runs nothing.** It reports **VERIFY INCOMPLETE -- 0
  changed, 1 not present here** and exits 0, because `results/phen_panel_sar.csv`
  (35.8 MiB) is excluded on size.

  **What that does and does not cover, precisely:**

  | | from a clone alone |
  |---|---|
  | integrity of the 14 committed figure files against recorded hashes | **yes** |
  | integrity of the 10 inputs that ARE committed | **yes** |
  | integrity of `results/phen_panel_sar.csv` | **no — the file is absent** |
  | redrawing fig3, fig4, fig7 from committed derived inputs | **yes** (`--only fig3,fig4,fig7`) |
  | redrawing **fig2** | **no — it reads the excluded pixel panel directly** |
  | rebuilding `retention_by_terrain.csv` or `montecarlo_precision.csv` | **no — both are derived FROM the excluded panel** |
  | a full `make_figures.py` run with no `--only` | **no** |

  So **fig2 cannot be reproduced from a clone**, and the two derived tables that
  feed fig3 and fig7 cannot be rebuilt from one either — they are reused after
  their recorded hashes are checked, which is an integrity check and not a
  reproduction. Anyone who wants to reproduce those must obtain the excluded
  panel; the deposition listed at the top of this file is where it goes.

  `--strict` turns a missing file into a failure, which is what `run_all.sh` uses,
  where every input exists.
- **The §3.10 attrition tables, with the exact command that produced them.**
  Both levels were run CLEAN, with no `--resume`, at 9,999 replications, and
  the full invocation and console output are committed beside the tables as
  `results/s310_v2_<level>/run_clean_noresume.log`. The run key written by
  each run (`run_key.json`) records repository-relative logical paths and
  LF-normalised content hashes for the panel, the exposure catalogue, the
  phase-exposure table and the estimator source, so a reviewer can confirm
  which bytes produced which table. `--resume` exists but is NOT how these
  were produced: it recomputes only the attrition-diagnostic strata, so it is
  a convenience with a sampled provenance check rather than a guarantee.
- **The comparison totals quoted in any handoff**, by running
  `python python/compare_tables.py --base <parent> --cand <candidate>`. The
  buckets partition every field and the tolerance is a reported parameter.
- **The entire declared district headline**, by re-estimating it:
  `cd python && python3 permutation_test.py --level district --n-perm 2000`.
  It reproduces `results/permutation_test/Table_SX_Permutation_district.csv` byte
  for byte.
- Every reported number, against the committed results tables.

**With the full archived input package (or newly regenerated Earth Engine exports),
the MARC NetCDF, the frozen pre-run reference panel and separately rebuilt exposure
catalogues:** the intended end-to-end command is `bash run_all.sh all`. An Earth
Engine account alone is not sufficient. The runner stops if any of those inputs is
missing; `analysis/current_audit_status.md` records the current execution status.
No stage now depends on an export whose generating script and configuration are
undescribed; that is narrower than saying every external input is in the repository.

**What cannot be verified from here by anyone:** that the Earth Engine collections
themselves have not changed since the exports were taken. `COPERNICUS/S1_GRD` and
`ESA/WorldCereal/2021/MODELS/v100` are versioned, and the catalogue values this
study depends on are recorded in the scripts that read them — for WorldCereal, the
asset id, the `product` value and the cropland code of 100, each printed by a
verification block that still runs on every execution so a later revision cannot
pass silently.

## Archive — current status, 2026-09-14

**The deposit exists and is complete, and it is not public.** All **10** intended files are
uploaded at **100%** to the **unpublished Zenodo draft `22750338`**, including
`Paper2_raw_inputs_2017-2025.zip` (md5 `dd6c208a27ce86555fd34cd8f13a1b6c`) — the raw exports
this file describes as excluded above.

Four things follow, and each matters for how this file may be cited.

1. **Uploaded is not released.** The draft has **no DOI**. Nothing in this repository, the
   protocol or the manuscript may cite a DOI, assert public availability, or describe the
   archive as published until the record is released.
2. **This file remains the statement of record** until that release, and should then be
   replaced by the DOI rather than supplemented with it.
3. **The replay kit in the draft is pinned to `fc5eadb6292dfba945cf53c2b1f4eea9b8d75019`.**
   It must be refreshed after the final accepted commit, or the archive will describe code
   the paper does not use.
4. **The rows above still stand as written.** They describe what a reader can regenerate from
   *this repository*, with no Earth Engine account and no archive access. The deposit changes
   what will be available on release; it does not change what a clone contains today.

*(Corrected 2026-09-14, eighth pass. This section read "§5.1 commits the full panels to a
Mendeley Data v3 archive with a Zenodo mirror as a versioned release. Until that DOI exists,
this file is the statement of record." That was written before the upload and understated the
position: the files are already deposited. The Mendeley route is superseded by the Zenodo
draft above. No Zenodo record was created or modified by this repository or by any patch.)*
