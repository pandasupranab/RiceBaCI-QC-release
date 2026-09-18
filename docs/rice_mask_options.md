# Rice mask options for the RiceBaCI-QC multi-state panel

**Companion document to `docs/Protocol_v1.md`.**
**Current-status notice (2026-09-16):** the operative mask decision is the
2026-09-09 amendment in **§8**. Sections 1–7 are retained as the historical
record and are **not current instructions or current evidence**; where they
conflict with §8, §8 controls. For manuscript claims, also follow
`analysis/manuscript_source_of_truth_2026-09-16.md`.
**Authors:** Supranab Panda; Sarat Chandra Sahu — Center for Environment and Climate, Institute of Technical Education and Research, Siksha 'O' Anusandhan (Deemed to be) University, Bhubaneswar 751030, Odisha, India.

---

## 1. Purpose

Two things must be settled before any extraction script pulls a rice pixel: (a) which map defines "this pixel is rice", and (b) how that choice is disclosed in the manuscript. This document records both, per state, with the trade-offs stated. **Current correction:** the documentation identifies the declared mask configuration and the aggregate checks performed; it does not establish the identity of every selected pixel or reconstruct the masked raw exports without the archived inputs.

## 2. Requirements the mask has to meet

The rice mask must, in this order of priority:

1. **Cover the full 2019–2024 analysis window** (post-DEV-001 floor). Any product whose year coverage does not span the six-cyclone window (Fani 2019 → Remal 2024) is disqualified as the primary mask.
2. **Distinguish rice from other cropland** at ≤30 m resolution. A cropland-only mask (rice + wheat + pulses undifferentiated) is not admissible as primary because our DiD attributes signal changes to rice phenology.
3. **Be published, versioned, and citable.** No unpublished layers, no personal assets that cannot be redistributed, no preprint-only products.
4. **Cover all three states** — Odisha, West Bengal, and coastal Andhra Pradesh — with a single or documented per-state approach.
5. **Come with an accuracy statement** (producer's and user's accuracy) that we can cite in Limitations.

## 3. Options evaluated

### 3.1 IRRI RiceAtlas (v1.0)

- **Citation:** Laborte, A. G., Gutierrez, M. A., Balanza, J. G., Saito, K., Zwart, S. J., Boschetti, M., Murty, M. V. R., Villano, L., Aunario, J. K., Reinke, R., Koo, J., Hijmans, R. J., Nelson, A. (2017). "RiceAtlas, a spatial database of global rice calendars and production." *Scientific Data*, 4, 170074. https://doi.org/10.1038/sdata.2017.74
- **Repository DOI:** Harvard Dataverse 10.7910/DVN/JE6R2R
- **Format:** vector polygons keyed to sub-national administrative units, with rice season calendars (planting, harvesting month windows), area planted, and season type.
- **Year coverage:** static / climatological. Not tied to a specific acquisition year.
- **Strengths:** authoritative for South and South-East Asian rice, published in a Nature-family journal, widely cited, admin-level polygons align with GADM Level-2 for OD/WB/AP. Provides not only "is rice" but also the season timing, which we use for the kharif window definition (DOY 152–304, cross-referenced in §3.2 of Protocol_v1.md).
- **Weaknesses:** polygon-level, not pixel-level. Within a RiceAtlas polygon, non-rice pixels (roads, water, fallow, orchards) are not excluded. Requires a within-polygon cropland or NDVI-phenology filter to reach pixel-level rice.
- **Existing use in the repo:** WB primary mask is `users/supranab/RiceAtlas_WB` (a GEE asset hosting the RiceAtlas West Bengal polygons; see `RiceAtlas_WB.zip` in the session workspace). OD and AP-coastal are uploaded per state to the `durable-pulsar-486209-b5` Cloud project (see §5).

### 3.2 ESA WorldCereal 2021 temporarycrops (general cropland, not rice-differentiated)

