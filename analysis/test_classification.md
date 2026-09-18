# Classified index of every test and decision

**Created 2026-09-13, at `775aef2`.** Written on the recommendation of an external
audit, which observed that this project's changes "can remain defensible only if
they are clearly dated and separated into original confirmatory tests, protocol
deviations made before results, and result-aware robustness or exploratory
analyses." The logs carry that separation chronologically across twenty-three dated
entries; nothing carried it as a single table a reviewer could read in one pass.
This is that table.

## The classes, and why there are four

The audit asked for three. Three is not quite enough for this study, because the
largest group of design changes was driven by measurement on the **untreated 2017
baseline season** — before any treated season was fitted and before any exposure
coefficient existed. Those are neither blind deviations nor result-aware choices,
and collapsing them into either class would misdescribe them. So:

| class | definition | researcher-degrees-of-freedom risk |
|---|---|---|
| **A** | Predeclared test; confirmatory only to the extent the frozen estimand and implementation were preserved. | reduced, not zero; documented deviations still apply |
| **B1** | Deviation for feasibility or data availability. No measurement involved. | low — the alternative was not available |
| **B2** | Deviation driven by measurement on the **untreated 2017 baseline only**. No treated season fitted, no exposure coefficient in existence. | moderate — a measurement informed it, but not the tested one |
| **C** | Decision made **after** treated-season exposure coefficients were known. | **high — read these first** |

**The boundary between B2 and C is 2026-09-12, third entry**, the last design
decision recorded before any exposure coefficient existed. The panel was extracted
2026-09-11; the estimator and unit of analysis were settled on the 2017 baseline in
the 2026-09-12 entries; the first β on a treated season dates from 2026-09-12/13.
Everything dated 2026-09-13 or later that changed an analysis choice is class C by
construction, and is listed as such even where the choice was conservative.

A fifth group, **defect corrections**, is listed separately at the end. These are
not design choices — they are errors found and fixed — but they are dated, and one
of them changed a headline number.

---

## Class A — confirmatory

Predeclared in `docs/Protocol_v1.md`, frozen before the data they were tested on,
and tested as written.

| test | declared at | frozen | verdict |
|---|---|---|---|
| H1 clause (a) — radar trough between-orbit agreement, tolerance fixed on 2017 | §2 | 2026-09-09 | **MET as declared** — 0.9443 within T = 70 d against a 0.90 criterion. *Corrected 2026-09-14: this row read NOT MET on the 38.2%-within-one-dekad figure, which is a stricter test §2 never declared* |
| H1 clause (b) — radar trough within- vs between-pixel dispersion | §2 | 2026-09-09 | **NOT MET** — 1.340 [1.273, 1.408] |
| H2 clause (a) — as H1, radar fall-end | §2 | 2026-09-09 | **MET as declared** — 0.9114 within T = 60 d against 0.90; fails in Andhra Pradesh alone (0.8564, n = 195). *Corrected 2026-09-14, as H1 clause (a)* |
| H2 clause (b) — as H1, radar fall-end | §2 | 2026-09-09 | **NOT MET** — 1.508 [1.424, 1.592] |
| H3 — β_pre > 0 on SOS, peak, EOS; β_harv > 0 on EOS | §2, §4 | 2026-09-07 | **NOT ESTIMABLE AS DECLARED** — those are optical constructs; this study fits radar breakpoints that §3 states are not them (MARC: harvest-related breakpoint **+50.4 d** from the MARC harvest date, all 25 districts). Radar analogue **exploratory**: 0 of 4, β_pre on the fitted fall-end breakpoint is significant in the direction **opposite to the predeclared analogue**. *Corrected 2026-09-14: this row read "NOT MET, 0 of 4", which claims a test that was never run* |
| H4 — β₀ sign agreement, 5 of 6 named cyclones | §2 | 2026-09-09 | **FAILS on its declared criterion — 2 of 6** |
| H5 — MODIS district SOS coherence, ρ ≥ 0.70 | §2 | frozen | **WITHDRAWN — not tested, not failed**; §4.3.2 (data never acquired). An untested hypothesis has no verdict |
| §3.9 timing placebo — β_harv on the fitted trough breakpoint = 0 | §3.9 | frozen | **REJECTED IN THE PIXEL ROBUSTNESS ARM** — +7.438 d, p_WCB 0.0008, p_perm 0.0395; district headline +5.001 d, p_WCB 0.1102, p_perm 0.3068 is inconclusive |
| §3.9 lead test — λ = 0, p > 0.10 | §3.9 | frozen | **FAILS** for the harvest-window class at pixel level |
| §3.9 spatial permutation, 2,000 draws | §3.9 | frozen | run 2026-09-13 |
| §3.9 SAR sanity check | §3.9, §3.3 | frozen | run |
| §3.9 r-value grid | §3.9 | frozen | withdrawn, §4.3.3 (inapplicable to a breakpoint estimator) |
| §3.10 attrition diagnostic and IPSW | §3.10 | 2026-09-09 | clean no-resume reruns passed exact-key and field-by-field completeness gates at 9,999 draws on 2026-09-16; seven triggered output labels represent six designs; two-season restrictions remain descriptive, not same-estimand composition comparators |
| §3.8 A robustness — state × season FE, 75 km, 100 km, 64 kt | §3.8 A | 2026-09-07 | corrected clean reruns completed at 9,999 draws on 2026-09-16; 30 keys preserved at each level, six state-by-season cells explicitly lack an implemented WCB, and no 0.05/0.10 verdict reverses |
| §3.8 A robustness — HLS panel 2016–2025 | §3.8 A | — | withdrawn, §4.1.8 |
| §3.5 mask sensitivity — primary vs intersection mask | §3.5 | 2026-09-09 | **Corrected 2026-09-16 against the current tables.** In the declared six-cyclone block, 35 paired estimates are available and sign agreement is **31/35 trough, 22/35 heading, 21/35 harvest**. The former 47-unit claim mixed estimands/rosters and is withdrawn. Seven additional estimable pairs are separately exploratory. Mask choice can materially change per-unit descriptive estimates; no general mask-stability conclusion is supported. |

