# Deviation Log — RiceBaCI-QC (Paper 2)

> Current-reading notice, 2026-09-16: historical claims of bootstrap
> miscalibration inferred from permutation quantiles, mechanism identification
> by relabelling, and general per-unit mask stability are superseded. See the
> dated correction in Protocol §4.1.7 and `current_audit_status.md`. This notice
> does not alter the original entries or imply the current audit is complete.

Append-only record of deviations from the locked OSF Pre-Registration
(`osf/OSF_PreReg_v0.2.md`). Each entry must state: **what changed**,
**why**, **what it affects in the pre-reg**, and **the new commitment**.
Do not edit prior entries — only append new ones.

---

## 2026-06-15 — DEV-001: Drop control years 2017 & 2018 (S2 L2A unavailability)

### What changed
The pre-registered analysis years were:

> **§3.1 (OSF_PreReg_v0.2):** 2017, 2018, 2020, 2021, 2022 — with 2020 as
> the Amphan treatment year and the remaining four as untreated controls.

Effective with `gee/S2_QC_Ingest.js` v0.3.1 (commit on 2026-06-15), the
analysis years are:

> **Revised:** 2019, 2020, 2021, 2022, 2023 — with 2020 as the Amphan
> treatment year and 2019, 2021, 2022, 2023 as untreated controls.

### Why
The dry run of `gee/S2_QC_Ingest.js` v0.3 on Nadia × 2017 × tile01 failed
with `Image has no bands` during `Export.table.toDrive`. Root cause:

- **Sentinel-2 Surface Reflectance Level-2A** (the product we are
  required to use per OSF §3.2 for atmospheric-correction parity across
  treatment and control) entered **global** production on
  **2018-12-18**. Before that date, S2 L2A exists only over Europe.
- The GEE collection `COPERNICUS/S2_SR_HARMONIZED` therefore returns
  an **empty `ImageCollection`** for any West Bengal AOI in 2017 and
  for the Kharif-relevant window (DOY 152–304) of 2018.
- Empty collections produce empty `.median()` images, which propagate
  to a zero-band `Image` and crash `Export.table.toDrive`.

We considered three alternatives and rejected each:

| Option | Decision | Reason |
|---|---|---|
| (A) Substitute S2 L1C TOA for 2017–2018 | Reject | Breaks AC parity with treatment year; introduces SR-vs-TOA confound that contaminates DiD. |
| (B) Use Landsat 8 SR for 2017–2018 controls | Reject for primary panel | Sensor-mix confound mirrors (A). Will instead be used for the *separate* Landsat HLS pre-trends robustness check (`gee/HLS_QC_Ingest.js`, Day 4). |
| (C) Replace 2017 & 2018 controls with 2019 & 2023 | **Accept** | Keeps S2 L2A consistent across all panel-years. Preserves T = 1 treated + N = 4 controls. Maintains balance: 2 pre-treatment controls (2019) and 3 post-treatment controls (2021, 2022, 2023). |

### Affected pre-reg sections (OSF_PreReg_v0.2.md)
- **§3.1 Study Period:** years list `[2017, 2018, 2020, 2021, 2022]` → `[2019, 2020, 2021, 2022, 2023]`.
- **§4.2 DiD Specification:** pre-period is now {2019}; post-period
  controls are {2021, 2022, 2023}. Two-way fixed effects unchanged.
  Wild-cluster bootstrap (9999 reps, district level) unchanged.
- **§4.4 Parallel-Trends Diagnostic:** With only one pre-treatment
  year of S2 data, the visual parallel-trends plot from S2 alone is
  weak. **Mitigation:** the formal pre-trends test will be run on the
  Landsat HLS panel (`gee/HLS_QC_Ingest.js`, Day 4), which extends
  back to 2014 and provides ≥5 pre-treatment years per district. This
  was already the design intent for H2 (pixel-level RMSE on HLS);
  it is now also the primary pre-trends evidence base.
- **§5 Falsifiability Checks:** placebo-year tests will draw from
  {2019, 2021, 2022, 2023} instead of {2017, 2018, 2021, 2022}.
  Sample of placebos is reduced from 4 to 4 (unchanged count, but the
  draw distribution shifts toward post-treatment years).

### Pre-specified impacts on hypotheses
- **H1 (peak-relative Gate 1 separates rice from non-rice):** unaffected.
  Pixel-level test runs within each year independently.
- **H2 (QC-screened phenometric harvest-date bias and RMSE against the
  Zhao et al. 2024 MARC benchmark on HLS):** unaffected — HLS panel is
  the validation substrate, not S2. The authoritative sub-claim wording is
  in `docs/Protocol_v1.md` §2 (H2a: harvest-date bias against MARC's
  reported −5.76 d; H2b: harvest-date RMSE against MARC's reported
  28.32 d).
- **H3 (Amphan reduces SOS lateness vs controls, DiD coefficient
  significant at p < 0.05 wild-bootstrap):** mildly affected. Power
  computation re-runs with N_pre = 1 instead of N_pre = 2. To be
  re-computed in `python/Power_DiD.py` on Day 5; current pre-reg
  Table S6 (MDE = 4.2 days at α = 0.05) will be superseded.
- **H4 (transferability to a second cyclone):** unaffected.
- **H5 (district-level MODIS Spearman ρ ≥ 0.70 between QC SOS and
  MOD13Q1 NDVI peak):** unaffected.

### New commitment
1. `gee/S2_QC_Ingest.js` CONFIG.years is now `[2019, 2020, 2021, 2022, 2023]`.
2. The script also carries a "dummy-schema armor" patch
   (`dummy.addBands(composite, null, true)`) so that any empty bin in
   any future year still exports as a masked CSV row rather than
   crashing the task. This is defensive — under the revised year list,
   no bin should be globally empty, but the armor protects against
   district-tile-bin combinations with zero valid pixels after the
   SCL + cloud-probability mask (e.g., monsoon overcast weeks).
3. The pre-trends test of record moves to the HLS panel in
   `gee/HLS_QC_Ingest.js` (Day 4 deliverable).
4. Power and placebo tables (S6, S7) will be re-generated with the
   revised year list before any DiD coefficient is reported.

### References
- Sentinel-2 L2A global production start date:
  https://sentinels.copernicus.eu/web/sentinel/-/sentinel-2a-products-availability
  (S2 L2A globally available from 2018-12-18; ESA Sentinel Online).
- GEE catalog page for `COPERNICUS/S2_SR_HARMONIZED`:
  https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED
  (date range starts 2017-03-28 but coverage is Europe-only until
  2018-12-18; user-confirmed empty for WB AOI in 2017 dry run).

### Logged by
Pipeline dry run 2026-06-15 (Nadia × 2017 × tile01) — user-confirmed.

---

## 2026-09-04 — Correction to DEV-001 H2 wording (in-place rewrite)

The H2 bullet under "Pre-specified impacts on hypotheses" in DEV-001 was
originally written as:

> H2 (QC-screened phenometric RMSE ≤ Han et al. 2024 benchmark on HLS):
> unaffected — HLS panel is the validation substrate, not S2.

That wording contained two errors: (1) "Han et al. 2024" is not a real
reference — it is a mis-attribution of Zhao et al. 2024 MARC (Monsoon Asia
Rice Calendar, ESSD 16, 3893–3921, https://doi.org/10.5194/essd-16-3893-2024);
(2) the single-metric "RMSE ≤ benchmark" framing conflated bias and RMSE,
which are separate metrics with separate MARC values (bias +3.93 / −5.76 d
for transplanting / harvest; RMSE 27.62 / 28.32 d). The sentence has been
rewritten in place to reference Zhao et al. 2024 MARC directly and to split
the test into the H2a (bias) and H2b (RMSE) sub-claims defined in
`docs/Protocol_v1.md` §2. The original DEV-001 entry is otherwise
unchanged. See also `docs/LitGap_v0.1.md` §8 for the full misattribution
history across the repo.

---

## 2026-09-05 — Cross-reference: attrition-correction decision

Not a deviation from a previously frozen protocol item; recorded here so a
reader following DEV entries doesn't miss it. On 2026-09-05 a new
downstream reporting-discipline decision was adopted: every Objective 4
DiD/TWFE coefficient in this study is accompanied by (i) a per-stratum
attrition diagnostic, (ii) an inverse-probability-of-survival-weighted
point estimate, and (iii) a Lee (2009) trimming-bound interval; any
stratum with zero treated support is reported as "not estimable". The
empirical trigger is Panda & Sahu (companion paper, in review at
*Remote Sensing Applications: Society and Environment*), which documents
a treatment × cyclone-window coefficient of +0.29 (i.e. +29 percentage
points) on extraction-failure rate, measured on its native 0–1
proportion scale (p_WCB = 0.010; 95% WCB CI 0.108–0.422), in this same
QC pipeline. Full decision text and rationale in
`analysis/decisions_log.md` under "2026-09-05 · Attrition correction
adopted for all Objective 4 DiD/TWFE reporting". Procedural specifics are
frozen in `docs/Protocol_v1.md` §3.10.

---

## 2026-09-06 — Cross-reference: WorldCereal 2021 sensitivity-mask characterization corrected

Not a deviation from a previously frozen protocol item; recorded here so a
reader following DEV entries doesn't miss it. On 2026-09-06 the
characterization of the WorldCereal 2021 sensitivity mask was corrected
across `docs/rice_mask_options.md` §§3.2, 4, 5, 6, `docs/Protocol_v1.md`
§3.5, and the `gee/S2_QC_Ingest.js` v0.4 draft. The v100 WorldCereal
ImageCollection (`ESA/WorldCereal/2021/MODELS/v100`) contains no rice
product; v100 products are `temporarycrops`, `maize`, `wintercereals`,
`springcereals`, and `irrigation` (Van Tricht et al. 2023, ESSD 15,
5491–5515, §2.2 and §5.1). The sensitivity mask is therefore the
`temporarycrops` product — a general cropland / non-cropland binary
classifier, not a rice-differentiated product — and the 88.5 % user's /
92.1 % producer's accuracy figures in `docs/rice_mask_options.md` §3.2
apply to temporarycrops globally, not to a rice class. The intersection-
mask sensitivity test therefore tests "is this pixel any cropland (per
WorldCereal) versus is this pixel inside a rice polygon (per RiceAtlas)"
and not "is this pixel rice versus rice"; the disagreement-flag name is
updated from `high_disagreement` to `high_cropland_disagreement` to
reflect this. No Paper 1 numerical results, Paper 2 protocol items, or
2026-09-05 attrition-correction decisions are affected. Full decision
text, empirical trigger, rationale, and file-by-file impact in
`analysis/decisions_log.md` under "2026-09-06 · WorldCereal 2021
sensitivity-mask characterization corrected — no rice product exists in
v100".

## 2026-09-07 — Cross-reference: attrition correction extended (balanced-composition check, graduated reporting-language rule)

Not a deviation from a previously frozen protocol item; recorded here so
a reader following DEV entries doesn't miss it. On 2026-09-07 the
2026-09-05 attrition-correction decision was extended with (i) a
balanced-composition robustness check (re-estimating each DiD on pixels
retained in both the pre- and post-cyclone season of that cyclone) and
(ii) a graduated reporting-language rule covering the case where treated
support is nonzero but the Lee (2009) bounds include zero. Neither
addition revises the 2026-09-05 decision or any prior entry. Full
decision text and rationale in `analysis/decisions_log.md` under
"2026-09-07 · Attrition correction extended — balanced-composition check
and graduated reporting-language rule". Procedural specifics are frozen
in `docs/Protocol_v1.md` §3.10.

## 2026-09-07 — Cross-reference: units-label correction to attrition coefficient

Not a deviation from a previously frozen protocol item; recorded here so
a reader following DEV entries doesn't miss it. On 2026-09-07 the
"+0.29 percentage-point" phrasing used to describe the Paper 1
attrition-regression coefficient (in the 2026-09-05 entry above,
`analysis/decisions_log.md`'s 2026-09-05 entry, and
`docs/Protocol_v1.md` §3.10) was corrected in place to "+29 percentage
points" — 0.29 is the coefficient on the underlying 0–1 proportion
scale, not already a percentage-point figure. SE, p-values, and the
95% WCB CI were already correct on that same 0–1 scale and are
unchanged. No decision is revised. Full text in
`analysis/decisions_log.md` under "2026-09-07 — Correction to prior
entry (units label, in-place rewrite)".

## 2026-09-07 — Cross-reference: DiD specification moved to pixel-year level

Not a deviation from a previously frozen protocol item — no extraction
has been run under the old district×year specification
(`CONFIG.enableRealExports` is still `false`); recorded here so a
reader following DEV entries doesn't miss it. On 2026-09-07 §3.8's
headline DiD/TWFE specification was changed from district×year to
pixel-year (pixel and year fixed effects, standard errors clustered and
wild-cluster-bootstrapped at district level), to match the pixel-level
operation of §3.10's attrition diagnostic, IPSW weighting, Lee bounds,
and balanced-composition check. Full decision text and rationale in
`analysis/decisions_log.md` under "2026-09-07 — DiD specification moved
to pixel-year level (§3.8), matching §3.10's attrition correction".

## 2026-09-07 — Cross-reference: Gate 3 (fit-quality screening) added

Not a deviation from a previously frozen protocol item — Gates 1 and 2
are unchanged, and no extraction has been run yet; recorded here so a
reader following DEV entries doesn't miss it. On 2026-09-07 a Gate 3
(fit-quality screening via RMSR, adopted from Paper 1's Gate C) was
added as `docs/Protocol_v1.md` §3.11, and the previously undocumented
curve-fitting method (Whittaker–GCV smoothing + Beck et al. 2006
double-logistic fit) was stated explicitly at the top of §3 for the
first time. This resolves §3.10 item 3a's previously-undefined "QC
Gates 1–3" reference. Full decision text, rationale, and the
implementation note (new `rmsr`/`gate3_pass` panel columns needed
before real extraction) are in `analysis/decisions_log.md` under
"2026-09-07 — Gate 3 (fit-quality screening) added to §3; curve-fitting
method now stated".

## 2026-09-07 — Cross-reference: Kolkata-exclusion documentation added to §1.3

Not a deviation from a previously frozen protocol item — the 27-district
extraction roster in `gee/S2_QC_Ingest.js` is unchanged; only the
protocol's documentation of it changed; recorded here so a reader
following DEV entries doesn't miss it. On 2026-09-07 `docs/Protocol_v1.md`
§1.3 was amended to explicitly document that Kolkata is dropped from the
28-district `docs/coastal_districts_gadm41.csv` coastal-buffer roster to
reach the 27-district extraction roster, because IRRI RiceAtlas v1.0 has
no rice-extent polygon for Kolkata (`docs/coastal_districts_crosswalk.csv`:
`match = EXCLUDED, poly_count = 0`). Full decision text and rationale in
`analysis/decisions_log.md` under "2026-09-07 — Kolkata's exclusion from
the 27-district extraction roster, versus the 28-district coastal-buffer
file, documented".

## 2026-09-07 — Cross-reference: §3.8 fixed effects corrected to district + year; §3.11 cadence and eligibility aligned with Paper 1

Not a deviation from a frozen protocol item — no extraction has run
(`CONFIG.enableRealExports` is still `false`); recorded here so a reader
following DEV entries doesn't miss it. On 2026-09-07 §3.8's pixel fixed
effect (introduced earlier the same day and wrongly attributed to Paper 1)
was corrected to district + year fixed effects at pixel-year level, which
is Paper 1's actual Model 2; the reason pixel fixed effects are excluded
from the headline (they condition on surviving the cyclone and collapse
the balanced-composition check onto the headline) is now stated in §3.8.
The §3 lead-in and §3.11 "dekadal" wording was corrected to Paper 2's
5-day cadence, Paper 1's observation-eligibility rule was carried into
§3.11 with a cadence-adjusted translation flagged for confirmation, and
assumption statements were added under §3.10 items 3a–3c. An open design
question on cross-cyclone contamination of the §1.1 control years is
recorded in the decisions log and remains open. Full text in
`analysis/decisions_log.md` under "2026-09-07 — §3.8 fixed effects
corrected to district + year (Paper 1 Model 2) …".

## 2026-09-07 — Cross-reference: window, Gate 2 bounds and fitting cadence re-based on the submitted Paper 1; stacked clean-control design adopted

Not a deviation from a frozen protocol item — no extraction has run
(`CONFIG.enableRealExports` is still `false`) and Gate 1's frozen r-values
and rule are untouched; recorded here so a reader following DEV entries
doesn't miss it. On 2026-09-07 the season window was corrected from DOY
152–304 to Paper 1's DOY 150–425 (the earlier "same as Paper 1" claim was
true only of the pre-correction Paper 1 design), Gate 2's bounds were
replaced by Paper 1's Gate B bounds (the earlier table was not Paper 1's),
curve fitting was moved to dekadal composites aggregated from the exported
5-day bins so that Paper 1's eligibility rule and RMSR threshold apply
without translation, and the same-district t ± 1, t ± 2 control-year rule
was replaced by a stacked clean-control event-study (one stack per
cyclone, district × stack and year × stack fixed effects, β₀ headline, lead
test replacing the temporal placebo). `gee/S2_QC_Ingest.js` CONFIG
`seasonStartDOY`/`seasonEndDOY` changed to 150/425 (file now v0.5.1; no logic
change).
Full text in `analysis/decisions_log.md` under "2026-09-07 — Protocol
re-based on the submitted Paper 1 …".

## 2026-09-07 — Cross-reference: Objective 4 exposure panel, pre-declared footprint rule, H3/H4 revision, seasons to 2025

Not a deviation from a frozen protocol item — no extraction has run
(`CONFIG.enableRealExports` is still `false`) and Gate 1's frozen r-values
and rule are untouched; recorded here because H3 and H4 are reworded.
Treatment for Objective 4 is now derived from the IBTrACS v04r01 catalogue
by `python/build_cyclone_exposure.py` (50-km buffer, ≥ 48 kt severe,
34–47 kt minor, timing class by month), the headline model is a
district-season exposure panel with district and season fixed effects,
the six named cyclones are an event-level view with clean controls from
the same tables, Sitrang is declared not estimable a priori, and
`CONFIG.years` runs 2019–2025. H3 now tests the pooled exposure
coefficients; H4 now tests unchanged r-values across states plus sign
agreement for four of five estimable named cyclones. Full text and the
pre-revision H3/H4 wording in `analysis/decisions_log.md` under
"2026-09-07 — Objective 4 redesigned as a catalogue-derived exposure
panel …".

## 2026-09-08 — DEV: candidate cohort added to §3.6 after the freeze; per-tile export grid retired

First amendment to `docs/Protocol_v1.md` after its freezing commit
`2cf493a` (2026-09-07), recorded here under §5.3. **No threshold or
hypothesis in §3 is changed** and no extraction has run
(`CONFIG.enableRealExports` is still `false`).

What changed: §3.6 now defines the candidate cohort the panel is extracted
at — 400 pixels per district, drawn once by `stratifiedSample` at seed 42,
committed as `docs/candidate_cohort_v1.csv` and read back as an Earth Engine
asset — and §3.1 states that Gate 1's bin counts are taken over those cohort
pixels. The protocol had never said which pixels were candidates, although
§3.10 and §3.11 both referred to a candidate frame.

Why: the export path committed in `2cf493a` built its grid with
`reduceToVectors` over a constant-valued mask, which returns connected
components rather than pixels — measured 2026-09-08 on a Bhadrak tile as one
cell against 774,673 rice pixels, i.e. ~570 arbitrary pixels for the whole
study. The same reading showed the per-(district, tile, season) loop would
have queued ~4,000 Earth Engine tasks; the cohort design makes it 189.

Full text, including the measurement, the 400-per-district rationale and two
in-place corrections to the 2026-09-07 entries, in
`analysis/decisions_log.md` under "2026-09-08 — Candidate cohort defined and
the per-tile grid retired ...".

## 2026-09-09 — DEV: post-freeze amendments part 1 — rice mask, roster, panel floor, cohort

Protocol_v1.md was frozen at `2cf493a` (2026-09-07). Under §5.3 the following amendments are recorded here rather than made silently. Full reasoning, measurements and sources are in `analysis/decisions_log.md` (2026-09-09); this entry is the cross-reference.

| § | Amendment | Reason |
|---|---|---|
| 1.1 | Named-cyclone table 6 → 7 events (Titli added); estimability column added | 2018 enters the panel; per-event estimability stated in advance rather than found during analysis |
| 1.1 | Exposure counts recomputed for 25 districts × 2017–2025 | roster and panel both changed |
| 1.1, 1.2 | Analysis floor 2019 → 2017; panel 2017–2025 | the 2019 floor was a Sentinel-2 collection-start artefact (DEV-001) and does not bind a radar substrate; measured S1 coverage supports 2017 and 2018 but not 2016 |
| 1.3 | Minimum-Kharif-rice criterion added; roster 27 → 25 | Nellore 1.3% and Prakasam 0.9% Kharif rice; §1.3's coastal rule selected rice-producing, not Kharif-rice-producing, districts |
| 3.5 | Primary mask RiceAtlas → RiceAtlas ∩ Chen et al. 2024 Kharif 2018 | the polygon-only mask failed `rice_mask_options.md` §2 requirement 2; measured purity 0.9–61.3%, mean 29.8% |
| 3.6 | Cohort v1 retired; cohort v2 defined on the new mask | ~7,578 of v1's 10,800 pixels were not Kharif rice, and v1 spans two districts the roster no longer contains |
| 3.8 A | Panel scope 27 districts × 2019–2025 → 25 × 2017–2025 | follows §1.1–1.3 |

**Not withdrawn.** DEV-001 (2026-06-15, Sentinel-2 L2A empty before 2018-12-18) remains correct as written. It ceases to govern the analysis floor only because the substrate changes; it still governs any Sentinel-2 use.

**Known-inconsistent until part 2.** §3.1 (Gate 1), §3.3 (SAR), §3.4 and §2 (MARC, H1/H2, H4), §3.10 (Lee bounds) and the §3 lead-in phenometric method remain as frozen at `2cf493a` and are known to require amendment. They are listed in `analysis/decisions_log.md` (2026-09-09). No coefficient, phenometric or table is computed from them in the interim.

## 2026-09-09 — DEV: post-freeze amendments part 2 — Sentinel-1 substrate, Gate 1, MARC/H1/H2, SAR section, Lee bounds, H4

Protocol_v1.md was frozen at `2cf493a` (2026-09-07). Under §5.3 the following
amendments are recorded here rather than made silently. This is the second and
final part of the 2026-09-09 revision; part 1 is the entry above. Full
reasoning, measurements and sources are in `analysis/decisions_log.md`
(2026-09-09, "Protocol revision part 2 of 2"); this entry is the
cross-reference.

| § | Amendment | Reason |
|---|---|---|
| 3 lead-in, 3.6 | Phenometric substrate Sentinel-2 NDVI → Sentinel-1 VH/VV ratio; per-orbit per-pixel normalisation; calibration on the 2017 baseline made mandatory | median 2 valid optical composites per pixel-season out of 55, DOY 170–290 nearly empty (part 1); a 6-parameter double-logistic is not fittable on that. VH/VV rather than VH because VH rises with local minima and VV falls up to 10 dB through tillering — neither is shaped for the fit |
| 3.1 | Gate 1 admission rule *N(b)* ≤ r·*N_peak* → *N(b)* ≥ r·*N_peak* | the frozen rule admitted sparse bins and rejected well-sampled ones; at *N_peak* = 100, r = 0.5 it admitted 10 observations and rejected 80 |
| 3.1 | r-values (0.75 / 0.50 / 0.50) withdrawn, to be re-derived on the untreated 2017 season | reasoned from optical cloud statistics under a rule pointing the other way; neither the numbers nor their justification transfers |
| 3.1 | Gate 1 no longer described as the headline contribution; four-criterion justification test added (fit quality, inter-seasonal stability, spatial coherence, orbit agreement) | under Sentinel-1, *N(b)* varies far less; whether the gate earns a place is settled empirically. No accuracy criterion is possible — see §3.4 |
| 3.3 | Repurposed from SAR falsification check to cyclone inundation-intensity variable `inundated_frac`, 3 dB VH drop criterion | the frozen check was calendrically unpassable (Fani's window ends 18 d from the nearest admissible SOS; Bulbul's 59 d) and, with the substrate now SAR, would compare a measurement against itself |
| 3.4 | MARC's 27.62 d / 28.32 d re-characterised as MARC-vs-RiceAtlas agreement at 0.5°, not field-validated pixel error | source states it cannot validate without ground truth; the frozen comparison set this study's RMSE-vs-MARC beside MARC's RMSE-vs-RiceAtlas |
| 3.4 | Explicit non-claim: no pixel-level accuracy is claimed or established | no field-observed dates exist for these districts in any panel season; established by search, recorded in the decisions log |
| 3.4 | Three-tier structure with internal consistency primary; HLS removed as pixel-level validation substrate, retained for post-monsoon EOS only | HLS is Landsat + Sentinel-2 and sits under the same monsoon cloud |
| 2 | H1, H2 rewritten as measurement-consistency claims; product agreement moved to H1c/H2c, reported never tested | follows §3.4; no accuracy hypothesis of any form is testable here |
| 2 | H4 event set 5 → 6 estimable cyclones; criterion four-of-five → five-of-six signs; the retired significance criterion removed | Titli enters with the 2017 floor, Fani gains its *k* = −1 reference from 2018; 6/32 ≈ 19% vs 7/64 ≈ 11% under coin-flip signs holds strictness roughly constant. The significance criterion was unmeetable with two treated clusters (MacKinnon & Webb 2018) |
| 3.10 | Lee (2009) trimming bounds **withdrawn**, not corrected | wrong group trimmed with a formula returning a negative proportion under the protocol's own monotonicity; and Lee's randomised two-arm derivation does not transfer to an observational DiD panel |
| 3.10 | Balanced-composition check promoted to primary robustness anchor; reporting rule and manuscript disclosure sentence rewritten | it holds composition fixed by construction rather than by assumption. The frozen rule read "Lee bounds include zero → direction supported", which is invalid |
| 3.10 3a | IPSW covariate list flagged as an open item under the Sentinel-1 substrate | cloud-frequency climatology is not the operative survival mechanism for radar; the replacement is deferred to a revision that states it, and is not substituted silently |

**In-place corrections made the same day** (recorded, not rewritten):

- §2 H4's closing sentence still read "four-of-five … about 19%" after the
  criterion earlier in the same bullet had been raised to five-of-six. Found on
  re-reading before this commit. No result had been reported under either
  wording.
- §3.10's reporting-language rule and manuscript-body disclosure sentence both
  carried dated correction notes for the withdrawn Lee bounds. No coefficient
  was ever computed under the superseded wording.

**New file.** `python/attrition_diagnostics.py` implements §3.10 items 1, 2, 3a
and 3c and §3.9's lead test; it does **not** implement item 3b, by decision.
numpy and pandas only. `--selftest` verifies its estimator against a
brute-force dummy-variable OLS before it is used on real data, and caught three
defects that would each have produced a plausible-looking wrong number — a
storm-name mismatch that would have reported Bulbul as "not estimable", a
non-converging logit, and rank-deficient designs reaching a pseudo-inverse.
All three are described in the decisions log.

**Code.** `gee/S2_QC_Ingest.js` v0.6.1 → v0.7.0 adds §4b and §9e (Sentinel-1
substrate and its 225-task export path). `CONFIG.enableS1Exports` is `false`;
nothing dispatches until it is set, and §9e refuses to run without a committed
cohort asset.

**Not withdrawn.** DEV-001 remains correct and still governs any Sentinel-2
use. Every part-1 amendment stands unchanged.

**Deliberately unset after this commit**, to be derived on the untreated 2017
baseline season and recorded in `analysis/decisions_log.md` before any treated
season is fitted: §3.1's r-values, §3.3's 3 dB criterion and window length,
§3's curve-parameter-to-date calibration, and H1/H2's consistency tolerances.

## 2026-09-09 — DEV: post-freeze amendments part 3 — Gate 2/Gate 3 units, smoother property, degenerate-variance rule

Third amendment set of 2026-09-09, recorded under §5.3. All three arise from
writing and testing `python/fit_phenometrics.py`, the stage between the
Sentinel-1 exports and §3.8. Full reasoning and measurements in
`analysis/decisions_log.md` (2026-09-09, "Protocol revision part 3").

| § | Amendment | Reason |
|---|---|---|
| 3.2 | Unit correction: the DOY bounds transfer to the Sentinel-1 substrate, the amplitude column does not; the three dB equivalents are derived on the untreated 2017 baseline, never defaulted | the criteria are in NDVI units and the index is now a backscatter ratio in dB; there is no principled conversion |
| 3.2 | The rise and decline criteria may be set separately | the VH/VV limbs are asymmetric — median 30-day rise +5.1 dB against a median decline of −4.3 dB — and a common threshold at the rise limb's 5th percentile rejected 36% of otherwise valid EOS values. Set equal, they reproduce the frozen table |
| 3.11 | Unit correction: the 0.15 RMSR threshold is in NDVI units and is re-derived on the 2017 baseline; the gate's structure is unchanged | as above |
| 3 lead-in | Measured property of the Whittaker step recorded: SOS ≈1 d early, EOS ≈2 d late, dispersion down 19% (SOS) and 27% (POS) | the step is mandated for comparability with Paper 1, so this is documentation, not a change. The level shift is common to all pixel-seasons and is differenced out: planted +8.0 d recovered as +7.73 d despite a −1.34 d level bias |
| 3.10 item 2 | A degenerate (non-positive) cluster-robust variance is recorded as an instance of the zero-treated-support rule: report "not estimable" with the point estimate and `n_score_clusters`, never a zero standard error | found in testing: a variance of −9.4e−18 printed as se 0.000 with a zero-width interval. §3 lead-in's "Gate 2 and Gate 3 apply unchanged" is corrected by dated notes in §3.2 and §3.11 rather than rewritten, because the structure it refers to does carry over |

**New file.** `python/fit_phenometrics.py` — Gate 1, dekadal aggregation,
eligibility, Whittaker/GCV, Beck double-logistic by a hand-written bounded
Levenberg–Marquardt, 20% amplitude crossings, Gates 2 and 3. numpy and pandas
only; `--selftest` runs nine checks against known answers and cross-checks the
optimiser against scipy when scipy is present. It emits every attempted
pixel-season, not only survivors. It has **no defaults** for r, the amplitude
thresholds, the peak level or the RMSR threshold, and refuses to run the gates
without them.

**Changed file.** `python/attrition_diagnostics.py` — non-positive
cluster-robust variances now yield NaN and a "not estimable" stratum instead of
a standard error of 0.000; new `n_score_clusters` column; two regression tests
added.

**Not withdrawn.** DEV-001 and every part-1 and part-2 amendment stand.
`gee/S2_QC_Ingest.js` is unchanged at v0.7.0.

**Still deliberately unset**, to be derived on the untreated 2017 baseline and
recorded in `analysis/decisions_log.md` before any treated season is fitted:
§3.1's r values, §3.2's two amplitude thresholds and peak level, §3.11's RMSR
threshold, §3.3's 3 dB criterion and window length, and §3's
curve-parameter-to-date calibration.

## 2026-09-11 — DEV: export header must be pinned explicitly (v0.7.1)

Recorded under §5.3. Full reasoning and the diagnostic history are in
`analysis/decisions_log.md` (2026-09-11).

| § | Amendment | Reason |
|---|---|---|
| 3.6 | The export must call `Export.table.toDrive` with an explicit `selectors` list matching the committed schema | Without it Earth Engine infers the CSV header from the leading features. The table emits bin 0 first, so a district-season whose earliest 5-day bins hold no acquisition yields a leading block of nulls, and the header is written without the band-derived columns — losing them for the whole file while the metadata columns survive, so the file looks complete. Measured: 97 of 225 Sentinel-1 files lost `VHVV_med` and `valid_obs_count`; all 128 intact files have data in bin 0, 128 of 128 |

**No threshold, window, gate, estimator, hypothesis or decision rule changes.**
Only the CSV header is affected; every computed value is identical.

**Code.** `gee/S2_QC_Ingest.js` v0.7.0 → v0.7.1. `selectors` added to §9e
(Sentinel-1) and §9c (Sentinel-2, retained as the §3.4 post-monsoon EOS
cross-check). Both lists verified programmatically against their table builders.

