# Re-audit brief — RiceBaCI-QC (Paper 2)

**For:** the reviewer who audited this repository at `a59f5fa` and produced the
findings answered in `AUDIT_RESPONSE_2026-09-13.md`.

**Repository:** `github.com/pandasupranab/RiceBaCI-QC` (private), branch `main`.
**Audited state then:** `a59f5fa`. **State now:** see the repository — this header
named `cb0e330` while `main` had moved to `1d4de62`, which the re-audit caught.
GitHub `main` is the source of record; this file is not.
**The commits to re-audit are those after `a59f5fa`**, the earliest listed below.

This brief is written to make the re-audit efficient and to point it at the places
most likely to be wrong. Section 4 lists defects found in this project's own work
since the last audit — including several found by the author rather than reported.
Those are the places to push hardest, because a codebase that has produced twelve
self-inflicted defects in two days will produce a thirteenth. Entry 10 is the one that
matters most — it casts doubt on the counts in the others — and entry 11 is what
finding entry 10 immediately exposed.

---

## 1. The six commits

| commit | what it did |
|---|---|
| `775aef2` | Closed the retained-only defect; resolved all five predeclared hypotheses (verdicts corrected later the same day — see §3); amended the protocol at §4.1–§4.3 |
| `1a93678` | Added `analysis/test_classification.md` (every test classified A / B1 / B2 / C); rewrote figure 5, which was stale and carried a withdrawn causal claim |
| `684f928` | Made figure output byte-reproducible **within one recorded test environment** (matplotlib and freetype fixed; cross-environment byte identity, and cross-environment pixel identity, are separate claims and are not made — scope stated 2026-09-15); added `figures/figure_provenance.json` and `make_figures.py --verify` |
| `7c163a0` | Ran the §3.5 mask-comparison arm at both levels in two variants; closed §4.3.4 |
| `9d61a6e` | Fixed a reproducibility defect in `run_all.sh` stage 13; added `DATA_AVAILABILITY.md` |
| `cb0e330` | Made the stage-13 guard fire before any work, so it is demonstrable from the repository alone |

---

## 2. Disposition of the previous findings

| finding | disposition |
|---|---|
| Hard-coded absolute paths made scripts unrunnable off the authoring machine | Fixed. One `RICEBACI_ROOT` relocates everything; a `_find_doc()` resolver in 10 scripts locates committed `docs/` inputs from any working directory. Verified by relocating the code **and** removing the data, not by relocating alone. |
| The export script had no dry-run and would have spent 25 tasks on a structural defect | Fixed and used. `S1_MASK_FLAG.js` has `verifyOnly` (0 tasks) and `dryRunDistrict` (1 task). Both were exercised; the verification block caught a real defect (§4 below) and the dry run was checked before the 25-task run was authorised. |
| H3's construct mismatch: predeclared on SOS / peak / EOS, estimator produces trough / heading / drainage / harvest | Recorded, not papered over. §4.3.1 authorises the mapping for **direction only, never identity**; outcomes are named as fitted breakpoints in every table and figure. |
| §3.5 mask comparison not run, no script implemented | **Run.** Section 3 below. §4.3.4 carries a dated amendment; the original text is left in place per the append-only rule. |
| H5 unsupported by available data | Withdrawn by dated amendment (§4.3). |
| The r-value grid was undocumented | Documented at §4.3. |
| GitHub state was behind the analysis | Current. Every result now in the repository. |
| README did not orient a reader | Rewritten, and `DATA_AVAILABILITY.md` added (§5 below). |

---

## 3. The substantive results, stated so the asymmetry is visible