Four class-A items were **run after the headline coefficients were known** — the
permutation test, the robustness arms, and both clauses of H1/H2. Their *design* was
frozen beforehand and none was altered on seeing the result, so they remain
confirmatory; but a reviewer should know the order, and §4.1.7 records that the
permutation test's historical *interpretation* was class C. Its bootstrap-calibration
rationale and preference rule were withdrawn on 2026-09-16; both conditional
inference procedures are now reported, without declaring either validated.

---

## Class B1 — feasibility deviations, no measurement involved

| date | change | why it was not a choice |
|---|---|---|
| 2026-09-07 | Exposure derived from IBTrACS by a fixed rule, not assigned by hand | the hand-assigned stacked design had no clean controls: Fani's ≥48 kt track exposes 17 of 18 Odisha and West Bengal roster districts |
| 2026-09-09 | Substrate Sentinel-2 → Sentinel-1 | the optical panel cannot observe the ascending limb under monsoon cloud |
| 2026-09-09 | H1/H2 accuracy claims withdrawn, replaced by consistency claims | no field-observed transplanting or harvest date exists for these districts in any panel season |
| 2026-09-09 | HLS removed as the pixel-level validation substrate | HLS is Landsat + Sentinel-2, under the same cloud |
| 2026-09-09 | Lee bounds withdrawn (§3.10 3b) | not computable on this design |
| 2026-09-09 | Rice mask → RiceAtlas ∩ Chen et al. 2024 | RiceAtlas alone supplies no within-polygon pixel filter |
| 2026-09-09 | Roster cut to 25 districts; panel extended to 2017–2025 | Sentinel-1 coverage permits 2017; the 2019 floor was a Sentinel-2 artefact |
| 2026-09-09 | H4 event set 5 → 6; criterion 4-of-5 → 5-of-6 | Titli and Fani become estimable with the 2017 floor; the criterion was *tightened* to offset the extra event. No result existed under either wording |
| 2026-09-13 | H5 withdrawn (§4.3.2) | the MODIS panel was never exported |

---

## Class B2 — driven by measurement on the untreated 2017 baseline only

No treated season had been fitted and no exposure coefficient existed when any of
these was decided. Each is a measurement-driven change to the *instrument*, made
before the instrument was pointed at the question.

