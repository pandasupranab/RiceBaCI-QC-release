# SUPERSEDED / NEVER REGISTERED / DO NOT USE AS CURRENT METHODS

This is a preserved planning draft. It was **never registered on OSF** and is
not evidence that any decision was prospective. Its Sentinel-2/HLS/MODIS design,
thresholds, hypotheses and file paths were superseded during execution. Current
methods and dated deviations are in `docs/Protocol_v1.md`,
`analysis/deviation_log.md` and `analysis/decisions_log.md`. Historical wording
below is retained for auditability only.

# Historical draft: “OSF Pre-Registration — Paper 2 (RiceBaCI-QC)”

**Title:** A peak-relative non-parametric quality-control framework for cyclone-impact rice phenometric extraction in smallholder coastal systems

**Version:** v0.2 — 15 June 2026
**Author:** S. Panda (sole author for now; co-author block pending)
**Companion documents:** `docs/LitGap_v0.1.md`, `osf/Paper2_Kickoff_Pack_v2.pdf`, `analysis/decisions_log.md`
**Pre-registration philosophy:** *every threshold, gate, and analysis decision below is fixed before any cyclone is analyzed. Deviations will be logged in `analysis/deviation_log.md` with rationale.*

---

## 1. Background and motivation

Paper 1 (RSASE, in revision, manuscript ID RSE-D-26-02588 transferred) established a difference-in-differences (DiD) framework for cyclone disturbance on rice phenology in Odisha (Fani 2019 and Bulbul 2019). It used **absolute pixel-count thresholds** (8.3 % and 12.5 %) to gate which 5-day DOY bins entered phenometric extraction. Those thresholds were tuned on Odisha and may not transfer to other coastal Indian states. Paper 2 addresses the transferability question directly by:

1. Replacing the absolute thresholds with a **peak-relative non-parametric rule**, with **phenometric-aware r-values** locked before any cyclone is analyzed (§3.3).
2. Introducing a **two-tier validation** that uses Landsat HLS for pixel-level accuracy (RMSE) and MODIS MOD13Q1 only for district-level coherence (Spearman ρ), explicitly avoiding the smallholder-fragmentation pitfall (§3.4).
3. Adding a **Sentinel-1 SAR sanity-check witness** (Bouvet et al. 2018 method) at each cyclone landfall window, so cloud-induced optical blindness does not silently propagate to the DiD estimates (§3.5).

The pilot cyclone is **Cyclone Amphan (20 May 2020, landfall near Bakkhali, West Bengal)** — chosen instead of Fani 2019 because Amphan's footprint over West Bengal allows immediate stress-testing of the framework in a state not used to tune any threshold. This is the strongest possible transferability test available to me in 2026 without new field instrumentation.

---

## 2. Hypotheses

**H1 (RETRACTED 2026-09-04).** Original draft language: "In smallholder coastal rice systems, the peak-relative gate (r-based, see §3.3) achieves transplanting-date RMSE ≤ Han et al. 2024's reported bias of 4 d (transplanting) and −6 d (harvest), benchmarked against the Bangladesh / monsoon-Asia gridded calendar." Retracted because (a) "Han et al. 2024" is a mis-attribution of Zhao et al. 2024 MARC (ESSD 16, 3893–3921), (b) the numbers 4 d / −6 d are MARC's *bias* values (actually +3.93 / −5.76), not RMSE (which is 27.62 / 28.32 d) — conflating them is the error this retraction corrects, (c) MARC is a 0.5° gridded product benchmarked against RiceAtlas, not the Bangladesh gridded calendar. Superseded by the H1a/H1b/H2a/H2b sub-claims in `docs/Protocol_v1.md` §2.

**H2** — Sentinel-2 10 m and Landsat HLS 30 m phenometric estimates, both passed through the peak-relative QC framework, agree at pixel level with RMSE ≤ 12 d on the SOS phenometric, in non-cyclone control years (2017, 2018, 2021, 2022) over the three pilot districts.

**H3** — In cyclone years, the post-event DiD coefficient on SOS shift remains robust to swapping the absolute Paper 1 thresholds (8.3 %, 12.5 %) for the peak-relative gates (r = 0.75 for SOS, r = 0.50 for peak NDVI / EOS). Robustness defined as |Δβ| ≤ 1.5 d.

**H4** *(SAR sanity)* — Sentinel-1 VH transplanting-date estimate (Bouvet 2018 method) and Sentinel-2 peak-relative transplanting-date estimate agree on the three districts closest to each cyclone landfall, within ±10 d median absolute deviation. Disagreement larger than this triggers re-inspection of the optical record in that district.

**H5** *(MODIS coherence only)* — At district level only, Sentinel-2 and MODIS MOD13Q1 phenometric medians correlate at Spearman ρ ≥ 0.70 in control years. MODIS pixel-level RMSE is explicitly **not** reported because smallholder fragmentation (mean field size < 0.5 ha in coastal Odisha and West Bengal) violates MOD13Q1 250 m pixel purity.