**Retrospective, recorded not rewritten.** The Sentinel-2 run of 2026-09-08
lost the science columns in 175 of 189 files, attributed at the time to a stale
pre-fix dispatch. This defect is the more likely cause: optical bins are empty
far more often than radar bins, so the leading-block-null condition would be met
almost always, which fits a 93% failure rate better than stale dispatch does.
The earlier entry stands as written; this note supersedes its explanation.

**Data status.** The 128 intact Sentinel-1 files are correct and are retained
unchanged. Only the 97 affected district-seasons are re-exported. The panel's
`cell_id` keys were verified identical across all nine seasons and an exact
match to committed cohort v2 in all 25 districts.

## 2026-09-12 — DEV: the double-logistic fails calibration; radar markers are read as features

Recorded under §5.3. Full reasoning in `analysis/decisions_log.md` (2026-09-12).

| § | Amendment | Reason |
|---|---|---|
| 3 lead-in | "Only the index changes, not the estimator" **withdrawn**; the Beck double-logistic is replaced on the radar path by feature extraction | VH/VV in transplanted rice is trough–rise–plateau–drop, not a bell (Phan et al. 2021: "remains stable until the end of its cycle"). Fitted peak pinned near DOY 326 at every window start tested, 56% convergence, 40% with no descending crossing |
| 3 lead-in | Three markers defined — trough, heading, harvest — and explicitly **not** named SOS/POS/EOS | the radar fall is drainage, not senescence; naming them as optical phenometrics would assert an equivalence that does not hold |
| 3.2 | The 2026-09-11 note claiming the DOY bounds fail under radar is **withdrawn** | it was written from fits now withdrawn. Read as features, all three markers land inside Paper 1's windows: 214.5 / 304.5 / 364.5 |
| 3.11 | Gate 3 does not apply to the radar path; screening passes to minimum rise and marker completeness | RMSR is a fitted-curve residual and there is no fit |
| 3.11 | Whittaker smoothing recorded as costing harvest identifiability, 85% → 60% | measured on the baseline; no effect on amplitude (3.33 vs 3.27 dB) |

**No threshold, window, gate bound, hypothesis or decision rule is loosened.**
§3.2's DOY bounds are carried over from Paper 1 unchanged. The change is to the
estimator, made on the untreated baseline before any treated season was marked.

**New file.** `python/extract_phenometrics_sar.py`, numpy and pandas only,
four self-test checks against a synthetic curve with markers placed by
construction.

**Still deliberately unset**, to be derived on the 2017 baseline and recorded
before any treated season is marked: the eligibility rule, the operative
minimum-rise threshold, and whether smoothing is retained on the radar path.

## 2026-09-12 (second entry) — DEV: radar parameters derived; nothing left unset

| § | Amendment | Reason |
|---|---|---|
| 3 lead-in | Smoothing OFF on the radar path | unsmoothed 88.7% three-marker completeness against smoothed 54.0%, both medians inside §3.2 |
| 3 lead-in | Minimum rise fixed at 5.32 dB | 5th percentile of the rise among the 2,554 baseline pixel-seasons whose markers all sit inside §3.2 |
| 3 lead-in | Retention rule fixed; baseline retention 24.3% recorded as a result | the retained set has median rise 8.50 dB and markers at DOY 214.5 / 284.5 / 334.5, the Odisha Sali calendar. The loss measures §3.5's 0.5 mask purity, not the method |

All three derived on the untreated 2017 baseline by rules stated before
computing, before any treated season was marked. **No threshold is loosened to
raise retention.** Raising §3.5's purity would raise retention and is
deliberately not done: the cohort is committed, and re-drawing it after seeing
which pixels survive would select the cohort on the outcome.

**Nothing on the radar path remains unset.**

> **Correction, 2026-09-12 (third entry).** The entry immediately above is
> superseded in three specific claims and left standing as the record of what
> was decided and why. (1) "Nothing on the radar path remains unset" was true of
> the crossing estimator and is no longer the operative statement: that
> estimator is now a robustness arm. (2) "All three markers land inside Paper
> 1's windows" rested on the MEDIAN of the crossing markers; at unit level 54%
> of troughs and 35% of headings sat exactly ON a §3.2 boundary, so the windows
> were binding, not satisfied. (3) The 5.32 dB minimum rise was derived as the
> 5th percentile of a reference set whose selectivity the boundary-binding
> inflated, and split-half reliability is FLAT in rise amplitude, so no absolute
> floor buys precision. See the third entry below.

## 2026-09-12 (third entry) — DEV: the estimator, the unit of analysis, and the screen

| § | Amendment | Reason |
|---|---|---|
| 3 lead-in | The **five-segment piecewise-linear season model (PLSM)** replaces the crossing rule as the primary estimator. `base → decline → dark phase → rise → plateau → fall → base`; the four breakpoints ARE the markers, so the 0.80 and 0.50 crossing fractions are removed, not re-tuned | split-half reliability on the untreated 2017 baseline: heading σ 35.3 → 26.2 d, harvest σ 40.9 → 25.2 d, median disagreement halved (30 → 20 d and 40 → 20 d), within-one-dekad agreement 0.24 → 0.41 and 0.21 → 0.39. Rule stated before the test: adopt the arm with the smaller split-half σ on the markers §3.8 uses |
| 3 lead-in | The leading **declining** segment is what distinguishes PLSM from a plain trapezoid | the series starts high (previous crop, pre-monsoon cover) and falls into the dark phase. A flat base splits the residual between the two: Kendrapara 2019 fitted base −7.56 dB against an observed −6.05 early and −9.50 at the real trough, rmse 1.02 dB, trough placed at DOY 304.5 when it is plainly 254.5. Median district-season rmse 0.397 → 0.316 dB |
| 3.8 | The **unit of analysis becomes the district-season.** The pixel panel is retained as the §3.10 input and as a robustness arm | per-pixel marker dates carry σ ≈ 18 d, measured two independent ways that agree (split-half resampling of disjoint 5-day bins; Monte Carlo at the measured 2.03 dB dekadal noise). The district-mean dekad has a sampling se of 0.122 dB and its breakpoints recover to ±1.3 d. Measured within-district dispersion of heading across the nine seasons is 7.8 d, so the year-to-year movement is signal by a factor of six over the measurement error — **the "is signal" inference is WITHDRAWN 2026-09-14 (fifth pass); ±1.3 d is simulated, not a matched empirical error assessment, so the ratio separates nothing** |
| 3.2 | **No phenometric calendar gate in the primary specification.** Breakpoints are searched over the whole 28-dekad grid under ordering and shape admissibility only | the windows bind at unit level (54% of troughs, 35% of headings on a boundary). Free the search and only 35% of troughs and 55% of headings remain inside §3.2, in a direction consistent across all three markers and all districts: the windows are 40–60 days too early for the radar season on this coast |
| 3.2 | The 2026-09-12 (second entry) claim that §3.2 transfers unchanged is **withdrawn**, and with it the withdrawal of the 2026-09-11 note | both rested on medians. The correct statement is that §3.2's windows describe Paper 1's optical substrate and do not describe the radar season |
| 3 lead-in | The absolute **5.32 dB minimum rise is withdrawn**; the primary screen is a per-pixel-season test that the fitted rise is positive | split-half reliability is FLAT in rise amplitude from 3 dB to 12 dB and flat in fit signal-to-noise from below 1 to above 3. No amplitude floor buys timing precision, so none is imposed. An absolute floor is retained as a **specification-curve** argument (`--min-rise-db`) so §3.8 reports across it |
| 3 lead-in | The rise screen uses a **selection-aware critical value**, tabulated by parametric bootstrap, not the nominal t | measured: on pure noise with no season at all, **29%** of series clear the nominal 5% one-sided value, because the fit chooses among thousands of breakpoint quadruples. The calibrated values are t95 = 2.94 (pixel grid, 4,322 designs) and 4.17 (free grid, 12,649 designs, AR(1) null at ρ = 0.25) against a nominal 1.71, and they hold the false-positive rate at 0.048 |
| 3 lead-in | The null used for that calibration is chosen by a **measurement**, not an assumption | fitted-residual lag-1 autocorrelation is −0.22 at pixel level (586 baseline pixel-seasons) and +0.21 at district level (25 baseline districts). Negative makes a spurious rise less likely, so the i.i.d. table is conservative at pixel level and is used there; positive cuts the other way, so the district fit uses the AR(1) table. ρ = 0.40 (t95 = 4.98) ships as the conservative arm |
| 3.1 | Gate 1's sampling-density rule is **not applied at pixel level** and **is applied to the district-mean curve** at 0.5 coverage | its purpose is optical: a sparse bin means few cloud-free looks. Sentinel-1 acquisition is an orbit schedule, not weather, and at pixel level the gate manufactures the only §3.11 ineligibility in the entire untreated baseline (minimum valid dekads 19 → 10). At district level the concern is real and different: a dekad carried by 6 of 400 pixels is a composition step, not phenology (Guntur 2017, DOY 214.5, −11.18 dB against −7.8 dB either side) |
| 3.10 3a | The IPSW covariate set is **closed** for the radar substrate: `obs_total`, `n_valid_dekads`, `dist_to_track_km`, `elevation_m`, `slope_deg`, `incidence_deg` | the frozen set was optical (`cloud_freq_clim`, `dist_to_track_km`, `elevation_m`); cloud is not the operative mechanism and the terrain quantity that drives VH/VV is local geometry. The last three come from a new **25-task** static export (`S1_STATIC_COVARIATES.js`), not 225, because they do not vary by season. Until it lands the estimate is labelled `ipsw_partial` and names what is missing |
| 3.10 3c | The balanced arm is **indexed by the storm's season only** — documented, not changed | it restricts to units retained in t_c−1 and t_c and regresses on the exposure class, so FANI and BULBUL, both 2019, return the same number twice. Not two confirmations |
| 3 lead-in | Marker names: `trough` is reported as **onset of canopy development**, not transplanting | a puddled flooded field and a dry bare pre-monsoon field are both radar-dark in VH/VV, so the dark phase runs from land preparation through early tillering as one stretch whose interior minimum is placed by noise. The lag from transplanting is not resolvable in this data and is not claimed |

**Nothing is loosened to raise sample.** Two changes raise it (freeing the
windows, withdrawing the amplitude floor) and three lower it (the calibrated
critical value, district-level Gate 1, the four-breakpoint requirement); the net
at district level is 208 of 225 estimable and at pixel level 35.3%. Every
parameter was derived on the untreated 2017 baseline or by Monte Carlo under a
null, before any treated season was read.

**A finding that belongs to Paper 1.** Paper 1's Gate B deleted nine of ten
treated post-period district-years, every one for exceeding its 240-DOY SOS
ceiling. The radar puts the end of the dark phase at DOY 245–265 on this coast.
A ceiling at 240 sat below the true onset and therefore deleted precisely the
district-years it was meant to bound. The missing treated support in Paper 1 is
a mis-specified window, not attrition.

> **WITHDRAWN 2026-09-14 (eighth pass).** The entry stands as the dated record; this is the
> note against it. **This is a cross-sensor construct-identity claim and Paper 2 cannot make
> it.** Paper 1's optical calendar bounds do not align with Paper 2's radar breakpoint distribution and would censor many radar estimates if transferred across sensors. This demonstrates **non-transferability between these different measurands**. It does **not** establish that Paper 1's optical SOS bound was mis-specified, identify a true agronomic onset, or reinterpret Paper 1's support loss. Those questions require analysis of Paper 1's own optical measurements or an independent field reference. Paper 2's `t1` is an onset of canopy development in a VH/VV
> trajectory, not an optical SOS, and this study holds no field reference against which
> either could be judged.

**An open item, named rather than buried.** The exposure catalogue's
`timing_class` labels are Paper 1's and do not describe when a storm lands
relative to the radar-measured season. Measured: the 21 severe `harvest_window`
rows fall in October (15), November (2) and December (4), while radar heading is
10 November and harvest 19 January — so that class is mostly a **late-vegetative
/ pre-heading** exposure, not a harvest one. The frozen §3.8 classes are kept as
the headline; re-classifying each storm against the district's BASELINE markers
(never the same season's fitted markers, which the storm may move) is specified
as the next robustness arm and is not run here.

**New and changed files.** `python/extract_phenometrics_sar.py` (PLSM, the
calibrated screen, both panels, nine PLSM self-test checks);
`python/calibrate_plsm_null.py` and the two tables it writes;
`python/merge_static_covariates.py`; `gee/S1_STATIC_COVARIATES.js`;
`python/attrition_diagnostics.py` (radar marker names, the closed IPSW
declaration, `--level district`, a district-name resolution check that refuses
rather than silently coding a district as unexposed).

## 2026-09-13 — DEV: exposure re-classified against the measured season (robustness arm)

The open item named at the end of the 2026-09-12 (third entry) is closed. It was
named there as "specified as the next robustness arm and is not run here"; it is
now run, and the frozen §3.8 classes remain the headline.

| § | Amendment | Reason |
|---|---|---|
| 3.8 | A **robustness arm** is added in which severe exposure is classified against each district's **baseline markers** rather than the catalogue's `timing_class`. Three phases, reported alongside the frozen classes and never instead of them: `S_phase_pre_window` (storm before DOY 150), `S_phase_rise` (window opening to baseline heading), `S_phase_post_heading` | measured: of the 21 severe rows labelled `harvest_window`, **14 fall in the rise phase**, 4 in the plateau and 3 after harvest. None is a harvest exposure in the sense the label asserts. The 31 `pre_season` rows are all before DOY 150, so that label is correct and unchanged |
| 3.8 | The baseline markers are the mean over each district's district-seasons with **no catalogued exposure of any severity** — never the markers of the season being classified | classifying a storm on the markers of the season it hit would move the class with the effect and define the estimate in terms of its own outcome. Every district has a baseline from 2 to 7 unexposed estimable seasons (median 6) |
| 3.8 | The phase split was fixed by a rule stated before any coefficient was seen: collapse toward the heading boundary until every retained phase carries ≥ 3 treated clusters; a phase still short of three is reported not estimable, never as a null | raw counts were pre_window 17, rise 14, plateau 4, post_harvest 2. post_harvest alone is below three, so plateau, fall and post_harvest collapse into one post-heading phase. Final counts as the estimator sees them: 17 / 14 / 4, all estimable |
| 3.10 | Treated-cluster counts are reported on the **final** indicator table, restricted to roster districts and panel seasons, not on the raw catalogue | the raw count credits clusters the regression never receives: VARDAH 2016 is outside the panel window and MICHAUNG's post-harvest rows are in non-roster districts (Nellore, Prakasam). The first version of this module printed 3 for post_heading where the estimator sees 4 |

**What the arm shows, and it is a confirmation rather than a correction.** The
heading effect survives re-classification at almost identical magnitude and
attaches to the physically coherent phase:

    frozen    heading : S_harvest_window   +7.11 d  p_WCB 0.0025  CI [+2.38, +11.69]
    measured  heading : S_phase_rise       +7.37 d  p_WCB 0.0154  CI [+1.34, +13.26]

A severe storm between a district's baseline canopy-development onset and its
baseline heading delays heading by about a week. Under the frozen label the same
effect read as a harvest-window storm moving an event that precedes it, which was
the causal awkwardness the re-classification was written to test. Plateau
duration shortens correspondingly (−8.99 d, p_WCB 0.042) while drainage onset
does not move (−1.61 d, p_WCB 0.53). The pre-window results are unchanged, as
they must be, since that class is the same 29 of 31 rows: harvest −10.32 d
(p_WCB 0.033), grain-fill −11.96 d (0.056), plateau level +0.200 dB (0.014).

**And the arm weakens the attrition problem rather than adding to it.** §3.10's
item 1 on the phase classification gives `S_phase_rise` −0.145 on district
estimability at p_WCB **0.083** — not significant at 5% — against the frozen
`harvest_window`'s −0.126 at p_WCB **0.040**. Part of the apparent
attrition-treatment correlation was the mis-specified label, not selection.

**Parallel trends.** 33 lead tests in the arm; 3 fall below 0.10 and none below
0.05, against 3.3 expected below 0.10 by chance at 33 tests. All three are on
`Slead_phase_pre_window` (heading 0.0995, veg_days 0.081, fall_db 0.066). The
rise-phase heading result, which is the arm's finding, is not among them. The
pre-window heading lead of +4.27 d is large relative to that class's own null
headline of +1.64 d and is reported as such rather than dismissed on its p value.

**New and changed files.** `python/classify_exposure_phase.py` (new);
`python/attrition_diagnostics.py` (a `--phase-exposure` option; the arm is off
unless that file is supplied, so the frozen specification is what runs by
default).

## 2026-09-13 (second entry) — CORRECTION: a split-half number was asserted, not measured

**What was wrong.** The 2026-09-12 (third entry) above, the same table in
`analysis/decisions_log.md`, and the docstring of
`python/extract_phenometrics_sar.py` all present a three-column split-half table
in which the trapezoid and PLSM columns carry **identical** figures (trough 24.5,
heading 26.2, harvest 25.2 days). Those are the TRAPEZOID's measured values. PLSM's
split-half reliability was never measured; its column was filled from the
trapezoid's on the assumption that a shape model with one more segment would
behave the same way. That is an assertion dressed as a measurement, and it is the
one thing this project's logs exist to prevent.

**Measured now**, same protocol — one series from the first 5-day bin of every
dekad, one from the second, disjoint observations on the same grid with the same
orbit mix, σ of a single measurement = sd(difference)/√2, untreated 2017 baseline:

| marker | crossings | trapezoid | PLSM (measured) |
|---|---|---|---|
| trough σ / within 1 dekad | 21.9 d / .35 | 24.5 d / .55 | **33.6 d / .33** |
| heading σ / within 1 dekad | 35.3 d / .24 | 26.2 d / .41 | **23.4 d / .38** |
| drainage σ / within 1 dekad | — | 28.0 d / .34 | **22.5 d / .40** |
| harvest σ / within 1 dekad | 40.9 d / .21 | 25.2 d / .39 | **27.8 d / .32** |
| testable pixel-seasons | 3,360 | 2,553 | 3,021 |

The three columns are not on the same pixel set — each estimator admits a
different set of pixel-seasons in both halves — and that is reported rather than
papered over.

**What this changes, and what it does not.** PLSM beats the crossing rule on
heading (35.3 → 23.4) and harvest (40.9 → 27.8), which is the comparison the
selection rule was written for. Against the **trapezoid** it is better on heading
and drainage and **worse on trough** (24.5 → 33.6) and marginally on harvest. So
the stated rule — "adopt the arm with the smaller split-half σ on the markers §3.8
uses" — does not by itself settle trapezoid against PLSM, and the earlier entry
should not have implied it did.

**The decision stands, on the evidence that actually decided it, now named
correctly.** PLSM was adopted over the trapezoid because the trapezoid is the
wrong SHAPE, not because it is noisier: its flat pre-season base cannot represent
a series that starts high and declines into the dark phase, and on such a series
it mis-places the trough by weeks (Kendrapara 2019, trough at DOY 304.5 against an
observed 254.5, fit rmse 1.02 dB). A 50-day bias is not traded against a 9-day
difference in σ. The independent evidence that the fifth segment is right is fit
adequacy at the primary unit: median district-season rmse 0.397 → 0.316 dB. That
is the argument, and the earlier entry substituted a fabricated variance
comparison for it.

**A consequence worth stating.** Under PLSM the **trough is the least reliable of
the four markers** (σ 33.6 d, within one dekad .33). That is consistent with what
the module already says about it — a puddled flooded field and a dry bare
pre-monsoon field are both radar-dark, so the dark phase is one long low whose
interior break is weakly identified — and it is the reason `trough` and the
durations that depend on it (`veg_days`, `season_days`) are the weakest outcomes
in §3.8. Per-pixel `rise_db` carries σ 2.13 dB against a median of 6.1 dB.

None of this touches the district-season panel, which is the primary unit: there
the Monte Carlo at the measured 0.122 dB noise recovers every breakpoint within
1.3 days, and that number was measured, not assumed, and is checked by
`--selftest`.

**Changed files.** `python/extract_phenometrics_sar.py` (the docstring table);
`analysis/decisions_log.md`, `analysis/deviation_log.md`;
`results/splithalf_reliability.csv` (new — the measured table, so the claim can be
checked against a file rather than a sentence).

## 2026-09-13 (third entry) — CORRECTION: the phase accounting was quoted from a superseded probe

**What was wrong.** The 2026-09-13 first entry above, the matching section in
`analysis/decisions_log.md`, the §3.8 note in `docs/Protocol_v1.md` and the
commit message of `d12eeaa` all describe the severe `harvest_window` rows as
"14 in the rise phase, **four in the plateau** and **three after harvest**", and
list the per-storm classification with `plateau` and `post_harvest` labels. Those
labels come from a six-phase exploratory probe run before the module existed.
`python/classify_exposure_phase.py` as committed emits **three** phases, and its
actual output is:

| `timing_class` | rise | post_heading | unclassifiable | total |
|---|---|---|---|---|
| harvest_window | **14** | **4** | **3** | 21 |
| pre_season | 0 | 0 (29 pre_window) | 2 | 31 |

**The headline number is unchanged and correct: 14 of the 21 severe
`harvest_window` rows are rise-phase exposures.** What was mis-stated is the
other seven. They are four **post-heading** rows —

    North 24 Parganas 2019  BULBUL:MATMO  DOY 313 vs baseline heading 306.5
    Guntur            2023  MICHAUNG      DOY 339 vs 327.8
    East Godavari     2025  MONTHA        DOY 301 vs 286.2
    West Godavari     2025  MONTHA        DOY 301 vs 261.2

— and three **unclassifiable** rows, which are unclassifiable because they are in
catalogue districts outside the 25-district panel roster and therefore have no
baseline markers: Nellore 2016 (VARDAH), Nellore 2023 and Prakasam 2023
(MICHAUNG). Calling those three "after harvest" asserted a classification that
was never computed for them. Two `pre_season` rows are unclassifiable for the
same reason (Kolkata 2019 FANI, Kolkata 2020 AMPHAN), which the earlier entry did
not mention at all.

**Consequence for the denominator.** Both "14 of 21" and "14 of 18" are true and
mean different things — 21 is every severe `harvest_window` row in the catalogue,
18 is the classifiable subset, i.e. those in roster districts. The figures and
the text now say **"14 of the 18 classifiable"** and give 21 as the catalogue
total in the same sentence, so the two can never be read as disagreeing.

Nothing estimated changes: the three unclassifiable rows and the two
unclassifiable `pre_season` rows contribute no indicator to any regression, which
is what the module's self-test asserts and what `d12eeaa`'s own cluster counts
(17 / 14 / 4) already reflect.

**Changed files.** `analysis/decisions_log.md`, `analysis/deviation_log.md`,
`docs/Protocol_v1.md` §3.8.

## 2026-09-13 (fourth entry) — CORRECTION: the static-covariate export would have matched nothing

`gee/S1_STATIC_COVARIATES.js`, committed at `be4079e`, carried three defects in
its CONFIG, all of the same kind: values written from the pattern of
`gee/S2_QC_Ingest.js` rather than read out of it. Every one of the 25 districts
would have filtered zero features and exported an empty table.

| key | committed at be4079e | actual, from S2_QC_Ingest v0.7.1 |
|---|---|---|
| `riceAtlasAssetPath['West Bengal']` | `projects/…/gadm41_IND_2_WestBengal` | `users/supranab/RiceAtlas_WB` |
| `riceAtlasAssetPath['Odisha']` | `projects/…/gadm41_IND_2_Odisha` | `projects/durable-pulsar-486209-b5/assets/RiceAtlas_OD` |
| `riceAtlasAssetPath['Andhra Pradesh']` | `projects/…/gadm41_IND_2_AndhraPradesh` | `projects/durable-pulsar-486209-b5/assets/RiceAtlas_AP_coastal` |
| `filterField`, all three states | `NAME_2` | WB `SUB_REGION`, OD and AP `GADM_NAME` |
| `WB_NAME_MAP` | absent | `Purba Medinipur → East Midnapore`, `Pashchim Medinipur → West Midnapore` |

The third is the subtle one: the West Bengal legacy asset has no `GADM_NAME`
column and transliterates the two Midnapore districts differently, so even with
the right asset and the right field those two would have matched nothing while
the other four WB districts matched. That is a *partial* failure, which is worse
than a total one — it would have produced a covariate missing for exactly two
districts, which is not missing at random.

**Guards added, because "it would have been obvious" is not a guard.** The script
now prints `[DISTRICT NOT FOUND]` with the asset, field and value it filtered on;
prints `[NO COHORT POINTS]` when a district matches geometry but no cohort
points; prints the cohort-point count beside every task; and ends with a loud
`*** STOP ***` whenever the task count is not 25, saying in the message why a
short export is worse than no export. None of these existed before.

Nothing estimated changes — the export had not been run. §3.10 item 3a remains
`ipsw_partial` until it is.

**Changed files.** `gee/S1_STATIC_COVARIATES.js`, `analysis/deviation_log.md`.

## 2026-09-13 (fifth entry) — §3.10 item 3a CLOSED; the IPSW is estimable at pixel level and not at district level

The 25-task static export ran clean: 25 files, 400 cohort points each, 10,000
rows, every declared column present and non-null, and a join to both panels with
**zero unmatched rows**. Values are physically coherent — elevation median 17 m
with the deltaic districts (Kendrapara, North and South 24 Parganas) at 2–3 m and
Gajapati, the Eastern Ghats district, at 320 m; slope median 2.1°; Sentinel-1
incidence 32.1–43.7°, median 38.1°, from a median of 776 scenes per cell.

| § | Amendment | Reason |
|---|---|---|
| 3.10 3a | The pre-declared IPSW is **estimated in full at pixel level**: all six declared covariates, 90,000 rows, 39 parameters, **813.9 events per parameter**, converged, calibration \|mean(p̂) − mean(retained)\| = 2.8e−16. The open item of 2026-09-09 is closed, and the estimate is labelled `ipsw`, not `ipsw_partial` | every declared covariate is present and varies within district; nothing is dropped or substituted |
| 3.10 3a | The IPSW is **not estimable at district level**, and is now reported as not estimable rather than as weights pinned at the clip | two distinct reasons, both reported by name. First, `elevation_m`, `slope_deg` and `incidence_deg` are constant within a district by construction and are absorbed entirely by the district fixed effects. Second, and decisively, **20 of the 25 districts have every one of their nine seasons estimable**, so their dummies predict retention perfectly. Dropping perfectly-predicting fixed-effect levels leaves 30 of 225 rows and 13 parameters — **1.0 events per parameter** — and the logit does not converge |
| 3.10 3a | A logit that does not converge now **discards its weights and produces no `ipsw` rows**, instead of reporting them under a WARNING line | a fit pinned at the clip looks like a result and is not one, and a warning printed under a number is read by nobody. `python/attrition_diagnostics.py` prints the row count, parameter count and events per parameter, and names §3.10 3c's balanced-composition check as carrying the robustness role — which is what the protocol's own safeguard note already assigns it |

**What the IPSW buys, which is reassurance rather than a different answer.** At
pixel level every headline coefficient moves by less than one standard error
when the weights are applied:

    trough  : S_harvest_window   +4.77 -> +3.44 d   (p 0.001 -> 0.014)
    heading : S_harvest_window   +1.19 -> +1.00 d   (p 0.053 -> 0.049)
    harvest : S_pre_season       -2.23 -> -2.29 d   (p 0.022 -> 0.025)
    plateau_db : S_pre_season    +0.131 -> +0.150 dB (p 0.050 -> 0.069)

So the pixel-level attrition is real and detectable (`class:pre_season` −0.053 on
retention, p_WCB 0.001) but does not materially bias the estimates once corrected
for. Weight behaviour is benign: median 3.16, 99th percentile 18.9, only **23 of
90,000 rows** hit the 0.01 clip, the top 1% of units hold 9.0% of total weight,
and the Kish effective sample size is 41,236 of 90,000.

**The finding the export actually bought.** The selection model says pixel
retention is governed by **terrain and viewing geometry, not by exposure**.
Log-odds of retention: `slope_deg` −0.0705, `incidence_deg` +0.1024,
`elevation_m` −0.0014 per metre, against `dist_to_track_km` **−0.0001**, which is
indistinguishable from zero. Unconditionally, retention falls monotonically:

    elevation  0-10 m 0.431 | 10-50 0.379 | 50-150 0.250 | 150-300 0.167 | >300 0.169
    slope      <1°   0.389 | 1-2°  0.389 | 2-4°   0.355 | 4-8°    0.246 | >8°  0.135

The 6.5% of the cohort above 300 m or steeper than 8° retains at 0.170 against
0.365 for the rest. **The screen is rejecting terrain that cannot be paddy.**
That converts the 35.3% pixel retention from a weakness into a measurement of
§3.5's 0.5 mask purity, and it is a statement about time-invariant pixel
characteristics, which fixed effects absorb — not about exposure. New figure 7
plots it.

**Parallel trends, 55 lead tests at each level.** District: none below 0.05, four
below 0.10 against 5.5 expected by chance. Pixel: two below 0.05, and they are
the same outcome in both arms — `fall_db` under pre-season exposure, p_WCB 0.001
in the frozen arm and 0.001 in the phase arm. **`fall_db` under pre-season
exposure is reported as not causal at pixel level.** It is not one of the
headline findings, and the district-level `fall_db` lead is null.

**Changed files.** `python/attrition_diagnostics.py` (fixed-effect absorption
screening, separation handling, refusal on non-convergence);
`python/make_figures.py` (figure 7); `results/s1_static_covariates.csv`,
`results/retention_by_terrain.csv`, `results/phen_panel_district_season_static.csv`,
`results/Table_SX_AttritionDiagnostic_final_district.csv`,
`results/Table_SX_AttritionDiagnostic_final_pixel.csv` and the two run logs (new);
`figures/fig7_terrain_retention.*` (new); `docs/Protocol_v1.md` §3.10.

---

## 2026-09-13 (sixth entry) — DEV: the exposure design fails §3.9's own placebo and lead test; §3.8's coefficients are withdrawn as causal effects

### 1. What changed

Three things, all forced by measurement on the corrected retained-only sample:

**(a) The primary outcome family is written down as four tests.** §4 and §2's H3
already fixed it; it had never been stated as a count, and 22 coefficients were
being read as though all were tests. The family is β_pre on SOS, peak and EOS, and
β_harv on EOS. H3 conjoins all four, so H3 needs no multiplicity correction;
individual family members are read at Bonferroni 0.05/4 = 0.0125. β_harv on peak
— the cell §4 explicitly leaves unsigned — is exploratory, as are the duration and
amplitude outcomes, δ and μ.

**(b) §3.9's timing placebo and lead test are recorded as FAILED.** β_harv on SOS
= +7.438 d, p_WCB 0.0008 at pixel level (9,999 replications), surviving both the
lead adjustment (+7.106 d, p 0.0006) and IPSW (+5.955 d, p 0.0080). λ_harv is
p_WCB 0.0024 on peak and 0.0702 on SOS, both under §3.9's own 0.10 bar.

**(c) No §3.8 A or §3.8 B coefficient is reported as a causal effect of cyclone
exposure on rice phenology.** The measured quantity is renamed for what it is: the
displacement of a fitted radar-trajectory breakpoint. §3.8's estimator,
clustering, bootstrap and reporting rules are untouched — what changes is what the
output is called and what may be concluded from it.

A new required output, `python/censoring_test.py`, measures why the checks fail.

### 2. Why

§3.9 states the consequence of each failure itself, before any of this was
estimated: a non-null placebo "indicates selection or mis-specification, not a
cyclone effect", and a non-null lead flags "that class's β as descriptive only".
Both conditions are met at pixel level. Applying them is not a new judgement.

The district column is **not** a contrary reading. Its point estimates agree with
pixel level in sign and rough magnitude at every cell (+5.001 d placebo, −2.654 d
λ on peak) and are all non-significant on 208 unit-seasons in 25 clusters. §3.10's
MacKinnon–Webb rule — a null with too little treated support is uninformative —
applies to the design's self-tests as it does to its estimates. Treating the
district column as a placebo pass would be reading absence of power as absence of
effect, which is the single error this project has most consistently refused.

The mechanism is measured, not assumed. The trough was fitted three ways on the
same 18,174 pixel-seasons: the full five-segment PLSM on 28 dekads; a reduced
one-breakpoint V-shape on 28 dekads; and the same reduced model on dekads 0–12
(DOY 154.5–274.5), a window earlier than every severe harvest-window landfall in
the panel, so containing no post-storm observation.

    (1) five segments, 28 dekads      +4.941 d   se 1.592   p_WCB 0.0068
    (2) one breakpoint, 28 dekads     -2.388 d   se 2.318   p_WCB 0.3108
    (3) one breakpoint, dekads 0–12   +1.158 d   se 0.947   p_WCB 0.2545
    paired (1)−(3), same rows         +3.782 d   se 1.320   p_WCB 0.0065
    paired (1)−(2), same rows         +7.329 d   se 1.867   p_WCB 0.0027

Arm (3) has the smaller standard error and finds nothing, so this is not a power
failure; the paired rows make the comparison immune to the common sample's
composition. PLSM picks the breakpoint quadruple minimising weighted RSS across
all 28 dekads with the four levels profiled out, so a late-season change in
backscatter alters the levels, alters which quadruple wins, and moves t1 months
upstream of the change. On a synthetic series, subtracting 4 dB from only the
post-window dekads moves the full-window trough **20 days** while the censored fit
cannot move — in the script's self-test, so it runs every time.

Limits, stated with the finding: arm (2) keeps all 28 dekads and still passes, so
the post-landfall window is not the sole cause and this design cannot rank the two
interventions; the reduced model is a diagnostic instrument, not a replacement
estimator (it places the trough 13.67 d earlier, r = +0.544); the district arm
(100 common rows, all p > 0.43) is uninformative either way.

### 3. Sections of `docs/Protocol_v1.md` affected

New §4.1 (the full amendment, with the four-test family, both failures, the
censoring test and the per-hypothesis impact). Dated pointer notes appended to §2,
§3.9 and §4. §3 lead-in and §3.8 are affected in naming only — the estimator is
unchanged. §5.2's Results ordering changes: the falsifiability checks are reported
before any coefficient.

### 4. New commitment

1. §3.8's outputs are named **radar-trajectory breakpoint displacements** in every
   table, figure and sentence, and no causal phenological claim is made from them.
2. The timing placebo and the lead test are **primary results**, reported before
   any coefficient.
3. `python/censoring_test.py` is a required output, with its synthetic
   demonstration and its stated limits.
4. §3.9's 2,000 spatial permutations and the r-value grid are still to be run, now
   as diagnostics of a design known to fail its placebo rather than as robustness
   checks on a finding.
5. No manuscript Results or Discussion text is written until the above is in the
   repository — unchanged from the standing instruction.

### 5. Per-hypothesis impact

- **H1 (measurement consistency, transplanting).** No impact. It is a claim about
  agreement between independent relative orbits and about within-pixel versus
  between-pixel dispersion, and contains no causal claim about cyclones. Live;
  blocked on the per-orbit export.
- **H2 (measurement consistency, harvest).** No impact, same reason. Live; blocked
  on the per-orbit export.
- **H3.** **NOT MET, 0 of 4, at both levels.** β_pre on EOS is significant with the
  wrong sign at both (−10.18 d, p 0.044 district; −3.35 d, p 0.008 pixel). Beyond
  not being met, H3 is **not testable in this design**: the class whose β it tests
  fails the design's own placebo and lead checks.
- **H4.** **NOT MET, 2 of 6** sign agreements against a 5-of-6 criterion; pooled β₀
  on EOS −13.04 d, p_WCB 0.0034, opposite the predicted sign for all six. Same
  construct-validity limit as H3.
- **H5.** Unchanged — already withdrawn (MODIS not obtained).
- **Objective 4 as a causal question** is **withdrawn** as answerable by this
  design and this instrument, and replaced by what was measured: a quantified
  account of why a radar-breakpoint exposure design of this form does not identify
  a phenological response, plus the diagnostic that demonstrates it.

### Changed files

`python/censoring_test.py` (new); `python/placebo_check.py` (new);
`python/attrition_diagnostics.py` (`load_panel` extracted so the focused scripts
cannot drift from the driver's sample definition; `--resume` with a run key and a
recomputation-based provenance check; the §3.10 3c balanced arm made opt-in);
`docs/Protocol_v1.md` (§4.1 and three pointer notes);
`analysis/decisions_log.md` (2026-09-13 sixth and seventh entries);
`results/s310_v2_district/`, `results/s310_v2_pixel/`,
`results/censoring_test/`, `results/placebo_check.log` (new).

---

## 2026-09-13 (seventh entry) — CORRECTION to the sixth: arm (3) of the censoring test is ceiling-limited

**What changed.** The sixth entry, written the same day, cited arm (3) of the
censoring test — the reduced model on dekads 0–12 — as primary evidence and argued
from its smaller standard error that its null was not a power failure. Arm (3)
cannot place a trough later than **DOY 254.5** (its window is dekads 0–12 with a
two-dekad minimum segment at each end), while the full PLSM places troughs on the
same rows out to **DOY 304.5**, and **28.7% of common-sample rows sit exactly on
that ceiling**. Arm (3)'s null is attenuated by construction for any late trough,
and the standard-error argument does not repair it: the estimator cannot express
the alternative it is being credited with rejecting. That argument is withdrawn.

**Why it does not change the finding.** The placebo failure never depended on the
censoring test — β_harv on SOS is +7.438 d, p_WCB 0.0008 on all retained rows
against a §4-declared zero, and §3.9 states the consequence itself. The mechanism
rests on **arm (2)**, which keeps all 28 dekads, has no ceiling (its breakpoint can
land out to DOY 404.5), returns −2.388 d with CI [−7.26, +2.45] excluding arm (1)'s
+4.941 d, and whose **paired difference against arm (1) on the same rows is
+7.329 d, p_WCB 0.0027**. That establishes the response to exposure is
estimator-dependent without requiring either measurement to be ranked better than
the other, which is why it is now the load-bearing result.

A ceiling-free row restriction was added and is reported, but it conditions on the
dependent variable and is therefore **descriptive only**, labelled as such in the
output and in the table's `specification` field. It shows that the failure is
absent among early-trough rows and carried by rows whose five-segment fit placed
t1 unusually late — the signature the mechanism predicts.

**Sections affected.** `docs/Protocol_v1.md` §4.1.4 — a dated correction note is
appended there rather than rewriting the subsection.

**New commitment.** Arm (3) is reported only with its ceiling and the 28.7% figure
attached. Arm (2) and the (1)−(2) paired test are the cited evidence for the
mechanism.

**Per-hypothesis impact.** None. H3 and H4 remain NOT MET on the grounds recorded
in the sixth entry, which rest on the placebo and lead tests rather than on the
censoring test.

**Changed files.** `python/censoring_test.py`; `analysis/decisions_log.md`
(2026-09-13 eighth entry); `docs/Protocol_v1.md` (§4.1.4 correction note);
`results/censoring_test/Table_SX_CensoringTest*.csv` and run logs (regenerated).

---

## 2026-09-13 (eighth entry) — CORRECTION to the sixth: the placebo is rejected in the robustness arm, not the declared headline

**What changed.** The sixth entry described §3.9's timing placebo as failing
without distinguishing the declared headline from the robustness arm. §3.8's
"Level of estimation (2026-09-12, third entry)" puts the headline TWFE on the
**district-season panel** and the pixel panel is "reported as a robustness arm and
… the input to §3.10". Corrected statement: **the placebo is rejected in the
robustness arm (β_harv on SOS = +7.438 d, p_WCB 0.0008) and is uninformative in
the declared headline (+5.001 d, p_WCB 0.1102, CI [−1.04, +11.25])**.

**Why the finding stands.** The estimate is large and positive at both levels, and
a storm landing three to four months after transplanting cannot move the
transplanting date by five days any more than by seven. The district interval
contains the pixel estimate, so it cannot resolve the question rather than
answering it in the design's favour — and §3.10's own MacKinnon–Webb rule forbids
reading an underpowered null as a pass. The pixel arm **is** the §3.10 input, so
the attrition diagnostic, the IPSW weights and the balanced-composition check all
rest on the arm whose placebo is rejected. H3 remains 0 of 4 on both panels.

**Also recorded: the estimator reproduces exactly.** Checked against explicit
dummy columns with statsmodels OLS and statsmodels' cluster-robust covariance —
no shared code — the district-panel coefficient and analytic standard error agree
to four decimals (+5.0010 d, se 3.1035). A sparse pixel-level check initially
appeared to disagree (+7.7130 d); the cause was that it absorbed cell_id × year,
which §3.8 line 12 **deliberately excludes**, and not an error in `twfe`. Three
solvers agree to the last digit within each specification. The placebo failure is
therefore robust to the fixed-effect choice: +7.438 d declared, +7.713 d with
pixel FE.

**Sections affected.** `docs/Protocol_v1.md` §4.1.2 — dated correction note
appended, not rewritten.

**New commitment.** Every statement of the placebo result names the arm it comes
from. The phrase "fails at headline level" is not used.

**Per-hypothesis impact.** None. H3 and H4 remain NOT MET on the grounds recorded
in the sixth entry.

**Changed files.** `docs/Protocol_v1.md` (§4.1.2 correction note);
`analysis/decisions_log.md` (2026-09-13 ninth entry).

---

## 2026-09-13 (ninth entry) — DEV: §3.9's permutation test run; permutation p-values become the headline inference for harvest-window coefficients

### 1. What changed

§3.9's 2,000-permutation spatial placebo, declared and never run, has been run
(`python/permutation_test.py`). Two changes follow.

**(a) Inference rule.** §3.8 A declares the wild cluster bootstrap as "the
headline inference". The permutation test measures it to be **anti-conservative
for harvest-window exposure**: the permutation 95th percentile of |t| is 2.14 to
4.09 there, against 1.25 to 1.97 for the pre-season arm and 1.96 nominal. **The
permutation p-value becomes the headline inference for every harvest-window
coefficient, with p_WCB reported beside it.** Unchanged for the pre-season arm.

**(b) Three p-values restated, one strengthened.**

    cell                                 p_WCB    p_perm
    beta_pre  on EOS                     0.0080   0.0005   (stronger)
    beta_harv on SOS  (SS3.9 placebo)    0.0008   0.0395
    beta_harv on peak (exploratory)      0.0430   0.1774   (now null)
    censoring (1)-(3) paired             0.0065   0.0340
    censoring (1)-(2) paired             0.0027   0.0420

District arm: beta_pre on EOS 0.0075; placebo 0.3068; beta_harv on peak 0.0720.

### 2. Why

The test was declared, and a reviewer would ask for it. It also adjudicated a
live competing explanation for the placebo failure — that a spatially and
temporally clustered exposure variable (17 of 18 Odisha and West Bengal roster
districts inside Fani's 48-kt footprint) plus spatially correlated phenology
could produce an "impossible" coefficient without any estimator problem. Both
possible outcomes were named in the script docstring before the run.

The answer is that the clustering account is **partly right and does not displace
the estimator account**. Relabelling districts does not reproduce |t| ≈ 4.2 more
than 4% of the time, so the placebo coefficient is not a generic consequence of
spatial clustering; but the reference distribution is wide enough that p_WCB
0.0008 was never credible. Severe harvest-window exposure is six adjacent Odisha
and Andhra districts in one season (Titli 2018), six adjacent Odisha districts in
another (Dana 2024), two adjacent West Bengal districts in a third (Bulbul 2019) —
25 nominal clusters, far fewer effective ones for that indicator.

§3.9's reading of "exposure HISTORIES are re-assigned" is implemented as a
relabelling of districts within a state carrying each district's whole 2017–2025
history, not an independent per-season shuffle. That preserves each season's
exposed-district count exactly, as §3.9 requires (verified on ten draws in the
self-test), and preserves the temporal autocorrelation the lag and lead terms
depend on.

### 3. Sections of `docs/Protocol_v1.md` affected

New §4.1.7. §3.9's permutation bullet annotated with the result. §4.1.2's stated
strength for the placebo corrected from p_WCB 0.0008 to p_perm 0.0395. §3.8 A's
"headline inference" declaration amended for the harvest-window arm only.

### 4. New commitment

1. Every harvest-window coefficient is reported with p_perm as headline and p_WCB
   beside it, and the manuscript states that the two disagree by about an order of
   magnitude for that arm and why.
2. The permutation 95th percentile of |t| is reported per cell, so the effective
   cluster count is visible rather than implied.
3. β_harv on peak is reported in the supplementary table only.

### 5. Per-hypothesis impact

- **H1, H2.** No impact. Live; blocked on the per-orbit export
  (`gee/S1_PER_ORBIT.js`, written 2026-09-13, awaiting a run).
- **H3.** Still **NOT MET, 0 of 4**, and the contradiction is now stronger, not
  weaker: β_pre on EOS is significant with the wrong sign at **p_perm 0.0005**
  (pixel) and 0.0075 (district). This is the study's most robust result.
- **H4.** Unchanged, NOT MET, 2 of 6. The per-cyclone stacks have not been
  permutation-tested; with ≤ 3 treated clusters for several of them, §3.10's
  MacKinnon–Webb rule already forbids an event-level significance claim, so no
  p-value there is being relied on.
- **Objective 4 as a causal question.** Withdrawn, unchanged. The §3.9 placebo is
  rejected at p_perm 0.0395 in the robustness arm and the estimator-dependence at
  p_perm 0.0340 and 0.0420, so §4.1.5's commitments rest on the conservative test.

### Changed files

`python/permutation_test.py` (new); `docs/Protocol_v1.md` (§4.1.7, §3.9 note,
§4.1.2 strength correction); `analysis/decisions_log.md` (2026-09-13 tenth
entry); `results/permutation_test/Table_SX_Permutation_district.csv`,
`Table_SX_Permutation_pixel.csv`, `Table_SX_Permutation_pixel_cens.csv` and the
three permutation-draw stores (new).

---

## 2026-09-13 (tenth entry) — DEV: §3.8 A's robustness arms run; HLS arm withdrawn; both live results survive every arm

**1. What changed.** Four of §3.8 A's five declared robustness arms are run
(`python/robustness_arms.py`): state × season FE, exposure buffer 75 km and
100 km, severity threshold 64 kt. The HLS arm is **withdrawn**.
`build_cyclone_exposure.py` is parameterised on buffer and severity so one
implementation of the rule produces every variant; its defaults reproduce the
committed catalogue **byte-for-byte** (md5 d5da3934fd3f2fd0a1f1b729d70d4089) and
the footprint table content-identically, and that equality is asserted before any
variant is reported.

**2. Why.** They are declared, never run, and a reviewer would ask. The buffer and
severity variants cannot be derived from the committed 50 km file, which records
only winds within 50 km, so the GADM v4.1 L2 shapefile was re-obtained and the
roster reconstructed from the catalogue's own 28 state/district pairs.

The HLS arm is withdrawn on two independent grounds: §3.4's 2026-09-09 amendment
already removed HLS as a substrate (Landsat plus Sentinel-2, same monsoon cloud,
cannot see the ascending limb here), and the arm's purpose — adding seasons
2016–2018 including Titli 2018 — is already met by the radar panel's 2017–2025
span with Titli in the headline.

**3. Sections affected.** New §4.1.8. §3.8 A's robustness bullet (HLS withdrawn,
the other four reported). §3.9's r-value grid recorded as still open.

**4. New commitment.** (a) Every §3.8 A coefficient reported in the manuscript
carries its five-arm robustness row. (b) **No arm is promoted to headline** — the
state × season arm removes the placebo violation at district level but not at
pixel level, so the declared headline stands. (c) The 64 kt arm's harvest-window
cells are reported as uninformative, not as null: 6 treated clusters,
MacKinnon–Webb. (d) §3.9's r-value grid is checked against §3.1's Gate 1 density
ratio and then either run or withdrawn by dated amendment; it is not left silent.

**5. Per-hypothesis impact.**

- **H1, H2.** No impact. Live; blocked on the per-orbit export.
- **H3.** Still **NOT MET, 0 of 4**, and the contradiction is now robust to every
  predeclared variation: β_pre on EOS is **negative in all ten arm × level cells**
  and |t| > 1.96 in eight, strongest under state × season FE (−18.16 d district,
  −4.61 d pixel) and the 64 kt threshold (−4.90 d pixel, t −5.07). Harvest earlier
  where later was predicted.
- **H4.** Unchanged, NOT MET, 2 of 6. The arms are §3.8 A quantities and do not
  bear on the §3.8 B stacks.
- **Objective 4 as a causal question.** Withdrawn, and now on firmer ground: the
  §3.9 timing placebo is rejected in **four of five** arms at pixel level, the
  fifth having too few treated clusters to test. The violation is not an artefact
  of the buffer, the severity threshold, or the between-state comparison —
  state × season FE removes about 40% of it and what remains is rejected at
  p_perm 0.0075.

**Changed files.** `python/build_cyclone_exposure.py`, `python/robustness_arms.py`
(new), `docs/Protocol_v1.md` (§4.1.8 and §3.8 A / §3.9 notes),
`analysis/decisions_log.md` (2026-09-13 eleventh entry),
`results/robustness/Table_SX_RobustnessArms_{district,pixel}.csv` and the per-arm
tables (new), `results/expo_var/` variant catalogues (new, not committed as
protocol docs — they are robustness inputs, and the frozen catalogue remains the
only committed one).

---

## 2026-09-13 (eleventh entry) — DEV: H1 and H2 resolved; both NOT MET; H2's optical cross-check withdrawn

**1. What changed.** The per-orbit export ran to completion (225 district-seasons,
170,321 per-orbit PLSM fits) and H1/H2 are resolved on measurement. Both are **NOT
MET**, clause by clause. H2's post-monsoon Sentinel-2 EOS cross-check is
**withdrawn**. Protocol §4.2 records the whole result.

    clause (a), between-orbit agreement, 8,515 paired pixel-seasons
        trough   sigma 25.90 d  r +0.339  38.2% within one dekad
        harvest  sigma 25.79 d  r +0.147  35.0% within one dekad
    clause (b), committed panel, 2,000-draw district cluster bootstrap
        trough   ratio 1.340 [1.273, 1.408]      required < 1
        harvest  ratio 1.508 [1.424, 1.592]      required < 1
    clause (b) corrected for the measured error, single-orbit, matched estimator
        trough   0.441        harvest 0.724      i.e. the claim is TRUE once
                                                 measurement error is removed

**2. Why.** Clause (b) needed no export and had been wrongly treated as blocked on
one; it fails. Clause (a) was then run not to rescue H1 — a conjunction cannot be
saved once a conjunct fails — but because two independent looks at one pixel-season
are the only way to decide whether clause (b) failed on noise or on real crop
variation. They decide it: **on noise.** A pixel's transplanting date varies 7.0 d
between seasons against 15.9 d between pixels, and σ ≈ 26 d swamps both.

H2's cross-check cannot be run: §3.4's 2026-09-09 amendment removed HLS as a
substrate and the optical panel is unusable under monsoon cloud, so no Sentinel-2
EOS series exists for these district-seasons.

**3. Sections affected.** New §4.2 (7 subsections). §2's H1 and H2. §3.4 (the
cross-check). §3.11 (the retention figure at per-orbit level, 26.2%).