> **Correction, 2026-09-13 (later the same day).** The sentence below — "all five
> predeclared hypotheses fail" — is **wrong as a summary and was result-aware**, and
> `analysis/hypothesis_verdicts.md` now carries the authoritative verdict table,
> checked number by number against the committed results. The accurate sentence: of
> the five predeclared hypotheses, **one fails on its declared criterion (H4, 2 of 6
> signs)**; **two fail on one clause while their other clause passes as declared (H1,
> H2 — clause (a)'s tolerance is 0.90 and the measured within-tolerance shares are
> 0.9443 / 0.9114 / 0.9387, so clause (a) PASSES)**; **one is not estimable as
> declared (H3 — the declared quantities are optical SOS / peak NDVI date / EOS and
> this study never estimated them)**; and **one was withdrawn untested (H5 — MODIS was
> never obtained, which is not a failure)**. Every paragraph below that says or implies
> "all five fail" is superseded by that table. The paragraphs are left in place rather
> than rewritten so that the claim and its correction are both on the record.

**SUPERSEDED — do not quote:** **All five predeclared hypotheses fail**, each for a measured reason. That
conclusion is unchanged since `a59f5fa`. What has changed is that the §3.5 arm now
tests whether the surviving measurement results depend on the cohort mask.

### 3.1 The place to look first: the timing placebo's level asymmetry

§3.9's timing placebo is β_harv on SOS, declared zero. Within-state permutation,
2,000 draws — a conditional spatial sensitivity. **Correction 2026-09-16:** the
earlier bootstrap-calibration rationale is withdrawn. Comparing permutation
quantiles with 1.96 does not test bootstrap size, and within-state relabelling
requires an unverified exchangeability assumption. See Protocol §4.1.7.

**Pixel level, p_perm by robustness arm:**

| arm | coef | t | p_perm | treated clusters |
|---|---|---|---|---|
| frozen (50 km, 48 kt) | +7.438 | 4.22 | **0.0395** | 18 |
| buffer 75 km | +6.436 | 4.47 | **0.0210** | 20 |
| buffer 100 km | +6.063 | 4.63 | **0.0105** | 23 |
| state × season FE | +4.493 | 3.54 | **0.0075** | 18 |
| severity 64 kt | +4.761 | 1.20 | 0.4518 | 6 |

**4 of 5 arms reject at 5%.** The one that does not has 6 treated clusters, where
MacKinnon & Webb (2018) makes a null uninformative.

**District level, the same cell:**

| arm | coef | t | p_perm |
|---|---|---|---|
| frozen | +5.001 | 1.61 | 0.3068 |
| buffer 75 km | +5.432 | 2.07 | 0.0980 |
| buffer 100 km | +6.330 | 2.94 | **0.0205** |
| severity 64 kt | +6.627 | 1.20 | 0.3358 |
| state × season FE | +0.721 | 0.21 | 0.8186 |

**1 of 5 rejects.** §3.8 declares the **district** panel as the headline.

So, put plainly: **the placebo fails robustly at pixel level and is not rejected at
the declared district headline.** The coefficient is positive and of similar
magnitude at both levels (+5.0 against +7.4 on the frozen arm); what differs is
precision, with 25 clusters and 18 treated at district level. This project's
reading is that the district non-rejection is a power result rather than evidence
of a clean placebo, and that the pixel-level failure is the substantive finding —
because a null that only appears where power is lowest is not reassurance.

**This is the single interpretation in the paper most in need of adversarial
review.** If the counter-reading is that §3.8's declared headline simply passes its
placebo and the pixel-level failure is a property of a non-headline level, that
would materially change what the paper can claim, and it should be argued out now
rather than at review.

### 3.2 H3 fails with the wrong sign, and it is robust

