# Paper 2 manuscript source of truth

Status: **GREEN and authoritative for manuscript drafting, 2026-09-16.** The
independent clean attrition replay, fail-closed gates and portable-clone checks
have passed. This is a drafting signal, not a public-release or journal-submission
signal; the separate gates at the end of this file still apply.

The protocol is an append-and-correct audit record. It deliberately retains
superseded statements. A drafter must therefore use this file and the current
result tables named below, not select prose from an older protocol paragraph.

## Title and scientific question

**Provisional title**

> Between-orbit repeatability and interpretation limits of Sentinel-1 rice
> phenology breakpoints along the Bay of Bengal coast

**Question actually answered**

How consistently are fitted Sentinel-1 radar-trajectory breakpoints recovered
across relative orbits, and what limits their interpretation as agronomic dates
or cyclone-response outcomes in the analysed district-seasons?

**Distinct contribution relative to Paper 1**

Paper 1 presents an optical quality-control workflow. Paper 2 is a Sentinel-1
measurement and interpretation study. It quantifies between-orbit repeatability,
tests the declared dispersion criteria, compares the fitted breakpoints with a
coarse external calendar product, and shows where cyclone-response readings fail
the study's own falsifiability checks. It is not a second claim to the same QC
framework and not a causal cyclone-impact paper.

## Operative outcome names

The fitted quantities are trajectory breakpoints, not field-observed crop dates:

| code | required manuscript name | permitted interpretation |
|---|---|---|
| `t1` | fitted end-of-dark-phase breakpoint | transplanting/onset-related interpretation only |
| `t2` | fitted end-of-rise breakpoint | heading-related interpretation only |
| `t3` | fitted end-of-plateau breakpoint | drainage-related interpretation only |
| `t4` | fitted end-of-fall breakpoint | harvest-related interpretation only |

Tables may include short parenthetical aliases such as “rise-end (heading-related)”
after the operational name has been given. They must not rename these quantities
SOS, POS, EOS, transplanting date, heading date, drainage date or harvest date.

## Hypothesis verdicts

These classifications must appear consistently in the Abstract, Results,
Discussion, Conclusions and supplement.

| hypothesis | operative verdict |
|---|---|
| H1(a), fitted trough/end-of-dark-phase | **Met as declared**, 0.9443 within the baseline-derived `T = 70 d` against 0.90; explicitly describe the criterion as permissive and close to true by construction. |
| H1(b) | **Fails as measured**, within/between dispersion ratio 1.340, 95% CI 1.273–1.408; criterion `< 1`. |
| H2(a), fitted fall-end | **Met as declared** at pooled scope, 0.9114 within `T = 60 d` against 0.90; explicitly describe the criterion as permissive. Andhra Pradesh alone is 0.8564. |
| H2(b) | **Fails as measured**, ratio 1.508, 95% CI 1.424–1.592; criterion `< 1`. |
| H2 optical arm | **Withdrawn** because the required optical observations were not obtained. |
| H3 | **Not estimable as declared** because the declared optical SOS/peak/EOS quantities were not estimated. The radar-breakpoint analogue is exploratory, not an H3 verdict. |
| H4 | **Fails its declared criterion**, 2 of 6 named cyclones agree in sign against the required 5 of 6. |
| H5 | **Withdrawn untested**, because MODIS was not obtained. It did not fail. |
| H1c/H2c | **Reported, never tested**: MARC product offsets are descriptive and the calendar-source leg is available for Odisha only. |

The one-sentence summary is: one hypothesis fails its declared criterion; two
fail one clause while their permissive clause passes as declared; one is not
estimable as declared; and one was withdrawn untested.

## Results that may be reported

1. The untreated-2017 tolerance sample contains 798 usable orbit pairs. The
   post-baseline repeatability statistics use 7,717 pairs, not 8,515.
2. On those 7,717 pairs, `sd(orbit difference)/sqrt(2)` is 25.90 d for the fitted
   trough, 19.82 d for the fitted rise-end, and 25.79 d for the fitted fall-end.
   These are scaled between-orbit disagreement statistics under the stated
   equal-variance interpretation. They are not measurement-error estimates,
   accuracy estimates, lower bounds for each orbit, or upper bounds for the
   multi-orbit composite.
3. Fractions within one 10-day dekad are 0.3820 for the fitted trough, 0.4529
   for the fitted rise-end and 0.3504 for the fitted fall-end. These exploratory
   absolute-agreement figures are separate from the declared tolerance tests.
