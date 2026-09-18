# RiceBaCI-QC — Paper 2 repository

> Clean public code/results release (2026-09-18):
> https://github.com/pandasupranab/RiceBaCI-QC-release
> Code: MIT (`LICENSE`). Author-created data/results: CC BY 4.0
> (`LICENSE-DATA.md`); upstream rights are retained (`THIRD_PARTY_NOTICES.md`).
> The raw-data Zenodo deposit is not yet public. Read
> `RELEASE_NOTES_2026-09-17.md` for provenance and the remaining release gates.

**Current paper title:** *Between-orbit repeatability and interpretation limits
of Sentinel-1 rice phenology breakpoints along the Bay of Bengal coast.*
The study measures breakpoint repeatability and tests the
limits of interpreting those breakpoints as agronomic dates or cyclone-response
outcomes. Cyclone contrasts are descriptive stress tests, not causal effects.

**This study was not pre-registered, and §5.2 of the protocol forbids saying it
was.** The QC thresholds and hypotheses in §3 were fixed in `docs/Protocol_v1.md`
(commit `2cf493a`, dated 2026-09-07) before the full multi-state extraction was
run, according to the preserved private development history at
`github.com/pandasupranab/RiceBaCI-QC`. That older repository remains private
because it contains third-party reference PDFs. Historical commit identifiers
in these records refer to that private history, not commits available in this
new clean repository. The public snapshot alone does not independently prove
the historical timing. That is the whole of the claim. *(This line read "a pre-registered test" until
2026-09-13, in direct contradiction of §5.2, which had prohibited the phrase since
the protocol was written. Found by an external audit, not by the author.)*

**GitHub `main` is the source of record.** Any loose copy of the protocol, the logs
or the results elsewhere on disk may be older than the repository and should not be
cited.

**Current-document map.** Read `docs/Protocol_v1.md` for the design and dated
amendments, `analysis/hypothesis_verdicts.md` for the current verdicts,
`docs/LitGap_v0.2.md` for the executed literature search and claim boundaries,
and `DATA_AVAILABILITY.md` for the exact reproducibility scope. `docs/LitGap_v0.1.md`,
`python/README.md`, `gee/README.md`, and `python/apply_round*.py` preserve planning
or one-time migration history; they are not current scientific or execution
instructions.

**This README was rewritten 2026-09-13.** The previous version described the
Sentinel-2 optical design, which was superseded on 2026-09-09, and promised a
`requirements.txt` and `run_all.sh` that did not exist. Both now do.

---

## What this study found

> **Corrected 2026-09-14.** This section said "**Every one of the five predeclared
> hypotheses fails**" with NOT MET against H1, H2, H3 and H4. That was withdrawn as
> result-aware on 2026-09-13 and the correction was propagated into the re-audit brief
> but **not into this file, `analysis/test_classification.md` or `osf/README.md`** — so
> the repository carried three contradicting answers to its own central question for a
> day. Found by an external re-audit, not by the author. The table below is the
> corrected one; `analysis/hypothesis_verdicts.md` is authoritative and every figure in
> it was checked against the committed results tables.
>
> **Superseded later the same day: it was not three files, it was six.** A second sweep —
> by meaning rather than by phrase — found the withdrawn verdict still standing in
> `docs/Protocol_v1.md` §4.2.6 (headed "Per-hypothesis status, **final**", contradicting
> §4.2.2 above it and §4.2.7 below it), in §4.3.1 ("the verdict is unchanged: H3 NOT MET"), and in a
> reviewer-checklist line of `analysis/test_classification.md` whose *table* the first pass
> had already corrected. All three now carry dated corrections. The cause of the miss is
> recorded in `analysis/decisions_log.md`: the first pass searched for the propagated
> summary sentence, and these three state the same verdict in a different shape.