> **Correction, 2026-09-13 (later the same day), two parts.**
>
> **(a) It is not H3, and it is not EOS.** H3 declares β_pre on *EOS*, an optical
> phenological construct. This is β_pre on the *harvest breakpoint* of a radar
> five-segment model, which §3 states is not that quantity and §4.3.1 authorises for
> **direction only, never identity**. MARC now makes the gap quantitative: the harvest
> breakpoint sits **+50.4 d** later than MARC's harvest date, positive in all 25
> districts, MAD 3.1 d. So H3 is **not estimable as declared**, and this cell is the
> exploratory radar-breakpoint analogue, reported as such.
>
> **(b) It survives two further tests run after this brief was written, and the
> heading's word "robust" is now earned rather than asserted.** The §1.4 window sweep
> found that **8.2% of estimable district-seasons (17 of 208) have no valid dekad
> after the harvest breakpoint**, so their harvest date is where the fitted fall
> *would* reach baseline rather than an observed return to it. Re-estimating on the
> units that do have a post-t4 observation: **−10.184 (t −2.08) → −8.084 (t −2.12)**.
> Sign preserved, t unchanged, magnitude attenuated by the 13% sample loss. The
> coefficient does not rest on an extrapolated harvest date. Details and the full
> five-endpoint table: `python/window_sweep.py`, `results/window_sweep/`.

β_pre on EOS is significant with the **wrong sign** at both levels: district
−10.184 (p_perm 0.0075), pixel −3.351 (p_perm 0.0005). Robust across all 10
arm × level cells, and it **strengthens** under the WorldCereal mask
(pixel −3.351 → −4.044).

### 3.3 ~~H1/H2 fail on the instrument, not the phenology~~ — HEADING WITHDRAWN 2026-09-14

> **Correction, 2026-09-13 (later the same day).** Clause (a) does **not** fail. §2
> declares agreement "within a pre-declared tolerance… fixed on the untreated 2017
> baseline season before any treated season is fitted", and `orbit_agreement.py` fixes
> T as the 90th percentile of |orbit difference| on 2017 and requires a 0.90
> within-tolerance share. Measured: **0.9443 / 0.9114 / 0.9387** — clause (a) is
> **MET as declared** for all three markers. The figures quoted below (r, and the
> share within one dekad) are a **different and stricter criterion that §2 never
> declared**, and reporting them as the verdict was reading the hypothesis against a
> test chosen after seeing the result. Clause (b) does fail: 1.340 / 1.508 against a
> declared < 1. What follows is therefore **H1/H2 failing on clause (b) only**.
>
> Two methods that share no arithmetic now agree on the σ that drives clause (b): the
> between-orbit estimator gives 25.90 / 19.82 / 25.79 d and the semivariogram nugget
> gives **25.68 / 20.57 / 25.30 d** — within 0.8 d. The same analysis shows the
> coherence is **regional, not field-scale**: the 0–4 km lags are flat (spreads 1.78 /
> 0.61 / 0.54 d) while 64 km+ reaches 30.36 / 22.37 / 29.34 d.

Clause (a): σ ≈ 26 d, r +0.339 / +0.147, 38.2% / 35.0% within one dekad.
Clause (b): 1.340 / 1.508. Model-implied ratios **0.441 / 0.724**.