4. H1(b) and H2(b) fail as measured. The single-orbit sensitivity also leaves
   all observed within/between ratios above one (1.3278, 1.4750 and 1.5772 for
   trough, rise-end and fall-end in seasonal order), but the samples differ and
   the analysis does not identify why the clauses fail.
5. The archived synthetic Monte Carlo (`results/montecarlo_precision.csv`,
   `sigma_db = 0.122`, `grid = free`, 80 draws) reports per-breakpoint standard
   deviations of 0.000000, 0.000000, 2.179449 and 1.899836 d for t1, t2, t3 and
   t4, with mean signed errors of 0.000, 0.000, -0.500 and +0.375 d. The earlier
   approximately ±1.3 d summary is withdrawn as unsupported by this archived
   table. These are conditional, on-grid synthetic-trajectory results, not
   empirical precision, field accuracy, or quantities comparable with the
   between-orbit statistic. Release wording corrected 2026-09-17; no analysis
   or result-table value changed.
6. Against the 0.5-degree MARC product, the transplanting-related offset averages
   +20.2 d and the harvest-related offset +50.4 d. MARC is not field truth or
   pixel validation. The harvest offset supports non-interchangeability at the
   compared aggregate scale; it does not identify the true agronomic date.
7. The declared mask arm is a sensitivity analysis. At unit level, sign agreement
   between mask variants is 31/35, 22/35 and 21/35 for trough, rise-end and
   fall-end. It does not support a claim that mask choice is immaterial.
8. The pixel-level timing placebo is rejected; the district analogue is
   inconclusive. All cyclone coefficients therefore remain descriptive
   associations. The censoring simulation supplies a plausible estimator
   pathway, not the identified cause.
9. Attrition diagnostics use 9,999 bootstrap replications at both levels. The
   accepted accounting is seven triggered output labels representing six tested
   designs because one pixel pair is a verified alias. Magnitudes are not
   point-identified under differential attrition.
10. Named-event usable control pools are small. Per-unit results are descriptive
    sensitivity evidence, not causal estimates and not a basis for generalisation.

## Claims that are prohibited

- No causal effect of cyclone exposure.
- No accuracy, validation, ground-truth or field-validation claim for a radar
  breakpoint.
- No claim that orbit errors are independent or that the scaled orbit difference
  is “the measurement error”.
- No claim of a district-versus-pixel precision boundary and no ratio between
  the synthetic ±1.3 d result and pixel disagreement.
- No variance subtraction, “true crop variation”, corrected dispersion ratio,
  or explanation of why H1(b)/H2(b) fail.
- No identity between radar breakpoints and optical SOS/POS/EOS or agronomic
  dates. A directional analogue is not construct identity.
- No claim that Paper 1's optical calendar ceiling was mistimed, that Paper 1's
  support loss has been explained, or that radar results validate Paper 1.
- No claim that the 2018 rice mask is pre-treatment or independent of all study
  events. Titli occurs within the mask epoch, and pixel identity is not validated.
- No claim that a coarse product validates 30 m pixels.
- No claim that the permutation design is unconditionally valid; within-state
  exchangeability is an unverified assumption and the spatial procedure differs
  from the wild-cluster bootstrap.
- No “first study”, “no previous study” or equivalent priority claim without a
  fresh, documented literature search that directly supports it.
- No promise of cross-environment byte identity.

## Limitations that must be stated plainly

1. No independent field reference is available; repeatability is not accuracy.
2. Orbit agreement is evaluated in a selected usable paired sample and the
   best-covered-pair rule, although marker-blind, may affect representativeness.
3. The pooled baseline-derived tolerances are permissive and do not establish
   state-level transferability; Andhra Pradesh has only 15 baseline pairs in the
   post-hoc state diagnostic.
4. The rice mask is a product classification, not plot-level ground truth. Its
   2018 epoch includes Titli, and membership identity cannot be established from
   aggregate counts alone.
5. The MARC comparison is across different measurands and scales.
6. Small and contaminated event-specific control pools prevent a causal reading.
7. Exposure-associated attrition is detected, so descriptive coefficient
   magnitudes are not point-identified as cyclone effects.
8. H3's declared optical constructs and H5's MODIS input are unavailable.
9. Raw-export replay requires the archive; a Git clone alone cannot regenerate
   every pixel-level artifact or figure input.
10. Some permutation results depend on an unverified within-state exchangeability
    condition. Wild-cluster and permutation p-values must be reported as two
    conditional procedures, not used to validate one another.

These limitations bound the paper; they are not defects if the manuscript stays
inside this scope. New field observations would enable accuracy claims, but they
are not required for this repeatability-and-interpretation paper.