- **Citation:** Van Tricht, K., Degerickx, J., Gilliams, S., Zanaga, D., Battude, M., Grosu, A., Brombacher, J., Pelgrum, H., Lesiv, M., Bayas, J. C. L., Fritz, S., Szantoi, Z., Buchhorn, M., Smets, B., Duerauer, M., Herold, M., Waldner, F., Defourny, P. (2023). "WorldCereal: a dynamic open-source system for global-scale, seasonal, and reproducible crop and irrigation mapping." *Earth System Science Data*, 15, 5491–5515. https://essd.copernicus.org/articles/15/5491/2023/
- **Product (corrected 2026-09-06):** ESA WorldCereal 2021 `temporarycrops` product from the v100 GEE ImageCollection `ESA/WorldCereal/2021/MODELS/v100`, 10 m, Sentinel-1 + Sentinel-2 + Landsat-8 machine learning, one calendar year (2021). This is a **general cropland / non-cropland binary classifier**, not a rice-differentiated product. The v100 collection contains only `temporarycrops`, `maize`, `wintercereals`, `springcereals`, and `irrigation` products (Van Tricht et al. 2023, §2.2 and §5.1). No rice product exists in v100. Earlier drafts of this document, of `Protocol_v1.md` §3.5, and of `gee/S2_QC_Ingest.js` v0.3 mischaracterized this asset as a "rice map"; that mischaracterization is corrected here and everywhere it appeared (see `analysis/decisions_log.md` 2026-09-06 entry).
- **Accuracy (reported by product, corrected 2026-09-06):** user's accuracy 88.5 %, producer's accuracy 92.1 %, **for the `temporarycrops` (general cropland) product globally**, per Van Tricht et al. 2023 abstract and §5.1. These figures do NOT apply to a rice class. Validation methodology and confidence intervals in the ESA validation report (https://esa-worldcereal.org/sites/worldcereal/files/VITO-WorldCereal-rapport-FINAL_0.pdf).
- **Year coverage:** 2021 only in the current public release. A rolling year is planned but not yet available for our full 2019–2024 window.
- **Strengths:** pixel-level 10 m general-cropland map, produced by an ESA-led consortium with a peer-reviewed methods paper and published validation. Independent of RiceAtlas (different sensor stack, different production pipeline, different training data).
- **Weaknesses:** (i) single-year (2021) — cannot serve as the primary mask across a 2019–2024 panel because cropland extents shift year to year. (ii) **General cropland, not rice** — a pixel classified as `temporarycrops` may be rice, wheat, maize, pulses, oilseeds, vegetables, or any other short-cycle crop. It cannot distinguish rice from other cropland within a mixed-agriculture district. This weakens (but does not eliminate) its diagnostic value as an independent sensitivity check against RiceAtlas rice polygons (see §5, corrected).

### 3.3 Rejected options (documented for completeness)

- **Song et al. rice map (2020) / Zhao et al. 10 m rice map (2025 preprint):** Song et al. covers 2016 only; Zhao et al. 2025 remains a preprint as of 2026-09-04 and does not carry a peer-reviewed accuracy validation for eastern India. Neither meets requirement 3 (published + versioned).
- **ESA WorldCover 2021 cropland class:** cropland ≠ rice. Fails requirement 2.
- **National land use / land cover products from ISRO Bhuvan:** Bhuvan LULC 1:50k tiles cover the domain but are not versioned to a single year within the analysis window in a way that we can cite as a peer-reviewed product; also the rice sub-class is derived from a different segmentation regime per tile release. Rejected on requirement 5.

## 4. Locked decision — the tiered approach

| State | Primary mask | Sensitivity mask | Rationale |
|---|---|---|---|
| **West Bengal** | RiceAtlas (existing `users/supranab/RiceAtlas_WB`) | WorldCereal 2021 `temporarycrops` (general cropland) | Preserves continuity with Paper 1 pilot; WorldCereal `temporarycrops` used only for the pixel-disagreement sensitivity flag (see §5 for the reinterpreted meaning of that flag). |
| **Odisha** | RiceAtlas (per-state polygons uploaded as `projects/durable-pulsar-486209-b5/assets/RiceAtlas_OD`) | WorldCereal 2021 `temporarycrops` (general cropland) | RiceAtlas is the only rice-differentiated option that spans 2019–2024. |
| **Coastal Andhra Pradesh** (coastal districts per `coastal_districts_gadm41.csv`) | RiceAtlas (per-state polygons uploaded as `projects/durable-pulsar-486209-b5/assets/RiceAtlas_AP_coastal`) | WorldCereal 2021 `temporarycrops` (general cropland) | Same rationale as Odisha. |

**In one line:** RiceAtlas is the primary mask in all three states because it is the only rice-differentiated option that spans the full 2019–2024 window at admin level with a published citation. WorldCereal 2021 `temporarycrops` is the sensitivity mask because it is pixel-level and independent, with the caveat that it identifies general cropland rather than rice specifically (see §5 for what that caveat means for the disagreement metric).

## 5. Sensitivity procedure (the >20 % rule)

Purpose: quantify how much of our reported DiD signal depends on the specific rice-extent boundary we chose.

**Corrected 2026-09-06 — what this test actually tests.** The WorldCereal 2021 `temporarycrops` product (§3.2) is a general cropland / non-cropland classifier, not a rice-differentiated product. Therefore the `pixel_disagreement_pct` computed below tests **"is this pixel any cropland (per WorldCereal) versus is this pixel inside a rice polygon (per RiceAtlas)"**, NOT **"is this pixel rice (per WorldCereal) versus is this pixel rice (per RiceAtlas)"**. A high `pixel_disagreement_pct` in a mixed-agriculture district can therefore mean either (a) RiceAtlas polygon over-includes non-rice cropland such as wheat, pulses, or vegetables, OR (b) RiceAtlas polygon includes non-cropland (roads, water, fallow) that WorldCereal correctly excludes. The test cannot separate these two failure modes. It remains a useful, independent, pixel-level cross-check on RiceAtlas polygon fidelity to cropland extent — but it is not a cross-check on rice identity specifically. This weakens the diagnostic value of the flag but does not eliminate it: districts flagged as `high_cropland_disagreement` are still districts where the RiceAtlas polygon disagrees with an independent cropland dataset over more than one pixel in five, which is worth surfacing to the reviewer regardless.

(Analogy to an existing pattern in Protocol §3.3: the MODIS pixel-purity threshold used in Paper 1 tests whether a 500 m MODIS pixel is dominated by rice, not whether it is pure rice. The same substrate-honest framing applies here: the test measures what its inputs can measure, not what we might wish it measured.)

Procedure, run once per district × cyclone × phenometric:

1. Compute the phenometric extraction and DiD coefficient using the **primary mask** (RiceAtlas).
2. Repeat the extraction, restricting to the intersection of RiceAtlas AND WorldCereal 2021 `temporarycrops` pixels within the same district × season.
3. Compute **`pixel_disagreement_pct`** for that unit:
   `pixel_disagreement_pct = 100 * (pixels_in_RiceAtlas_only + pixels_in_WorldCereal_temporarycrops_only) / pixels_in_union`
   using the WorldCereal 2021 `temporarycrops` layer resampled to the S-2 10 m grid and clipped to the RiceAtlas polygon.
4. If `pixel_disagreement_pct > 20 %` for a district × cyclone unit, that unit gets a **`mask_flag = "high_cropland_disagreement"`** in the results table. (Flag name updated 2026-09-06 to reflect that this measures cropland-vs-rice-polygon disagreement, not rice-vs-rice disagreement.)
5. Report **both** DiD coefficients (primary-mask and intersection-mask) side by side for every flagged unit in the manuscript's supplement table `Table_SX_MaskSensitivity.csv`, along with a footnote reminding the reader that the intersection is with a general-cropland classifier and not with an independent rice product.
6. If more than 30 % of district × cyclone units are flagged for a given cyclone, that cyclone's headline DiD claim is downgraded from "supported by pixel-level analysis" to "supported at admin level; pixel-level cropland-extent disagreement warrants caution" in the discussion.

**What the manuscript body must state, verbatim (corrected 2026-09-06):** "Rice mask choices are documented in `docs/rice_mask_options.md`. Both the primary-mask (RiceAtlas rice polygons) and the intersection-mask (RiceAtlas ∩ WorldCereal 2021 `temporarycrops`, a general-cropland classifier) DiD coefficients are reported before any coefficient is discussed in the results. The intersection-mask sensitivity test measures disagreement between RiceAtlas rice polygons and an independent cropland extent, not disagreement between two rice products; no v100 WorldCereal rice product exists."

## 6. Provenance of the masks

- **RiceAtlas v1.0.** Public. Harvard Dataverse DOI 10.7910/DVN/JE6R2R. Per-state polygons uploaded as GEE assets, referenced from `gee/S2_QC_Ingest.js` and `gee/HLS_QC_Ingest.js`:
  - West Bengal: `users/supranab/RiceAtlas_WB` (legacy Paper 1 upload in the `supranab` user-asset namespace, retained; not re-uploaded).
  - Odisha: `projects/durable-pulsar-486209-b5/assets/RiceAtlas_OD` (Paper 2 upload in the `durable-pulsar-486209-b5` Cloud project).
  - Coastal Andhra Pradesh: `projects/durable-pulsar-486209-b5/assets/RiceAtlas_AP_coastal` (Paper 2 upload in the `durable-pulsar-486209-b5` Cloud project).
  Provenance line in every extraction script: `RICE_MASK_SOURCE = 'IRRI RiceAtlas v1.0 (Laborte et al. 2017), Harvard Dataverse DOI 10.7910/DVN/JE6R2R'`.
- **ESA WorldCereal 2021 temporarycrops.** Public. ESSD paper cited above. GEE ImageCollection: `ESA/WorldCereal/2021/MODELS/v100`, filtered on the image property `product == 'temporarycrops'` (the collection has no rice product; v100 products are `temporarycrops`, `maize`, `wintercereals`, `springcereals`, `irrigation`). Provenance line: `CROPLAND_SENSITIVITY_MASK = 'ESA WorldCereal 2021 temporarycrops (general cropland, not rice-differentiated; Van Tricht et al. 2023, ESSD, 15, 5491–5515)'`.

### 6.1 RiceAtlas → GADM crosswalk (Step 1 reconciliation, 2026-09-04)

The 28-district coastal roster in `docs/coastal_districts_gadm41.csv` uses GADM 4.1 district spellings. The RiceAtlas SUB_REGION field uses IRRI's transliteration and, in one case, historical state naming. The per-CSV-district crosswalk is committed as `docs/coastal_districts_crosswalk.csv` for provenance. Reconciliation rules applied:

- `REGION == 'Orissa'` in RiceAtlas is the same state as GADM `'Odisha'`.
- SUB_REGION `'East Midnapore'` / `'West Midnapore'` in RiceAtlas map to GADM `'Purba Medinipur'` / `'Pashchim Medinipur'`.
- SUB_REGION `'Vishakhapatnam'` in RiceAtlas is the transliteration variant of GADM `'Visakhapatnam'`.
- SUB_REGION `'Jagatsinghpur'` and `'Jajpur'` in RiceAtlas are the transliteration variants of GADM `'Jagatsinghapur'` and `'Jajapur'`.

After these mappings, 27 of the 28 CSV districts have a one-to-one RiceAtlas polygon. The exception is **Kolkata (West Bengal)**, which RiceAtlas does not include — Kolkata is a fully urban municipal-corporation district with approximately zero rice cropland, so no source polygon exists to import. Kolkata is therefore excluded from the effective GEE-run district roster consumed by `gee/S2_QC_Ingest.js`. It is **not** removed from `docs/coastal_districts_gadm41.csv`; that CSV remains the honest coast-buffer roster (100 km buffer, all three states, Kolkata retained), and the exclusion is enforced at the CONFIG step rather than by editing the roster upstream.

The effective per-state coverage feeding the QC extraction is:

| State | CSV districts | Effective (GEE run) | Reason for difference |
|---|---:|---:|---|
| Andhra Pradesh (coastal) | 9 | 9 | — |
| Odisha | 12 | 12 | — |
| West Bengal | 7 | 6 | Kolkata excluded (no RiceAtlas polygon) |
| **Total** | **28** | **27** | |

### 6.2 Area-calculation method for provenance areas

Where per-district area is reported (in `docs/coastal_districts_crosswalk.csv` and the Step 1 commit report), the number is a **planar area computed on features reprojected to EPSG:7755 (India LCC, Kalianpur 1937)**, divided by 10⁶ for km². It is not geodesic and it is not the `Shape_Area` field baked into the RiceAtlas DBF (that field is in decimal degrees squared and is meaningless as an area).

An independent geodesic recheck using pyproj `Geod(ellps='WGS84').geometry_area_perimeter` on all 21 features (12 OD + 9 AP-coastal) gives areas that are systematically **1.2%–3.7% larger** than the EPSG:7755 planar values, mean 2.9%. The gap is a real projection distortion, not an error in either computation; it does not compound over district counts. Users should treat the planar-EPSG:7755 areas as a sanity-check number ("nothing empty, nothing absurdly small") — they are not authoritative agricultural-statistics areas. For any downstream use that needs true areas, recompute geodesic values from the shapefile geometries directly.

## 7. What this document does not cover

- The Sentinel-2 pixel-level cloud/edge/QC pipeline (Protocol_v1.md §3).
- Field reference sources for H1 (to be catalogued in `docs/field_reference_sources.md`; see Protocol_v1.md §6).
- The coastal district inclusion rule (Protocol_v1.md §1.3; district list produced by `gadm/build_coastal_districts.py` → `coastal_districts_gadm41.csv`).

---

*End of rice_mask_options v1.*

---

## 8. Revision of the §4 locked decision (2026-09-09)

**Status:** the tiered decision locked in §4 on 2026-09-04 is superseded. §§1–7 are left as written; this section records what changed, the evidence, and the correction to §4's stated rationale. Nothing above is deleted.

### 8.1 What was wrong with the locked decision

§4 made IRRI RiceAtlas the primary mask in all three states on the ground that it is "the only rice-differentiated option that spans the full 2019–2024 window at admin level with a published citation."

That sentence conflates two senses of *rice-differentiated*. RiceAtlas differentiates rice at the **administrative-unit** level: it records which units grow rice, their season calendars and their planted area. It does not differentiate rice from other land **at pixel scale**. §3.1 of this document says so directly — "polygon-level, not pixel-level. Within a RiceAtlas polygon, non-rice pixels (roads, water, fallow, orchards) are not excluded. Requires a within-polygon cropland or NDVI-phenology filter to reach pixel-level rice."

§2 requirement 2 of this document demands discrimination "at ≤30 m resolution" and states that a mask which cannot do so "is not admissible as primary". The locked configuration therefore did not meet this document's own admission criteria, and the within-polygon filter §3.1 identifies as necessary was never implemented: `loadRiceAtlasMask30m` in `gee/S2_QC_Ingest.js` sets a constant on the polygon and rasterises it, so every pixel inside a district passed the mask.

**Measured consequence (2026-09-09).** Kharif rice covers between **0.9%** and **61.3%** of the roster districts, mean **29.8%** (`docs/chen_rice_2018_per_district.csv`). Candidate cohort `cohort_v1`, drawn uniformly from the polygon, therefore placed approximately **7,578 of its 10,800 pixels on land that is not Kharif rice**. That cohort is retired (Protocol §3.6). No phenometrics were reported from it.

### 8.2 Correction to §3.3's rejected-options list

§3.3 rejected "Zhao et al. 10 m rice map (2025 preprint)" on requirement 3, because it was a preprint without peer-reviewed accuracy validation for eastern India. That rejection stands and is unchanged.

The layer adopted below is **not** that product. It is Chen et al. (2024), a different paper by different authors, published in *Remote Sensing* on 28 August 2024 — a year before this document's §4 decision was taken — and it was simply absent from the options evaluated in §§3.1–3.3. This is a gap in the original evaluation, not a reversal of a rejection.

### 8.3 New primary mask

**RiceAtlas polygon ∩ Chen et al. (2024) Kharif rice, 2018 epoch.**

- Chen, X., Shen, R., Pan, B., Peng, Q., Zhang, X., Fu, Y., Yuan, W. (2024). "A High-Resolution Distribution Dataset of Paddy Rice in India Based on Satellite Data." *Remote Sensing* 16(17), 3180. https://doi.org/10.3390/rs16173180
- Data: https://doi.org/10.6084/m9.figshare.24228619 — GeoTIFF, WGS 84, 10 m, three seasons (autumn / winter / summer) × three epochs (2018, 2020, 2022), 23 Indian states covering 98% of national rice production.
- Method: SAR-based rice index over Sentinel-1 VH backscatter, keyed to the transplanting flood signature, with Sentinel-2 imagery.
- Reported accuracy: overall 84.40%, producer's 82.31%, user's 84.72%; per-state R² 0.53–0.95.

**Against §2's requirements:** (1) covers all analysis seasons as one temporally fixed layer, as RiceAtlas and WorldCereal also do; it is **not** called pre-treatment because Titli falls inside the 2018 epoch, as stated below; (2) **satisfied** — rice discriminated from other cropland at 10 m, which the previous configuration could not do; (3) satisfied — peer-reviewed, versioned, citable, with a repository DOI; (4) satisfied — all three states; (5) satisfied — accuracy statement available for Limitations.

**Season selection.** The product separates autumn (pre-Kharif), winter (Kharif) and summer (Rabi) rice by harvest timing. The paper defines winter rice as planted June–July and harvested November–December, about 84% of Indian rice cultivation — which matches this study's own Gate 2 windows (SOS DOY 155–240, EOS DOY 280–380). The **winter (Kharif)** layer is used. Selecting a season-specific layer is a strengthening over a generic rice mask: it excludes Rabi and pre-Kharif fields that would otherwise contaminate a Kharif phenology panel.

**Epoch selection.** The **2018** epoch is used. It predates every named cyclone in Protocol §1.1 except Titli (11 October 2018). This reduces, but does not eliminate, post-treatment selection risk: Titli falls inside the map's seasonal epoch, and the classifier's complete insensitivity to that event is not established. The 2020 and 2022 epochs are used only as a stability check and never in the selection rule. The 2018 choice is therefore a risk-reduction decision, not proof that selected extent is independent of every study event.

**Purity threshold.** The 10 m layer is aggregated to the 30 m analysis grid as the fraction of 10 m rice pixels per 30 m cell (`reduceResolution`, mean), and a cell is admitted at fraction ≥ **0.5** (majority rice). A threshold of 0.8 is the pre-declared purity sensitivity. Implemented as `loadKharifRiceMask30m` with `CONFIG.ricePurityMin`.

### 8.4 Aggregate plausibility check over this roster

The layer was tallied district by district against GADM v4.1 Level-2 boundaries for all 27 then-roster districts (`docs/chen_rice_2018_per_district.csv`, 2026-09-09). Its aggregate pattern is broadly consistent with several expected regional cropping systems:

- **West Bengal** — all six districts 35–61% Kharif, 1–3% autumn, **0% summer**: the aman-dominant, no-boro pattern of the coastal districts, which lack the irrigation command that boro requires.
- **Godavari–Krishna delta** — double-cropped, e.g. West Godavari 15.5% Kharif and 21.0% Rabi, East Godavari 15.4% and 11.0%.
- **Nellore** — inverted, 1.3% Kharif against 20.0% Rabi, matching that district administration's report that 80% of sown area is Rabi.

These aggregate correspondences are a plausibility check, not validation of individual 30 m pixels and not a replacement for the product's published accuracy assessment. The manuscript may report the check and the two flagged districts, but must not call it independent validation.

**Flagged, not corrected.** Two districts look low against expectation and are reported in Limitations: **Puri** at 13.8% Kharif is low for a Mahanadi delta district even after allowing for Chilika Lake (~1,000 km² of the 3,385 km² polygon), and **Prakasam** is near zero in all three seasons. Possible under-detection in delta transition zones.

### 8.5 Sensitivity mask

ESA WorldCereal 2021 `temporarycrops` is retained in its sensitivity role, and §3.2's 2026-09-06 correction stands unchanged: the v100 collection has no rice product, so the disagreement metric compares "any cropland" against the primary mask. Re-checked 2026-09-09 — the Earth Engine catalogue entry remains v100, and WorldCereal v2 provides on-demand custom crop-type mapping rather than a ready global rice layer, so nothing about that correction changes.

### 8.6 Consequential changes elsewhere

- Protocol §3.5 — mask definition replaced.
- Protocol §1.3 — minimum-Kharif-rice criterion added; roster 27 → 25 (Nellore 1.3%, Prakasam 0.9% excluded).
- Protocol §3.6 — cohort v1 retired, cohort v2 drawn from the new mask.
- `gee/S2_QC_Ingest.js` — `loadKharifRiceMask30m` added; `CONFIG.riceLayerAssetPath`, `CONFIG.ricePurityMin`; cohort id `cohort_v2`.
- §2 requirement 1 of this document reads "2019–2024"; the analysis window is now 2017–2025 (Protocol §1.1, §1.2). The requirement is otherwise unchanged in substance — one temporally fixed layer spans the full window — and the date range there should be read as superseded by Protocol §1.1. The layer is not called pre-treatment because Titli falls inside its 2018 epoch (§8.3).
