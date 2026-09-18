# SUPERSEDED HISTORICAL LITERATURE MAP — DO NOT USE FOR CURRENT NOVELTY

This June 2026 planning document describes an optical peak-relative QC paper
that was not executed. Paper 2 became a Sentinel-1 measurement and inference-
limitation study, and the current evidence does not support the contribution or
priority claims below. The cited `manuscript/scoping_memo.md` and
`manuscript/refs.bib` never existed. A dated v0.2 search protocol and its logged
results must replace this file before any manuscript novelty claim is drafted.
The historical text is preserved only to show how the project changed.

# Lit-Gap Map v0.1 — Paper 2 (RiceBaCI-QC), historical text

**Compiled:** 15 June 2026 · Bhubaneswar
**Authors:**
- Supranab Panda (corresponding author) — Center for Environment and Climate, Institute of Technical Education and Research, Siksha 'O' Anusandhan (Deemed to be) University, Bhubaneswar 751030, Odisha, India. `pandasupranab@gmail.com`
- Sarat Chandra Sahu (supervisor, co-author) — Center for Environment and Climate, Institute of Technical Education and Research, Siksha 'O' Anusandhan (Deemed to be) University, Bhubaneswar 751030, Odisha, India (Director, CEC).

**Status:** Day 2 deliverable for Paper 2 (peak-relative QC framework for cyclone-impact rice phenology)
**Companion files:** `osf/OSF_PreReg_v0.2.md`, `manuscript/scoping_memo.md` (see Paper2_Kickoff_Pack v2)

---

## 1. Purpose

This document audits how existing optical and SAR rice/crop phenology workflows handle quality control (QC) — specifically the **gates that decide whether a pixel-by-DOY observation is admitted to phenometric extraction**. The literature defines many such gates, but they are almost always **absolute thresholds tuned to one region**. The Paper 2 contribution is to replace those absolute gates with a **peak-relative non-parametric rule** that travels across districts and states without retuning. This matrix shows where the field currently sits and where the gap lives.

The 10 QC-workflow papers below cover three eras: (a) the MODIS-era foundational workflows (Zhang 2003, Sakamoto 2005, Pan 2015, Boschetti 2017, Yan & Roy 2014), (b) the HLS/Sentinel-2 transition (Bolton 2020, Onojeghuo 2023), and (c) the SAR + smallholder + South Asia stack relevant to Amphan 2020 (Bouvet 2018, Singha 2019, Mishra 2024). Row 9 (Zhao et al. 2024 MARC) is included as a **benchmark product** rather than a QC workflow; see the note directly above the matrix.

---

## 2. Synthesis matrix — 10 QC-workflow papers × 6 QC dimensions, plus 1 benchmark product

**Note on row 9 (Zhao et al. 2024 MARC).** MARC is a 0.5° × 0.5° gridded rice calendar built by aggregating ~20 sampled paddy fields per grid cell within a 500 m MODIS-derived rice mask. It is not commensurable with the pixel-level QC workflows in rows 1–8 and 10–11 — its "gates" operate at a fundamentally different scale. Row 9 is retained here because MARC is the **benchmark product** that H1a/H1b/H2a/H2b in `docs/Protocol_v1.md` §2 are pledged to beat; a separate benchmark-product treatment would fragment the audit trail. Do not read row 9's QC-dimension cells as commensurable with the other rows; read them as a description of how MARC was built.

