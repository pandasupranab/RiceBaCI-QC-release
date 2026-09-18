# Hypothesis verdicts — the authoritative table

**Created 2026-09-13, after an external re-audit found the previous framing wrong.**

Until this file existed, this project stated in the protocol, both logs, the re-audit
brief and every summary that **"all five predeclared hypotheses fail."** That is not
true, and it is not true in a way that matters: it conflates a hypothesis that failed
its own declared test with one that was never tested, and with two whose declared
criterion actually passed.

This file is the single place the verdicts are stated. Where `docs/Protocol_v1.md`
§4.2 and `analysis/deviation_log.md` say otherwise, they are superseded by the dated
amendments that point here; their original text is left standing per this project's
append-and-correct convention.

> **Amended 2026-09-14 — the sentence above assumed a pointer that was not there.** Three
> places carried the withdrawn verdict with **no** amendment pointing here: §4.2.6 of the
> protocol (headed "Per-hypothesis status, **final**", and contradicting §4.2.2 two pages
> above it), §4.3.1's "the verdict is unchanged: H3 NOT MET", and a reviewer-checklist line
> in `analysis/test_classification.md`. The external re-audit of 2026-09-14 caught the
> withdrawn verdict in three *other* files; these three survived that pass because the sweep
> matched the propagated summary phrase and these state the verdict in a different shape —
> hypothesis by hypothesis, or as a checklist instruction. All three now carry dated
> corrections pointing here. **The lesson is recorded rather than just the fix: a phrase
> sweep does not find a claim restated in another form, so a withdrawn verdict must be
> chased by meaning, file by file.**
>
> **Also added 2026-09-14, on H1c/H2c's calendar leg.** §2 states H1c/H2c as agreement
> against MARC *and* against §3.4's published district crop calendars.
> `docs/field_reference_sources.md` endorses sources for **Odisha only** — West Bengal and
> coastal Andhra Pradesh are NOT FOUND — and §3.4's AICRP attribution is suspended as
> unsourced. The MARC leg is complete; the calendar leg is **partial**, and no three-state
> calendar-validation statement may be written.

---

## Summary

| | declared criterion | measured | verdict |
|---|---|---|---|
| **H1** clause (a), radar trough | orbit agreement within a tolerance fixed on the untreated 2017 baseline | **0.944 within T = 70 d** against a 0.90 criterion | **MET as declared** — and vacuous; see below |
| **H1** clause (b) | within-pixel inter-seasonal dispersion < between-pixel dispersion in district | ratio **1.340** [1.273, 1.408] | **FAILS as measured** |
| **H2** clause (a), radar fall-end | as H1, for the fitted fall-end breakpoint | **0.911 within T = 60 d** against 0.90 | **MET as declared**, vacuous; fails in Andhra Pradesh alone (0.856) |
| **H2** clause (b) | as H1, for harvest | ratio **1.508** [1.424, 1.592] | **FAILS as measured** |
| **H2** optical arm | Sentinel-2 EOS cross-check reported alongside | not obtained | **WITHDRAWN** |
| **H3** | β_pre > 0 and significant for **SOS, peak NDVI date and EOS**; β_harv > 0 for EOS | those quantities were never estimated | **NOT ESTIMABLE AS DECLARED** |
| **H4** | point estimate agrees in sign with §4 for **at least five of the six** named cyclones | **2 of 6** | **FAILS on its declared criterion** |
| **H5** | MODIS district SOS correlates at Spearman ρ ≥ 0.70 | MODIS never obtained | **WITHDRAWN — not tested, not failed** |
| **H1c / H2c** | product agreement against MARC **and against §3.4's published district crop calendars**, no threshold pre-declared | MARC: transplanting +20.2 d, harvest +50.4 d. Calendar leg: **Odisha only** | **REPORTED** for MARC as declared; the calendar leg is **PARTIAL — Odisha only** (added 2026-09-14) |

**The sentence that replaces "all five fail":** of the five predeclared hypotheses,
**one fails on its declared criterion (H4)**; **two fail on one clause while their
other clause passes as declared (H1, H2)**; **one is not estimable as declared (H3)**;
and **one was withdrawn untested (H5)**.

---

## H1 and H2 clause (a) — the declared criterion passes, and saying otherwise was
## result-aware

