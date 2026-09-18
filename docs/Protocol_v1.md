# Protocol v1 — RiceBaCI-QC (Paper 2)

> Release correction, 2026-09-17: `../RELEASE_NOTES_2026-09-17.md` governs the
> historical Monte Carlo wording throughout this append-and-correct document.
> The old common ±1.3 d summary is not supported by the archived table. The
> current 0.122 dB, 80-draw t1/t2/t3/t4 standard deviations are
> 0.00/0.00/2.18/1.90 d, conditional on one on-grid synthetic trajectory;
> they do not estimate empirical district-panel precision. No result changed.

**Title:** A peak-relative non-parametric quality-control framework for cyclone-impact rice phenometric extraction in smallholder coastal systems of the Bay of Bengal.

> **WITHDRAWN 2026-09-14 as the working title.** It duplicates the framing of the submitted Paper 1 ("a reproducible quality-control framework for cyclone-impact case studies"), by the same authors on an overlapping region and seasons. The title is left standing here as the record of what the protocol was frozen under; **§1.5 is the positioning of record** and records the adopted provisional replacement. No objective, hypothesis or threshold changes with it.

**Authors:**
- Supranab Panda (corresponding author) — Center for Environment and Climate, Institute of Technical Education and Research, Siksha 'O' Anusandhan (Deemed to be) University, Bhubaneswar 751030, Odisha, India. `pandasupranab@gmail.com`
- Sarat Chandra Sahu (supervisor, co-author) — Center for Environment and Climate, Institute of Technical Education and Research, Siksha 'O' Anusandhan (Deemed to be) University, Bhubaneswar 751030, Odisha, India (Director, CEC).

**Version:** v1 — first frozen protocol for the full multi-state, multi-cyclone scope.
**Date locked:** 2026-09-07.
**Commit hash:** `2cf493a` — the freezing commit for §3's QC thresholds and hypotheses on `main`. These two lines were filled by the next commit, which cannot contain its own hash; `2cf493a` remains the freeze point of record, and every later change is logged in `analysis/deviation_log.md`.
**File path:** `docs/Protocol_v1.md` in `github.com/pandasupranab/RiceBaCI-QC`.

**Discipline note.** The QC thresholds, hypothesis definitions, and analytical decisions in this document are fixed **before** the full multi-state extraction is run. Any change after that point must be recorded — with date, rationale, and affected hypotheses — in `analysis/deviation_log.md` as an append-only entry. This is the same discipline used successfully for Paper 1's Odisha analysis; it is what defends the Gate-1 thresholds against a "you tuned this after seeing the data" critique.

---

## 1. Scope

### 1.1 Cyclones and years

Seven Bay of Bengal cyclones with landfalls in the study region, spanning 2018–2024 (Titli added 2026-09-09 with the extension of the panel floor to 2017, §1.2):

| Cyclone | Landfall date | Landfall coast | Analysis year | Severe roster districts | Event-level status |
|---|---|---|---|---|---|
| Titli | 11 Oct 2018 | Palasa, Andhra Pradesh | 2018 | 6 | estimable (reference 2017) |
| Fani | 3 May 2019 | Puri, Odisha | 2019 | 17 | estimable (reference 2018) |
| Bulbul | 9 Nov 2019 | Sagar Island, West Bengal / coastal Bangladesh | 2019 | 2 | estimable, underpowered |
| Amphan | 20 May 2020 | Bakkhali, West Bengal | 2020 | 5 | estimable, pre-period Fani-exposed |
| Yaas | 26 May 2021 | Balasore, Odisha | 2021 | 5 | estimable |
| Sitrang | 24 Oct 2022 | Barisal, Bangladesh (fringe impact on WB) | 2022 | 0 | not estimable |
| Remal | 26 May 2024 | Sagar Island / Mongla, WB / Bangladesh | 2024 | 2 | estimable, underpowered |

Each district × season is one panel cell (pixel-year observations within it, §3.8); the named cyclones label the severe events, and exposure is assigned from the full storm catalogue as defined below. The final column records, per event, whether §3.8 B's event-level stack can be estimated at all, and is stated here rather than discovered during analysis: Sitrang exposes no roster district; Bulbul and Remal have two treated districts each, which is too few to support a causal claim and are reported descriptively (§3.8 B); all five of Amphan's treated districts carry severe Fani exposure in the preceding season, so its *k* = −1 reference is contaminated and that contamination is reported with the coefficient. Titli's six severe districts are Cuttack, Gajapati, Ganjam, Nayagarh, Srikakulam and Vizianagaram.

**Exposure, treatment and controls (revised 2026-09-07; supersedes both the "same-district t ± 1, t ± 2 control years" rule and a stacked-clean-control wording drafted earlier the same day).** Treatment in Objective 4 is not assigned by hand from the table above. It is derived, before any phenology is extracted, from the full IBTrACS v04r01 North-Indian-basin catalogue by a fixed rule implemented in `python/build_cyclone_exposure.py` and committed as `docs/district_cyclone_exposure_ibtracs50km.csv`:

- A roster district is *exposed* to a storm in season *t* if its GADM v4.1 Level-2 polygon lies within 50 km of any segment of that storm's best track at which the IMD sustained wind (IBTrACS `WMO_WIND`; JTWC `USA_WIND` only where IMD is missing) is ≥ 34 kt — Paper 1's 50-km exposure buffer (RSASE-D-26-02830 §2.3), computed in EPSG:7755. Exposure is *severe* if that wind is ≥ 48 kt (IMD Severe Cyclonic Storm or stronger) and *minor* at 34–47 kt (IMD Cyclonic Storm).
- Each exposure carries a *timing class* from the month of the track segment carrying the district's maximum wind within 50 km (`maxwind_fix_month`): *pre-season* (April–July: disturbs land preparation and transplanting), *mid-season* (August–September) or *harvest window* (October–February of the following calendar year: disturbs maturation and harvest).
- The district × season exposure indicators used in §3.8 are the maxima over all catalogued storms in that season, so every district-season carries an exposure status and nothing is assumed untreated. Recomputed 2026-09-09 for the 25-district roster (§1.3) and seasons 2017–2025 (225 district-seasons), the catalogue gives **29 severe pre-season, 18 severe harvest-window and no severe mid-season** district-season exposures — 45 distinct district-seasons carrying severe exposure, from nine storms (Titli 2018, Fani and Bulbul 2019, Amphan 2020, Yaas 2021, Michaung 2023, Dana and Remal 2024, Montha 2025) — and **21 district-seasons with minor exposure only** (Daye and Phethai 2018, Nivar 2020, Gulab 2021, Asani 2022, Michaung 2023 in one district, and two unnamed cyclonic storms of August 2022 and October 2025). Three storms outside the seven named in the table above carry severe exposure to roster districts: Michaung 2023 (one district, after the §1.3 exclusions), Dana 2024 and Montha 2025. The remaining catalogued storms carry minor exposure only. Season 2017 carries no exposure of any severity in any roster district and is the panel's untreated baseline season.
- The named cyclones in the table are the severe events with Indian landfall on this coast that motivated the study; the six estimable events are the units of the event-level view (§3.8 B) and of the §4 sign table. The full exposure catalogue is the computational source for footprint and clean-control membership. `docs/cyclone_footprints_ibtracs50km.csv` is an older six-cyclone audit table (Fani, Bulbul, Amphan, Yaas, Sitrang and Remal); it predates Titli entering when the panel floor moved to 2017. `python/event_study.py` derives every stack from the full catalogue, verifies that derivation against the audit table for the five estimable events it contains, and then applies the same rule to Titli. A clean control has no severe exposure to any catalogued storm in seasons t − 1, t or t + 1; same-storm fringe districts are excluded. Under this rule **Sitrang** (24 Oct 2022, landfall at Barisal, Bangladesh) exposes no roster district — its ≥ 34-kt track stays more than 50 km from every Indian roster polygon — and is therefore **not estimable as a treatment for this roster**; it remains in the table as a named event and is excluded from the H4 count (§2). Fani and Bulbul both fall in analysis year 2019, so Bulbul's two footprint districts (North and South 24 Parganas) also carry severe pre-season exposure from Fani; the exposure panel handles this additively, and the event-level view flags every footprint district that has severe exposure to a different storm in t − 1, t or t + 1 (Fani 8 of 17, Bulbul 2 of 2, Amphan 5 of 5, Yaas 0, Remal 0; Titli is computed directly from the 2017–2025 exposure catalogue; §3.8 B).

**Analysis seasons (revised 2026-09-09; was Sentinel-2 seasons 2019–2025).** Seasons **2017–2025**, nine seasons (`CONFIG.years` in `gee/S2_QC_Ingest.js`; the 2025 season closes at the end of February 2026 and is complete). Remal's t + 1 season is 2025; no event window extends beyond the data. The floor moves from 2019 to 2017 because the phenometric substrate moves from Sentinel-2 to Sentinel-1, which has no equivalent start-date constraint — see §1.2.

Three consequences of the longer panel, each of which the 2019–2025 panel could not deliver:

- **Fani becomes estimable at event level.** Fani made landfall 3 May 2019, i.e. DOY 123, before the §1.4 window opens at DOY 150. The entire 2019 Kharif season is therefore post-Fani, and §3.8 B's *k* = −1 reference season for Fani is 2018 — which the 2019-floor panel did not extract. Under that panel Fani, the largest event in the study at 17 treated districts, had no pre-treatment season at all and could enter only the headline TWFE, where every one of its comparison seasons was also post-Fani. Season 2018 supplies the missing reference.
- **Titli (11 October 2018, Palasa, Andhra Pradesh) enters as the seventh named and sixth estimable event**, with severe harvest-window exposure in six roster districts (Cuttack, Gajapati, Ganjam, Nayagarh, Srikakulam, Vizianagaram) and 2017 as its reference season. Sitrang remains named but not estimable.
- **Season 2017 carries no catalogued storm exposure of any severity in any roster district** — the only such season in the 2016–2025 catalogue. It is therefore a genuinely untreated baseline, which materially strengthens the parallel-trends evidence of §3.9 relative to a panel whose first season (2019) was itself the largest treatment year.

Season 2016 is deliberately **not** included. Sentinel-1 coverage in 2016 is thinner and uneven across the roster (Purba Medinipur returns 19 acquisition dates in the §1.4 window against 64–85 in later seasons, measured 2026-09-09), which would make measurement precision vary by district in the earliest season; and the only severe exposure it carries is Vardah, in a single district that this protocol no longer extracts (§1.3). The HLS panel (§3.7) still covers 2016–2025 and remains available as a robustness substrate.

### 1.2 Analysis-year floor (revised 2026-09-09)

Analysis years start no earlier than **2017**.

**The former 2019 floor was an optical constraint, and it no longer binds.** It was set because Sentinel-2 Surface Reflectance Level-2A (`COPERNICUS/S2_SR_HARMONIZED`) did not enter global production until **2018-12-18**; before that date the collection is empty for the Bay of Bengal region, and requesting 2017 or 2018 returned an empty ImageCollection and crashed `Export.table.toDrive` (`analysis/deviation_log.md` DEV-001, 2026-06-15, discovered on Nadia × 2017 × tile01). That constraint is a property of Sentinel-2, not of the study region or the question. With the phenometric substrate moved to Sentinel-1 (§3.6), which has been acquiring over this coast since 2014, it ceases to apply. DEV-001 remains correct as written and is not withdrawn; it simply no longer governs the floor.

**The 2017 floor is set by measured Sentinel-1 coverage, not by a collection start date.** Acquisition counts in the §1.4 window, measured on 2026-09-09 across Bhadrak, Purba Medinipur and East Godavari: 2018 returns 87, 90 and 48 distinct acquisition dates; 2017 returns 61, 63 and 46; 2016 returns 39, 19 and 38. Seasons 2017 and 2018 are therefore comparable to 2019–2025 (40–95 dates), while 2016 is both thinner and uneven across districts and is excluded on that basis (§1.1).

The **Landsat HLS panel** (`HARMONIZED_LANDSAT_SENTINEL`, `HLSL30 v2.0` + `HLSS30 v2.0`) extends back to **2016** and remains a robustness substrate; it is no longer the sole means of reaching seasons before 2019.

### 1.3 Study region

Three Indian states along the Bay of Bengal coast: **Odisha, West Bengal, and coastal Andhra Pradesh** (northern AP districts on the Bay coast).