| # | Paper | Sensor / scale | Cloud / atmosphere gate | VI floor / threshold | Smoothing | Phenometric extraction rule | Validation metric | Region |
|---|---|---|---|---|---|---|---|---|
| 1 | Pan et al. 2015 (winter wheat, Czech) | MODIS MOD09GQ 250 m | QA-band "good quality" pixels only; snow + cloud state from MOD09 flags; NDVI < 0.1 dropped as soil | Z-score thresholds Thr-0 to Thr-0.6 (in 0.05 steps), per-station tuned; default 0.1 outperformed standard 0.5 (RMSE −8.89 d) | BISE (best-index slope extraction) on multi-year NDVI; SOS searched only DOY 220–280 | **Per-station threshold tuning** against ground phenology; no transferability test | RMSE in days vs. ground phenology stations | Czech winter wheat, 2015–2020 |
| 2 | Zhang et al. 2003 / 2018 VIIRS update | MODIS NBAR / VIIRS, 500 m–1 km | NBAR view-angle correction + cloud-cleared SR; 16-day moving window for BRDF fit | EVI increase > **35 % of annual range** within any rising/falling period; local-max EVI ≥ **0.7 × annual-max EVI**; EVI < 0.25 treated as snow | Logistic curve fit on 5×8-day NBAR EVI windows | Curvature change-rate extrema on the fitted logistic; rejects sub-amplitude wiggles | Continental land-cover dynamics product comparison | Global LSP |
| 3 | Bolton et al. 2020 (HLS continental) | HLS L30 + S30, 30 m | HLS Fmask QA bands; per-scene drop of cloud/shadow/snow | Seasonal amplitude threshold (Friedl 2020 rule); EVI2 background = mean of values below 10th percentile | Penalized cubic smoothing splines, daily interpolation; product year ± 6-month buffer | HPLM (hybrid piecewise logistic model) reconstruction of green-up & senescence; 4 transition dates from curvature extrema | Phenocam network comparison across CONUS | CONUS / Alaska, 2016–2018 |
| 4 | Sakamoto et al. 2005 (paddy rice, Japan) | MODIS MOD09 daily, 250–500 m | Sensor zenith > 32.25° dropped; daily EVI smoothed before peak detection | Heading-date EVI ≥ **0.5**; harvesting EVI ≥ **0.3** AND (EVI + 0.05) ≥ LSWI within 13–15 8-day composites; transplanting (LSWI + 0.05) ≥ EVI within 7–9 composites preceding heading | Wavelet transform (Coiflet order 4, scales 32 + 64) | Local maxima/minima/inflection on smoothed EVI; absolute VI thresholds gate each stage | RMSE 9–12 d vs. statistical heading/harvest dates | Japan, Mekong Delta |
| 5 | Boschetti et al. 2017 — PhenoRice | MODIS MOD13Q1, 250 m, 16-day | Weighted Savitzky–Golay using usefulness + reliability flags; blue band (b3) gates atmospheric contamination; MODIS QA 250 m removes cloud-contaminated SOS pixels; LST ≥ 15 °C gate | Local min / max on smoothed EVI; **agronomic plausibility rules** (SOS-to-POS duration, flood signature within transplanting window) reject implausible cycles | Weighted S–G two-iteration | Rule-based: every candidate min/max must satisfy SOS-POS interval + flood-index check | MAE 9.95 d, ME 4.07 d on crop establishment; r² 0.75–0.92 on rice area | India, Italy, Philippines |
| 6 | Yan & Roy 2014 (WELD field extraction) | Landsat WELD, 30 m | QA-band cloud/shadow/water/snow + NDWI ≤ 0.05 zeroed out; multi-temporal compositing fills gaps | No absolute VI threshold for cropland gate — uses 10 time-series statistics (min, max, mean, CV, P25/50/75, max-slope, min-slope, day-of-max) | Multi-scale image segmentation + temporal differencing | Field-object level rather than per-pixel; statistics-driven | Compared to USDA CDL classification | Texas, California, South Dakota |
| 7 | Bouvet et al. 2018 (Sentinel-1 transplanting) | Sentinel-1 GRD IW, 10–20 m | SAR is cloud-immune; speckle filter Refined Lee 3×3; terrain corrected; dB-scale | **Transplanting date = local minimum of VH (or VV) in pre-monsoon → monsoon transition**; threshold-free, signature-based | Multi-temporal compositing (5-day median) | VV/VH backscatter local minima detected; secondary check using VV–VH ratio | OA 93.5 % on Vietnam Mekong (10 m VVVH stack) | Vietnam, India, Bangladesh |
| 8 | Singha et al. 2019 (boro rice Bangladesh) | Sentinel-1 IW VV + VH | Cloud-immune SAR; multi-Otsu thresholding instead of fixed VI cuts | **Multi-Otsu adaptive threshold** on transplantation VVmin per crop zone; peak NDVImax composite for second-stage classification | Per-zone min-composite over transplantation period; max-composite over peak | Zone-specific Otsu break used to identify boro rice; not phenometric extraction per se | Validated against Bangladesh upazila statistics | Bangladesh (boro rice) |
| 9 | **[BENCHMARK PRODUCT — not a QC workflow]** Zhao et al. 2024 (MARC gridded rice calendar, ESSD) | Sentinel-1 VH + Sentinel-2 EVI/NDYI, **aggregated to 0.5° × 0.5° grid** via ~20 sampled paddy fields per grid cell in a 500 m MODIS rice mask | S-1 cloud-immune; S-2 uses QA60 60 m band + cloud filter > 50 % + cloud-score method | Feature-based algorithm + fitted Weibull function; not a VI-value gate | LOESS smoothing (span 0.075 on VH; span 0.2 on EVI and NDYI) | **Transplanting date = minimum VH (Sentinel-1)** in detection window; **harvest date = peak NDYI (Sentinel-2 yellowness)**, fallback = peak EVI + cropping-specific offset. Grid values are von-Mises MLE integrated across sampled fields. | vs. RiceAtlas at 0.5°: bias **+3.93 d** transplanting, **−5.76 d** harvest; RMSE **27.62 d** transplanting, **28.32 d** harvest. Reported as 6 d and 15 d lower RMSE than MODIS-based RICA. Additional 40-site literature validation: bias 7.99/−9.07 d, RMSE 19.00/22.43 d. | Monsoon Asia, 2019–2020 |
| 10 | Onojeghuo et al. 2023 (smallholder Senegal) | Sentinel-1 + Sentinel-2 10 m | Sentinel-2 cloud probability **threshold 65 %**, plus QA + edge masks | Phenology-based NDVI signature, but the gate is the cloud probability filter rather than a VI floor | ResU-Net deep learning on stacked S1 + S2 features | DL learns the phenometric extraction implicitly; thresholds replaced by training data | Field-validated F1 on smallholder polygons | Senegal River valley |
| 11 | Mishra et al. 2024 (ACRS flood-damage rice, Nepal) | Sentinel-1 GRD + Sentinel-2, 10 m | S2 cloud filter > 50 %; QA60; daily median synthesis + 10-day max composite | **DVDI / mVCI**: relative to historical median NDVI at same DOY in same pixel — already a **peak/median-relative metric**, not an absolute cut | Median-of-medians historical NDVI baseline | Rule-based: SOS = rapid NDVI rise, peak = NDVI max, harvest = rapid NDVI decline; damage = drop relative to historical median | Inundation overlap vs. ground field reports | Southern Nepal flood 2020 |