**4. New commitment.** (a) H1/H2 reported clause by clause, never summarised
without naming which conjunct failed and what the other showed. (b) Clause (a)
reported per state with pair counts and pass composition; the four zero-pair
districts named — East Godavari, Visakhapatnam, Ganjam, Nayagarh; no Andhra Pradesh
claim from 210 pairs. (c) The 2017 baseline tolerance reported in dekads and
labelled a stability criterion, never an agreement threshold. (d) σ ≈ 26 d quoted
wherever a per-pixel quantity appears; no per-pixel marker quoted to better than a
few dekads. (e) The district-season mean stays the unit for every substantive claim.

**5. Per-hypothesis impact.**

- **H1 NOT MET.** Clause (a) 38.2% within one dekad, σ 25.90 d, r +0.339; clause
  (b) 1.340 [1.273, 1.408]. Fails on the instrument, not the phenology.
- **H2 NOT MET.** Clause (a) 35.0% within one dekad, σ 25.79 d, r +0.147; clause
  (b) 1.508 [1.424, 1.592]. Optical cross-check withdrawn.
- **H3 NOT MET.** 0 of 4; β_pre on EOS significant with the wrong sign at both
  levels. Unchanged.
- **H4 NOT MET.** 2 of 6. Unchanged.
- **H5** withdrawn. Unchanged.
- **All five predeclared hypotheses fail**, each for a measured reason. The
  study's positive contribution is the located boundary: ±1.3 d on a
  district-season mean marker against σ ≈ 26 d on a pixel-season.

**Changed files.** `docs/Protocol_v1.md` (§4.2);
`python/orbit_agreement.py` (tolerance framing, absolute tolerances, single-orbit
recheck, refusal on negative variance); `python/dispersion_test.py` (new);
`results/orbit_agreement/` (per_orbit_fits.csv, orbit_pairs.csv,
Table_SX_OrbitAgreement.csv, Table_SX_DispersionSingleOrbit.csv,
Table_SX_ClauseA_byDistrict.csv, run_full.log); `results/dispersion/`;
`analysis/decisions_log.md` (2026-09-13 fifteenth, seventeenth, eighteenth,
nineteenth and twentieth entries).

---

## 2026-09-13 — §3.5 mask-comparison arm: the WorldCereal defect and the arm it produced

**Deviation class:** open item closed. §4.3.4 recorded the mask arm as NOT RUN
because it required an Earth Engine export the repository cannot produce. The
export has now been produced and the arm is implemented, so §4.3.4's "not run"
status is superseded. This entry is the dated correction note; the §4.3.4 text
itself is left in place per the append-only rule, with the status amended there.

### The defect that had to be corrected first, and which I wrote

`gee/S1_MASK_FLAG.js` was written with `verifyOnly: true` precisely because its
three catalogue assumptions — the asset id, the `product` filter value and the
cropland code — had been written from memory and never checked. That caution was
correct and it paid. What it did not protect against was a defect in the
verification block itself: VERIFY 3 probed with the raw cohort asset rather than
the rebuilt `cohort` collection. The committed cohort asset was uploaded without
an X/Y mapping, so lon/lat are PROPERTIES and every feature's geometry is empty;
`filterBounds` therefore matched nothing and the block died on a null image.

This is the same failure the file's own header warns about, three sections above
the line that committed it. Recorded plainly: the warning was written and then not
applied. Fixed by probing
`cohort.filter(ee.Filter.eq('district','Puri')).geometry()`, and a fourth
verification block was added that prints the per-point flag for one district,
which is the check that would have caught it without a run.

### What the catalogue actually returned

All four checks passed on re-run and the values are now recorded in the script's
CONFIG so they do not depend on a chat transcript:

| check | result |
|---|---|
| asset id | `ESA/WorldCereal/2021/MODELS/v100` resolves, 591 images |
| products | irrigation, maize, springcereals, temporarycrops, wintercereals; 106 `temporarycrops` tiles |
| `classification` | bands `[classification, confidence]`; histogram over Puri's bounds has exactly two keys, 0 and 100 |
| per-point flag | Puri 400/400 covered, 346 coded 100, distinct values exactly {0, 100} |

The cropland code of 100 was the one assumption that could have silently voided
the arm, and it is confirmed. That `{0, 100}` came back exactly, in 400
independent draws, also establishes something the script depends on and did not
state: it samples a 10 m categorical band at `scale: 30` to match the panel's
30 m cell, and had the band's pyramid policy been `mean`, a 30 m aggregation of
0/100 pixels would have returned intermediate values and the `== 100` equality
test would have silently dropped real cropland.

### Dry run, then the full run

`dryRunDistrict: 'Puri'` queued one task instead of 25. Its CSV was checked before
the full run was authorised: 400 rows, exactly the five declared columns, no
nulls, `cell_id` unique and joining 400/400 both ways against the committed
panels. The full 25-task run then reproduced the Puri file **byte for byte**,
which is a reproducibility check on the export path rather than an assumption
about it.

### The full export, verified

25 files, 10,000 rows, 400 per district, one district per file, no duplicate
`cell_id`, zero points outside WorldCereal coverage, flag values exactly {0, 1},
and a 10,000/10,000 join both ways against `phen_panel_sar.csv` (90,000 rows =
10,000 × 9 seasons) and `s1_static_covariates.csv` with zero district-label
disagreements.

Retained: **8,085 of 10,000 points (80.85%)**. Per district 46.0%
(Visakhapatnam) to 98.3% (Bhadrak); no district at 0% or 100%.

### The one external corroboration of the cohort in this paper

Over Puri's bounding box WorldCereal calls 30.9% of the area cropland; at Puri's
cohort points it calls 86.5% cropland. That is a **2.8× enrichment**, and it is
the direction it must go if the cohort selection is finding agricultural land at
all. Stated precisely, because it is easy to overclaim: WorldCereal v100 has no
rice layer, so this is a general cropland classifier and the arm is not a rice
validation. It is nevertheless the only point in this study where something
outside the project agrees with the cohort, which has otherwise only ever been
checked against itself.

### An ambiguity that is bounded rather than assumed away

WorldCereal ships overlapping per-AEZ tiles and the export mosaicked them, taking
the last unmasked tile at each pixel; where two tiles disagree the pick is
arbitrary. `worldcereal_pixels_sampled` was exported for exactly this reason and
shows **62 of 10,000 points (0.62%) under two tiles** — Guntur 54, Krishna 7,
Mayurbhanj 1 — of which 59 are flagged cropland. A mosaicked export cannot
resolve the disagreement, so the arm is run a second time with those 59 points
also dropped (8,026 points, 80.26%) and reported both ways. If the two agree, the
arbitrariness does not matter at this sample size; that is then a statement about
the result rather than a hope about it.

### Why the arm re-runs the estimator instead of masking the panel

The district-season panel is not an average of pixel phenometrics:
`extract_phenometrics_sar.py` fits the five-segment PLSM to the district-season
**mean curve**. A pixel mask therefore cannot be applied to the committed
district panel after the fact — the mean curve has to be rebuilt from masked
pixels and refitted. `mask_sensitivity.py` consequently filters the 225 raw
exports to the masked `cell_id`s and hands them to the committed estimator,
rather than re-implementing the aggregation. A re-implementation would put a
second, unaudited copy of the estimator in the repository and the arm would then
test the copy rather than the paper.

The static covariates are filtered on the same whitelist, because
`merge_static_covariates.py` aggregates them to the district mean over that
district's cohort points; left unmasked, the district covariate would describe a
different set of points from the district's phenometric.

**Changed files.** `gee/S1_MASK_FLAG.js` (empty-geometry fix, VERIFY 4, verified
values and the dry-run result recorded in CONFIG, `verifyOnly` and
`dryRunDistrict` released); `python/mask_sensitivity.py` (new);
`results/mask_flag_all.csv`; `results/mask_sensitivity/`; `run_all.sh` (the arm's
steps); `docs/Protocol_v1.md` (§4.3.4 status amended);
`analysis/decisions_log.md`.

---

**Correction note, 2026-09-13 (later the same day).** The bullet above reading
"**All five predeclared hypotheses fail**, each for a measured reason" is withdrawn.
It is wrong twice over: **H5 was never tested** — MODIS was not obtained, so no
correlation was computed, and an untested hypothesis has no verdict — and **H3's
declared quantities were never estimated**, since §2 declares it on optical SOS, peak
NDVI date and EOS while this study fits radar trajectory breakpoints that §3 states
are not those quantities. A third correction applies to the same bullet's H1/H2 lines:
the **pre-declared** clause (a) criterion, tolerance fixed on the untreated 2017
baseline, is **met** (0.9443, 0.9114, 0.9387 against 0.90); the NOT MET verdict rested
on an absolute one-dekad rule adopted after the orbit fits existed, which is
result-aware. H1 and H2 fail on clause (b) alone.

The replacement sentence: **one hypothesis fails on its declared criterion (H4, two of
six against five of six); two fail on one clause while their other clause passes as
declared (H1, H2); one is not estimable as declared (H3); one was withdrawn untested
(H5).**

Found by an external re-audit, not by the author. The authoritative table is
`analysis/hypothesis_verdicts.md`; every figure in it was checked against the
committed results tables before it was written.

---

## 2026-09-13 (fourth entry) — §1.4's declared window sweep was not run until today; and the harvest breakpoint is identified by extrapolation for 8.2% of headline units

**Deviation 1 — a pre-declared sweep was never executed.** §1.4 declares: "Results are
also reported for the 0-, 20-, 30- and 45-day extensions (upper endpoints DOY 365, 385,
395, 410)… Gate 1–3 pass rates, extraction-failure rate and the §3.8 headline
coefficient are tabulated for all five endpoints." Until today only the 425 endpoint had
ever been extracted. An external re-audit found this; the author did not. **Closed**:
`python/extract_phenometrics_sar.py --window-end-doy` extracts the four truncated
endpoints and `python/window_sweep.py` tabulates all five into
`results/window_sweep/`. No new Earth Engine export was required — the truncation
operates on the committed per-bin composites, and `bins_within(425) ==
bins_within(None) == 55`, so the headline code path is unchanged and the no-truncation
run doubles as the sweep's control.

**Deviation 2 — a quantity the paper reports is, for some units, an extrapolation, and
nothing flagged it.** The five-segment model's final segment falls from the plateau to
*b₂* between *t₃* and *t₄* and is flat at *b₂* afterwards. A unit with **no valid dekad
after *t₄*** identifies *b₂* only from the slope of the fall projected forward: the
harvest date is where the fitted fall *would* reach baseline, not an observed return to
it. `plsm_fit` screens on |det(A)| > 1e-10, which such a fit passes, so it cleared every
gate silently and no committed output carried a flag for it. Measured exactly from `used`
on the district-season panel: **17 of 208 estimable units (8.2%) at the DOY 425
headline**, rising to **125 of 204 (61.3%) at DOY 365**.

**What this does and does not change.**

- It does **not** overturn any reported result. Re-estimating every §3.8 cell on the 191
  units with at least one valid dekad after *t₄* preserves every material sign: β_pre on
  harvest −10.184 (t −2.08) → −8.084 (t −2.12), β_harv on heading +6.183 (t +2.51) →
  **+7.438 (t +3.10)**, which strengthens. The two cells that change sign carry |t| ≤
  0.30 at every specification.
- It **does** mean the harvest coefficient cannot be read across the five endpoints, and
  the sweep table therefore carries the extrapolation share in every row with the harvest
  rows flagged.
- It **does** give §1.4's own justification a measured number: the 60-day extension is
  not a preference over Paper 1's core window, it is what identifies the harvest
  breakpoint at all.
- And the sweep's **positive** result must be recorded here too, because a deviation log
  that only carries defects misrepresents what the exercise found: **§3.9's timing
  placebo is not a window artefact.** β_harv on the trough breakpoint, declared zero,
  measures **+7.291 to +8.099 d with cluster-robust *t* between +3.80 and +4.30 at every
  one of the five endpoints** — a spread of 0.807 d over a 60-day change in the
  compositing window. §4.1 withdraws the causal claims of §3.8 on the strength of that
  placebo, so the sweep had the standing to overturn the paper's central negative result
  and instead confirmed it. The two `heading` cells and `trough` on `S_pre_season` are
  equally stable (ranges 1.349, 0.574 and 0.823 d at pixel level).
- The **headline retention rule is not changed**. Adding a post-*t₄* observation
  requirement after seeing which units it would drop is the discretion §3 exists to
  remove. The arm is reported alongside, labelled as an arm; any change to §3.11 must be
  declared as an amendment first and applied to all five endpoints together.

**Deviation 3 — a queued explanation was tested and found wrong.** The decisions log's
2026-09-13 third entry recorded, explicitly as an untested hypothesis, that the
machine-epsilon differences between the committed panel and the sweep control came from
multiprocessing chunk order, and queued a `--jobs 4` control as the test. **The test was
run and the hypothesis is refuted**: six runs crossing `--jobs` ∈ {1, 2, 4} with BLAS
threads free and pinned to 1 all produce one md5. Recorded here because the log stated a
cause and the cause was wrong; what replaces it is the measurement rather than another
guess — every breakpoint, retention flag, failure reason and failure class is
bit-identical across all 90,000 pixel-seasons, and only the fitted dB levels differ, at
≤ 3.55 × 10⁻¹⁵ absolute and ≤ 2.46 × 10⁻¹⁶ relative.