**Of the five predeclared hypotheses: one fails on its declared criterion, two fail on
one clause while their other clause passes as declared, one is not estimable as
declared, and one was withdrawn untested.** Each outcome is measured, not asserted, and
the reasons are more useful than a positive result would have been.

| | verdict | why |
|---|---|---|
| **H1** radar trough consistency | clause (a) **MET**, clause (b) FAILS | (a) the *declared* test is agreement within a tolerance fixed on the untreated 2017 baseline: **0.9443** within T = 70 d against a 0.90 criterion. The 38%-within-one-dekad figure previously quoted here is a **stricter test §2 never declared**. (b) dispersion ratio 1.340 [1.273, 1.408], required < 1 |
| **H2** radar fall-end consistency | clause (a) **MET**, clause (b) FAILS | (a) **0.9114** within T = 60 d against 0.90; fails in Andhra Pradesh alone (0.8564, n = 195). (b) 1.508 [1.424, 1.592] |
| **H3** exposure shifts phenology | **NOT ESTIMABLE AS DECLARED** | §2 declares β on optical SOS, peak NDVI date and EOS. This study fits radar trajectory breakpoints, which §3 states are not those quantities — MARC puts the harvest breakpoint later than its harvest date in all 25 districts, by a mean of **+50.35 d** (per-district range **+26.19 to +60.54 d**; *made precise 2026-09-14 — the mean is not each district's offset*). The declared quantities were never estimated, so "fails" claims a test that was not run. The radar analogue is **exploratory**: 0 of 4 cells positive-and-significant, β_pre on the fitted fall-end breakpoint points **opposite to the predeclared analogue** at both levels (p_perm 0.0005 pixel, 0.0075 district) |
| **H4** transfers across cyclones | **FAILS on its declared criterion** | 2 of 6 sign agreements against a 5-of-6 criterion; pooled β₀ on harvest −13.04 d |
| **H5** MODIS coherence | **WITHDRAWN — not tested, not failed** | MODIS panel never acquired (§4.3.2). An untested hypothesis has no verdict |

### Two findings the failures produced

**1. The exposure design fails its own falsifiability check.** §3.9 predeclares
that severe harvest-window exposure cannot causally alter the observations
supporting the *same season's earlier radar trough breakpoint* — a storm three
to four months later cannot reach backwards. Measured:
**+7.438 d, p_WCB 0.0008, p_perm 0.0395** in the robustness arm, surviving the
pre-trend adjustment, IPSW, and four of five declared robustness arms. A
post-analysis censoring diagnostic shows that the association is
**estimator-dependent** on its common pixel sample: the five-segment estimate is
+4.941 d, the 28-dekad one-breakpoint estimate is −2.388 d, and their paired
difference is +7.329 d (p_WCB 0.0027). Separately, a synthetic −4 dB
post-window perturbation can move the full-window fitted trough by **20 days**.
These observations demonstrate a plausible estimator-deformation pathway; they
do **not** identify the cause of the observed association. The result is not a
shift in a field-observed transplanting date, and no §3.8 coefficient is
reported as a causal effect of cyclone exposure on rice phenology (§4.1).

**2. Two disagreement statistics, reported separately and never combined.** *(Heading
rewritten 2026-09-14, sixth pass. It read "The instrument's working level is located and
quantified", then "stated separately at two scales" — both claimed a scale boundary the
evidence does not support. See Protocol §4.2.3.)* On a single pixel-season, two relative
orbits place the same marker **25.90 / 19.82 / 25.79 d apart** for trough /
rise-end (`heading`) / fall-end (`harvest`), as sd(difference)/√2 — computed on
the 7,717 later-season pairs of the 8,515
usable orbit pairs, themselves 9.5% of the 90,000 candidate pixel-seasons. That identity
equals each path's error sd only under conditions this study has not tested, so it is
reported as a **scaled disagreement statistic, not an error** (Protocol §1.5.6 constraint
2). Separately, a Monte Carlo on a **synthetic** district-season trajectory at an assumed
mean noise of 0.122 dB reports standard deviations of **0.00 / 0.00 / 2.18 / 1.90 d**
for t1 / t2 / t3 / t4 over 80 draws in `results/montecarlo_precision.csv`
(`grid = free`), with signed errors 0.000 / 0.000 / -0.500 / +0.375 d.
The earlier **±1.3 d** summary is withdrawn: it is not supported by that archived
table. These are conditional results for one on-grid synthetic trajectory,
**not field-validated accuracy** or measured precision of the real district panel.
**The two numbers are not commensurable and no ratio between them is reported.**

A post-hoc marker-blind pair-selection sensitivity reaches the same pooled
clause-(a) verdict. Choosing the lowest eligible orbit numbers instead of the
declared best-coverage pair gives scaled disagreement of **25.85 / 19.85 /
25.78 d** for trough / rise-end (`heading`) / fall-end (`harvest`);
unit-weighting every eligible orbit
pair gives **26.18 / 20.03 / 25.83 d**. All three markers still exceed the
declared 0.90 within-tolerance criterion under both alternatives, including
when the declared 2017 tolerances are held fixed. This supports robustness to
the pair-selection rule; it does not establish accuracy or independent errors.

Recomputing H1/H2's clause (b) on a single orbit, so the dispersion and the between-orbit
statistic describe one estimator, leaves the observed ratio **above 1 on all three markers**
(1.328 / 1.577 / 1.475 on 6,602 pixels and 28,562 pixel-seasons). So clause (b) **fails as
measured** here too. That single-orbit sample is **selected separately** from the paired
sample, so the two sit side by side as observations and **no causal statement about why
clause (b) failed follows**. *(Narrowed 2026-09-14, eighth pass: this read "the failure is
not an artefact of comparing two estimators".)* *(Why it fails
is not identified. An earlier version of this section subtracted an assumed error variance
and reported a "corrected ratio" of 0.441, concluding the crop claim was true and the
estimator was the cause. **That calculation is retired** — Protocol §4.2.3 records the four
defects and the decision, and `results/orbit_agreement/README_DispersionSingleOrbit.md`
describes the columns it used to write.)*

The cyclone contrasts are also sensitive to the reference distribution:
within-state exposure-history permutations and the wild cluster bootstrap can
give different p-values. Comparing permutation |t| quantiles with 1.96 does not
test bootstrap calibration. Permutation results require exchangeability of
district exposure histories within state, which actual storm geography does not
guarantee. Both are reported as conditional, descriptive inference; neither
establishes a causal effect or identifies the source of the disagreement.

---

## Reproducing it

```bash
python -m venv .venv-analysis && . .venv-analysis/bin/activate
pip install -r environments/requirements-analysis.txt
python python/environment_check.py --profile analysis --receipt results/analysis-environment.json
export RICEBACI_ROOT=/path/to/data      # holds results/ and the export folders
export FROZEN_REFERENCE_RESULTS=/path/to/archived-reference-panel
export EXPOSURE_VARIANT_DIR=/path/to/verified-exposure-rebuild
export FIGURE_PYTHON=/path/to/figure-environment/bin/python
bash run_all.sh selftest                # counts and explicit exemptions printed by the runner
bash run_all.sh all                     # full analysis; the pixel 9,999-bootstrap arm takes hours
```

Use a separate environment from `environments/requirements-figures.txt` and pass
the `figures` environment check before redrawing figures. The full analysis also
requires the archived raw Earth Engine exports and the excluded pixel panel;
`DATA_AVAILABILITY.md` states exactly which stages a repository-only clone can and
cannot execute.

Use a new results directory for clean acceptance runs. Old filename-only orbit
fit caches are deliberately refused; do not delete the historical outputs to
make a run proceed. The exposure rebuild is generated with
`python/robustness_arms.py --rebuild --roster ... --gadm ... --ibtracs ... --variant-dir ...`
in an empty directory. `FROZEN_REFERENCE_RESULTS` must contain the separately
archived reference pixel panel and must not be the directory the run overwrites.
The full-run command remains under end-to-end audit; see
`analysis/current_audit_status.md` rather than treating this command as an
acceptance certificate.

The registered estimator, analysis and verifier modules carry a `--selftest` that
checks the property each module exists to guarantee — the FE absorber against
brute-force dummy OLS, the bootstrap
against a planted effect, the screened-sample filter against a planted +40 d effect
in screened-out rows, the permutation tolerance against a deliberately-wide later
season. The runner also
inventories explicitly named utilities without a `--selftest` and refuses
any Python file in neither list. This was verified from an unzipped copy with
`RICEBACI_ROOT` pointing at an empty directory. One registered check,
`lf_output.py`, is a guard rather than an analysis: it pins every committed CSV and
JSON to LF on every platform and its self-test scans the other modules' source to
confirm none can bypass it. It exists because `pandas` defaults `to_csv`'s line
terminator to `os.linesep`, so until 2026-09-14 every committed table would have
regenerated with CRLF on Windows — the same values, a different md5, and every md5
check in every handoff broken for any Windows reproducer. Found by an external
auditor who ran the reproduction on Windows. Run them first; they are
the cheapest evidence that the repository is intact.

Read that number only from `bash run_all.sh selftest`'s **exit code**, not from its
printed lines. Until 2026-09-13 the runner could not fail: every check was
`if … then echo PASS else echo FAIL fi`, so the function always returned 0, and the
caller read `exit 0` outright. It printed FAIL and reported success, and the `all`
path ran the whole analysis on code it had just watched fail. It now distinguishes
**FAIL** (ran, an assertion did not hold — the code is wrong) from **ERROR** (could
not start, e.g. a missing dependency — the environment is incomplete), returns
non-zero on either, and stops the pipeline. Both paths were tested by sabotage:
a broken assertion and a missing module each produce the right verdict and exit 1.
`fit_phenometrics.py` was also absent from the roster, which is why the count was
nine and not eleven.

`permutation_test.py` has a second half that reproduces `twfe`'s published
coefficient on the real district panel — the check that caught `fit_cell` failing
to restrict to `retained == 1`. That panel is a pipeline **output**, so the check
runs when it resolves and prints a visible `[SKIP]` when it does not. A skip is not
a pass being claimed: the line says which checks did not run and why. Until
2026-09-13 this half ran unconditionally from a hard-coded absolute path and the
whole self-test died with `FileNotFoundError` on any other machine — found by a
receive-only executor running the handoff checks, which refused to commit. The
original claim of "nine of nine" in this file was true only in the environment it
was written in — and, as the runner note above records, was not something that
runner could ever have established.

### Earth Engine stages

Two inputs cannot be produced from this repository. Each GEE script prints a
task inventory and refuses with `*** STOP ***` rather than exporting short.

| script | tasks | produces |
|---|---|---|
| `gee/s1_block.js` | 225 | combined-orbit VH/VV panel |
| `gee/S1_STATIC_COVARIATES.js` | 25 | elevation, slope, incidence (§3.10 IPSW) |
| `gee/S1_ORBIT_INVENTORY.js` | 0 | go/no-go check — run before the next one |
| `gee/S1_PER_ORBIT.js` | 225 | per-orbit series (H1/H2 clause (a)) |
| `gee/S1_MASK_FLAG.js` | 25 | §3.5 mask sensitivity — run 2026-09-13 |

---

## Layout

```
docs/Protocol_v1.md        the protocol, with §4.1–§4.3 amendments of 2026-09-13
analysis/decisions_log.md  dated decisions; twenty-two entries on 2026-09-13 alone
analysis/deviation_log.md  §5.3 deviations, each with per-hypothesis impact
analysis/test_classification.md  every test classified A / B1 / B2 / C, dated
DATA_AVAILABILITY.md       what is and is not committed, and what each lets you verify
python/                    analysis; test roster and explicit exemptions in run_all.sh
gee/                       Earth Engine exports (8 scripts + README; task counts named)
data/s1_maskflag/          the 25 §3.5 mask exports, committed
results/                   tables, panels, run logs
figures/                   figures
```

`analysis/test_classification.md` is the index to read first: every test and
decision in one table, classified as confirmatory, a feasibility deviation, a
deviation driven by measurement on the untreated 2017 baseline, or **result-aware**
— with the boundary between the last two dated at the last design decision made
before any exposure coefficient existed. The result-aware group is listed first
within it, and every entry states what protects it.

**Read the logs before the results.** This analysis changed substantially during
execution — the substrate moved from Sentinel-2 to Sentinel-1, the estimator from a
double-logistic to a five-segment piecewise-linear model, and the headline from
pixel to district level. Every change is dated, and corrections are appended in
place rather than rewritten, so a superseded decision stays visible next to what
replaced it. Several entries record defects in this project's own code, including
one (a regression that ignored the QC screen) that had contaminated 59% of the
observations in the pixel-level headline before it was found.

---

## Open items, recorded rather than buried

- **§3.10 attrition reporting** — **the rule fired and was never executed; fixed
  2026-09-15.** §3.10 declares that where an attrition diagnostic is significant
  at p_WCB < 0.05, the magnitude is reported as *not point-identified under
  differential attrition*. Seven output labels meet that condition, representing
  six distinct designs because `class:pre_season` and
  `phase_attrition:S_phase_pre_window` are verified aliases. Five labels are at
  pixel level (`class:pre_season` and its alias at p 0.0008,
  `cyclone:FANI` 0.0012, `cyclone:TITLI` 0.0094,
  `phase_attrition:S_phase_rise` 0.0411) and two are at district level
  (`class:harvest_window` 0.0397, `cyclone:YAAS` 0.0432). None was reported in
  live text: `analysis/hypothesis_verdicts.md` did not contain the word
  "attrition", and the declared phrase appeared only as a statement of the rule.
  The numbers were in the committed tables throughout.

  Three things caused it and all three are now fixed. `run_all.sh` never passed
  `--balanced`, so the declared reproducible run emitted **no balanced-composition
  rows at all** — none at pixel level, and the district table's 132 rows came from
  a hand-run a rerun would have silently deleted. The attrition step also could
  not run at all as written, because it read the exposure catalogue by bare
  filename from `python/` while the file lives in `docs/`. And nothing checked
  any of it. `python/attrition_completeness.py` is now a gate in the runner: it
  writes `Table_SX_AttritionTriggers.csv` and fails the run if a triggered
  stratum lacks a required status, if a status is blank rather than an explicit
  `not_estimable:<reason>`, if keys duplicate, or if the balanced block shrinks.

  **No coefficient, standard error, test statistic, sample count or scientific
  verdict moved materially** in the final clean replay. The pixel bootstrap
  statistics did move when the earlier 999-replication table was replaced by the
  declared **9,999**-replication analysis. Against the immediately preceding
  9,999-draw candidate, one underpowered, non-triggering WCB value also changes by
  one draw (`cyclone:REMAL`, 0.7134 → 0.7135) in the recorded Windows numerical
  environment; a targeted clean recomputation returns 0.7135 again. This is
  reported rather than hidden, and it changes no trigger, multiplicity result or
  interpretation. The exact key set is unchanged, and 132 pixel balanced rows
  that had never been computed in the original pipeline are present.

  **The district `+5.001 d` trough coefficient under severe harvest-window
  exposure is reported as not point-identified**, and no pooled class-level
  balanced estimator has been invented to rescue it: §3.10 item 3c defines the
  balanced restriction *per cyclone* and specifies no pooled form, so that is
  recorded as a post-analysis implementation gap. The per-cyclone balanced rows
  are separate descriptive sensitivities on two-season sub-samples, not a pooled
  comparator.

  **`delta_beta` is retired as a composition sensitivity (2026-09-15).** It
  compares a two-season balanced fit with an all-season pooled headline, so it
  changes the time window as well as the composition and identifies neither. A
  valid one must differ *only* in composition; none is declared in the protocol
  and none is introduced.

  **Multiplicity is a sensitivity, not the gate.** The predeclared trigger stays
  on the raw p. Holm and BH-FDR are computed over the **distinct designs** given
  by a **verified alias map**: `class:pre_season` and
  `phase_attrition:S_phase_pre_window` are one regression under two names, and
  that is known because their exposure vectors are elementwise identical across
  all 225 district-seasons — checked against the panel, not inferred from matching
  output. The conservative all-labels calculation is carried alongside. Neither
  district finding survives adjustment; `class:pre_season` and `cyclone:FANI`
  survive Holm at pixel level.

  **Counted consistently: seven triggered output labels, six distinct tested
  designs** — five labels at pixel level and two at district, with one pixel pair
  a verified alias that is counted once.

- **§3.5 mask sensitivity** — **closed 2026-09-13.** Run at both levels, in two
  variants, with §3.9's declared permutation inference on both sides. 8,085 of
  10,000 cohort points (80.85%) survive an intersection with ESA WorldCereal
  `temporarycrops`. Every reported result holds; the §3.9 placebo failure gets
  *sharper* on the masked subset (pixel p_perm 0.0395 → 0.0185), and the
  β_pre on the fitted fall-end breakpoint moves farther in the direction opposite
  to the predeclared analogue too, so neither pattern can be attributed solely to cohort
  contamination. 0 of 24 cells show a material sign flip. The 0.62% of points
  under overlapping WorldCereal tiles, where the mosaic pick is arbitrary, are
  dropped in the second variant and change p_perm by 0.001. WorldCereal v100 has
  no rice layer, so §3.5's disclosure still binds: this is a general-cropland
  classifier and the arm does not show the cohort is rice.
- **§3.5's per-unit sub-arm — reopened 2026-09-14, and its headline claim withdrawn.**
  The district- and pixel-level results above are unaffected: they come from re-running the
  committed estimator on masked exports. The **per-unit** table did not. A second external
  audit found it built on the wrong estimand (an average of pixel dates instead of the
  district mean-curve fit — against a rule written at the top of the file it was added to),
  a two-season instead of three-season clean-control window, and all nine severe storms
  instead of §3.8 B's declared six. All three are corrected. The claim **"mask choice does
  not move the per-unit estimates" is withdrawn**: over the 35 declared units the
  intersection-minus-primary difference is mean −7.39 / −0.67 / −1.59 d with signs agreeing
  **31/35, 22/35, 21/35**, against the withdrawn 46/47, 47/47, 45/47. The instability sits
  where §3.8 B's control rule leaves almost no control group — usable controls are Titli 1,
  Fani 2, Bulbul 2, Amphan 4, Yaas 13, Remal 11 — so the per-unit arm is now reported as a
  disclosure of unit-level spread, not as evidence that mask choice is immaterial.
- **H3's construct mismatch**: H3 is predeclared on SOS / peak NDVI / EOS, and the
  estimator produces trough / heading / drainage / harvest, which §3 says are *not*
  those quantities. The mapping is authorised for **direction only, never
  identity** (§4.3.1); outcomes are named as fitted breakpoints everywhere.
- **Results, Abstract and Conclusions are not frozen.**

## Status

**Green for manuscript drafting as of 2026-09-16.** The accepted bounded scope,
authoritative values, required limitations and prohibited claims are fixed in
`analysis/manuscript_source_of_truth_2026-09-16.md`. This is not a release or
submission signal: the draft, supplement, final journal figures/tables, public
GitHub release and public Zenodo DOI still require independent acceptance.