---

## 3. Cross-paper observations

### 3.1 Where the field already does something peak-relative
- **Zhang 2003 / 2018** uses two **range-relative** rules — "35 % of annual range" and "0.7 × annual max" — to reject sub-amplitude wiggles. This is the closest existing analogue to the Paper 2 Gate 1. Difference: Zhang's rules operate on the **EVI value** axis (amplitude). Paper 2's rule operates on the **valid-pixel count** axis (sample density per 5-day DOY bin). The two are complementary, not duplicative.
- **Mishra 2024 (DVDI / mVCI)** uses NDVI relative to the **historical median at the same DOY in the same pixel**. This is peak-relative in time, not in pixel count. Again complementary.
- **Bouvet 2018** is **signature-based** (looks for the SAR VH minimum), so it is implicitly relative — but it sidesteps the pixel-count problem because SAR has no clouds.

### 3.2 Where every existing optical paper still uses absolute cuts
- Sakamoto's EVI ≥ 0.5 (heading) and ≥ 0.3 (harvest), LSWI offset rules — region-tuned for Japan/Mekong.
- Pan's NDVI < 0.1 floor — tuned for Czech winter wheat soil background.
- PhenoRice's blue-band atmospheric and LST ≥ 15 °C cuts — region-defensible but fixed.
- Yan & Roy's NDWI ≤ 0.05 zeroing — Landsat-specific.
- Onojeghuo's S-2 cloud probability > 65 % — defensible per scene but does not solve the **temporal sparsity** problem within a 5-day DOY bin.

### 3.3 The smallholder fragmentation problem (relevant to Odisha + West Bengal)
- **Onojeghuo 2023** explicitly calls out that smallholder fields under 0.5 ha violate MODIS 250 m pixel purity; their workaround was to drop MODIS and use S-2 10 m + S-1 10 m only with a deep-learning ResU-Net. This validates the v2 decision to demote MODIS to district-level Spearman ρ only (Tier 2 in Protocol_v1.md §3.4).
- **Zhao 2024 (MARC)** discusses the same MODIS-pixel-purity limitation of the RICA product (500 m sensor, small rice fields) but **does not** workaround MODIS — they use a 500 m MODIS-derived rice mask, aggregated to 0.5°, and sample ~20 paddy fields per grid cell to average out mis-classification. MARC's own product resolution is 0.5°, not pixel-level.
- **None of the reviewed papers reports a pixel-level RMSE** of MODIS phenometrics against an in-situ benchmark in a smallholder South-Asian setting — this is the precise gap Paper 2 protects against by not making that claim (H5 in Protocol_v1.md §2 restricts MODIS to district-level Spearman ρ).