§2's corrected measurand statement declares that radar trough and fall-end
breakpoints fitted separately to Sentinel-1 relative-orbit series agree within a
pre-declared tolerance, with tolerances fixed on the untreated 2017 baseline
season before any treated season is fitted. Earlier text called those fitted
breakpoints transplanting and harvest dates; that agronomic identity is not
validated and is no longer used in the active hypothesis wording.

`orbit_agreement.py` does exactly that. T is the 90th percentile of |orbit difference|
on 2017, and the criterion is 90% of later pixel-seasons within T:

> **Row order, stated because it is not the obvious one.** This table and `results/orbit_agreement/Table_SX_OrbitAgreement.csv` list the markers as **trough, harvest, heading** — ordered by tolerance (70, 60, 50 d), not by position in the season. So the bare triple "0.9443 / 0.9114 / 0.9387" that appears elsewhere in this repository is trough / harvest / heading, whereas the σ triples ("25.90 / 19.82 / 25.79", "25.68 / 20.57 / 25.30") are trough / heading / harvest. Two orderings for bare triples side by side is a defect in the writing: on 2026-09-14 the author mis-mapped this one while verifying a brief against these tables. Quote clause (a) with its marker names attached.

| marker | T (2017 baseline) | fraction within T | criterion | passes |
|---|---|---|---|---|
| trough | 70 d | **0.9443** | 0.90 | yes |
| harvest | 60 d | **0.9114** | 0.90 | yes |
| heading | 50 d | **0.9387** | 0.90 | yes |

Every marker passes at the pooled scope, and `stable_vs_baseline` is 1 for all three.
Of the sub-scopes, only **harvest in Andhra Pradesh fails** (0.8564 on n = 195).

### Post-hoc state-specific tolerance diagnostic

The pooled criterion does **not** establish that one tolerance transfers across
states. Recomputing the 2017 90th-percentile tolerance separately gives, for
trough / heading / harvest, **56 / 46 / 62 d** in Andhra Pradesh,
**70 / 50 / 60 d** in Odisha, and **60 / 40 / 70 d** in West Bengal. Later-season
shares within those state-specific tolerances are **0.821 / 0.851 / 0.856**,
**0.940 / 0.931 / 0.919**, and **0.927 / 0.902 / 0.954**, respectively. Andhra
Pradesh has only **15 baseline pairs**, so its state threshold is explicitly
underpowered and diagnostic only. These post-hoc calculations do not replace the
declared pooled test; they show why its passing verdict must not be described as
three-state transferability. Source:
`results/orbit_agreement/Table_SX_OrbitStateSensitivity.csv`.

### Post-hoc orbit-pair selection diagnostic

The declared rule chooses a retained orbit pair without using its breakpoint
agreement: prefer an ascending/descending pair, then maximise total valid
dekads. Two marker-blind alternatives leave the pooled result essentially
unchanged. The lowest-orbit rule gives scaled disagreement of **25.85 / 19.85 /
25.78 d** for trough / rise-end (`heading`) / fall-end (`harvest`);
unit-weighting all eligible pairs
gives **26.18 / 20.03 / 25.83 d**, against **25.90 / 19.82 / 25.79 d** under
the declared rule. All three outcomes remain above the declared 0.90
within-tolerance criterion under both alternatives, including with the declared
2017 tolerances held fixed. This post-hoc check supports robustness to the
marker-blind pair-selection rule only; it does not establish accuracy,
independence of orbit errors, or state-level transferability. Source:
`results/orbit_agreement/Table_SX_OrbitPairSelectionSensitivity.csv`.
The input/output hashes and repeated-run byte check are recorded in
`analysis/verification_orbit_pair_selection_2026-09-16.md`.

§4.2.2 nevertheless concluded "**Clause (a) is NOT MET**", on the ground that an
absolute one-dekad criterion is the meaningful one: 38.2% of pixel-seasons agree within
one dekad for the trough breakpoint and 35.0% for the fall-end breakpoint, with between-orbit correlations of
r = +0.339 and +0.147 and σ ≈ 26 d.