**Deviation 4 — a comparison produced a false difference count.** The first
control-versus-committed comparison reported 31,741 differing rows in `fail_reason`,
exactly the retained count. Artefact, not data: `fail_reason` is a pandas `StringDtype`
column, null on every retained row, and `pd.NA != pd.NA` is `pd.NA`, which `.sum()`
counted as differing. Both sides were null on all 31,741 rows.
`window_sweep.check_control` now fills nulls with a sentinel before comparing, and a
self-test fails on the artefact. Recorded because a comparison that invents differences
is the same defect class as a test that cannot fail — it reports a number nobody
produced.

**Changed files.** `python/window_sweep.py` (new); `python/extract_phenometrics_sar.py`
(`--window-end-doy`); `docs/Protocol_v1.md` (§1.4 amendment, four points);
`analysis/REAUDIT_BRIEF_2026-09-13.md` (dated corrections at §3, §3.2, §3.3 and §7);
`results/window_sweep/`; `analysis/decisions_log.md`; `analysis/deviation_log.md`.

---

## 2026-09-13 (fifth entry) — §3.3's two windows overlap by 9 days; the earlier reading of the dry-run export as a clean negative is WITHDRAWN

**The defect, and it is arithmetic rather than data.** §3.3 declares an event window of
"±14 days around landfall" and a pre-event reference of "the median σ⁰_VH over the 30
days ending 5 days before landfall". Those windows are **[L−14, L+14]** and
**[L−35, L−5]**. They share **[L−14, L−5]** — **9 days, 30% of the reference**. For Dana
2024 the run reported them verbatim: reference 2024-09-19 to 2024-10-19, event
2024-10-10 to 2024-11-07.

Two consequences, both measured on the committed dry-run export
(`S1_INUND_Baleshwar.csv`, 2,400 rows, three severe storms × two arms):

**(a) A point mass at exactly 0 dB, and it is arm-asymmetric.** An orbit whose scenes in
both windows are the same acquisition gives pre-median minus event-minimum **exactly 0**.
235 of 2,400 rows (9.8%) carry drop_db = 0.0 exactly. By unit and arm:

| storm | timing | actual | null2017 | ratio |
|---|---|---:|---:|---:|
| DANA 2024 | harvest_window | 0.1925 | 0.1050 | 1.8× |
| FANI 2019 | pre_season | 0.0950 | 0.0025 | **38×** |
| YAAS 2021 | pre_season | 0.1525 | 0.0400 | 3.8× |

A point mass that differs 38-fold between the two arms being compared is not a property
of flooding. **Any actual-against-null comparison on this statistic is comparing two
differently contaminated quantities**, which is why the comparison is void rather than
merely noisy. Pooled over the file the arm gap is 0.1467 against 0.0492 — 0.0975, about
five times the tolerance the consumer now enforces.

**(b) Half the declared event window predates the storm.** The minimum that defines
"inundated" can be an acquisition taken up to 14 days **before** landfall. A flood
signature attributed to a storm cannot be measured from a scene that predates it.

**WITHDRAWN: the reading of that export as a clean negative.** Earlier the same day this
session reported the Dana percentiles (actual p50 0.915 against null p50 1.024, maximum
percentile gap 0.442 dB) as evidence that the drop statistic carries no flood signal on
this coast, and stated that the balanced scene counts made the comparison fair. The scene
counts *were* balanced and that confound *is* absent — but the window overlap is a second,
larger confound that was not checked, and it is present and arm-asymmetric. **The
negative result is withdrawn. §3.3 is now neither supported nor withdrawn.** The defect
was findable by arithmetic from the two declared window definitions before any export was
run, and it was not found until the export made the zeros visible.

**The correction, and its authority.** §3.3's own sentence — "The 3 dB criterion **and the
window length** are re-derived on the untreated 2017 baseline season before use" —
authorises fixing the window as part of a calibration this section already required. It is
not a specification changed after seeing a result. The corrected event window starts **at**
landfall: **[L, L+14]** against a reference of **[L−35, L−5]**, which gives **zero
overlap** and no pre-landfall minimum, while keeping both declared numbers (a 14-day event
span, a 30-day reference ending 5 days before landfall).

**What changed in the code.**

- `gee/S1_INUNDATION.js` now exports **both** specifications — `postlandfall`
  ([L, L+14], the measurement) and `declared` ([L−14, L+14], reported as §3.3 writes it)
  — so the correction appears as a difference rather than a substitution. It also emits
  `overlap_days` per row (0 and 9 respectively) and **`win_min_day_off`**, the day of the
  window minimum relative to landfall, so a minimum that predates the storm is visible
  rather than inferred. `qualityMosaic('drop_db')` replaces `.max()` and selects the same
  per-pixel maximum, so **the declared arm's drop_db is unchanged by this patch and the
  re-export's declared rows are a regression test against the CSV already in hand.**
  `verifyOnly` is returned to **true**: these are structural changes and must be verified
  before further quota is spent.
- `python/inundation_intensity.py` (new) gates on the window rather than reporting through
  it. `check_windows()` admits a specification only if its reference and event windows do
  not overlap **and** its exact-zero mass differs between the arms by no more than 0.02.
  A specification failing either is marked DIAGNOSTIC ONLY and its verdict is
  **`WITHHELD -- window not admissible`**, never `DOES NOT SEPARATE`. An export with no
  `window_spec` column — every export made before today — admits nothing and issues no
  verdict. Run against the committed dry-run CSV it returns WITHHELD, as it must.
  23 self-tests, including that a pre-correction export cannot yield a negative result.

**Changed files.** `gee/S1_INUNDATION.js`; `python/inundation_intensity.py` (new, held
for patch14 with its verdict); `analysis/deviation_log.md`; `analysis/decisions_log.md`.

---

## 2026-09-13 (sixth entry) — the window correction is confirmed by measurement; and the verify block's percentiles were never measurements

**The correction is confirmed, on the probe that found the defect.** Re-running the
Baleshwar verify with both specifications exported side by side:

| quantity | `declared` [L−14, L+14] | `postlandfall` [L, L+14] |
|---|---:|---:|
| reference/event overlap | **9 days** | **0 days** |
| pixels with drop exactly 0 (of 400, Dana) | **79 actual / 42 null** | **0 / 0** |
| day of the window minimum, Dana actual (p5/p50/p95) | **−8.0 / −5.5 / +6.5** | +1.0 / +3.5 / +7.0 (Fani) |
| event scenes, actual vs null (Dana) | 10 vs 11 | 5 vs 5 |

The third row is the direct measurement of defect (b) and it could not be made before
`win_min_day_off` existed: **under the declared window the median pixel's "flood minimum"
came from a pass 5.5 days BEFORE landfall.** Under the corrected window every reported
minimum is post-landfall. Both defects are closed and the closure is measured, not argued.

**A second, independent sign the correction is right.** Under the declared window the
median drop was ≈ +0.9 dB in **both** arms — a bias manufactured by differencing a
minimum-over-ten-scenes against a median-over-fourteen. Under the corrected window the
median drop is ≈ **−0.05 dB in both arms**: centred on zero, which is what a no-flood
baseline must look like. The statistic was inflated and is now unbiased under the null.

**And a process defect in this session, recorded because it caused a wrong published
conclusion.** Comparing the two verify runs: the **actual** arm's reported percentiles
agreed to sixteen significant figures, while the **null** arm's p50 moved from **1.1149**
to **1.0493 dB** on identical code over an identical scene set — and neither equals the
exact value computed on the exported CSV, **1.0235**. The actual arm's exact CSV value
(0.9150) likewise differs from its reported 0.9095.

`ee.Reducer.percentile` is histogram-based and approximate. Its error here is up to
≈ 0.1 dB and it is **not stable between runs**. The precise mechanism for why one arm
shifted and the other did not is **not resolved** and is recorded as unresolved; what
matters is established without it: **the verify block's percentiles are not measurements,
and this session read them as measurements twice and drew the withdrawn "clean negative"
from them once.** The gap between arms that was being interpreted (0.44 dB on the
declared window, 0.30 dB on the corrected one) is only two to four times the reducer's own
instability, which is not a margin any conclusion can rest on.

**Fix.** The verify block now reports, first and labelled EXACT, the **count** of pixels at
or above 2, 3, 4 and 5 dB in each arm, and the exact mean. A share above a fixed threshold
is a count: exact, reproducible, and precisely the quantity §3.3's criterion needs. The
percentiles remain, labelled "APPROXIMATE -- shape only, ±~0.1 dB, not a measurement",
with the two conflicting run values written into the comment so the reason is on the face
of the code. A new block states that nothing in the verify output is the verdict, because
Baleshwar carries **one** severe harvest-window storm against a three-unit floor.

**Decision on sequencing, with its reasoning.** The single-district dry run is **skipped**
for the full export. Baleshwar has one severe harvest-window unit, below
`MIN_TREATED_UNITS = 3`, so a Baleshwar-only export cannot produce a verdict under the
pre-declared rule — it could only re-check the file layout, which `selectors: COLS`
already guards and which the verify run has now exercised twice. Expected round trips
going direct are ≈ 1.15 against a guaranteed 2 for a dry run first. The user is instead
given the exact expected row counts per district (113,600 total = 400 points × 71
storm-district rows × 2 arms × 2 window specs) and the 19-column header to check before
running all 25 tasks, so a structural failure is caught by arithmetic on the first file
rather than by a round trip.

**Changed files.** `gee/S1_INUNDATION.js` (exact count-based verify statistics;
percentiles labelled approximate; no-verdict block); `analysis/deviation_log.md`.

---

## 2026-09-13 (seventh entry) — §3.3's `inundated_frac` is WITHDRAWN. It was tested on 71 storm-district rows against 71 matched nulls and it does not separate.

**The declared test was executed in full, not abandoned.** All 25 districts exported,
**71 storm-district rows**, each paired with the same calendar window shifted to the
untreated 2017 season, **113,600 pixel rows**, 19 columns, every per-file row count
matching its predicted value exactly. The criterion was re-derived on the null arm as
§3.3 requires and judged against a rule fixed in writing **before the export existed**.

**Verdict on the 18 severe harvest-window units** — above the three-unit floor, so this is
an informative null and not an uninformative one:

| criterion | τ | median per-unit excess | perm p | rule (i) ≥ +0.05 | rule (ii) p ≤ 0.05 |
|---|---:|---:|---:|:--:|:--:|
| §3.3's declared 3 dB | 3.00 dB | **−0.0063** | 0.9385 | FAIL | FAIL |
| re-derived, null 95th | 5.45 dB | +0.00375 | 0.0845 | FAIL | FAIL |
| re-derived, null 99th | 8.11 dB | +0.0000 | 0.2594 | FAIL | FAIL |

**Four independent lines, any one sufficient.**

1. The declared criterion's excess is **negative** — the untreated year flags more pixels
   than the cyclone year.
2. **Not one unit of 18 reaches the threshold.** Largest per-unit excess anywhere
   **+0.0375**; 7 positive, 10 negative, 1 exactly zero. The signal is not a small one
   hidden by the median; it is absent in every unit.
3. **No threshold works.** Swept across 15 values from 1 to 12 dB, the best median excess
   is **+0.00375 at 5 dB** and it is *negative* below 3.5 dB. The failure belongs to the
   statistic, not to the 3 dB value — which is the answer to the obvious objection.
4. **The flagged drop has no physical timing.** The median flagged minimum falls
   **6.01 d** after landfall in the cyclone arm and **6.51 d** in the untreated arm
   (39.4% against 36.1% within five days). A flood would cluster early in the cyclone arm
   only. This check uses no threshold and no rate comparison, so it is independent of
   lines 1–3.

**Robustness.** Dropping the 2 of 18 units whose null arm carries > 1.25× the
event-window scenes: declared criterion median −0.0063, p 0.9060. The **most favourable
reading available anywhere** — 5.45 dB on the 16 clean units — gives p 0.0418 with a median
excess of **+0.0063**, six tenths of one percent of pixels. It is recorded as the best case
and it is two orders of magnitude below what an intensity variable needs. Rule (i) exists
precisely to stop a statistically detectable but negligible effect being reported as a
treatment intensity, and here it did its job.

**What the criterion is actually responding to.** It flags between **3.3% and 22.3%** of
pixels in years with no cyclone at all. Bouvet et al.'s open-water signature is real, but
in transplanted Kharif paddy on this coast it fires on the crop's ordinary standing water,
which is present every season. A criterion that responds to normal hydrology cannot
isolate the increment a cyclone adds.

**Consequences.** `inundated_frac` is not offered to §3.8 A as a continuous intensity
term and no secondary specification uses it. The binary severe-exposure indicators of
§1.1 remain the only exposure measure — which §3.8 always declared as the headline — so
**no reported estimate changes.** §3.3's amendment records the withdrawal with all four
lines of evidence and its limits: median 4 acquisitions in the 14-day window, and 6 of 36
unit-arms carrying 2 or fewer.

**This is a result.** The standard SAR open-water criterion, calibrated on a matched
untreated baseline and tested on 18 severe cyclone exposures over transplanted paddy, does
not distinguish a cyclone year from an untreated year, and no threshold on that statistic
does. ~~No published Sentinel-1 cyclone-flood study we could find reports a matched-null test
of this kind at all.~~ **Priority framing withdrawn 2026-09-14** (Protocol §3.3; repeated here
against the entry itself on the fifth pass, because this is where the claim is read). It was
never tested, and an untested priority claim is withdrawn rather than repeated. "Tested and
failed" is reportable; "not tested" would not have been.

**Changed files.** `docs/Protocol_v1.md` (§3.3 amendment, withdrawal);
`python/inundation_intensity.py` (threshold sweep and timing test added as first-class
outputs; 30 self-tests); `results/inundation/` (six tables);
`analysis/deviation_log.md`.

---

## 2026-09-13 (eighth entry) — a self-audit of the protocol, not prompted by a reviewer: §3.1's pre-declared Gate 1 justification test had never been run, and §3.2 asserts an exclusion the primary estimator deliberately does not perform

**Why this entry exists.** The §1.4 window sweep was found missing by an **external**
re-audit. Rather than wait for the next one, the protocol was read through for any other
declared test with no corresponding result. Three candidates surfaced; two are real
omissions and one is a declaration that cannot be executed as written. All three are
closed below. The remaining "supplementary sensitivity" items — the §3.9 r-value grid and
the §3.5 mask arm — were checked and are already properly closed, by §4.3.3's withdrawal
and §4.3.4's amendment respectively.

### Omission 1 — §3.1's Gate 1 justification test was pre-declared and never run

§3.1 (2026-09-09) declares: the panel is extracted twice, with Gate 1 and without, and
compared on **four named criteria** — fit quality, temporal stability, spatial coherence,
orbit agreement — with "Gate 1 retained only if it improves these on the majority of
criteria."

**It had not been run.** §3.1's third 2026-09-12 entry switched Gate 1 off at pixel level
on the strength of four summary statistics measured on the **2017 baseline season alone**,
and three of the four declared criteria cannot be evaluated on a single season at all
(temporal stability needs multiple seasons by construction; spatial coherence and orbit
agreement were not part of that comparison). The decision was right and is unchanged. What
was wrong is that a pre-declared four-criterion test over nine seasons was reported as
settled by a narrower measurement — which is precisely the shape of finding an external
re-audit converts into "the declared test was not run".

**Run.** `python/gate1_justification.py`, full panel extracted twice at
`--gate1-r 0.50` against the radar default 0.0, 90,000 pixel-seasons each.

| criterion | own retained set | fixed common subset |
|---|---|---|
| fit quality | **WORSENS** (0 improve / 2 worsen) | **WORSENS** |
| temporal stability | MIXED (1 / 2) | **WORSENS** (0 / 3) |
| spatial coherence | MIXED (2 / 4) | MIXED (2 / 4) |

The fourth criterion, **orbit agreement**, was then run through
`python/orbit_agreement.py --gate1-r 0.50` — the committed estimator with the gate on,
not a second copy — and is **MIXED (2 improve / 4 worsen)**, with the changes
**negligible in magnitude**: the paired-orbit **scaled between-orbit disagreement statistic changes** by 0.0006 to 0.016 d *(reworded 2026-09-14, eighth pass: "measurement error moves" named it an error)*
on a ~26 d quantity, and the within-tolerance share by 0.00002 to 0.0002. The comparison
tolerance was deliberately **not** loosened after seeing those numbers, so six tiny
non-zero changes register and the criterion reads MIXED; the magnitudes are reported so
that MIXED is understood as *negligible* rather than *conflicting*.

**Improves 0 of 4 evaluable criteria → Gate 1 REJECTED at pixel level**, which is what
the study already does. The verdict was determined before the fourth criterion was
computed — a majority of four needs three, and the first three gave zero — and it was run
and reported anyway.

**The gate makes the measurement worse, not merely fails to improve it.** Retention
**0.3527 → 0.3378** (−1.5 pp, 1,335 pixel-seasons); median RMSR **1.9847 → 2.0292 dB**.
On the **28,612 pixel-seasons retained by both arms** — the same pixels, so selection
cannot explain it — within-pixel dispersion about each pixel's own mean, season means
removed, **rises on all three markers**: trough 22.68 → 23.24 d, heading 17.66 → 17.92 d,
harvest 23.16 → 23.27 d. Deleting five-day bins removes observations from the dekadal
aggregation, and fewer observations per dekad is a noisier series.

**Two design points recorded because they are what make the test honest.** (a) Every
criterion is computed on each arm's own retained set **and** on the pixel-seasons retained
in both, because a gate that deleted the noisiest pixels would improve every dispersion
statistic by **sample selection alone**; a self-test plants exactly that confound and
checks the two columns separate it. (b) The statistics standing for each criterion are
declared in the module docstring, since §3.1 names criteria without fixing statistics, and
a criterion counts as improved only if **every** statistic it carries moves favourably —
MIXED is not an improvement, because §3.1 retains Gate 1 only if it *improves*.

### Omission 2 — §3 and §3.2 assert a Gate 2 exclusion that the primary estimator does not perform

§3's lead-in: "Gate 2 (§3.2) and Gate 3 (§3.11) apply unchanged." §3.2: "Pixels whose
extracted phenometric falls outside these bounds are flagged and excluded from the panel."
**Both are false for the primary five-segment estimator.** `plsm_retain` applies §3.11's
dekad count, shape admissibility and the selection-aware rise screen and **no calendar
window at all** — its docstring says so, and the module note gives §3.2's own reason: a
DOY ceiling "removes the class of gate that deleted Paper 1's treated post-period."
**§3.11 received exactly this correction on 2026-09-12; §3.2 did not, and the omission
stood until today.** The behaviour is correct and unchanged; the protocol's description of
it was wrong.

Measured (`python/gate2_state_sensitivity.py`): Gate 2 rejects **0 of 5,184 / 0 of 17,886
/ 0 of 8,671** pixel-seasons reaching it in Andhra Pradesh / Odisha / West Bengal. Had the
bounds been applied as declared, **2 of 9 state × marker medians lie outside them** —
trough in Odisha and West Bengal, each **14.5 d above the 240 ceiling** — and **9 of 9**
have a 95th percentile beyond the upper bound (harvest p95 = 422.0 against 380 in all
three states). More than half of two states' pixel-seasons would have been deleted on the
trough ceiling alone.

**This confirms §3.2's own prediction.** That section states: "The radar puts the end of
the dark phase at DOY 245–265 on this coast. The ceiling sat **below** the true onset."
Measured trough median **254.5** — mid-range of the predicted 245–265, above Paper 1's 240
ceiling. The prediction predates this panel's fitting.

> **Narrowed 2026-09-14 (eighth pass).** What was predicted and measured is the **radar
> trough distribution**, and the quoted phrase "below the **true onset**" is withdrawn with
> the §3.2 passage it quotes. Paper 1's optical calendar bounds do not align with Paper 2's radar breakpoint distribution and would censor many radar estimates if transferred across sensors. This demonstrates **non-transferability between these different measurands**. It does **not** establish that Paper 1's optical SOS bound was mis-specified, identify a true agronomic onset, or reinterpret Paper 1's support loss. Those questions require analysis of Paper 1's own optical measurements or an independent field reference.

### Declaration 3 — §3.2's state-specific-bounds sensitivity cannot be executed as written, and is not

§3.2 declares "state-specific bounds for West Bengal (aman) and coastal Andhra Pradesh"
as a supplementary sensitivity and **never specifies them**. Choosing them now, with the
panel fitted and the markers known, would measure the choice rather than the data.
**It is refused rather than run**, and the refusal is recorded here and in §3.2's
amendment instead of the item being left to look unexecuted.

What the sensitivity was *for* is answered without inventing anything: the rejection rate
is **0.0000 in all three states** because nothing is excluded, and the largest
between-state difference in the margin to the upper bound is **10.0 days** — the three
states behave alike against one set of bounds. There is no differential-screening problem
to correct.

**A defect in the first version of that module, recorded.** It returned a single verdict
conflating two different questions and therefore got one wrong: it reported
"state-specific bounds MAY be needed" whenever a marker sat near a bound, **even though
the primary path excludes nothing on those bounds, so nearness carries no screening
consequence at all**. The verdict is now split — Q1 differential screening, Q2 calendar
plausibility — with self-tests that check a near-bound or out-of-bound marker is reported
under Q2 and does **not** become a screening finding, and that genuine differential
screening still is one.

### Contingent, and recorded as contingent rather than unrun

§3.1's window note offers "applying Gate 1 over all 55 bins (with *N_peak* recomputed over
the full window)" as a supplementary sensitivity. It is a variant **of a gate**; with the
pixel-level gate rejected above there is no pixel-level gate for it to vary, so it is moot
at that level. Gate 1's surviving district-mean coverage role is a different rule and is
untouched by a pixel-level test.

**Changed files.** `python/gate1_justification.py` (new);
`python/gate2_state_sensitivity.py` (new); `python/orbit_agreement.py` (`--gate1-r`, so
the fourth criterion runs through the committed estimator rather than a copy of it);
`docs/Protocol_v1.md` (§3.1 and §3.2 amendments); `results/gate1_justification/`;
`results/gate2_state/`; `analysis/deviation_log.md`.

---

## 2026-09-14 — an external re-audit was right on six of seven findings; the claim that the repository was closed is WITHDRAWN

**The claim being withdrawn.** `REAUDIT_BRIEF_2026-09-14.md` and this session's messages
stated that every gap was closed and that nothing in the repository declared an unrun test
or described behaviour the code does not perform. **That was wrong.** An external re-audit
on 2026-09-14 raised seven findings; **six are confirmed** against the code and the
committed tables, and the seventh could not be checked from the author's working copy. Each
was verified before being accepted — none was taken on the auditor's word.

Five of the six are places where the **writing claimed more than the work supported**. One
required new analysis.

### 1. Three files carried the withdrawn "all five hypotheses fail" verdict

On 2026-09-13 "all five predeclared hypotheses fail" was withdrawn as result-aware and
`analysis/hypothesis_verdicts.md` became authoritative. That correction was propagated into
`REAUDIT_BRIEF_2026-09-13.md` **and nowhere else**. Still carrying the withdrawn verdict:

* `README.md` — "Every one of the five predeclared hypotheses fails", with NOT MET against
  H1, H2, H3 and H4, and clause (a) quoted on the 38%-within-one-dekad figure that §2 never
  declared;
* `analysis/test_classification.md` — NOT MET rows for both clauses (a) and "NOT MET, 0 of
  4" for H3;
* `osf/README.md` — "all five predeclared hypotheses fail".

So the repository held **three contradicting answers to its own central question** for a
day. `README.md` additionally claimed "Eleven of eleven pass" against a runner carrying 17.
All corrected in place, each with a dated note recording what it previously said.

### 2. §3.5's per-unit arm was not a DiD, and it was confounded — the substantive finding

§3.5 requires "both the primary-mask and intersection-mask **DiD coefficients** … for every
district × cyclone unit". `unit_estimate`, added 2026-09-13, computed **the exposed season
minus that same district's other seasons**: no comparison district anywhere in it.

**Measured harm, not asserted:** on the committed panel **38 of the 47 estimable units
(81%)** drew at least one control season from **another severe exposure of the same
district**. Baleshwar's Fani estimate used 2021 and 2024 as controls and Baleshwar was
severely exposed in both, so for four units in five the comparison was cyclone-year against
cyclone-year.

**And it gave a materially different answer.** Re-estimated properly, the median difference
from the superseded quantity is **+5.6 d** on trough (mean +3.7, max **25.4 d**), +1.2 d on
heading, +3.4 d on harvest. That is why the auditor's softer option — relabel it
"descriptive" — was **rejected**: it would have left a confounded number in the repository
under a gentler name.

**Replacement.** `unit_did` computes the canonical 2 × 2 estimate per unit — (treated
district's exposure season − its k = −1 season) − (mean over **clean** control districts of
the same difference) — on district-season means, §3.8's declared level of estimation. A
control is clean only with **no severe exposure in either the pre or post season**, and the
number dropped for that reason is reported per unit (median 8 clean controls survive, range
5–24). **8 of 47** units have a treated district itself severely exposed in its pre-season
and are flagged, per §3.8 B's `treated_other_severe_exposure` rule. No inference — one
treated cluster (MacKinnon & Webb 2018).

Two further gaps in the same arm, also closed: it ran for **trough only** (now all three
markers) and was **not called by `run_all.sh`**, so the pipeline did not reproduce its own
table (now stage 13).

**The §3.5 conclusion survives**, which is why both estimates are reported side by side:
intersection minus primary has mean **+0.110 / −0.256 / −0.401 d** on trough / heading /
harvest, signs agreeing in **46/47, 47/47, 45/47** units. Ten self-tests cover the new
estimator, including one that plants a common trend and checks the DiD recovers the planted
+8.000 d where the superseded contrast returns **+11.333 d**.

### 3. "Rule fixed before the export existed" was not accurate

§3.3's amendment, `b0f7a17`'s commit message and the 2026-09-14 brief all said the §3.3
decision rule was fixed "before the export existed". **It was fixed after the Baleshwar
two-probe verify run**, whose console output already carried the cyclone-arm and 2017-arm
drop percentiles for a severe harvest-window storm, and **before the full 25-district
export**. The accurate wording is now in all three places. The rule itself is unchanged and
its threshold was deliberately weak, so the author's judgement is that it was not tuned to
the outcome — but the claim about **when** was stronger than the facts and was repeated
more than once, which is the defect.

### 4. Gate 1's test was a retrospective operationalisation of predeclared domains

The four criteria were genuinely predeclared (2026-09-09). The **statistics** standing for
them, and the every-sub-statistic rule, were chosen on 2026-09-14 — before that comparison
ran, but **after** §3.1's 2026-09-12 entry had already measured the direction on the 2017
baseline (retention 0.2426 with the gate against 0.2544 without). "Retention share, higher
is better" was therefore selected already knowing which way it moved. The verdict is
unaffected — the margins are far larger than any choice of statistic would flip — but
"run as declared" overstates it and is corrected in §3.1.

### 5. The semivariogram was oversold as independent validation

The brief said "two independent confirmations" and "two methods sharing no arithmetic".
The arithmetic does differ, but both routes read the **same panel** through the **same
breakpoint estimator**, so neither is independent of a defect in the other; and the nugget
is an **upper bound** on structure-free error, containing real sub-kilometre variability
and any spatially correlated error component. *(**Corrected 2026-09-14, sixth pass:** the short-lag semivariance bounds only the **spatially uncorrelated** error component from above, under an additive signal-independent model. It does **not** bound total error: error shared between neighbouring pixels cancels from the difference and is **missing** from the statistic. Simulated — shared sd 25 d plus independent sd 5 d gives a short-lag root of 5.0 d against a total error sd of 25.50 d. It is also the shortest interpretable **bin**, not a fitted zero-distance intercept.)* *The trailing clause here —
"and any spatially correlated error component" — is the wrong way round for the same reason:
such a component cancels from the neighbour difference rather than being contained in it.* **`python/semivariance.py` states both
caveats itself** — the brief was less careful than the script it described. Corrected to:
*an internal spatial diagnostic yields an error scale consistent with the between-orbit
estimate.*

### 6. Reproduction documentation was stale or misleading

* `mask_sensitivity.py --per-unit` was never called by `run_all.sh` (fixed, all three
  markers).
* The runner's closing line read "ALL STAGES RUN -- no remaining Earth Engine dependency",
  while stages 2, 11, 13, 14 and 17 each call `need()` on an export directory this
  repository does not contain and stage 14 needs the external MARC NetCDF. A reader would
  read the old line as "clone and go". Replaced with an explicit note naming what a fresh
  clone still requires.
* `DATA_AVAILABILITY.md` said `gee/` holds 7 files; it holds **9**. `S1_INUNDATION.js` was
  added on 2026-09-13 and the count was not updated.
* The promised Mendeley/Zenodo DOI does not exist. This is already disclosed in
  `DATA_AVAILABILITY.md` itself and is a pre-submission rather than pre-drafting item.

### 7. NOT VERIFIED — the crop-calendar evidence

The re-audit reports `docs/field_reference_sources.md` as lacking an endorsed West Bengal
reference, lacking an endorsed coastal-Andhra reference, and citing one Odisha/CRRI document
that is not locally archived. **That file is not present in the author's working copy** — it
has never been edited by this session — so no bytes were available to check and **no claim
is made about it here in either direction.** Every other finding that *could* be checked was
correct, so the prior is that this one is too. It must be resolved before any statement of
three-state field-calendar validation is written; until then the claim is restricted to MARC
product agreement plus limited Odisha calendar plausibility.

**Changed files.** `python/mask_sensitivity.py` (`unit_did`, `district_season_means`,
`unit_before_after` marked superseded, 10 new self-tests); `README.md`;
`analysis/test_classification.md`; `osf/README.md`; `docs/Protocol_v1.md` (§3.5 amendment,
§3.3 and §3.1 provenance corrections); `run_all.sh`; `DATA_AVAILABILITY.md`;
`REAUDIT_BRIEF_2026-09-14.md`; `results/mask_sensitivity/Table_SX_MaskPerUnit_*.csv`;
`analysis/deviation_log.md`.


---

## 2026-09-14 (later the same day) — item 7 above is resolved, and resolving it found three further defects

**Correction note on item 7, in place rather than by rewrite.** Item 7 says of
`docs/field_reference_sources.md`: "That file is not present in the author's working copy …
no claim is made about it here in either direction." **That is superseded.** The file was
supplied, verified byte-for-byte against the committed blob `60d81d7`, and read in full. The
prior stated in item 7 held: every one of the re-audit's reported gaps is real, so the
external re-audit was right **7 of 7**. Item 7's text is left standing as the record of what
was and was not checkable at the time.

**Confirmed exactly as reported.** No endorsed West Bengal source. No endorsed coastal Andhra
Pradesh source — its one ANGRAU RARS Tirupati candidate was dropped on agro-climatic-zone
grounds (Southern Zone against the coastal delta), a rejection the catalogue already records
in bold. CRRI Technology Bulletin 62 is endorsed but **not locally archived**, because
`icar-nrri.in` could not be resolved from the sandbox. No endorsement changes.

Three further defects came out of reading the file. **None was raised by the re-audit**; all
three were found while checking its seventh claim, and all three are recorded because the
pattern in them is the same as the pattern in the six findings above — the writing claimed
more than the work supported.

### 7a. The PDF archive inverted its own catalogue, and nothing labelled it

`docs/field_reference_pdfs/` holds nine PDFs. **Three are endorsed** (the Odisha CRIDA/OUAT
contingency plans), one is auxiliary and unendorsed (PMFBY), and **five are not endorsed at
all** — two West Bengal plans in a repository whose catalogue says West Bengal is NOT FOUND,
two Andhra delta plans pending issuance metadata, and the ANGRAU Tirupati PoP the catalogue
says in bold must not be added. The one document the catalogue *does* endorse but could not
retrieve, CRRI TB62, is the one **absent** from the folder. A reviewer browsing the directory
would have concluded the opposite of what the catalogue says. Keeping rejected candidates is
deliberate and useful — it is the record of a search — but leaving them unlabelled was a
defect. Fixed with an **archive manifest** giving each file's status and the explicit rule
that presence in the folder is not endorsement.