---

## 3. Methods — locked before any analysis

### 3.1 Study area and pilot cyclone

- **Pilot cyclone:** Cyclone Amphan, landfall 20 May 2020, 14:30 IST, near Bakkhali, West Bengal.
- **Treatment districts (3):** South 24 Parganas, North 24 Parganas, Purba Medinipur (West Bengal). Selected because they sustained 88.2 % cropland flooding per Bera et al. 2021, *J. Environ. Manage.*
- **Control districts (3):** Bardhaman, Hooghly, Nadia (West Bengal), interior districts < 200 km from landfall but outside the Amphan footprint.
- **Control years (4):** 2017, 2018, 2021, 2022.
- **Treatment year (1):** 2020.
- **Kharif rice season window:** DOY 152–304 (1 June – 31 October).

### 3.2 Data sources

| Tier | Sensor | Product | Resolution | Role | QA gate |
|---|---|---|---|---|---|
| **Primary** | Sentinel-2 MSI L2A | `COPERNICUS/S2_SR_HARMONIZED` | 10 m, 5-day | Phenometric extraction | SCL keep classes {4, 5, 6, 7, 11}; cloud-probability < 30 % via `s2cloudless`; edge mask 1500 m |
| **Tier 1 validation** | Landsat HLS L30 + S30 | `NASA/HLS/HLSL30/v002`, `NASA/HLS/HLSS30/v002` | 30 m, ~3-day combined | Pixel-level RMSE benchmark (H2) | Fmask classes 0 only; same cloud-prob filter as S-2 |
| **Tier 2 coherence** | MODIS MOD13Q1 | `MODIS/061/MOD13Q1` | 250 m, 16-day | District-level Spearman ρ only (H5) | Pixel reliability ≤ 1 (good or marginal) |
| **SAR sanity (H4)** | Sentinel-1 GRD IW | `COPERNICUS/S1_GRD` | 10 m, 6-day | Transplanting-date witness ±14 d of landfall | Refined Lee 3×3 speckle, terrain-corrected, dB-scale; VH primary, VV secondary |
| **Field reference** | *To be catalogued* | Field reference sources for H1 (all three states — West Bengal, Odisha, coastal Andhra Pradesh) are to be catalogued in `docs/field_reference_sources.md` before H1 is claimed for any state. Historical draft language claiming WB block-wise paddy reports (2017–2022) and ICAR-NRRI Cuttack RTI records was retracted 2026-09-04 as neither dataset was actually collected. | — | Ground reference for H1 sub-claims | See `docs/field_reference_sources.md` (pending). |

### 3.3 Gate 1 — peak-relative non-parametric rule (the headline contribution)

**Rule.** For each district × season × phenometric:

1. Group all valid Sentinel-2 pixel-day observations within the season window (DOY 152–304) into 5-day DOY bins (31 bins total).
2. Compute *N(b)* = count of valid pixels in bin *b*, for each district.
3. Identify *N_peak* = max(*N(b)*) across all 31 bins in that district × season × phenometric.
4. Admit bin *b* to phenometric extraction **iff** *N(b)* ≤ r × *N_peak* OR *b* is the peak bin itself. (Bins above the threshold may indicate over-sampling artifacts and are excluded.)

**Phenometric-aware r values — locked.**

| Phenometric | r | Reasoning |
|---|---|---|
| SOS / transplanting | **0.75** | Smallholder bimodal planting waves can legitimately reach 60–70 % of the peak bin; tighter values reject real signal |
| Peak NDVI date | **0.50** | Sharply unimodal in a single district-season; tighter rejection guards against cloud-driven artifacts that mimic the peak |
| EOS / harvest | **0.50** | Unimodal; same reasoning as peak NDVI |

These r-values are **frozen** for the Amphan pilot. Post-pilot, they may be re-evaluated in a registered amendment before extension to the remaining five cyclones (Fani 2019, Bulbul 2019, Yaas 2021, Asani 2022, Mocha 2023).

### 3.4 Gate 2 — phenometric quality bounds (carried from Paper 1)

| Phenometric | Lower bound (DOY) | Upper bound (DOY) | NDVI / EVI amplitude requirement |
|---|---|---|---|
| SOS (transplanting) | 160 | 210 | NDVI rise ≥ 0.20 over 30 d |
| Peak NDVI date | 220 | 280 | Peak NDVI ≥ 0.55 |
| EOS (harvest) | 270 | 310 | NDVI decline ≥ 0.20 over 30 d |

Pixels whose extracted phenometric falls outside these bounds are flagged and excluded from the panel.

### 3.5 SAR sanity-check protocol (§3.12 of kickoff pack v2)