**Both halves of that are defensible; putting them together as a NOT MET verdict is
not.** T = 70 d is six or seven dekads, and because it is the 90th percentile of the
baseline's own disagreement, "90% within T" is close to true by construction. That the
criterion is nearly vacuous is provable from its definition without seeing a single
treated season. But it was **noticed after the orbit fits existed**, and the absolute
one-dekad rule that replaced it was adopted at the same time. Substituting a criterion
after seeing results is result-aware however sound the reasoning, and a protocol that
fixes tolerances in advance exists precisely to stop it.

**So the verdict is split, and both parts are reported:**

- **The pre-declared criterion is MET** (0.944, 0.911, 0.939 against 0.90), and is
  reported as *uninformatively permissive*, with T's value in dekads and the
  construction that makes it so.
- **Absolute agreement is poor**, and is reported as **exploratory**: 38.2% and 35.0%
  within one dekad, r = +0.339 and +0.147, σ ≈ 26 d against a quantisation floor of
  10/√12 = 2.89 d.

Neither statement is withheld and neither is presented as the other.

## H1 and H2 clause (b) — fails as measured

| marker | within-pixel sd | between-pixel sd | ratio | 95% CI |
|---|---|---|---|---|
| trough (H1) | 26.745 d | 19.965 d | **1.340** | 1.273 – 1.408 |
| harvest (H2) | 25.998 d | 17.246 d | **1.508** | 1.424 – 1.592 |
| heading (supplementary) | 20.304 d | 14.130 d | 1.437 | 1.384 – 1.491 |

The criterion is ratio < 1. It is not met, and the confidence intervals exclude 1 by a
wide margin. Restricting to district-seasons with no severe exposure of any timing
class changes nothing (1.316, 1.454).

### Post-hoc repeat-coverage diagnostic

The failure is not driven only by pixels with two retained seasons. Recomputing
each district-centred ratio after requiring at least **2 / 4 / 6 / 8 / 9** retained
seasons leaves **6,453 / 4,265 / 2,277 / 639 / 168 pixels**. The trough ratios are
**1.338 / 1.595 / 1.657 / 1.703 / 1.730**; heading **1.436 / 1.612 / 1.719 /
1.769 / 1.616**; and harvest **1.508 / 1.715 / 1.853 / 1.977 / 2.135**. Every
value remains above 1. This was added after seeing the headline result, so it is
a robustness diagnostic, not a new confirmatory test, and it still does not
identify *why* clause (b) fails. Source:
`results/dispersion/Table_SX_RepeatCoverageSensitivity.csv`.

**This is the clause on which H1 and H2 fail, and it is the only one.**

### The single-orbit recomputation — observed only

Recomputed on a **single orbit**, so that the dispersion and the between-orbit statistic
describe one estimator rather than two:

| marker | within (d) | between (d) | observed ratio | pixels | pixel-seasons |
|---|---:|---:|---:|---:|---:|
| trough | 26.836301 | 20.210418 | **1.327845** | 6,602 | 28,562 |
| harvest | 27.213362 | 17.254319 | **1.577191** | 6,602 | 28,562 |
| heading | 21.322590 | 14.455730 | **1.475027** | 6,602 | 28,562 |