### 3.4 Cyclone-period validity (relevant to Amphan 2020 pilot)
- Pal et al. 2021 / Bera et al. 2021 (cited in cyclone Amphan literature, not in this matrix): show Sentinel-2 cropland NDVI dropping from pre-event (14 May 2020) to post-event (3 Jun 2020) over **88.2 %** of the flooded area in West Bengal. Optical detection works only on cloud-free days, which is precisely the 11–13 day Amphan landfall window where optical fails.
- This is the **H4** test in the v2 pack: Sentinel-1 VH backscatter (Bouvet 2018 method, paper #7 above) should detect transplanting-date shifts even when Sentinel-2 cannot, in the ±14-day landfall window around Amphan (20 May 2020) for South 24 Parganas, North 24 Parganas, and Purba Medinipur.

---

## 4. The gap Paper 2 fills (one paragraph)

Existing optical workflows (Sakamoto 2005, Boschetti 2017, Pan 2015, Bolton 2020) all encode QC gates as **absolute thresholds on the vegetation index value** (EVI ≥ 0.3, NDVI < 0.1, etc.), tuned to one region. Zhang 2003 introduced amplitude-relative gates ("35 % of annual range") but on the EVI axis, not on pixel-count density. Smallholder studies (Onojeghuo 2023) drop to 10 m S-2 + S-1 to escape MODIS pixel-impurity but still inherit cloud sparsity in the monsoon. None of the reviewed papers defines a **non-parametric gate on the within-DOY-bin valid-pixel count, normalized to the district's local peak**. This is the contribution: a transferable, training-free rule that respects smallholder bimodality (via phenometric-aware r: 0.75 for SOS/transplanting, 0.50 for peak NDVI date / EOS) and is paired with a SAR sanity witness for cyclone-period cloud blindness (Bouvet 2018).

---

## 5. Mapping anchor papers → Paper 2 sections

| Anchor | Where it lives in the kickoff pack |
|---|---|
| Zhang 2003 (amplitude-relative gates) | §3.7 Gate 1 prior art; §3.6 hypotheses H1 baseline |
| Sakamoto 2005 (paddy-rice EVI thresholds) | §3.5 anchor for South Asian rice phenology; §3.8 Tier 1 RMSE expectation |
| Pan 2015 (winter wheat threshold tuning) | §3.7 counter-example for region-specific overfitting |
| Boschetti 2017 PhenoRice | §3.6 H2; §3.5 data sources alignment |
| Yan & Roy 2014 | §3.3 falsifiability — multi-statistic approach as alternative |
| Bolton 2020 HLS | §3.8 Tier 1 Landsat HLS pixel-level RMSE benchmark |
| Bouvet 2018 | §3.12 SAR sanity-check protocol (NEW in v2) |
| Singha 2019 | §3.12 cross-validation method; §3.6 transferability evidence |
| Zhao et al. 2024 MARC (ESSD gridded calendar) | Protocol_v1.md §3.4 benchmark product for H1a/H1b/H2a/H2b sub-claims |
| Onojeghuo 2023 (smallholder DL) | §3.10 falsifiability — DL-driven counterfactual |
| Mishra 2024 (DVDI flood damage) | §3.11 deviation-log analogue; §3.6 H4 cyclone disturbance signal |

---

## 6. Open questions to resolve in Week 2

1. **Phenometric-aware r values** — locked at 0.75 (SOS/transplanting) and 0.50 (peak NDVI / EOS) for the Amphan pilot. Will re-evaluate after Amphan run.
2. Should the **Z-score path of Pan 2015** be added as a parallel diagnostic, or is the peak-relative pixel-count rule sufficient? — defer to Week 3 once Amphan pilot output is in.
3. **Zhao et al. 2024 MARC's reported metrics** (bias +3.93 d transplanting / −5.76 d harvest, RMSE 27.62 d / 28.32 d, all vs RiceAtlas at 0.5°) are the benchmarks to beat for H1a/H1b/H2a/H2b. Locked in Protocol_v1.md §2.
4. For Bouvet 2018 SAR application, **VH or VV?** — Singha 2019 found VH more sensitive to rice growth; Bouvet originally used VV minimum. Adopt **VH primary, VV secondary** for the ±14 d Amphan window.

---

## 7. References (selected; full BibTeX in `manuscript/refs.bib`)

- Bolton, D.K., Gray, J.M., Melaas, E.K., et al. (2020). Continental-scale land surface phenology from harmonized Landsat and Sentinel-2 imagery. *Remote Sensing of Environment*, 240, 111685.
- Boschetti, M., Busetto, L., Manfron, G., et al. (2017). PhenoRice: A method for automatic extraction of spatio-temporal information on rice crops using satellite data time series. *Remote Sensing of Environment*, 194, 347–365.
- Bouvet, A., Le Toan, T., Lam-Dao, N., et al. (2018). Sentinel-1 InSAR coherence for early crop monitoring: applied to a rice paddy. *Remote Sensing of Environment*.
- Zhao, X., Nishina, K., Izumisawa, H., Masutomi, Y., Osako, S., Yamamoto, S. (2024). Monsoon Asia Rice Calendar (MARC): a gridded rice calendar in monsoon Asia based on Sentinel-1 and Sentinel-2 images. *Earth System Science Data*, 16, 3893–3921. https://doi.org/10.5194/essd-16-3893-2024
- Mishra, A., et al. (2024). Rice crop loss and damage estimation due to flood using optical and SAR remote sensing. *ACRS 2024 Proceedings*.
- Onojeghuo, A.O., Miao, Y., et al. (2023). Deep learning for smallholder paddy rice field mapping with Sentinel-1 and Sentinel-2. *Remote Sensing*, 15, 1517.
- Pan, Z., et al. (2015). Mapping crop phenology using NDVI time-series derived from MODIS data over Czech Republic. *International Journal of Applied Earth Observation and Geoinformation*.
- Sakamoto, T., Yokozawa, M., Toritani, H., et al. (2005). A crop phenology detection method using time-series MODIS data. *Remote Sensing of Environment*, 96, 366–374.
- Singha, M., Dong, J., Zhang, G., Xiao, X. (2019). High resolution paddy rice maps in cloud-prone Bangladesh and Northeast India using Sentinel-1 data. *Scientific Data*, 6, 26.
- Yan, L., & Roy, D.P. (2014). Automated crop field extraction from multi-temporal Web Enabled Landsat Data. *Remote Sensing of Environment*, 144, 42–64.
- Zhang, X., Friedl, M.A., Schaaf, C.B., et al. (2003). Monitoring vegetation phenology using MODIS. *Remote Sensing of Environment*, 84, 471–475.

---

## 8. Corrections history

- **2026-09-04 — misattribution of Zhao et al. 2024 MARC.** The v0.1 draft cited row 9 of the synthesis matrix as "Han et al. 2024 (mapping boro rice, ESS-Data)" and the reference list as "Han, J., Zhang, Z., Cao, J. et al. (2024)" with page range 3893–3911. This was a real paper mis-attributed to a non-existent first author "Han". The correct citation is Zhao, X., Nishina, K., Izumisawa, H., Masutomi, Y., Osako, S., Yamamoto, S. (2024), *Earth System Science Data*, 16, 3893–3921, https://doi.org/10.5194/essd-16-3893-2024. Corrected in row 9, §3.3, §4, §5 anchor table, §6 Q3, and the reference list.
- **2026-09-04 — mis-scoring of MARC as a QC workflow.** The v0.1 draft scored MARC row against the 6 QC dimensions used for pixel-level QC workflows (rows 1–8, 10–11). MARC is a 0.5° gridded product built by aggregating ~20 sampled paddy fields per grid cell within a 500 m MODIS-derived rice mask; its "gates" operate at a different scale. Row 9 is now labelled "[BENCHMARK PRODUCT — not a QC workflow]" and its cells describe how MARC was built rather than pretending it competes on QC dimensions. See the note directly above the synthesis matrix.
- **2026-09-04 — numeric errors in the v0.1 row 9 metrics.** The v0.1 draft reported "Bias 4 d transplanting / −6 d harvest vs. RiceAtlas; MAE −10/−15 d, RMSE −6/−15 d vs. RICA", conflating MARC's absolute RMSE with the *delta* between MARC and RICA (which is why an RMSE appeared with a negative sign, which is impossible). Corrected: bias +3.93 / −5.76 d, RMSE 27.62 / 28.32 d vs RiceAtlas at 0.5°; MARC's RMSE is reported as 6 d and 15 d **lower than** MODIS-based RICA.
- **2026-09-04 — false claim in §3.3.** The v0.1 draft claimed "Han 2024's workaround was to drop MODIS and go to S-2 10 m + S-1 10 m only". Zhao 2024 does not drop MODIS — they use a 500 m MODIS-derived rice mask. Fixed.

— End of LitGap_v0.1 —