> **Correction, 2026-09-14 (fifth pass) — this section's heading and its closing
> sentences are withdrawn.** They read "H1/H2 fail on the instrument, not the
> phenology … the crop claim appears true and the instrument is the reason the test
> fails. The study's positive contribution is the located boundary: ±1.3 d on a
> district-season mean marker against σ ≈ 26 d on a pixel-season." **Both claims are
> withdrawn.** The variance subtraction is a conditional sensitivity calculation on
> five untested assumptions, numerically fragile (a σ **3.613470%** higher drove the
> trough's implied within-variance to zero), and built on a between-pixel factor that is
> itself wrong under unbalanced season counts. **The calculation is retired entirely as of
> 2026-09-14 (sixth pass)** — Protocol §4.2.3 records the four defects and the decision, and
> nothing in the active result set carries a corrected ratio. What replaces it is the
> observed single-orbit recomputation: ratios 1.327845 / 1.577191 / 1.475027, all above the
> declared criterion of 1, so clause (b) fails as measured and **why it fails is not
> identified**. The scale boundary was retired on 2026-09-14
> (§1.5.4 item 1): ±1.3 d is simulated precision under measured noise and σ is an
> observed disagreement in a selected paired sample, so the two are not commensurable
> and no ratio between them is reported. This brief is a **dated, superseded**
> document — `REAUDIT_BRIEF_2026-09-14.md` is the current one — and is corrected in
> place rather than rewritten.

### 3.4 §3.5 mask arm — the new work in `7c163a0`

Design: hold the cohort fixed, flag all 10,000 committed points against ESA
WorldCereal 2021 v100 `temporarycrops`, filter the 225 raw exports to the flagged
points, and re-run **the committed estimator**. 8,085 points retained (80.85%);
per district 46.0% to 98.3%; no district at 0% or 100%.

The arm deliberately does **not** re-implement the aggregation. The district panel
is a five-segment PLSM fitted to the district-season **mean curve**, not an average
of pixel phenometrics, so a pixel mask cannot be applied to the committed panel
after the fact — the curve must be rebuilt and refitted. A re-implementation would
have made the arm a test of the re-implementation.

Result on the placebo cell:

| arm | level | committed | masked | p_perm |
|---|---|---|---|---|
| mask | pixel | +7.438, t 4.22 | +7.909, t 4.73 | 0.0395 → **0.0185** |
| mask, overlap excluded | pixel | +7.438, t 4.22 | +7.808, t 4.64 | 0.0395 → **0.0195** |
| mask | district | +5.001, t 1.61 | +6.431, t 1.62 | 0.3068 → 0.3463 |
| mask, overlap excluded | district | +5.001, t 1.61 | +6.356, t 1.60 | 0.3068 → 0.3633 |

Across all 24 cells: **0 material sign flips** (four cells change sign; all four had
committed |t| < 0.6 — noise changing sign, which is why the table carries
`sign_flip_material`, requiring committed |t| > 2 before a flip counts). Four of 24
cells cross |t| = 2, all at district level, all downward, all from just above the
line to just below.

Two things deliberately bounded rather than assumed:

- **Mosaic arbitrariness.** WorldCereal ships overlapping per-AEZ tiles and the
  export mosaicked them, so where two tiles disagree the pick is arbitrary. 62 of
  10,000 points (0.62%) fall under two tiles, 59 flagged cropland. The whole arm
  was re-run with those 59 dropped; p_perm moves by 0.001 at pixel level.
- **Nesting.** The masked sample is nested at pixel level (1,448 retained
  pixel-seasons lost, 0 gained) and **not** at district level (4 district-seasons
  become fittable, 2 stop). The district arm is a different sample, not a
  subsample. An earlier version of the output asserted nesting at both levels; that
  was wrong and is corrected. The script now measures it per level.

**What this arm does not establish:** WorldCereal v100 has no rice layer, so this
is a general-cropland classifier and §3.5's verbatim disclosure still binds. The
arm shows the reported measurement results do not depend on the mask. It does not
show the cohort is rice.

One result is worth separate scrutiny because it is the **only external
corroboration of the cohort anywhere in this study**: over Puri's bounding box
WorldCereal calls 30.9% of the area cropland; at Puri's cohort points, 86.5% — a
2.8× enrichment. Please attack this if it is weaker than it looks. The bounding box
includes sea, which inflates the contrast, and the comparison is against a
bounding box rather than the district polygon.

---

## 4. Defects found in this project's own work since `a59f5fa`

Listed because they are the best available evidence of where this codebase fails,
and because eight of the twelve were found by the author after the code was already
pushed — and the tenth undermines the evidence for the rest. Each is logged with a dated entry.

1. **`fit_cell` omitted `retained == 1`.** Caught by a self-test (+4.7582 against
   +5.0010). Fixed inside the function, because a caller can forget.
2. **Figure 5 was stale and carried a withdrawn causal claim.** Generated 11:08
   against tables corrected at 15:15 and 15:52; title asserted "Heading is delayed
   by about a week". Rewritten; `fig5()` now refuses to run without the corrected
   table.
3. **PDF timestamp churn destroyed the figure hash check.** Six PDFs in `1a93678`
   differed from their parents in exactly 6 bytes, all inside `/CreationDate`. This
   cost the one check that catches defect 2. Fixed by freezing `SOURCE_DATE_EPOCH`
   **and** adding a provenance manifest, since freezing alone would have removed
   the only staleness signal.
4. **`S1_MASK_FLAG.js`'s own verification block was broken.** VERIFY 3 probed the
   raw cohort asset, whose geometries are empty because the asset carries lon/lat
   as properties — the exact failure the file's header warns about three sections
   above the line that committed it.
5. **`run_all.sh` stage 13 omitted `--n-perm`.** A full pipeline run would have
   silently overwritten the committed mask tables with column-poorer ones; three of
   the **eight** files in `results/mask_sensitivity/` were unreproducible by the
   pipeline that claims to produce them. (`9d61a6e`'s commit message and the log
   entry for it both say "three of the nine files". That is wrong — there are
   eight. Corrected here rather than in the committed text, per the append-only
   rule.) Found by auditing the stage minutes after pushing
   it.
6. **The guard fixing defect 5 was not demonstrable from the repository.** It fired
   only after the panels were loaded, and the panels are not committed — so a
   reviewer could not confirm the protection. Reordered to a pre-flight check that
   needs no data. Found by the executor's run, not by the author.
7. **Two self-tests that could not fail.** Both asserted a local expression rather
   than the function under test (`... or True` in one case). Both are now real
   tests. The pattern to look for: an assertion whose truth does not depend on the
   code it names.

8. **A wrong denominator in `9d61a6e`'s commit message and log entry** — "three
   of the nine files in `results/mask_sensitivity/`" when there are eight. Found
   by fact-checking every number in this brief against the files: 73 of 74
   verified, and this was the one that did not.
9. **`make_figures.py --verify` failed for a reason that was not a defect — and
   this brief told you to run it.** On a checkout without the excluded panel it
   reported `VERIFY FAILED` and printed the stale-figure explanation, when the
   count was `0 changed, 1 missing`. Nothing had drifted; one input
   (`results/phen_panel_sar.csv`, 35.8 MiB) is excluded on size and so could not
   be compared. A reviewer following §5 of the first version of this brief would
   reasonably have concluded the figures did not match the tables. The verdict now
   separates *missing* from *changed*: `VERIFY INCOMPLETE` and exit 0 for absence,
   `VERIFY FAILED` and exit 1 only for a real change, with `--strict` for the
   pipeline. Fixed in `c24ba32`.

10. **The author's verification baseline was a self-built artifact that silently
    omitted 47 of 110 results files, and was never validated.** Every
    "expected staged file count" given to the executor was computed against a
    reconstruction assembled from a snapshot zip plus subsequent patches — not
    against the repository. The zip had been created with exclusions that were not
    recorded: 35 `results/*.csv` where the working tree had 75. Two manifests were
    consequently wrong (`1a93678`'s "expect 18" and `c24ba32`'s "expect 11"), both
    caught by the executor's `git add -A`, which was authoritative both times.

    **This is the most important entry in this list, because it casts doubt on the
    other nine.** Every count in them was checked rigorously against the wrong
    object. The immediate consequence: `c24ba32`'s own commit message claims six
    figure inputs were uncommitted and that committing 138 KiB made the headline
    reproducible. Both are false — it was one input, and
    `results/phen_panel_district_season_static.csv` has been tracked since
    **`a59f5fa`, the commit you audited.** The headline was reproducible from the
    repository at the state you examined; nobody had checked, including the author.
    Corrected in `DATA_AVAILABILITY.md`, in this brief, and by a dated log entry;
    the commit message itself cannot be changed. The baseline is now taken from
    `git ls-files -s` blob SHAs, which are verifiable against any local file.

11. **Five committed tables carried withdrawn numbers, and one was named
    `_final_`.** `results/Table_SX_AttritionDiagnostic_*.csv` — five files — held the
    pre-correction §3.10 output: district placebo +4.7582 on 213 observations where
    208 are retained, and pixel +4.7737 on **76,717 observations where 31,741 are
    retained, so 58.6% of the rows should not have been there.** The authoritative
    tables under `results/s310_v2_*/` give +5.0010 and +7.4384. The contaminated
    pixel estimate understated the very placebo failure the paper reports.

    No script reads them, so this was never a live computation error. It was worse in
    one respect: `make_figures.py`'s `fig5` docstring already recorded that the
    district file was defective and refuses to plot it, so the defect was known, the
    consumer was guarded, and the artifact was left in `results/` under a name a
    reader would trust — with `final` on the bad table and nothing on the good one.
    Moved to `results/superseded_pre-2026-09-13/` with a README naming the
    replacement for each and explaining both defects. **Found by using the
    `git ls-files -s` baseline from defect 10 to read the repository's real file
    list** — the reconstruction it replaced had been concealing this all along, which
    is the sharpest argument for entry 10 being the important one.

12. **Four directory READMEs described a project that does not exist, and one
    described a withdrawn design.** `figs/`, `qc/`, `osf/` and `manuscript/`
    READMEs, all dated 2026-09-04 — before the Sentinel-1 substrate change — named
    **13 files and scripts of which zero are tracked.** `figs/README.md` is the one
    that matters: under the heading "Pre-registered figure list" it described, in the
    present tense, `fig1_study_area.pdf` ("Amphan landfall, treatment + control
    districts"), `fig3_did_coefplot.pdf` ("DiD coefficient plot"),
    `fig4_event_study.pdf` ("with parallel-trends test") and
    `fig7_parallel_trends.pdf`. **§4.1 withdraws every causal claim from §3.8.** A
    reviewer opening that directory — next to `figures/`, which holds the fifteen
    real files — would have concluded this paper runs a difference-in-differences on
    treatment and control districts. It does not. All four are rewritten; `figs/` and
    `qc/` now say UNUSED in their headings.

    Also in the same pass: the five `results/s310_*.log` transcripts of the
    superseded runs, carrying `+4.758` and `+4.774` in plain text with nothing
    marking them retracted, two of them named `s310_final_*`. Moved alongside their
    tables. Defect 11 fixed the artifact that was noticed; this fixed the class.

**Suggested probes.** Grep the self-tests for assertions that do not call the
function they claim to test; two were found that way and a third would not be
surprising. Run every command this brief tells you to run — defect 9 was in one of
them. Treat every *count* in this repository's logs and commit messages as
unverified until checked against `git ls-files`, per defect 10. Check `results/` for any other artifact that a guard in
the code quietly works around rather than removes — defect 11 was one. And read every
orientation document — directory READMEs above all — against the file list, because
defect 12 was four of them describing a project that does not exist.

**Where the sweep stopped, and why.** Eight candidates were tested against one
question: could a reviewer read this file and take something withdrawn as current?
Four needed changing (the five tables, the five logs, `figs/README.md`, and three
further READMEs) and **four did not**: `results/censoring_test/Table_SX_CensoringTest.csv`
is the documented `--collect` merge, `results/Table_SX_EventStudy.csv` is current,
the `*.partial.csv` files are resume artifacts of the corrected runs, and
`docs/candidate_cohort_v1.csv` is unambiguous in its name. A sweep that finds a
problem everywhere it looks is not a sweep.

---

## 5. What can be verified with nothing but the repository

No Earth Engine account needed. All four of these were run against a
reconstruction of the committed tree before this section was written, which is how
defect 9 was found:

    bash run_all.sh selftest                       # 10 scripts, all PASS
    cd python && python3 mask_sensitivity.py --selftest      # 27 checks
    cd python && python3 make_figures.py --verify --out ../figures
    cd python && python3 permutation_test.py --level district --n-perm 2000

The third reports **VERIFY INCOMPLETE -- 0 changed, 1 not present here** and exits
0. That is the expected result, not a failure: one figure input,
`results/phen_panel_sar.csv` (35.8 MiB), is excluded on size. Nothing has drifted
and every file present matches its recorded hash.

The fourth **re-estimates the entire declared district headline** and reproduces
`results/permutation_test/Table_SX_Permutation_district.csv` byte for byte (md5
`6f62cb2fd688af4c33e0e11b96aa7e8b`), confirmed by an independent executor. §3.8
declares the district panel as the headline, so the headline is independently
checkable from this repository alone — please do check it.

**It was checkable at `a59f5fa` too**, the state you audited:
`results/phen_panel_district_season_static.csv` has been tracked since that commit
and `phen_panel_district_season.csv` since `be4079e`. An earlier version of this
section claimed the capability was created on 2026-09-13 by committing those
files. That was wrong — see defect 10. If the previous audit did not exercise this,
it is the single highest-value check available, because it tests the declared
headline end to end rather than any claim about it.

And the guard from defect 5/6, which **should fail** — exit 1 is correct, and the
target table's md5 must be unchanged at `49a8e47e0329e403b36d5a9b7b5ec7db`:

    cd python && RICEBACI_ROOT=.. python3 mask_sensitivity.py --compare --level district

`make_figures.py --verify` re-hashes every table each figure was drawn from and
every figure file, so it establishes that the committed figures were produced from
the committed tables without re-running anything.

`DATA_AVAILABILITY.md` states what is excluded and why: the 225 panel exports
(712 MiB, 4,950,225 rows) and 225 per-orbit exports (281 MiB, 3,719,836 rows).
Both are deterministic functions of the committed cohort
(`docs/candidate_cohort_v2.csv`, 10,000 points) and the committed `gee/` scripts.
The 25 mask exports **are** committed (441 KiB), which makes the §3.5 arm's
structural gate runnable with no Earth Engine account. So are the district-season
panel, its `_static` form, and the four remaining figure inputs.

**What nobody can verify from here:** that `COPERNICUS/S1_GRD` and
`ESA/WorldCereal/2021/MODELS/v100` have not changed since the exports were taken.
The catalogue values this study depends on are recorded in the scripts that read
them, and `S1_MASK_FLAG.js`'s verification block still runs on every execution so a
later revision cannot pass silently.

---

## 6. Where scrutiny is most wanted

1. **§3.1's level asymmetry.** Is the district non-rejection of the placebo a power
   result, as this project reads it, or does §3.8's declared headline simply pass?
   This changes what the paper may claim.
2. **The 2.8× WorldCereal enrichment.** Bounding box includes sea. Is the contrast
   real enough to report as corroboration, and should it be against the district
   polygon instead?
3. **The district arm of §3.5 is not a nested subsample.** Is a comparison against
   the committed headline still interpretable when 4 district-seasons enter and 2
   leave, or does that need a separate framing?
4. **H3's direction-only mapping** (§4.3.1). Is "direction only, never identity"
   sufficient, or does the construct mismatch require withdrawing H3 rather than
   reporting it as failed?
5. **Whether any test remains that cannot fail** (§4.7), whether any other claim
   here is an unexecuted instruction (§4.9), and whether any other *count* in the
   logs was computed against the wrong baseline (§4.10). The third is the one I
   cannot rule out myself, because the same faulty baseline was used throughout.
6. **Whether the append-only logs are now so long that a reader cannot find the
   superseded decisions.** `analysis/decisions_log.md` carries 27 entries dated
   2026-09-13 alone. `analysis/test_classification.md` is the intended index; if it
   does not do that job, say so.

---

## 7. Standing status

- ~~All five predeclared hypotheses **fail**.~~ **Corrected 2026-09-13, later the
  same day:** one fails on its declared criterion (H4); two fail on one clause while
  the other passes as declared (H1, H2); one is not estimable as declared (H3); one
  was withdrawn untested (H5). `analysis/hypothesis_verdicts.md` is authoritative.
  §4.1 still withdraws every causal claim from §3.8, and nothing in these commits
  restores one — that part stands unchanged.
- `run_all.sh` has **no remaining Earth Engine dependency** and no open protocol
  item.
- **No manuscript Results, Abstract or Conclusions have been written**, by
  instruction, pending this re-audit.