- **Method:** Bouvet et al. 2018 Sentinel-1 transplanting-date detection.
- **Scope:** Three districts closest to Amphan landfall (South 24 Parganas, North 24 Parganas, Purba Medinipur), in the ±14-day window centered on 20 May 2020.
- **Workflow:** Build VV + VH backscatter time series in IW GRD 5-day median composites for the 60-day window preceding the cyclone. Detect transplanting date as the local minimum of VH (primary) and VV (secondary cross-check) in the pre-monsoon → monsoon transition.
- **Decision rule (H4):** If |SAR transplanting date − Sentinel-2 peak-relative transplanting date| ≤ 10 d median absolute deviation per district, optical estimate is accepted. If > 10 d, the optical record in that district for that season is flagged in `analysis/sar_disagreement_log.md` and inspected manually before entering the DiD.
- **Output:** `qc/sar_tp_by_district.csv` (district, year, sar_tp_doy, sar_tp_mad, s2_tp_doy, agreement_flag).

### 3.6 Two-tier validation analyses (§3.8 of kickoff pack v2)

| Tier | Comparison | Metric | Test |
|---|---|---|---|
| **Tier 1 — primary accuracy** | Sentinel-2 10 m vs. Landsat HLS 30 m, same pixel-day after resampling to 30 m | Pixel-level RMSE in days | H2 |
| **Tier 2 — regional coherence** | Sentinel-2 district-median vs. MODIS MOD13Q1 district-median | Spearman ρ at district level | H5 |

**Explicit non-claim:** Sentinel-2 vs. MODIS pixel-level RMSE is not reported because of mean field size < 0.5 ha in coastal Odisha and West Bengal violating MOD13Q1 250 m pixel purity. This is stated in the methods, the limitations, and the response-to-reviewer template (`manuscript/anticipated_critiques.md`).

### 3.7 Difference-in-differences specification

For each phenometric *Y* (SOS, peak NDVI date, EOS) and district × year *(i, t)*:

\[
Y_{it} = \alpha_i + \gamma_t + \beta \cdot (\text{Treated}_i \times \text{Post}_t) + \varepsilon_{it}
\]

- Treated = {South 24 Parganas, North 24 Parganas, Purba Medinipur} = 1, else 0.
- Post = year 2020 = 1, else 0.
- Standard errors clustered at district level; **wild-cluster bootstrap** with 9 999 replications (Roodman et al. 2019, `boottest`) reported because there are only 6 districts.
- Pre-trends test: event-study coefficients on years 2017–2019 vs. 2020–2022 must satisfy joint *F*-test *p* > 0.10 to claim parallel trends.

### 3.8 Falsifiability checks

| Test | What it does | Pre-registered pass criterion |
|---|---|---|
| Placebo cyclone year | Re-run DiD with treatment year set to 2018 (no cyclone) | β not statistically distinguishable from 0 at p > 0.10 |
| Placebo treatment districts | Re-run DiD swapping treatment for control districts | β not distinguishable from 0 at p > 0.10 |
| r-value sensitivity | Re-run the full pipeline at r = 0.70, 0.75, 0.80 for SOS/transplanting | β changes by ≤ 1.5 d across the three r values |
| SAR-witness alignment | H4 above | Median |Δ| ≤ 10 d on all three landfall districts |

### 3.9 Deviation log

Any deviation from this pre-registration will be recorded in `analysis/deviation_log.md` with date, deviation, rationale, and an updated estimate of how the deviation affects each headline coefficient.

---

## 4. Outputs (Mendeley Data v2 + Zenodo)

- `data/balanced_panel_2017_2022.csv` — district × year × phenometric × pixel-count panel.
- `data/sar_tp_by_district.csv` — H4 sanity-check outputs.
- `data/tier1_hls_rmse.csv` — H2 Landsat HLS pixel-level RMSE.
- `data/tier2_modis_spearman.csv` — H5 district-level coherence.
- `figs/fig1_study_area.pdf`, `figs/fig2_qc_distributions.pdf`, `figs/fig3_did_coefplot.pdf`, `figs/fig4_event_study.pdf`, `figs/fig5_qc_framework.pdf`, `figs/fig6_district_sos_panel.pdf`, `figs/fig7_parallel_trends.pdf`, `figs/figS1_cyclone_climatology.pdf`, `figs/figS2_sar_witness_agreement.pdf`.
- `analysis/run_all.sh` — full reproducibility harness.

---

## 5. Author and conflicts

**RETRACTED 2026-09-04.** The historical draft text of this section claimed "Sole author: S. Panda (PhD candidate, ICAR-NRRI / Utkal University, Bhubaneswar). No conflicts of interest. Funding: ICAR-NRRI institutional fellowship." That affiliation and funding claim was unverified and is incorrect. It is superseded by the author block in `docs/Protocol_v1.md` §0. This study received no specific grant from any funding agency in the public, commercial, or not-for-profit sectors (matching the funding declaration of Paper 1). No conflicts of interest.

— End of OSF_PreReg_v0.2 —