## Authoritative evidence

Use the tables, not rounded prose, for manuscript values:

- `results/orbit_agreement/Table_SX_OrbitAgreement.csv`
- `results/orbit_agreement/Table_SX_OrbitStateSensitivity.csv`
- `results/orbit_agreement/Table_SX_OrbitPairSelectionSensitivity.csv`
- `results/dispersion/Table_SX_Dispersion.csv`
- `results/dispersion/Table_SX_RepeatCoverageSensitivity.csv`
- `results/orbit_agreement/Table_SX_DispersionSingleOrbit.csv`
- `results/marc/Table_SX_MARC_Summary.csv`
- `results/permutation_test/Table_SX_Permutation_{district,pixel}.csv`
- `results/robustness/Table_SX_RobustnessArms_{district,pixel}.csv`
- `results/s310_v2_{district,pixel}/Table_SX_AttritionDiagnostic.csv`
- `results/s310_v2_{district,pixel}/attrition_trigger_summary.csv`
- `results/mask_sensitivity/Table_SX_MaskSensitivity_ALL.csv`
- `results/mask_sensitivity/Table_SX_MaskPerUnit_{trough,heading,harvest}.csv`
- `results/window_sweep/`
- `analysis/hypothesis_verdicts.md`
- `analysis/test_classification.md`
- `DATA_AVAILABILITY.md`

All table joins must be keyed explicitly. Do not copy bare triples without marker
names, because the orbit-agreement table and some summaries use different marker
orders.

## Journal manuscript package requirements

Target journal: **Physics and Chemistry of the Earth, Parts A/B/C**. Before
drafting, re-read the supplied Elsevier Guide for Authors and apply whichever
requirement is stricter when it conflicts with a house preference below.

- Main manuscript in editable Word format, double-line-spaced and fully justified.
- Separate title page with full title, all authors in agreed order, affiliations,
  corresponding-author details, ORCID identifiers and required declarations.
  Author order must match the submission system; use lower-case superscript
  letters for full affiliations and give the corresponding author's publishable
  email address. Keep any present address as a numbered footnote while retaining
  the affiliation where the work was done.
- Keep the abstract at or below **250 words**, self-contained and normally free
  of references; supply **1–7 English keywords**.
- Supply a separate editable highlights file with **3–5 bullets**, each no more
  than **85 characters including spaces**.
- A graphical abstract is encouraged rather than mandatory. If prepared, submit
  it separately at 531 × 1328 pixels (height × width) or proportionally larger,
  readable at 5 × 13 cm, using a journal-accepted editable/vector format where
  possible.
- Figures numbered in first-citation order, cited in the text, embedded near their
  first discussion for the review copy, and also supplied as separate 1000 dpi JPG
  files. At full-page width the guide's minimum for a bitmapped line drawing is
  **7480 pixels**; retain an editable/vector source as well. Figures should occupy
  the usable full page width, have readable labels,
  contain no title inside the image, and have a complete caption below the figure.
- Tables numbered in first-citation order, cited in the text, editable rather than
  images, formatted in the journal's table style, and headed by a concise title.
  Put notes below the table body and use neither vertical rules nor cell shading.
- Every in-text citation must have one bibliography entry and every bibliography
  entry must be cited. Verify bibliographic metadata and DOI values against primary
  sources; do not manufacture or infer missing references.
- Include all required end matter immediately before the references: funding,
  conflicts of interest, data availability, code availability, author
  contributions/CRediT, acknowledgements, ethics/consent where applicable, and a
  transparent generative-AI-use declaration.
- The supplement must carry full diagnostic and sensitivity tables, provenance
  and methods needed to support the bounded claims; it must not contain stronger
  interpretations than the main text.
- Claude may prepare drafts only. Claude must not commit, push, publish a deposit,
  or submit. Codex will independently audit the manuscript and supplement.

## Release and submission gates (not drafting gates)

Before journal submission, Codex must independently verify all of the following:

1. the accepted repository version is committed and publicly accessible on GitHub;
2. a matching frozen release/tag identifies the exact accepted commit;
3. the Zenodo deposit is refreshed to that same version, published, and its DOI
   resolves publicly;
4. repository, archive, manuscript data statement, DOI and hashes all identify the
   same frozen package;
5. the final Word/PDF manuscript and supplement pass numerical, citation,
   cross-reference, visual-layout and disclosure checks; and
6. the author gives final confirmation after being shown the exact files and
   submission metadata.

The present unpublished Zenodo draft is not a DOI-bearing public release and must
not be described as one.