**District inclusion rule (100 km coast buffer).** A district is included in the analysis if the district centroid, computed on the **GADM v4.1** Level-2 India polygon (Global Administrative Areas Database, https://gadm.org/data.html, version 4.1, released 16 July 2022), falls within **100 km** of the Bay of Bengal coastline. The coastline is the Bay-facing portion of India's national coastline extracted from GADM v4.1 Level-0 (the boundary line segments that face the Bay, i.e., excluding the Arabian Sea coast). Distance is computed as great-circle distance between the district centroid and the nearest coastline vertex in EPSG:4326 (WGS 84).

The full list of admitted districts, with GADM v4.1 spelling and computed centroid-to-coast distance, is in `docs/coastal_districts_gadm41.csv` — committed alongside this protocol. That file is generated by `python/build_coastal_districts.py` from `gadm41_IND_shp.zip` and is the authoritative candidate district roster under the 100 km coastal-buffer rule (28 districts: 9 Andhra Pradesh, 12 Odisha, 7 West Bengal).

**Kolkata exclusion (added 2026-09-07).** Of these 28, Kolkata is dropped from the extraction roster because IRRI RiceAtlas v1.0 has no rice-extent polygon for it — it is a fully urban district with no paddy area to mask against (`docs/coastal_districts_crosswalk.csv`: `match = EXCLUDED, poly_count = 0, area_km2 = 0.0`). This is a data-availability exclusion, not a coastal-buffer-rule exclusion: Kolkata's centroid is 37.9 km from the coast and passes this section's 100 km rule the same as every other admitted district.

**Minimum Kharif-rice criterion (added 2026-09-09; roster 27 → 25).** A district is extracted only if **at least 5% of its GADM v4.1 Level-2 polygon area is mapped as Kharif (winter) rice** in the 2018 epoch of the rice layer defined in §3.5. Measured per district on 2026-09-09 (`docs/chen_rice_2018_per_district.csv`), twenty-five of the twenty-seven fall between **13.8%** (Puri) and **61.3%** (Hugli). Two do not:

| District | Kharif rice | Rabi rice | Decision |
|---|---|---|---|
| Nellore (AP) | 1.3% | 20.0% | excluded |
| Prakasam (AP) | 0.9% | 0.9% | excluded |

The threshold is set at 5% because the distribution is bimodal there: the gap between 1.3% and 13.8% contains no district, so the criterion does not depend on where in that interval the cut is placed. Both excluded districts are Rabi-dominant or low-rice, not Kharif-rice districts; Nellore's own district administration reports 80% of sown area under Rabi. Selecting coastal *rice-producing* districts (the §1.3 rule above) is not the same as selecting *Kharif*-rice districts, and this criterion closes that gap. The excluded pair is reported in the manuscript with these figures rather than dropped silently.

**Cost of the exclusion, stated (2026-09-09).** It is not free. Both districts carry severe harvest-window exposure to **Michaung** (December 2023, 55 kt), whose severe roster districts were Guntur, Nellore and Prakasam; on the 25-district roster Michaung retains one. Nellore additionally carried severe exposure to Vardah 2016, outside the panel. The exclusion is nevertheless taken, because a treated unit holding roughly 1% Kharif rice supplies treatment variation in name only — the phenometrics extracted there would be dominated by non-rice land cover — and because Michaung struck in December, which in a Rabi-dominant district is planting season, not Kharif harvest, so the §1.1 timing classes would be applied to the wrong crop. Retaining the pair would manufacture treatment variation rather than preserve it.

**Extraction roster: 25 districts (7 Andhra Pradesh, 12 Odisha, 6 West Bengal).** `docs/coastal_districts_gadm41.csv` remains the authoritative file for the coastal-buffer definition itself; `CONFIG.districtsByState` in the extraction script is the authoritative record of what is actually extracted.

### 1.4 Kharif season window

**Compositing window (corrected 2026-09-07).** Day-of-year 150–425 (30 May of the analysis year to the end of February / 1 March of the following calendar year, depending on leap years), matching the submitted Paper 1's adopted 60-day-extension window (RSASE-D-26-02830 §3.2: lower endpoint DOY 150; upper endpoints DOY 365/366, 385/386, 395/396, 410/411 and 425/426 for the 0-, 20-, 30-, 45- and 60-day extensions; 22–28 scheduled dekads). Bin width 5 days → 55 five-day bins per season (bin starts DOY 150, 155, …, 420), aggregated pairwise into 28 dekads for curve fitting (§3 lead-in; the 28th dekad is the single bin 420–424). Day-of-year values above 365 are days counted from 1 January of the analysis year and fall in the following calendar year.

**Why the window was corrected.** An earlier version of this section gave DOY 152–304 (1 June – 31 October) and described it as "same as Paper 1". That was true of the pre-correction Paper 1 design (5-day bins, DOY 152–304) against which this protocol was first drafted, but not of the submitted Paper 1, whose corrected workflow composites to DOY 425. Paper 1's retained panel has median POS at DOY 289 and median EOS at DOY 342 (early December), and its mean district-year extraction failure was 62.1% with the window ending 31 December and 39.6% ending in late February; a window closing on 31 October ends before the typical harvest, so the descending limb of the double-logistic is largely unobserved, EOS is not identifiable for the typical pixel, and two of the six cyclones in §1.1 (Bulbul, 9 Nov 2019 = DOY 313; Sitrang, 24 Oct 2022 = DOY 297) — harvest-window storms that could only ever be tested through β_EOS — would have their landfall at or after the window's close.

**Window sensitivity sweep (pre-declared, as in Paper 1).** The 60-day-extension window (DOY 150–425) is the headline. Results are also reported for the 0-, 20-, 30- and 45-day extensions (upper endpoints DOY 365, 385, 395, 410), obtained by truncating the same per-bin composites before smoothing and fitting; Gate 1–3 pass rates, extraction-failure rate and the §3.8 headline coefficient are tabulated for all five endpoints, matching Paper 1's Table 2 layout.

> **Amendment, 2026-09-13 (run and tabulated).** This sweep was declared above and, until today, **unimplemented** — an external re-audit found it missing. It is now run by `python/extract_phenometrics_sar.py --window-end-doy` and tabulated by `python/window_sweep.py` into `results/window_sweep/`. Five points of record, three of them substantive.
>
> **(1) Truncation, not re-export.** Bin *b* spans DOY 150 + 5*b* to 154 + 5*b*, so an upper endpoint *E* keeps exactly the bins whose **end** falls at or before *E*: 43 / 47 / 49 / 52 / 55 bins at DOY 365 / 385 / 395 / 410 / 425. That is the same per-bin composite the headline uses with later bins removed before smoothing and fitting, which is what this paragraph specifies, so no new Earth Engine export was needed. `--window-end-doy 425` and omitting the flag are the same code path by construction (`bins_within(425) == bins_within(None) == 55`), which makes the no-truncation run simultaneously the 425 arm and the sweep's control.
>
> **(2) The control reproduces the committed panel, and where it does not is recorded.** Every breakpoint, every retention flag, every failure reason and every failure class is bit-identical across all 90,000 pixel-seasons. The fitted dB **levels** differ on 176–2,032 rows at a maximum absolute difference of 3.55 × 10⁻¹⁵ (relative ≈ 2.5 × 10⁻¹⁶, i.e. the 16th significant figure of a double). Two candidate causes were tested and **both refuted**: `--jobs` 1, 2 and 4 produce a byte-identical panel, and so does pinning the BLAS thread count to 1 — all six combinations give one md5. The remaining candidate is that the container which produced the committed panel presented a different core count to OpenBLAS, changing its reduction order; that is recorded as an untested candidate, not as a finding.
>
> **(3) The fall-end breakpoint is what the window buys, and this is the number for it.** The five-segment model's final segment falls from the plateau to *b₂* between *t₃* and *t₄* and is flat at *b₂* afterwards. A unit with **no valid dekad after *t₄*** identifies *b₂* only from the slope of the fall extrapolated forward: its fitted fall-end breakpoint is where the fitted fall *would* reach baseline, not an observed return to it. `plsm_fit`'s determinant screen keeps such a fit numerically identified, so it passes every gate silently. Measured on the district-season panel: **17 of 208 estimable units (8.2%) at DOY 425**, against **125 of 204 (61.3%) at DOY 365**. Two consequences. The fall-end coefficient **cannot be read across the endpoints** — at Paper 1's core window three fifths of the fall-end breakpoints are extrapolations, so a change in that coefficient between endpoints is a change in what the coefficient is *of*; every row of the sweep table therefore carries the share, and the fall-end rows are flagged. And this is the sweep's own finding on §1.4: **the 60-day extension is not a preference over Paper 1's core window, it is what identifies the fall-end breakpoint at all.**
>
> **(4) Window sensitivity, interpretation corrected 2026-09-16.** Across the five tested endpoints, total coefficient ranges are **0.807, 1.349, 0.823 and 0.574 days** at pixel level and 1.647, 1.717, 2.518 and 1.749 days at district level for the four non-harvest cells, over a 60-day change in the compositing window. The pixel timing placebo, β_harv on the trough breakpoint, measures **+7.291 to +8.099 d with cluster-robust t between +3.80 and +4.30**. The association persists across these endpoints; this does not exclude other design effects or identify why it arose. β_harv on heading retains its sign and exceeds the descriptive |t| = 1.96 reference at four endpoints (t +1.81 at DOY 365). This comparison is not WCB or permutation inference. The two `S_pre_season` cells on trough and heading do not exceed that reference at the tested endpoints; a failure to reject zero is not evidence that the coefficients equal zero.
>
> **(5) At the headline it is a diagnostic, not a correction.** `window_sweep.py` reports the same cells on the units with at least one valid dekad after *t₄*. β_pre on fall-end goes **−10.184 (t −2.08) → −8.084 (t −2.12)** and β_harv on the rise-end breakpoint **+6.183 (t +2.51) → +7.438 (t +3.10)**: every sign is preserved and the one significant positive cell strengthens, so no reported result rests on an extrapolated fall-end breakpoint. **The headline retention rule is not changed on this basis** — changing a gate after seeing which units it would drop is exactly the discretion this protocol exists to remove — and the arm is reported alongside the headline, labelled as an arm. Should a later reading of §3.11 add a post-*t₄* observation requirement, it must be declared as an amendment first and applied to all five endpoints together.

### 1.5 Positioning against Paper 1 — amendment, 2026-09-14, written AFTER the analysis

**This section is post-analysis and is not predeclared.** It was written on 2026-09-14, after
every estimate in §4 existed, and it changes **nothing** in §1.1–§1.4, §2 or §3: the objectives,
the five hypotheses and their verdicts stand exactly as recorded, including the ones that fail.
What it changes is how the *finished* study is described. It is placed here, at the end of §1,
rather than rewritten into §1.1, so that the original scope and the later reframing are both
visible and neither is mistaken for the other. `analysis/hypothesis_verdicts.md` remains the
authoritative record of what was asked in advance and what came back.

**Why it was needed.** This protocol's working title is *"A peak-relative non-parametric
**quality-control framework** for **cyclone-impact** rice phenometric extraction in smallholder
coastal systems of the Bay of Bengal."* The submitted Paper 1 is titled *"Fitting-window
sensitivity and differential attrition in Sentinel-2 rice phenology extraction: **a reproducible
quality-control framework for cyclone-impact** case studies."* The two titles claim the same
thing in almost the same words, by the same authors, on an overlapping region and overlapping
seasons. That is a self-overlap a reviewer will find in one search, and the working title is
**withdrawn** below.

#### 1.5.1 Paper 1 as actually submitted (RSASE-D-26-02830, second submission, 4 September 2026)

Read from the submitted PDF, not from a plan or the first submission (RSASE-D-26-01669, which
was rejected). Its specifics:

| | Paper 1, as submitted |
|---|---|
| substrate | Sentinel-2, 10 m optical |
| scope | **eight** Odisha districts, **six** seasons (2019–2024), one state |
| cohort | one fixed candidate cohort, **15,162 candidate pixel-years per window** |
| estimator | Whittaker smoother with generalised cross-validation, **difference-form double-logistic** |
| quantities | **SOS, POS, EOS** |
| the experiment | five window extensions (0, 20, 30, 45, 60 days) on the *same* cohort |
| QC | Gate A (mode-share ≤ 0.20, panel diagnostic), Gate B (agronomic plausibility), Gate C (fit quality) |
| headline findings | every phenometric below Gate A at every extension (0.063 / 0.104 / 0.146 at 60 d); mean district-year extraction failure **62.1% → 39.6%** from 0 to 60 days; Gates B and C retain **38 of 48 district-years** and **6,850 pixel-years from 2,195 unique pixels** |
| downstream | *exploratory* TWFE: Model 1 −8.14 d SOS, −3.42 POS, +2.15 EOS; Model 2 POS −6.51 d (p_WCB 0.024), SOS and EOS indistinguishable from zero |
| its own stated limits | "treatment-correlated extraction failure and absent treated support in 2022 limit causal interpretation" |

Its three stated contributions are window sensitivity on a fixed cohort, the separation of three
QC roles, and carrying the retained panel into an exploratory application. **Paper 1 is a
quality-control paper and says so.** Paper 2 cannot be a second one.

#### 1.5.2 What the two papers genuinely share, stated rather than minimised

A reviewer checking self-overlap should find this disclosed, not discovered:

- **Region and seasons overlap.** Paper 1's eight Odisha districts are a subset of this study's
  25-district roster; its 2019–2024 is a subset of 2017–2025.
- **Three cyclones are common** — Fani 2019, Amphan 2020, Yaas 2021.
- **The compositing window is deliberately matched** to Paper 1's adopted 60-day extension
  (DOY 150–425, §1.4), so the two are comparable.
- **The Whittaker–GCV smoother is inherited from Paper 1** (§3, where it is measured and then
  *not used* on the radar path, at a cost of 35 points of completeness).
- **The regression structure is Paper 1's Model 2** — pixel-year resolution, district and season
  fixed effects, clustered at district (§3.8).
- **The working discipline is Paper 1's** — predeclared thresholds, an append-only deviation
  log, a window-sensitivity sweep tabulated in Paper 1's Table 2 layout.
- **Same authors**, and Paper 1 is cited as the companion paper throughout.

#### 1.5.3 The distinct question, and why Paper 1 could not have asked it

Paper 1 asks: **does a processing choice move the phenometric, and does extraction failure track
treatment?** It answers within one sensor and one estimator.

Paper 2 asks: **how consistently are Sentinel-1 seasonal breakpoints recovered across relative
orbits, and what limits their interpretation as agronomic dates and as cyclone-response
outcomes?**

*Corrected 2026-09-14 (third pass): this question previously read "at what spatial scale is a
Sentinel-1 seasonal breakpoint a reliable measurement at all". **It promised the scale finding
that §1.5.4 item 1 withdraws** — the study has no district-scale repeat measurement and cannot
locate that boundary. A central question must be answerable by the evidence assembled, and this
one is: consistency across orbits is measured, and the interpretation limits are measured against
MARC and against §3.9's placebo.*

That question needs a **repeat observation of the same quantity along a separate instrument
path**, and Sentinel-1 supplies one: where two or more relative orbits cover a district-season,
the breakpoint is estimated separately from each (§3.4 Tier 1). **In the optical record assembled
for Paper 1 no such repeat exists** — under monsoon cloud the ascending limb is not observed a
second time independently, which is why Paper 1's own §3.4 removed HLS as a validation substrate.
That is a statement about **these datasets over this coast in these seasons**, not a categorical
claim about optical remote sensing: with a different cloud regime, or a denser optical record, the
same question could be posed optically.

**Paper 1 names this gap itself.** Three statements from the submitted manuscript:

> the sensitivity checks "do not convert the downstream contrast into a causal estimate or prove
> that the retained panel is **free of measurement error**"

> "Independent MODIS, **Sentinel-1**, calendar, or field **validation is not contained** in the
> supplied corrected outputs"

> "**Independent reference validation remains necessary** before general accuracy claims"

**What Paper 2 does and does not do about those three sentences, stated exactly.** Paper 2
**addresses a related measurement question that Paper 1 left unexplored; it does not validate
Paper 1's phenometric accuracy.** Paper 1's limitation concerns validating *its own optical*
SOS, POS and EOS. Paper 2 evaluates *radar breakpoints*, which §3 of this protocol states are
**not those quantities**, and it does so **without any field reference** — no field-observed
transplanting or harvest date exists for any district-season in this panel. So Paper 2 cannot
close Paper 1's validation gap and does not claim to. The positioning is narrower and still
sufficient: **not a second QC framework, but a measurement study of a different instrument's
timing estimates, on a question the first paper identifies as open.**

#### 1.5.4 What Paper 2 adds, at the strength the evidence supports

Four things, each stated with its own limit:

1. **Two uncertainty figures, reported separately, because they are not commensurable.**

   *Pixel scale, observed.* Where two orbits both retain a pixel-season, the two separately
   fitted breakpoints disagree. **8,515 pixel-seasons carry a usable orbit pair — 9.5% of the
   90,000 offered** — of which **798 are the untreated 2017 baseline** used only to fix the
   tolerance, so the reported statistics run on the remaining **7,717**. The implied
   scaled between-orbit disagreement statistic is **σ = 25.90 d (trough), 19.82 d
   (rise-end; legacy column `heading`), 25.79 d (fall-end; legacy column
   `harvest`)** — *not* a uniform "≈ 26 d", and **not a measured error** (§1.5.6
   constraint 2). *(Reworded 2026-09-14, seventh pass: "the implied single-measurement error
   scale" is withdrawn — it names σ an error, which the identity does not license.)* Heading shows **smaller observed between-orbit
   disagreement** than the other two markers; that is a statement about consistency, not about
   accuracy, and it does not imply the rise-end breakpoint is closer to any agronomic truth.
   Directly observed alongside it, with no modelling assumption: 38.2% of trough pairs agree
   within one dekad and 55.6% within two, with a **mean signed between-orbit difference** of
   −5.63 d (so called rather than "bias": neither orbit is ground truth).

   *Synthetic trajectory, simulated.* At assumed noise 0.122 dB, the archived
   80-draw `grid = free` Monte Carlo reports standard deviations **0.00 / 0.00 /
   2.18 / 1.90 d** for t1 / t2 / t3 / t4 and signed errors 0.000 / 0.000 / -0.500 /
   +0.375 d. The common ±1.3 d summary is withdrawn as unsupported by
   `results/montecarlo_precision.csv` (release correction 2026-09-17).
   These are conditional on-grid simulation results, never field-validated
   accuracy or measured precision of the district-season panel (§3.4).

   **No ratio between the two is reported, and no scale boundary is claimed.** Dividing an
   observed pixel-scale disagreement by a simulated district-scale precision is not a matched
   comparison: it does not establish that district-season timing is reliable, and it does not
   locate the scale at which reliability begins. A claim of that kind would require *comparable
   uncertainty assessments at both scales* — a district-scale repeat measurement, which this study
   does not have. What the two figures jointly support is narrower and still useful: **the selected
   paired sample shows substantial between-orbit disagreement, which limits fine-resolution timing
   applications under this estimator and this sampling design**, and that is why §3.8 estimates at
   district-season level. It does **not** rule out every pixel-level application, and it does
   **not** establish an instrument-wide limitation of Sentinel-1.
2. **Construct-validity evidence against an external product — strong for harvest, weaker and
   mixed for transplanting.** Against MARC (Zhao et al. 2024), the fitted harvest breakpoint sits
   later than MARC's harvest date in **all 25 districts**, by a **mean of +50.35 d with a
   per-district range of +26.19 to +60.54 d**. The mean is not each district's offset and must not
   be quoted as one; what holds in every district is that the offset is **positive and exceeds
   +26 d**. The transplanting comparison is weaker: mean **+20.2 d**, range **−16.9 to +37.9 d**,
   so it **changes sign** across districts. The defensible conclusion is therefore
   **marker-specific**: a strong warning against reading the harvest breakpoint as an agronomic
   harvest date, and a weaker, directionally inconsistent signal on transplanting. It does not
   establish a definitive agronomic identity — or non-identity — for every marker. The breakpoints
   are not reported as SOS, POS or EOS anywhere (§3, §4.3.1) and the mapping is authorised for
   direction only.
3. **This estimator, in this design, fails its own falsifiability check; the cause is not identified.**
   §3.9 predeclares that severe harvest-window exposure cannot causally move the
   *same season's earlier radar trough breakpoint*. Measured **+7.4 d**, and it is the most window-robust cell in the study
   across all five compositing endpoints. A post-analysis censoring diagnostic shows that the
   association is estimator-dependent on its common pixel sample, and a synthetic perturbation
   demonstrates that the five-segment fit can move an early breakpoint in response to later
   values. Those results establish a plausible pathway, not the cause of the observed
   association. §4.1
   therefore withdraws every §3.8 coefficient as a causal effect. **The claim is bounded to the
   estimator and design tested here** — a five-segment piecewise-linear fit to a whole-season
   radar trajectory, with exposure assigned at district level. It is **not** a demonstrated
   failure of radar-breakpoint exposure designs as a class; a differently-specified estimator, or
   one fitted on a censored window by construction, is untested here. What generalises is the
   *warning* and the *diagnostic*, not the verdict.
4. **A stated scope for downstream users**, which is what a phenology paper owes an
   impact study *(reworded 2026-09-14, seventh pass: "a stated working level" is withdrawn — it
   implies a scale at which the instrument is established to work, which this study has not
   shown)*: **in the selected paired sample, between-orbit disagreement at a single 30 m
   pixel is substantial enough to limit fine-resolution timing applications under this estimator
   and this sampling design**, and §3.8's decision to estimate at district-season level follows
   from that rather than from convenience. *Qualified 2026-09-14 (fourth pass): this item
   previously said "a timing claim is not supportable", which item 1 had already qualified and
   this one had not.* It is **not** a located scale boundary (item 1), it does **not** certify
   district-season timing as reliable, it does **not** rule out every pixel-level application, and
   it is **not** an instrument-wide limitation of Sentinel-1.

#### 1.5.5 The priority claim is WITHDRAWN — it was tested and it is false

§3's lead-in stated: *"No published Sentinel-1 rice-phenology study we could find reports a
marker timing uncertainty in days at all … so this measurement is a contribution of the paper."*
**That claim is withdrawn.** It was checked on **2026-09-14** rather than repeated, and published
studies reporting rice marker timing error in days do exist:

| study | what it reports in days | reference used |
|---|---|---|
| Manago et al. 2020, *Agriculture* 10(12):625 (Sentinel-1 VH, Indonesia) | transplanting-date error **SD ≈ 5–6 d**; 69% / 92% / 97% within 5 / 10 / 15 d | farmer-interview transplanting dates, 25 irrigation blocks over 250 ha |
| Wang et al. 2022, *Sustainability* 14(13):8009 (Sentinel-1, China) | **average error 3.08 d**, pooled across BBCH stages, not separable to heading or harvest | in-situ field measurement, single region |
| Zhao et al. 2024 MARC, *ESSD* 16:3893 | bias **+4 d / −6 d** transplanting / harvesting; RMSE 27.62 / 28.32 d against RiceAtlas | census calendar and 40 literature site records; **Sentinel-1 *and* Sentinel-2**, so not attributable to radar alone |

**Search of record.** Conducted 2026-09-14 by web search on the queries *"Sentinel-1 rice
phenology transplanting date accuracy RMSE days validation"* and *"Sentinel-1 rice transplanting
date estimation RMSE days Indonesia Philippines phenology error"*, followed by full-text retrieval
of five candidates. **The search is incomplete and is recorded as such:** two ScienceDirect papers
— Cauba et al. (Philippines, S1 transplanting and harvest dates) and the *Remote Sensing of
Environment* systematic-method paper — **could not be retrieved** (HTTP 429 / 400) and were not
assessed. That incompleteness does not affect the withdrawal: a negative claim is refuted by one
counter-example, and three were found.

**What survives is a statement about the KIND of quantity, not about scale or scope, and not
about priority.** *Corrected 2026-09-14, second pass: an earlier draft of this paragraph said all
three studies report accuracy "at site or irrigation-block scale, on small managed samples, in one
region". **That is false of MARC**, which is a monsoon-Asia product on a 0.5° grid validated
against a census calendar and 40 literature site records — continental in scope, not a small
managed sample. The generalisation was drawn from the two field-referenced studies and wrongly
extended to the third.*

The accurate distinction is between **two different measurands**:

* Manago (2020), Wang (2022) and MARC (2024) all report **agreement with an external reference** —
  farmer-reported dates, in-situ field measurement, a census calendar. That is a form of
  *accuracy*, and its value depends on the reference.
* This study reports **disagreement between two observations of the same quantity by the same
  estimator along different orbit paths** — a *repeatability* statistic, which uses no external
  reference and says nothing about accuracy.

**The two are not directly comparable in either direction**, and MARC's RMSE of 27.62 / 28.32 d
against RiceAtlas must not be set beside this study's σ as though they measured the same thing.
**Paper 2's contribution must stand on the measurement work itself and on §1.5.4's items 2–4, not
on being first and not on a favourable comparison of incomparable numbers.** Any manuscript
sentence implying priority is to be struck.

**A discrepancy that must be addressed in the Discussion, not buried.** Manago's ≈ 5–6 d and
Wang's 3.08 d are far smaller than this study's pixel-scale σ of 19.8–25.9 d. Three candidate
reasons, none of them established here: those two studies compare **aggregates** — irrigation
blocks, field sites — rather than single 30 m pixels; both are single-region studies of managed
irrigated systems rather than smallholder monsoon rice across three states; and both measure
*accuracy against a reference* rather than *repeatability between instrument paths*, which are
different quantities that need not take similar values. **These are candidates to be tested and
defended, not an explanation to be asserted**, and it is recorded here as an open item for the
Discussion rather than settled in this protocol. Note also that the figures for Manago and Wang
were read from their abstracts during the 2026-09-14 check and **have not been independently
re-verified against their full texts**; the reviewer's own attempt to retrieve them was blocked by
the publisher.

#### 1.5.6 Framing constraints carried into every manuscript section

Binding, and each traces to a result in this repository:

1. **Report the archived per-marker Monte Carlo results, not the unsupported
   common ±1.3 d summary.** At sigma_db = 0.122, grid = free, 80 draws, the t1/t2/t3/t4
   standard deviations are 0.00/0.00/2.18/1.90 d. These are conditional results
   for one on-grid synthetic trajectory, never field-validated accuracy or
   empirical district-panel precision. No field-observed reference exists here.
2. **The pixel-scale σ is a SCALED DISAGREEMENT STATISTIC, not a measured error, and no second
   route validates it.** Two separate qualifications, both binding. *(Reworded 2026-09-14,
   seventh pass: this read "an error-scale ESTIMATE UNDER STATED ASSUMPTIONS, and is corroborated
   rather than independently validated". "Error scale" names σ an error; "corroborated" implies
   the semivariogram measures the same thing, which it does not.)*
   *(a)* σ is derived as **sd(difference)/√2**. Write the two observations of one latent
   quantity as *Y₁ = μ + e₁* and *Y₂ = μ + e₂*, and let *s² = Var(Y₁ − Y₂)/2*. Then

   > *s²*  =  [ Var(e₁) + Var(e₂) ] / 2  −  Cov(e₁, e₂)

   **This is a population relationship under stated assumptions, not a measured bound on unknown
   errors.** Reading it off: with **zero** error covariance *s²* equals the **average** error
   variance, and if the variances are additionally **equal** it equals either orbit's error
   variance. **Positive** covariance makes it **smaller than the average total error variance**.
   An identical additive component in both errors — including a shared systematic bias —
   **cancels from the difference** and is not measured at all.

   **What this does NOT license, and two earlier drafts claimed both.** *Corrected 2026-09-14
   (fourth pass), each by an explicit counterexample supplied by the reviewer and reproduced here
   by simulation:*

   * **It is not a lower bound on each individual orbit's error.** With unequal variances σ can
     exceed the better orbit's total error even when the covariance is positive. Counterexample:
     shared component sd 1, independent residuals sd 3 and sd 10, so Cov = 1 > 0 — the
     difference-based scale is **√((9+100)/2) = 7.38 d** while orbit 1's total error sd is
     **√(1+9) = 3.16 d**. What σ bounds below, when covariance is non-negative, is the
     **quadratic mean of the two total errors**, not either one.
   * **It is not an upper bound on the combined-orbit panel's error.** Using the very example an
     earlier draft relied on — shared sd 25, independent sd 5 each — the difference-based scale is
     **5.0 d**, while even a simple equal-weight two-orbit average carries a total error sd of
     **√(625 + 25/2) = 25.25 d**. Averaging reduces the independent part and **does not remove a
     common component**. The pipeline does not average date estimates either: it fits a
     **nonlinear breakpoint model to composited observations**, which supplies no automatic
     ordering in either direction.

   **What is claimed, therefore: neither bound.** The combined-orbit panel uses a different
   estimator, and **this study has not established its total-error relationship to the
   single-orbit difference statistic**. The estimator-mismatch warning in
   `python/orbit_agreement.py` stands as a warning — the two quantities are not interchangeable,
   which is why `dispersion_single_orbit` exists — but its inference that σ *overstates* the
   composite error is withdrawn: a negative variance subtraction establishes that two estimates or
   assumptions are incompatible, not uniquely which one is larger. A direct matched assessment at
   both scales could settle it; none is attempted here, and none is needed to remove the claim.

   An earlier draft also said σ "tracks the average independent error variance" as though the
   identity gave that. It does not: that reading needs an explicit **common-additive-component
   model with independent residuals**, which is a modelling assumption about these orbits and not
   a consequence of the covariance algebra.

   Every report of σ must be accompanied by the **directly observed** disagreement, which needs no
   assumption at all: sd of the orbit difference, the within-one- and within-two-dekad shares
   (38.2% and 55.6% on trough) and the **mean signed between-orbit difference** (−5.63 d on
   trough) — *called that rather than "bias", because neither orbit is ground truth and the sign
   is a statement about one path relative to the other, not about error.* *(b)* The semivariogram short-lag value agrees within 0.8 d,
   but the two are **not the same estimand** — a short-lag spatial semivariance mixes local
   variation in the true field with the spatially uncorrelated part of the error, while a
   between-orbit difference cancels whatever the two paths share — and both read the same panel
   through the same estimator, so **neither validates the other**. The similarity is a
   description of this dataset. *(Tightened 2026-09-14, seventh pass: this clause read
   "corroboration and not independent validation"; "corroboration" is withdrawn too, since it
   implies the two measure one thing. No wording anywhere in this repository may call σ's
   magnitude corroborated, confirmed, independently established or independently validated.)*
   *Corrected 2026-09-14 (fifth pass): this clause read "the nugget is an upper bound", full stop.
   **Withdrawn as stated.** the shortest-lag spatial semivariance is a **descriptive mixture** of local spatial variation in the true field and the **spatially uncorrelated** part of the error. Under an additive signal-independent error model it bounds **that component** from above at the population level; it does **not** bound total measurement error, because error shared between neighbouring pixels — orbit geometry, incidence angle, terrain, a district-season common mode — very largely cancels from the pixel difference and is **missing** from the statistic rather than contained in it, and a constant bias cancels completely. It is also the shortest interpretable **bin**, not a fitted zero-distance intercept (`semivariance.py`'s `nugget_and_sill`), and a finite-sample value is not a guaranteed numerical bound. Worked counterexample, simulated on that
   date: with a constant true field, a district-season shared error of sd 25 d and an independent
   error of sd 5 d, the short-lag root is 5.0 d while each pixel's total error sd is 25.50 d —
   five times larger.*
   *(c)* Values are **marker-specific — 25.90 / 19.82 / 25.79 d for trough / heading / harvest —**
   and are computed on the **7,717 later-season pairs** of the **8,515 usable pairs**, themselves
   **9.5% of the 90,000 candidate pixel-seasons**. That subset is selected by requiring two orbits
   to pass every §3 screen, so **any generalisation beyond it must be qualified**: the pixels that
   fail on one orbit are not represented.
3. **The §3.5 per-unit mask-stability conclusion is withdrawn.** Mask choice *does* move the
   per-unit estimates (mean −7.39 / −0.67 / −1.59 d, signs agreeing 31/35, 22/35, 21/35). The
   district- and pixel-level §3.5 results stand. No sentence may say mask choice is immaterial.
4. **Cyclone contrasts are descriptive throughout.** §4.1 withdraws every §3.8 coefficient as a
   causal effect; H3 is **not estimable as declared**; H4 fails its criterion; §3.3's intensity
   variable is withdrawn; per-unit inference is unavailable on one treated cluster. Cyclones
   occupy a secondary section demonstrating how measurement limits propagate — they do not
   control the title, the abstract or the conclusion.
5. **Reproducibility is stated at its true scope.** The per-unit calculation is reproducible from
   the committed fitted district panels; **reconstructing those panels still requires the archived
   raw exports** (`docs/verify_masked_panels.md`).
6. **Calendar plausibility is Odisha-only**, attributed to the named ICAR-CRIDA / OUAT
   contingency plans, and **no AICRP attribution may be made** (§3.4 amendment of 2026-09-14).

#### 1.5.7 The working title is withdrawn; a replacement is proposed

The title at the head of this document is withdrawn as duplicating Paper 1's framing. Proposed
replacement, for the author's decision:

> **Between-orbit repeatability and interpretation limits of Sentinel-1 rice phenology
> breakpoints along the Bay of Bengal coast**

*Adopted as the provisional title on the author's preference, 2026-09-14.* It is the right choice
for a further reason: the earlier candidates both led with **scale dependence**, and §1.5.4 item 1
now records that **no scale claim is supported** — the two uncertainty figures are not
commensurable. "Interpretation limits" is carried by the evidence that exists: the marker-specific
repeatability, the harvest-breakpoint offset against MARC, and the falsifiability failure.

This keeps "quality control" and "cyclone impact" out of the title, which is what separates this
paper from Paper 1 at the only point most readers will look. The title is the author's call; the
constraint set by this amendment is that it must not claim a QC framework and must not lead with
cyclone impact.

---

## 2. Hypotheses

Locked at the start of the multi-state extraction. Language is deliberately identical to the six hypotheses carried in prior planning; only the geographic scope is broadened from West Bengal only to the three-state Bay of Bengal panel.

**H1 and H2 rewritten 2026-09-09; the frozen accuracy claims are withdrawn.** The superseded wording asserted that transplanting and harvest bias and RMSE would be "improved relative to MARC's own reported" figures of +3.93 d / 27.62 d and −5.76 d / 28.32 d. Those figures are MARC's agreement with RiceAtlas on a 0.5° grid, not field-validated pixel error (§3.4), and the comparison set this study's RMSE-against-MARC beside MARC's RMSE-against-RiceAtlas — different quantities, so beating the number would have demonstrated nothing about accuracy. No field-observed transplanting or harvest date exists for these districts in any panel season (§3.4), so no accuracy hypothesis of any form is testable here. The replacements are consistency and agreement claims, and are labelled as such wherever reported.

- **H1 (measurement consistency — radar trough breakpoint).** For pixels admitted by Gate 1 (§3.1), trough breakpoints fitted separately to different Sentinel-1 relative-orbit series agree within a pre-declared tolerance, and each pixel's inter-seasonal dispersion about its own mean, after removing season effects, is smaller than the between-pixel dispersion within its district. Tolerances are fixed on the untreated 2017 baseline season (§1.1) before any treated season is fitted. The trough is interpreted as related to establishment but is not called a field-observed transplanting date.
- **H2 (measurement consistency — radar fall-end breakpoint).** As H1, for the fitted fall-end breakpoint. The planned post-monsoon Sentinel-2 EOS arm was not obtained and is reported as withdrawn; no optical estimate is described as an independent validation of the radar breakpoint.
- **H1c / H2c (external-product agreement, reported never tested).** District-median trough and fall-end breakpoints are compared with MARC's transplanting and harvest dates and, where a source exists, with published district crop calendars. The compared quantities are different measurands. Signed difference and dispersion are reported separately and never conflated, and always described as agreement or plausibility rather than accuracy. No threshold is pre-declared because resemblance to a 0.5° product would not establish correctness at 30 m.

**Correction 2026-09-16 — the cancellation assurance is withdrawn.** This study
does not establish pixel-level accuracy for any phenometric. Repeatability is
necessary but not sufficient for a causal difference-in-differences
interpretation: cancellation would require the magnitude of measurement error to
be invariant, or at least nondifferential with respect to treatment and time.
Common direction alone does not establish that condition, and this study's timing
placebo shows that an exposure-period signal change can move an earlier fitted
breakpoint. No §3.8 coefficient is therefore rescued by the consistency results.
- **H3 (revised 2026-09-07; pre-revision wording preserved in `analysis/decisions_log.md`).** In the exposure panel of §3.8 A, the severe pre-season exposure coefficient β_pre is positive and significant at *p* < 0.05 by wild-cluster bootstrap (9,999 replications, district-clustered, 25 clusters) for SOS, peak NDVI date and EOS, and the severe harvest-window coefficient β_harv is positive and significant at *p* < 0.05 for EOS. Directions are the timing-class hypotheses stated at §4 below.
- **H4 (revised 2026-09-07; event set and criterion updated 2026-09-09).** The framework transfers across states and cyclones without re-tuning. Specifically, (i) the r values of §3.1 — re-derived once on the untreated 2017 baseline season, then frozen — are used unchanged for all three states and all seasons, and (ii) in the event-level view of §3.8 B the point estimate β₀ for each estimable named cyclone agrees in sign with §4 for **at least five of the six**. The estimable set is now **Titli, Fani, Bulbul, Amphan, Yaas and Remal** — six, not five: Titli enters with the 2017 panel floor and Fani becomes estimable because 2018 supplies the *k* = −1 reference season it previously lacked (§1.1, §1.2). Sitrang remains not estimable, exposing no roster district. Raising the bar from four-of-five to five-of-six keeps the criterion at a comparable strictness as the event count grows: under independent coin-flip signs four-of-five would pass about 19% of the time and five-of-six about 11%, so the tighter fraction offsets the extra event rather than exploiting it. The earlier criterion — H3 significance for at least four of six cyclones — is retired: two of the named cyclones expose only two roster districts each, and cluster-robust inference with two treated clusters cannot reject at any conventional level whatever the true effect (MacKinnon & Webb, 2018, *Econometrics Journal* 21(2), 114–135), so that criterion could not have been met by construction. Significance is tested once, on the pooled panel (H3); the five-of-six sign criterion is a consistency check, not a test — under independent coin-flip signs it passes about 11% of the time — and is reported as such. *(Correction 2026-09-09: this closing sentence still read “four-of-five … about 19%” after the criterion earlier in this bullet was raised to five-of-six on the same day, contradicting it. Both probabilities are arithmetically correct for their own criterion — 6/32 and 7/64 — but only the five-of-six figure applies. Found on re-reading before the part-2 commit; no result had been reported under either wording.)*
- **H5.** *(MODIS district-level coherence only; later withdrawn untested in §4.3.2.)* At district level, the QC-median marker of this study and MODIS MOD13Q1 timing were to be compared by Spearman ρ in district-seasons without severe exposure (§1.1). No pixel-level MODIS RMSE was planned. The original rationale asserted an unsourced <0.5 ha mean field size for all three states and misattributed that conclusion to Zhao et al. (2024); that rationale is withdrawn. The MODIS panel was never acquired, so H5 has no result.

**Amendment 2026-09-13 — read §4.1 before any hypothesis in this section.** On the
corrected sample H3 is not met (0 of 4) and H4 is not met (2 of 6), and more
consequentially the design fails §3.9's own timing placebo and lead test, so no
§3.8 coefficient is reported as a causal effect. H1 and H2 are measurement-
consistency claims and are unaffected. Full amendment and evidence at §4.1.

---

## 3. Methods

**Phenometric extraction method (substrate changed to Sentinel-1, 2026-09-09; supersedes the Sentinel-2 NDVI method stated 2026-09-07; used throughout §3.1–3.11).**

**Why the substrate changed.** The optical method could not be executed. Measured on 2026-09-08/09 across the fourteen district-seasons that exported usable data — 5,600 cohort pixels — the median pixel carried **2 valid five-day NDVI composites out of 55**; the mean was 2.4, 32% of pixels carried none at all, 6 of 5,600 reached 16 and none reached 20. A six-parameter double-logistic cannot be fitted to two points. The distribution over the season is what makes this structural rather than marginal: valid observations cluster before the monsoon (DOY 150–165) and after it (DOY 295 onward), while DOY 170–290 — the growing season, containing the entire ascending limb from which transplanting date is derived — is close to empty, several five-day bins holding zero valid observations across 2,000 pixel-slots. Pooling all 400 pixels of a district does not fill the gap, because the gap is in cloud cover and not in the sample. The cloud mask is not the cause: `cloudProbMax` 30 with SCL classes 4, 5, 6, 7 and 11 is conservative but defensible, and relaxing it would trade sparsity for cloud-contaminated reflectance, which biases phenometrics rather than recovering them. This measurement is reported as a result of the study (§4), not buried as a limitation.

**Substrate.** Sentinel-1 GRD, IW mode, dual-polarisation VV+VH (`COPERNICUS/S1_GRD`), which is unaffected by cloud. Measured acquisition density in the §1.4 window, 2026-09-09: combining relative orbits gives **40–95 distinct acquisition dates per district-season with a maximum gap of 7–12 days and a median gap of 3–7 days**, against a median of 2 usable optical observations. Sentinel-1 has acquired over this coast since 2014, which is what permits the 2017 panel floor (§1.2).

**Index: the VH/VV ratio, not VH alone.** Over a rice field the two polarisations behave differently and neither is individually well shaped for double-logistic fitting: VH rises through the season with local minima rather than forming a single peak, and VV *decreases* through tillering as the canopy becomes erectophile and attenuates the return. The **cross-polarisation ratio VH/VV** follows a trough–rise–plateau pattern in the dense Mekong Delta series of Phan, Le Toan & Bouvet (2021, DOI `10.3390/rs13050921`). This supports use of the ratio as a radar trajectory, not identity of its breakpoints with agronomic dates. The panel therefore carries the per-pixel VH/VV ratio in decibels as the phenometric index, in place of NDVI.

**Everything downstream of the index is unchanged from Paper 1.** The ratio series is composited to the §1.4 five-day bins (median of all acquisitions falling in the bin, across all orbits after the normalisation below), aggregated pairwise into the same 28 dekads, smoothed with the same Whittaker smoother under generalised cross-validation, and fitted with the same difference-form double-logistic model of Beck et al. (2006). SOS and EOS remain the 20% amplitude crossings on the ascending and descending limbs and POS the fitted maximum. A fit is accepted on the same conditions: the optimisation converges, the six-parameter Jacobian has full rank, and the RMSR is finite. Gate 2 (§3.2) and Gate 3 (§3.11) apply unchanged. This preserves structural comparability with the submitted Paper 1 — only the index changes, not the estimator — which is what makes the substrate change defensible rather than a different study.

**Measured property of the smoothing step (added 2026-09-09, corrected
2026-09-16).** The Whittaker–GCV step is not neutral. In the stated 400-series
simulation it shifted the fitted optical crossings and reduced dispersion, and
one planted-effect example recovered +7.73 d from +8.0 d. The former sentence
that a common direction means the shift “is removed by any
difference-in-differences” is withdrawn: one simulation cannot establish
invariance across treatment and time, and common direction does not imply equal
magnitude. These results describe that simulation only; they do not validate a
causal correction or establish accuracy for the radar breakpoints used later.

**Calibration outcome, and the estimator change it forced (2026-09-12).** The calibration required above was run on the untreated 2017 baseline and the double-logistic **failed it**. The sentence above reading "Everything downstream of the index is unchanged from Paper 1 … only the index changes, not the estimator" is **withdrawn**: it is the assumption that made the substrate change look cheap, and it is false.

A double-logistic models a bell — background, rise, peak, fall. The VH/VV trajectory of transplanted rice is not a bell. Phan, Le Toan & Bouvet (2021, *Remote Sensing* 13(5), 921), on 300 field-seasons of ground truth, report a **minimum** at tillering, a rise of roughly 10 dB to booting–heading, then, verbatim, "The VH/VV ratio remains stable until the end of its cycle", with only "a small decrease (<1 dB)" through grain filling and maturity; the eventual fall is pre-harvest **drainage**, not senescence. Fitting a bell to a trough–rise–plateau–drop produced, on the baseline season: the fitted peak pinned near DOY 326 at *every* window start tested (150, 180, 200, 220, 240), 56% convergence, no descending crossing for 40% of pixels, and phenometrics outside §3.2 in every configuration.

*Eliminated by direct test before this conclusion was reached*, each on the baseline season: the per-orbit normalisation, orbit structure, image timestamps, the export path, the fitting-window start, the phenometric definitions read off the fitted curve, and the Whittaker smoother (fitted amplitude 3.33 dB smoothed against 3.27 dB unsmoothed).

*Why the literature timings never applied.* The measured trough-to-heading interval on this coast is about **80 days**; Phan et al. report 30–40. That is a different crop, not a discrepancy: their dataset is 80% short-cycle (<100 day) **direct-seeded** rice, whereas Odisha *Sali* and West Bengal *aman* are long-duration **transplanted** rice of 140–150 days, for which heading at ~80 days after transplanting is correct. This is the transfer failure the calibration clause was written to catch.

**Radar phenometrics are read as features, not fitted (2026-09-12).** `python/extract_phenometrics_sar.py` reads three markers directly off the Whittaker-smoothed dekadal series, with no curve fitting, each named for the physical state it marks:

- **Trough** — minimum within the transplanting window (DOY 170–294, §3.4's AICRP calendar): the flooded near-bare field, specular and weak in cross-polarisation. **Corrected 2026-09-14: the parenthetical describes no live code path and is withdrawn as a description of this pipeline.** `TROUGH_WINDOW = (170.0, 294.0)` is only the *default* of `extract_markers`, and the one production call site overrides it with `GATE2["trough"] = (155.0, 240.0)` — §3.2's window, not §3.4's calendar. What each arm actually searches: the **crossing rule** (superseded, `xr_*` columns) DOY 155–240 from §3.2; the **trapezoid** (superseded, `tz_*`) §3.2's windows structurally; the **PLSM primary estimator**, which produces every reported coefficient, `PIXEL_GRID_DOY["t1"] = (184.5, 304.5)` — derived from the untreated 2017 baseline district-mean range padded two dekads, and not a calendar bound at all. No reported number depends on DOY 170–294. This sentence was a protocol claim about behaviour the code does not perform; it was found by tracing the AICRP citation of §3.4, not by an audit.
- **Heading** — first crossing of 80% of the trough-to-plateau rise: canopy closed, structure maximal.
- **Harvest** — first fall back below 50% of that rise after the plateau: Phan et al., "the fields are drained two weeks before rice harvest."

These are **not** SOS, POS and EOS and are never reported under those names. Optical EOS is senescence; this fall is drainage. Where Objective 4 compares against Paper 1, the comparison is stated as being between different quantities.

Measured on the 2017 baseline, 10 districts, 3,496 pixel-seasons: fitted trough
median **DOY 214.5** (2 August), rise-end **DOY 304.5** (31 October), and
fall-end **DOY 364.5** (30 December). All three fall inside §3.2's inherited
windows. Calendar plausibility is not field validation, so these dates are not
called agronomically correct.

**The three open parameters, derived and closed (2026-09-12).** All derived on the untreated 2017 baseline, 25 districts, 10,000 pixel-seasons, by rules stated before computing, and fixed. None is re-tuned on a treated season.

- **Smoothing: OFF on the radar path.** Rule: retain the arm with higher three-marker completeness while keeping median markers inside §3.2. Measured — unsmoothed **88.7%** complete against smoothed **54.0%**, both arms' medians inside §3.2. The Whittaker step is inherited from Paper 1 for optical comparability and on a step-shaped index it suppresses the drainage fall. It is retained on the optical path and not used on the radar path.
- **Minimum rise: 5.32 dB.** The 5th percentile of the trough-to-plateau rise among the 2,554 baseline pixel-seasons whose three markers all land inside §3.2 — calibrated to admit 95% of demonstrably well-behaved seasons.
- **Retention rule.** A pixel-season is retained iff it is eligible on §3.11's ≥14-dekad count, all three markers are recovered, all three lie inside §3.2, and the rise clears 5.32 dB. A failure is recorded with its reason and enters §3.10's diagnostic as a failure — the role non-convergence played under the withdrawn double-logistic.

**Measured baseline retention: 24.3%, and it is reported as a result rather than tuned away.** That is below Paper 1's optical pipeline (about 60% retained). The retained set has a median rise of **8.50 dB** against roughly 3.7 dB across all pixel-seasons, and median breakpoints at DOY **214.5 / 284.5 / 334.5**, positions consistent with the Odisha *Sali* calendar. The gate separates pixel-seasons whose radar trajectories satisfy the declared rice-like shape, eligibility and rise criteria, from a cohort drawn at 0.5 mask purity (§3.5) where up to half of each 30 m cell may not be rice. *(Corrected 2026-09-15, eleventh pass. This read "— transplanting in early August, heading in mid-October, harvest at the end of November, which is the Odisha Sali calendar. The gate is **separating pixels that behave like rice**". **Both halves are withdrawn.** Naming DOY 214.5 "transplanting" states an agronomic date this study never observed — there is no field reference anywhere in it (§4.3.1) — and a screen on trajectory shape cannot establish crop identity: it admits any pixel-season whose VH/VV trajectory satisfies the criteria, rice or not. The withdrawal note below this list withdraws the **estimator**, and left these two claims standing; they are withdrawn here, in place.)* **The cause of the retention difference is not identified here.** It cannot be separated among mask classification, signal quality, estimator behaviour and the screening rule itself, and this study does not attempt to. *(Corrected 2026-09-15, twelfth pass: this read "**The loss measures the mask, not the method.**" That named one of four candidate causes as the answer, on no evidence that separates them, and it is withdrawn.)* Two consequences are stated rather than left implicit: §3.10's attrition diagnostic becomes more important, not less, since three quarters of the frame is now screened out and the relationship between that screening and exposure has to be measured rather than assumed; and the retained panel is still roughly 21,900 pixel-years against Paper 1's 6,850, so power is not the binding constraint. **§3.10's diagnostics do detect associations between retention and some exposure indicators** — see §4's attrition-trigger reporting — so nothing here should be read as establishing that exposure-related selection is absent.

**Third calibration outcome: the feature-extraction estimator is itself superseded (2026-09-12, third entry).** Everything in the four paragraphs above, from "Radar phenometrics are read as features" to the end of the retention paragraph — which until 2026-09-15 ended "the loss measures the mask, not the method", a sentence now withdrawn in place — is **withdrawn as the primary specification** and retained as the record of a step that had to be taken to see the next one. What broke it, in order, each measured on the untreated 2017 baseline:

1. **§3.2's windows were binding, not satisfied.** 54% of retained trough estimates sat on the LAST dekad inside §3.2's trough window and 35% of headings on the last dekad inside its heading window. Free the search and only 35% of troughs and 55% of headings remain inside §3.2, in one direction across all three markers and all 25 districts: the radar breakpoint distribution lies **later** than the positions of Paper 1's optical bounds, so those bounds are **not transferable** across these measurands — the separation is roughly 40–60 days. *(Reworded 2026-09-14, ninth pass: this read "**the inherited windows are 40–60 days too early for the radar season on this coast**". "Too early" judges an optical bound against a radar distribution, which this study cannot do; only the separation and its consequence for transfer are reported.)* The claim two paragraphs above that all three markers land inside §3.2 rested on the median, and the median was inside while most units were pinned to a boundary.
2. **Per-pixel marker dates carry σ ≈ 18 days**, and no threshold reduces it. Each dekad aggregates two 5-day bins (§1.4); one series built from the first bin of every dekad and another from the second give two estimates of the same season from disjoint observations on the same grid with the same orbit mix, so their disagreement is a **scaled disagreement statistic**, σ = sd(difference)/√2 — not a measured error (§1.5.6 constraint 2). Half-series σ: trough 21.9 d, heading 35.3 d, harvest 40.9 d for the crossing rule. A Monte Carlo at the measured 2.03 dB dekadal noise returns 12–27 d **separately**. *(Reworded 2026-09-14, ninth pass: this read "returns 12–27 d **independently**". The Monte Carlo reads the same estimator and the same assumed noise level, so it is a separate calculation, not an independent one.)* Within-one-dekad agreement is **flat** at .55/.41/.39 across every bin of rise amplitude from 3 dB to 12 dB and every bin of fit signal-to-noise from below 1 to above 3 — so the 5.32 dB minimum rise bought no precision and is withdrawn.

**The primary estimator is now the five-segment piecewise-linear season model (PLSM)**, in `python/extract_phenometrics_sar.py`:

    a0 --decline--> b1 --rise--> p --plateau--> p --fall--> b2 --flat-->
       [start,t1]      [t1,t2]      [t2,t3]       [t3,t4]     [t4,end]

Four levels enter linearly and are profiled out by weighted least squares; only the four breakpoints are searched, on the dekad grid. **The breakpoints are the markers**, so the 0.80 and 0.50 crossing fractions are removed rather than re-tuned. The leading **decline** is what a plain trapezoid lacked: on this coast the series starts high (previous crop and pre-monsoon cover) and falls into the radar-dark phase, and forcing a flat base there splits the residual between the two and displaces the trough by weeks (Kendrapara 2019: fitted base −7.56 dB against −6.05 observed early and −9.50 at the real trough, rmse 1.02 dB, trough placed at DOY 304.5 when it is plainly 254.5). Median district-season rmse 0.397 → 0.316 dB. PLSM was chosen over the crossing rule by a rule stated before the test — the smaller split-half σ on the markers §3.8 uses — and it wins on heading (35.3 → 26.2 d) and harvest (40.9 → 25.2 d) on every statistic, halving the median disagreement on all three markers. The crossing rule and the intermediate trapezoid are retained in the module and reported as pre-declared robustness arms (`xr_*` and `tz_*` columns).

**Correction to the split-half figures above (2026-09-13).** The two numbers quoted in the previous paragraph as PLSM's — heading 26.2 d and harvest 25.2 d — are the **trapezoid's**. PLSM's own split-half reliability had not been measured when that paragraph was written; its column was filled from the trapezoid's. Measured, same protocol, untreated 2017 baseline, 3,021 testable pixel-seasons: trough **33.6 d** (.33 within a dekad), heading **23.4 d** (.38), drainage **22.5 d** (.40), harvest **27.8 d** (.32), against the trapezoid's 24.5 / 26.2 / 28.0 / 25.2 on 2,553 and the crossing rule's 21.9 / 35.3 / — / 40.9 on 3,360. The three columns are not on the same pixel set, since each estimator admits a different set of pixel-seasons in both halves. **PLSM still beats the crossing rule on heading and harvest**, which is the comparison the selection rule was written for; against the trapezoid it is better on heading and drainage and **worse on the trough**, so that rule does not by itself settle trapezoid against PLSM. The adoption of PLSM rests instead on the evidence stated in the previous paragraph and not on variance: the trapezoid is the wrong shape here, its flat pre-season base displaces the trough by weeks on a season that starts high, and district-season fit rmse falls 0.397 → 0.316 dB against a sampling error of 0.122 dB. A 50-day displacement is not traded against 9 days of σ. **Consequence for reporting:** under PLSM the trough is the weakest of the four markers, and `trough`, `veg_days` and `season_days` are correspondingly the weakest outcomes in §3.8 — which is the same fact the marker-naming paragraph below states physically. Per-pixel `rise_db` carries σ 2.13 dB against a median of 6.1 dB. The measured table is committed as `results/splithalf_reliability.csv`.

**Marker names, stated precisely.** `t1` is the fitted **end of the dark phase**,
not a transplanting date: a puddled flooded field and a dry bare pre-monsoon
field are both radar-dark in VH/VV, so the dark phase can span land preparation
and early crop development. The lag from transplanting is not resolvable in
these data and is not claimed. `t2` is the fitted end of the rise
(heading-related interpretation), `t3` the fitted end of the plateau
(drainage-related interpretation), and `t4` the fitted end of the fall
(harvest-related interpretation). The parenthetical readings are physical
interpretations, not field-validated agronomic dates. These remain not SOS, POS
and EOS.

**The unit of analysis moves to the district-season (§3.8).** *(Scoped 2026-09-15, eleventh pass: the numbers in this paragraph are the ones that were in front of the author when the move was made, and they are left as the record of that. They are **not** the reason the district-season panel is primary. §3.8 fixes the primary estimand by **declaration** — the breakpoint fitted to the district-mean curve is the quantity the hypotheses are about — and neither the simulated ±1.3 d below nor any measured dispersion selects a level of estimation after the fact. Read this paragraph as history, and §3.8 as the specification.)* The district-mean dekadal series has a sampling standard error of **0.122 dB** against 2.03 dB per pixel, and a Monte Carlo on a **synthetic** season at that assumed noise level recovers its own **planted** breakpoints to **±1.3 d** with no detectable bias — conditional performance of a simulation, not a measured precision of the real panel, which holds no repeat observation at district scale to check it against. Measured within-district dispersion of heading across the nine seasons is **7.8 d**, set beside that ±1.3 d simulated figure. *(Narrowed 2026-09-14, fifth pass: this read "— six times the measurement error, so the year-to-year movement the difference-in-differences uses is signal". **Withdrawn.** ±1.3 d is a Monte Carlo result under its own synthetic-trajectory and noise assumptions, not a matched empirical error assessment for these district-seasons, so the ratio of the two does not separate real seasonal change from measurement error, and "is signal" claims more than the comparison supports.)* The pixel panel is retained because §3.10's attrition diagnostic is a statement about pixels, and as a robustness arm; it no longer carries the headline. *(Narrowed 2026-09-14, fifth pass: the paragraph also read "Per-pixel measurement error of this size is classical error in the **outcome**: it inflates standard errors and does not bias the treatment coefficient." **Withdrawn.** Outcome error leaves the treatment coefficient unbiased only if it is independent of exposure with zero conditional mean; neither is established here, and §4.1's censoring test — a late-season backscatter change moving a fitted breakpoint months upstream — is a direct reason to doubt both, since the deformation is driven by the same storm-season signal the exposure indicator marks. No classical-error assertion is made, and this is one of the reasons the cyclone contrasts stay descriptive.)* The observed disagreement is reported rather than smoothed over. ~~No published Sentinel-1 rice-phenology study we could find reports a marker timing uncertainty in days at all … so this measurement is a contribution of the paper.~~ **WITHDRAWN 2026-09-14: tested and false.** A literature check on that date found at least three published studies reporting rice marker timing error in days — Manago et al. (2020, *Agriculture* 10(12):625) with a transplanting-date SD of ≈ 5–6 d against farmer-interview dates; Wang et al. (2022, *Sustainability* 14(13):8009) with a 3.08 d average error against field measurement; and Zhao et al. (2024, MARC, *ESSD* 16:3893) with bias, MAE and RMSE in days. The claim was a priority claim and it does not hold. What survives is a statement about the **kind of quantity**, set out with the search of record in **§1.5.5**. *Corrected 2026-09-14 (fourth pass): the first version of this replacement said those studies report accuracy "at site or irrigation-block scale in one region" — **false of MARC**, a monsoon-Asia product on a 0.5° grid — and said the two scales "are comparable within one estimator" and that "the contribution is that comparison", which §1.5.4 item 1 withdraws. Both were fixed in §1.5 and left standing here, in the paragraph that introduced them. That is the seventh instance in five days of a correction written in one place while the claim it corrects stood in another.* The accurate distinction is between **measurands**: those three studies report **agreement with an external reference** (accuracy, whose value depends on the reference), while this study reports **disagreement between two observations of one quantity by one estimator along different orbit paths** (repeatability, which uses no external reference and says nothing about accuracy). The two are not directly comparable in either direction, and MARC's 27.62 / 28.32 d RMSE must not be set beside σ as though they measured the same thing. The **district-season ±1.3 d is a separate, simulated quantity** and is not combined with σ into any ratio or scale claim (§1.5.4 item 1). The contribution rests on the measurement work itself and on §1.5.4's items 2–4, not on being first and not on a comparison of incomparable numbers. (Pazhanivelan et al. 2025, *Sci Rep* 15:8202 does validate classification spatially, κ 0.77–0.87, and gives no timing error in days — that part of the original sentence was correct but it does not support the general claim built on it.)

**The rise screen, and why the nominal test cannot be used.** A pixel-season or district-season is retained iff it is eligible on §3.11's ≥14-dekad count, an admissible shape is found (a rise above the dark phase, a fall after it, a start above the dark phase), and the fitted rise is significantly positive at 5% one-sided on the series' own residual variance — tested against a **selection-aware critical value**, because the fit chooses among thousands of breakpoint quadruples. Measured, not assumed: on pure noise with no season at all, **29% of series clear the nominal value.** The parametric-bootstrap critical values, tabulated in `python/plsm_null_t.csv` and `plsm_null_t_ar1.csv` by `python/calibrate_plsm_null.py`, are **t95 = 2.94** (pixel grid, 4,322 designs) and **4.17** (district grid, 12,649 designs, AR(1) null at ρ = 0.25), against a nominal 1.71; they hold the false-positive rate at **0.048**. Which null applies where is also measured rather than assumed: fitted-residual lag-1 autocorrelation is **−0.22** at pixel level (586 baseline pixel-seasons), which makes the i.i.d. table conservative there, and **+0.21** at district level (25 baseline districts), which makes it too permissive, so the district fit takes the AR(1) value. ρ = 0.40 (t95 = 4.98) ships as the conservative arm and costs seven of 225 district-seasons. An absolute dB floor is retained only as a **specification-curve** argument (`--min-rise-db`, default 0), never as a fixed threshold.

**No phenometric calendar gate in the primary specification.** Required by finding 1 above. It also removes the class of gate that deleted Paper 1's treated post-period — see §3.2.

**The measured fitted-breakpoint calendar.** All 225 district-season curves fit;
**208 clear the screen**. Median fitted breakpoints are `t1` **DOY 249.5**
(6 September), `t2` **DOY 314.5** (10 November), `t3` **DOY 324.5**
(20 November), and `t4` **DOY 384.5** (19 January), with the operational
interpretations defined above. Odisha's 108 district-seasons all fit (median rise
2.47 dB) and West Bengal's 54 all fit; **all 17 non-estimable district-seasons are
Andhra Pradesh** (Guntur, Krishna, Visakhapatnam, Vizianagaram, West Godavari),
whose amplitudes are much weaker (Visakhapatnam 0.76 dB, West Godavari 1.15 dB).
The association with the delta double-crop context is descriptive; its cause is
not identified. Five of the seventeen fall in the untreated 2017 baseline, so
the pattern is not confined to treated seasons. Pixel-level retention is 35.3%.

**Nothing is loosened to raise sample.** Two changes raise it (freeing the windows, withdrawing the amplitude floor) and three lower it (the calibrated critical value, district-level Gate 1 in §3.1, requiring all four breakpoints). Every parameter was derived on the untreated 2017 baseline or by Monte Carlo under a null, before any treated season was read.

**Orbit combination and normalisation.** A single relative orbit yields a clean 12-day series but is fragile: measured 2026-09-09, East Godavari's orbit 19 falls to 18 dates with a 36-day gap in 2024, and Bhadrak's orbit 48 carries 24-day gaps from 2022 onward. All available relative orbits are therefore combined. Because backscatter depends on incidence angle and look direction, each orbit's series is normalised to a common level before compositing by subtracting that orbit's within-season median VH/VV from its own observations and adding back the district-season median across orbits; this removes the constant geometric offset between orbits while preserving the temporal shape each orbit records. Orbit availability is district-specific and is not assumed uniform — Purba Medinipur is ascending-dominant, Bhadrak descending-dominant, and East Godavari has effectively no ascending coverage in five of seven measured seasons — so the set of contributing orbits is recorded per district-season in the exported panel and reported.

**Calibration requirement (stated 2026-09-09, not optional).** The backscatter trajectory described above is documented for **direct-seeded** rice in the Mekong Delta, expressed in days after sowing. Coastal eastern India grows **transplanted** aman rice, whose establishment differs: puddling, transplanting shock and the flooded period preceding canopy closure do not map onto a direct-seeded timeline. The physical mechanism is the same — a flooded surface returns weakly, a developed canopy returns strongly — so the curve shape is expected to hold, but the timing offsets are not transferable. Before any phenometric is reported, the fitted SOS, POS and EOS distributions are checked against the district crop calendars of §3.4 and against Gate 2's bounds, and the amplitude and offset parameters are calibrated on the untreated 2017 baseline season rather than imported from the literature. If that check fails for a state, the failure is reported for that state rather than absorbed by re-tuning.

**Sentinel-2's remaining role.** Optical NDVI is retained only where the observation record supports it — the post-monsoon window, and therefore harvest timing alone — as a supplementary cross-check on EOS, never as the source of SOS or POS and never as the headline. The 2026-09-08 measurement above defines where that boundary falls.

### 3.1 Gate 1 — peak-relative sampling-density rule (QC gate; no longer described as the headline contribution — see the justification test below)

**Locked, carried over unchanged from the prior draft's §3.3.**

For each district × season × phenometric:

1. Group all valid pixel-day observations at the district's candidate-cohort pixels (§3.6) within the season window into 5-day DOY bins.
2. Compute *N(b)* = count of valid observations contributing to bin *b*, for that district × season.
3. Identify *N_peak* = max(*N(b)*) across the bins in that district × season.
4. Admit bin *b* to phenometric extraction **iff** *N(b)* ≥ r × *N_peak*, or *b* is the peak bin itself. Bins built from too few observations relative to the season's best-sampled bin carry an unreliable composite median and are excluded.

**Direction corrected 2026-09-09.** The rule frozen at `2cf493a` read *N(b)* **≤** r × *N_peak*, admitting sparsely-sampled bins and rejecting well-sampled ones. Worked through: with *N_peak* = 100 and r = 0.5, a bin holding 10 observations was admitted and a bin holding 80 was rejected, the peak surviving only by its explicit exception. On the optical panel that would have discarded precisely the post-monsoon bins carrying almost all of the usable signal (see the phenometric-method note above) and retained the sparse monsoon bins. The inequality is reversed. The stated rationale was separately wrong: it argued about smallholder planting waves, which concern the distribution of *transplanting dates*, while *N(b)* counts *observation availability*. Those are different quantities, and only the second is what the gate measures.

**r values are not carried over.** The frozen values (0.75 for SOS, 0.50 for peak and EOS) were reasoned from optical cloud statistics under a rule pointing the other way, so neither the numbers nor their justification transfers. They are re-derived on the untreated 2017 baseline season (§1.1) before any treated season is fitted, and the derivation is recorded in `analysis/decisions_log.md` before any coefficient using them is reported.

**What the gate is for under Sentinel-1, stated honestly.** Gate 1 was designed against an optical record in which *N(b)* varies by an order of magnitude with cloud cover. Under Sentinel-1 it varies far less: acquisitions are weather-independent and combining orbits gives a median gap of 3–7 days across the season, so most bins carry a comparable number of observations and the gate excludes correspondingly few. Its remaining function is genuine but narrower — screening bins that fall in an orbit gap, where a composite median rests on one acquisition rather than three. This protocol therefore no longer describes Gate 1 as the study's headline contribution. Whether it earns a place at all is settled empirically, not by assertion, under the test below.

**Gate 1 justification test (pre-declared, added 2026-09-09).** Phenometrics are extracted twice on the same cohort and the same panel, once with Gate 1 applied and once without, and the two are compared on:

- **fit quality** — distribution of RMSR (§3.11) and the share of pixel-seasons whose fit is accepted at all;
- **temporal stability** — for each pixel, the dispersion of its phenometric across the nine seasons, after removing season means, since a pixel's true planting date should not swing wildly year to year;
- **spatial coherence** — within-district dispersion of each phenometric, and the semivariance between neighbouring cohort pixels;
- **orbit agreement** — where a district-season is covered by two or more relative orbits, the phenometric estimated from each orbit independently, which is the closest available proxy for repeatability.

Gate 1 is retained only if it improves these on the majority of criteria. If it does not, it is reported as a tested and rejected QC step, which is a result rather than a failure. Note what this test deliberately is **not**: a comparison against observed dates. No field-observed transplanting or harvest dates exist for these districts (§3.4), so no accuracy criterion can be evaluated, and the review comment that the gate should "improve date estimates against a baseline" cannot be executed as stated. Substituting agreement with another satellite product would test resemblance to that product, not correctness. The four internal criteria above are what the available evidence can actually support.

> ### Amendment, 2026-09-13 — the Gate 1 justification test is RUN as declared, on the full nine-season panel. Verdict: **Gate 1 is rejected at pixel level as a tested QC step.**
>
> The test above was pre-declared on 2026-09-09 with four named criteria and a decision rule. Until today it had **not** been run as declared. §3.1's third 2026-09-12 entry decided the same thing on four summary statistics measured on the **2017 baseline season alone** — median valid dekads, minimum, the §3.11 fraction, retention — and three of the four declared criteria (temporal stability, spatial coherence, orbit agreement) cannot be evaluated on one season at all. The decision was right; the evidence was narrower than the declaration. `python/gate1_justification.py` runs it properly: the whole panel extracted twice, `--gate1-r 0.50` against the radar default of 0.0, 90,000 pixel-seasons each.
>
> **Correction, 2026-09-14 — this is a retrospective operationalisation of predeclared domains, not a fully prespecified test.** The four *criteria* were genuinely predeclared on 2026-09-09. The *statistics* standing for them, and the rule that every sub-statistic must move favourably, were chosen on 2026-09-14 — before this comparison ran, but **after** §3.1's third 2026-09-12 entry had already measured the direction on the 2017 baseline (retention 0.2426 with the gate against 0.2544 without). So "retention share, higher is better" was selected already knowing which way retention moved. The verdict is unaffected — the gate worsens the criteria it was supposed to improve, and by margins far larger than any choice of statistic would flip — but the amendment's phrase "run as declared" overstates it and is corrected here. Found by an external re-audit, not by the author.
>
> **The statistics standing for each criterion are declared in that module's docstring**, because this section names the criteria without fixing them. A criterion counts as improved only if **every** statistic it carries moves favourably; where they disagree it is MIXED, and **MIXED is not an improvement** — this section retains Gate 1 only if it *improves*, so ambiguity resolves against retention.
>
> | criterion | on each arm's own retained set | on the fixed common subset |
> |---|---|---|
> | fit quality | **WORSENS** (0 improve, 2 worsen) | **WORSENS** |
> | temporal stability | MIXED (1 improve, 2 worsen) | **WORSENS** (0 improve, 3 worsen) |
> | spatial coherence | MIXED (2 improve, 4 worsen) | MIXED (2 improve, 4 worsen) |
> | orbit agreement | MIXED (2 improve, 4 worsen) | not evaluable at this level |
>
> **Improves 0 of 4 evaluable criteria. Gate 1 is rejected.** The verdict was already
> determined before the fourth criterion was computed — with four criteria a majority
> needs three, and the first three gave zero — but it was run and reported anyway,
> because "the declared test was not run" is the finding this exercise exists to prevent.
>
> **Orbit agreement is, to the precision that matters, unchanged.** It is run through
> `python/orbit_agreement.py --gate1-r 0.50`, i.e. the committed estimator with the gate
> switched on, not a second copy of it. The paired-orbit **scaled between-orbit
> disagreement statistic changes** by **0.0006 to 0.016 days** on a quantity of roughly 26 days, and the within-tolerance
> share against the 2017-fixed tolerances by **0.00002 to 0.0002**; the signs are mixed,
> which is what "no effect measured through a noisy channel" looks like. The comparison
> threshold was **not** loosened after seeing these numbers — doing so would be
> result-aware — so the module records six tiny non-zero changes and returns MIXED, and
> the magnitudes are quoted here so a reader can see that MIXED here means *negligible*
> rather than *conflicting*. Either reading rejects the gate.
>
> **The gate does not merely fail to help; it makes the measurement worse.** Retention falls from **0.3527 to 0.3378** (−1.5 percentage points, 1,335 pixel-seasons) and median RMSR rises from **1.9847 to 2.0292 dB**. And on the **28,612 pixel-seasons retained in both arms** — the same pixels, so sample selection cannot explain it — within-pixel dispersion about each pixel's own mean, season means removed, **rises on all three markers**: trough 22.68 → 23.24 d, heading 17.66 → 17.92 d, harvest 23.16 → 23.27 d. A gate that deletes five-day bins removes observations from the dekadal aggregation, and fewer observations per dekad is a noisier series. That is the mechanism, and it is measured rather than argued.
>
> **Why both samples are reported, and why it matters.** Gate 1 changes which pixel-seasons are retained at all, so a gate that happened to delete the noisiest pixels would improve every dispersion statistic **by sample selection alone**, with no better measurement. Every criterion is therefore computed twice — on each arm's own retained set, and on the pixel-seasons retained in both — and `gate1_justification.py` has a self-test that plants exactly that confound and checks the two columns separate it. Here the gate fails on both, so the question does not arise; the machinery is in place because the opposite result would have needed it.
>
> **Status.** Gate 1 is **reported as a tested and rejected QC step at pixel level**, which this section already anticipated is "a result rather than a failure". It remains applied to the **district-mean curve** as a 0.5 coverage rule, for the different reason given in the third 2026-09-12 entry — a district mean over a shifting subset of pixels is not a series of the same object — and that role is untouched by this test, which is a pixel-level test. §3.2's amendment of this date records that the 55-bin variant offered in the window note below is contingent on a pixel-level gate existing, and is therefore moot at that level.
>
> Full table: `results/gate1_justification/`.

**Window note (2026-09-07).** Gate 1 is unchanged by the §1.4 window correction: *N_peak* and the admission rule are computed over the 31 core Kharif bins (bins 1–31 of the 55-bin window, DOY 150–304; the locked rule's core window was written as 152–304 and moves two days earlier so that its bin edges coincide with the §1.4 grid — the r-values and the admission rule are untouched) exactly as locked above. The 24 extension bins (DOY 305–424) are not subject to Gate 1 and enter fitting after the §3.6 cloud/SCL mask only — the same treatment Paper 1 gave its extension dekads, which had no sampling-density gate. Applying Gate 1 over all 55 bins (with *N_peak* recomputed over the full window) is reported as a supplementary sensitivity.

**Gate 1 on the radar path, split by level (2026-09-12, third entry).** The peak-relative sampling-density rule is **not applied at pixel level** on the radar substrate and **is applied to the district-mean curve** at 0.5 coverage. The reason is that Gate 1's purpose is optical: a sparse five-day bin means few cloud-free looks, so its dekadal mean is dominated by whatever passed the cloud mask. Sentinel-1 acquisition is an orbit schedule, not a weather process — a bin's count is set by which relative orbits cross the tile in those five days, repeating on a 12-day cycle every year — so a peak-relative gate deletes bins for a cause that does not operate. Measured on the 2017 baseline, no gate against r = 0.50: median valid dekads 26 against 24, **minimum 19 against 10**, fraction meeting §3.11's ≥14 rule 1.0000 against 0.9993, retention 0.2426 against 0.2544. The gate manufactures the only §3.11 ineligibility in the entire untreated baseline. At district-mean level the concern is real and different in kind: the mean over a shifting subset of pixels is not a series of the same object, and a dekad carried by 6 of 400 pixels is a composition step rather than phenology (Guntur 2017, DOY 214.5, −11.18 dB against −7.8 dB in the dekads either side). Gate 1 is therefore applied there, as a coverage rule, and is reported as such.

### 3.2 Gate 2 — phenometric quality bounds (bounds carried from Paper 1's Gate B; corrected 2026-09-07)

| Phenometric | Lower bound (DOY) | Upper bound (DOY) | NDVI / EVI amplitude requirement (Paper 2 addition) |
|---|---|---|---|
| SOS (transplanting) | 155 | 240 | NDVI rise ≥ 0.20 over 30 d |
| Peak NDVI date | 240 | 320 | Peak NDVI ≥ 0.55 |
| EOS (harvest) | 280 | 380 | NDVI decline ≥ 0.20 over 30 d |

Pixels whose extracted phenometric falls outside these bounds are flagged and excluded from the panel. For district-year reporting, a district-year cell whose median SOS, POS or EOS falls outside the same bounds is flagged as biologically implausible, matching Paper 1's district-year Gate B convention.

**Correction to the correction (2026-09-12).** The note below states that the DOY bounds do not transfer to the radar substrate. It was written from double-logistic fits that are now withdrawn (§3 lead-in), and it is **wrong**. Read as features rather than fitted, all three radar markers land inside these windows on the 2017 baseline: trough DOY 214.5 in the 155–240 row, heading DOY 304.5 in the 240–320 row, harvest DOY 364.5 in the 280–380 row. **The DOY bounds are carried over from Paper 1 unchanged.** The amplitude column still does not transfer, for the units reason given below.

**Unit correction (2026-09-09, part 3).** The DOY bounds above are calendar bounds and transfer to any substrate unchanged. **The amplitude column does not.** It is stated in NDVI units, and since the substrate moved to the Sentinel-1 VH/VV ratio (§3 lead-in) the index is a backscatter ratio in decibels spanning roughly −13 to −3 dB, against which "NDVI rise ≥ 0.20" has no meaning. There is no principled conversion — rescaling 0.20 of an NDVI amplitude onto a 10 dB range would be an invented number carrying a citation it does not have. The §3 lead-in sentence "Gate 2 (§3.2) and Gate 3 (§3.11) apply unchanged" is therefore true of the DOY bounds and of the gate structure, and false of these three thresholds; it is corrected by this note rather than rewritten, since the structure it refers to does carry over.

The dB equivalents are **derived on the untreated 2017 baseline season** before any treated season is fitted, by the same procedure §3.1 fixes for its r values and §3.3 for its 3 dB inundation criterion, and recorded in `analysis/decisions_log.md` before any coefficient using them is reported. `python/fit_phenometrics.py --derive-baseline` computes the distributions; the script has **no defaults** for these quantities and refuses to run the gates without them, so a placeholder cannot silently become the study's threshold. The criteria retain their §3.2 meaning: a 30-day rise at SOS, a fitted peak level, a 30-day decline at EOS, each read off the fitted curve.

**Limb asymmetry (measured 2026-09-09).** The rise and decline rows of the table above carry the same number. On the VH/VV curve the two limbs are not symmetric — the descending limb is the slower one — so a single threshold set from the rising limb rejects admissible harvests. Measured on a synthetic season with ascending slope 0.10 and descending slope 0.08, the median 30-day rise was +5.1 dB against a median 30-day decline of −4.3 dB, and a common threshold at the rise limb's 5th percentile rejected 36% of otherwise valid EOS values. The two thresholds may therefore be set separately, with the values and the reason recorded in the decisions log; set equal, they reproduce §3.2 exactly.

**Correction note (2026-09-07).** An earlier version of this table gave SOS 160–210, peak 220–280 and EOS 270–310 and labelled them "carried from Paper 1". Those are not Paper 1's bounds. The submitted Paper 1's Gate B windows are SOS 155–240 (early June to late August), POS 240–320 (late August to mid-November) and EOS 280–380 (early October to mid-January) (RSASE-D-26-02830 §3, Gate B), and Paper 1's own retained-panel medians — SOS 205, POS 289, EOS 342 — would have failed the earlier table for two of the three phenometrics. The DOY bounds are now Paper 1's verbatim. The amplitude requirements in the last column are Paper 2 additions and were never part of Paper 1's Gate B. Paper 1's bounds were predeclared from the Odisha Kharif calendar; state-specific bounds for West Bengal (aman) and coastal Andhra Pradesh are reported as a supplementary sensitivity, with Paper 1's bounds as the headline for comparability.

**Second correction to the correction (2026-09-12, third entry): the DOY bounds do NOT transfer, and this is the last word on it.** The 2026-09-12 note above, which withdrew the 2026-09-11 note and reinstated the bounds, was itself built on medians. At unit level the bounds **bind**: 54% of retained trough estimates sat on the last dekad inside the 155–240 window and 35% of headings on the last dekad inside 240–320. Freeing the search leaves only 35% of troughs, 55% of headings and 47% of harvests inside these windows, and the direction is the same for all three markers in all 25 districts: the radar breakpoint distribution lies **later** than the positions of Paper 1's optical bounds, so those bounds are **not transferable** across these measurands. The measured radar-trajectory breakpoints are the fitted end of the dark phase at DOY 249.5, end of the rise at DOY 314.5 and end of the fall at DOY 384.5, against windows of 155–240, 240–320 and 280–380. **The radar breakpoint distribution is roughly 40–60 days later than the positions of those optical bounds in these data.** Because the two measurands differ and neither is ground truth, that establishes **non-transferability** — Paper 1's bounds would censor much of this radar distribution if carried across sensors — and **not** that Paper 1's windows were incorrectly timed for their own sensor. *(Corrected 2026-09-15, tenth pass: this sentence read "**These are Paper 1's optical windows and they are 40–60 days too early for the radar season on this coast.**" The ninth pass added the non-transferability statement earlier in this same paragraph and left this sentence standing three sentences later — the same defect, inside one paragraph.)* The primary specification therefore applies **no phenometric calendar gate at all** (§3 lead-in); §3.2's structure is retained only for the optical path and for the superseded robustness arms, where the windows are made structural — the search grid is restricted to them — so a marker can never be refused for landing where the search was permitted to look.

> ### Amendment, 2026-09-13 — Gate 2's DOY bounds are NOT applied as an exclusion on the primary path. §3's "applies unchanged" and this section's "excluded from the panel" are both false for it, and are corrected here.
>
> §3's lead-in says "Gate 2 (§3.2) and Gate 3 (§3.11) apply unchanged", and this section says "Pixels whose extracted phenometric falls outside these bounds are flagged and excluded from the panel." **Neither is true of the primary five-segment estimator.** `plsm_retain` applies §3.11's dekad count, shape admissibility and the selection-aware rise screen, and **no calendar window at all** — its docstring and the module note say so explicitly, and the reason given there is this section's own: a DOY ceiling "removes the class of gate that deleted Paper 1's treated post-period." §3.11 received exactly this correction on 2026-09-12 ("Gate 3 on the radar path, revised"); §3.2 did not, and the omission stood until today. The decision is unchanged and is still the right one — what was wrong was the protocol asserting an exclusion that the code deliberately does not perform.
>
> **Measured, on the committed pixel panel** (`python/gate2_state_sensitivity.py`, `results/gate2_state/`): Gate 2 rejects **0 of 5,184** Andhra Pradesh, **0 of 17,886** Odisha and **0 of 8,671** West Bengal pixel-seasons that reach it, because it rejects nothing. Had the bounds been applied as this section declares:
>
> | state | marker | bound | 5th pct | median | 95th pct |
> |---|---|---|---:|---:|---:|
> | Odisha | trough | 155–240 | 184.5 | **254.5** | 304.5 |
> | West Bengal | trough | 155–240 | 194.5 | **254.5** | 304.5 |
> | Andhra Pradesh | trough | 155–240 | 184.5 | 234.5 | 294.5 |
> | all three | harvest | 280–380 | 324.5–334.5 | 364.5–374.5 | **422.0** |
>
> **2 of 9 state × marker medians lie outside the bounds** — trough in Odisha and West Bengal, each 14.5 d above the 240 ceiling — and **9 of 9** have a 95th percentile beyond the upper bound. More than half of two states' pixel-seasons would have been deleted on the trough ceiling alone.
>
> **The measured radar distribution sits outside Paper 1's optical bounds, and that is all it shows.** The measured trough median is **254.5**, above Paper 1's 240 SOS ceiling, and in the middle of the 245–265 range this section predicted before the panel was fitted. Paper 1's optical calendar bounds do not align with Paper 2's radar breakpoint distribution and would censor many radar estimates if transferred across sensors. This demonstrates **non-transferability between these different measurands**. It does **not** establish that Paper 1's optical SOS bound was mis-specified, identify a true agronomic onset, or reinterpret Paper 1's support loss. Those questions require analysis of Paper 1's own optical measurements or an independent field reference.
>
> *Withdrawn 2026-09-14 (eighth pass).* This paragraph read "**This confirms this section's own prediction rather than contradicting it**", quoting "The ceiling sat **below** the true onset, so it deleted precisely the district-years it was meant to bound." **Both the quoted sentence and the inference from it are withdrawn.** Paper 2's `t1` is an onset of canopy development in a VH/VV trajectory; Paper 1's SOS is an optical construct. §4.3.1 authorises no identity between them, this section's own closing paragraph says the fitted quantities are not the named ones, and a breakpoint in one sensor cannot locate a "true onset" against which another sensor's bound is judged too low.
>
> **The state-specific-bounds sensitivity declared in the correction note below is resolved, and not by running it as written.** It asks for "state-specific bounds for West Bengal (aman) and coastal Andhra Pradesh" as a supplementary sensitivity but **never specifies them** — no numbers appear anywhere in this protocol. Choosing them now, with the panel fitted and the markers known, would measure the choice rather than the data, and is exactly the discretion §3 exists to remove. What the sensitivity was *for* is the concern that bounds derived from the Odisha calendar screen one state more than another, and that is answerable without inventing anything: **the rejection rate is 0.0000 in all three states because nothing is excluded, and the largest between-state difference in the margin to the upper bound is 10.0 days** — the three states behave alike against one set of bounds. There is no differential-screening problem to correct, and no state-specific bounds are introduced. If they ever are, they must be declared before being applied and applied to all three states together.
>
> **What Gate 2's bounds are, from here on.** A **reported calendar plausibility check**, not an exclusion rule: the fitted marker distributions are compared against them per state and the comparison is reported, which is what §3.4 Tier 2's "these catch gross error; they cannot measure fine error" already describes. This does **not** licence reading the breakpoints as SOS, POS and EOS — §4.3.1 stands. The MARC offset (+50.4 d on harvest) and the §3.3 withdrawal warn against assuming agronomic identity; neither is field validation or proof of the true agronomic date.
>
> **The 55-bin Gate 1 variant declared in §3.1 is contingent on Gate 1 surviving.** §3.1's window note offers "applying Gate 1 over all 55 bins (with *N_peak* recomputed over the full window)" as a supplementary sensitivity. That variant is a variant *of a gate*; if §3.1's justification test rejects Gate 1 at pixel level, there is no pixel-level gate for it to vary and the sensitivity is moot at that level. It is recorded here as contingent rather than left to look unrun. See §3.1's amendment of this date.

**What this does and does not say about Paper 1.** Paper 1's optical calendar bounds do not align with Paper 2's radar breakpoint distribution and would censor many radar estimates if transferred across sensors. This demonstrates **non-transferability between these different measurands**. It does **not** establish that Paper 1's optical SOS bound was mis-specified, identify a true agronomic onset, or reinterpret Paper 1's support loss. Those questions require analysis of Paper 1's own optical measurements or an independent field reference.

*Withdrawn 2026-09-14 (eighth pass).* This paragraph read "**And this settles a question about Paper 1** … The ceiling sat **below** the true onset, so it deleted precisely the district-years it was meant to bound. Paper 1's 'no treated support in 2022' is a mis-specified window, not attrition." **Every clause of that is withdrawn.** It is a cross-sensor construct-identity claim: it treats the radar's end-of-dark-phase breakpoint as the same quantity Paper 1's optical SOS ceiling was bounding, and then reads Paper 1's attrition through it. Paper 2 measures neither Paper 1's SOS nor any agronomic onset, and it holds no field reference against which either could be judged. Whether Paper 1's ceiling was well chosen, and what caused its support loss, are questions for Paper 1's own optical measurements or for independent field data — not for this paper, in either direction.

### 3.3 SAR sanity check (not fusion)

**Repurposed 2026-09-09: this section is no longer a falsification check on optical SOS. It defines a cyclone inundation-intensity variable.**

**Why the frozen version cannot stand.** It required a district × cyclone unit to pass iff the median absolute deviation between optical SOS and a SAR flood date from a ±14-day landfall window was ≤ 10 days. That test is unpassable for calendar reasons, independent of any data. Against this protocol's own Gate 2 SOS bounds (DOY 155–240): Fani makes landfall at DOY 123, so its window spans DOY 109–137 and the nearest admissible SOS is **18 days** away; Bulbul lands at DOY 313, window 299–327, nearest admissible SOS **59 days** away. Titli (DOY 284), Sitrang (DOY 297) and Michaung are in the same position. Only Amphan, Yaas and Remal produce windows that touch the SOS range at all, and then only at its extreme edge. A cyclone in May can flood a field that is transplanted in July; those dates differ for a sound agronomic reason and their disagreement falsifies nothing. The frozen version also never defined how median VH and VV backscatter yield a flood *date* — only that the medians are computed.

**Why it cannot simply be corrected.** With the phenometric substrate moved to Sentinel-1 (§3 lead-in), a SAR-derived check on SAR-derived dates would compare a measurement against itself. There is no independent falsification available from this instrument.

**What the section now specifies.** Landfall-window backscatter measures something the study needs and has no other source for: **how much of each district was actually inundated by each cyclone**, as a continuous treatment-intensity variable rather than the binary exposure indicator of §1.1.

For each named cyclone *c* and each cohort pixel *p*, over a **±14-day window around landfall**:

- σ⁰_VH and σ⁰_VV are loaded from `COPERNICUS/S1_GRD` (IW, dual-polarisation), all available relative orbits, normalised as in the §3 lead-in.
- A **pre-event reference** is the median σ⁰_VH over the 30 days ending 5 days before landfall, on the same orbits.
- A pixel is scored **inundated** for cyclone *c* if its minimum σ⁰_VH within the landfall window falls at least **3 dB** below its pre-event reference. Low VH over smooth water and flooded/transplanted paddy is documented in the Sentinel-1 rice literature, including Phan, Le Toan & Bouvet (2021, DOI `10.3390/rs13050921`), but that literature does not validate this study's 3 dB cyclone-increment threshold. The threshold and window are re-derived on the untreated 2017 baseline season before use.
- `inundated_frac_{d,c}` = the share of district *d*'s cohort pixels scored inundated for cyclone *c*. This is the district-level intensity variable.

**How it enters the analysis.** `inundated_frac` is reported per district × named cyclone in the results table, and is offered to §3.8 A as a **continuous intensity term alongside** the binary severe-exposure indicators, never in place of them. The binary indicators remain the headline, because they derive from the IBTrACS rule recorded in the frozen working protocol (§1.1) before the full phenology extraction, whereas `inundated_frac` is measured from the same instrument that produces the outcome and is therefore not independent of it. Reported as a secondary specification and labelled as such. This is a prospective-timing statement supported by the repository history, not an OSF pre-registration claim (§5.2).

**What is given up, stated.** The frozen protocol offered SAR as an independent falsification of the phenometrics. That is no longer available and this section does not pretend otherwise. Verification of the phenometrics now rests on the internal-consistency measures of §3.4 Tier 1 — orbit repeatability, inter-seasonal stability, spatial coherence and fit quality — rather than on a second instrument.

> ### Amendment, 2026-09-13 — `inundated_frac` is WITHDRAWN as an intensity variable. It was tested against its own matched null and it does not separate.
>
> Everything above was executed: `gee/S1_INUNDATION.js` exported the drop statistic for all **71 storm-district rows** across 25 districts, each paired with the **same calendar window shifted to the untreated 2017 season** (§1.1 carries no severe exposure that year), 113,600 pixel rows; `python/inundation_intensity.py` re-derived the criterion on that null arm and applied a decision rule **fixed in writing before the export existed**. The rule: over the severe harvest-window units — the only units where a standing crop can be flooded — the criterion separates only if the median per-unit excess is at least **+0.05** (five percentage points more pixels flagged in the cyclone year than in that unit's own 2017 window) **and** a within-unit arm-label sign-flip permutation gives **p ≤ 0.05**. Both are required; the first exists precisely so that a statistically detectable but negligible effect cannot be reported as a treatment intensity.
>
> **Correction, 2026-09-14 — "before the export existed" is not accurate, and it is stated in several places above.** The decision rule was fixed **after the Baleshwar two-probe verify run**, whose console output already showed the cyclone-arm and 2017-arm drop percentiles for a severe harvest-window storm, and **before the full 25-district export**. The accurate sentence is *"fixed after the Baleshwar dry run and before the full 25-district export"*, and it should replace "before the export existed" wherever that phrase appears in this amendment, in the commit message of `b0f7a17`, and in `REAUDIT_BRIEF_2026-09-14.md`. The rule itself is unchanged and its threshold was deliberately weak (five percentage points), so the author's judgement is that it was not tuned to the outcome — but the **claim about when** was stronger than the facts support and was repeated more than once. Found by an external re-audit, not by the author.
>
> **Result, on 18 severe harvest-window units (above the three-unit floor at which a null is informative at all):**
>
> | criterion | τ | median excess | perm p | verdict |
> |---|---:|---:|---:|---|
> | §3.3's declared 3 dB | 3.00 dB | **−0.0063** | 0.9385 | fails both rules |
> | re-derived, null 95th pct | 5.45 dB | +0.00375 | 0.0845 | fails rule (i) |
> | re-derived, null 99th pct | 8.11 dB | +0.0000 | 0.2594 | fails both rules |
>
> Four independent lines, any one of which would be enough:
>
> 1. **The declared criterion's excess is negative.** More pixels are flagged in the untreated year than in the cyclone year.
> 2. **Not one unit of the 18 reaches the threshold.** The largest per-unit excess anywhere is **+0.0375**; the split is 7 positive, 10 negative, 1 exactly zero. The null is not a small signal hidden by the median — it is absent in every unit.
> 3. **No threshold works, so the failure is of the statistic and not of the 3 dB value.** Swept across 15 thresholds from 1 to 12 dB, the best median excess anywhere is **+0.00375 at 5 dB**, thirteen times below the required +0.05; below 3.5 dB the excess is *negative*. This is the answer to the obvious objection that 3 dB is simply the wrong number.
> 4. **The flagged drop has no physical timing.** If the statistic detected cyclone inundation, deep drops in the cyclone arm would cluster in the first days after landfall while the untreated arm's had no reason to. Measured: the median flagged minimum falls **6.01 days** after landfall in the cyclone arm and **6.51 days** in the untreated arm (39.4% against 36.1% within five days). The timing is the acquisition schedule, not the storm. This check needs no threshold and no rate comparison.
>
> Robustness: dropping the 2 of 18 units whose null arm carries more than 1.25× the event-window scenes leaves the declared criterion at median −0.0063, p 0.9060. The most favourable reading available anywhere — the 5.45 dB criterion on those 16 clean units — gives p 0.0418 with a median excess of **+0.0063**, i.e. six tenths of one percent of pixels. It is reported here as the best case and it is two orders of magnitude below what an intensity variable needs.
>
> **What the criterion is actually doing.** It flags between **3.3% and 22.3%** of pixels *in years with no cyclone at all* — that is the range of the 2017 null arm's own flagged share across the 18 units. The low-backscatter water response documented by Phan, Le Toan & Bouvet (2021) is real, but on this coast in this season the criterion also responds to ordinary standing water in transplanted paddy, which is present every Kharif. A criterion that fires on the crop's normal hydrology cannot isolate the increment a cyclone adds.
>
> **Consequences for the protocol.** `inundated_frac` is **not** offered to §3.8 A as a continuous intensity term, and no secondary specification uses it. The binary severe-exposure indicators of §1.1 remain the only exposure measure, which is what §3.8 always declared as the headline. Nothing that was reported depended on `inundated_frac`, so no estimate changes.
>
> **Two window defects found on the way, recorded because they were in this section's own text.** §3.3 as written declares an event window of ±14 days around landfall *and* a reference of the 30 days ending 5 days before landfall. Those windows **overlap by 9 days**, 30% of the reference: an orbit whose scenes in both windows are the same acquisition yields a drop of exactly 0, the dry-run export carried that point mass on 9.8% of rows, and it was **arm-asymmetric** by up to a factor of 38 — so a comparison of the arms on the declared window is not a comparison. Separately, half the declared event window lies *before* landfall, and measurement confirmed the median flagged minimum there fell **5.5 days before the storm**. This section's own sentence — "the 3 dB criterion **and the window length** are re-derived on the untreated 2017 baseline season before use" — is what authorises the corrected window: event window **[L, L+14]**, zero overlap, no pre-landfall minimum, both declared numbers preserved. The declared window is exported alongside and is marked inadmissible rather than silently replaced; the verdict above is computed on the corrected window only.
>
> **This is a result, not a gap.** The claim the study can now make is that the standard SAR open-water criterion, calibrated on a matched untreated baseline and tested on 18 severe cyclone exposures over transplanted paddy, **does not distinguish a cyclone year from an untreated year** — and that no threshold on that statistic does. ~~No published Sentinel-1 cyclone-flood study we could find reports such a matched-null test at all.~~ **Priority framing withdrawn 2026-09-14.** This is the same untested form of claim as §3's "no published study reports a marker timing uncertainty in days", which was checked on that date and found **false**. This one has **not** been tested, and an untested priority claim is withdrawn rather than repeated: the matched-null result stands on its own evidence and needs no claim about being first. If a priority statement is ever wanted here it must be preceded by a recorded search, as §1.5.5 now requires. The negative is reported in §4 with its four lines of evidence, its two window defects, and its limits (median 4 acquisitions in the 14-day window; 6 of 36 unit-arms carry 2 or fewer).

### 3.4 Two-tier validation (locked)

Benchmark product: **Monsoon Asia Rice Calendar (MARC)** — Zhao, X., Nishina, K., Izumisawa, H., Masutomi, Y., Osako, S., Yamamoto, S. (2024). "Monsoon Asia Rice Calendar (MARC): a gridded rice calendar in monsoon Asia based on Sentinel-1 and Sentinel-2 images." *Earth System Science Data*, 16, 3893–3921. https://doi.org/10.5194/essd-16-3893-2024

**What MARC's published figures actually measure (corrected 2026-09-09).** MARC reports bias +3.93 d and RMSE 27.62 d for transplanting, and −5.76 d and 28.32 d for harvest. Checked against the source: these are **MARC's agreement with RiceAtlas, rasterised to MARC's own 0.5° grid** — "the RiceAtlas … was rasterized to the same spatial resolution as that of the proposed rice calendar (0.5°)" — and not field-validated error at pixel scale. The paper states plainly that "due to the absence of ground-truth data, it is not possible to validate the Asian continental-scale rice calendar with correct accuracy." Its one field-referenced figure is a site-level comparison against 40 literature records, R² 0.90 and RMSE 19.00 d, which is a different and much smaller exercise than the headline number.

The frozen protocol treated 27.62 d and 28.32 d as accuracy benchmarks for H1/H2 to beat. They cannot serve that purpose. Worse, the comparison as specified set *this study's RMSE against MARC* beside *MARC's RMSE against RiceAtlas* — two different quantities measuring agreement between different pairs of products — so returning a smaller number would have shown only that this study resembles MARC more closely than MARC resembles RiceAtlas, which is not an accuracy statement about anything.

**Explicit non-claim on accuracy (stated 2026-09-09).** No field-observed transplanting or harvest dates exist for the roster districts in any season of the panel. This was established by search, not assumed: district-level crop-weather calendars for coastal Odisha exist but are derived from 30-year climate normals rather than observation; IMD and KVK agromet bulletins narrate crop stage per district weekly but are unindexed narrative PDFs at district resolution; and no compiled dataset of dated field observations at known coordinates could be located. **This study therefore does not claim, and cannot establish, pixel-level accuracy for any phenometric.** Every comparison below is agreement or plausibility, and is labelled as such wherever it is reported.

**Tier 1 (primary) — internal consistency.** This is what the available evidence supports, and it is what Objective 4 actually requires. Four measures, reported per phenometric:

- **Orbit repeatability.** Where a district-season is covered by two or more Sentinel-1 relative orbits, the breakpoint is estimated separately from each and the between-orbit difference reported. The paths share the sensor, estimator, smoothing and crop state, so their errors are not assumed independent and the difference is not an accuracy estimate.
- **Inter-seasonal dispersion.** Dispersion of each pixel's fitted breakpoint across the nine seasons after removing season means. It describes the fitted output; without field observations it cannot separate crop timing from measurement or model variation.
- **Spatial coherence.** Within-district dispersion and the semivariance between neighbouring cohort pixels. This describes local similarity of fitted breakpoints; cohort pixels are not treated as field-validated parcels.
- **Fit quality.** RMSR distribution and accepted-fit share (§3.11).

**Tier 2 — district-level agreement and plausibility, never accuracy.** MARC is compared at district level only, as agreement between two products, with its 0.5° native resolution stated wherever the comparison appears. Fitted phenometrics are additionally bounded against published district crop calendars — for coastal Odisha, the AICRP Agrometeorology crop-weather calendars giving Kharif rice as Standard Meteorological Weeks 25–42 for medium-duration and 26–49 for long-duration varieties, approximately DOY 170–294 — and against the RiceAtlas season windows already used for §1.4. These catch gross error; they cannot measure fine error and are not reported as though they could.

**Amendment 2026-09-14 — the AICRP attribution above is not sourced, and is suspended.** The
sentence immediately preceding cites "the AICRP Agrometeorology crop-weather calendars giving
Kharif rice as Standard Meteorological Weeks 25–42 … approximately DOY 170–294". **No AICRP
document appears in `docs/field_reference_sources.md`**, none has been retrieved, and none is
archived under `docs/field_reference_pdfs/`. The four endorsed Odisha sources in that catalogue
give something different in kind — monthly *sowing* windows ("May – June", "June – July",
"July –Aug") and harvest stated only as a physiological criterion ("at physiological maturity
stage") — so neither an SMW range nor a calendar-date harvest window is supported by any
endorsed source. Until an AICRP source is retrieved, quoted and archived, **no statement in this
study may attribute a date bound to AICRP**, and the SMW 25–42 / DOY 170–294 figures are
suspended rather than merely re-cited.

*What this does and does not reach.* Traced call site by call site rather than assumed: the
constant carrying this attribution, `TROUGH_WINDOW = (170.0, 294.0)` in
`python/extract_phenometrics_sar.py`, is a **dead default** — the one production call overrides it
with §3.2's `GATE2["trough"]`, and the primary PLSM estimator uses a baseline-derived grid with no
calendar bound. **No reported coefficient, table or figure in this study rests on the AICRP
attribution.** The gap is therefore a citation defect in the protocol and a comment in live code,
not a contaminated result. It is recorded in full, with the trace, in
`docs/field_reference_sources.md`.

*What Tier 2 can still claim, and for which states.* The calendar-plausibility leg of Tier 2 is
available for **Odisha only**: `docs/field_reference_sources.md` carries no endorsed West Bengal
source and no endorsed coastal Andhra Pradesh source, and explicitly drops the one ANGRAU
candidate on agro-climatic-zone grounds. Five of the nine PDFs archived under
`docs/field_reference_pdfs/` are **not** endorsed by that catalogue — presence in the folder is
not endorsement, and the catalogue's archive manifest of this date says so per file. **No
three-state calendar-validation sentence may be written**, and any Odisha sentence must name
"the ICAR-CRIDA / OUAT Agricultural Contingency Plan for X district" rather than "the state
extension crop calendar". The RiceAtlas leg of Tier 2 is unaffected.

**Tier 3 — MODIS district-level Spearman ρ only (H5), later withdrawn.** The planned comparison used MOD13Q1 (250 m, 16-day) district median curves and rank correlation only; no pixel-level RMSE was planned. The field-size rationale in the frozen text was not adequately sourced for all three states. More importantly, the MODIS panel was never acquired, so §4.3.2 withdraws H5 untested and no MODIS result is reported.

**HLS is removed as the pixel-level validation substrate (2026-09-09).** The frozen §3.4 made Landsat HLS the "primary pixel-level validation substrate" for H1 and H2. HLS is Landsat plus Sentinel-2 and therefore sits under the same monsoon cloud that made the optical panel unusable; it cannot observe the ascending limb in this region either. Validating a radar-derived transplanting date against an optical one that cannot see transplanting would not be a test. HLS is retained only as a supplementary cross-check on EOS in the post-monsoon window, where the optical record does support it.

**Optional strengthening (not a dependency).** A small reference set could be assembled from published field trials in these districts reporting actual transplanting dates — the approach MARC itself used for its 40-site check, which produced a materially better figure than its headline. Twenty to thirty dated observations at named locations would not support pixel-level RMSE but would permit a statement of consistency with published field observation, which is stronger than product-to-product agreement alone. Recorded here as an improvement to make if time permits; nothing in the analysis depends on it.

### 3.5 Rice / cropland mask (substrate-honest)

**Superseded 2026-09-09.** The locked decision of 2026-09-04 made IRRI RiceAtlas v1.0 the primary mask in all three states, with ESA WorldCereal 2021 `temporarycrops` as a sensitivity mask, on the stated ground that RiceAtlas was "the only rice-differentiated option that spans the full window at admin level with a published citation". That decision is replaced for the reasons below. The original §4 text of `docs/rice_mask_options.md` is left standing rather than rewritten; the superseding decision, the evidence for it and the correction to §4's rationale are recorded there as a dated §8 (2026-09-09), following this project's append-and-correct convention.

**Why it was replaced.** RiceAtlas is rice-differentiated at the *administrative-unit* level: it identifies which units grow rice and on what calendar. It does not discriminate rice from other land at pixel scale, and `docs/rice_mask_options.md` §3.1 says so directly — "polygon-level, not pixel-level … requires a within-polygon cropland or NDVI-phenology filter to reach pixel-level rice". Requirement 2 of that document demands discrimination "at ≤ 30 m resolution", so the locked configuration did not satisfy the document's own admission criteria, and the required within-polygon filter was never implemented: `loadRiceAtlasMask30m` paints the polygon with a constant and rasterises it, so every pixel inside a district passed. Measured on 2026-09-09 against the layer below, Kharif rice covers between **0.9% and 61.3%** of the roster districts, mean **29.8%** — so of the 10,800 pixels in cohort `cohort_v1`, approximately **7,578 were not Kharif rice**. That cohort is retired (§3.6).

**Primary mask (locked 2026-09-09).** The intersection of the IRRI RiceAtlas v1.0 polygon (Laborte et al. 2017, Harvard Dataverse DOI 10.7910/DVN/JE6R2R) with the **2018 Kharif ("winter") rice layer of Chen et al. (2024)** — a 10 m Sentinel-1/Sentinel-2 paddy-rice map of 23 Indian states built from the VH-backscatter transplanting-flood signature, reporting overall accuracy 84.40%, producer's accuracy 82.31% and user's accuracy 84.72% (Chen, X., Shen, R., Pan, B., Peng, Q., Zhang, X., Fu, Y., Yuan, W., 2024, "A High-Resolution Distribution Dataset of Paddy Rice in India Based on Satellite Data", *Remote Sensing* 16(17), 3180, https://doi.org/10.3390/rs16173180; data at https://doi.org/10.6084/m9.figshare.24228619). RiceAtlas is retained as the administrative backbone and the source of the §1.4 season calendar; Chen et al. supplies the within-polygon pixel filter §3.1 of the options document always required.

**Why the 2018 epoch specifically.** The layer exists for 2018, 2020 and 2022. The 2018 epoch predates every named cyclone in §1.1 except Titli (11 October 2018). Using it therefore reduces, but does not eliminate, post-treatment selection risk: the map is a seasonal remote-sensing classification, Titli occurred within its epoch, and this study has no evidence that the classifier is wholly insensitive to that late-season event. The 2020 and 2022 epochs are used only as a stability check (what share of 2018 rice is still classified rice later), never in the selection rule. No claim is made that the selected extent is statistically independent of every study event.

**Roster-level plausibility check, not pixel validation (2026-09-09).** A district-by-district tally against GADM v4.1 Level-2 boundaries follows several expected regional cropping patterns: all six West Bengal districts show 35–61% Kharif rice, 1–3% autumn and **0% summer**; the Godavari–Krishna delta districts appear double-cropped (West Godavari 15.5% Kharif and 21.0% Rabi); and Nellore inverts to 20.0% Rabi against 1.3% Kharif, consistent with its district administration's report that 80% of sown area is Rabi. These aggregate correspondences do not validate the identity of individual 30 m pixels. Per-district figures are committed as `docs/chen_rice_2018_per_district.csv`. Two districts are flagged as possible under-detection and reported in Limitations rather than corrected: Puri at 13.8% is low for a Mahanadi delta district even after allowing for Chilika Lake, and Prakasam is near zero in all three seasons.

**Sensitivity mask (unchanged in role, reinterpreted).** ESA WorldCereal 2021 `temporarycrops` (Van Tricht et al. 2023, ESSD 15, 5491–5515) remains the sensitivity layer. The v100 collection contains no rice product, so the disagreement metric it supports compares "any cropland" against the primary rice mask, not "rice versus rice"; with a genuine rice layer now in the primary mask, that comparison measures cropland-versus-rice disagreement and is reported as such.

- **West Bengal:** RiceAtlas v1.0 clipped to WB, 18 polygons, EPSG:4326. GEE asset `users/supranab/RiceAtlas_WB`.
- **Odisha:** RiceAtlas v1.0 clipped to the 12 coastal districts in `docs/coastal_districts_gadm41.csv`, 12 polygons. GEE asset `projects/durable-pulsar-486209-b5/assets/RiceAtlas_OD`.
- **Coastal Andhra Pradesh:** RiceAtlas v1.0 clipped to the 9 coastal districts in `docs/coastal_districts_gadm41.csv`, 9 polygons. GEE asset `projects/durable-pulsar-486209-b5/assets/RiceAtlas_AP_coastal`.

> ### Amendment, 2026-09-14 — the per-unit arm below is now a genuine DiD. The first attempt at it was not, and was confounded.
>
> The rule below requires "both the primary-mask and intersection-mask **DiD coefficients** … for every district × cyclone unit". The per-unit arm added on 2026-09-13 did not deliver that. `unit_estimate` computed **the exposed season minus that same district's other seasons** — a before-and-after contrast with no comparison district anywhere in it. Two consequences, both measured rather than argued:
>
> * **It was confounded.** On the committed panel, **38 of the 47 estimable units (81%)** drew at least one control season from **another severe exposure of the same district**. Baleshwar's Fani estimate used 2021 and 2024 as controls, and Baleshwar was severely exposed in both. For four units in five the comparison was cyclone-year against cyclone-year.
> * **It differed materially from the right answer.** Re-estimated as a proper DiD, the median difference from the superseded quantity is **+5.6 d** on trough (mean +3.7 d, maximum 25.4 d), **+1.2 d** on heading and **+3.4 d** on harvest. The supersession is therefore a correction, not a relabelling — which is why the alternative of renaming the old output "descriptive" was rejected: it would have left a confounded number in the repository under a gentler name.
>
> **What replaces it.** `unit_did` computes the canonical 2 × 2 estimate for each unit: (treated district's exposure season − its k = −1 season) − (mean over **clean** control districts of the same difference), on district-season means, which is §3.8's declared level of estimation. A control district is clean only if it carries **no severe exposure in either the pre or the post season**; the count dropped for that reason is reported per unit (median 8 clean controls survive, range 5–24). The treated district's own pre-season is checked too and **8 of 47 units are flagged** as themselves severely exposed in it — those read as an increment over the adjacent exposure, exactly as §3.8 B's `treated_other_severe_exposure` flag intends. One treated cluster, so **no inference is reported** (MacKinnon & Webb, 2018); the point estimate is what this rule asks for.
>
> **Two further gaps in the first attempt, also closed.** It ran for the **trough breakpoint only** — it now runs for trough, heading and harvest — and it was **not called by `run_all.sh`**, so the pipeline that claims to reproduce everything did not reproduce its table. Stage 13 now runs all three markers.
>
> **The §3.5 conclusion is unchanged by the correction**, which is the point of reporting both: across the 47 estimable units the intersection-minus-primary difference has mean +0.110 d (trough), −0.256 d (heading) and −0.401 d (harvest), with signs agreeing in **46/47, 47/47 and 45/47** units. Mask choice does not move the per-unit estimates. Found by an external re-audit on 2026-09-14, not by the author; `analysis/deviation_log.md` carries the full record.

> ### Amendment, 2026-09-14 (second pass) — the DiD above was built on the wrong estimand, the wrong control window and the wrong roster. All three are corrected, and **the conclusion in the paragraph above does not survive.**
>
> A second external audit found three defects in the correction of the same day. Each was
> verified against the code and the committed tables before being accepted; each is real.
>
> **(a) The estimand was not the declared one.** `district_season_means` grouped the
> **pixel** panel by district and season and took the mean. §3.5's own amendment above, and
> the header of `python/mask_sensitivity.py`, both state that the district-season value is a
> **PLSM fit to the district-season mean curve, not an average of pixel phenometrics** — the
> module header adds that re-implementing the aggregation "would put a second, unaudited copy
> of the estimator in the repository, and the arm would then test the copy rather than the
> paper". The violation was committed to that same file, 570 lines below the rule. Measured
> on the committed panels, the wrong estimand moved the median per-unit coefficient by
> **9.6 d (trough), 7.5 d (heading), 12.4 d (harvest)**, with maxima of 63.2, 34.3 and 70.6 d.
> `district_curve_panel` now reads `phen_panel_district_season.csv` for each mask and
> **refuses a pixel panel outright**, with a self-test that asserts the refusal.
>
> **(b) The clean-control window was two seasons, not three.** §3.8 B requires controls with
> no severe exposure in **t − 1, t or t + 1**. The code tested t − 1 and t only. For Titli this
> admitted **19 control districts where the declared rule admits 5**; the 14 wrongly admitted
> were all severely exposed by Fani or Bulbul in 2019. The stack membership is no longer
> computed here at all: it is taken from `event_study.derive_stack`, this repository's audited
> implementation of §3.8 B's rule, whose own self-test asserts that it reproduces
> `docs/cyclone_footprints_ibtracs50km.csv` exactly for the five cyclones that file covers.
>
> **(c) The roster was all nine severe storms, not the declared six.** Michaung 2023, Dana 2024
> and Montha 2025 entered a table reported against a design §3.8 B states over six named
> cyclones. The primary block is now exactly `event_study.ESTIMABLE` — Titli, Fani, Bulbul,
> Amphan, Yaas, Remal — and the other three are reported in a separately labelled
> `additional_severe` block that is **not part of this rule's claim and enters no sign test**.
>
> **What the corrected arm measures, and it is weaker than what was withdrawn.** Over the
> **35** declared units (not 47), intersection minus primary is mean **−7.39 d** (trough),
> **−0.67 d** (heading), **−1.59 d** (harvest), with signs agreeing in **31/35, 22/35 and
> 21/35**. The withdrawn paragraph above claimed +0.110 / −0.256 / −0.401 d and 46/47, 47/47,
> 45/47. **The sentence "mask choice does not move the per-unit estimates" is therefore
> withdrawn.** What can be said is narrower: mask choice moves individual per-unit estimates,
> by up to 36.7 / 25.0 / 50.0 d, while the district- and pixel-level §3.5 results — which are
> produced by re-running the committed estimator on masked exports and are untouched by any of
> this — continue to hold.
>
> **Why, and it is not a mask problem.** Applying §3.8 B's control rule honestly leaves four of
> the six cyclones with almost no comparison group. The declared clean controls for Titli,
> Fani, Bulbul and Amphan are almost entirely coastal Andhra Pradesh districts, and most of
> those fail the district-level fit in the relevant seasons. Usable control districts per
> cyclone: **Titli 1, Fani 2, Bulbul 2, Amphan 4, Yaas 13, Remal 11.** With one control
> district the "mean over clean controls" *is* that district, so Titli's per-unit number is a
> two-district comparison and not a difference-in-differences against a control group; that is
> a definitional statement, not a threshold. Split on whether at least three declared controls
> survive the fit screen — a property of the panel, though computed after the coefficients were
> seen, and declared as such — the 12 units that have a control group give mean **−0.99 /
> +0.14 / −4.42 d** with signs agreeing **10/12, 10/12, 11/12**, and the 23 that do not give
> **−10.72 / −1.09 / −0.11 d** with **21/23, 12/23, 10/23**. The instability is concentrated
> where the control group is one or two districts, which is the study's own σ ≈ 26 d
> pixel-level finding reappearing at the district level through a tiny denominator.
>
> **Per-unit inference remains unavailable** (one treated cluster, MacKinnon & Webb 2018), and
> the per-unit arm is now reported as a disclosure of unit-level spread rather than as evidence
> that mask choice is immaterial. Found by an external audit, not by the author. The full
> record, including the two self-audit findings that followed from it, is in
> `analysis/deviation_log.md`.

**Sensitivity procedure and disclosure rule (corrected 2026-09-06):** per `docs/rice_mask_options.md` §5, both the primary-mask (RiceAtlas rice polygons) and intersection-mask (RiceAtlas ∩ WorldCereal 2021 `temporarycrops`, a general-cropland classifier) DiD coefficients are computed for every district × cyclone unit and reported side by side before either is discussed. The manuscript body must state, verbatim, that the intersection is with a general-cropland classifier and not with an independent rice product (no v100 WorldCereal rice product exists).

### 3.6 Optical QC — Sentinel-2

Collection: `COPERNICUS/S2_SR_HARMONIZED` (SR L2A). Cloud probability: `COPERNICUS/S2_CLOUD_PROBABILITY`.
- Drop pixels with cloud probability > 30%.
- Keep SCL classes {4, 5, 6, 7, 11}: vegetation, bare soil, water, unclassified (with caveat), snow/ice.
- Bin composites: median of admitted pixels per 5-day DOY bin; 55 bins per season over the §1.4 window (bin starts DOY 150 … 420), with `doy_bin_start` / `doy_bin_end` values above 365 denoting days counted from 1 January of the analysis year (i.e. dates in the following calendar year). Dekadal aggregation for fitting (§3 lead-in) is done downstream in Python, not in Earth Engine; the exported schema is unchanged.
- Output schema (13 columns): `district, year, tile_id, cell_id, lon, lat, bin_index, doy_bin_start, doy_bin_end, NDVI_med, EVI2_med, LSWI_med, valid_pixel_count`.
- Empty bins carry a dummy-schema mask row via `dummy.addBands(composite, null, true)` — never crash `Export.table.toDrive`.
- **The export must name its columns explicitly (added 2026-09-11, v0.7.1).** `Export.table.toDrive` is called with an explicit `selectors` list matching the schema above. This is a correctness requirement, not tidiness: without it Earth Engine infers the CSV header from the leading features of the collection, and because the table emits bin 0 first, a district-season whose earliest 5-day bins carry no acquisition produces a leading block in which every band-derived property is null. Earth Engine then writes a header without those columns and the entire file loses them, while the properties set from feature metadata survive — so the file looks structurally complete and is silently missing the measurements. Measured on the Sentinel-1 run of 2026-09-10: 97 of 225 files lost `VHVV_med` and `valid_obs_count` this way, and all 128 that survived have data in bin 0, 128 of 128, with none starting at a later bin. The dummy-schema armor above prevents a crash on an empty bin but does **not** prevent this, because a masked band still samples as null. Both conditions must be handled.

**Candidate cohort (added 2026-09-08; cohort v1 retired and redefined 2026-09-09; post-freeze amendments, `analysis/deviation_log.md`).** The panel is extracted at a **fixed candidate cohort** of rice pixels per district, not at every 30 m pixel and not at one point per sub-tile. For each of the **25** extracted districts (§1.3), 400 pixels are drawn once from the district's **primary rice mask as defined in §3.5** — the RiceAtlas polygon intersected with the Chen et al. 2018 Kharif rice layer — by `stratifiedSample` with seed 42 (`CONFIG.cohortPointsPerDistrict` / `cohortSeed`), exported, committed as `docs/candidate_cohort_v2.csv`, and re-uploaded as an Earth Engine table asset that the extraction path reads.

**Cohort v1 is retired and must not be used.** It was drawn from the constant-filled RiceAtlas polygon before the §3.5 correction, so roughly 70% of its 10,800 pixels are not Kharif rice, and it covers two districts the §1.3 criterion excludes. `docs/candidate_cohort_v1.csv` remains committed as the record of what was drawn and is never overwritten; no result is reported from it. No phenometrics were extracted under it — the optical extraction attempted against it on 2026-09-08 is documented in `analysis/decisions_log.md` and produced no usable panel. The committed file, not the seed, is authoritative: the panel does not depend on Earth Engine's random number generator remaining stable. The cohort is identical in every season, so `cell_id` is a stable per-pixel key across years by construction — which is what §3.10's descriptive two-season restriction and §3.8's pixel-year panel require. Any change of seed, size or draw method creates a new cohort id and a new decisions-log entry; the old cohort file is never overwritten.

This mirrors Paper 1, which extracted a fixed candidate cohort of 210–453 pixels per district, static across years (RSASE-D-26-02830 §2.4, Table 1: 2,527 candidate pixels per year, 15,162 candidate pixel-years over eight districts). At 400 pixels × 25 districts × 9 seasons, Paper 2's frame is **90,000 candidate pixel-years** (revised 2026-09-09 from 75,600 at 27 districts × 7 seasons). Density beyond a few hundred per district buys little: inference is clustered on 25 districts (§3.8), so the cluster count, not the within-district pixel count, governs the standard errors.

**Why not every pixel, and why not the previous grid.** Exporting the full mask is infeasible — East Godavari's rice mask alone is 12.6 million 30 m pixels, which at 55 bins is tens of millions of rows for one district-season. The path committed in `2cf493a` instead built its grid with `reduceToVectors(geometryType: 'centroid')` over a constant-valued mask, which returns connected components rather than pixels: measured on a Bhadrak tile on 2026-09-08, one cell against 774,673 rice pixels. That would have yielded roughly 570 arbitrary pixels for the whole study. `CONFIG.enableRealExports` was never `true`, so nothing had been extracted under it.

**Export unit.** One CSV per (district, season) — 27 × 7 = 189 tasks — replacing the per-(district, tile, season) loop, which the 25 km fishnet would have made roughly 4,000 tasks (570 rice-bearing tiles × 7 seasons). The 13-column schema of this section is unchanged; `tile_id` carries the cohort id (`cohort_v1`) rather than a 25 km sub-tile label, since the cohort is drawn district-wide. `gee/S2_QC_Ingest.js` remains the authority for what is extracted.

### 3.7 Optical QC — Landsat HLS

Collections: `NASA/HLS/HLSL30/v002` and `NASA/HLS/HLSS30/v002`. Fmask decoder per LP DAAC HLS v2.0 User Guide §6.4.
- Bits: 0 cirrus, 1 cloud, 2 adjacent-to-cloud, 3 cloud shadow, 4 snow/ice, 5 water, 6–7 aerosol level (0..3).
- Drop rule: any of bits {0, 1, 2, 3, 4, 5} set OR aerosol == 3.
- Band harmonisation (locked): L30 (OLI) B04→Red, B05→NIR, B06→SWIR1. S30 (MSI) B04→Red, **B8A→NIR (narrow, 855–875 nm)**, B11→SWIR1. B8A rather than B08 for OLI-MSI spectral parity (Claverie et al. 2018).
- HLS analysis year range: **2016–2025** (pre-2016 lacks S30 overlap; extended from 2016–2023 on 2026-09-07 to match the Sentinel-2 seasons of §1.1). Same §1.4 window.
- Output schema: identical to Sentinel-2 for downstream ingest parity.

### 3.8 Objective 4 specification — exposure-panel TWFE (headline) and named-cyclone event-level view (revised 2026-09-07)

**A. Headline: district-season exposure panel.** All **25** extracted districts (§1.3), all seasons **2017–2025** — 225 district-seasons — pixel-year observations; exposure indicators from `docs/district_cyclone_exposure_ibtracs50km.csv` (§1.1). For each phenometric *Y* (SOS, peak NDVI date, EOS), pixel *p* in district *i(p)* and season *t*:

\[
Y_{pt} = \alpha_{i(p)} + \gamma_t + \beta_{\text{pre}}\, S^{\text{pre}}_{i(p),t} + \beta_{\text{harv}}\, S^{\text{harv}}_{i(p),t} + \delta_{\text{pre}}\, S^{\text{pre}}_{i(p),t-1} + \delta_{\text{harv}}\, S^{\text{harv}}_{i(p),t-1} + \lambda_{\text{pre}}\, S^{\text{pre}}_{i(p),t+1} + \lambda_{\text{harv}}\, S^{\text{harv}}_{i(p),t+1} + \mu\, M_{i(p),t} + \varepsilon_{pt}
\]

- `S^pre_{d,t} = 1` if district *d* had severe (≥ 48 kt within 50 km) pre-season exposure in season *t*; `S^harv_{d,t} = 1` for severe harvest-window exposure; `M_{d,t} = 1` for any minor (34–47 kt) exposure in season *t*, any timing class. No severe mid-season exposure occurs in the catalogue for 2016–2025, so no mid-season term is estimable and none is included; minor mid-season exposures enter *M*.
- **β_pre and β_harv are the headline coefficients (H3).** δ (lag-1) tests persistence into the following season. λ (lead-1) is the pre-trend test: exposure in the *next* season cannot move this season's phenology, so a non-zero λ flags a violated parallel-trends assumption for that class (§3.9). The lead terms are undefined for season 2025 (they would need the complete 2026 season — its pre-season term above all — which is not yet in the catalogue), so 2025 observations enter with the lead terms set to missing and are excluded from the lead test rather than coded as unexposed; likewise the lag terms for 2019 use the catalogued 2018 exposures (Titli), which exist even though no 2018 phenology is extracted. μ is reported and carries no pre-declared sign.
- `α_{i(p)}` is a **district** fixed effect and `γ_t` a **season** fixed effect; the unit of observation is the pixel-year. This is the structure of Paper 1's Model 2 (RSASE-D-26-02830 §3: "the same equation at pixel-year resolution … α_d and γ_t retained as district and year fixed effects, and standard errors clustered at district level (G = 8)"; 6,850 retained pixel-years from 2,195 unique pixels), with Paper 1's single Treated × Post indicator replaced by catalogue-derived exposure indicators so that no district-season is assumed untreated. This closes the control-year contamination question recorded in `analysis/decisions_log.md`: Bulbul 2019 inside Amphan-2020's window, Fani 2019 and Yaas 2021 two seasons apart, and eight further catalogued storms (severe: Michaung 2023, Dana 2024, Montha 2025; minor: Nivar 2020, Gulab 2021, Asani 2022, two unnamed storms) striking roster districts in seasons the earlier rule treated as untreated controls.
- **Pixel fixed effects are deliberately not used in the headline** (corrected 2026-09-07). A pixel fixed effect identifies β only from pixels observed in both the cyclone year and at least one control year — pixels that fail extraction in the cyclone year are absorbed by their own intercept and contribute nothing. That would silently condition the headline estimate on surviving the cyclone, which is the selection §3.10 exists to diagnose. With district fixed effects, every retained pixel-year contributes and year-to-year composition may change. The attrition diagnostic and IPSW arm address that threat under their stated assumptions; the descriptive two-season restriction does not isolate composition.
- Standard errors clustered at **district** level (`i(p)`, 25 clusters), not pixel level — exposure is assigned at district level, and pixel-level clustering would understate the correct standard errors.
- **Wild-cluster bootstrap** with 9,999 replications (Roodman et al. 2019, `boottest`), clustered by district, reported as the headline inference.
- **Robustness (reported, never headline):** state × season fixed effects in place of `γ_t` (identification then uses within-state, within-season contrasts only); exposure buffer 75 km and 100 km in place of 50 km; severity threshold 64 kt (IMD Very Severe Cyclonic Storm) in place of 48 kt; the HLS panel 2016–2025 in place of Sentinel-2 (adds seasons 2016–2018, including Titli 2018).
- §3.10 (attrition diagnostic, IPSW, and descriptive two-season restriction) applies with "treated" read as "severely exposed" and the stratum as district × season; the six estimable named cyclones remain the per-cyclone reporting units of §3.10 item 1.

**B. Event-level view: named-cyclone stacks.** For each estimable named cyclone *c* (§1.1: Titli, Fani, Bulbul, Amphan, Yaas, Remal — six, updated 2026-09-09; Sitrang exposes no roster district), one stack is built following Cengiz, Dube, Lindner & Zipperer (2019, *Quarterly Journal of Economics* 134(3), 1405–1454): seasons *t_c* − 1, *t_c*, *t_c* + 1; treated = footprint districts; controls = districts with no severe exposure to any catalogued storm in those three seasons, derived from the full exposure catalogue; same-storm fringe districts are dropped. `docs/cyclone_footprints_ibtracs50km.csv` is an audit table for the original six-cyclone roster and predates Titli; `python/event_study.py` verifies its derivation against that table for the five estimable events it contains, then applies the same rule to Titli. Controls are drawn from all three states because no named cyclone has three clean same-state coastal controls. With *k* = *t* − *t_c* and *k* = −1 as reference:

\[
Y_{ptc} = \alpha_{i(p),c} + \gamma_{t,c} + \beta_{0,c}\,\big(\text{Treated}_{i(p),c} \times \mathbf{1}[k = 0]\big) + \beta_{+1,c}\,\big(\text{Treated}_{i(p),c} \times \mathbf{1}[k = +1]\big) + \varepsilon_{ptc}
\]

clustered by district across stacks. β₀,c is the per-cyclone estimate whose sign enters H4; β₊₁,c is persistence. The executed Sentinel-1 panel spans 2017–2025, so the 2019 Fani and Bulbul stacks use 2018 as *k* = −1; no HLS or Sentinel-2 event-stack result is used. Controls are required to be clean. A footprint district is flagged when it also has severe exposure to a different storm in t − 1, t or t + 1: Amphan's five footprint districts were all severely exposed to Fani in 2019; Bulbul's two were Fani-exposed in the same season; eight of Fani's seventeen carry Titli 2018 or Amphan 2020. A flagged β₀,c is a descriptive contrast conditional on that adjacent exposure, not a clean single-storm causal effect; part A is also descriptive after the timing placebo fails. Yaas and Remal carry no flags. The current roster-restricted counts and the smaller fit-usable pools are stated in the correction immediately below.

**Correction, 2026-09-14 — the clean-control counts in the sentence above are too high, and the repository's own committed table already said so.** They were read off `docs/cyclone_footprints_ibtracs50km.csv` without restricting to the 25-district roster, so four of the five count **Nellore and Prakasam** — southern Andhra districts that are not in this study's panel at all and can never supply a control observation. (Kolkata *was* excluded, as the sentence says; these two were not.) Restricted to the roster the counts are **Fani 17 / 0 / 5; Bulbul 2 / 0 / 5; Amphan 5 / 0 / 8; Yaas 5 / 0 / 15; Remal 2 / 0 / 13**, and `results/Table_SX_EventStudy.csv` has carried those figures — 5, 5, 8, 15, 13 — since the event study was run. Titli, which the estimable set gained on 2026-09-09 when the panel floor moved to 2017, has **6 / 0 / 5** and no row in the footprints file at all: `python/build_cyclone_exposure.py`'s `NAMED` list is the pre-2026-09-09 roster (it still carries Sitrang and lacks Titli), which is why `python/event_study.py` derives every stack from the exposure catalogue and asserts in its self-test that the derivation reproduces the committed file exactly for the five it covers. **No estimate changes** — the two phantom districts have no phenology to contribute, so nothing ever used them — but the counts advertised the control pools as larger than they are, and the per-unit arm of §3.5 shows why that matters: after the district-level fit screen, the usable control pools are Titli 1, Fani 2, Bulbul 2, Amphan 4, Yaas 13, Remal 11. Found by tracing the numbers in this sentence to the table that produces them. With two treated clusters for Bulbul and for Remal, no event-level significance claim is made (MacKinnon & Webb, 2018); event-level results are reported as point estimate, wild-cluster-bootstrap interval and flags.

**Level-of-analysis note (corrected 2026-09-07, fixed-effects wording corrected the same day).** An earlier draft of this section specified the DiD at district × year level, while §3.10's attrition correction has operated at pixel level (via `cell_id`) since 2026-09-05. IPSW-reweighting a handful of treated district-year observations per cyclone (typically 1–2 treated districts, ~5–10 controls per state) is not a workable correction. The headline specification is therefore fixed at pixel-year level with district and year fixed effects — Paper 1's Model 2, verified against the submitted manuscript — and inference clustered at district level to respect the level at which treatment is assigned. An intermediate draft on 2026-09-07 wrote pixel fixed effects and attributed them to Paper 1; that attribution was wrong (Paper 1 uses district fixed effects at pixel-year resolution) and is corrected here.

**Design history (2026-09-07).** This section was revised three times on one day, each time before any extraction: from district-year to pixel-year level; from a pixel fixed effect to Paper 1's district + year fixed effects; and from a drafted stacked clean-control design with hand-assigned footprints and same-state clean controls to the exposure panel above. The last step was forced by computing that draft from the IBTrACS catalogue before committing it: Fani's ≥ 48-kt track exposes 17 of the 18 Odisha and West Bengal roster districts, so no Odisha or West Bengal district is a clean control for any 2019–2021 event, and eight further catalogued storms strike roster districts in seasons the earlier rule treated as untreated. The exposure panel is the design that survives that check; the stacks are retained as the per-cyclone view.

**Level of estimation (2026-09-12, third entry; rewritten 2026-09-15, tenth pass).** The headline TWFE is estimated on the **district-season panel** (225 district-seasons, 208 estimable, 25 clusters) because **that is where the declared estimand lives**: §3.8's outcome is the breakpoint fitted to the **district-mean curve**, not a summary of pixel breakpoints. The choice is one of estimand, not of precision.

**Two measured quantities, reported separately and not set against each other.** *(a)* Per-pixel marker dates carry an **observed split-half disagreement** of σ ≈ 18 days — two half-series of one season differenced, so whatever is common to both halves cancels and is invisible to it. *(b)* At an assumed district-mean noise level of 0.122 dB, a Monte Carlo on a **synthetic** season recovers its own **planted** breakpoints to **±1.3 days**. **Neither establishes the precision of the real district panel**, for which this study holds no repeat measurement, and no ratio or contrast between them is formed. *(Removed in this pass: the paragraph previously gave "σ ≈ 18 d … while … ±1.3 days" as the **reason** for the district headline. That contrast is withdrawn here for the same reason it was withdrawn from `analysis/test_classification.md`.)*

**The two arms do not estimate identical quantities, and this is the substantive point.** They share the exposure assignment and the district clustering, so the treatment definition and the inference level are the same. But **a breakpoint of the district-mean curve is not an average of pixel breakpoints**: the PLSM fit is nonlinear in the breakpoints, so fitting to an averaged series and averaging the fits to the individual series are different operations with no general ordering between them. Any difference between the district and pixel arms may therefore reflect **aggregation and nonlinear fitting**, not merely a change in residual variance. *(Withdrawn in this pass: "the two levels are directly comparable; what changes is residual variance, not the cluster count." The second clause is true and is kept — the cluster count is 25 either way. The first asserts a comparability the estimators do not have.)* The pixel-level panel is reported as a robustness arm and is the input to §3.10; where the two arms disagree, that disagreement is reported rather than attributed to one cause.

**Timing-class labels are known to be mis-specified for this substrate, and are kept as the headline anyway (open item, 2026-09-12).** The exposure catalogue's `timing_class` comes from Paper 1's optical calendar. Measured against the radar calendar: the 21 severe `harvest_window` rows fall in October (15), November (2) and December (4), while radar heading is 10 November and harvest 19 January — so that class is mostly a **late-vegetative / pre-heading** exposure, not a harvest-window one, and the 31 severe `pre_season` rows are all May, genuinely before the §1.4 window opens. The frozen classes are retained as the headline **because re-classifying exposure after seeing the results is exactly the discretion this protocol exists to remove.** The specified next robustness arm is to classify each storm against the **district's baseline markers** — never the same season's fitted markers, which the storm may itself move — and to report it alongside. **Run 2026-09-13; see the third paragraph below.**


> **Correction, 2026-09-13 (third entry).** The per-storm phase labels in this section come from a six-phase exploratory probe, not from `python/classify_exposure_phase.py`, which emits three phases. The headline is unchanged and correct — **14 of the 21 severe `harvest_window` rows are rise-phase exposures** — but the other seven are **four post-heading** rows (North 24 Parganas 2019 BULBUL:MATMO, Guntur 2023 MICHAUNG, East Godavari and West Godavari 2025 MONTHA) and **three unclassifiable** rows in districts outside the panel roster (Nellore 2016 and 2023, Prakasam 2023), not "four in the plateau and three after harvest". Two `pre_season` rows are unclassifiable for the same reason (Kolkata 2019, 2020). Of the 21 catalogue rows, **18 are classifiable and 14 of those 18 are rise-phase**; both denominators are quoted together from here on. Nothing estimated changes — unclassifiable rows contribute no indicator. See the deviation log's 2026-09-13 third entry.

**The arm is run (2026-09-13).** `python/classify_exposure_phase.py` classifies
each severe storm against the district's baseline markers — the mean over its
district-seasons with no catalogued exposure at any severity, never the markers
of the season being classified — and collapses phases toward the heading boundary
until every retained phase carries at least three treated clusters, a rule fixed
before any coefficient was seen. Three phases result, with 17, 14 and 4 treated
clusters: `S_phase_pre_window` (storm before DOY 150), `S_phase_rise` (window
opening to baseline heading), `S_phase_post_heading`. The heading effect survives
at almost the same magnitude and attaches to the coherent phase — frozen
`heading : S_harvest_window` +7.11 d (p_WCB 0.0025) against measured
`heading : S_phase_rise` +7.37 d (p_WCB 0.0154), with plateau duration shortening
−8.99 d (0.042) and drainage onset unmoved (−1.61 d, 0.53). §3.10's item 1 on the
phase classification is weaker than on the frozen one (`S_phase_rise` −0.145,
p_WCB 0.083, against `harvest_window` −0.126, p_WCB 0.040), so part of the
apparent treatment-correlated attrition was the label rather than selection. Of
33 lead tests in the arm, three fall below 0.10 and none below 0.05 against 3.3
expected by chance; all three are on `Slead_phase_pre_window`, so the rise-phase
finding is not among them. The arm runs only when `--phase-exposure` is supplied:
the default specification is the frozen one.

### 3.9 Falsifiability checks

- **Lead test (pre-trends).** λ_pre and λ_harv in §3.8 A must be indistinguishable from zero (wild-cluster bootstrap *p* > 0.10). A non-null lead for a class flags that class's β as descriptive only.
- **Timing placebo (built into the design).** Severe harvest-window exposure occurs after the observations supporting the same season's earlier radar trough; it therefore cannot causally alter those earlier observations. β_harv on the fitted trough breakpoint must be indistinguishable from zero, and a non-null value indicates selection, estimator deformation or other mis-specification, not a cyclone effect on an agronomic transplanting date. The same zero is *not* declared for the rise-end breakpoint: late-October landfalls (Dana, 24 Oct 2024; Montha, 28 Oct 2025) can truncate the curve before some units complete the rise, so that coefficient is reported without a pre-declared value.
- **Permutation inference (spatial placebo).** Exposure histories are randomly re-assigned across districts within each state (2,000 permutations, preserving each season's count of exposed districts) and β_pre, β_harv re-estimated; the permutation *p*-value is reported beside the wild-cluster-bootstrap *p*-value. **Run 2026-09-13; interpretation corrected 2026-09-16 (`python/permutation_test.py`); see §4.1.7.** These are conditional spatial sensitivity results, requiring exchangeability within state. Actual storm geography does not guarantee that assumption, and relabelling histories changes spatial footprint geometry. A permutation |t| quantile exceeding 1.96 does not establish wild-bootstrap size distortion: the bootstrap uses its own reference distribution. No method is selected as more valid because it gives a larger or smaller observed p-value. This replaces the earlier interior-district and shifted-year placebos; it does not validate causal inference.
- **SAR sanity check.** As in §3.3.
- **r-value robustness.** Report DiD coefficients at r_SOS ∈ {0.70, 0.75, 0.80} and r_peak = r_EOS ∈ {0.45, 0.50, 0.55} as a supplementary sensitivity grid. The locked pair (0.75, 0.50, 0.50) is the headline.


**Both checks in this section have now failed, 2026-09-13 — see §4.1.** β_harv on
the fitted trough breakpoint is +7.438 d, p_WCB 0.0008 at pixel level (9,999
replications), surviving lead adjustment and IPSW; λ_harv is p_WCB 0.0024 on the
rise-end breakpoint and 0.0702 on the trough breakpoint, both below this section's
own 0.10 bar. The consequences stated above — "selection or mis-specification, not
a cyclone effect", and "descriptive only" — are therefore in force. §4.1.4 shows
that a late-season synthetic perturbation can move an earlier breakpoint under
this estimator, a plausible pathway rather than identification of the observed
association's cause. The permutation check has been run (§4.1.7); the amplitude-
crossing r-value grid was withdrawn as inapplicable to the fitted-breakpoint
estimator (§4.3.3).

### 3.10 Attrition correction (treatment-correlated missingness)

Panda & Sahu (companion paper, in review at *Remote Sensing Applications: Society and Environment*) document that this QC pipeline's extraction failure is not random with respect to treatment: an attrition regression finds a treatment × cyclone-window coefficient of +0.29 on extraction failure, measured on its native 0–1 proportion scale (SE = 0.083; p_cluster = 0.010; p_WCB = 0.010; 95% WCB CI 0.108–0.422) — i.e. a +29 percentage-point increase — and in at least one cyclone-year treated support falls to zero, making the balanced-panel DiD non-estimable for that stratum. Objective 4 assumes this threat applies by default in every cyclone × state stratum and addresses it as follows, before any DiD/TWFE coefficient in this study is reported or discussed:

1. **Per-stratum attrition diagnostic (mandatory, run first).** Replicate Paper 1's Table S4 specification for each severe-exposure class (pre-season, harvest window; §3.8 A) and independently for each of the six estimable named cyclones (Titli, Fani, Bulbul, Amphan, Yaas, Remal; Sitrang exposes no roster district, §1.1), reporting the treatment × cyclone-window coefficient on extraction-failure rate with p_cluster, p_WCB, and 95% WCB CI, in a new supplement table `Table_SX_AttritionDiagnostic.csv`.

2. **Zero-treated-support rule (pre-specified in the frozen working protocol, not discretionary).** If treated support in a district × cyclone × season stratum is zero, or the wild-cluster bootstrap is not computable for that stratum, the DiD/TWFE coefficient for that stratum is reported as "not estimable" rather than omitted silently or imputed — mirroring Paper 1's own precedent. This is not an OSF pre-registration claim (§5.2).

   *Degenerate cluster-robust variance is an instance of this rule (added 2026-09-09, part 3).* A cluster-robust sandwich is not guaranteed positive semi-definite. Where few clusters carry any score for the tested coefficient — the two-season balanced windows of item 3c, in which the exposure indicator is constant within most districts — the estimated variance can come out non-positive, and no t-statistic and therefore no bootstrap exists. That stratum is reported as **not estimable**, with its point estimate still shown and the number of score-carrying clusters reported alongside the nominal cluster count. It is never reported with a zero or near-zero standard error: measured on a synthetic balanced window, a variance of −9.4 × 10⁻¹⁸ would otherwise print as a coefficient of +7.628 with a standard error of 0.000 and a confidence interval of zero width. `python/attrition_diagnostics.py` enforces this and reports `n_score_clusters` for every stratum.

3. **Correction for strata with nonzero but unbalanced treated support:**
   a. **Primary: inverse-probability-of-survival weighting.** Model Pr(pixel-year survives QC Gates 1–3, defined in §3.1, §3.2, and §3.11) via logit on pre-cyclone cloud-frequency climatology, distance to cyclone track, elevation, and district/cyclone fixed effects, estimated on the full attempted (pre-QC) candidate frame — the observation-eligible pixel set defined in §3.11, the same denominator Paper 1's Table S4 uses. Weight the DiD/TWFE regression by 1 / p̂_i (Wooldridge, 2002, *Portuguese Economic Journal* 1(2), 117–139; attrition framing per Fitzgerald, Gottschalk & Moffitt, 1998, *Journal of Human Resources* 33(2), 251–299).
      *Covariate list, open item (raised 2026-09-09; superseded by the closed radar list below).* The original optical covariates did not match the Sentinel-1 substrate. The executable code uses only the later six-variable radar list and never silently substitutes an incomplete set. The descriptive two-season arm is not a fallback correction.

      *Identifying assumption (corrected 2026-09-15).* IPSW recovers the treatment effect only if survival is ignorable conditional on the modelled covariates. If pixels drop out *because of* the outcome itself, the IPSW estimate remains biased in an unknown direction. This study has no same-estimand composition safeguard for that case; item 3c changes both sample and time window and is descriptive only.
   b. **Lee (2009) trimming bounds are REMOVED (2026-09-09).** They are not corrected and re-used; they are withdrawn, and this item records why.

      *The frozen specification was wrong in two ways.* Lee's Proposition 1a trims the group with the **higher** selection rate, by p = [Pr(select | that group) − Pr(select | other)] / Pr(select | that group). The frozen text states its own monotonicity in the opposite direction — exposure *lowers* treated retention, so treated is the **lower**-retention group — and then applies Lee's formula unflipped, trimming the treated-post distribution using treated-minus-control over the treated rate. Under the protocol's own stated direction that numerator is negative, making the trimming share a negative proportion, which is not computable. The correct application would trim the **control** group at [Pr(survive | control) − Pr(survive | treated)] / Pr(survive | control).

      *Why it is withdrawn rather than corrected.* Fixing the arithmetic would leave a deeper problem. Lee derives these bounds for a randomised two-arm design with a single post-treatment outcome. This is an observational panel and the estimand is a difference-in-differences; transferring the bounds requires individual-level monotonicity and does not yield a bound on the DiD coefficient itself unless pre-period retention is balanced within the stratum. A corrected but mis-transferred estimator invites sharper criticism than an honest absence, and item 3c below already provides a robustness anchor that needs no borrowed assumptions.

      *What replaces it.* ~~The balanced-composition check (item 3c) becomes the **primary robustness estimate**, because it holds composition fixed by construction rather than by assumption.~~ **WITHDRAWN 2026-09-15 (fourteenth pass).** The balanced-composition arm is **not** a primary robustness estimate and is not described as one anywhere. It restricts to units retained in both seasons *of one cyclone* and estimates on **those two seasons**, while the headline pools **all nine**, so the comparison changes the **time window** as well as the **composition** and identifies neither. `delta_beta` is retired with it. What is reported for a triggered stratum is the unbalanced estimate, the IPSW estimate where it is estimable, and the explicit statement that **no same-estimand composition comparator is defined** — the balanced rows are carried as a **descriptive sensitivity** only. The magnitude is reported as **not point-identified under differential attrition**, which is unchanged.

      *Monotonicity was an assumption, not a finding.* The +0.290 attrition coefficient establishes that exposure raises extraction failure **on average**. It does not establish that no pixel-year's retention is improved by exposure, which is what monotonicity requires. That distinction is stated in the manuscript rather than resolved by assertion.

      *The substrate change shrinks the problem this item exists for.* The +0.290 coefficient was measured on an optical pipeline in which cyclone-associated cloud, standing water and canopy loss all directly reduced the count of valid observations. Sentinel-1 acquires through cloud, so that mechanism largely disappears and the attrition rate is expected to fall substantially. What remains is narrower and more clearly outcome-related: a fit can still fail Gates 2–3 when a cyclone has destroyed the phenological signal it was fitting. That residual is precisely the selection this section exists to diagnose, so §3.10 is retained in full and its diagnostic re-run on the Sentinel-1 panel rather than carried over from Paper 1's figure.
   c. **Descriptive two-season restriction (corrected 2026-09-15).** Re-estimate on pixels retained in BOTH the pre-cyclone and post-cyclone season of that cyclone and report the coefficient and `balanced_n_pixels`. This is **not** a same-estimand composition check: relative to the nine-season headline it changes the time window and the retained composition together. `beta_balanced` and `delta_beta` are retired and are not regenerated. The rows may be described only as a post-hoc descriptive sensitivity; they cannot establish a composition effect, direction identification, or robustness of the headline magnitude.
      *Relation to §3.8 and to Paper 1.* These rows are not the named-cyclone event-study estimator and not Paper 1's retired balanced-panel estimator. They are indexed by the cyclone season but regress the exposure class. A missing both-season set is reported as not estimable. No same-estimand composition comparator is defined in this study.

**Implementation note (2026-09-07):** No new Earth Engine extraction is
required for the descriptive two-season restriction. `cell_id` in the existing
13-column CSV schema (§3.6) is a stable per-pixel key (formatted from
`lon`/`lat` on a fixed 30 m grid, same tile geometry every year), so a
pixel counts as "retained in both seasons" for a given cyclone iff its
`cell_id` appears in the extracted panel for both the pre-cyclone
comparison year and the post-cyclone (treatment) year of that cyclone's
stratum. `python/attrition_diagnostics.py` (implements §3.10
items 1-3 in full: attrition diagnostic regression, IPSW weighting, and the
descriptive two-season restriction; the Lee bounds of the frozen item 3b are withdrawn
and not implemented) computes this directly from the committed panel CSV --
no pipeline change to the extraction script is needed for this check.

**Reporting-language rule (added 2026-09-07, extends the 2026-09-05 zero-treated-support rule):**
- Zero treated support, or non-computable wild-cluster bootstrap: report "not estimable" (unchanged, 2026-09-05).
- Attrition diagnostic significant at p_WCB < 0.05: report the matching unbalanced estimate and the IPSW estimate where estimable; state that no same-estimand composition comparator is defined and that the magnitude is **not point-identified under differential attrition**. The descriptive two-season rows are reported separately and cannot rescue the triggered estimate.
- Agreement or disagreement in sign between a descriptive two-season row and the nine-season headline does not identify a composition effect or a causal direction, because both sample composition and time window change.

*Correction note (2026-09-09).* The rule frozen at `2cf493a` read "Lee bounds include zero: report 'direction supported'". That inference is invalid — an identified set containing zero cannot support a sign — and the Lee bounds it referred to are withdrawn (item 3b). No result was ever reported under it.
- Attrition diagnostic not significant at p_WCB < 0.05: report the unadjusted coefficient with its causal limitations; IPSW and descriptive two-season figures may be reported alongside but are not called confirmatory.

**Manuscript disclosure rule (corrected 2026-09-15):** State that every reported coefficient is accompanied by its per-stratum attrition diagnostic and an IPSW estimate where estimable; a significant attrition diagnostic makes the magnitude not point-identified under differential attrition because no same-estimand composition comparator is defined. Describe the balanced rows only as post-hoc, descriptive two-season restrictions. Never call them a balanced-composition robustness check.

*Correction note (2026-09-09).* The 2026-09-07 version of this sentence promised "a Lee (2009) trimming-bound interval" and reported a stratum as "direction-supported" when those bounds included zero. The bounds are withdrawn (item 3b) and that inference was invalid; the sentence above replaces it. No coefficient was ever computed or reported under the superseded wording.

**IPSW covariate list: the open item is CLOSED for the radar substrate (2026-09-12, third entry).** The three optical covariates are replaced by six declared here, each the radar analogue of what the optical one was for:

| declared | role |
|---|---|
| `obs_total` | total valid Sentinel-1 observations for the unit-season. Replaces `cloud_freq_clim`: how well the sensor sees this unit, which on radar is orbit geometry rather than cloud |
| `n_valid_dekads` | dekadal coverage after §1.4 aggregation. §3.11 is a coverage rule, so selection runs partly through coverage |
| `dist_to_track_km` | district-season minimum distance to the 34-kt wind radius of that season's catalogued storms, coded at 500 km where no storm is catalogued. Carried over unchanged |
| `elevation_m` | terrain height |
| `slope_deg` | terrain slope. On radar the operative terrain quantity is local geometry, so slope is declared **alongside** elevation, not instead of it |
| `incidence_deg` | mean Sentinel-1 incidence angle over the cell. VH/VV depends on it, so retention does too |

The last three come from a new **25-task** static export, `gee/S1_STATIC_COVARIATES.js` — one per district, not per district-season, because they do not vary by season — joined by `python/merge_static_covariates.py`. Until that export lands, `python/attrition_diagnostics.py` computes the weights on the available subset, labels the result **`ipsw_partial`**, names which covariates are missing, and states that it must not be reported as the pre-declared IPSW. That is a labelled interim estimate with a specified path to closure, not a silent substitution.

**CLOSED 2026-09-13; interpretation corrected 2026-09-15.** The 25-task static export ran and joined to both panels with zero unmatched rows, so the six-covariate list above is complete. The IPSW is estimated **in full at pixel level** — 90,000 rows, 39 parameters, 813.9 events per parameter, converged, calibration 2.8e−16 — and is labelled `ipsw`, not `ipsw_partial`. It is **not estimable at district level**, for two reasons that are properties of the level rather than gaps in the data: `elevation_m`, `slope_deg` and `incidence_deg` are constant within a district and are absorbed by the district fixed effects; and **20 of the 25 districts have all nine seasons estimable**, so their dummies predict retention perfectly, leaving 30 of 225 rows against 13 parameters once those levels are dropped — one event per parameter, and no convergence. A non-converging logit discards its weights and emits no `ipsw` rows. No other arm supplies a same-estimand composition correction at district level, so a triggered magnitude remains not point-identified. Applying the weights at pixel level moves every headline coefficient by less than one standard error (trough under severe harvest-window exposure +4.77 → +3.44 d; heading +1.19 → +1.00 d; harvest under pre-season −2.23 → −2.29 d), and the weights are well behaved: median 3.16, 99th percentile 18.9, 23 of 90,000 rows at the 0.01 clip, Kish effective sample size 41,236.

**And the covariates bear on a question §3.5 left open.** In the fitted selection model, retention is **associated** with terrain and viewing geometry, and **no association with cyclone distance was detected**: log-odds of retention slope −0.0705 per degree, incidence angle +0.1024 per degree, elevation −0.0014 per metre, against distance to the 34-kt track at **−0.0001**, indistinguishable from zero. *(Reworded 2026-09-14, ninth pass: this read "retention is **governed by** terrain and viewing geometry, **not by exposure**". Withdrawn — these are observed associations in a fitted model. The cause cannot be separated among mask classification, signal quality, estimator behaviour and the screening rule itself, and this study does not attempt to.)* Unconditionally, retention is 0.431 at 0–10 m and 0.169 above 300 m; the elevation pattern is **not strictly monotonic** (0.1667 at 150–300 m versus 0.1687 above 300 m). Retention is 0.389 below 1° of slope and 0.135 above 8°. The 6.5% of the cohort above 300 m or steeper than 8° retains at 0.170 against 0.365 for the rest. The selected cohort includes cells up to 1,422 m and 41.5° of slope. These observations do not determine whether individual cells are rice, or which mechanism causes lower retention. The covariates entered here are time-invariant per pixel and are absorbed by the pixel fixed effects.

**What this does not establish.** A null coefficient on cyclone distance in one fitted model is **not** evidence that exposure-related selection is absent. The model carries only the covariates that were available; an exposure-related mechanism acting through something unmeasured, non-linearly, or through a channel other than distance to the 34-kt track would not appear in it, and the fixed effects absorb only what is genuinely time-invariant. **No claim is made that retention cannot carry an exposure effect.** **And §3.10's own per-stratum diagnostics do detect associations between retention and exposure** — four distinct regressions at pixel level and two at district level fire the declared p_WCB < 0.05 trigger (§4.0). The distance null and those findings are different predictors in different models and are reported together; neither overrides the other. *(Corrected 2026-09-15, tenth pass. This sentence previously ended "— and **every covariate that drives it** is time-invariant per pixel, so it is absorbed by the fixed effects and **cannot masquerade as an exposure effect**", and described retention as associated with cell properties "**rather than with exposure**". "Every covariate that drives it" asserts the model is complete; "cannot masquerade" converts a detected null into a proven absence; "rather than exposure" states a contrast the data do not support. The ninth pass corrected the first half of this same sentence and left the second half standing.)* Figure 7 plots it.

**A district-name resolution check was added (2026-09-12).** Every panel district must resolve in the exposure catalogue, under its own spelling or with underscores replaced by spaces, or the script refuses to run. Without it a naming difference codes a district as never exposed, and the output reads as a null result rather than as an error.

**The balanced arm is indexed by the storm's season only (2026-09-12, documented, not changed).** Item 3c restricts to units retained in t_c−1 and t_c and then regresses on the exposure **class**, not on a storm indicator. Two cyclones in the same season therefore return the same number twice — FANI and BULBUL are both 2019. That is the frozen design; it must not be read as two independent confirmations. Per-storm separation lives in item 1b, which does use a storm-specific indicator.

### 3.11 Gate 3 — fit-quality screening (RMSR) (added 2026-09-07)

Adopted from Paper 1's Gate C (RSASE-D-26-02830), since Paper 2 uses the identical curve-fitting method (Beck et al. 2006 double-logistic fit over a Whittaker–GCV-smoothed composite, stated at the top of §3) on the same sensor family.

The root-mean-squared residual (RMSR = √(SSE/n), as in Paper 1 Supplement S1.3) between the observed dekadal NDVI values (§3 lead-in: pairwise-aggregated 5-day bins) and the fitted double-logistic curve is computed for each pixel. Pixels with **RMSR > 0.15 NDVI units** are flagged as poor-fit. This gate catches persistently cloud-contaminated composites that compositing/gap-filling did not fully recover, and mixed-cropping pixels where a single-season double-logistic does not represent the observed trajectory.

**Gate 3 does not apply to the radar path (2026-09-12).** RMSR is the residual of a fitted curve. The radar substrate reads markers off the smoothed series without fitting (§3 lead-in), so there is no residual and no Gate 3 there. Its screening role passes to the minimum-rise criterion and to marker completeness: a pixel-season that cannot be marked is reported with its reason and enters §3.10's diagnostic as a failure, exactly as a non-converged fit did. Gate 3 continues to govern the optical path.

**Whittaker smoothing costs harvest identifiability (measured 2026-09-12).** On the baseline the smoother has no effect on recovered amplitude (3.33 dB against 3.27 dB unsmoothed) but reduces the share of pixels yielding a harvest marker from **85% to 60%**. The step is inherited from Paper 1 for optical comparability; on a step-shaped radar index it suppresses the drainage fall. Whether it is retained on the radar path is derived on the baseline and recorded before any treated season is marked.

**Unit correction (2026-09-09, part 3).** The 0.15 threshold is in NDVI units and does not transfer to a backscatter ratio in decibels, for the reason given in §3.2's unit correction. The gate's structure — RMSR between the observed dekadal values and the fitted curve, applied per pixel, with the district-year 30% reporting convention below — is unchanged; only the threshold is re-derived, on the untreated 2017 baseline season, and recorded in `analysis/decisions_log.md` before use. `python/fit_phenometrics.py` computes RMSR in dB and has no default for the threshold.

**Gate 3 on the radar path, revised (2026-09-12, third entry).** The 2026-09-12 note above says there is no residual on the radar path because markers are read off the series without fitting. That is no longer true: the primary estimator is a fitted five-segment model (§3 lead-in) and it has a residual. Gate 3's role is therefore **not** vacant on the radar path — it is served by the rise-significance screen, which tests the fitted rise against the series' own residual variance at a selection-aware critical value, and which is a fit-quality screen in the same sense RMSR was. The 0.15 NDVI threshold still does not transfer, for the units reason of §3.2. The ≥14-dekad eligibility rule below is unchanged and is applied before any fitting.

**Observation eligibility and denominator (carried from Paper 1 verbatim; corrected 2026-09-07).** Paper 1 fitted a pixel-season only when it had at least eight valid dekads and no more than 50% of scheduled composites missing, counted non-convergence as extraction failure, and used the observation-eligible pixel set as Gate C's denominator (RSASE-D-26-02830 §3.2 and Supplement S1.2–S1.3). Because Paper 2 now fits at dekadal cadence over Paper 1's window (§1.4, §3 lead-in), the same rule applies with no translation: a pixel-season is fit-eligible only with at least eight valid dekads and no more than 50% of the 28 scheduled dekads missing (i.e. at least 14 valid); non-convergence counts as extraction failure; and the observation-eligible pixel set is the denominator for Gate 3, for §3.10 item 1's extraction-failure rate, and for §3.10 item 3a's survival model. An earlier version of this paragraph translated the rule to "at least 16 of the 31 five-day bins"; that translation is retired — it was stricter than Paper 1's rule (a 10-day dekad is more likely to contain one clear observation than a 5-day bin), so it would have inflated Paper 2's extraction-failure rates relative to Paper 1's Table S4.

**Cadence note (revised 2026-09-07).** With fitting at dekadal cadence, the 0.15 RMSR threshold is applied at the cadence on which Paper 1 predeclared it, and Gate 3 pass rates are directly comparable with Paper 1's Gate C (48/48 district-years). The supplementary 5-day-bin fit (§3 lead-in) reports its own RMSR distribution and Gate 3 failure share per district-year in `Table_SX_AttritionDiagnostic.csv`, so that any cadence-driven difference is visible rather than hidden.

For panel-level reporting (extraction-failure-rate tables, §3.10 item 1), a district-year cell is additionally flagged if more than 30% of its pixels carry a Gate 3 poor-fit flag — matching Paper 1's district-year reporting convention — but Gate 3 exclusion for the pixel-year DiD panel itself (§3.8) is applied per pixel, individually, consistent with the pixel-year level of analysis.

**Implementation note (2026-09-07; corrected the same day).** `rmsr` and `gate3_pass` are computed in the Python fitting stage, not in Earth Engine — `gee/S2_QC_Ingest.js` is extraction-only (its own architecture note: no fits, no Gate 1, no DiD; all of that runs locally in Python), and curve fitting happens after the dekadal aggregation of the §3 lead-in. They are columns of the per-pixel phenometric output table alongside SOS/POS/EOS, not of the 13-column export schema (§3.6), which is unchanged. An earlier version of this note placed them in the export path; that was wrong.

---



## 4. Cyclone-specific expected signs

**Exposure-class predictions (headline, §3.8 A; tested by H3).** β_pre > 0 for SOS, peak NDVI date and EOS (delayed transplanting, delayed peak, delayed harvest). β_harv > 0 for EOS (harvest disruption), β_harv = 0 for SOS (the timing placebo of §3.9), and no declared value for β_harv on peak NDVI date (late-October landfalls sit inside the POS window). No sign is declared for δ, λ or μ.

**Named-cyclone predictions (event-level, §3.8 B; enter H4 as sign agreement of β₀,c).** Each named cyclone's coefficient is signed a priori:

| Cyclone | Expected β_SOS | Expected β_peak | Expected β_EOS |
|---|---|---|---|
| Fani (May 2019, pre-Kharif) | Positive (delayed transplanting) | Positive (delayed peak) | Positive (delayed harvest) |
| Bulbul (Nov 2019, harvest window) | Not applicable — pre-Kharif signal absent | Not applicable | Positive (harvest disruption) |
| Amphan (May 2020, pre-Kharif) | Positive | Positive | Positive |
| Yaas (May 2021, pre-Kharif) | Positive | Positive | Positive |
| Sitrang (Oct 2022, harvest window) | Not estimable | Not estimable | Not estimable — no roster district within 50 km of the ≥ 34-kt track (§1.1) |
| Remal (May 2024, pre-Kharif) | Positive | Positive | Positive |

Cyclones that make landfall in the harvest window are tested only against β_EOS. Sitrang is retained in the table as a named event but contributes nothing to H4 (§2).

**Amendment 2026-09-13 — see §4.1.** The predictions above are unchanged as
predictions and unchanged as the definition of the primary family (four tests:
β_pre on SOS, peak and EOS; β_harv on EOS). What has changed is that the design
carrying them fails this protocol's own §3.9 checks, so the outcomes signed here
are reported as fitted radar-trajectory breakpoint displacements and not as
phenological effects of cyclones. β_harv on peak, for which no value is declared
above, remains exploratory and is not promoted to a finding.

---

## 4.0 Amendment, 2026-09-15 — §3.10's reporting rule fired and was never executed; the triggered strata and their classification

**This section exists because the rule at §3.10 item 3 was declared, its trigger
condition was met at both levels, and nothing reported it.** The phrase "not
point-identified under differential attrition" appeared in this protocol three
times as a *statement of the rule*, and nowhere as an applied *verdict*.
`analysis/hypothesis_verdicts.md` did not contain the word "attrition" at all.
The numbers were in the committed tables the whole time.

**THE TRIGGER ACCOUNTING, STATED ONE WAY EVERYWHERE.** There are **seven
triggered output labels** — five at pixel level and two at district level —
representing **six distinct tested designs**, because one pixel pair is a
*verified alias*: `class:pre_season` and `phase_attrition:S_phase_pre_window`
are the same regression reported under two names, their exposure vectors being
elementwise identical across all 225 district-seasons. *(Corrected 2026-09-15,
fourteenth pass: earlier passes wrote "six strata" in one place and "five pixel
and two district" in another, which are two different counts of the same thing.
Seven labels, six designs, stated that way from here on.)*

The triggered labels, at 9,999 replications at both levels:

All p-values below are at **9,999 replications at both levels**, which is what
§3.8 declares. The pixel figures previously carried in this table were computed
at 999 and are superseded; the previous value is shown in brackets.

| level | stratum | coef | p_WCB raw | Holm | BH-FDR |
|---|---|---:|---:|---:|---:|
| pixel | `class:pre_season` | −0.0533 | **0.0008** *(was 0.0010)* | **0.0080** | **0.0060** |
| pixel | `cyclone:FANI` | −0.0877 | **0.0012** *(was 0.0040)* | **0.0108** | **0.0060** |
| pixel | `cyclone:TITLI` | +0.0683 | **0.0094** *(was 0.0070)* | 0.0752 | 0.0313 |
| pixel | `phase_attrition:S_phase_rise` | +0.0358 | **0.0411** *(was 0.0420)* | 0.2877 | 0.1028 |
| district | `class:harvest_window` | −0.1260 | **0.0397** | 0.3970 | 0.2160 |
| district | `cyclone:YAAS` | +0.1063 | **0.0432** | 0.3970 | 0.2160 |

**The trigger set is unchanged by the tenfold increase in replications**: the
same five pixel strata and two district strata fire, and the same two pixel
strata survive Holm. Coefficients do not depend on the bootstrap and did not
move.

`phase_attrition:S_phase_pre_window` also fires at pixel level and is **the same
regression as `class:pre_season` under a second name** — identical coefficient,
standard error and p. It is not a separate finding and is not counted as one.

**The predeclared trigger stays on the raw p.** Holm and BH-FDR are reported as a
**sensitivity, never as the gate**, and are computed over the **distinct designs**
given by a **verified alias map**. *(Corrected 2026-09-15, thirteenth pass: the
twelfth pass deduplicated by matching OUTPUT STATISTICS — coefficient, standard
error and sample sizes rounded to 12 significant figures. That is unsound, because
two genuinely different designs can produce identical rounded summaries, and
merging them would make the adjustment too lenient. Output-based deduplication is
**withdrawn**.)* Exactly one alias is recognised, and only because its **design**
identity was checked: `S_pre_season` and `S_phase_pre_window` are **elementwise
identical across all 225 district-seasons**, 29 exposed in each, verified against
the panel and the exposure catalogue rather than against the results.
`attrition_completeness.py --verify-aliases` re-runs that check against the live
panel. The conservative
all-11-labels calculation is carried alongside in the trigger table and gives
Holm 0.4367 and BH-FDR 0.2376 for both district results. **Neither district
finding survives either adjustment**; `class:pre_season` and `cyclone:FANI`
survive Holm at pixel level.

**The distance null and these findings are reported together.** §3.10's selection
model finds no association between retention and distance to the 34-kt track
(−0.0001). These diagnostics find associations with exposure class and with
individual cyclones. They are different predictors in different models and
neither overrides the other; §3.10's live text and Figure 7 carried only the
null until the eleventh pass, which left a reader with a conclusion the
diagnostics do not support.

**Classification.** Every triggered stratum is classified in
`results/s310_v2_<level>/Table_SX_AttritionTriggers.csv` and its magnitude is
reported as **not point-identified under differential attrition**. The one
bearing on a headline number is district `class:harvest_window`, whose indicator
is shared with `headline:trough:S_harvest_window` = **+5.001 d** (se 3.103,
p_WCB 0.1102).

**That +5.001 d is not an identified magnitude.** Its own p_WCB is 0.1102; its
IPSW comparator does not exist, because the district-level logit does not
converge; and its pooled composition comparator is **not defined at class
level**, because item 3c restricts to units retained in both seasons *"of that
cyclone"* and `harvest_window` spans several cyclones in several seasons.

**The per-cyclone balanced rows are not a comparator for it, in either
direction.** They are separate descriptive sensitivities on two-season
sub-samples. Their spread must not be quoted as though it bracketed the pooled
coefficient, and their `delta_beta` values must not be read as composition
effects — see the amendment below, which retires that reading.

### Amendment, 2026-09-15 (twelfth pass, second entry) — `delta_beta` is RETIRED as a composition sensitivity

`delta_beta` = |β_unbalanced − β_balanced| was specified in item 3c as the measure of how far composition moves a coefficient. **It does not measure that, and it is withdrawn as a sensitivity.**

The balanced arm restricts to units retained in both seasons **of one cyclone** and estimates on those **two seasons**. The unbalanced headline pools **all nine seasons**. So the difference between them changes the **time window** as well as the **composition**, and identifies neither: a large |Δβ| is equally consistent with composition mattering, with the coefficient differing between a two-season and a nine-season window, and with both.

**What a valid composition sensitivity requires.** The balanced and unbalanced estimates must share the **same outcome, the same exposure definition, the same seasons, the same controls, the same fixed effects and the same inference settings**, and differ **only** in which units are included. That estimator is **not declared anywhere in this protocol**, and it is not introduced now: choosing one with the coefficients visible would measure the choice. Recorded as a post-analysis specification gap.

The obsolete `beta_balanced` and `delta_beta` columns are no longer regenerated. `balanced_n_pixels` remains because it describes the two-season sample. Historical tables and logs retain the old columns as evidence of what was computed; current result tables must not. A range across per-cyclone rows must not be quoted as a pooled comparator.



**No pooled class-level balanced estimator is introduced.** Item 3c fixes the
restriction per cyclone and specifies no pooled form; at least four are available
(union, intersection, stacked with fixed effects, fully balanced panel) and item
3c explicitly rules out the last. Selecting one now, with the coefficients
visible, would measure the choice rather than the data. **Recorded as a
post-analysis implementation gap**, with the pooled magnitude reported as not
point-identified. If a pooled estimator is ever adopted it must be declared
before it is computed and applied to all classes together.

**What was fixed so this is reproducible.** `run_all.sh` never passed
`--balanced`, so the declared run produced no balanced rows: none at pixel level
at all, and the district table's 132 rows came from a hand-run the pipeline did
not reproduce, so a rerun silently deleted them. It also could not run the
attrition step at all, because it passed the exposure catalogue by bare filename
from `python/` while the file lives in `docs/`. And it ran the **pixel level at
999 replications** against §3.8's declared 9,999.

All three are fixed. The runner requests the balanced arm at both levels, runs
both at 9,999, resolves the catalogue through `_find_doc`, and calls
`python/attrition_completeness.py` as a gate. That gate compares the **exact
expected stratum key set** — constructed as a cross-product, not counted — and
fails on a missing key, an extra key, a duplicate key, a blank status, a
comparator that was never run, or a bootstrap count other than 9,999.
`n_boot_requested` is recorded in every WCB row.

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

**Final replay correction, 2026-09-16.** The counts `1,018` and `1,078` in the
preceding audit narrative describe one earlier comparison pass; run-to-run
last-digit serialization counts are not stable evidence and must not be reported
as results. The accepted clean no-resume replay has the exact expected key sets,
9,999 successful WCB draws wherever applicable, and no retained
coefficient/SE/t/count difference above 1e-9. One underpowered, non-triggering
WCB p-value changes by one draw from the preceding candidate
(`cyclone:REMAL`, 0.7134 → 0.7135); a targeted clean recomputation returns
0.7135. No trigger, multiplicity result, hypothesis verdict or interpretation
changes.

---

## 4.1 Amendment, 2026-09-13 — the exposure design fails its own falsifiability checks; §3.8's coefficients are not causal effects

This section is an amendment under §5.3, not a rewrite. Everything above it stands
as written and is superseded only where this section says so. Evidence:
`analysis/decisions_log.md`, 2026-09-13 sixth and seventh entries;
`results/s310_v2_pixel/`, `results/s310_v2_district/`, `results/placebo_check.log`,
`results/censoring_test/`.

All numbers below are on the corrected retained-only sample (the `twfe` screening
defect, decisions log 2026-09-13 fourth entry) and supersede every earlier number
for the same quantity.

### 4.1.1 The primary outcome family and the multiplicity policy

This is a clarification, not a new choice. §4 and §2's H3 already fix the family;
it had never been written down as a count, and 22 coefficients were being
inspected as though all were tests.

**The primary family is four tests**, exactly those §4 signs and H3 conjoins:

| # | coefficient | outcome | predicted |
|---|---|---|---|
| 1 | β_pre | SOS | positive |
| 2 | β_pre | peak | positive |
| 3 | β_pre | EOS | positive |
| 4 | β_harv | EOS | positive |

H3 requires **all four**, so H3 itself needs no multiplicity correction — a
conjunction of four one-sided claims is harder to satisfy than any one of them,
not easier. Where an individual coefficient in the family is reported on its own,
the threshold is **Bonferroni 0.05/4 = 0.0125**.

Two further cells in §3.8 A are **falsifiability checks, not estimands**: β_harv
on SOS (§3.9's timing placebo, predicted zero) and the lead terms λ (predicted
zero). A check is not corrected for multiplicity and is not reported as a finding
in either direction.

**β_harv on the fitted rise-end breakpoint is exploratory.** §4 states "no declared value" for the optical peak analogue. It is
reported in the full supplementary table with its diagnostics attached and appears
in no abstract, no conclusion and no figure that implies an effect. Every other
coefficient the pipeline produces — the duration and amplitude outcomes, the lag
terms δ, the minor-exposure term μ — is likewise **descriptive**, reported in the
supplement, never headline. §4 declares no sign for δ or μ; it never declared the
duration or amplitude outcomes at all.

### 4.1.2 The timing placebo fails

§3.9 requires β_harv on the fitted trough breakpoint to be indistinguishable from zero and states the
consequence itself: a non-null value "indicates selection or mis-specification,
not a cyclone effect." Measured, 9,999 replications, district-clustered:

    pixel,    declared specification    +7.438 d   p_WCB 0.0008
    pixel,    + lead terms              +7.106 d   p_WCB 0.0006
    pixel,    + IPSW                    +5.955 d   p_WCB 0.0080
    district, declared specification    +5.001 d   p_WCB 0.1102
    district, + lead terms              +4.821 d   p_WCB 0.1783

The check is rejected at pixel level in the declared, lead-adjusted and IPSW
specifications. That persistence is a sensitivity result; it does not identify
why the association occurs. The district estimate is positive but its interval
includes zero, so it is **inconclusive**, neither a clean placebo pass nor a
rejection. No post-hoc power claim is used to convert that null result into a
positive finding.

**Correction, 2026-09-13 (same day) — headline versus robustness arm.** The
paragraph above, and the sixth decisions-log entry, treat the pixel failure as
though it were the declared headline's. It is not. §3.8's "Level of estimation
(2026-09-12, third entry)" declares the headline TWFE on the **district-season
panel**, with the pixel panel "reported as a robustness arm and … the input to
§3.10". Stated correctly: **the timing placebo is rejected in the robustness arm
(p_WCB 0.0008) and is uninformative in the declared headline (p_WCB 0.1102).**

Four things are unchanged by that correction, and they are why §4.1.5 stands:

1. The placebo estimate is large and positive at **both** levels — +5.001 d and
   +7.438 d. A late-season storm cannot causally alter radar observations made
   months earlier; movement of the fitted earlier trough is therefore a warning
   about selection or estimator deformation, not an agronomic date effect.
2. The district interval **[−1.04, +11.25] contains the pixel estimate**. It does
   not contradict it and cannot resolve it. A placebo the headline arm lacks the
   power to check is not a placebo that passed, and calling it one would invert
   §3.10's own MacKinnon–Webb rule.
3. The pixel arm **is** the §3.10 input, so the whole attrition correction — the
   diagnostic and the IPSW weights — rests on the arm
   whose placebo is rejected.
4. The exploratory radar analogue is 0 of 4 on both panels, with β_pre on the
   fitted fall-end breakpoint pointing opposite to the predeclared analogue at
   both. This is not an H3 verdict because H3's optical outcomes were not measured.

**Separate implementation cross-check of the estimator.** `twfe`'s absorbed-FE result was
checked against an implementation sharing none of its code — fixed effects as
explicit dummy columns, statsmodels OLS, statsmodels' cluster-robust covariance —
and reproduces **exactly**: district panel β_harv on trough +5.0010 d, se 3.1035
by both routes. At pixel level a sparse design with a hand-written cluster-robust
sandwich gives +7.7130 d, and the difference is the **fixed-effect
specification**, not an error: that check absorbed cell_id × year, which line 12
of §3.8 deliberately excludes. Three solvers agree to the last digit on each
specification. The placebo failure therefore does not depend on the fixed-effect
choice — +7.438 d under the declared district × year, +7.713 d under pixel ×
year. Evidence: `analysis/decisions_log.md` 2026-09-13 ninth entry.

### 4.1.3 The lead test fails for the harvest-window class

§3.9 requires λ to satisfy p > 0.10 and states its own consequence: a non-null
lead "flags that class's β as descriptive only." At pixel level, 9,999
replications:

    λ_harv on fitted rise-end breakpoint   -2.412 d   p_WCB 0.0024
    λ_harv on fitted trough breakpoint     -2.898 d   p_WCB 0.0702

Both are below 0.10. **By §3.9 as written, every β_harv is descriptive only.**
This consequence was predeclared and is applied, not chosen now.

### 4.1.4 Censoring diagnostic: a plausible estimator pathway (`python/censoring_test.py`)

The trough was measured three ways on the same pixel-seasons — the full
five-segment PLSM on all 28 dekads; a reduced one-breakpoint V-shape on all 28;
and the same reduced model on **dekads 0–12 only, DOY 154.5–274.5**, a window that
precedes every severe harvest-window landfall in the panel (earliest: Titli,
2018-10-10, DOY 283), so no censored series contains any post-storm observation.
The window is identical for treated and control rows, so the truncation cannot act
as a treatment; the script verifies this against the exposure catalogue on every
run and refuses otherwise.

On the 18,174 rows all three arms can measure, with identical regressors and
bootstrap:

    (1) five segments, 28 dekads      +4.941 d   se 1.592   p_WCB 0.0068
    (2) one breakpoint, 28 dekads     -2.388 d   se 2.318   p_WCB 0.3108
    (3) one breakpoint, dekads 0–12   +1.158 d   se 0.947   p_WCB 0.2545

    paired, same rows:
    (1) − (3)                         +3.782 d   se 1.320   p_WCB 0.0065
    (1) − (2)                         +7.329 d   se 1.867   p_WCB 0.0027

Arm (3) has the **smaller** standard error and finds nothing, so this is not a
power failure. The paired rows are the load-bearing result: both measures exist on
the same rows, so the difference is directly estimable and the common sample's
composition cancels.

**Candidate estimator-deformation pathway.** PLSM selects the breakpoint quadruple minimising weighted residual
sum of squares across all 28 dekads at once, with the four levels profiled out. A
late-season change in backscatter alters the profiled levels, which alters which
quadruple wins, which moves t1 — months upstream of the change. On a synthetic
series, subtracting 4 dB from only the post-window dekads moved the full-window
trough by **20 days** while the censored fit could not move at all (in the script's
self-test). The estimator is global; a cyclone's effect on the canopy is local.

**What this does not establish.** The observed estimator dependence and the
synthetic perturbation do not identify why the real-data association occurs.
Arm (2) keeps all 28 dekads and its coefficient is not distinguishable from zero, but replacing five segments
with one changes the measured quantity as well as the fit's flexibility. The reduced model is a diagnostic
instrument, not a proposed replacement — it places the trough 13.67 d earlier than
PLSM (r = +0.544). The district arm (100 common rows, all p > 0.43) is
uninformative in either direction.

**Correction, 2026-09-13 (same day), narrowed 2026-09-16 — arm (3) is ceiling-limited; the estimator-dependence comparison
rests on arm (2).** Arm (3) admits no breakpoint later than **DOY 254.5**, while
the full PLSM places troughs on the same rows out to DOY 304.5, and **28.7% of
common-sample rows sit on that ceiling**. Arm (3)'s null is therefore attenuated by
construction for any late trough, and this subsection's original argument from its
smaller standard error (0.947 against 1.592) is **withdrawn** — the issue is not
variance but that the estimator cannot express the alternative. The three
coefficients are as reported; the inference from arm (3) alone was unsound.

What carries the estimator-dependence comparison instead, and is free of the ceiling: **arm (2)** keeps
all 28 dekads, its breakpoint can land anywhere out to DOY 404.5, it returns
−2.388 d with CI [−7.26, +2.45] excluding arm (1)'s +4.941 d, and the **paired
difference (1) − (2) on the same rows is +7.329 d, p_WCB 0.0027**. So the response
to exposure is **estimator-dependent**, established without ranking either
measurement as the better one. It shows that the fitted association changes when
the estimator changes; it does not identify which feature of the data or estimator
causes the original association. Arm (3) is reported only with its ceiling
and the 28.7% figure attached.

A ceiling-free row restriction (full-PLSM trough at least one dekad below the
ceiling; 10,496 rows) gives arm (1) +0.296 d, p_WCB 0.8014 and arm (3) −0.118 d,
p_WCB 0.9313. It **conditions on the dependent variable**, so both are mechanically
attenuated and neither is a valid estimate — it is reported as **descriptive
only**, and what it legitimately shows is that the placebo failure is absent among
early-trough rows and carried by rows whose five-segment fit placed t1 unusually
late, which is consistent with the candidate pathway but does not identify it as
the cause. Evidence:
`analysis/decisions_log.md` 2026-09-13 eighth entry, `analysis/deviation_log.md`
2026-09-13 seventh entry.

### 4.1.5 New commitment

1. **No coefficient in §3.8 A or §3.8 B is reported as a causal effect of cyclone
   exposure on rice phenology** — not the null ones and not the significant ones.
   The measured quantity is the **displacement of a fitted radar-trajectory
   breakpoint**, and every table, figure and sentence names it that way. §3.8's
   estimator, clustering, bootstrap and reporting rules are unchanged; what
   changes is what the output is called and what may be concluded from it.
2. The **timing placebo and the lead test are reported as primary results**, in
   §5.2's Results, before any coefficient. They are the strongest evidence this
   study produces about this design.
3. The **censoring test** (`python/censoring_test.py`) is a required output, with
   its synthetic demonstration and its stated limits.
4. **H1 and H2 are unaffected.** They are measurement-consistency claims —
   agreement between separate relative-orbit paths, which are not independent
   accuracy references, and inter-seasonal against between-pixel dispersion — and
   contain no causal claim about cyclones. The per-orbit export has now been
   analysed; §4.2 gives the results and their error-model limits.
5. §3.9's **permutation inference** (2,000 spatial permutations) has been run and
   is reported as a conditional spatial sensitivity (§4.1.7). The amplitude-
   crossing r-value grid is withdrawn as inapplicable to the fitted-breakpoint
   estimator (§4.3.3).

### 4.1.6 Per-hypothesis impact (§5.3 item 5)

- **H1 (measurement consistency, transplanting).** No impact. Live; blocked on the
  per-orbit export.
- **H2 (measurement consistency, harvest).** No impact. Live; blocked on the
  per-orbit export.
- **H3.** **NOT ESTIMABLE AS DECLARED.** §2 declares optical SOS, peak-NDVI and
  EOS outcomes, whereas this study estimated fitted radar breakpoints. The
  direction-only radar analogue is exploratory: 0 of 4 cells meet its positive-
  and-significant pattern, and β_pre on the fitted fall-end breakpoint points
  opposite to the predeclared analogue at both levels (−10.18 d district,
  p_perm 0.0075; −3.35 d pixel, p_perm 0.0005). Those numbers are not a verdict
  on H3, and the failed timing-placebo and lead checks prevent a causal reading.
- **H4.** **FAILS ITS DECLARED CRITERION: 2 of 6 sign agreements** (criterion 5
  of 6); pooled β₀ on the fitted fall-end breakpoint is −13.04 d (p_WCB 0.0034).
  The coefficients remain descriptive and subject to the same construct limit.
- **Objective 4 as a causal question** is **withdrawn** as answerable by this
  design and this instrument. It is replaced by what was actually measured: a
  quantified account of why a radar-breakpoint exposure design of this form does
  not identify a phenological response, and the diagnostic that shows it.

### 4.1.7 Amendment — §3.9's permutation test, run; conditional spatial sensitivity

§3.9's 2,000-permutation spatial placebo had never been run. It has now been
(`python/permutation_test.py`). Its interpretation was corrected on 2026-09-16:
the table does not establish bootstrap calibration or a causal mechanism.
Pixel arm, 2,000 within-state relabellings of whole
exposure histories, identity excluded, p = (1 + #{|t_perm| ≥ |t_obs|}) / (1 + n):

| cell | p_WCB | **p_perm** | permutation 95th pct of \|t\| |
|---|---|---|---|
| β_pre on fitted trough breakpoint | 0.8926 | 0.8381 | 1.250 |
| β_pre on fitted rise-end breakpoint | 0.6005 | 0.4608 | 1.469 |
| β_pre on fitted fall-end breakpoint | 0.0069 | **0.0005** | 1.970 |
| β_harv on fitted fall-end breakpoint | 0.8160 | 0.7961 | 2.144 |
| β_harv on fitted trough breakpoint — §3.9 placebo | 0.0008 | **0.0395** | 4.088 |
| β_harv on fitted rise-end breakpoint — exploratory | 0.0409 | 0.1774 | 3.059 |
| censoring (1)−(3) paired | 0.0065 | **0.0340** | 2.290 |
| censoring (1)−(2) paired | 0.0027 | **0.0420** | 3.609 |

The WCB column above is from the clean 9,999-replication rerun of 2026-09-16.
The earlier robustness table had silently used 999 replications; that runner defect
changed p-values but caused no 0.05 or 0.10 threshold reversal among the 48 cells
for which WCB is implemented. Coefficients, standard errors and permutation results
are unchanged to the reported precision.

District arm: β_pre on the fitted fall-end breakpoint p_perm 0.0075; placebo
p_perm 0.3068; β_harv on the fitted rise-end breakpoint p_perm 0.0720.

**What the table establishes.** The two conditional procedures give different
p-values. For the pixel timing placebo, p_perm is 0.0395; for its district
counterpart it is 0.3068. The paired censoring contrasts have permutation
p-values 0.0340 and 0.0420 under the specified relabelling scheme. These are
observations under that reference scheme, not proof that one procedure is
correct or that the other over-rejects. The earlier phrase "two to four times
wider" was also arithmetically unsupported: 2.14–4.09 divided by 1.96 is about
1.09–2.09, and a single quantile is not the width of an entire distribution.

**What it does not establish.** District histories are not randomly assigned in
the real study. Exchangeability within state is unverified; real cyclones have
spatially structured footprints. Studentizing the coefficient does not remove
this requirement. The relabelling exercise neither separates spatial confounding
from estimator behaviour nor calibrates WCB rejection rates under a known null.
The earlier claims that it resolved the competing explanation, established a
bootstrap failure, or selected a universally conservative test are withdrawn.

Both p-values must accompany the relevant descriptive contrasts, with the
district-season estimand kept primary and the selected pixel sample reported
separately. H3 and any mechanistic interpretation remain limited by the attrition,
measurement and observational-design constraints already recorded elsewhere.
No causal conclusion is rescued by choosing whichever p-value is preferred.

### 4.1.8 Amendment, same day — §3.8 A's declared robustness arms, run; both live results survive all of them

Four of §3.8 A's five declared arms are run (`python/robustness_arms.py`); the
fifth is withdrawn below. Inference is the permutation *p* of §4.1.7, 2,000
within-state relabellings per arm.

**Provenance of the variant catalogues.** The buffer and severity arms need
exposure recomputed from IBTrACS — the committed catalogue records only winds
within 50 km, so wider buffers add district-storm pairs absent from it.
`build_cyclone_exposure.py` was parameterised on buffer and severity with the
frozen values as defaults, so **one implementation of the rule** serves all arms;
the GADM v4.1 L2 shapefile was re-obtained and the roster reconstructed from the
catalogue's own state/district pairs (28 districts, matching the footprint
table). Rebuilding at 50 km / 48 kt reproduces
`district_cyclone_exposure_ibtracs50km.csv` **byte-for-byte** (md5
d5da3934fd3f2fd0a1f1b729d70d4089) and the footprint table content-identically
(row order aside). The script asserts that equality on every run and reports
nothing if it fails.

**§3.9's timing placebo, β_harv on the fitted trough breakpoint, declared zero:**

| arm | district β (p_perm) | pixel β (p_perm) |
|---|---|---|
| frozen 50 km / 48 kt | +5.001 (0.3068) | +7.438 (0.0395) |
| state × season FE | +0.721 (0.8186) | +4.493 (**0.0075**) |
| buffer 75 km | +5.432 (0.0980) | +6.436 (0.0210) |
| buffer 100 km | +6.330 (0.0205) | +6.063 (0.0105) |
| severity 64 kt | +6.627 (0.3358) | +4.761 (0.4518) — 6 treated clusters |

**Rejected in four of five arms at pixel level.** The fifth has 6 treated
clusters for harvest-window exposure, so §3.10's MacKinnon–Webb rule makes its
null uninformative, as the script predicted before the run.

**The state × season arm is not a rescue, and no arm is promoted.** At district
level the placebo nearly vanishes under it (+0.721, p_perm 0.8186) — that arm
removes between-state, within-season comparisons. At pixel level it gives +4.493,
p_perm **0.0075**: the coefficient is about 40% smaller, but the change cannot be
attributed uniquely to between-state contamination because the specification
changes the comparison set and fixed effects together. The remainder is rejected
more clearly than under the frozen FE,
because state × season FE narrows the permutation 95th percentile of |t| from
4.088 to 2.405. Had the two levels agreed there would have been a disciplined case
for interpreting under that arm — selecting a specification by a **placebo** is not
selecting on the outcome of interest, since the placebo must be zero by design and
carries no information about H3. That case does not arise. The declared headline
stays the declared headline. Widening the buffer is accompanied by smaller
district-level permutation p-values (0.3068 → 0.0980 → 0.0205 across 50, 75,
100 km); this pattern does not by itself identify a spatial mechanism.

**β_pre on the fitted fall-end breakpoint has a negative sign in every declared
arm, opposite to the predeclared analogue:**

| arm | district β (t) | pixel β (t) |
|---|---|---|
| frozen | −10.184 (−2.079) | −3.351 (−3.263) |
| state × season FE | −18.164 (−2.927) | −4.609 (−3.846) |
| buffer 75 km | −10.194 (−2.463) | −2.425 (−2.507) |
| buffer 100 km | −8.790 (−1.676) | −2.078 (−1.922) |
| severity 64 kt | −10.906 (−2.399) | −4.896 (−5.070) |

**Negative in all ten arm × level cells, |t| > 1.96 in eight.** Strongest under the
two arms that sharpen identification, weakest under the 100 km buffer, which is
what attenuation from adding marginally-exposed districts looks like. Harvest
occurs **earlier** under severe pre-season exposure where §4 predicts later, and no
predeclared variation of the design removes it.

**The fifth arm is withdrawn.** "The HLS panel 2016–2025 in place of Sentinel-2
(adds seasons 2016–2018, including Titli 2018)" cannot serve: §3.4's 2026-09-09
amendment already removed HLS as a substrate (Landsat plus Sentinel-2, the same
monsoon cloud, cannot observe the ascending limb here), and the arm's substantive
purpose — seasons 2016–2018 including Titli — is already met, the radar panel
spanning 2017–2025 with Titli 2018 in the headline.

**Still open, recorded rather than dropped.** §3.9's r-value grid (r_SOS ∈ {0.70,
0.75, 0.80}, r_peak = r_EOS ∈ {0.45, 0.50, 0.55}) is neither run nor withdrawn.
Those are amplitude-crossing thresholds from Paper 1's optical method; under PLSM
the markers are fitted breakpoints, so r appears to have no role in the primary
estimator and would move only the superseded crossing-rule arm. That must be
checked against §3.1's Gate 1 density ratio — a different quantity sharing the
letter — before the grid is run or withdrawn. Evidence:
`analysis/decisions_log.md` 2026-09-13 eleventh entry.


---

## 4.2 Historical amendment, 2026-09-13 — SUPERSEDED verdict and scale interpretation

> **Do not quote this section's heading or its “both NOT MET” summary as the
> current verdict.** The current clause-by-clause classifications are in §4.2.6
> and `analysis/hypothesis_verdicts.md`; the district-versus-pixel precision
> boundary is withdrawn. This section is retained only as the audit record of
> the intermediate interpretation.

The per-orbit export ran to completion (225 of 225 district-seasons, 170,321
per-orbit PLSM fits, `gee/S1_PER_ORBIT.js` → `python/orbit_agreement.py`). H1 and
H2 are now resolved on measurement rather than on assumption, and **both are NOT
MET**. Evidence: `analysis/decisions_log.md` 2026-09-13 fifteenth and nineteenth
entries; `results/dispersion/`, `results/orbit_agreement/`.

### 4.2.1 Clause (b), which needed no export and was never blocked

"Each pixel's inter-seasonal dispersion about its own mean, after removing season
effects, is smaller than the between-pixel dispersion within its district."
Measured on the committed panel, 2,000-draw district cluster bootstrap:

| marker | within | between | ratio | 95% CI |
|---|---|---|---|---|
| trough (H1) | 26.75 d | 19.97 d | **1.340** | [1.273, 1.408] |
| harvest (H2) | 26.00 d | 17.25 d | **1.508** | [1.424, 1.592] |

The clause requires the ratio below 1. Restricting to pixel-seasons with no severe
exposure of any timing class changes nothing (1.316, 1.454), so this is not
cyclones. **Clause (b) is NOT MET for H1 and for H2.** Season effects are removed
first, verified by a self-test that plants a 25 d/season common shift with no pixel
noise and recovers a within term of 1.6e-14 d.

### 4.2.2 Clause (a): between-orbit agreement, 8,515 paired pixel-seasons

> **Historical block retained for audit only; superseded by the amendment
> immediately below. Do not cite its verdict or terminology.** In particular,
> “harvest date” should read *fall-end breakpoint*, “bias” should read *mean
> signed between-orbit difference*, and the two orbit paths are not independent
> accuracy references.

    marker    sigma_single   r       within 1 dekad   within 2 dekads   baseline T
    trough      25.90 d    +0.339       38.2%            55.6%           70.0 d
    harvest     25.79 d    +0.147       35.0%            52.1%           60.0 d
    heading     19.82 d    +0.290       45.3%            64.6%           50.0 d

Two looks from different relative orbits — different look direction and
incidence angle — at the same pixel in the same season agree within one dekad **35
to 45% of the time**, and the harvest date correlates between orbits at
**r = 0.147**, very nearly uncorrelated. Between-orbit biases are a few days
(trough −5.63 d, heading −3.64 d, harvest +1.39 d), so the failure is variance and
not offset. **Clause (a) is NOT MET.**

#### Amendment, 2026-09-13: clause (a)'s verdict is split. The text below stands as written and is superseded.

The paragraph headed "Clause (a) is NOT MET" above, and the discussion following it,
are corrected by `analysis/hypothesis_verdicts.md`, which is now the authoritative
statement of every verdict. In short:

**The pre-declared criterion is MET.** T is the 90th percentile of |orbit difference|
on the untreated 2017 baseline, exactly as §2 requires, and the fraction of later
pixel-seasons within T is **0.9443** (trough, T = 70 d), **0.9114** (harvest, 60 d)
and **0.9387** (heading, 50 d) against a 0.90 criterion. All three pass; only harvest
in Andhra Pradesh fails a sub-scope (0.8564, n = 195).

**The NOT MET verdict rested on an absolute one-dekad criterion adopted after the
orbit fits existed.** That the declared tolerance is nearly vacuous is provable from
its construction without any treated season — but it was noticed afterwards, and
substituting a criterion after seeing results is result-aware however sound the
reasoning. An external re-audit on 2026-09-13 identified this and was correct.

So both are now reported and neither is presented as the other: the pre-declared
criterion **met but uninformatively permissive**, with T's value in dekads and the
construction that makes it so; and absolute agreement **poor, as exploratory** — 38.2%
and 35.0% within one dekad, r = +0.339 and +0.147, σ ≈ 26 d.

**H1 and H2 fail on clause (b), and on clause (b) alone.**

**And "all five predeclared hypotheses fail", stated at §4.2 and in the deviation log,
is withdrawn.** H5 was never tested (MODIS not obtained); H3's declared quantities —
optical SOS, peak NDVI date, EOS — were never estimated. See
`analysis/hypothesis_verdicts.md`.

**On the pre-declared tolerance.** §2 requires the tolerance fixed on the untreated
2017 baseline, and `orbit_agreement.py` does exactly that: T is the 90th percentile
of |orbit difference| on 2017 (n = 798). It comes out at **70, 60 and 50 days** —
six or seven dekads, a large fraction of the season. Because T is the 90th
percentile of the baseline's own disagreement, "90% within T" is close to true by
construction, so that column tests only whether later seasons are **no worse than
the baseline** — a stability check, which they pass. It is not an agreement
criterion and is not read as one. §2's instruction is followed and its output
reported; the absolute one- and two-dekad columns are what the claim rests on. One
dekad is the grid spacing and the finest agreement this grid can express; the
quantisation floor is 10/√12 = 2.89 d.

### 4.2.3 Clause (b) recomputed on a single orbit — observed quantities only

Clause (b) failed as measured. **This section does not explain why, and this study has
no evidence that would.** Two explanations point opposite ways — a noisy estimator, or a
crop whose planting really does move more between seasons than fields differ within a
district — and nothing here separates them.

What can be removed is an *estimator* mismatch. `dispersion_test.py` measures dispersion
on the committed panel, whose marker is fitted to all orbits composited together, while
the between-orbit statistic is measured between two single-orbit fits. Those are two
estimators and the two numbers are not commensurable. Recomputing the dispersion on a
**single orbit** — each pixel's best-covered relative orbit, at least two retained
seasons — puts both on one estimator:

| marker | within (d) | between (d) | observed ratio | pixels | pixel-seasons |
|---|---:|---:|---:|---:|---:|
| trough | 26.836301 | 20.210418 | **1.327845** | 6,602 | 28,562 |
| harvest | 27.213362 | 17.254319 | **1.577191** | 6,602 | 28,562 |
| heading | 21.322590 | 14.455730 | **1.475027** | 6,602 | 28,562 |

Mean retained seasons per pixel on its chosen orbit: **4.326265**, range two to nine.
The declared criterion is ratio < 1. **All three ratios remain above 1 in the single-orbit sample as well.** That sample is **selected separately** — each pixel's best-covered orbit with at least two retained seasons — from the paired sample the between-orbit statistic uses, and from the committed panel. So the three results sit side by side as observations on three samples, and **no causal statement about why clause (b) failed follows from any of them**. The committed panel's own figures
(1.340 and 1.508) are reported in `results/dispersion/`. *(Narrowed 2026-09-14, eighth pass:
this read "so the failure is not an artefact of the estimator mismatch". Withdrawn — ruling
out one candidate explanation is itself a causal statement, and the single-orbit sample is
not the paired sample, so the comparison does not license it.)*

The between-orbit statistic — sd(difference)/√2 = **25.90 / 19.82 / 25.79 d** for trough /
heading / harvest — is reported **alongside** these figures and is never subtracted from
them. §1.5.6 constraint 2 states what that identity does and does not license. The two
also describe different samples: the between-orbit statistic needs two orbits to have
fitted the same pixel-season, while the dispersion takes each pixel's best-covered orbit
alone.

> **Retired 2026-09-14 (sixth pass) — the variance subtraction.** Earlier versions of this
> section subtracted an assumed error variance from both dispersions and reported the
> remainder as "true within", "true between" and a "corrected ratio" of 0.441 / 0.724 /
> 0.724, concluding that clause (b)'s substantive claim about the crop was true and that
> the estimator was the cause. **That calculation is retired as an active analysis.** It is
> no longer computed, no longer written to any table, and appears nowhere in the active
> result set or the manuscript.
>
> Four defects, found across three external audits. *(i)* The error model it requires —
> additive error independent of the true date, equal variance on the two orbit paths,
> uncorrelated between them, independent across seasons within a pixel, and transporting
> from the paired sample to the single-orbit sample — was never tested, and §1.5.6
> constraint 2 declines to grant the third of those in the first place. *(ii)* Its
> between-pixel term divided σ² by the **mean** season count where unbalanced counts
> require the **mean reciprocal**: 1/mean(nᵢ) = 0.23114628 against mean(1/nᵢ) =
> 0.28164872, a 21.85% understatement of the error removed, always in that direction.
> *(iii)* The residuals are **district-year centred** before the pixel means are formed,
> which induces covariance between them that the subtraction ignores, so no single factor
> repairs it. *(iv)* The result was a small difference of two large numbers: a σ 3.613470%
> larger drove the trough's implied within-variance to zero, and a σ 10% smaller lifted
> two of the three derived ratios above 1.
>
> **It is not rescued with a better factor.** The paper does not use it, a matched
> uncertainty propagation for the unbalanced, centred estimator would be a new analysis in
> service of a calculation nothing depends on, and the untested error and selection
> assumptions would remain untested afterwards. The full dated history — the calculation,
> each defect, and the decision — is preserved in `analysis/deviation_log.md` and
> `analysis/decisions_log.md`, and the table's retired columns are described in
> `results/orbit_agreement/README_DispersionSingleOrbit.md`.

> **Also withdrawn, 2026-09-14 (fourth pass, §1.5.4 item 1) — the scale boundary.** This
> section once ended "That boundary, located and quantified, is the finding", setting the
> pixel-scale σ against ±1.3 d at district-season scale. **Withdrawn.** The two are not
> commensurable: σ is an *observed* between-orbit disagreement on the 7,717 later-season
> pairs of 8,515 usable pairs — 9.5% of 90,000 candidate pixel-seasons — while ±1.3 d is a
> *Monte Carlo on a synthetic trajectory* at an assumed district-mean noise of 0.122 dB,
> with no repeat measurement at district scale to check it against. Dividing one by the
> other locates nothing and certifies nothing about district-season timing. What the
> section supports is that **in the selected paired sample, between-orbit disagreement at a
> single 30 m pixel is substantial enough to limit fine-resolution timing applications
> under this estimator and this sampling design** — not that every pixel-level application
> is ruled out, and not that district-season timing is thereby reliable.

### 4.2.4 Where clause (a) is not estimable, named

A pixel-season enters clause (a) only when **two** orbits both pass §3's screens.
Per-orbit retention is 26.2%, so the rates compound: 8,515 of 90,000 pixel-seasons
offered, **9.5%**.

**Zero estimable pairs in all nine seasons — clause (a) is not testable at all:**
East Godavari and Visakhapatnam (Andhra Pradesh); **Ganjam and Nayagarh** (Odisha).
The orbit inventory predicted three of these four in advance.

**Fewer than 100 pairs across nine seasons, reported but carrying no weight:**
Krishna 55, West Godavari 25, Vizianagaram 7, Guntur 6 (Andhra Pradesh);
Khordha 61, Gajapati 57 (Odisha).

**By state:** Odisha 5,166 pairs across 10 of 12 districts; West Bengal 3,139
across 6 of 6; **Andhra Pradesh 210 across 5 of 7** — so clause (a) is effectively
an Odisha and West Bengal result, and no Andhra Pradesh claim is made from 210
pairs.

**Not one ascending/descending pair exists in Andhra Pradesh.** Every AP district
with pairs has `asc_desc` = 0.000. §4.1.8 recorded AP as mostly lacking that
pairing; at pixel level it lacks it entirely. Where the pair does exist (Odisha
0.59–0.97, West Bengal 0.83–1.00) agreement is better than for same-pass pairs
(σ 25.46 vs 27.97 d on the trough), but that comparison is **confounded with
district and state** — same-pass pairs occur where only same-pass orbits exist — and
nothing is inferred from it.

### 4.2.5 H2's optical cross-check is withdrawn

§2's H2 asks for "the post-monsoon Sentinel-2 EOS cross-check of §3.4 reported
alongside as a second, partly independent optical estimate". §3.4's 2026-09-09
amendment removed HLS as a substrate and the optical panel is unusable under
monsoon cloud, so no Sentinel-2 EOS series exists for these district-seasons.
Withdrawn by this amendment; `orbit_agreement.py` prints the withdrawal in its
output so the absence cannot read as an oversight. H2 clause (a) rests on the radar
orbit pair alone.

### 4.2.6 Per-hypothesis status, final

> **CORRECTED 2026-09-14, and the heading's word "final" was part of the defect.** The
> block below is the **superseded** status. It is left standing, as every superseded
> statement in this protocol is, with the corrected block after it. Three things were
> wrong with it: H1 and H2 are summarised as "NOT MET" although clause (a) is **MET as
> declared** and only clause (b) fails — which §4.2.7 item 1 of this very amendment
> forbids, below; H3 is given a verdict on a test that was never run;
> and the closing sentence asserts the "every predeclared hypothesis fails" verdict that
> **§4.2 itself withdraws** at §4.2.2 above, in the same amendment. So this protocol
> contradicted itself within one section, and asserted it was final while doing so.
>
> The external re-audit of 2026-09-14 found that withdrawn verdict standing in three
> files (`README.md`, `analysis/test_classification.md`, `osf/README.md`). **It was in a
> fourth — this one — and the first pass of corrections did not reach it**, because the
> search was run over the propagated *summary* phrasing and this block states the verdict
> hypothesis by hypothesis instead. Found on a second sweep of the same day, by the
> author, after the same residue turned up in a reviewer-checklist line of
> `analysis/test_classification.md` that the first pass had also missed. Two files, two
> misses, one cause: a phrase-match sweep does not find a verdict restated in a different
> shape. `analysis/hypothesis_verdicts.md` is and remains the authoritative record.

    SUPERSEDED 2026-09-14 -- do not quote this block:

    H1  NOT MET   clause (a) 38.2% within one dekad, sigma 25.90 d, r +0.339;
                  clause (b) ratio 1.340 [1.273, 1.408]
    H2  NOT MET   clause (a) 35.0% within one dekad, sigma 25.79 d, r +0.147;
                  clause (b) ratio 1.508 [1.424, 1.592]
    H3  NOT MET   0 of 4; beta_pre on EOS significant with the WRONG sign at both
                  levels (p_perm 0.0005 pixel, 0.0075 district)
    H4  NOT MET   2 of 6 sign agreements against a 5-of-6 criterion
    H5  withdrawn (MODIS not obtained)

~~**Every predeclared hypothesis in this study fails, and each failure is now measured
rather than asserted.**~~ **Withdrawn 2026-09-14.**

**The corrected per-hypothesis status.** Each clause is named, and no hypothesis is
summarised past its clauses:

    H1  clause (a) MET AS DECLARED  0.9443 within the baseline tolerance T = 70 d
                                    against a 0.90 criterion
        clause (b) NOT MET          dispersion ratio 1.340 [1.273, 1.408], required < 1
        exploratory, not declared:  38.2% within one dekad, sigma 25.90 d, r +0.339
    H2  clause (a) MET AS DECLARED  0.9114 within T = 60 d against 0.90; fails in
                                    Andhra Pradesh alone (0.8564, n = 195)
        clause (b) NOT MET          ratio 1.508 [1.424, 1.592]
        exploratory, not declared:  35.0% within one dekad, sigma 25.79 d, r +0.147
    H3  NOT ESTIMABLE AS DECLARED   S2 declares beta on optical SOS, peak NDVI date and
                                    EOS. This study fits radar trajectory breakpoints,
                                    which S3 states are NOT those quantities (MARC puts
                                    the harvest breakpoint +50.4 d from a harvest date,
                                    in all 25 districts). The declared quantities were
                                    never estimated, so "NOT MET" claimed a test that
                                    was not run.
        radar analogue, EXPLORATORY 0 of 4 cells positive-and-significant; beta_pre on
                                    the harvest breakpoint significant with the WRONG
                                    sign at both levels (p_perm 0.0005 pixel,
                                    0.0075 district)
    H4  FAILS ON ITS DECLARED       2 of 6 sign agreements against a 5-of-6 criterion;
        CRITERION                   pooled beta_0 on harvest -13.04 d
    H5  WITHDRAWN, NOT TESTED       MODIS panel never acquired (S4.3.2). An untested
                                    hypothesis has no verdict and is not a failure.

**Read as one sentence: of the five predeclared hypotheses, one fails on its declared
criterion, two fail on one clause while their other clause passes as declared, one is not
estimable as declared, and one was withdrawn untested.** No clause's criterion was
rewritten in either direction; §4.2.7 below states the reporting commitments that follow.
What the study establishes instead is stated at §4.1.5 and §4.2.3: a quantified account of
the level at which this instrument works, and a design whose own falsifiability check
rejects it at pixel level.

### 4.2.7 New commitment

1. H1 and H2 are reported **clause by clause**. Neither is summarised as "not met"
   without naming which conjunct failed and what the other showed — clause (b)'s
   substantive claim survives error correction and that must be said.
2. Clause (a) is reported **per state**, with pair counts and pass composition, and
   the four zero-pair districts named. No Andhra Pradesh claim from 210 pairs.
3. The baseline tolerance is reported with its value in dekads and the explicit
   statement that it is a stability criterion, never as an agreement threshold.
4. σ ≈ 26 d per pixel-season is reported wherever a per-pixel quantity appears, and
   no per-pixel marker is quoted to better than a few dekads.
5. The district-season mean marker remains the unit for every substantive claim, as
   §3.8's level-of-estimation note already required for its own reasons.


---

## 4.3 Amendment, 2026-09-13 — four open items closed: H3's construct mismatch, H5's withdrawal, §3.9's r-value grid, and §3.5's mask comparison

Raised by an external audit of GitHub `main` (`a59f5fa`) on 2026-09-13. Each was
genuinely open; each is closed here rather than left to be found again.

### 4.3.1 H3 is predeclared on optical markers the radar estimator does not produce

**The problem, stated plainly.** §2's H3 and §4's sign table are written on **SOS,
peak NDVI date and EOS**. The primary estimator produces fitted trajectory
breakpoints — **end of the dark phase, end of the rise, end of the plateau and
end of the fall** — and §3's own 2026-09-12 note says these are *not* SOS/POS/
EOS. Their observed medians are DOY 249.5, 314.5 and
384.5, against Paper 1's optical windows of 155–240, 240–320 and 280–380, a
separation of roughly 40–60 days. *(Reworded 2026-09-14, eighth pass: that note
described the optical windows as "40–60 days **too early** for the radar season on
this coast". "Too early" judges an optical bound by a radar distribution, which is
a cross-sensor construct-identity claim this study cannot make. The separation is
reported as a separation — it shows the bounds are **not transferable** between
these two measurands, and says nothing about whether either is correct for its own
sensor.)*

The H3 verdict recorded at §4.1 and §4.2.6 was reached by mapping trough→SOS,
heading→peak, harvest→EOS. **That mapping was never authorised by an amendment**,
and `python/event_study.py` has been printing a warning that the correspondence "is
NOT validated by this study" while the verdict relied on it. That is an
inconsistency in this protocol's own paper trail, not merely a caveat.

**The resolution.** The mapping is authorised **for direction only, never for
identity.** §4's predictions are directional — exposure *delays* transplanting,
*delays* the peak, *delays* harvest. A directional prediction about the timing of a
season transfers to any marker that tracks that season monotonically: if the season
runs late, every breakpoint on its trajectory moves later, whatever each breakpoint
is called. What does **not** transfer is the claim that a radar breakpoint measures
the same physical event as an optical threshold crossing. So:

- The radar analogue is explored as a set of **directional predictions on fitted
  radar-trajectory breakpoints**: β_pre > 0 on the fitted trough, rise-end and
  fall-end breakpoints; β_harv > 0 on the fitted fall-end breakpoint.
- This exploratory analogue is **not H3's declared optical test**, and no sentence
  in the manuscript may imply that it is.
- Every table, figure and sentence names the outcome as the fitted breakpoint —
  trough, heading, drainage, harvest — never SOS/POS/EOS. This is §4.1.5's
  commitment 2, and it is now the condition under which H3 has any verdict at all.

**Current verdict: H3 is NOT ESTIMABLE AS DECLARED.** The optical outcomes were
not measured. In the exploratory radar analogue, 0 of 4 cells meet the directional
and significance pattern, and β_pre on the fitted fall-end breakpoint points
opposite to the predeclared analogue at both levels (p_perm 0.0005 pixel, 0.0075
district). These are exploratory radar-breakpoint results, not an H3 verdict.

> **Historical correction, 2026-09-14.** The previous version of the paragraph
> above said "The mismatch affects what the verdict means, not what it is". That is wrong, and
> it is wrong in the direction that flatters the study: it lets a verdict stand on a test
> that was not run. §2 declares β on optical SOS, peak NDVI date and EOS. Those quantities
> were **never estimated** — §3 states the fitted breakpoints are not them, and MARC puts
> the harvest breakpoint later than its harvest date in all 25 districts, by a mean of +50.35 d
> with a per-district range of +26.19 to +60.54 d (*precision added 2026-09-14: the mean is not
> each district's offset; what holds everywhere is positive and above +26 d*). A hypothesis whose
> declared outcome was never measured cannot be NOT MET; it is **NOT ESTIMABLE AS
> DECLARED**, and the radar analogue's 0-of-4 is **exploratory**, which is a weaker claim
> than the one made here, not a stronger one. §4.2.6's corrected block of this date carries
> the authoritative wording, together with `analysis/hypothesis_verdicts.md`. Everything
> else in §4.3.1 stands: the direction-only mapping, the naming rule, and the four
> coefficients themselves are unaffected.

### 4.3.2 H5 is withdrawn, formally

H5 (MODIS district-level SOS coherence, Spearman ρ ≥ 0.70) has been treated as
withdrawn in working notes since the MODIS panel was not obtained, but never by a
dated amendment. **It is withdrawn here.** The MOD13Q1 panel was never exported and
no correlation output exists. §2's own H5 bullet already refused pixel-level MODIS
RMSE, although its all-state field-size rationale was not adequately sourced; what is
withdrawn now is the district-level coherence claim as well, for the plain reason
that the data was not acquired. No result is reported for H5 in any form.

### 4.3.3 §3.9's r-value grid is withdrawn as inapplicable to this substrate

§3.9 asks for "DiD coefficients at r_SOS ∈ {0.70, 0.75, 0.80} and
r_peak = r_EOS ∈ {0.45, 0.50, 0.55} as a supplementary sensitivity grid." Those are
**amplitude-crossing thresholds** from Paper 1's optical method: the fraction of
seasonal amplitude at which a marker is declared. The primary estimator does not
use them. `plsm_fit` selects breakpoints by weighted residual sum of squares and
`plsm_retain` screens on the fitted rise against the series' own residual variance;
neither references an amplitude ratio anywhere. Varying r would move only the
superseded crossing-rule arm (`extract_markers`), which is not the headline and
carries no reported coefficient. **The grid is withdrawn as inapplicable, not as
inconvenient.**

The letter *r* also names a different quantity — §3.1's peak-relative
sampling-density ratio — and that sensitivity **is** already reported, in §3.1's
2026-09-12 note, as a measured two-arm comparison on the 2017 baseline: no gate
against r = 0.50 gives median valid dekads 26 vs 24, minimum 19 vs 10, and
retention 0.2426 vs 0.2544, with the gate manufacturing the only §3.11
ineligibility in the entire baseline. Gate 1 is therefore inert at pixel level by a
documented decision and applied at 0.5 to the district-mean curve. Nothing further
is owed on either r.

### 4.3.4 §3.5's mask comparison: not run, and how it will be

§3.5's disclosure rule requires the primary-mask and intersection-mask
coefficients "computed for every district × cyclone unit and reported side by side
before either is discussed." **It has not been run, and no script implements it.**
That is a real omission and it is recorded as one.

Re-drawing a cohort inside RiceAtlas ∩ WorldCereal `temporarycrops` would mean a
second complete data campaign — new cohort, 225 new exports, full refit — and would
break `cell_id` as a stable key across the two arms, which is the one thing that
makes them comparable. The feasible design holds the cohort **fixed** and splits it:
export a WorldCereal membership flag for each of the 10,000 committed cohort points
(25 tasks, one row per point, the same shape as the static-covariate export), then
re-run the reported analyses on the in-both-masks subset and report the two side by
side. `gee/S1_MASK_FLAG.js` implements that export.

Until it is run, **no mask-dependent claim is made.** That is a weaker commitment
than it sounds, because §4.1's amendment already withdraws every causal claim from
§3.8, and the surviving results are measurement quantities — σ ≈ 26 d, retention,
the placebo failure — whose mask dependence is exactly what this arm would test. So
the arm remains **required before any of those is reported as a property of rice
pixels rather than of this cohort**, and the manuscript states the omission where
the mask is discussed.

Whenever it is run, §3.5's verbatim disclosure stands: the intersection is with a
**general-cropland classifier**, not an independent rice product, because
WorldCereal v100 contains no rice layer.

#### Amendment, 2026-09-13: run. The status above is superseded.

The section heading and body above are left as written, per the append-only rule.
They are no longer accurate: the export has been produced and the arm is
implemented in `python/mask_sensitivity.py`. The full record is in
`analysis/deviation_log.md` under this date; what matters for the protocol:

- **The export is verified, not assumed.** All four catalogue checks in
  `gee/S1_MASK_FLAG.js` passed and the returned values are recorded in its
  CONFIG: the asset resolves (591 images), `temporarycrops` is present (106
  tiles), and `classification` takes exactly the two values 0 and 100 — so the
  cropland code of 100, the one assumption that could have silently voided the
  arm, is confirmed. A one-district dry run was checked before the 25-task run
  was authorised, and the full run reproduced the dry-run CSV byte for byte.
- **The fixed-cohort design above is the one implemented.** 25 files, 10,000
  rows, one per committed cohort point, joining 10,000/10,000 both ways against
  the committed panels with zero district-label disagreements. `cell_id` remains
  the stable key across arms, which was the requirement.
- **Retention: 8,085 of 10,000 points (80.85%).** Per district 46.0% to 98.3%;
  no district at 0% or 100%. The arm therefore has a sample, which was not
  guaranteed in advance.
- **The arm re-runs the committed estimator, it does not mask the panel.** The
  district-season panel is a PLSM fit to the district-season *mean curve*, not an
  average of pixel phenometrics, so the mask is applied to the 225 raw exports
  and the mean curve is rebuilt and refitted. Re-implementing the aggregation
  would have made the arm a test of the re-implementation.
- **The mosaic ambiguity is bounded, not waved away.** 62 of 10,000 points
  (0.62%) fall under overlapping WorldCereal tiles, where the mosaic pick is
  arbitrary. The arm is reported a second time with those points dropped
  (8,026 points, 80.26%). *Clarified 2026-09-14: 62 points are **identified** as
  multi-tile; **59** of them are also flagged `in_worldcereal_temporary = 1` and so
  are the only ones the second variant actually removes (8,085 − 59 = 8,026). The
  other 3 were already outside the intersection mask, so dropping them changes
  nothing. Both figures are readable from the committed
  `results/mask_sensitivity/mask_flag_all.csv`; the earlier wording implied 62 points
  left the sample.*
- **§3.5's disclosure is unchanged and still binding:** the intersection is with
  a general-cropland classifier, not an independent rice product.

One result is worth recording here rather than only in the log, because it is the
only external corroboration of the cohort anywhere in this study: over Puri's
bounding box WorldCereal calls 30.9% of the area cropland, and at Puri's cohort
points 86.5% — a 2.8× enrichment, in the direction required if the cohort
selection is finding agricultural land. It is not a rice validation and is not
reported as one.

The consequence for §4.1's standing withdrawal is narrow and must not be
overstated: this arm tests whether the surviving measurement results depend on
the mask. It restores no causal claim.

## 4.4 Post-analysis correction and robustness audit, 2026-09-16

This amendment records corrections made after the analysis and does not recast
them as predeclared tests.

1. **The active H1/H2 measurands are radar breakpoints, not agronomic dates.**
   Earlier active wording still called the fitted trough a transplanting date and
   the fitted fall-end a harvest date, despite the protocol's own construct-validity
   restriction and the absence of field reference data. H1/H2, their code comments,
   the timing placebo and the window-sweep summary now name the measured trough,
   rise-end and fall-end breakpoints. MARC's dates remain dates; the comparison is
   explicitly between different measurands.
2. **Repeat-coverage robustness was added post hoc.** Requiring progressively
   more retained seasons per pixel leaves all trough, rise-end and fall-end
   within/between dispersion ratios above one. The diagnostic supports the
   stability of the measured failure but does not identify its cause.
3. **State-specific orbit tolerances were added post hoc.** They show that passing
   the pooled baseline-tolerance rule is not evidence that one threshold transfers
   across three states. Andhra Pradesh has only 15 baseline pairs and its
   state-specific result is labelled underpowered.
4. **Orbit-pair selection was tested post hoc with marker-blind alternatives.**
   The lowest-orbit rule and a unit-weighted all-eligible-pairs rule leave the
   pooled clause-(a) verdict and scaled disagreement essentially unchanged,
   including under the fixed declared tolerances. This addresses dependence on
   the declared pair rule; it does not establish accuracy or independent errors.
5. **The attrition completeness gate was rebuilt to fail closed.** It now verifies
   exact row keys and schemas, finite numeric fields, bootstrap counts, event-study
   provenance and agreement between final and partial tables. The old
   `beta_balanced`/`delta_beta` comparison is not regenerated because it changed
   both sample composition and time window; the two-season rows remain descriptive.
6. **The executed literature search supersedes the planning matrix.**
   `docs/LitGap_v0.2.md` records the 2026-09-16 queries, screened-result counts,
   verified sources and claim boundaries. It supports no priority claim.
7. **Reproduction environments are separated.** The numerical-analysis and
   figure-rendering profiles are checked separately under `environments/`. The
   archived independent Windows replay records Python 3.12.14; the older root
   note naming 3.11.15 is preserved as production history, not misreported as the
   replay environment.

### 4.4.1 Additional implementation and inference corrections, 2026-09-16

The exposure-variant verifier was experimentally shown to accept an empty
rebuild directory: joining an absolute baseline pathname discarded the variant
directory and compared the file with itself. That check is replaced by a separate
baseline path, exact eight-output receipt, generator hash and changed-output
refusal. A raw NOAA/GADM rebuild on 2026-09-16 reproduces the baseline and all
three exposure catalogues exactly; the footprint variants agree by keys and
values but differ in row order. This verifies the recorded rebuild, not the
scientific adequacy of the exposure definition.

The robustness-arm driver also defaulted to 999 bootstrap draws, despite §3.8's
9,999. Both levels are being rerun at 9,999; counts and unavailable state-by-season
FE bootstrap inference are now explicit. Final acceptance depends on the completed
tables and their comparison, not this amendment. No stale per-arm file may
silently overwrite a newer row through last-file-wins collection.

Protocol §4.1.7 now distinguishes permutation sensitivity from bootstrap
calibration and withdraws the mechanism inference. The quantified effects of
changing an endpoint are restricted to the endpoints tested; failure to reject
zero is not an assertion of zero. Figure 7's strict-monotonicity claim is removed.
The selection model and grouped terrain summaries remain descriptive.

The runner's dependency order, static-panel merge, explicit phase inputs and
figure interpreter routing are corrected. Orbit fitting now refuses stale,
legacy or interrupted caches unless restarted in a new output directory. These
are reproducibility safeguards, not changes to numerical fitting rules.

`analysis/current_audit_status.md` distinguishes completed checks from work still
running. This amendment grants neither manuscript approval nor release approval.

## 5. Outputs and reporting

### 5.1 Data products

- `RiceBaCI_QC_panel_S2_v1.csv` — full Sentinel-2 QC panel, 13-column schema, one row per (district, year, tile_id, cell_id, bin).
- `RiceBaCI_QC_panel_HLS_v1.csv` — full HLS panel, same schema, 2016–2025.
- `docs/district_cyclone_exposure_ibtracs50km.csv` and `docs/cyclone_footprints_ibtracs50km.csv` — the pre-declared exposure and named-cyclone footprint tables of §1.1, generated by `python/build_cyclone_exposure.py` from IBTrACS v04r01 and GADM v4.1 and committed before extraction.
- `RiceBaCI_QC_panel_MODIS_v1.csv` — district-median MOD13Q1 NDVI curves for H5.
- `SAR_sanity_v1.csv` — VH/VV medians in ±14-day landfall windows per district × cyclone.

All CSVs shipped in a versioned archive. **Status, 2026-09-14:** all 10 intended files are uploaded at 100% to the **unpublished Zenodo draft `22750338`**, including `Paper2_raw_inputs_2017-2025.zip` (md5 `dd6c208a27ce86555fd34cd8f13a1b6c`). The draft is **not released and has no DOI**, so no DOI may be cited and the archive may not be described as public until it is. Its replay kit is pinned to `fc5eadb6292dfba945cf53c2b1f4eea9b8d75019` and **must be refreshed after the final accepted commit**. `DATA_AVAILABILITY.md` is the statement of record until release. *(Updated 2026-09-14, eighth pass; this read "All CSVs shipped in a Mendeley Data v3 archive (v2 was for the Paper 1 WB pilot). Zenodo mirror as a versioned release", which predates the upload. The Mendeley route is superseded.)*

### 5.2 Manuscript

- Methods section prose language for pre-registration substitute: **"The QC thresholds and hypotheses in §3 were fixed in `docs/Protocol_v1.md` (commit `2cf493a`, dated 2026-09-07) before the full multi-state extraction was run. The commit history of `github.com/pandasupranab/RiceBaCI-QC` is auditable."**
- Do **not** claim this study was "pre-registered".
- Do **not** cite any OSF DOI or `osf.io/*` URL.
- The `osf/` folder in the repo contains historical drafts from the WB pilot phase and is not part of the Paper 2 evidentiary base. `osf/README.md` will be updated to say so before any manuscript submission.

### 5.3 Deviation discipline

Any deviation from this protocol after the commit that adds it to `main` must be recorded in `analysis/deviation_log.md`. Each entry states:

1. What changed.
2. Why.
3. Which sections of `docs/Protocol_v1.md` are affected.
4. New commitment.
5. Per-hypothesis impact.

The existing `analysis/deviation_log.md` starts with DEV-001 (2026-06-15). Future entries append.

---

## 6. Provenance

- **Analysis substrate:** GEE Cloud project `durable-pulsar-486209-b5` (legacy user asset namespace `users/supranab/` retained for the West Bengal RiceAtlas asset); Sentinel-2, HLS, MODIS, Sentinel-1 collections cited above.
- **District geometry:** GADM v4.1, downloaded from https://gadm.org/data.html.
- **Rice mask (WB):** IRRI RiceAtlas v1.0, Harvard Dataverse DOI 10.7910/DVN/JE6R2R.
- **Rice mask (OD, coastal AP):** documented in `docs/rice_mask_options.md`.
- **Field reference for H1:** Field reference sources for H1 (all three states — West Bengal, Odisha, coastal Andhra Pradesh) are to be catalogued in `docs/field_reference_sources.md` before H1 is claimed for any state.

  **Amendment 2026-09-14 — this precondition was written for a version of H1 that no longer exists, and it is re-attached.** It dates from the frozen protocol, where H1/H2 were *accuracy* claims (bias and RMSE against MARC and against field observation). §2's rewrite of 2026-09-09 withdrew every accuracy claim: H1 and H2 are now **measurement-consistency** claims, tested by between-orbit agreement and by inter-seasonal against between-pixel dispersion. Neither needs a field reference, and both were resolved in §4.2 without one. **The precondition therefore does not gate H1 or H2 as they now stand.** It gates **H1c / H2c** (product agreement and calendar plausibility, reported and never tested) and **§3.4's Tier 2** calendar-bounding leg — and there it binds harder than before, not softer. The catalogue now exists and is committed. It endorses **Odisha only**: three ICAR-CRIDA / OUAT district contingency plans plus CRRI Technology Bulletin 62, the last of which is **endorsed but not archived** (`icar-nrri.in` unreachable from the sandbox). West Bengal is **NOT FOUND**; coastal Andhra Pradesh is **NOT FOUND**, with its one ANGRAU candidate explicitly dropped on agro-climatic-zone grounds. Consequently: **no three-state calendar-validation statement may be written**, any Odisha calendar statement must be attributed to the named contingency plan rather than to "the state extension crop calendar", and §3.4's AICRP attribution is suspended (see the §3.4 amendment of this date). Presence of a PDF in `docs/field_reference_pdfs/` is not endorsement — five of the nine archived files are unendorsed candidates, one of them explicitly rejected — and the catalogue's archive manifest of this date states the status of each.

---

*End of Protocol v1.*