Mean retained seasons per pixel on its chosen orbit **4.326265**, range two to nine.
**Clause (b) fails as measured.** **All three ratios remain above 1 in the single-orbit sample as well.** That sample is **selected separately** — each pixel's best-covered orbit with at least two retained seasons — from the paired sample the between-orbit statistic uses, and from the committed panel. So the three results sit side by side as observations on three samples, and **no causal statement about why clause (b) failed follows from any of them**. The between-orbit statistic (25.90 /
19.82 / 25.79 d) is reported alongside and is not subtracted from these. *(Narrowed
2026-09-14, eighth pass: this read "the failure is not an artefact of the estimator
mismatch".)*

> **Retired 2026-09-14 (sixth pass).** This section previously carried a subtraction of an
> assumed error variance and reported "true within", "true between" and a "corrected ratio"
> of 0.441 / 0.724 / 0.724, with the qualification that they held "under a classical
> measurement-error model". **The whole calculation is retired as an active analysis**, not
> merely qualified: its error model was never tested, its between-pixel term used the wrong
> factor for unbalanced season counts (1/mean(nᵢ) = 0.23114628 against mean(1/nᵢ) =
> 0.28164872), the residuals are district-year centred before the pixel means are formed,
> and the result was fragile to a few per cent in σ. Protocol §4.2.3 carries the full
> statement; the dated history is in `analysis/deviation_log.md` and
> `analysis/decisions_log.md`. **Why clause (b) failed is not identified by this study.**

### The semivariogram comparison, and what it is not

`semivariance.py`'s shortest-lag value is **25.68 / 20.57 / 25.30 d** for trough / heading /
harvest against the between-orbit **25.90 / 19.82 / 25.79 d** — similar to within 0.8 d.

That similarity is a **description of this dataset and nothing more**. The two are not the
same estimand: a short-lag spatial semivariance mixes local variation in the true field with
the spatially uncorrelated part of the error, while a between-orbit difference cancels
whatever the two paths share. Both read the same Sentinel-1 panel through the same breakpoint
estimator, so neither is independent of a defect in the other and **neither validates the
other**. *(Corrected 2026-09-14, sixth pass. This section previously opened "What is now
established independently is the magnitude of σ" and later called it "corroborated"; a
fifth-pass note also claimed the short-lag value is an upper bound on measurement error, which
is false in the direction that matters — a spatially shared error cancels from the neighbour
difference and is missing from the statistic, so it can sit far below total error.)*

## H3 — not estimable as declared

§2 declares β_pre positive and significant "for **SOS, peak NDVI date and EOS**", and
β_harv positive for EOS. Those are optical phenological constructs. **This study
estimates radar trajectory breakpoints — trough, heading, drainage, harvest — and §3
states they are not those quantities.** §4.3.1 authorises the mapping for **direction
only, never identity**.

The declared quantities were therefore never estimated, and "H3 fails" asserts a test
that was not run. The honest classification is **not estimable as declared**.

**MARC adds a coarse-product comparison to the definitional distinction.** Against
the 0.5° MARC rice calendar, the harvest breakpoint sits **+50.4 d** later than MARC's harvest
date — positive in all 25 districts, 22 of 25 within ten days of the median, MAD
3.1 d. This systematic offset is evidence that the two quantities should not be
treated as interchangeable. MARC is neither a field reference nor ground truth for
these pixels, so the comparison does not prove the agronomic identity or non-identity
of an individual breakpoint.

**The radar-breakpoint analogue is reported as exploratory**: 0 of 4 cells meet the
positive-and-significant pattern, and β_pre on the harvest breakpoint is significant
in the direction **opposite to the predeclared analogue** at both levels — district −10.184 d (p_perm 0.0075), pixel
−3.351 d (p_perm 0.0005) — robust across all 10 arm × level cells and *strengthening*
under the WorldCereal mask (pixel −4.044 d). That is a finding about the radar
breakpoints. It is not a verdict on H3.

**Added 2026-09-13 (§1.4 window sweep): a third quantitative reason the harvest
breakpoint is not a harvest date, and a limit on what this cell may be read across.**
The five-segment model's last segment falls from the plateau to *b₂* between *t₃* and
*t₄* and is flat afterwards, so a unit with **no valid dekad after *t₄*** has a harvest
breakpoint that is where the fitted fall *would* reach baseline, not an observed return to it.
Measured: **17 of 208 estimable district-seasons (8.2%) at the DOY 425 headline**, and
**125 of 204 (61.3%)** at Paper 1's DOY 365 core window. A quantity that is an
extrapolation for one unit in twelve cannot itself validate a cutting date. Together
with the MARC offset (+50.4 d, all 25 districts positive, MAD 3.1 d), this is a
warning against agronomic identity, not proof of the true date.
Two consequences for this cell specifically:

* **It must not be read across the five window endpoints.** At DOY 365 three fifths of
  the fall-end breakpoints are extrapolations, so a change in the coefficient between endpoints
  is a change in what the coefficient is *of*. Its total range across the sweep, 16.132 d
  at district level, is therefore not a window sensitivity and is not reported as one.
* **It does not rest on the extrapolated units.** Re-estimated on the 191 of 208 units
  with at least one valid dekad after *t₄*: **−10.184 (t −2.08) → −8.084 (t −2.12)**.
  Sign preserved, *t* unchanged, magnitude attenuated with the 13% sample loss. The
  headline retention rule was **not** changed on this basis — changing a gate after
  seeing which units it would drop is the discretion §3 exists to remove — and the arm
  is reported alongside.

Source: `results/window_sweep/`, `python/window_sweep.py`.

## H4 — fails on its declared criterion

§2 requires the point estimate to "agree in sign with §4 for **at least five of the
six**" estimable named cyclones (Titli, Fani, Bulbul, Amphan, Yaas, Remal). **Two of
six agree.** The criterion is not met.

§2 already records that this is a consistency check and not a test — under
independent coin-flip signs five-of-six passes about 11% of the time — so the failure
is reported at that weight.

## H5 — withdrawn, not failed

§2 declares district-level Spearman ρ ≥ 0.70 between this study's QC-median SOS and
MODIS MOD13Q1 NDVI peak dates. **MODIS was never obtained for these districts and
seasons, so the correlation was never computed.**

An untested hypothesis has no verdict. Calling it a failure claims evidence that does
not exist, and in the wrong direction: it makes the study look as though it tested
more than it did. Recorded as **withdrawn** by dated amendment, with the reason.

## H1c / H2c — reported, as declared

§2 declares these "product agreement, reported never tested", with **no threshold**,
"because passing or failing agreement with a 0.5° product would not establish or
refute correctness at 30 m". Both are now reported: mean signed transplanting-related offset +20.2 d
(sd 13.9), harvest +50.4 d (sd 7.8), against MARC's native 0.5° grid and a median of 7
MARC cells per district. Neither number is a pass or a fail.

---

## Why this matters beyond bookkeeping

"All five fail" is a stronger and more dramatic claim than the evidence supports, and
it is the kind of overstatement that a reviewer converts into a reason to doubt
everything else. The corrected version is less tidy and more defensible: **the design
fails where it was tested and could not be tested where it was not.**

**The window sweep is a bounded sensitivity result.** §4.1 withdraws
every causal claim of §3.8 on the strength of §3.9's timing placebo — β_harv on the
trough breakpoint, declared zero. The §1.4 window sweep re-estimated it at all five
pre-declared endpoints, a 60-day change in the compositing window, with the standing to
overturn it. It measures **+7.291 to +8.099 d with cluster-robust *t* between +3.80 and
+4.30 at every endpoint**: a total spread of **0.807 d**, the tightest cell in the table.
The association persists across those five tested endpoints; this does not rule
out other design effects or identify its cause. β_harv on heading retains its
sign and exceeds the descriptive |t| = 1.96 reference at four of the five
endpoints (*t* +1.81 at DOY 365). That normal-reference comparison is neither
WCB nor permutation inference. Both `S_pre_season` cells on trough and heading
are not distinguishable from zero by that reference at the tested endpoints
(coefficient ranges 0.823 and 0.574 d); they are not established to equal zero.

What the study reports positively is a set of **measured disagreement statistics with their
scope attached**: between-orbit disagreement of 25.90 / 19.82 / 25.79 d on a single
pixel-season in the selected paired sample, a separate 80-draw Monte Carlo reporting
standard deviations 0.00 / 0.00 / 2.18 / 1.90 d for t1 / t2 / t3 / t4 on one
on-grid synthetic trajectory at an assumed 0.122 dB noise level, and a MARC harvest
offset averaging +50.35 d across 25 districts (range +26.19 to +60.54 d, all
positive). *(Rewritten 2026-09-14, sixth pass. This paragraph read
"the instrument resolves district-season timing to about ±1.3 d … and fails at a 30 m pixel
with σ ≈ 26 d, and that σ is corroborated by two independent routes". Every clause of that is
withdrawn: the two figures are not commensurable, the simulation is not a resolution, and the
semivariogram is neither independent nor a validation. MARC is genuinely external; the internal
spatial diagnostic is not.)* **No scale boundary is claimed, and no ratio between the
pixel-scale and district-scale figures is reported.**

**Sources for every number here:** `results/orbit_agreement/Table_SX_OrbitAgreement.csv`,
`results/dispersion/Table_SX_Dispersion.csv`,
`results/semivariance/Table_SX_Semivariance_Summary.csv`,
`results/marc/Table_SX_MARC_Summary.csv`,
`results/permutation_test/Table_SX_Permutation_{district,pixel}.csv`,
`results/robustness/Table_SX_RobustnessArms_*.csv`,
`results/mask_sensitivity/Table_SX_MaskSensitivity_ALL.csv`,
`results/window_sweep/Table_SX_WindowSweep_{gates,coefficients}.csv`.

---

## §3.10 attrition diagnostics — added 2026-09-15, because this file did not mention them at all

**Why this section exists.** Until today the word "attrition" appeared **zero
times** in this file. §3.10 declares a per-stratum attrition diagnostic and a
reporting rule keyed to it, several of those diagnostics are significant, and the
authoritative verdicts table said nothing about any of it. The significant
results were sitting in `analysis/deviation_log.md`. That is a reporting gap, not
a new analysis: every number below was already in the committed tables.

### What the diagnostics measure

Retention — whether a pixel-season or district-season yields a usable fit —
regressed on exposure. The trigger is **raw p_WCB < 0.05**, predeclared in §3.10
item 3, and it is unchanged by anything here.

All at **9,999 replications at both levels** (§3.8). The pixel figures were
previously computed at 999; the superseded value is shown in brackets.

| level | stratum | coef | p_WCB (raw) | Holm | BH-FDR |
|---|---|---:|---:|---:|---:|
| pixel | `class:pre_season` | −0.0533 | **0.0008** *(was 0.0010)* | **0.0080** | **0.0060** |
| pixel | `cyclone:FANI` | −0.0877 | **0.0012** *(was 0.0040)* | **0.0108** | **0.0060** |
| pixel | `cyclone:TITLI` | +0.0683 | **0.0094** *(was 0.0070)* | 0.0752 | 0.0313 |
| pixel | `phase_attrition:S_phase_rise` | +0.0358 | **0.0411** *(was 0.0420)* | 0.2877 | 0.1028 |
| district | `class:harvest_window` | −0.1260 | **0.0397** | 0.3970 | 0.2160 |
| district | `cyclone:YAAS` | +0.1063 | **0.0432** | 0.3970 | 0.2160 |

**The trigger set is unchanged by the tenfold increase in replications.** The
same seven output labels fire and the same two pixel designs survive Holm.
Coefficients do not depend on the bootstrap and did not move.

**THE TRIGGER ACCOUNTING, STATED ONE WAY EVERYWHERE.** There are **seven
triggered output labels** — five at pixel level and two at district level —
representing **six distinct tested designs**, because one pixel pair is a
*verified alias*: `class:pre_season` and `phase_attrition:S_phase_pre_window`
are the same regression reported under two names, their exposure vectors being
elementwise identical across all 225 district-seasons. *(Corrected 2026-09-15,
fourteenth pass: earlier passes wrote "six strata" in one place and "five pixel
and two district" in another, which are two different counts of the same thing.
Seven labels, six designs, stated that way from here on.)*

**Retention is associated with exposure at pixel level, and the strongest of
these is not a marginal result.** `class:pre_season` at p_WCB 0.0008 survives
both adjustments.

**`phase_attrition:S_phase_pre_window` is not a seventh finding.** It is
`class:pre_season` under a second name — identical coefficient, standard error
and p to every digit. Multiplicity here is computed on **unique regression
signatures**, so it is counted once; the conservative all-11-labels calculation
is carried alongside in `Table_SX_AttritionTriggers.csv`
(`p_wcb_holm_all_labels`, `p_wcb_bh_all_labels`) and gives Holm 0.4367 and
BH-FDR 0.2376 for the two district results.

**The district results do not survive multiplicity adjustment.** With 11 strata
tested per level, p = 0.0397 and p = 0.0432 are the kind of thing multiple
comparisons produce. The predeclared trigger still fires on the raw p, because it
was declared on the raw p; the adjustment is reported as a transparent
sensitivity and not as the gate.

### The distance null and the exposure-indicator findings, together

§3.10's selection model reports **no association between retention and distance
to the 34-kt track** (`dist_to_track_km` = −0.0001, indistinguishable from zero).
The diagnostics above report **associations with exposure class and with
individual cyclones**.

These do not contradict each other and neither overrides the other. They are
**different predictors in different models**: a continuous distance covariate
inside a pixel-level selection logit, against a treatment indicator in a
difference-in-differences attrition regression. A pixel can sit far from a track
and still be in a district-season the catalogue classes as exposed. Reporting
only the null — which is what §3.10's live text and Figure 7 did until the
eleventh pass — leaves a reader with "exposure does not drive retention", and
the diagnostics do not support that.

### What follows for the coefficients

§3.10 item 3's reporting rule fires for every stratum above. Each is classified in
`results/s310_v2_<level>/Table_SX_AttritionTriggers.csv` and the magnitude is
reported as **not point-identified under differential attrition**.

The one that bears on a headline number is **district `class:harvest_window`**,
which shares its indicator with `headline:trough:S_harvest_window` = **+5.001 d**
(se 3.103, p_WCB 0.1102).

**That +5.001 d is not an identified magnitude, and three separate things stop it
from being one.** Its own p_WCB is 0.1102. Its IPSW comparator does not exist —
the district-level logit does not converge (§3.10), so no `ipsw:` row is
produced. And its balanced-composition comparator is **not defined at class
level**: item 3c restricts to units retained in both seasons *"of that cyclone"*,
per cyclone, and `harvest_window` spans several cyclones in several seasons.

**The per-cyclone balanced rows are not a comparator for it.** They are separate
descriptive sensitivities, each estimated on the two seasons of one cyclone, and
the arm is indexed by the storm's *season*, so FANI and BULBUL return one number
twice. Their spread is a spread *across samples*, not an interval for one
quantity, and quoting it as though it bracketed +5.001 d would be an invented
comparator.

**`delta_beta` is retired as a composition sensitivity (2026-09-15).** It
compares a **two-season** balanced fit with an **all-season** pooled headline, so
it changes the time window as well as the composition and identifies neither. A
valid composition sensitivity must hold outcome, exposure definition, seasons,
controls, fixed effects and inference settings fixed and differ only in which
units are included; no such estimator is declared in this protocol and none is
introduced now. The obsolete columns do not appear in newly generated tables.
Historical logs retain them as a record of what was computed;
`balanced_n_pixels` remains to describe the two-season sample.

**No pooled class-level balanced estimator has been introduced.** At least four
pooled definitions are available (union, intersection, stacked with fixed
effects, fully balanced panel) and item 3c explicitly rules out the fourth;
the protocol selects none of the rest. Choosing one now, with the coefficients
visible, would measure the choice. This is recorded as a **post-analysis
implementation gap** and the pooled magnitude is reported as not point-identified.

### What was fixed to make this reproducible

`run_all.sh` never passed `--balanced`, so the declared reproducible run emitted
**no balanced rows at all**. The pixel table had none anywhere — the level where
four distinct diagnostics are significant — and the district table's 132 balanced
rows came from a hand-run the pipeline did not reproduce, so a rerun **silently
deleted them**. The runner now requests the arm at both levels and
`python/attrition_completeness.py` fails the run if a triggered stratum is
missing any required status, if a status is blank rather than an explicit
`not_estimable:<reason>`, if keys are duplicated, or if the balanced block
shrinks below its recorded floor.

**No coefficient moved materially, and the measured truth is stated rather than
rounded away.** Re-running both levels changed **no bootstrap-independent field
by more than 1.4 × 10⁻¹⁴ relative** — coefficients, standard errors, t
statistics, cluster counts, sample sizes — against a stated tolerance of 10⁻⁹.
There are **1,018 last-digit differences** in that block across the four tables,
and they are counted as differences rather than absorbed under a tolerance, which
is what the previous pass did when it reported "0 fields with a different value".

**The pixel bootstrap statistics did move, and that is the correction.** The
committed pixel table was computed at **999** replications while Protocol §3.8
declares **9,999**; the whole pixel analysis has been re-run at 9,999 rather than
reusing any 999-replication row. 1,078 bootstrap-dependent fields changed, all of
them at pixel level; the district table, already at 9,999, shows **0 material
differences in either block**. The trigger set is unchanged.

132 pixel balanced rows that had never been computed were added.

**Final replay correction, 2026-09-16.** The counts `1,018` and `1,078` above
describe an earlier comparison pass and are not stable scientific quantities;
they must not be quoted in the manuscript. The accepted evidence is the clean
no-resume replay itself: exact expected key sets, all applicable WCB rows at
9,999 successful draws, and no retained coefficient/SE/t/count difference above
1e-9. One underpowered non-trigger WCB p-value differs by one draw from the
immediately preceding candidate (`cyclone:REMAL`, 0.7134 → 0.7135); a targeted
clean recomputation returns 0.7135. No trigger, multiplicity result, hypothesis
verdict or interpretation changes.