### 7b. §3.4 cites the AICRP calendar, which is not in the catalogue and was never retrieved

§3.4 Tier 2 bounds the fitted phenometrics against "the AICRP Agrometeorology crop-weather
calendars giving Kharif rice as Standard Meteorological Weeks 25–42 … approximately DOY
170–294". **AICRP appears zero times in `docs/field_reference_sources.md`.** Nothing AICRP has
been retrieved or archived. The four endorsed Odisha sources give something different in
kind: monthly *sowing* windows ("May – June", "June – July", "July –Aug") and harvest only
as a physiological criterion ("at physiological maturity stage"). **No endorsed source in this
project supports an SMW range or a calendar-date harvest window.** §3.4's attribution is
**suspended** by amendment of this date, and no statement in the study may attribute a date
bound to AICRP until a source is retrieved, quoted and archived.

**How far it reaches was traced, and the answer narrowed twice — both times towards zero.**
The constant is `TROUGH_WINDOW = (170.0, 294.0)` in `python/extract_phenometrics_sar.py`.
First reading: it defaults `extract_markers`, the superseded crossing arm, so no primary
coefficient touches it. Checking the call site refuted even that — the single production call
(`run_district`) passes `trough_window=GATE2["trough"] = (155.0, 240.0)` **explicitly**, so
the `xr_*` panel columns do not use it either. Its only remaining callers are four self-tests.
**It is a dead default, and no committed number in this study depends on it.** The first draft
of the catalogue's own gap section carried the wider claim; it was corrected before being
committed and the correction is dated in that file. The constant is left in place rather than
deleted or silently re-valued, because deleting it would remove the only thing the protocol's
withdrawn sentence can be checked against; its comment now states both caveats.

### 7c. A protocol sentence describing behaviour the code does not perform

`docs/Protocol_v1.md` line 155 described the trough as "minimum within the transplanting
window (DOY 170–294, §3.4's AICRP calendar)". **No live code path searches DOY 170–294.** The
crossing arm searches §3.2's 155–240; the trapezoid is bounded by §3.2 structurally; the
**primary PLSM estimator has no calendar window at all** — its trough breakpoint lives on
`PIXEL_GRID_DOY["t1"] = (184.5, 304.5)`, derived from the untreated 2017 baseline district-mean
range padded two dekads, and documented in code as a compute decision rather than a gate.
The parenthetical is **withdrawn as a description of this pipeline** and replaced with what
each arm actually searches. This is the defect class §5 item 5 of the 2026-09-14 brief asks
reviewers to hunt for — a declaration-language sentence the code does not honour — and it is
the second instance found (the first was §3.2's Gate 2). It was found by tracing a citation,
which is now recorded as a method worth repeating: *trace every constant that carries a
citation in its comment to its call sites, and check the citation exists in the catalogue.*

### 7d. The §6 field-reference precondition attaches to a hypothesis that no longer exists

§6's Provenance bullet required the three-state catalogue "before H1 is claimed for any
state". It dates from the frozen protocol, where H1/H2 were **accuracy** claims (bias and
RMSE against MARC and against field observation). §2's rewrite of 2026-09-09 withdrew every
accuracy claim; H1 and H2 are measurement-consistency claims tested by between-orbit agreement
and by inter-seasonal against between-pixel dispersion, and §4.2 resolved both **without any
field reference**. So the precondition as written gated nothing, while appearing to gate the
study's two live hypotheses. Re-attached by amendment of this date to **H1c/H2c** (product
agreement and calendar plausibility, reported and never tested) and to **§3.4 Tier 2**, where
it binds harder than before: the calendar leg is available for **Odisha only**, every Odisha
calendar sentence must be attributed to "the ICAR-CRIDA / OUAT Agricultural Contingency Plan
for X district" rather than to "the state extension crop calendar", and **no three-state
calendar-validation statement may be written**. The RiceAtlas leg of Tier 2 is unaffected.

**Impact on the hypotheses.** None on H1, H2, H3, H4 or H5. No reported coefficient, table or
figure changes. Every change here is to a citation, a comment, a protocol sentence or a
precondition's scope. The restriction that *is* new is on what the manuscript may say: the
calendar-plausibility claim is Odisha-only and named-source-only, and AICRP may not be cited.

**Changed files.** `docs/field_reference_sources.md` (archive manifest; AICRP provenance gap;
same-day correction of that section's reach claim; change-log entry);
`docs/Protocol_v1.md` (§3.4 trough-bullet withdrawal, §3.4 Tier 2 amendment, §6 precondition
re-attachment); `python/extract_phenometrics_sar.py` (`TROUGH_WINDOW` comment, two caveats);
`REAUDIT_BRIEF_2026-09-14.md` (§4b.7 closed, §6 standing status superseded);
`analysis/deviation_log.md`; `analysis/decisions_log.md`.


---

## 2026-09-14 (third pass, same day) — the withdrawn verdict was in six files, not three

The external re-audit found the withdrawn "all five predeclared hypotheses fail" verdict
standing in three files (`README.md`, `analysis/test_classification.md`, `osf/README.md`).
Those were corrected in the first pass of this date. **A second sweep found it standing in
three more**, and the third of them is inside a file the first pass had just corrected:

1. **`docs/Protocol_v1.md` §4.2.6, headed "Per-hypothesis status, final."** A verdict block
   reading `H1 NOT MET / H2 NOT MET / H3 NOT MET / H4 NOT MET`, closing with "Every
   predeclared hypothesis in this study fails." **§4.2 withdraws that verdict at §4.2.2, two
   pages above, in the same amendment** — and §4.2.7, *below*, commits that
   H1 and H2 will never be summarised as "not met" without naming the clause. So the protocol
   contradicted itself twice within one section while calling itself final.
2. **`docs/Protocol_v1.md` §4.3.1**, "The verdict is unchanged: H3 NOT MET, 0 of 4 … the
   mismatch affects what the verdict *means*, not what it *is*." That sentence is the origin
   of the H3 error: it lets a verdict stand on a test that was never run. §2 declares β on
   optical SOS, peak NDVI date and EOS; those were never estimated.
3. **`analysis/test_classification.md`**, item 1 of "What a reviewer should check": "Every
   predeclared hypothesis fails; confirm the criteria were not rewritten to produce that."
   The **table** in that file was corrected in the first pass of this date; **this line was
   not** — a reviewer instruction telling the reviewer the withdrawn answer.

**Also found:** `docs/Protocol_v1.md` §4.1.6's per-hypothesis impact bullet carries
"H3. NOT MET, 0 of 4"; it belongs to the earlier 2026-09-13 amendment and is left standing
with a dated forward note, as this project's convention requires.

**Why the first pass missed them.** It swept for the propagated *summary* phrase. These
state the same verdict in a different shape — hypothesis by hypothesis, as a single-clause
assertion, and as a checklist instruction. **A phrase sweep does not find a claim restated
in another form.** The rule now recorded: a withdrawn verdict is chased **by meaning**, file
by file, and the sweep must include the files already corrected in the same pass, because a
narrative file states its central claim more than once.

**Severity.** No number changes. What changes is that the protocol no longer contradicts
itself about its own central question, and `analysis/hypothesis_verdicts.md`'s claim that
the protocol "points here" is now true — it was not when written.

**Impact on the hypotheses.** None. Every correction is to wording that had already been
superseded elsewhere in the repository.

### One more omission, found by checking the manifest against the repository index

The archive manifest added earlier today was **verified against `git ls-files`, not just
written**: all nine filenames match the committed index exactly, and the catalogue's claim that
CRRI TB62 is absent is confirmed by its absence from that index. Doing that check surfaced a
separate omission: **`DATA_AVAILABILITY.md` had no row for `docs/field_reference_sources.md` or
`docs/field_reference_pdfs/` at all.** That file is the repository's index of what is committed
and what each item lets a reader verify, so nine committed PDFs and the catalogue governing them
were invisible to anyone using it as intended. A row was added carrying the endorsement counts
and the "presence is not endorsement" rule, so the index cannot be read as an endorsement list.

**Changed files.** `docs/Protocol_v1.md` (§4.2.6 superseded block plus a corrected block,
§4.3.1 correction note, §4.1.6 forward note); `analysis/test_classification.md` (checklist
item 1); `analysis/hypothesis_verdicts.md` (the pointer claim amended; H1c/H2c's calendar leg
marked partial); `README.md`; `osf/README.md`; `DATA_AVAILABILITY.md` (field-reference row
added); `analysis/deviation_log.md`; `analysis/decisions_log.md`;
`REAUDIT_BRIEF_2026-09-14.md`.


---

## 2026-09-14 (fourth pass) — a SECOND external audit; §3.5's per-unit arm rebuilt again, and its conclusion withdrawn

The corrected per-unit DiD shipped in `292c4c0` was audited the same day by an external
reviewer working from the pushed commit. **It found three defects and all three are real.**
Every one was verified against the code and the committed tables before being accepted, and
the numbers below are this project's own recomputation, not the auditor's figures taken on
trust — they agree to within a day on every marker.

### 1. The estimand was not the declared one

`district_season_means` grouped the **pixel** panel by district and season and took the mean.
The declared district-season value is a **PLSM fit to the district-season mean curve**. That
is stated in §3.5's own amendment, and — worse — in the header of
`python/mask_sensitivity.py` itself, which says the module "does NOT re-implement the panel
construction … re-implementing that here would put a second, unaudited copy of the estimator
in the repository, and the arm would then test the copy rather than the paper." **The
violation was added to that same file, 570 lines below the rule forbidding it.** The correct
input existed on disk for both masks the whole time
(`results/masked/phen_panel_district_season.csv`).

Measured: switching to the declared estimand moves the median per-unit coefficient by
**9.6 d (trough), 7.5 d (heading), 12.4 d (harvest)**, maxima **63.2 / 34.3 / 70.6 d**, and
flips the sign of 6 of 44 trough units, 12 of 44 heading and 19 of 44 harvest. A different
number, not a differently-labelled one.

`district_curve_panel` replaces it, reads the committed panel, and **refuses a pixel panel
outright**; a self-test asserts the refusal.

### 2. The clean-control window was two seasons, not three

§3.8 B requires controls with no severe exposure in **t − 1, t or t + 1**. The code tested
t − 1 and t. For Titli that admitted **19 controls where the declared rule admits 5** — the
14 wrongly admitted were all Fani- or Bulbul-exposed in 2019, i.e. the contamination the DiD
was built to remove, re-entering through the back door.

Fixed by deleting the local control logic entirely and taking stack membership from
`event_study.derive_stack`, the repository's audited implementation of §3.8 B, whose own
self-test asserts it reproduces `docs/cyclone_footprints_ibtracs50km.csv` exactly for the five
cyclones that file covers. There is now **one** implementation of the rule in the repository,
which is what the module header demanded in the first place.

### 3. The roster was all nine severe storms, not the declared six

Michaung 2023, Dana 2024 and Montha 2025 entered a table reported against a design §3.8 B
states over six named cyclones. The primary block is now exactly `event_study.ESTIMABLE`;
the other three are reported in a separately labelled `additional_severe` block that is not
part of §3.5's claim and enters no sign test. Same-storm fringe districts are dropped by
`derive_stack`; in this catalogue exactly one such district exists (Krishna, Michaung), and it
falls outside the declared roster anyway.

### What the corrected arm measures — and the §3.5 per-unit conclusion is WITHDRAWN

Over the **35** declared units (not 47), intersection minus primary is mean **−7.39 d**
(trough), **−0.67 d** (heading), **−1.59 d** (harvest), signs agreeing **31/35, 22/35,
21/35**. The withdrawn text claimed +0.110 / −0.256 / −0.401 d and 46/47, 47/47, 45/47.
**"Mask choice does not move the per-unit estimates" is withdrawn.** Individual units move by
up to 36.7 / 25.0 / 50.0 d.

**The district- and pixel-level §3.5 results are unaffected and still hold.** They are
produced by filtering the raw exports and re-running the committed estimator, exactly as the
module header requires; only the per-unit sub-arm took the shortcut.

### The structural finding underneath it, which neither audit raised

Applying §3.8 B's control rule honestly leaves four of six cyclones with almost no comparison
group. The declared clean controls for Titli, Fani, Bulbul and Amphan are almost entirely
coastal Andhra Pradesh districts, and most fail the district-level fit in the relevant
seasons. **Usable control districts: Titli 1, Fani 2, Bulbul 2, Amphan 4, Yaas 13, Remal 11.**
With one control district the "mean over clean controls" *is* that district, so Titli's
per-unit number is a two-district comparison, not a DiD against a control group. This is a
definitional consequence, not a threshold.

Split on whether at least three declared controls survive the fit screen — a property of the
panel rather than of the coefficients, **though computed after the coefficients were seen, and
declared as such** — the 12 units with a control group give mean **−0.99 / +0.14 / −4.42 d**,
signs **10/12, 10/12, 11/12**; the 23 without give **−10.72 / −1.09 / −0.11 d**, signs
**21/23, 12/23, 10/23**. The instability is concentrated where the denominator is one or two
districts. That is this study's own σ ≈ 26 d finding reappearing through a tiny control pool,
not a property of the masks.

### A fourth finding, from tracing the numbers rather than the code

§3.8 B states per-cyclone clean-control counts of Fani 7, Bulbul 7, Amphan 10, Yaas 17,
Remal 13. Four of those are **too high**: they were read off
`docs/cyclone_footprints_ibtracs50km.csv` without restricting to the 25-district roster, so
they count **Nellore and Prakasam**, southern Andhra districts that are not in this study's
panel and can never supply a control observation. (Kolkata *was* excluded, as the sentence
claims; these two were not.) Roster-restricted: **5, 5, 8, 15, 13** — the figures
`results/Table_SX_EventStudy.csv` has carried all along. So a committed results table has been
contradicting a protocol sentence, and nobody compared them. **No estimate changes** — phantom
districts contribute nothing — but the protocol advertised the control pools as larger than
they are, which is precisely the thing the per-unit arm turns out to be sensitive to.

### And a fifth: the brief contradicted its own correction

`REAUDIT_BRIEF_2026-09-14.md` §3.5 withdrew the phrase "two methods sharing no arithmetic",
and its §6 standing-status bullet 270 lines later still used it. Corrected in place. This is
the **third** time in two days that a withdrawn phrase survived somewhere the correction pass
did not reach, and the second time inside a file that was being corrected for exactly that.

**Impact on the hypotheses.** None on H1, H2, H3, H4 or H5. No headline estimate changes:
§3.5's per-unit arm is a disclosure rule, not a reported specification, and its district- and
pixel-level results are untouched. What changes is a claim — "mask choice does not move the
per-unit estimates" — which is withdrawn, and a set of protocol counts, which are corrected.

**Changed files.** `python/mask_sensitivity.py` (`district_curve_panel` replaces
`district_season_means`; `unit_did` takes declared stacks; `declared_roster`;
`unit_before_after` re-based; the CLI reads the district-season panels; 12 rewritten
self-tests); `docs/Protocol_v1.md` (§3.5 second-pass amendment, §3.8 B count correction);
`README.md`; `REAUDIT_BRIEF_2026-09-14.md`;
`results/mask_sensitivity/Table_SX_MaskPerUnit_{trough,heading,harvest}.csv`;
`analysis/deviation_log.md`; `analysis/decisions_log.md`.


---

## 2026-09-14 (fifth pass) — the masked district panels were never committed; an "already exists on disk" claim was environment-specific

**The audit is right and this project was wrong.** On 2026-09-14 this log and the
accompanying correspondence stated that the correctly fitted district-season panels
"already existed on disk for both masks", given as the reason §3.5's per-unit arm needed no
re-export. That was true of the author's working environment and **false of this
repository**: at `292c4c0`, `git ls-files` carries nothing under `results/masked*`. An
external audit of the full local copy of the project, ZIP archives included, found only the
primary `results/phen_panel_district_season.csv` and said so.

**Consequence, stated without softening.** The per-unit arm as shipped in patch18 could not
have been reproduced from a clone, while §3.5's amendment describing it implied it could. A
disclosure rule that nobody else can recompute is not a disclosure.

**This is a repeat, not a new failure mode.** `README.md`'s original "nine of nine
self-tests pass" was likewise true only in the environment it was written in, and that entry
is already in this log. Twice now, a property of the author's machine has been written down
as a property of the repository. The rule that follows, recorded in
`analysis/decisions_log.md`: **before any claim that an input "exists", check it against
`git ls-files`, not against the working directory.**

### The fix

The four masked **district-season** panels are committed:
`results/masked/phen_panel_district_season{,_static}.csv` and
`results/masked_noovl/phen_panel_district_season{,_static}.csv` — 274 KiB in total, because
they are district-level (225 rows each: 25 districts x 9 seasons). The masked **pixel**
panels (~117 MiB) stay excluded; the per-unit arm does not read them. `--per-unit` now runs
from a clone with no Earth Engine account.

`docs/verify_masked_panels.md` is added as the provenance record, and it is written so a
third party validates the new files against files that were **already committed**: the
committed `mask_flag_all.csv` gives 8,085 of 10,000 flagged and 62 multi-tile points of
which 59 are inside the mask; the committed `filter_report_masked{,_noovl}.csv` give
`cells_out` 72,765 and 72,234, exactly 8,085 x 9 and 8,026 x 9; the new panels carry
`n_pixels` of 8,085 and 8,026 per season and are nested inside the primary panel; and
regenerating the three per-unit tables from them must reproduce the committed md5s. Nothing
in that chain depends on trusting the author.

### Two smaller things found while fixing it

* **`DATA_AVAILABILITY.md` over-claimed the regeneration path.** It said the masked panels
  are "Produced by stage 13 of `run_all.sh` from the committed mask flags". Stage 13 also
  needs `$RICEBACI_ROOT/s1full`, the 225 raw exports, which are excluded — `--filter` masks
  those raw files. Stage 13 gated only on `s1_maskflag`, so a fresh clone would have failed
  several commands into the stage rather than at its gate. Both corrected: the row now names
  the raw exports, and the stage calls `need()` on them.
* **§3.5's overlap figure was loosely worded.** "62 of 10,000 points … the arm is reported a
  second time with those points dropped" — 62 points are *identified* as multi-tile, but only
  **59** are flagged inside the intersection mask and therefore actually removed
  (8,085 - 59 = 8,026, which is the figure the protocol already reports). The other 3 were
  outside the mask already. Both numbers are readable from the committed `mask_flag_all.csv`;
  clarified in place.

**Impact on the hypotheses.** None. No coefficient, table or figure changes. What changes is
that a claim of reproducibility becomes true, and two number statements become exact.

### And committing the panels was NOT sufficient — a second dependency, found by executing the claim

Having committed the district panels, the reproducibility claim was **tested** rather than
asserted: the arm was run with `RICEBACI_ROOT` pointing at a directory holding only files this
patch commits, and the output compared byte for byte against the committed tables. **It did not
match.** The per-unit table carried two further columns — `primary_withdrawn_pixelavg_coef` and
`intersection_withdrawn_pixelavg_coef` — computed from the masked **pixel** panels, which are
~117 MiB and are not committed. From committed files only the table came out with 39 columns
instead of 41; every other column was byte-identical.

So the table was unreproducible for a **second, independent** reason, and reading the code
would not have revealed it — the dependency is in which files a default argument happens to
find. The withdrawn comparison is now opt-in (`--withdrawn-comparison`) and writes a separate
file, `Table_SX_MaskPerUnit_withdrawnCompare_<marker>.csv`, which `DATA_AVAILABILITY.md`
labels as not regenerable from this repository. The three main tables now regenerate
**byte-identically** from committed inputs alone, confirmed in both directions, and their md5s
changed as a result (`a74c8ac8…`, `dee80607…`, `89c9df73…`).

**The method, which is the reusable part.** Two reproducibility claims failed in one day and
neither was caught by reading. The first was caught by an external auditor running
`git ls-files` across the whole project; the second by running the arm against committed files
only. Standing rule: **a reproducibility claim is established by executing it against committed
files only — never by inspecting code, and never from the author's working directory.** The
test cost one directory and three commands and found what four passes of reading had not.

**Changed files.** `docs/verify_masked_panels.md` (new); `DATA_AVAILABILITY.md`;
`docs/Protocol_v1.md` (§3.5 overlap clarification); `run_all.sh` (stage 13 gate, and the
side-table call); `python/mask_sensitivity.py` (`--withdrawn-comparison` made opt-in);
`results/masked/phen_panel_district_season{,_static}.csv`;
`results/masked_noovl/phen_panel_district_season{,_static}.csv`;
`results/mask_sensitivity/Table_SX_MaskPerUnit_{trough,heading,harvest}.csv` (regenerated
without the two pixel-panel columns);
`results/mask_sensitivity/Table_SX_MaskPerUnit_withdrawnCompare_{trough,heading,harvest}.csv`
(new); `analysis/deviation_log.md`; `analysis/decisions_log.md`.


---

## 2026-09-14 (sixth pass) — corrections to the record above, and a platform defect in every committed table

### Correction: patch18 was NOT withdrawn before delivery. It is commit `f585325`.

The fifth-pass entry above, and the handoff that accompanied it, said patch18 was withdrawn
before delivery and that patch18b replaced it. **That is wrong as history.** patch18 had
already been verified, committed and pushed by the receive-only executor as **`f585325`** by
the time the uncommitted-panel finding arrived. The panel fix is therefore a **follow-on
commit on top of `f585325`**, not a replacement of anything. The fifth-pass text is left
standing, as this project's convention requires, and this note is the correction.

**The executor's handling of it is worth recording, because the STOP rule did its job.**
patch18b's handoff declared parent `292c4c0` and instructed that patch18 be discarded. The
executor checked `git log`, found HEAD at `f585325`, recognised that the handoff's first
factual claim was false, **refused to extract or commit anything**, and reported the mismatch
with the options it could see. It did not force-push, did not reset, and did not improvise a
merge. That is exactly the behaviour the receive-only rule exists to produce, and the fault was
in the handoff: I wrote a parent commit that was already stale when I wrote it, because I
assumed a hold that had not been confirmed. **A handoff must state the parent it was built
against and must not instruct the discarding of a commit whose status has not been checked.**

Corrected numbers for the follow-on: against `f585325` the change is **17 lines — 9 modified,
8 added** (not 19, because `README.md` and `REAUDIT_BRIEF_2026-09-14.md` were already at their
patch18b content in `f585325`), and the tracked-file count goes 225 → 233.

### The reproducibility claim was platform-dependent, across the whole repository

An external auditor regenerated the three per-unit tables **on Windows**. They came back with
the same parsed values and **CRLF** line endings: each file 226 bytes larger (225 rows + a
header), a different md5, byte-identical only after normalising. So "byte-identical" was a
property of Linux, not of the repository.

**The cause, and its real extent.** `pandas.DataFrame.to_csv` defaults `lineterminator` to
**`os.linesep`**. The defect was not confined to the three tables that happened to be tested:
**65 `to_csv` call sites across 22 modules** carried it, none passing the argument, so *every*
committed CSV in this repository would have regenerated with a different md5 on Windows — which
means every md5 table in every handoff, and every reproducibility sentence in
`DATA_AVAILABILITY.md`, was false for any Windows reproducer. Four modules also wrote committed
JSON through a bare `open(path, "w")`, which Python translates to CRLF on Windows; one of them
writes `figures/figure_provenance.json`, the file `make_figures.py --verify` compares against,
so the figure-verification story had the same hole.

**The fix is a guard with a gate, not 65 edits.** `python/lf_output.py` pins
`lineterminator="\n"` on `DataFrame.to_csv` and `Series.to_csv` at import, and supplies
`open_lf()` for text writes; all 22 CSV-writing modules import it and the four JSON writers
pin their newline. Editing 65 call sites would have fixed today and guaranteed nothing about
the next one, so the module's `--selftest` **scans the source of every sibling module** and
fails if a module that calls `.to_csv(` does not import the guard, or if a committed-JSON
writer leaves its newline unpinned. Both gates are tested by sabotage. It is self-test module
1 of **18**; the roster count rises from 17 and `README.md` and `DATA_AVAILABILITY.md` are
updated.

**No output changes on Linux.** Every committed table regenerates to the same md5 it had
before the guard, verified for the three per-unit tables and the three side tables.

### Two scope corrections to `docs/verify_masked_panels.md`, both from the auditor and both right

1. **Checks 1–3 are consistency checks, not construction proofs.** Row count, per-season pixel
   totals and nesting all follow from the mask, not from the estimator, so a panel built by
   averaging pixel dates could satisfy them. They rule out a panel masked at the wrong step or
   built over the wrong sample; they do not prove the PLSM was fitted to the mean curve. The
   governing sentence is now stated exactly: **the per-unit calculation is reproducible from
   the committed fitted district panels; reconstructing those panels still requires the
   archived raw exports.** Also recorded: `phen_curves_district_season.csv`, the mean curves the
   fit was performed on, exists per variant (508 KiB) and is *not* committed — noted rather
   than implied away, so a reviewer who wants the fit itself re-checkable knows what to ask for.
2. **"Byte-identical" needed the platform qualifier**, which is what exposed the defect above.
   Rather than weaken the wording to "value-identical", the code now makes the stronger
   statement true.

**Impact on the hypotheses.** None. No coefficient, table or figure changes. What changes is
that a reproducibility claim becomes platform-independent and correctly scoped, and that the
history of patch18 is stated accurately.

> **Correction note, 2026-09-15 (tenth pass) — this entry's item 2 overstated what the LF pin
> achieved, and the phrase "platform-independent" just above is withdrawn.** Item 2 said
> `"Byte-identical" needed the platform qualifier ... Rather than weaken the wording to
> "value-identical", the code now makes the stronger statement true.` **It does not.** Pinning
> `lineterminator` removes the **line-ending** source of byte difference and only that one.
> Byte identity of a committed CSV also depends on how the installed `pandas` and `numpy`
> render floats to text, and on the values themselves — and this repository measured its own
> two containers producing values that differ at the 16th significant figure, traced to
> OpenBLAS reduction order (`results/window_sweep/window_sweep_summary.md`), which is recorded
> in this same log. So the repository already held the counterexample to its own claim when the
> claim was written. Across environments the defensible statement is **value identity to
> within last-bit floating-point difference**; **byte** identity is a separate and stronger
> claim and is now scoped to the pinned environment in `DATA_AVAILABILITY.md` and
> `docs/verify_masked_panels.md`. The entry above is left standing as the record of what was
> done and thought on 2026-09-14; this note is the current interpretation.

### A misleading error message, found by running the reproduction check rather than writing it

Testing STEP 4b of the handoff on a deliberately incomplete tree surfaced a small defect of
its own: when the **primary** district-season panel was absent, `--per-unit` printed a
recovery command naming the **masked** export directory — it used the same message for either
panel. A reader following it would have gone after the wrong file. The message now names which
panel is missing, states that both are committed so a miss means an incomplete checkout, and
gives the correct rebuild path for that specific panel. Worth recording because it is the
third defect today found by executing something rather than reading it.

**Changed files.** `python/lf_output.py` (new); the 22 modules that write CSV (one import line
each); `python/make_figures.py`, `python/attrition_diagnostics.py`,
`python/orbit_agreement.py`, `python/permutation_test.py` (JSON newline pinned);
`python/mask_sensitivity.py` (also: the missing-panel message);
`run_all.sh` (roster 17 → 18); `README.md`; `DATA_AVAILABILITY.md`;
`docs/verify_masked_panels.md`; `analysis/deviation_log.md`; `analysis/decisions_log.md`.


---

## 2026-09-14 (seventh pass) — the headline precision figure carried its provenance in 1 of 7 places

Raised by an external reviewer while assessing Paper 2's positioning against Paper 1, and
**verified by sweeping the repository rather than taken on report**: the reviewer noted that
the **±1.3 d** district-season precision "comes from simulation under measured district-level
noise; it is not field-validated accuracy". Correct, and the protocol's §3 lead-in says exactly
that. But the sweep found the figure stated in **seven** places and carrying its provenance in
**one** — `README.md`, two further sites in `docs/Protocol_v1.md`,
`analysis/hypothesis_verdicts.md`, `REAUDIT_BRIEF_2026-09-14.md` and
`analysis/test_classification.md` all state it bare.

**Why this one matters more than the others found this week.** ±1.3 d is the number the
paper's surviving positive contribution rests on, and bare it reads as measured accuracy
against a field observation. **No field-observed transplanting or harvest date exists for any
district-season in this panel** (§3.4, and `docs/field_reference_sources.md` endorses calendar
sources for Odisha only). The honest statement is *simulated precision under measured noise* —
a Monte Carlo at the district-mean sampling noise of **0.122 dB** — and it is now attached at
every one of the seven sites. This is the fourth propagation failure found in three days, and
the pattern is identical each time: a qualifier is written once, in the place it was derived,
and the number travels without it.

**Also corrected in passing:** `analysis/hypothesis_verdicts.md` still said σ ≈ 26 d was
"confirmed by two" methods. §3.5 of the re-audit brief withdrew "confirmed"/"independent" for
that pair on 2026-09-14 because both routes read the same panel through the same estimator;
this site kept the old word and now reads "corroborated".

**Impact on the hypotheses.** None. No number changes. What changes is that the study's
headline measurement claim is stated at the strength the evidence supports wherever it appears.

**Changed files.** `README.md`; `docs/Protocol_v1.md`; `analysis/hypothesis_verdicts.md`;
`REAUDIT_BRIEF_2026-09-14.md`; `analysis/test_classification.md`;
`analysis/deviation_log.md`.


---

## 2026-09-14 (eighth pass) — the LF gate caught a module I did not know existed, because I tested it against my working copy again

**The gate worked. The patch did not.** `python/lf_output.py`'s self-test scans every sibling
module and fails if one calls `.to_csv(` without importing the guard. Run in the actual
repository it **failed**, and it was right to: `python/build_coastal_districts.py` is tracked at
`f585325`, calls `to_csv`, and does not import the guard. It writes
`docs/coastal_districts_gadm41.csv` and `docs/coastal_districts_crosswalk.csv`, both committed,
so it is squarely inside the defect the guard exists to close and must not be exempted.

**Why I did not catch it.** The module is **absent from this session's working copy** — 26
Python files on both sides, but mine has `lf_output.py` and lacks
`build_coastal_districts.py`. So my pre-ship run of the gate scanned 25 of the repository's 26
modules and passed. **I built a gate whose whole purpose is to scan the committed source set,
and then validated it against a directory that is not the committed source set.** That is the
fourth time in three days that a claim was tested against this environment instead of against
`git ls-files`, and the third time an external party found it.

**Standing rule, strengthened.** The existing rule was: any claim that an input *exists* is
checked against `git ls-files`. It is now: **any check whose scope is "all files of kind X in
the repository" must be run against the committed file list, and any patch must be diffed
against `git ls-files` for the parent commit before it ships.** The second half is what would
have caught this: the file list comparison takes one command and I had already used it, twice,
for other purposes in the same session.

### A second defect, found because the first one was reported well

The executor reported `FAIL` and could not say what failed: `run_all.sh` printed `tail -4` of a
failing self-test, and `lf_output.py`'s failures are early in its output, so the tail showed
only the closing banner. The executor was left reporting a failure with no diagnosis, and the
round trip cost a patch cycle. Two fixes, both general rather than specific to this module:

* `run_all.sh` now prints **every `[FAIL]` line** of a failing module, then three lines of tail.
* `lf_output.py` **restates its failed checks at the very end**, so even a tail-only view names
  them.

Verified by simulation: with the offending module present, a runner's last six lines now read
`SELF-TEST FAILED -- 2 check(s)` followed by both failures, naming
`build_coastal_districts.py` explicitly.

**Impact on the hypotheses.** None. No number changes.

**Blocked on.** `python/build_coastal_districts.py` is not in this working copy, so the one-line
guard import cannot be written here. It has been requested from the repository. Nothing else in
the patch depends on it.


### The same audit found three more, and one of them is the fifth instance of this week's pattern

1. **`docs/verify_masked_panels.md` contradicted itself, thirty lines apart.** The scope note
   added earlier that day says row counts, pixel totals and nesting are consistency checks and
   **cannot** show how a panel was built. Check 3's expected-output paragraph still ended
   "…or built by averaging pixels instead of fitting the mean curve, would not reproduce those
   three constants". That is the withdrawn claim, restated below the withdrawal. Corrected.
   **This is the fifth time in three days** that a correction was written in one place and the
   claim it corrects was left standing nearby — after the hypothesis verdict (six files), the
   AICRP citation, the semivariance wording and the ±1.3 d qualifier. The pattern is now so
   consistent that it is a process fact, not a series of slips: **writing a correction does not
   remove the thing corrected, and only a sweep by meaning does.**

2. **The module count was wrong wherever it was written.** "22 CSV-writing modules" came from
   this working copy, which lacks `build_coastal_districts.py`; the real figure is one higher,
   and the call-site count is correspondingly low. Rather than restate a corrected number, the
   count is now **removed from prose entirely**: `scan()` derives it from the directory and the
   self-test prints it. A number that can go stale in documentation is what produced this
   defect, and `lf_output.py`'s docstring now says so in terms — NEVER HARDCODE THE COUNT.
   The counts quoted in the sixth-pass entry above are left standing as the dated record of
   what was believed then, with this note as the correction.

3. **Schema debris in the committed tables.** With `--withdrawn-comparison` off, the main
   per-unit tables still emitted `primary_did_minus_withdrawn_pixelavg` and
   `intersection_did_minus_withdrawn_pixelavg` as **all-NaN columns** — 39 columns where 37
   carry data. Harmless to the numbers and exactly the kind of thing a reader must waste time
   ruling out. The delta columns are now emitted only when the comparison was computed; the
   three main tables are regenerated at 37 columns and their md5s change again.

**Also confirmed by that audit, and worth recording as a pass:** the three per-unit tables
regenerate **byte-identically on Windows** now that `lf_output` pins LF — the platform defect
that prompted the guard is closed on the platform that exposed it. And `make_figures.py` could
not start there for want of `matplotlib`; the runner classified that as **ERROR — could not
start**, not FAIL, which is the distinction added on 2026-09-13 working as intended.


### Resolved, and one correction to my own report of it

`python/build_coastal_districts.py` was read **directly from the author's machine** through the
connected-folder bridge and verified against both identifiers the auditor supplied: git blob
`81a58d4e0a1f9a74f399d97c57ba63facee9ec5e` and SHA-256
`1BE20E…459A80F1`. Both match, and a copy sent separately by hand is byte-identical to the one
read from disk. The guard import is added after its `import pandas as pd`, in the same form as
the other modules; `lf_output.py --scan` now reports **clean** and all 18 self-tests pass.

**Correction to this log's own eighth-pass entry.** It said the script "writes
`docs/coastal_districts_gadm41.csv` and `docs/coastal_districts_crosswalk.csv`, both
committed". **Wrong, and I had no evidence for it** — I inferred two outputs from two
similarly-named committed files without having read the script. It contains exactly **one**
`to_csv`, at line 130, writing `coastal_districts_gadm41.csv` into the GADM directory. The
auditor corrected this from the file itself. Nothing about the defect or the fix changes; what
changes is that a claim I made from filename similarity is withdrawn. `docs/coastal_districts_crosswalk.csv`
has no writer anywhere in `python/`, which is an open provenance question recorded here rather
than guessed at a second time.


---

## 2026-09-14 (ninth pass) — patch18d is committed as `d6278e8`, and the last wording defect is closed

**The push is verified, not accepted on report.** All 44 files were re-hashed as git blobs and
compared against `git ls-files` at `d6278e8`: **44 of 44 byte-identical** to what was shipped,
234 tracked (225 + 9), no drift on any of the other 190 files, `HANDOFF.md` and
`COMMIT_MESSAGE.txt` absent, and `run_all.sh` still mode 100755. The executor installed the
pinned requirements in an isolated environment after asking — the handoff's "do not install"
rule exists to stop silent environment changes, and asking first is the behaviour it was
written to produce. It also recorded that the runtime was Python 3.12.14 where
`requirements.txt`'s comment says 3.11.15; that mismatch is noted for a later pass.

### The remaining overclaims in `docs/verify_masked_panels.md` were real, all four of them

The auditor held that checks 1–3 still "overstate what counts establish", and was right on
every count. The corrected statement of what those checks do:

* They **cannot** establish **sample identity.** A different set of 8,085 cohort points
  reproduces the same totals and the same nesting. The earlier wording said they rule out a
  panel "built over the wrong sample" — they do not.
* They **cannot** establish the **stage** at which masking occurred. Nothing in a count does.
* The "closes the loop from committed mask flags, through the committed district panels, to the
  committed result tables" paragraph claimed the whole chain; only the half **downstream of the
  panels** is closed.
* The closing line said "the district-level half of §3.5 … is reproducible from the repository
  alone", broader than this document's own opening scope sentence, which it therefore
  contradicted. Corrected to: the per-unit **calculation** is reproducible; the **panels** are
  not.

**This is the sixth instance in four days of a correction written in one place while the claim
it corrects stands in another** — and the second inside this one file. The first narrowing of
this document did not go far enough and an auditor had to say so twice.

### Rather than only soften the words, a stronger check was added

`mask_flag_all.csv` is committed, and it carries the flag per cohort point. Grouping it by
district reproduces the `n_pixels` of all three committed panels **district by district**:
**25 districts × 3 panels = 75 constraints, 0 mismatches**, and `n_pixels` is constant across
the nine seasons in all 25 districts of each panel. That is now **check 3b**. It pins the
mask's spatial distribution rather than only its total, replacing 3 global constants with 75.

It is still a **count** check and the document says so: a permutation of members within a
district would survive it, and no check available from the committed files can establish sample
identity without the raw exports. The scope sentence is unchanged and is now consistent
everywhere in the file:

> The per-unit calculation is reproducible from the committed fitted district panels;
> reconstructing those panels still requires the archived raw exports.

**Impact on the hypotheses.** None. No number changes; one document is corrected and one
verification check is added.


---

## 2026-09-14 (tenth pass) — Paper 2 positioned against Paper 1; two priority claims tested or withdrawn

Written after the analysis was complete and after the patch series closed at `fc5eadb`. Nothing
in §1.1–§1.4, §2 or §3's thresholds changes; no estimate changes. What changes is how the
finished study is described, and two claims that were never checked.

### The overlap was real, and the working title was the sharpest form of it

Paper 2's frozen working title reads "A peak-relative non-parametric **quality-control framework
for cyclone-impact** rice phenometric extraction…". The submitted Paper 1 (RSASE-D-26-02830,
second submission, 4 September 2026 — read from the PDF, not from a plan, and not the rejected
first submission RSASE-D-26-01669) is titled "…**a reproducible quality-control framework for
cyclone-impact** case studies". Same claim, nearly the same words, same authors, overlapping
region and seasons. The working title is **withdrawn**; §1.5 of the protocol is the positioning
of record and proposes a replacement.