| date | change | the baseline measurement that forced it |
|---|---|---|
| 2026-09-12 | Double-logistic abandoned | failed its calibration check on the 2017 baseline |
| 2026-09-12 (2nd) | Three open radar parameters derived and closed | derived on the baseline, then frozen |
| 2026-09-12 (2nd) | Selection-aware critical values (`plsm_null_t*.csv`) | the nominal t-test gives 29% false positives after searching thousands of breakpoint quadruples |
| 2026-09-12 (3rd) | Feature-extraction estimator superseded; **PLSM adopted as primary** | four measured failures on the baseline, listed in that entry |
| 2026-09-12 (3rd) | **No phenometric calendar gate** in the primary specification | the radar breakpoint distribution lies later than the positions of Paper 1's optical bounds — a separation of roughly 40–60 d — so those bounds are not transferable across these measurands: 54% of retained troughs sat on the last admissible dekad. *(Reworded 2026-09-14, ninth pass: this read "Paper 1's optical windows are 40–60 d **too early** for the radar season".)* |
| 2026-09-12 (3rd) | Gate 1 inert at pixel level, applied at 0.5 to the district-mean curve | no gate vs r = 0.50 on the baseline: minimum valid dekads 19 vs 10; the gate manufactures the only §3.11 ineligibility in the entire baseline |
| 2026-09-12 (3rd) | Gate 3 served by the rise-significance screen | PLSM has a residual, so Gate 3's role is not vacant |
| 2026-09-12 (3rd) | **Headline TWFE moved to the district-season panel** | per-pixel marker dates carry a split-half disagreement of σ ≈ 18 d; district-mean series carry a sampling se of 0.122 dB against 2.03 dB per pixel. *(Reworded 2026-09-14, ninth pass: this row read "per-pixel σ ≈ 18 d **against** ±1.3 d on the district-season mean". The contrast is withdrawn as a justification. ±1.3 d is a **separate conditional simulation** — a Monte Carlo recovering its own planted breakpoints on a synthetic trajectory under an assumed noise level — and it does not demonstrate the actual precision of the district panel, for which this study holds no repeat measurement.)* |

The last of these matters most for reading the results. A later quantity measured on a
different principle — the between-orbit disagreement of 25.90 d (class A, H1 clause (a)) —
is of similar magnitude to the per-pixel figure this decision rested on. *(Rewritten
2026-09-14, sixth pass: this read "**independently corroborated after the fact**".
Withdrawn. Both quantities read the same Sentinel-1 panel through the same breakpoint
estimator, so neither is independent of a defect in the other, and a similar magnitude is
not a confirmation.)* The decision to work at district level was made on baseline evidence
and nothing measured since has overturned it. *(Amended 2026-09-14, ninth pass: this
sentence used to end "the ±1.3 d figure **in the row above** remains a Monte Carlo on a
synthetic trajectory, not a measured district-scale accuracy". The row above no longer
carries that figure — the contrast between per-pixel disagreement and the simulated
±1.3 d was removed as a justification for the district headline, because a conditional
simulation cannot demonstrate the precision of the real district panel. The reference is
removed with it; the decision rests on the reasoning recorded in §3.8, not on that
comparison.)*

---

## Class C — result-aware. Read these first.

Every item here was decided **after** treated-season exposure coefficients were
known. For each, what protects it is stated; where nothing protects it beyond
judgement, that is said.

| date | decision | what protects it |
|---|---|---|
| 2026-09-13 (§4.1.1) | **Primary outcome family declared as four tests** | **The most exposed decision in this study.** Written after 22 coefficients had been inspected. Protection: the four are §4's own predeclared text, verbatim — β_pre on SOS/peak/EOS and β_harv on EOS — and no coefficient was added or removed by choice. But the *act* of writing the family down came after seeing them, and a reviewer should verify the four against §4 rather than take this table's word for it |
| 2026-09-13 (§4.1.1) | Multiplicity policy: Bonferroni 0.05/4 on individual family members | same exposure as above; H3 itself is a conjunction and needs no correction |
| 2026-09-13 (§4.1.1) | β_harv on **peak** demoted to exploratory | §4 declares "no value" for this cell, and that text predates all results. It had been reading as the headline in working notes; the demotion removes a coefficient that *favoured* the hypothesis |
| 2026-09-13 (§4.1.4) | **The censoring test built** after the placebo failure | Designed after seeing a result, so class C by definition. Protection: the design, arms, window, and outcome incompatible with the candidate estimator-deformation pathway were recorded before it was run. The diagnostic establishes estimator dependence in its common pixel sample, not the cause of the observed association. |
| 2026-09-13 (§4.1.4 corr.) | Arm (3) of the censoring test demoted after its ceiling was found | a correction of my own analysis against itself; the conclusion was moved onto arm (2), which is ceiling-free |
| 2026-09-13 (§4.1.7) | Historical decision to prefer permutation p for harvest-window coefficients | **Preference and calibration rationale withdrawn 2026-09-16.** A larger observed p-value does not establish better calibration or validity. Both reference schemes have unverified assumptions in this observational design. |
| 2026-09-13 (§4.1.8) | **No robustness arm promoted** despite state × season FE clearing the placebo at district level | result-aware, and the conservative direction: the declared headline was kept. Had the pixel arm agreed, promoting it would have been defensible — selecting a specification by a *placebo* is not selecting on the outcome of interest — but that case did not arise |
| 2026-09-13 (§4.1.5) | Every §3.8 coefficient withdrawn as a causal effect | forced by a predeclared falsifiability check failing, not chosen |
| 2026-09-13 (§4.3.1) | H3's construct mapping authorised for **direction only, never identity** | the verdict is 0 of 4 under either reading, so the mapping cannot have produced it. Affects what the verdict *means*, not what it *is* |
| 2026-09-13 | Exposure-phase arm reported **alongside** the frozen timing classes | the frozen classes were deliberately kept as the headline: "re-classifying exposure after seeing the results is exactly the discretion this protocol exists to remove" (§3.8) |