**The positioning is not "different sensor, different scale".** It is that Paper 1 names this
gap itself. Three sentences from its submitted text: the sensitivity checks "do not … prove that
the retained panel is **free of measurement error**"; "Independent MODIS, **Sentinel-1**,
calendar, or field **validation is not contained** in the supplied corrected outputs"; and
"**Independent reference validation remains necessary** before general accuracy claims." Paper 2
takes up the second by name, using a **between-orbit repeat measurement** the optical design
structurally cannot perform — under monsoon cloud there is no second independent look, which is
why Paper 1's own §3.4 removed HLS as a validation substrate.

§1.5.2 discloses the genuine overlap rather than minimising it: eight of the 25 districts, six of
the nine seasons, three of the six cyclones, the compositing window matched to Paper 1's adopted
extension, the Whittaker–GCV smoother inherited from it, Paper 1's Model 2 regression structure,
its working discipline, and the same authors.

### Priority claim 1: TESTED, and FALSE

§3's lead-in claimed "No published Sentinel-1 rice-phenology study we could find reports a marker
timing uncertainty in days at all … so this measurement is a contribution of the paper."
**Withdrawn.** A literature check on 2026-09-14 found at least three counter-examples: Manago et
al. (2020, *Agriculture* 10(12):625), transplanting-date SD ≈ 5–6 d against farmer-interview
dates; Wang et al. (2022, *Sustainability* 14(13):8009), 3.08 d average error against field
measurement; Zhao et al. (2024, MARC, *ESSD* 16:3893), bias, MAE and RMSE in days. The search of
record, including the two ScienceDirect papers that **could not be retrieved** (HTTP 429/400) and
were therefore not assessed, is in §1.5.5. The incompleteness does not affect the withdrawal —
one counter-example refutes a negative claim and three were found.

**What survives is a scope statement.** Those studies report *accuracy against an external
reference at site or irrigation-block scale in one region*; this study reports *between-orbit
repeatability at 30 m pixel scale across 25 districts, three states and nine seasons*, with a
district-scale figure alongside so the two scales are comparable within one estimator.

**And a discrepancy that must be defended, not buried:** Manago's 5–6 d and Wang's 3.08 d are far
below this study's σ ≈ 26 d. The likely reason is the unit of analysis — irrigation blocks and
field sites against 30 m pixels, managed irrigation against smallholder monsoon rice — and this
study's own district-scale figure is of their order. Recorded in §1.5.5 as an open item for the
Discussion, to be tested rather than asserted.

### Priority claim 2: NOT tested, therefore WITHDRAWN

The sweep for conflicting claims found a second one of identical form in §3.3: "No published
Sentinel-1 cyclone-flood study we could find reports such a matched-null test at all." It has
**not** been checked. After the first one turned out false, an unchecked priority claim is
withdrawn rather than repeated. The matched-null result stands on its own evidence. §1.5.5 now
sets the rule: a priority statement requires a recorded search first.

### Corrections to earlier entries in this log and in `analysis/decisions_log.md`

Append-only, so the originals stand and these are the notes against them:

* `analysis/decisions_log.md` around the 2026-09-12 radar-parameter entry ("No published
  Sentinel-1 … measurement is a contribution of the paper, not a defect of it") — **superseded**
  by the withdrawal above.
* `analysis/deviation_log.md`'s §3.3 entry ("No published Sentinel-1 cyclone-flood study we could
  find reports a matched-null test") — **priority framing withdrawn** as above.
* `analysis/decisions_log.md`'s §3.5 entry "The mask choice does not move a single unit's estimate
  materially" — **withdrawn** by the fourth-pass entry of 2026-09-14; the corrected figures are
  mean −7.39 / −0.67 / −1.59 d with signs agreeing 31/35, 22/35, 21/35.

### Six framing constraints now bind every manuscript section

Listed in §1.5.6, each traceable to a result here: simulated precision is not field-validated
accuracy; σ ≈ 26 d is corroborated, not independently validated; per-unit mask stability is
withdrawn; cyclone contrasts are descriptive and occupy a secondary section; reproducibility is
stated at its true scope (the calculation, not the panels); calendar plausibility is Odisha-only
with no AICRP attribution.

**Impact on the hypotheses.** None. The objectives, the five hypotheses and their verdicts stand
exactly as recorded, failures included. §1.5 is explicitly marked post-analysis and is placed at
the end of §1 rather than rewritten into §1.1, so the original scope and the later reframing are
both visible.

**Changed files.** `docs/Protocol_v1.md` (title note, new §1.5, §3 priority claim withdrawn at
source, §3.3 priority framing withdrawn); `analysis/deviation_log.md`.


### Reviewer corrections to the 2026-09-14 positioning proposal — all six accepted, all six verified

The positioning proposal was reviewed before any commit, and six corrections came back. **Each
was checked against the committed output rather than accepted on report; all six hold.**

**1. The precision ratio and the "scale boundary" are withdrawn.** The proposal divided an
*observed* pixel-scale between-orbit disagreement by a *simulated* district-scale precision and
called the result "roughly twenty times more precise", then called the pair a "measured scale
boundary". That is not a matched comparison: it neither establishes that district-season timing is
reliable nor locates where reliability begins. Both are removed. The two figures are now reported
**separately**, with the statement that a scale claim would need comparable uncertainty
assessments at both scales — a district-scale repeat measurement, which this study does not have.
**The same overclaim existed independently in §4.2.3** ("That boundary, located and quantified, is
the finding") and is narrowed there too, as is `README.md`'s heading "The instrument's working
level is located and quantified".

**2. Paper 2 does not supply the validation Paper 1 lacks.** The proposal said Paper 2 "takes up
the second of those three by name". Paper 1's limitation concerns validating *its own optical*
SOS/POS/EOS; Paper 2 evaluates *radar breakpoints*, which §3 states are not those quantities, and
does so with **no field reference**. Replaced with: Paper 2 **addresses a related measurement
question left unexplored by Paper 1; it does not validate Paper 1's phenometric accuracy.** The
categorical "a question the optical design structurally cannot pose" is likewise replaced by a
statement about **these datasets over this coast in these seasons** — with a different cloud
regime or a denser optical record the question could be posed optically.

**3. The repeatability denominator and the marker-specific values were wrong. Verified from
`results/orbit_agreement/run_full.log`.** The committed log reads: "pixel-seasons with a usable
orbit pair: 8515"; "8515/90000 = 9.5%"; the tolerance is fixed on the 2017 baseline at n=798; and
every reported statistic runs at **n = 7,717** (= 8,515 − 798). Per-marker σ: **trough 25.90 d,
heading 19.82 d, harvest 25.79 d**. So "σ ≈ 26 d over 8,515 paired pixel-seasons" was wrong twice
— the denominator is 7,717, and **heading is 19.82 d, materially better than the other two**. The
9.5% selection is now disclosed wherever σ appears, with the qualification that pixels failing on
one orbit are not represented in it.

**4. Disagreement is not the same as measurement error.** σ is computed as **sd(difference)/√2**,
which `orbit_agreement.py`'s own docstring states assumes "two independent measurements of one
quantity each carry sigma". Different look direction, incidence angle and revisit make that
plausible but do not establish it; a shared error component would make σ overstate the independent
part. σ is now described as an **error-scale estimate under stated assumptions**, and every report
of it must carry the **directly observed** disagreement alongside — sd of the difference, the
within-one- and within-two-dekad shares (38.2% and 55.6% on trough), and the bias.

**5. The literature generalisation was false of MARC.** The proposal said all three cited studies
report accuracy "at site or irrigation-block scale, on small managed samples, in one region". MARC
is a **monsoon-Asia product on a 0.5° grid** validated against a census calendar and 40 literature
site records — continental, not a small managed sample. The generalisation was drawn from the two
field-referenced studies and wrongly extended to the third. Rewritten as a distinction between
**measurands** — agreement with an external reference (accuracy) versus disagreement between two
observations by one estimator along different paths (repeatability) — with the explicit statement
that **MARC's 27.62 / 28.32 d RMSE must not be set beside this study's σ as though they measured
the same thing**. Also recorded: the Manago and Wang figures were read from abstracts during the
2026-09-14 check and have **not** been re-verified against full texts; the reviewer's own retrieval
was blocked by the publisher.

**6. The MARC and falsifiability conclusions were too broad. Verified from
`results/marc/Table_SX_MARC_Summary.csv`.** The harvest offset is **mean +50.35 d across 25
districts, range +26.19 to +60.54 d** — the mean is not each district's offset, and every earlier
statement of "+50.4 d in all 25 districts" is imprecise; what holds everywhere is *positive and
above +26 d*. **And the transplanting comparison is weaker than the harvest one and was not
separated out: mean +20.2 d, range −16.9 to +37.9 d — it changes sign across districts.** So the
conclusion is **marker-specific**: a strong warning against reading the harvest breakpoint as an
agronomic harvest date, a weak and directionally inconsistent signal on transplanting, and no
definitive agronomic identity or non-identity for every marker. The falsifiability result is
likewise bounded to **this estimator and this design** — a five-segment piecewise-linear fit to a
whole-season radar trajectory with district-level exposure — and is **not** a demonstrated failure
of radar-breakpoint exposure designs as a class.

**Title.** The author's preferred provisional title is adopted: *Between-orbit repeatability and
interpretation limits of Sentinel-1 rice phenology breakpoints along the Bay of Bengal coast.* It
is also the right choice on the evidence, because both earlier candidates led with **scale
dependence** and correction 1 removes the scale claim.

**What is unchanged from the proposal:** the dated post-analysis framing of §1.5, the placement at
the end of §1, the full overlap disclosure, and the withdrawal of both unsupported priority claims.

**Impact on the hypotheses.** None. No estimate changes. Several figures become more precise and
three claims become narrower.

**Changed files.** `docs/Protocol_v1.md` (§1.5.3–§1.5.7 rewritten, §4.2.3 narrowed, the MARC figure
made precise at §4.2.6); `README.md` (finding 2 heading and figures); `analysis/deviation_log.md`.


### Reviewer corrections, third pass — one of them a real mathematical error of mine

**1. The shared-error explanation had the direction backwards. Verified by simulation before
accepting.** §1.5.6 constraint 2(a) said a shared error component "would make σ an overestimate of
the independent part". The algebra is

> Var(e₁ − e₂) / 2 = [Var(e₁) + Var(e₂)] / 2 − Cov(e₁, e₂)

so a positive covariance makes sd(difference)/√2 **smaller** than the average total error, not
larger: a component shared by both orbits **cancels in the subtraction** and is not measured, and
a systematic bias common to both is **invisible**. Checked numerically on 400,000 draws: with a
shared component of sd 25 d and independent parts of sd 5 d the estimator returns **5.0 d**
against an average total error of **25.5 d**; a shared +12 d bias leaves σ unchanged. With
**unequal** variances and zero covariance it estimates the **average** of the two variances, not
either orbit's own.

**This was an error in the direction that flatters the study**, and correcting it makes the
paper's position more conservative, not less: **σ is a lower bound on a single orbit's total
error wherever the two paths share error** — and they plausibly do, sharing estimator, smoothing
decisions, dekad grid and crop state. σ must never be called "the measurement error" of a marker.

*A separate fact that points the other way is now stated beside it, because a reader will
otherwise see a contradiction:* σ is measured between two **single-orbit** fits while the
committed panel composites **all** orbits, so σ **overstates the committed panel's** error — the
estimator mismatch already recorded in `orbit_agreement.py`'s `dispersion_single_orbit` docstring.
That is about number of looks, not covariance. Both hold: σ is a lower bound on a single orbit's
total error and an upper bound on the composited panel's.

**No calculation changes.** The three σ values, the counts and every downstream number stand.

**2. The central research question promised the finding the revision had just withdrawn.**
§1.5.3 asked "at what spatial scale is a Sentinel-1 seasonal breakpoint a reliable measurement at
all" while §1.5.4 item 1 states the study cannot locate that boundary. Replaced with a question
the assembled evidence answers: **"How consistently are Sentinel-1 seasonal breakpoints recovered
across relative orbits, and what limits their interpretation as agronomic dates and as
cyclone-response outcomes?"** Consistency across orbits is measured; the interpretation limits are
measured against MARC and against §3.9's placebo.

**3. "A timing claim is not supportable" was too broad.** Replaced with: the selected paired
sample shows substantial between-orbit disagreement, which **limits fine-resolution timing
applications under this estimator and this sampling design** — explicitly not ruling out every
pixel-level application and not establishing an instrument-wide limitation of Sentinel-1.

**4. Two wording corrections, both about implying accuracy where only consistency is measured.**
Heading's 19.82 d is now **"smaller observed between-orbit disagreement"** rather than "materially
better", which could be read as closer to an agronomic truth. And −5.63 d is the **mean signed
between-orbit difference** rather than a "bias", because neither orbit is ground truth and the
sign describes one path relative to the other.

A sweep confirms neither the withdrawn scale question nor the reversed covariance statement
appears anywhere else in the repository.

**Changed files.** `docs/Protocol_v1.md` (§1.5.3 question, §1.5.4 item 1, §1.5.6 constraint 2);
`analysis/deviation_log.md`.


### Fourth-pass reviewer corrections — two of my mathematical claims were wrong, both verified by counterexample

The reviewer supplied exact counterexamples; both were **reproduced by simulation here before
being accepted**, and both hold.

**1. σ is NOT a lower bound on each individual orbit's error.** The third-pass text said it was
"a lower bound on a single orbit's total error wherever the two paths share error". With
**unequal** variances σ can exceed the *better* orbit's total error even when the covariance is
positive. Counterexample: shared component sd 1, independent residuals sd 3 and sd 10, so
Cov = 1 > 0; the difference-based scale is √((9+100)/2) = **7.38 d** while orbit 1's total error
sd is √(1+9) = **3.16 d**. Reproduced at 2,000,000 draws: σ̂ = 7.42, sd(e₁) = 3.16. What σ bounds
below, when covariance is non-negative, is the **quadratic mean of the two total errors** — not
either orbit's.

**2. σ is NOT an upper bound on the combined-orbit panel's error, and the code comment that was
my source is corrected too.** The third-pass text called it a fact that σ "overstates the
committed panel's error", citing number of looks. Using the very model the same paragraph relied
on — shared sd 25, independent sd 5 each — σ is **5.0 d** while an equal-weight two-orbit average
carries √(625 + 25/2) = **25.25 d**. Reproduced: 5.00 against 25.27. **Averaging reduces the
independent part and does not remove a common component**, and the pipeline does not average date
estimates at all — it fits a nonlinear breakpoint model to composited observations, which supplies
no ordering in either direction.

`python/orbit_agreement.py`'s `dispersion_single_orbit` docstring carried the same inference and
is corrected: the **estimator-mismatch warning stands** — the two quantities are not
interchangeable, which is why that function exists — but the conclusion that σ overstates the
composite is **withdrawn**. A negative variance subtraction establishes that two estimates or
their assumptions are **incompatible**, not which is larger. No code behaviour changes; this is a
comment.

**The protocol now claims neither bound.** §1.5.6 constraint 2(a) states the identity, what it
licenses under zero covariance and under equal variances, what positive covariance does, and that
an identical additive component — including a shared systematic bias — cancels and is unmeasured.
It adds that these are **population relationships under stated assumptions, not measured bounds on
unknown errors**, and that reading σ as "the average independent error variance" needs an explicit
**common-additive-component model with independent residuals**, which is an assumption about these
orbits rather than a consequence of the algebra.

**3. The broad pixel-timing claim survived in two more places.** §1.5.4 item 4 still said "a
timing claim is not supportable" and §4.2.3's own third-pass note said "the evidence will not
carry a timing claim", while item 1 had already been qualified. Both now carry the same
qualification: **in the selected paired sample, between-orbit disagreement at a single 30 m pixel
is substantial enough to limit fine-resolution timing applications under this estimator and this
sampling design** — not ruling out every pixel-level application, not an instrument-wide
limitation, and not establishing district-season reliability.

**4. The §3 lead-in reintroduced two claims §1.5 had withdrawn.** The replacement written when the
priority claim was withdrawn still described the cited studies as site-scale work "in one region"
— **false of MARC** — and still said the two scales "are comparable within one estimator" and that
"the contribution is that comparison". Both were corrected in §1.5 on later passes and left
standing in the paragraph that introduced them. **That is the seventh instance in five days of a
correction written in one place while the claim it corrects stood in another**, and it is the
reason the reviewer's insistence on auditing the full patch rather than the extracted section was
right: the standalone §1.5 file was clean and the patch was not.

**Impact on the hypotheses.** None. No estimate, table or figure changes. Four interpretive
claims are withdrawn or qualified and one code comment is corrected.

**Changed files.** `docs/Protocol_v1.md` (§1.5.4 item 4, §1.5.6 constraint 2, §3 lead-in, §4.2.3);
`python/orbit_agreement.py` (docstring only); `analysis/deviation_log.md`.

### Fifth-pass reviewer corrections — two carry-over interpretations, and a sweep that found four more

The fourth-pass audit closed all four of its own findings and then said plainly that this was
"not a blanket finding that every live statement elsewhere in the repository is now defensible".
It named two carry-over interpretations. A sweep of every tracked file for the same claims
restated in another shape found **six more live instances**, five of them in files the audit had
not opened — two of those in committed **code**. Nothing numerical changes in this pass; no
estimate, table or figure is touched, and no committed CSV column is renamed.

**A. The variance subtraction became established crop variation.** §4.2.3 read "**The estimator
is the cause** … Clause (b)'s substantive claim about the crop appears to be TRUE", its table
columns were headed "true within" and "true between", and `README.md` said a pixel's
transplanting date "genuinely varies 7.0 d". **All withdrawn.** The subtraction is conditional on
five assumptions, none tested here, and the third of them — that the two orbit paths' errors are
uncorrelated, so σ = sd(difference)/√2 is each path's error sd — is *exactly* what §1.5.6
constraint 2 was corrected on the fourth pass to stop asserting. The bound claims were withdrawn
in §1.5.6 and the calculation that consumes them was left standing three sections later.

**The fragility is worth recording because it is severe.** Implied within = √(within² − σ²) is a
small difference of two large numbers. Holding the published within, between and n̄ fixed and
varying σ alone: a σ **3.613470% above** 25.90 d drives the trough's implied within-variance to
zero *(corrected 2026-09-14, sixth pass: written "3.6%" here, and at exactly +3.6% the variance is
still positive at +0.187240 d²)*, and a σ **10% below** it lifts the harvest ratio to 1.079564 and
the heading ratio to 1.004115 —
above 1, reversing the reading. The sensitivity table is in §4.2.3. It is arithmetic on published
figures; no model was refitted. Note also the direction of the transport concern: σ is measured
where **both** orbits fitted, the dispersion where each pixel's **best-covered** orbit did, so if
that selection favours the lower-error path then σ overstates it and the implied ratio is biased
toward the conclusion the paragraph used to draw.

**B. Simulation became empirical signal identification.** §3's lead-in read "7.8 d — six times
the measurement error, so the year-to-year movement the difference-in-differences uses is
signal", and then "Per-pixel measurement error of this size is classical error in the
**outcome**: it inflates standard errors and does not bias the treatment coefficient." **Both
withdrawn.** ±1.3 d is a Monte Carlo under its own assumptions, not a matched empirical error
assessment, so the ratio separates nothing; and outcome error leaves the coefficient unbiased
only under independence from exposure and zero conditional mean, which §4.1's own censoring test
gives direct reason to doubt — the deformation that moves a fitted breakpoint months upstream is
driven by the same storm-season signal the exposure indicator marks.

**Six further live instances, found by sweep rather than by the audit:**

1. `python/extract_phenometrics_sar.py` carried the **priority claim that was tested and found
   false on 2026-09-14** — "no published Sentinel-1 rice-phenology study we could find reports a
   timing uncertainty in days at all … This measurement is a contribution" — still live in a
   committed code comment, a full day after the protocol's copy was withdrawn. Corrected, with
   the search of record cited.
2. The same file's item (3) carried "is signal by an order of magnitude over the measurement
   error". Narrowed on the same reasoning as B.
3. `python/orbit_agreement.py`'s module header said two orbits observing one pixel give two
   estimates of one quantity "**which separates them exactly**". They do not: the separation
   holds only under the error model now stated in §4.2.3.
4. The same file's `recheck_dispersion` **printed** "true within … true between … corrected
   ratio" on every run. The console labels now read *model-implied*. The CSV column names
   `within_true` / `between_true` / `ratio_corrected` are **deliberately left alone** so the
   committed `Table_SX_DispersionSingleOrbit.csv` stays byte-identical; a code comment says how
   to read them. Renaming them would change a committed result, which this pass must not do.
5. `analysis/hypothesis_verdicts.md` used the "true within / true between" labels even while, in
   the same section, correctly warning that the §4.2.3 sentence "claims more than the arithmetic
   supports". Relabelled, and the two assumptions it had not named are added.
6. `REAUDIT_BRIEF_2026-09-13.md` — a **tracked** document — still carried both claims: the
   section heading "H1/H2 fail on the instrument, not the phenology" and a closing sentence
   giving the scale boundary as "the study's positive contribution". It is a dated, superseded
   brief, so it is corrected **in place** with a note rather than rewritten.

**This is the eighth instance in six days of a correction written in one place while the claim it
corrects stood in another** — and the sharpest one yet, because the correction already existed in
this repository twice. `analysis/hypothesis_verdicts.md` wrote the classical-model qualification
on 2026-09-13 and said it "was missing from §4.2.3 and is mandatory". `analysis/decisions_log.md`
wrote, the same day, "§4.2.3 must say so." §4.2.3 did not say so for a further day, and
`README.md` never did. The lesson recorded after the seventh instance — that a phrase sweep does
not find a claim restated in another shape, and that reviewing an extracted section is not
reviewing the patch — now extends: **a correction is not applied until every file that consumes
the corrected quantity has been re-read, including code comments.** The `.py` files are not
documentation appendices; they were carrying a claim already known to be false.

**One further narrowing, not raised by the audit and flagged here for checking.** The
semivariogram nugget agreeing with σ within 0.8 d corroborates σ's **magnitude**. But the nugget
contains genuine field-to-field variation at short lag as well as measurement error, so it is an
**upper** bound on error — which cuts against the variance subtraction rather than for it. Stated
in §4.2.3 and `analysis/hypothesis_verdicts.md`.

> **WITHDRAWN 2026-09-14 (sixth pass).** I flagged this paragraph for checking and the check found
> it wrong. *Corrected 2026-09-14, sixth pass:** the short-lag semivariance bounds only the **spatially uncorrelated** error component from above, under an additive signal-independent model. It does **not** bound total error: error shared between neighbouring pixels cancels from the difference and is **missing** from the statistic. Simulated — shared sd 25 d plus independent sd 5 d gives a short-lag root of 5.0 d against a total error sd of 25.50 d. It is also the shortest interpretable **bin**, not a fitted zero-distance intercept So the further inference — that the agreement "cuts against the
> variance subtraction" — is **not established either**: the agreement is equally consistent with σ
> being mostly error and with it not being, and this diagnostic cannot separate the two. Flagging a
> claim for review is not a substitute for being right about it.

**Also corrected:** `python/orbit_agreement.py`'s `recheck_dispersion` docstring said a negative
within² − σ² "is impossible when both terms describe one estimator". Too absolute — two variance
estimates of one estimator can subtract to a negative through sampling uncertainty alone. It now
reads as incompatible point estimates under the assumed model. The estimator-mismatch warning and
the REFUSE-never-clip behaviour are unchanged.

### Corrections to earlier entries in this log and in `analysis/decisions_log.md` (fifth pass)

Append-only, so the originals stand and these are the notes against them:

* This log's **§3.8 register row** ("the year-to-year movement is signal by a factor of six over
  the measurement error") — **withdrawn** as in B above.
* This log's **§3.3 entry** ("No published Sentinel-1 cyclone-flood study we could find reports a
  matched-null test of this kind at all") — the priority framing was withdrawn in Protocol §3.3
  and in the tenth-pass entry above; the note is repeated here **against the entry itself**,
  since that is where the claim is read.
* `analysis/decisions_log.md`'s **2026-09-12 radar-parameter entry** ("No published Sentinel-1 …
  measurement is a contribution of the paper, not a defect of it", and "so the year-to-year
  movement … uses is signal") — **superseded**, priority half tested and false, signal half
  withdrawn.
* `analysis/decisions_log.md`'s **2026-09-13 semivariogram entry** ("The paper's positive
  contribution — that this instrument resolves district-season timing to about ±1.3 d while
  failing entirely at a 30 m pixel") — **withdrawn**: that is the scale-boundary claim retired on
  the fourth pass (§1.5.4 item 1), and ±1.3 d is simulated, not resolved.

**Impact on the hypotheses.** None. H1 and H2 remain failed as measured on the verdicts already
recorded; what is withdrawn is the interpretation that the failure was shown to be the
instrument's rather than the crop's. No estimate, table or figure changes.

**Changed files.** `docs/Protocol_v1.md` (§3 lead-in, §4.2.3 including the table header and a new
narrowing note); `README.md` (finding 2); `analysis/hypothesis_verdicts.md` (labels and two added
assumptions); `REAUDIT_BRIEF_2026-09-13.md` (§3.3 correction in place);
`python/orbit_agreement.py` (two comments and the console labels);
`python/extract_phenometrics_sar.py` (two comments); `analysis/decisions_log.md`;
`analysis/deviation_log.md`. **Eight files, all modifications; tracked count stays 234.** No
`results/` file is touched and no CSV column is renamed.

### Sixth-pass reviewer corrections — four findings, all four verified before acceptance, all four mine

patch20c was audited and refused. Four findings. Every one was checked against primary evidence
before being accepted — by simulation, or by recomputation from the committed file — and every one
holds. Three of the four were defects **introduced by patch20c itself**, in the pass whose whole
purpose was to correct overclaiming.

**1. The nugget "upper bound" was backwards.** patch20c added, in five places, that the
semivariogram nugget is an "upper bound on measurement error". **Withdrawn.** The short-lag
semivariance is a descriptive mixture of local variation in the true field and the **spatially
uncorrelated** part of the error. Under an additive signal-independent model it bounds *that
component* from above. It does **not** bound total measurement error, because error shared between
neighbouring pixels — orbit geometry, incidence angle, terrain, a district-season common mode —
cancels from the pixel difference and is **missing** from the statistic rather than contained in
it, and a constant bias cancels completely.

*Verified by simulation on 2026-09-14:* constant true field, district-season shared error sd 25 d,
independent error sd 5 d → short-lag root **5.006 d** (analytic 5.0) against a per-pixel total
error sd of **25.4951 d** (analytic). The statistic is five times **smaller** than total error. *(Corrected 2026-09-14, seventh pass: the figure quoted here was **26.81 d**, from a 200-replicate run at seed 20260914. The **analytic** value is **√(25²+5²) = 25.4951 d**, and that is what should be quoted. The shared component U enters once per replicate, so mean(e²) carries Var(U²)/nrep = 2·25⁴/nrep — a standard error of 62.5 d² at 200 replicates, about ±1.2 d on the reported sd. 26.81 d sits 1.1 standard errors high: ordinary Monte Carlo error in the shared draw, not a coding fault. Re-run at 2,000 / 20,000 / 200,000 replicates the figure is 25.79 / 25.77 / 25.60 d, converging slowly because U² is heavy-tailed. The short-lag root is stable at 5.000 d throughout, which is the number the argument actually rests on.)*
A second run confirmed the direction that does hold: with genuine local variation of sd 12 d and
independent error of sd 5 d, the short-lag root is 12.99 d, above the 5 d it bounds.

This is the same structural mistake as the σ-bound errors of the fourth pass, one level out: a
difference statistic is blind to whatever the difference cancels. I made it again a day after
writing that lesson down. `REAUDIT_BRIEF_2026-09-14.md` carried an even worse version — it said
the nugget "also contains … **any spatially correlated component of the measurement error**",
which is precisely inverted — and that was the **fourth** propagation failure inside the file whose
own §3.5 documents propagation failures.

**Also withdrawn: "established independently".** `analysis/hypothesis_verdicts.md` opened its
cross-check section "What *is* now established independently is the magnitude of σ", and
`semivariance.py` said agreement gives §4.2.3's ratios "an independent leg". Both routes read the
**same panel through the same breakpoint estimator**. The arithmetic differs; the evidence does
not. No wording in this repository may now call σ's magnitude independently established or
independently validated. `semivariance.py`'s docstring and its run-time print are corrected, and
its description of the nugget as "the intercept as h → 0" is corrected too — `nugget_and_sill()`
takes the **shortest interpretable bin** and fits nothing.

**2. The sensitivity table was wrong in three ways.** Rebuilt from
`results/orbit_agreement/Table_SX_DispersionSingleOrbit.csv` (md5
`b9c5cb4cc878fcfa13150eaaafc6bcc7`) instead of from rounded prose. The fifth-pass version:

* reconstructed n̄ by **inverting the rounded published column**, getting 4.32–4.33 where the
  committed value is **4.326264768252045** — and I recorded the consistency of that inversion
  across three markers as a *check that the recovery was right*, when all three markers share one
  n̄ so the agreement was arithmetically guaranteed and tested nothing;
* **mislabelled its × 1.050 row as "+3.6%"**, so the harvest and heading entries printed there
  (0.235, 0.444) were the +5% values;
* printed the trough's +3.6% cell as **"undefined"** when the within-variance there is
  **+0.187240 d², positive** — implied within 0.432713 d, ratio 0.027814.

The zero crossing is at σ × **1.0361347003698465**, a **+3.613470%** increase, not 3.6%. Every row
is now generated from the committed file, and the × 1.000 row reproduces the committed
`within_true`, `between_true` and `ratio_corrected` **bit-for-bit** — the check the fifth pass
lacked. Positive, exactly zero and negative are kept as three distinct states.

**The substantive fragility conclusion survives**: at σ × 0.900 the harvest and heading
model-implied ratios are 1.079564 and 1.004115, above 1 on both the committed factor and the
corrected one (1.175869 and 1.069545).

**3. The live program messages still stated the withdrawn conclusion.** patch20c corrected a
docstring and left `recheck_dispersion`'s `note` strings untouched — and those are **printed on
every run and written into the committed CSV**: "below 1 once error is removed: clause (b) failed
on noise", "real variation exceeds between-pixel spread", and on a negative subtraction "sigma and
the dispersion still do not describe one estimator". The third contradicted patch20c's own
docstring correction two screens above it, which had just conceded that sampling uncertainty alone
can produce a negative subtraction. All three are now conditional.

**The consequence is declared, not hidden.** Correcting the strings means a fresh run writes a
different `note` column, so **the committed CSV is no longer byte-reproducible from the current
code — in that one text column and nowhere else**. All nine numeric fields in all three rows are
identical. The committed file is md5 `b9c5cb4cc878fcfa13150eaaafc6bcc7` (803 bytes); what the
corrected code would write is md5 `5e2eb89ba78142b10b225d89281a23b8` (947 bytes). Replacing
committed evidence is **proposed for approval, not done**: the file is unchanged in this patch and
the divergence is documented in the new
`results/orbit_agreement/README_DispersionSingleOrbit.md`, which also marks `within_true`,
`between_true` and `ratio_corrected` as legacy labels meaning *model-implied*.

**4. σ²/mean(nᵢ) is the wrong factor, and the whole subtraction is downgraded.** The code subtracts
σ²/mean(nᵢ) from the variance of *equally weighted* pixel means. For independent equal-variance
errors, one pixel mean carries σ²/nᵢ, so the average contribution is **σ²·mean(1/nᵢ)**. The counts
here are unbalanced — **6,602 pixels carrying two to nine** retained seasons (2:1,385 · 3:1,176 ·
4:1,145 · 5:1,084 · 6:869 · 7:586 · 8:265 · 9:92, summing to 28,562 pixel-seasons and reproducing
the committed n̄ exactly, which is how the audit's distribution was verified here) — so
**1/mean(nᵢ) = 0.23114628** against **mean(1/nᵢ) = 0.28164872**, a **21.85%** understatement of the
error removed, always in that direction by Jensen's inequality. Substituting the correct factor
moves the model-implied ratios from 0.4413 / 0.7240 / 0.7239 to 0.4742 / 0.8269 / 0.7936 — toward
1 on all three markers, the same direction as every other correction in this sequence.

And substituting it still would not be right: the residuals are **district-year centred** before
the pixel means are formed, which induces covariance between them.

**The decision, and it is the bounded one.** The formula is **left unchanged** so the committed
table stays reproducible, and the whole subtraction is relabelled an **illustrative plug-in
approximation** — not a validated decomposition, not licensed by assumptions (i)–(v), not evidence
about genuine crop timing, and **not in the manuscript**. No new analysis is invented to rescue it.
An exact treatment would need uncertainty propagation matched to the actual unbalanced, centred
estimator on top of the untested error and selection assumptions; that work is not needed for this
paper and is not claimed.

**What this pass does not close.** Three of these four defects were introduced by the immediately
preceding correction pass, and the first of them repeated, one level out, a mistake whose lesson
had been written down the day before. The reviewing discipline that catches these is external
audit against primary evidence, not my own sweep: my patch20c sweep found six instances the audit
had missed, and the audit then found four the sweep had introduced or missed. Neither alone is
sufficient.

**Impact on the hypotheses.** None. No estimate, table or figure changes; no `results/` file is
modified. H1 and H2 remain failed as measured.

### Corrections to earlier entries in this log and in `analysis/decisions_log.md` (sixth pass)

* This log's fifth-pass entry, "One further narrowing, not raised by the audit and flagged here for
  checking" — **withdrawn**; the check found it wrong, and flagging a claim for review is not a
  substitute for being right about it.
* This log's re-audit entry §5 ("the nugget is an upper bound on structure-free error, containing
  … any spatially correlated error component") — the trailing clause is **inverted** and is noted
  in place.
* `analysis/decisions_log.md`'s 2026-09-13 semivariogram entry — the γ(h) identity is the
  idealisation, not the computation (shortest bin, no intercept fitted); "by an independent route"
  is **withdrawn**.
* All fifth-pass statements of "3.6%" — **corrected to +3.613470%** wherever they appear.

**Changed files.** `docs/Protocol_v1.md`; `README.md`; `analysis/hypothesis_verdicts.md`;
`REAUDIT_BRIEF_2026-09-13.md`; `REAUDIT_BRIEF_2026-09-14.md`; `python/orbit_agreement.py`;
`python/semivariance.py`; `analysis/decisions_log.md`; `analysis/deviation_log.md`; and one
addition, `results/orbit_agreement/README_DispersionSingleOrbit.md`. **Ten files: nine
modifications and one addition; tracked count 234 → 235.** No `results/` data file is modified and
no CSV column is renamed.

### Seventh-pass reviewer corrections — the variance subtraction is retired, and the code is rewritten rather than annotated

The patch20d audit verified the four patch20c corrections, the archive md5, all 18 self-tests and
the proposed 947-byte CSV, and then found that the propagation was still incomplete. Eight
instructions followed. The substantive one is the first, and it changes what this repository
claims rather than how it words a claim.

**1. The variance subtraction is retired as an active analysis.** Not relabelled, not repaired
with `mean(1/nᵢ)`, not rebuilt with a matched propagation. It is no longer computed, written to
any table, or reported anywhere in the active result set, and it does not enter the manuscript.
The reasoning is short: the manuscript does not use it, its error model is untested, its
between-pixel factor is wrong under unbalanced season counts, the residuals are district-year
centred in a way the subtraction ignores, and the result was fragile to a few per cent in σ.
Building the matched propagation would be a new analysis in service of a calculation nothing
depends on. **The dated calculation, every defect found in it, and this decision are preserved in
the historical logs** — this one and `analysis/decisions_log.md` — and nowhere else.

What replaces it is observed: single-orbit `within` 26.836301 / 27.213362 / 21.322590 d,
`between` 20.210418 / 17.254319 / 14.455730 d, observed ratios **1.327845 / 1.577191 /
1.475027** on 6,602 pixels and 28,562 pixel-seasons, all above the declared criterion of 1 and
close to the committed panel's 1.340 and 1.508. So **clause (b) failed as measured**, the failure
is **not** an artefact of the estimator mismatch, and **why it failed is not identified**. That is
the finding.

> **Narrowed 2026-09-14 (eighth pass).** "Not an artefact of the estimator mismatch" is
> itself a causal statement and is withdrawn. The single-orbit sample is **selected
> separately** from the paired sample, so the correct report is only that **all three ratios
> remain above 1 in that separately selected sample**, alongside the committed panel's 1.340
> and 1.508. No statement about why clause (b) failed follows.

**2. `python/orbit_agreement.py` is rewritten, not annotated.** The audit's point was that
patch20c and patch20d corrected docstrings while the module's live statements stood. Removed
outright, not struck through: "sigma is the right error"; "The cause was an estimator mismatch";
the dry-run paragraph concluding "both causes appeared to be operating"; "error-corrected ratio";
"This table is the error decomposition"; and the two-candidate framing that implied the script
separates estimator noise from crop variation. `recheck_dispersion` is renamed
`single_orbit_dispersion`, since it no longer rechecks anything by correction. The run-time
output now says only that clause (b) failed as measured and that the evidence does not identify
why.

**3. `python/extract_phenometrics_sar.py` is in this patch, and patch20d had lost it.** patch20c
corrected it; patch20d's payload omitted the file, so applying patch20d alone would have silently
reverted those corrections. Both major comment blocks are swept. Removed: the false
literature-priority claim (tested and found false on 2026-09-14 — the withdrawal note that quoted
it is gone too, since the code carries current statements and the logs carry history); "classical
measurement error in the OUTCOME"; "does not bias the difference-in-differences coefficient";
"the year-to-year movement is signal by an order of magnitude"; and "The district-season panel is
unaffected". ±1.3 d is now described only as what it is — recovery of planted breakpoints on a
**synthetic** trajectory at an **assumed** 0.122 dB noise level, checked by `--selftest`, and not
a property of the real panel.

**4. `python/semivariance.py`: "a completely different route" and "corroborates" are gone.** The
short-lag spatial semivariance and the between-orbit statistic are **not the same estimand** — one
mixes local variation in the true field with the spatially uncorrelated part of the error, the
other cancels whatever the two paths share — so there is no reason in principle for them to agree
and their similarity here is a description of this dataset. Both read one panel through one
estimator; **neither validates the other**. No wording in this repository now calls σ's magnitude
corroborated, confirmed, independently established or independently validated.

**5. The live summaries are swept.** `analysis/hypothesis_verdicts.md`'s closing paragraph (it
said the instrument "resolves district-season timing" and "fails at a 30 m pixel", with σ
"corroborated by two independent routes"); `REAUDIT_BRIEF_2026-09-14.md`'s §3.5 heading and its
closing bullet (both still said "corroboration" and "an error scale");
`analysis/test_classification.md`'s "independently corroborated after the fact"; `README.md`'s
finding 2; and in `docs/Protocol_v1.md` the §4.2.3 title, §1.5.6 constraint 2(b), and "two
genuinely independent looks".

**6. The result artefacts are cleaned, with no observed value changed.**
`Table_SX_DispersionSingleOrbit.csv` is regenerated with `within_true`, `between_true`,
`ratio_corrected` and `note` removed; **every retained field is byte-identical to the committed
file**, checked cell by cell, and the writer is updated to match. `Table_SX_DispersionCorrected.csv`
is removed from the active set — a first-pass artefact of the retired subtraction, written by a
version of the script that no longer exists and read by nothing. `run_full.log` cannot be
regenerated without the raw exports, so it is **archived unchanged** to
`results/orbit_agreement/superseded_2026-09-14/` and labelled; it still prints the old wording and
is kept as dated evidence of what was run. `results/orbit_agreement/README_DispersionSingleOrbit.md`
records all of this.

**7. The simulation figure in the sixth-pass entry above was Monte Carlo noise, and is corrected
in place.** It reported a per-pixel total error sd of **26.81 d** where the analytic value is
**√(25²+5²) = 25.4951 d**. The shared component enters once per replicate, so mean(e²) carries
Var(U²)/nrep = 2·25⁴/nrep — a standard error of 62.5 d² at the 200 replicates used, about ±1.2 d
on the reported sd, and 26.81 d sits 1.1 standard errors high. Re-run at 2,000 / 20,000 / 200,000
replicates it gives 25.79 / 25.77 / 25.60 d, converging slowly because U² is heavy-tailed. The
**analytic value is quoted from now on**; the short-lag root is stable at 5.000 d throughout,
which is the number the argument rests on.

**8. The sweep was run over every tracked `.py`, `.md`, `.txt`, `.log` and `.csv`** — 201 files,
the complete tracked text set at `fc5eadb`, not the subset present in a working copy. Its output
accompanies the patch.

**What this pass says about the process.** Three of patch20c's six findings and three of
patch20d's four were introduced by the correction pass immediately before. The failure mode was
consistent: correct the explanation, leave the thing that does the claiming. A docstring is not
the output; a table's prose dictionary is not its columns; and a payload that omits a file
silently reverts it. The rule this adds: **when a claim is withdrawn, the code that emits it is
rewritten, the artefact that carries it is regenerated or archived, and the payload is checked
against the previous patch's file list.**

**Impact on the hypotheses.** None. H1 and H2 remain failed as measured on the verdicts already
recorded. No observed numerical value changes anywhere.

**Changed files.** `docs/Protocol_v1.md`; `README.md`; `analysis/hypothesis_verdicts.md`;
`analysis/test_classification.md`; `REAUDIT_BRIEF_2026-09-13.md`; `REAUDIT_BRIEF_2026-09-14.md`;
`python/orbit_agreement.py`; `python/extract_phenometrics_sar.py`; `python/semivariance.py`;
`analysis/decisions_log.md`; `analysis/deviation_log.md`;
`results/orbit_agreement/Table_SX_DispersionSingleOrbit.csv`; plus one addition
(`results/orbit_agreement/README_DispersionSingleOrbit.md`), one removal
(`results/orbit_agreement/Table_SX_DispersionCorrected.csv`) and one move
(`results/orbit_agreement/run_full.log` → `superseded_2026-09-14/`). Tracked count 234 → 234.

### Eighth-pass reviewer corrections — a cross-sensor construct-identity claim, and five wording defects that survived seven passes

The patch20e audit accepted the retirement of the variance subtraction and then found a
larger claim standing untouched behind it: **Paper 2 had been reading Paper 1's optical
attrition through its own radar breakpoint.** Six instructions followed.

**1. The cross-sensor construct-identity claim is withdrawn everywhere.** The claim, in its
strongest form: Paper 1's Gate B deleted nine of ten treated post-period district-years for
exceeding a 240-DOY SOS ceiling; the radar puts the end of the dark phase at DOY 245–265;
therefore "the ceiling sat below the **true onset**", it "deleted precisely the district-years
it was meant to bound", and Paper 1's missing treated support is "a mis-specified window, not
attrition".

**Every step after the first two is withdrawn.** Paper 2's `t1` is an onset of canopy
development in a VH/VV trajectory; Paper 1's SOS is an optical construct; §4.3.1 authorises
no identity between them, only direction. A breakpoint in one sensor cannot locate a true
agronomic onset, and without one there is nothing against which another sensor's bound can be
called too low. The study holds **no field reference** — that is stated in every other section
and was being quietly suspended here.

The replacement, used verbatim wherever the claim appeared: *Paper 1's optical calendar bounds
do not align with Paper 2's radar breakpoint distribution and would censor many radar
estimates if transferred across sensors. This demonstrates non-transferability between these
different measurands. It does not establish that Paper 1's optical SOS bound was
mis-specified, identify a true agronomic onset, or reinterpret Paper 1's support loss. Those
questions require analysis of Paper 1's own optical measurements or an independent field
reference.*

Corrected at: `docs/Protocol_v1.md` §3.2's Gate 2 amendment and the "And this settles a
question about Paper 1" paragraph that followed it, and §4.3.1's "40–60 days **too early**"
wording, which judges an optical bound by a radar distribution;
`python/extract_phenometrics_sar.py`'s PLSM block, where the code now carries **only** the
current interpretation, with the history in this log; `REAUDIT_BRIEF_2026-09-14.md`'s §3.6
"true onset" passage; and dated withdrawal notes placed **beside** the original text in this
log and in `analysis/decisions_log.md`, so the historical entries stand as the record without
being mistaken for the current reading.

**What this costs the paper, stated plainly:** one of its more quotable findings. It was a
claim about Paper 1 that Paper 2's data could not support, and it was in the protocol, the
code, a brief and both logs before anyone checked whether the two sensors measure the same
event. They do not.

**2. Five disagreement- and precision-wording defects.** "Paired-orbit measurement error
moves" → "the scaled between-orbit disagreement statistic changes". "The measured error is
reported" → "the observed disagreement is reported". The split-half comment "their
disagreement is measurement noise" → a scaled disagreement statistic, since whatever is common
to both halves cancels. §3.8's "the district-season mean marker **is precise to ±1.3 days**" →
a Monte Carlo on a synthetic season recovering its own planted breakpoints under an assumed
0.122 dB noise level. And `orbit_agreement.py`'s self-test comment "recovers a planted
measurement error" → "a planted **independent-noise scale** under this self-test's own equal,
uncorrelated model", which is what makes sd(difference)/√2 equal each path's scale *there* and
is not evidence the real orbit pair satisfies it.

**Two further sites the instruction did not name, found by sweep.** `python/make_figures.py`
carried the figure title "**A marker is precise at district level and imprecise at pixel
level**" — a measured-precision claim printed on a committed figure — now "Monte Carlo marker
recovery against assumed series noise: simulated, not a measured accuracy". And
`manuscript/README.md` still listed "the located measurement boundary: ±1.3 d … against σ ≈ 26
d" as the positive contribution, four days after that boundary was withdrawn.

**3. "Not an artefact of the estimator mismatch" is itself a causal statement, and is
narrowed.** Ruling out one candidate explanation is a claim about why clause (b) failed. The
single-orbit sample is moreover **selected separately** — each pixel's best-covered orbit —
from the paired sample the between-orbit statistic uses. What may be said is only that **all
three ratios remain above 1 in that separately selected sample**, reported beside the
committed panel's 1.340 and 1.508. Corrected in `README.md`, `docs/Protocol_v1.md` §4.2.3,
`analysis/hypothesis_verdicts.md`, `results/orbit_agreement/README_DispersionSingleOrbit.md`
and this log's seventh-pass entry.

**4. The package accounting was wrong.** patch20e's handoff said "117 committed `.csv`
files". The parent has **118**: 116 byte-identical, one modified by removing four derived
columns, and one deleted. The 14 supplied md5 values were correct; the count was not. Counting
after a deletion and quoting the post-deletion total as the pre-deletion one is a small error
of exactly the kind these audits keep finding, and it is recorded rather than quietly fixed.

**5. The data-availability status is corrected, and it had been understating the position.**
All **10** intended files are uploaded at **100%** to unpublished Zenodo draft **`22750338`**,
including `Paper2_raw_inputs_2017-2025.zip` (md5 `dd6c208a27ce86555fd34cd8f13a1b6c`) — the raw
exports `DATA_AVAILABILITY.md` describes as excluded. They are **uploaded, not released**:
**no DOI**, so no DOI may be cited and the archive may not be described as public. The replay
kit in the draft is pinned to `fc5eadb6292dfba945cf53c2b1f4eea9b8d75019` and **must be
refreshed after the final accepted commit**. `DATA_AVAILABILITY.md`'s *Archive* section and
Protocol §5.1 now say this; the Mendeley route is superseded. **No Zenodo record was created
or modified by this patch.**

**6. A repository-wide semantic sweep** for synonymous forms of "true onset", "Paper 1 was
mis-specified", "not attrition", "measurement error", "district precision" and "not an
artefact". Every surviving occurrence outside the dated logs is a quotation inside a
withdrawal note, a statement of an idealised model that the same paragraph then qualifies, or
an unrelated sense. The output accompanies the patch.

**Impact on the hypotheses.** None. No observed numerical value changes, and patch20e's
retirement of the variance subtraction stands; no replacement decomposition is introduced.

**Changed files.** `README.md`; `DATA_AVAILABILITY.md`; `REAUDIT_BRIEF_2026-09-14.md`;
`analysis/decisions_log.md`; `analysis/deviation_log.md`; `analysis/hypothesis_verdicts.md`;
`docs/Protocol_v1.md`; `manuscript/README.md`; `python/extract_phenometrics_sar.py`;
`python/make_figures.py`; `python/orbit_agreement.py`;
`results/orbit_agreement/README_DispersionSingleOrbit.md` — on top of everything patch20e
changed.

### Ninth-pass reviewer corrections — the figures were carrying claims the text had already withdrawn

The patch20f audit accepted the withdrawal of the cross-sensor claim and then made a point
that eight previous passes had missed: **a text sweep cannot read a PNG.** Every correction
since 2026-09-14 had been verified by grepping files, and the committed figures are binary.
Three of them were still printing claims this repository had retired days earlier, and
`make_figures.py --verify` reported PASSED throughout, because every input and every output
still matched its recorded hash. Source drift was outside what the manifest described.

**1. "40–60 days too early" is reworded wherever it survived.** The phrase judges Paper 1's
optical bounds against Paper 2's radar distribution, which is the same construct-identity move
the eighth pass withdrew, in a smaller form. What is now said everywhere: **the radar
breakpoint distribution lies later than the positions of Paper 1's optical bounds, so those
bounds are not transferable across these measurands.** The separation of roughly 40–60 days is
reported as a separation. Corrected in Protocol §3's lead-in and §3.2,
`analysis/test_classification.md` and `python/extract_phenometrics_sar.py`.

**2. Figure 3 said what the text had stopped saying.** Its overall title claimed a marker "is
precise at district level and imprecise at pixel level" and its left axis was labelled
"split-half σ of a **single measurement**". Neither panel supports a precision claim: the left
differences two half-series, which yields a **disagreement** — whatever is common to both
halves cancels and is invisible — and the right is a Monte Carlo recovering its own planted
breakpoints on a synthetic season at an assumed noise level. Now: overall title **"Observed
split-half disagreement and conditional Monte Carlo recovery"**, left axis **"scaled split-half
disagreement, sd(difference)/√2 (days)"**, right axis "s.d. of the recovered planted breakpoint
(days)", right panel titled "Monte Carlo on a synthetic season (assumed noise)". The section
comment is rewritten to say why the two panels are different kinds of quantity and that no
ratio between them is formed.

**3. The figures are rebuilt and were looked at.** Figures 3, 4 and 7 were redrawn and **all
seven PNGs and all seven PDFs were rendered and inspected visually**, not merely regenerated.
That caught two things a hash check could not: figure 3's two panel titles collided and
overflowed the canvas at the first attempt, and figure 4's new title ran to the edge — both
were shortened and redrawn. The four untouched figures are **byte-identical** to the parent.
`pdftotext` on all seven confirms no banned phrase survives in any text layer.

**4. The provenance manifest now hashes its own generator.** `figure_provenance.json` gains a
`generator` entry recording the LF-normalised md5 of `python/make_figures.py`, `--verify`
treats a mismatch as a failure, and `--selftest` proves it: a manifest naming this file's own
hash exits 0, one naming any other hash exits 1, and a manifest with **no** generator entry is
refused rather than passed silently. `.py` joins the LF-normalised extension set and the hash
policy is bumped to `text-lf-normalised-v2`, because a generator hash that flipped on a CRLF
checkout would reintroduce exactly the platform-dependent hash the policy exists to prevent.

**A capability the repository lacked, added because it was needed here.**
`results/phen_panel_sar.csv` is excluded on size, so fig2 cannot be drawn from a clone and a
full `make_figures.py` run is **impossible from this repository**. Correcting one title
therefore meant either running a pipeline a clone cannot run, or hand-editing the manifest into
something the committed code does not produce. Neither is acceptable. `--only fig3,fig4,fig7`
redraws a subset and merges into the existing manifest, **re-hashing from disk every entry it
did not touch and refusing the run if one has changed**, and records `partial_run` naming which
figures were redrawn and which inputs could not be checked. The output is deterministic:
re-running the same command reproduces the same bytes, verified.

**5. §3.10's terrain interpretation is narrowed to association.** "Retention is **governed by**
terrain and viewing geometry, **not by exposure**", "the screen rejects **terrain that cannot
be paddy**" and "the 35.3% pixel retention is **a measurement of the mask**" all name a cause.
What the data show is that retention is **associated** with elevation, slope and viewing
geometry in the fitted selection model and **not associated** with cyclone distance. The cause
cannot be separated among mask classification, signal quality, estimator behaviour and the
screening rule itself, and this study does not attempt to. Corrected in Protocol §3.10,
`python/extract_phenometrics_sar.py`, and figure 7, whose title now reads **"Observed
association: pixel retention falls monotonically with elevation and slope (cause not
identified)"**.

**6. `test_classification.md` no longer justifies the district headline by contrast.** The row
read "per-pixel σ ≈ 18 d **against** ±1.3 d on the district-season mean". The contrast is
removed: ±1.3 d is a **separate conditional simulation** and does not demonstrate the actual
precision of the district panel, for which this study holds no repeat measurement. The row now
reports the two observed quantities — a split-half disagreement of σ ≈ 18 d per pixel, and a
district-mean sampling se of 0.122 dB against 2.03 dB — and the paragraph below it, which used
to point at "the ±1.3 d figure in the row above", is amended rather than left dangling.

**7. Two smaller ones.** Protocol §3's "a Monte Carlo … returns 12–27 d **independently**" →
**separately**: the Monte Carlo reads the same estimator and the same assumed noise, so it is a
separate calculation, not an independent one. And figure 4's title read "**Heading date**",
naming the fitted quantity as the agronomic event; it now reads "Fitted heading-related
breakpoint (t2) — **NOT** an observed agronomic heading date", with the axis relabelled to
match.

**8. The sweep now includes figure text layers.** Twelve phrase families across every tracked
`.py .md .txt .log .csv .sh .js .json`, plus `pdftotext` on all seven committed PDFs. Every
surviving hit outside the dated logs is a quotation inside a withdrawal note. **All seven PDF
text layers are clean.**

**One item flagged rather than changed.** Figure 1's legend reads "breakpoints t1 onset, t2
heading, t3 drainage, t4 harvest". Those are this project's declared names for the breakpoints
and §4.3.1 governs their interpretation, but "t2 heading" in a legend is the same shape of
label figure 4 was just corrected for. It is **not** changed here, because the instruction
named figure 4 only and figure 1 is regenerable — the choice belongs to the reviewer, not to
this pass.

**Impact on the hypotheses.** None. No observed numerical value changes: 116 of the 118 tracked
CSVs at the parent are byte-identical, one loses four derived columns with every retained field
identical, one is deleted. Four figures are byte-identical; three are redrawn with identical
data and corrected labels.

**Changed files.** Everything patch20f changed, plus `python/make_figures.py`,
`figures/figure_provenance.json`, and the six files of figures 3, 4 and 7.

### Tenth-pass reviewer corrections — three of these were corrections of my own corrections

Six findings, every one verified directly before anything was changed. Three of them are the
**second half of a sentence whose first half a previous pass had already corrected**, which is
the sharpest form the recurring defect has taken yet.

**1. Protocol §3.2 still said Paper 1's windows are "40–60 days too early".** The ninth pass
added the non-transferability statement earlier in that same paragraph and left a **bolded
active sentence** three sentences later: "These are Paper 1's optical windows and they are
40–60 days too early for the radar season on this coast." It now reads: **the radar breakpoint
distribution is roughly 40–60 days later than the positions of those optical bounds in these
data**; because the measurands differ and neither is ground truth, that establishes
**non-transferability**, not that Paper 1's windows were incorrectly timed. A meaning-based
sweep found no other active instance — the remaining hits are quotations inside dated
withdrawals.

**2. Protocol §3.8's level-of-estimation paragraph is rewritten, and the reason for the
district headline is corrected.** It gave "per-pixel σ ≈ 18 d … while … ±1.3 days" as the
**reason** — the same contrast removed from `analysis/test_classification.md` on the ninth
pass and left standing here. The real reason is the **estimand**: §3.8's outcome is the
breakpoint fitted to the **district-mean curve**. The two measured quantities are now reported
separately, with neither establishing the precision of the real district panel.

**And the deeper correction: the two arms do not estimate identical quantities.** The paragraph
said "the two levels are directly comparable; what changes is residual variance, not the
cluster count." They share exposure assignment and district clustering, so the second clause is
kept — the cluster count is 25 either way. But **a breakpoint of the district-mean curve is not
an average of pixel breakpoints**: the PLSM fit is nonlinear in the breakpoints, so fitting an
averaged series and averaging fits are different operations with no general ordering. A
difference between the arms may reflect **aggregation and nonlinear fitting**, not residual
variance alone.

**3. §3.10's terrain result: a detected null became a proven absence, in the half of the
sentence the ninth pass did not reach.** The sentence ended "— and **every covariate that
drives it** is time-invariant per pixel, so it is absorbed by the fixed effects and **cannot
masquerade as an exposure effect**", with retention described as associated with cell
properties "**rather than with exposure**". "Every covariate that drives it" asserts the model
is complete; "cannot masquerade" converts a null coefficient into a proof. Everywhere — §3.10,
`extract_phenometrics_sar.py` and `make_figures.py` — the wording is now **"no association with
cyclone distance was detected in this fitted model"**, with an explicit paragraph stating that
this **does not establish the absence of exposure-related selection**.

**4. The documented partial command did not work, and I had been hiding that behind a flag.**

    python python/make_figures.py --only fig3,fig4,fig7 --out figures

died with a bare `FileNotFoundError`: the terrain table was built **before** `--only` was read,
and it was gated by `--skip-montecarlo` — a flag whose name says nothing about terrain, and
which I had been passing myself. Fixed properly: `--only` is parsed **first**; prerequisites are
built only for figures actually selected; in partial mode a committed derived input is
**reused only after its recorded hash is verified**, never rebuilt; and `--skip-montecarlo` and
the new `--skip-terrain-table` control one table each. Three new self-tests plant the exact
clean-clone situation — a results directory with the committed derived inputs and **no**
`phen_panel_sar.csv` — and assert that the command succeeds with no extra flag, and that a
**stale untouched input** and a **stale untouched output** are each **refused**.

**5. Figure 3's title collision is fixed.** Panel headings are now **"Observed split-half
disagreement"** and **"Conditional Monte Carlo recovery"**; the qualifications moved to a
caption under the figure. Rendered at journal width (491 pt) and inspected — the collision is
gone and the caption is legible.

**6. Figure 1's breakpoint labels are signal-defined.** The legend read "t1 onset, t2 heading,
t3 drainage, t4 harvest" — agronomic events. It now reads **"t1 end of dark phase, t2 end of
rise, t3 end of plateau, t4 end of fall"**, with a caption stating that the agronomic readings
are **interpretations, not field-validated dates**. *(This is the item the ninth pass flagged
and left to the reviewer; the reviewer took it.)*

**7. Byte-determinism claims are scoped.** The self-test saves one figure twice **in one
process on one machine**: that establishes determinism **within a pinned environment**, and
says nothing about another machine, where a different freetype or matplotlib can change the
bytes — and the **pixels**, which is a different claim again. Scoped in the module header, the
self-test output, `--verify`'s failure text, the manifest `note`, and the 2026-09-13 brief's
commit table.

**7b. The same conflation was live for the CSV tables, and the repository already held the
counterexample.** The repository-wide sweep item 7 asked for turned up a second, older
instance that the figure work had not touched: `DATA_AVAILABILITY.md` said **"Byte-identity
holds on every platform only because of `python/lf_output.py`"**, and
`docs/verify_masked_panels.md` said those md5s **"hold on any platform that writes LF"** and
that **"byte-identical on every platform" is now a property the build checks**. All three are
withdrawn. Pinning `lineterminator` removes the **line-ending** source of byte difference and
only that one; float-to-text rendering by the installed `pandas`/`numpy` and the values
themselves can still differ — and `results/window_sweep/window_sweep_summary.md`, recorded in
this same log, **measured** two of this project's own containers producing values that differ
at the 16th significant figure through OpenBLAS reduction order. The claim and its refutation
were sitting in the same repository. Across environments the defensible statement is now
**value identity to within last-bit floating-point difference**; **byte** identity is scoped to
the pinned environment. The 2026-09-14 log entry that introduced the overstatement keeps its
text and carries a dated correction note in place (see the note above at item 2 of that
entry).

**Verification.** All 18 self-tests pass (exit 0). The exact documented command runs from a
clean clone with no extra flag. Figures 1 and 3 redrawn and inspected; all seven PNGs and all
seven PDFs rendered and viewed; all seven PDF text layers scanned. No observed numerical value
changes.

**Still not closed, and named rather than buried.** Figures 5 and 6 still use the agronomic
marker names (`onset`, `heading`, `drainage`, `harvest`) as axis and legend text, because those
are the column names §3.8 and every results table use. §4.3.1 governs their interpretation and
figure 1 now carries the caveat explicitly, but the same relabelling has **not** been applied
to them — the instruction named figure 1, and applying it everywhere would rename the study's
outcome variables. Flagged for the reviewer, not taken.

**Changed files.** Everything patch20g changed, plus `REAUDIT_BRIEF_2026-09-13.md`,
`DATA_AVAILABILITY.md`, `docs/verify_masked_panels.md` (new to the payload in this pass) and
the figure-1 outputs; `python/make_figures.py` and `docs/Protocol_v1.md` change again.

## 2026-09-15 (eleventh pass) — three live interpretations corrected in executable strings and figure labels, and the pixel panel the figures are drawn from is replaced with a tested equivalent

Codex verified patch20h's archive, payload hashes, CSV accounting, numerical
invariance, 18 self-tests, partial rebuild, manifest verification and
generator-drift refusal, and then found three interpretations still live. All
three were reproduced here before anything was changed.

**1. A self-test told the operator the simulation chose the estimand.**
`extract_phenometrics_sar.py` printed, on every run, "every marker within 3 d of
truth **with sd under 5 d -- this is why the district-season panel is primary**".
That is the claim §3.8 was rewritten in patch20h to remove, still being printed
by the code. A second string a few lines down did the same thing in reverse,
calling the per-pixel spread "**the reason §3.8 estimates on districts**". Both
now state the conditional synthetic-recovery result and then say explicitly that
it does not measure the real district panel and does not determine the primary
estimand, which §3.8 fixes by declaration. **The test's numerical criteria are
unchanged** — still `|bias| < 3 d` and `sd < 5 d` on the planted breakpoints —
and the test still passes.

**2. A screen on trajectory shape was described as identifying rice.**
`plsm_retain`'s docstring said "The gate is separating pixels that **behave like
rice**", and the same sentence stood in §3.2's calibration narrative. It cannot:
the screen admits any pixel-season whose VH/VV trajectory satisfies the declared
shape, eligibility and rise criteria, and nothing in it distinguishes rice from
anything else that satisfies them. Both now say the gate separates pixel-seasons
satisfying the declared criteria and **does not establish crop identity**. The
retention calculation is untouched.

The same paragraph read the median breakpoints as "transplanting in early August,
heading in mid-October, harvest at the end of November". Those are agronomic
dates this study never observed. The positions are now reported as *consistent
with* the Sali calendar, which is a comparison of distributions. The withdrawal
note that follows that paragraph withdraws the **estimator** and had left both
claims standing; they are withdrawn in place.

**3. Figure labels named agronomic events the figures do not locate.** Display
labels are now signal-defined and come from one table, `DISPLAY_TERM` in
`make_figures.py`: t1 end of dark phase, t2 end of rise heading-related, t3 end
of plateau drainage-related, t4 end of fall harvest-related, and intervals
t1→t2, t2→t3, t1→t4. **No CSV column was renamed.** The columns are still
`trough`, `heading`, `drainage`, `harvest`, `veg_days`, `plateau_days`,
`season_days` in every table, every protocol section and every script; a display
label is not a data column, and renaming the columns would rename the study's
outcome variables.

Figure 5's caption now says the placebo requires the same season's **t1
breakpoint** unmoved. Figure 6's title said the storms "land in the rise phase,
**not at harvest**" — an inference about whether an agronomic harvest had
occurred, from the position of a fitted breakpoint. It now states only that they
**fall inside the fitted t1–t2 rise phase rather than the fitted post-t2 phase**,
and 'harvest window' is carried as the catalogue's label. The same inference was
live in `classify_exposure_phase.py`'s docstring — "**None is a harvest exposure
in the sense the label asserts**" — and is withdrawn there too.

**Found by rendering, not by reading.** The full display terms were tried on
figure 3's axes first and **collided**: four terms on a four-category axis
overlapped each other, and the right panel's end-of-line annotations ran off the
canvas. Figure 3 now carries `t1`–`t4` on the axes with the full terms glossed in
the caption — the same remedy patch20h applied to this figure's panel headings,
for the same reason. This is the second time a label change on this figure has
needed a render to catch.

**The pixel panel.** `results/phen_panel_sar.csv` is excluded on size, so
figure 2 could not be redrawn from the repository. The panel was located on the
author's machine, and the hash did **not** match what the manifest recorded:
`046d6029b3b131c5a06fb6ca9000d9ad` against a recorded
`d0559979df253232c623ba4084b710c5`. No file with the recorded hash exists
anywhere reachable. Rather than use the substitute and hope, a control run was
done first: a **full** `make_figures.py` at the **unchanged patch20h code**, with
the replayed panel as the only changed input, reproduced **all fourteen committed
figure files and both derived inputs byte-for-byte**. That is what licensed the
swap. `DATA_AVAILABILITY.md` records the change, the evidence and what it does
not establish — the two panels cannot be compared field by field, because only
one of them still exists.

**One standing limitation lifts.** A full figure rebuild is possible again when
the panel is present; it remains impossible from a clone alone.

**Verification.** All 18 self-tests pass. The documented partial command runs
from a clean clone with no extra flag. `--verify` reports 0 changed. Generator
drift, a missing generator entry, and stale untouched inputs and outputs are all
refused. Both derived inputs and figures 1 and 7 are byte-identical to patch20h;
figures 2, 3, 4, 5 and 6 changed, and every change is a label. **No observed
numerical value changed.**

**Live git state, confirmed today.** The device shell came back. `origin/main`
and `HEAD` both read `fc5eadb6292dfba945cf53c2b1f4eea9b8d75019` and the working
tree is clean. That closes a limitation carried since 8 September.

**Still not closed.** The attrition-diagnostic reporting gap (C1–C4, reproduced
independently by Codex) is **not** in this patch and is not fixed by it. It is a
separate workstream with its own specification.

## 2026-09-15 (twelfth pass) — five interpretation corrections, a semantic guard, the Figure 6 denominator, and §3.10's declared reporting rule finally executed

patch20i was rejected for revision. Six corrections were required and all six
were reproduced here before anything was changed.

**1. A self-test called a simulation a measurement.** It printed "in this
conditional simulation — **recorded as measured**". "Recorded as measured" is the
claim the whole eleventh pass removed, reintroduced three lines from where it was
removed. The string now says plainly that the number describes the simulation and
nothing else.

**A semantic guard now scans every module in `python/` on each run**, against
eight patterns in two families — estimand selection, and simulation as
measurement — and fails the build if any returns. It excludes its own block so
its pattern list does not trip it, and a companion case plants a violation to
prove the patterns are live. This is the third pass in a row to remove a claim of
this kind from an executable string; it is now the last one that can be removed
quietly.

**2. §3.2 attributed the retention loss to the mask.** "The loss measures the
mask, not the method" names one of four candidate causes as the answer, with
nothing separating them. Withdrawn in place; the text now says the cause cannot
be separated among mask classification, signal quality, estimator behaviour and
the screening rule. The same paragraph's "screening must be shown not to
correlate with exposure" is reworded to say the relationship must be **measured**,
and the paragraph now points at §4.0, where the diagnostics that **do** detect
associations are reported.

**3. Figure 6 counted records and called them storms.** `exposure_phase_storms.csv`
has one row per **district–storm exposure record**: one cyclone crossing several
districts contributes one row per district. The title read "14 of the 18
classifiable **storms**". There are **5** classifiable storms, not 18 — the title
overstated the storm count roughly threefold. Both denominators are now computed
and both are shown, records first. A self-test asserts they are computed
separately and genuinely differ, so they cannot be collapsed again.

**4. The provenance claim was narrower than what was run.** The eleventh pass
said the replayed panel's difference "does not touch anything this repository
derives from" it. The control run covered `make_figures.py` and nothing else —
`gate1_justification.py`, `gate2_state_sensitivity.py`, `marc_agreement.py`,
`mask_sensitivity.py` and `merge_static_covariates.py` all read that panel and
none was tested. Narrowed to exactly what was run: the replayed panel regenerates
the current derived tables and figure content. **Panel equivalence is not
established and cannot be**, because the `d0559979…` panel does not exist. The
old hash is preserved in `DATA_AVAILABILITY.md` and in a new `provenance_history`
field in the manifest.

**5. The manifest recorded one of seven things that move the bytes.** It recorded
`matplotlib` alone, then claimed byte reproducibility. It now records python,
platform, matplotlib, numpy, pillow, freetype and zlib, and carries a `scope`
field stating what it is for: **artifact integrity** — has a committed file
changed since these hashes were recorded — and distinguishing byte identity
(asserted only in the pinned environment) from pixel identity and content
equality (neither established by any hash). Dependencies are recorded, not
pinned, because this package ships no lockfile and cannot honestly promise
another environment will reproduce the bytes.

**6. §3.10's reporting rule had fired and nothing executed it.** Three separate
failures, each verified:

*The runner could not run the step at all.* `run_all.sh` cds into `python/` and
passed the exposure catalogue by bare filename; the file lives in `docs/`, so the
call raised `FileNotFoundError`. This is the same defect class an audit found in
three scripts on 2026-09-13 — which is why `_find_doc` exists — and this call site
was simply never routed through it.

*The mandatory balanced arm was never requested.* `--balanced` is off by default
and `run_all.sh` did not pass it. So the declared reproducible run emitted **no
balanced rows at all**: none at pixel level anywhere, and the district table's 132
rows came from a hand-run the pipeline did not reproduce, meaning **a rerun
silently deleted them**. Pixel is the level where four distinct diagnostics are
significant, including one at p_WCB 0.0010.

*Nothing checked any of it.* `python/attrition_completeness.py` is new: it writes
`Table_SX_AttritionTriggers.csv` at both levels and fails the run when a triggered
stratum lacks a required status, when a status is blank rather than an explicit
`not_estimable:<reason>`, when keys duplicate, or when the balanced block drops
below its recorded floor. Six self-tests, each by sabotage.

**Both levels were re-run at full bootstrap resolution with `--balanced`.**
District reproduced its committed table **exactly** — 253 strata, 0 differing
values across 4,807 fields, p_WCB included, so the bootstrap is seeded and
deterministic. Pixel reproduced all 176 pre-existing strata exactly and **added
132 balanced rows that had never been computed**, 110 estimated and 22 not
estimable.

**Reserialisation, reported rather than explained away.** Re-running rewrites the
tables with this environment's pandas, which formats floats and integer counts
differently from the version that wrote the committed files. Across every
byte-differing CSV: **13,948 fields identical as text, 3,533 equal in value with
a different text form, and 0 with a different value.** No number moved. The text
form of many did.

**Multiplicity is a sensitivity and never the gate.** The predeclared trigger is
raw p_WCB < 0.05 and is unchanged. Holm and BH-FDR are computed on **unique
regression signatures**, because `class:pre_season` and
`phase_attrition:S_phase_pre_window` are one regression under two names —
identical coefficient, standard error and p — and counting them twice inflates
the test count. Both are mapped back to every alias, and the conservative
all-11-labels calculation is carried alongside (district Holm 0.4367, BH 0.2376).

**The pooled class-level balanced estimator remains undefined, and none was
invented.** §3.10 item 3c restricts to units retained in both seasons *"of that
cyclone"* — per cyclone. At class level at least four pooled definitions are
available and item 3c explicitly rules out the fourth; the protocol picks none.
Recorded as a post-analysis implementation gap. The district **+5.001 d** trough
coefficient under severe harvest-window exposure is reported as **not
point-identified under differential attrition**, and the per-storm balanced rows
(+5.83 to +30.16 d) are stated to be five distinct seasonal samples, not a pooled
comparator.

**Live text updated.** `analysis/hypothesis_verdicts.md` did not contain the word
"attrition" at all; it now carries a full section. Protocol gains **§4.0**.
`README.md` gains an open-items entry. All three report the significant findings,
the declared not-point-identified language, the distance null **together with**
the exposure-indicator findings as different predictors in different models, and
the multiplicity sensitivity.

**Verification.** 19 self-tests pass in the candidate tree and in a clean clone
(18 plus the new checker). The documented partial command runs from a clean clone
with no extra flag and regenerates its six figures byte-identically. `--verify`
reports 0 changed. The completeness gate passes at both levels from a clean
clone. Only figure 6 changed; the other thirteen figure files are byte-identical
to patch20i. **Figure 5 is byte-identical even though its input table's hash
changed** — the values it plots did not move, only the file's serialisation,
which is exactly the byte-versus-content distinction the new `scope` field
states.

**Still not closed.** The pooled balanced estimator is undefined by the protocol
and is not invented here. No field reference exists anywhere. σ's error-model
conditions remain untested. The original pixel panel is gone and panel
equivalence cannot be established. Zenodo remains uploaded, unreleased, no DOI.


## 2026-09-15 (thirteenth pass) — patch20j was rejected on independent verification; ten defects, seven of them in the gate I had just written

patch20j shipped a completeness gate whose own docstring said it "checks the
EXACT KEY SET". It did not. An external auditor replaced a valid balanced key
with a unique FAKE key, left the row count at 132, and the gate returned PASS.
That is the single worst kind of defect this project can produce: a check that
reports success while the thing it claims to check is broken, which is more
dangerous than no check at all, because it stops anyone else from looking.

Every defect below was reproduced here before anything was changed.

**1. The gate counted rows and called it a key set.** Reproduced exactly: with
`balanced:trough:S_pre_season:FANI` renamed to `...:FAKEZZ` in both the final
and the partial table, 132 balanced rows present, the gate exited 0. The
expected key set is now CONSTRUCTED as an explicit cross-product — 11
phenometrics x 2 class exposure variables x 6 estimable cyclones = 132 — and
compared for EXACT EQUALITY. A missing key and an extra key are separate,
reported failures. The sabotage is now self-test case 1.

**2. Multiplicity deduplicated regressions by their OUTPUT STATISTICS.** Any two
strata whose coef, se, n and cluster counts matched to 12 significant figures
were merged into one "regression". That is unsound: identical rounded summaries
do not make two designs the same design, and merging them makes the adjustment
too lenient. Output-based deduplication is **removed**. One alias is hard-coded,
and only after its DESIGN identity was verified: `S_pre_season` and
`S_phase_pre_window` are **elementwise identical across all 225 district-seasons,
29 exposed in each**, checked against the panel and the exposure catalogue.
`--verify-aliases` re-runs that check against the live panel rather than trusting
the constant. A sabotage test plants two genuinely different regressions with
identical summaries and asserts they stay separate.

**3. The gate synthesised `not_estimable` out of nothing.** When no comparator
row existed it wrote `not_estimable:no_ipsw_row_for_this_stratum` and passed. A
missing row means the estimator WAS NEVER RUN. That is a completeness failure,
and calling it "not estimable" turns an unexecuted analysis into a reported
result. Absence now returns `NOT_RUN` and fails the gate; `not_estimable` is
accepted only from an executed row carrying status, reason and provenance.

**4. Mixed blocks collapsed to "available".** A block of 66 balanced rows with 55
estimated and 11 not estimable read as `available`. Every block now reports exact
counts — `available:55/66 estimated` — with the distinct reasons.

**5. `delta_beta` was never a composition sensitivity, and is retired.** The
balanced arm fits **two seasons**; the headline pools **all nine**. The
difference between them therefore changes the **time window** as well as the
**composition** and identifies neither. A valid composition sensitivity must hold
outcome, exposure definition, seasons, controls, fixed effects and inference
settings fixed and differ only in which units are included. No such estimator is
declared in this protocol and none is introduced now. The columns stay as a
record of what was computed, and every row of the trigger table carries the
retirement in a `delta_beta_interpretation` field.

**6. Per-cyclone ranges were being used as a pooled comparator.** They are
separate descriptive sensitivities on two-season sub-samples. For class-level
diagnostics the pooled balanced estimator is marked `not_defined`, and the
per-cyclone rows are reported in their own column.

**7. `not_estimable` and `not_defined` were run together.** They are different
answers. `not_defined` means the protocol specifies no such comparator, so none
was ever supposed to exist. `not_estimable` means one was attempted and could not
be computed. The estimand map now names, per diagnostic type, the comparator the
protocol actually defines: class to class-level headline and IPSW; cyclone to the
event-study estimates, which live in `Table_SX_EventStudy.csv` and not in this
table; phase to the phase unbalanced and phase IPSW estimates.

**8. THE PIXEL LEVEL HAD BEEN RUNNING AT A TENTH OF THE DECLARED BOOTSTRAP.**
`run_all.sh` read `boot=999; [ "$lvl" = district ] && boot=9999`. Protocol §3.8
and `attrition_diagnostics.py` both declare 9,999. So **every pixel WCB p-value,
every pixel confidence interval and every pixel inference in this package came
from 999 replications** while the protocol said 9,999. Both levels now run at
9,999, the whole pixel analysis has been re-run at 9,999 rather than reusing any
999-replication row, and `n_boot_requested` is recorded in every WCB row beside
`n_boot_ok` so the shortfall cannot recur unnoticed. The gate fails on any value
other than 9,999.

**The pixel p-values moved.** `class:pre_season` 0.0010 -> 0.0008;
`cyclone:FANI` 0.0040 -> 0.0012. Coefficients and standard errors do not depend
on the bootstrap and did not move. This is the correction working, not a defect,
and it is reported as a change rather than absorbed.

**9. Resume was machine-local and name-based.** The run key stored an ABSOLUTE
panel path and compared FILENAMES. Two consequences, both demonstrated: the same
bytes in another clone were REFUSED because the directory prefix differed, and an
EDITED file with the same name was ACCEPTED, so rows computed from different data
could splice in silently. The key is now schema 2: repository-relative logical
paths, LF-normalised content hashes for the panel, the exposure catalogue and the
phase-exposure table, a hash of the estimator source, and every option that can
change a number. A schema-1 key is refused outright rather than half-compared.
Four self-tests: same bytes in another clone resume; changed phase-exposure bytes
are refused; the estimator source is in the key; and `--balanced`, which selects
only WHICH strata are computed, is correctly absent from it.

**10. "No coefficient changed" was false.** patch20j compared fields under a
1e-12 tolerance and reported "0 fields with a different value". The auditor
measured **604 last-digit differences in the two final tables, maximum about
6e-15**, and the count is exactly reproduced here: 278 in the district table and
326 in the pixel table. They are real differences and my tolerance absorbed them.
Every claim of that shape is replaced by the measured truth: **no material change
within a stated relative tolerance of 1e-9**, with the last-digit count and the
largest observed difference given. The comparison now reports five categories
separately — identical text, same double with different text form, last-digit,
newly populated, and material — and never merges them.

**A defect I found while fixing 8 and 9.** `run_all.sh` could not run the
attrition step at all: it cds into `python/` and passed the exposure catalogue by
bare filename while the file lives in `docs/`, raising `FileNotFoundError` before
any flag was read. Fixed in patch20j's successor by routing that call site
through `_find_doc`, which exists for exactly this.

**What is preserved from patch20j unchanged.** Every verified figure and wording
correction: the signal-defined display terms, figures 1-7, the Figure 6
denominator fix, the semantic guard on executable strings, the §3.2 mask
withdrawal, the narrowed panel provenance, and the manifest's environment and
scope fields.

**The lesson, recorded because it is the third time.** A gate that has never been
seen to fail is not a gate. The patch20j checker had six self-tests and all six
passed, because each tested a case I had thought of. The auditor's FAKE-key test
took one line and defeated the module's headline claim. Sabotage tests now
accompany every check in this module, and the handoff asks the reviewer to run
one by hand rather than trust the suite.


## 2026-09-15 (fourteenth pass) — patch20k rejected; ten defects, and the gate had to be rebuilt to fail closed

patch20k's gate was the third version of the same module, and it was still
passing tables it should have refused. The pattern across all three is one thing:
**an unanticipated shape fell through to a default that meant "fine".** The
rewrite inverts that. Anything not explicitly recognised as valid now FAILS.

**1. The gate did not fail closed.** Five holes, each reproduced before it was
fixed: any status string was accepted; a `not_estimable` row with a blank reason
passed; a WCB estimate with no bootstrap count passed; duplicate keys were
checked only in the final table; a key present only in the partial table passed;
and the two tables were never compared row by row, so a field could disagree
between them silently. All six now fail, in both tables, with a named reason.

**2. Resume was described as something it is not.** `run_all.sh` called
`--resume` "safe and idempotent". That was never demonstrated and is not true:
the check recomputed **one** stratum — a single canary, which is consistent with
every other row in the partial table having come from somewhere else. Two
changes. Every attrition-diagnostic stratum is now recomputed and compared, not
one. And the comment says what the check does and does not establish: the
`twfe`-based families are **not** re-verified, so `--resume` is a convenience
with a sampled provenance check, not idempotence.

**The tables shipped with this package come from CLEAN runs with no `--resume`**,
at 9,999 replications, and the full command and log are preserved beside them.

**3. The cyclone comparator was scientifically wrong, and that is the serious
one.** patch20k mapped `cyclone:<NAME>` to the `balanced:*:*:<NAME>` rows as its
composition comparator. Those rows carry a coefficient on the **class** variable
(`S_pre_season` / `S_harvest_window`); the cyclone selects only the two-season
window. They are not a per-cyclone estimand and cannot compare with a per-cyclone
retention diagnostic. The real per-cyclone comparator is the **event study** in
`results/Table_SX_EventStudy.csv`, which was sitting in the repository unread —
42 rows, six cyclones plus POOLED, three outcomes, two terms each. It is now read
and mapped. Its **composition-restricted counterpart does not exist anywhere**,
so that comparator is reported `NOT_DEFINED`. The balanced rows are carried in
their own column as a descriptive sensitivity with a note saying exactly that.

**4. The alias check could be requested and skipped.** `--verify-aliases`
returned a three-valued result and a `None` printed as SKIP while the run still
exited 0. An unverified constant is precisely what the flag exists to prevent, so
an alias check that cannot run is now a FAILURE. The flag is also added to
`run_all.sh`, where `set -euo pipefail` means a nonzero exit stops the pipeline.

**5. The retired arm was still called primary.** §3.10 item 3b said the
balanced-composition check "becomes the primary robustness estimate". It is
retired and is not a robustness estimate at all: it fits **two seasons** against
a headline pooling **all nine**, so it changes the time window as well as the
composition. Struck through and replaced in place.

**6. The comparison totals were not reproducible.** patch20j and patch20k both
quoted totals — "0 fields with a different value", "1,018", "604" — computed by
scratch scripts that were thrown away. A number nobody else can recompute is not
evidence. `python/compare_tables.py` is now a committed module with its own
self-test: seven disjoint buckets that partition every field, an explicit `--tol`
reported in the output, `--scope final` to reproduce the audit's own 604, and an
assertion that the buckets sum to the number of fields compared.

**7. The trigger accounting was stated two ways.** "Six strata" in one place and
"five pixel and two district" in another. Both were counts of the same thing.
Stated one way everywhere now: **seven triggered output labels, six distinct
tested designs**, one pixel pair being a verified alias.

**8. Two stale counts and a word that overclaimed.** The self-test count is 18 in
two places and is now 19 (20 with `compare_tables.py`). And "pinned environment"
was wrong in six places: nothing is pinned — there is no lockfile and no
version-enforcement check anywhere in this package — so it is a **recorded test
environment**, recorded and not enforced, and the manifest's `scope` field says
so.

**9. `DATA_AVAILABILITY.md` implied more reproducibility than exists.** It said
"every committed figure was produced from the committed tables", which a reader
could take as a guarantee while one input is excluded. Replaced with a table
stating exactly what a clone can and cannot do: integrity of all 14 figure files
and 10 committed inputs, **yes**; redrawing fig3, fig4 and fig7 from committed
derived inputs, **yes**; redrawing **fig2**, **no**; rebuilding either derived
table, **no**; a full run, **no**.

**10. Every fix has a sabotage test.** Eleven cases in the gate, four in the
resume key, five in the comparison module, each planting a specific defect and
asserting a nonzero exit. The transcripts ship with the patch.

**What is preserved unchanged.** Every verified figure and wording correction
from patch20i, patch20j and patch20k.

**The recurring lesson, now at its fourth instance.** Each of the last four
packages passed its own checks and each had a defect the author had not thought
to test for. The checks are not the problem; the imagination of the person
writing them is. What helps is an adversary who tries shapes the author did not
consider, and every one of the ten items above came from that.

---

## 2026-09-16 — Codex correction and verification pass (in progress)

**Authority and scope.** The author asked Codex to implement the corrections,
with Claude reserved for later manuscript drafting. Work is isolated from the
clean canonical checkout at `fc5eadb`. No commit, push, deposit release or
manuscript submission has occurred in this pass.

**What changed and why.** Completeness/alias checks and event-study provenance
were tightened; retired composition contrasts are no longer regenerated. The
exposure verification gate was reproduced passing with an empty rebuild folder
because it compared a file with itself. It now requires a separate baseline and
an exact eight-output receipt. An actual NOAA/GADM rebuild matches the four
exposure definitions; footprint row order differs but values match by key.
The robustness driver defaulted to 999 bootstrap draws and is being rerun at
9,999, with explicit successful/requested counts. Incomplete inference is refused.
Filename-only orbit resume and a window-control comparison that missed nonfinite
changes are replaced by content checks and tested refusals. Runner dependency and
argument defects are corrected. These safeguards do not change the PLSM fitting
rule or provide new field evidence.

**Interpretation changes.** Permutation quantiles relative to 1.96 do not test
wild-bootstrap calibration or distinguish spatial confounding from estimator
behaviour. Those claims are withdrawn wherever active, including figure 5.
The spatial permutation is conditional on unverified within-state exchangeability.
The stale per-unit mask summary is corrected to 31/35, 22/35 and 21/35 sign
agreement in the declared named-event block. Window persistence is confined to
the tested endpoints, not an exclusion of all design explanations. Terrain means
are not strictly monotonic in elevation, and naive error bars do not account
for spatial dependence.

**Post-analysis sensitivities.** Repeat-coverage, state baseline tolerances and
three orbit-pair selection rules are additional class-C checks, not replacements
for frozen pooled H1/H2 criteria. Their numerical results and limits are recorded
in Protocol §4.4 and the associated tables/receipt. Literature searching is dated
2026-09-16 and supports no first-study claim.

**Affected sections.** Protocol §§1.5, 3.8–3.10, 4.1.7 and 4.4; implementation,
runner, current summaries and affected figures. Original log entries remain
historical. `analysis/current_audit_status.md` distinguishes completed work from
pending reruns and is not an acceptance certificate.

**Hypothesis impact and new commitment.** Do not change hypotheses to make
them pass. H1/H2's tested pooled clauses, H3's construct limitation, H4's result
and H5's untested status must remain distinct. Any inference-table changes from
correcting the bootstrap resolution will be reported explicitly. Final manuscript
approval waits for completed clean runs, final comparisons, contradictory-claim
review and portable reproduction checks. Absence of field validation and causal
identification will remain stated limitations, not be declared fixed by wording.

---

## 2026-09-16 — final Codex acceptance replay and drafting green signal

**Independent execution.** The pixel attrition analysis was run cleanly, without
resume, at 9,999 bootstrap draws and produced 308/308 expected strata. The
district clean replay produced 253/253. Both final/partial pairs agree field by
field, both contain all 132 declared balanced keys, and live verification confirms
the one design alias on all 225 district-seasons. Five deliberately malformed
external copies and the registered sabotage cases fail closed.

**Numerical comparison.** Removing only the two retired columns preserves every
key. All retained coefficient, standard-error, test-statistic and count fields
agree within 1e-9. One underpowered, non-triggering WCB value moves by exactly one
bootstrap draw relative to the preceding candidate (`cyclone:REMAL`, 0.7134 to
0.7135). A separate clean, targeted execution of that stratum returns 0.7135.
The accepted value is therefore 0.7135; no trigger, adjusted result or scientific
verdict changes.

**A newly detected output-propagation defect.** The source of
`results/placebo_check.log` had been corrected, but the committed transcript still
printed the withdrawn agronomic-date wording because `.log` files were outside
the semantic scan. The log was regenerated at 9,999 draws. The guard now scans
logs, refuses invalid UTF-8 and U+FFFD replacement characters, and passes 24
planted claim/encoding sabotages. Six damaged section signs in the four-hour
pixel console capture were repaired one-for-one after verifying every occurrence
was a `§1.1`, `§3.8`, `§3.9` or `§3.10` marker; no number or statement changed.
A separate district replay produced byte-identical tables and a clean UTF-8 log.

**Scope of the signal.** The repository is green for manuscript and supplement
drafting only. It is not yet green for commit, public release or submission. The
paper remains a bounded repeatability-and-interpretation study: it supplies no
field accuracy validation and no causal cyclone-effect estimate. Public GitHub,
a matching released Zenodo DOI, final manuscript QA and author confirmation are
later gates.