**Interpretation rule.** Whether a result-aware change makes a p-value larger or
smaller does not establish its validity. Each decision needs its own rationale,
and the original and revised analyses must remain distinguishable.

**Additional class-C analyses, 2026-09-16:** repeat-coverage sensitivity,
state-specific baseline tolerance diagnostics and alternative orbit-pair selection
rules. They are post-analysis robustness checks, not replacements for H1/H2's
frozen pooled criteria. Their limitations and execution receipts accompany the
corresponding tables.

---

## Defect corrections — not design choices

Errors found and fixed. Listed because they are dated and one changed a headline
number.

| date | defect | effect |
|---|---|---|
| 2026-09-11 | 97 of 225 export files lost their measurements to Earth Engine header inference | re-exported with explicit `selectors` |
| 2026-09-13 | **`twfe` never restricted to `retained == 1`** while its error strings said "retained" | district 213 rows used vs 208 retained; pixel **44,976 contaminating rows, 59% of the headline sample**. heading +7.11 → **+6.18 d**; plateau p .0488 → .0907; fill p .0449 → .0565. Two "significant" findings were artefacts. Independently reproduced by the external audit |
| 2026-09-13 | A split-half number asserted rather than measured | measured and corrected in all logs |
| 2026-09-13 | Phase accounting quoted from a superseded probe | corrected |
| 2026-09-13 | `S1_STATIC_COVARIATES.js` had invented asset ids and the wrong filter field | caught before it ran |
| 2026-09-13 | `fit_cell` in `permutation_test.py` did not restrict to `retained == 1` | caught by a self-test comparing against `twfe`'s published number; no permuted result was computed before the fix |
| 2026-09-13 | `permutation_test.py --selftest` required a pipeline output | caught by a receive-only executor, which refused to commit |

---

## What a reviewer should check, in order

1. **The four class-A verdicts against §2 and §4.** Confirm no criterion was rewritten
   to produce its verdict — in either direction. *Corrected 2026-09-14 (second pass): this
   line read "Every predeclared hypothesis fails", the verdict withdrawn as result-aware on
   2026-09-13. The table above was corrected in the first pass of this date and **this line
   was missed** — the same propagation failure the external re-audit found across three
   files, recurring inside a file that was being corrected for it. Found by a follow-up sweep
   of the same phrase, not by an audit.* The corrected verdicts are: one hypothesis fails on
   its declared criterion (H4), two fail on clause (b) while clause (a) passes as declared
   (H1, H2), one is not estimable as declared (H3), and one was withdrawn untested (H5).
   `analysis/hypothesis_verdicts.md` is authoritative.
2. **The class-C table against the amendments it cites.** Particularly §4.1.1: are
   the four family members §4's own, or were they chosen?
3. **The B2 boundary.** Confirm no exposure coefficient predates 2026-09-12's third
   entry. The logs are append-only and dated; the commit history at `775aef2` and
   before is the independent record.
4. **The defect corrections.** One of them moved a headline coefficient and removed
   two claims of significance. The external audit reproduced it independently from
   `a59f5fa`.
