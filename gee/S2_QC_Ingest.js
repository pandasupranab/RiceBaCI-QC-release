/**
 * ============================================================================
 * gee/S2_QC_Ingest.js
 * ----------------------------------------------------------------------------
 * Paper 2 (RiceBaCI-QC) — Sentinel-2 L2A ingest, cloud-masked VI generation,
 * 5-day Kharif composites, FULL-GRID rice-polygon pixel histograms,
 * exported in 25 × 25 km spatial sub-tiles per (district, year).
 *
 * VERSION : v0.6.1 (08 Sep 2026 — cohort-asset geometry fix. §9c now
 *           rebuilds each cohort point's geometry from its own committed
 *           lon/lat properties at load time, instead of trusting whatever
 *           geometry the Earth Engine table-upload wizard attached to the
 *           CSV. Supersedes v0.6.0 (candidate-cohort export path).
 * AUTHORS : Supranab Panda (corresponding) — Center for Environment and
 *           Climate, Institute of Technical Education and Research,
 *           Siksha 'O' Anusandhan (Deemed to be) University,
 *           Bhubaneswar 751030, Odisha, India.
 *           <pandasupranab@gmail.com>
 *           Sarat Chandra Sahu — same affiliation (Director, CEC).
 *
 * CHANGES FROM v0.6.0 (cohort-asset geometry fix — Part 2 Step 3b, cont'd):
 *   • ROOT CAUSE. Uploading docs/candidate_cohort_v1.csv to Earth Engine as
 *     a table asset cannot satisfy both halves compositesToTable() needs at
 *     once. Tested both ways on 08 Sep 2026:
 *       - Upload with NO X/Y column mapping: all 6 properties survive
 *         (state, district, tile_id, cell_id, lon, lat), but every feature's
 *         geometry comes back empty (MultiPoint, 0 vertices) — reduceRegions
 *         in compositesToTable() then has no location to sample.
 *       - Upload WITH X/Y = lon/lat: geometry becomes a real Point, but the
 *         wizard consumes lon and lat into that geometry and drops them as
 *         properties — compositesToTable()'s trailing
 *         .select([...,'lon','lat',...], null, false) would then fail on
 *         every one of the 189 real-export tasks (property not found).
 *     Neither upload path alone is usable against the committed script.
 *   • FIX. §9c now loads the cohort asset (uploaded plain, NO X/Y mapping —
 *     the first form above, so all 6 properties survive) and immediately
 *     rebuilds each feature's geometry from its own lon/lat properties:
 *         .map(function (f) {
 *           return f.setGeometry(
 *             ee.Geometry.Point([ee.Number(f.get('lon')), ee.Number(f.get('lat'))]));
 *         })
 *     This gives reduceRegions a valid sample location built exactly from
 *     the committed coordinates (no Earth-Engine-ingestion precision drift,
 *     since it is not passed through the upload wizard's own geometry
 *     builder), while lon/lat remain intact as properties for
 *     compositesToTable()'s .select(). CONFIG.cohortAssetPath is unchanged;
 *     only the re-upload method and the load-time code change.
 *   • Caught before any of the 189 real-export tasks ran, by inspecting
 *     ee.FeatureCollection(CONFIG.cohortAssetPath).first() in the Code
 *     Editor console after each of the two upload attempts above — neither
 *     printed exactly what compositesToTable() needs (a real Point AND
 *     lon/lat properties) until this fix was added.
 *   • CONFIG.enableRealExports remains false.
 *
 * CHANGES FROM v0.5.1 (candidate cohort — Part 2 Step 3b):
 *   • ROOT CAUSE. buildCroplandGrid() rasterised the RiceAtlas polygon to a
 *     CONSTANT-valued mask and then called reduceToVectors(geometryType:
 *     'centroid'). Vectorising a constant region returns its connected
 *     components, so a solid rice mask collapses to ONE centroid per tile.
 *     Measured 08 Sep 2026 on Bhadrak tile01 in the Code Editor:
 *         cells in one tile:        1
 *         rice pixels in that tile: 774,673
 *     Every exported row for that tile would therefore have been a single
 *     arbitrary 30 m pixel (Reducer.first() at that centroid), giving ~11
 *     "pixels" for Bhadrak and ~570 for the whole 27-district study, in
 *     place of the pixel-level panel Protocol §3.6/§3.8 specify. Nothing
 *     had been extracted under this path (CONFIG.enableRealExports was
 *     never true), so no data is affected.
 *   • FIX. §9c now reads a fixed candidate cohort (CONFIG.cohortAssetPath)
 *     and exports one CSV per (district, season) over those points —
 *     189 tasks instead of ~4,000 per-tile-year tasks. The cohort is drawn
 *     ONCE by §9d (stratifiedSample, CONFIG.cohortSeed, N =
 *     CONFIG.cohortPointsPerDistrict), exported, committed to the repo as
 *     docs/candidate_cohort_v1.csv, and re-uploaded as an Earth Engine
 *     table asset so the extraction reads a committed input rather than
 *     re-drawing. This mirrors Paper 1's fixed candidate cohort
 *     (RSASE-D-26-02830: 210–453 pixels per district, static across years).
 *   • buildCroplandGrid() is RETIRED but retained below with a banner, so
 *     the defect above stays legible in the file it occurred in.
 *   • 13-column export schema UNCHANGED. tile_id now carries the cohort id
 *     (CONFIG.cohortId) rather than a 25 km sub-tile label — see Protocol
 *     §3.6. buildDistrictTiles() is still used by the §9b dry pass.
 *   • CONFIG.enableRealExports remains false.
 *
 * CHANGES FROM v0.5.0 (window correction):
 *   • CONFIG.seasonStartDOY 152 -> 150 and CONFIG.seasonEndDOY 304 -> 425,
 *     matching the submitted Paper 1's adopted 60-day-extension window
 *     (Protocol v1 §1.4, corrected 07 Sep 2026). buildSeasonalComposites
 *     and the per-year season dates already compute everything as day
 *     offsets from 1 January, so DOY > 365 needs no code change; the
 *     season now yields 55 five-day bins (bin starts 150 … 420) instead of
 *     31, and doy_bin_start / doy_bin_end values above 365 denote dates in
 *     the following calendar year. Dekadal aggregation for curve fitting
 *     is done downstream in Python (Protocol §3 lead-in), not here.
 *   • No logic change. CONFIG.enableRealExports remains false.
 *
 * CHANGES FROM v0.4.9 (Step 3):
 *   • §§4-8 restored verbatim from the actual v0.3 source (buildMaskedS2,
 *     addVIs, buildSeasonalComposites, buildCroplandGrid, compositesToTable),
 *     re-verified line-by-line against the committed v0.3 blob (git show
 *     ddc6474^) rather than retyped from memory. Only parameter names
 *     changed (croplandMask -> riceMask) to match v0.4's vocabulary; no
 *     logic changed in buildMaskedS2, addVIs, buildSeasonalComposites, or
 *     compositesToTable.
 *   • buildCroplandGrid: reduceToVectors' labelProperty renamed 'cropland'
 *     -> 'riceatlas_polygon' for naming consistency with the rest of v0.4.
 *     NOTE — this is cosmetic only, not a functional bug fix: labelProperty
 *     just names the output attribute GEE assigns to each reduced region;
 *     it does not have to match the input image's band name, and the very
 *     next line in this function (.select(['cell_id','lon','lat'], null,
 *     false)) drops that attribute entirely before the FeatureCollection is
 *     returned. The v0.3 code with the mismatched label ran correctly.
 *     Earlier commit messages describing this as a ".get('cropland')" bug
 *     to fix were imprecise — there is no .get('cropland') call anywhere in
 *     this function's v0.3 source.
 *   • §9c real export loop: v0.3's per-(district, tile, year) MAIN loop is
 *     restored using the v0.4 27-district architecture (districtRecs,
 *     per-state loadRiceAtlasMask30m) instead of v0.3's single-state
 *     CONFIG.districts array. NOT_FOUND districts (matchCount == 0) are
 *     skipped with a loud print rather than crashing on empty geometry.
 *   • Deliberate scope decision: CONFIG.reduceMaxPixels (5e7) + bestEffort
 *     — added in v0.4.8 to keep the dry-pass pixel-COUNTING sanity check
 *     (buildDryPassFeature's raPx/wcPx scalar sums) from timing out — is
 *     NOT applied to the real extraction path (buildCroplandGrid's
 *     reduceToVectors, or buildDistrictTiles' reduceRegions). Both keep
 *     v0.3's original maxPixels: 1e10 with no bestEffort, so the real
 *     export enumerates the FULL 30 m rice grid with no auto-coarsening,
 *     preserving the "no statistical subsampling" commitment in this
 *     file's ARCHITECTURE section. Silently inheriting the dry-pass's
 *     coarsening tolerance into the actual scientific extraction would
 *     have changed the analysis's spatial resolution without anyone
 *     deciding that on purpose — flagged here so it is a visible, on-
 *     the-record choice rather than an accident of code reuse.
 *   • Cost warning: per analysis/decisions_log.md (2026-09-06), North 24
 *     Parganas and South 24 Parganas cost 13-18x more EECU-seconds than
 *     districts of comparable or larger pixel count (Sundarbans coastline
 *     vector-geometry complexity, not raster pixel volume). §9c prints an
 *     explicit warning before dispatching either district's tasks so this
 *     is not a silent surprise at run time.
 *
 * CHANGES FROM v0.3:
 *   • Scope: 6 WB pilot districts -> 27 coastal districts across three states
 *     (WB 6 + OD 12 + AP-coastal 9). Kolkata is excluded (no RiceAtlas
 *     polygon; documented in docs/coastal_districts_crosswalk.csv).
 *   • Asset architecture: districtAssetPath + croplandMaskAssetPath collapsed
 *     into per-state riceAtlasAssetPath (used for BOTH district geometry AND
 *     the rasterized primary rice mask). Second global asset
 *     worldCerealAssetPath is the pixel-level sensitivity mask, per
 *     docs/rice_mask_options.md §5.
 *   • Sensitivity mask CORRECTED (2026-09-06): the v100 WorldCereal
 *     ImageCollection has no rice product; the sensitivity mask is the
 *     'temporarycrops' product (general cropland / non-cropland classifier,
 *     NOT rice-differentiated). Van Tricht et al. 2023, ESSD 15, 5491–5515,
 *     §2.2 + §5.1; GEE Data Catalog entry for the v100 asset. Full
 *     rationale and impact on the pixel_disagreement_pct sensitivity test:
 *     analysis/decisions_log.md 2026-09-06 entry; interpretation of the
 *     disagreement metric: docs/rice_mask_options.md §5 (corrected).
 *   • Two-mask dry-pass table: BOTH pixel counts (RiceAtlas rice polygons,
 *     WorldCereal 2021 temporarycrops general cropland) are reported per
 *     district, enabling the pixel_disagreement_pct calculation required
 *     by §5. Sensitivity mask is resampled to the S-2 10 m grid (NOT the
 *     30 m scaleMeters used for phenology extraction) — the two scales are
 *     kept strictly separate in loadWorldCerealTemporaryCropsMask10m().
 *   • CRS: EPSG:32645 (UTM 45N, WB-only) replaced by EPSG:7755 (India TM),
 *     valid across all three states.
 *   • Filter field split: WB uses SUB_REGION with WB_NAME_MAP for the two
 *     Midnapore districts (GADM canonical -> RiceAtlas transliteration:
 *     'Purba Medinipur' -> 'East Midnapore', 'Pashchim Medinipur' ->
 *     'West Midnapore'), because the WB legacy asset lacks a GADM_NAME
 *     column. OD and AP-coastal use GADM_NAME directly (the assets carry
 *     the GADM 4.1 canonical spelling as a first-class column) — no name
 *     map needed for those states. Full crosswalk in
 *     docs/coastal_districts_crosswalk.csv.
 *   • loadDistrictGeom() carries a server-side matchCount and a null-safe
 *     geometry so downstream code cannot crash on a zero-match district;
 *     the loud client-side '[DISTRICT NOT FOUND]' print is a SEPARATE
 *     per-district check inside §9b MAIN (one .getInfo() per district),
 *     because loadDistrictGeom() runs server-side and cannot itself print
 *     conditionally at the client.
 *   • Dry-pass discipline: Export.table.toDrive is guarded by
 *     CONFIG.enableRealExports (default false). MAIN prints a loud
 *     'v0.4 DRY-PASS ONLY' banner up front so a user running the script
 *     cannot miss it. Script prints a 27-row per-district table only.
 *     The §9c real-export branch is a DISCLOSED EMPTY STUB pending
 *     restoration of §§4-8 (buildMaskedS2, addVIs, buildSeasonalComposites,
 *     buildCroplandGrid, compositesToTable) plus Step 3 sign-off; flipping
 *     the flag right now will THROW immediately rather than silently
 *     dispatch nothing, so premature re-enable fails loudly.
 *   • ee.data.getAsset() sanity check BEFORE MAIN (§0c, parse-time):
 *     confirms all three riceAtlasAssetPath values and the
 *     worldCerealAssetPath resolve before any tiling or dry-pass work
 *     starts. Deliberately relabeled out of §9 MAIN because it runs at
 *     module load, not as a MAIN subsection.
 *
 * CHANGES FROM v0.2 (carried forward):
 *   • Systematic spatial sub-tiler. Deterministic 25 km fishnet per
 *     district in tileCrs, one Export.table.toDrive per (district, year,
 *     tile_id) once exports are re-enabled.
 *
 * CHANGES FROM v0.1 (carried forward):
 *   • GAUL 2015 fallback removed.
 *   • Cropland mask gate is required and applied BEFORE compositing, so
 *     valid_pixel_count counts only rice pixels.
 *   • No statistical subsampling. Full 30 m rice grid is extracted.
 *     Memory pressure handled with tileScale: 16 in reduceRegions.
 *
 * ARCHITECTURE (per docs/Protocol_v1.md §3 — supersedes retracted OSF pre-reg):
 *   1. Extraction only. No harmonic Fourier fits. No peak-relative Gate 1.
 *      No DiD. All of that runs locally in Python.
 *   2. Outputs — dry-pass (always runs, §9b): one 27-row table with columns
 *      (state, gadm_district, filter_field, filter_value, asset_path,
 *      status, ra_polygon_feature_count, tile_count,
 *      riceatlas_polygon_px_30m, worldcereal_temporarycrops_px_10m).
 *      status is "OK" or "NOT_FOUND"; NOT_FOUND rows carry 0 in the count
 *      columns via reduceRegion .get(name, 0) default-value argument (NOT
 *      .unmask(0), which does not exist on ee.Number and would throw at
 *      runtime).
 *   3. Outputs — real export (§9c, restored v0.5.0, gated behind
 *      CONFIG.enableRealExports, default false): per-cell x per-5-day-bin
 *      medians of NDVI, EVI2, LSWI plus per-bin valid-pixel counts. One
 *      CSV per (district, year, tile_id), dispatched as an
 *      Export.table.toDrive task requiring manual "Run" in the Tasks tab
 *      (or the earthengine.batch CLI) once queued.
 * ============================================================================
 */

// ============================================================================
// 0. CONFIG — every threshold, switch, and asset path lives here, nowhere else
// ============================================================================

var CONFIG = {

  // -- Study domain (v0.4: 27 coastal districts across three states) --------
  // Source: docs/coastal_districts_gadm41.csv, canonical GADM 4.1 spellings.
  // WB pilot roster (Bardhaman, Nadia, plus non-coastal districts) is
  // superseded. Kolkata is EXCLUDED — RiceAtlas has no polygon for it
  // (docs/coastal_districts_crosswalk.csv row 'EXCLUDED, 0, 0.0').
  districtsByState: {
    'West Bengal': [
      'South 24 Parganas',
      'North 24 Parganas',
      'Purba Medinipur',
      'Haora',
      'Hugli',
      'Pashchim Medinipur'
    ],
    'Odisha': [
      'Baleshwar',
      'Puri',
      'Jagatsinghapur',
      'Kendrapara',
      'Bhadrak',
      'Khordha',
      'Ganjam',
      'Gajapati',
      'Jajapur',
      'Cuttack',
      'Nayagarh',
      'Mayurbhanj'
    ],
    'Andhra Pradesh': [
      'Srikakulam',
      'East Godavari',
      'Nellore',
      'Vizianagaram',
      'Visakhapatnam',
      'West Godavari',
      'Krishna',
      'Guntur',
      'Prakasam'
    ]
  },
  country: 'India',
  // Control years 2017 & 2018 DROPPED: global S2 L2A
  // (COPERNICUS/S2_SR_HARMONIZED) does not exist before 2018-12-18.
  // See docs/Protocol_v1.md §3 and analysis/deviation_log.md (2026-06-15).
  years: [2019, 2020, 2021, 2022, 2023, 2024, 2025],  // Protocol §1.1: S2 seasons 2019–2025 (2025 closes Feb 2026)

  // -- Compositing window (docs/Protocol_v1.md §1.4; corrected 07 Sep 2026) --
  seasonStartDOY: 150,                              // 30 May (Paper 1 lower endpoint; Protocol §1.4)
  seasonEndDOY: 425,                                // ~1 Mar next year (Paper 1 60-day window; Protocol §1.4). Bins = 55.
  binWidthDays: 5,                                  // 55 bins per season over DOY 150–425 (Protocol §1.4)

  // -- Sentinel-2 cloud QC (docs/Protocol_v1.md §3.6) -----------------------
  s2Collection: 'COPERNICUS/S2_SR_HARMONIZED',
  s2CloudCollection: 'COPERNICUS/S2_CLOUD_PROBABILITY',
  cloudProbMax: 30,
  sclKeepClasses: [4, 5, 6, 7, 11],
  edgeMaskMeters: 1500,

  // -- REQUIRED asset routing (docs/rice_mask_options.md §6) ----------------
  // Primary rice mask + district geometry: RiceAtlas polygons, per state.
  // Both roles served by ONE asset per state — the FeatureCollection is
  // filtered (by SUB_REGION for WB, by GADM_NAME for OD/AP), and rasterized
  // in-script via .reduceToImage() for the 30 m rice-polygon pixel gate.
  //
  // WB: legacy Paper 1 upload in the 'supranab' user-asset namespace, retained.
  //     The WB asset has only SUB_REGION (no GADM_NAME column).
  // OD & AP-coastal: Paper 2 uploads in the 'durable-pulsar-486209-b5' Cloud project.
  //     Both assets carry GADM_NAME as a first-class column, so no name map needed.
  riceAtlasAssetPath: {
    'West Bengal':    'users/supranab/RiceAtlas_WB',
    'Odisha':         'projects/durable-pulsar-486209-b5/assets/RiceAtlas_OD',
    'Andhra Pradesh': 'projects/durable-pulsar-486209-b5/assets/RiceAtlas_AP_coastal'
  },
  // Sensitivity mask: ESA WorldCereal 2021 temporarycrops product, 10 m native grid.
  // CORRECTED 2026-09-06 — the v100 collection has NO rice product. This is a
  // general cropland / non-cropland classifier, not a rice-differentiated product.
  // See analysis/decisions_log.md 2026-09-06 entry and docs/rice_mask_options.md
  // §3.2, §5 (both corrected). The 'temporarycrops' filter below is the actual
  // asset-catalog filter that pulls the right image from the ImageCollection.
  worldCerealAssetPath:      'ESA/WorldCereal/2021/MODELS/v100',
  worldCerealProductFilter:  'temporarycrops',    // v100 products: temporarycrops,
                                                  // maize, wintercereals,
                                                  // springcereals, irrigation.
                                                  // NO rice product exists.

  // -- Filter-field routing per state ---------------------------------------
  // WB filters on SUB_REGION (only field on legacy asset) with WB_NAME_MAP
  // for the two Midnapore districts. OD and AP-coastal filter on GADM_NAME
  // directly (both assets have GADM_NAME as a first-class column) — no name
  // maps needed. Full crosswalk: docs/coastal_districts_crosswalk.csv.
  filterField: {
    'West Bengal':    'SUB_REGION',
    'Odisha':         'GADM_NAME',
    'Andhra Pradesh': 'GADM_NAME'
  },
  WB_NAME_MAP: {
    'Purba Medinipur':    'East Midnapore',
    'Pashchim Medinipur': 'West Midnapore'
  },

  // -- Spatial sub-tiler (v0.4 CRS generalized) -----------------------------
  // 25 km tiles. District spans vary widely: Jagatsinghapur (~1600 km²) is
  // one of the smallest and will yield 1-3 tiles; East Godavari
  // (~10500 km²) is one of the largest and will yield 15-20+. WB pilot's
  // "~4-20 tiles per district" claim was pilot-specific and no longer holds.
  tileSizeMeters: 25000,
  tileCrs: 'EPSG:7755',                             // India TM, valid all-India

  // -- Two-scale discipline (docs/rice_mask_options.md §5) ------------------
  // scaleMeters (30 m) is used for phenology extraction and the primary-
  // mask (RiceAtlas rice polygons) pixel gate. sensitivityScaleMeters (10 m)
  // is used ONLY for the WorldCereal 2021 temporarycrops pixel_disagreement
  // calculation, where the sensitivity raster must sit on Sentinel-2's
  // native 10 m grid clipped to the RiceAtlas polygon. Do NOT collapse
  // these two scales into one.
  scaleMeters: 30,
  sensitivityScaleMeters: 10,

  // -- Output ---------------------------------------------------------------
  driveFolder: 'RiceBaCI-QC_S2_exports',
  exportPrefix: 'S2_QC_',

  // -- Candidate cohort (docs/Protocol_v1.md §3.6; added v0.6.0) -----------
  // The panel is a fixed, seeded, committed set of candidate pixels per
  // district — NOT every 30 m pixel (East Godavari alone holds 12.6 M) and
  // NOT one centroid per tile (the retired buildCroplandGrid defect; see the
  // CHANGES block at the top of this file). Paper 1 used 210–453 pixels per
  // district; 400 is that density, and inference is clustered on 27
  // districts, so pixels beyond a few hundred per district add compute
  // rather than power.
  cohortPointsPerDistrict: 400,
  cohortSeed: 42,                                   // any change = new cohort id + new decisions_log entry
  cohortId: 'cohort_v1',
  cohortExportPrefix: 'S2_COHORT_',
  // The cohort drawn by §9d on 2026-09-08, merged and committed as
  // docs/candidate_cohort_v1.csv (10,800 rows: 27 districts x 400), then
  // uploaded to Earth Engine UNCHANGED under this asset id (CSV ingest with
  // X = lon, Y = lat, EPSG:4326). §9c refuses to run while this is empty.
  // If the asset is uploaded under a different id, change this line — do
  // not re-draw the cohort.
  cohortAssetPath: 'projects/durable-pulsar-486209-b5/assets/RiceBaCI_cohort_v1',
  buildCohort: false,                               // true = run §9d cohort export only

  // -- Dry-pass gate (v0.4) -------------------------------------------------
  // Real Export.table.toDrive is GATED behind this flag in §9c MAIN until
  // the dry-pass table is reviewed. Flip this to true only after user
  // sign-off on the 27-row dry-pass output; no code needs to be uncommented.
  enableRealExports: false,

  // -- Memory tuning --------------------------------------------------------
  reduceTileScale: 16,
  // reduceMaxPixels: hard ceiling passed as maxPixels to reduceRegion()
  // calls in buildDryPassFeature(). Combined with bestEffort: true it
  // controls when GEE auto-coarsens the requested scale: if a request at
  // the nominal scale (30 m for raPx, 10 m for wcPx) would exceed this
  // pixel count, GEE bumps scale up until it fits, instead of throwing
  // 'Image.reduceRegion: Too many pixels'. Set to 5e7 so the very large
  // coastal districts (South 24 Parganas, East Godavari, etc.) auto-
  // coarsen instead of hitting compute-time / memory limits on the 10 m
  // WorldCereal read. Trades exact pixel precision for guaranteed
  // completion; the dry-pass table's pixel counts on the biggest
  // districts will therefore be approximate, not exact.
  reduceMaxPixels: 5e7,

  // -- Diagnostic export list (v0.4.9) --------------------------------------
  // Districts that failed 'Computation timed out' in every real dry-pass
  // run so far under interactive evaluation (3/3 across v0.4.7 and two
  // v0.4.8 tests), even after bestEffort + reduceMaxPixels (v0.4.8) fixed
  // the same failure for larger-pixel-count districts (Guntur, Prakasam).
  // Points to vector-geometry complexity (Sundarbans / Godavari delta /
  // Pulicat estuary coastlines) rather than pixel budget -- maxPixels/
  // bestEffort only governs raster pixel budget and had zero effect on
  // these four across two attempts. Routed through Export.table.toDrive()
  // instead, which gets a much longer wall-clock allowance than the
  // interactive Code Editor's per-print() evaluation.
  hardDistrictsForDiagnosticExport: [
    'South 24 Parganas',
    'North 24 Parganas',
    'East Godavari',
    'Nellore'
  ]
};

// ============================================================================
// 0b. HELPERS — SUB_REGION resolution and per-state routing
// ============================================================================

/**
 * Resolves a GADM canonical district name to the filter value used against the
 * state's RiceAtlas asset. WB uses SUB_REGION with WB_NAME_MAP for the two
 * Midnapore transliterations; OD and AP-coastal use GADM_NAME directly, so the
 * filter value IS the GADM canonical name. Full crosswalk:
 * docs/coastal_districts_crosswalk.csv
 */
function resolveFilterValue(state, gadmName) {
  if (state === 'West Bengal') {
    if (CONFIG.WB_NAME_MAP[gadmName]) { return CONFIG.WB_NAME_MAP[gadmName]; }
    return gadmName;                                          // fallback: identity
  }
  return gadmName;                                             // OD and AP: identity
}

/**
 * Flat client-side list of {state, gadmName, filterField, filterValue, assetPath}
 * for every (state, district) pair. Drives the MAIN loop and the dry-pass table.
 */
function enumerateDistricts() {
  var out = [];
  Object.keys(CONFIG.districtsByState).forEach(function (state) {
    var assetPath   = CONFIG.riceAtlasAssetPath[state];
    var filterField = CONFIG.filterField[state];
    CONFIG.districtsByState[state].forEach(function (gadmName) {
      out.push({
        state:       state,
        gadmName:    gadmName,
        filterField: filterField,
        filterValue: resolveFilterValue(state, gadmName),
        assetPath:   assetPath
      });
    });
  });
  return out;
}

// ============================================================================
// 1. DISTRICT GEOMETRY LOADER  (from RiceAtlas per-state FeatureCollection)
// ============================================================================

/**
 * Loads a single district's geometry from the state's RiceAtlas asset,
 * filtered on the state-appropriate field (SUB_REGION for WB, GADM_NAME for
 * OD and AP-coastal). Loudly flags districts that resolve to zero features
 * so a typo in CONFIG.districtsByState surfaces immediately rather than
 * causing silent null-geometry propagation into the dry-pass table.
 */
function loadDistrictGeom(rec) {
  var src = ee.FeatureCollection(rec.assetPath);
  var matches = src.filter(ee.Filter.eq(rec.filterField, rec.filterValue));
  var matchCount = matches.size();

  // Server-side conditional: if zero matches, print loudly and return an
  // empty geometry so the dry-pass row still gets a value (0 pixels,
  // 0 tiles) and the [DISTRICT NOT FOUND] print in the log points at the
  // exact CONFIG line to fix.
  var found = matchCount.gt(0);
  // Note: print() inside a server-side ee.Algorithms.If branch does NOT
  // fire client-side; we surface a client-side print via .getInfo() below
  // (invoked once per district by the dry-pass MAIN loop, before feature
  // collection assembly). See MAIN §9b for the loud-print pattern.

  var geom = ee.Algorithms.If(
    found,
    ee.Feature(matches.first()).geometry(),
    ee.Geometry.Rectangle([0, 0, 0.00001, 0.00001], null, false)  // degenerate 1 m^2 sentinel: valid GeoJSON, .bounds() safe, reduceRegion returns 0
  );
  return { geom: ee.Geometry(geom), matchCount: matchCount };
}

// ============================================================================
// 2. TWO-MASK LOADERS — RiceAtlas primary + WorldCereal sensitivity
// ============================================================================

/**
 * Primary rice mask: RiceAtlas polygon rasterized at 30 m in tileCrs.
 * A polygon inside the FeatureCollection becomes value 1; outside is masked.
 * This is a POLYGON-LEVEL mask, per RiceAtlas's documented limitation
 * (docs/rice_mask_options.md §3.1). Every pixel inside the polygon counts
 * as "in a rice-growing polygon" — non-rice pixels within the polygon
 * (roads, water, orchards, fallow) are NOT excluded here.
 */
function loadRiceAtlasMask30m(rec) {
  var fc = ee.FeatureCollection(rec.assetPath)
             .filter(ee.Filter.eq(rec.filterField, rec.filterValue));
  return fc.map(function (f) { return f.set('rice_polygon', 1); })
           .reduceToImage(['rice_polygon'], ee.Reducer.first())
           .rename('riceatlas_polygon')
           .selfMask();
}

/**
 * Sensitivity cropland mask: ESA WorldCereal 2021 'temporarycrops' product,
 * restricted to the RiceAtlas polygon and resampled to Sentinel-2's 10 m grid.
 * Used ONLY for the pixel_disagreement_pct calculation
 * (docs/rice_mask_options.md §5, corrected 2026-09-06), NOT for phenology
 * extraction. Kept at sensitivityScaleMeters (10 m), separate from
 * scaleMeters (30 m).
 *
 * IMPORTANT (corrected 2026-09-06): the v100 WorldCereal collection contains
 * NO rice product. This function pulls the 'temporarycrops' product, which is
 * a general cropland / non-cropland binary classifier (classification == 100
 * for cropland). Any pixel-level disagreement flagged in the dry-pass table
 * therefore reflects RiceAtlas-polygon vs. any-cropland disagreement, not
 * rice-vs-rice disagreement. See analysis/decisions_log.md 2026-09-06 and
 * docs/rice_mask_options.md §5.
 */
function loadWorldCerealTemporaryCropsMask10m(rec, districtGeom) {
  var col = ee.ImageCollection(CONFIG.worldCerealAssetPath)
              .filter(ee.Filter.eq('product', CONFIG.worldCerealProductFilter));
  // temporarycrops is a single-image product per AEZ; mosaic() over the AEZs
  // that intersect this district returns a single continuous raster.
  var cropland = col.select('classification').mosaic()
                     .eq(100).selfMask().rename('wc_temporarycrops');
  return cropland.clip(districtGeom)
                 .reproject({crs: CONFIG.tileCrs, scale: CONFIG.sensitivityScaleMeters});
}

// ============================================================================
// 3. SPATIAL SUB-TILER  (25 × 25 km fishnet, district-clipped, cropland-filtered)
// ============================================================================
// (unchanged from v0.3, only comment updated for tileCrs generalization)

/**
 * Builds a deterministic 25 km fishnet covering the district's bounding box
 * in tileCrs (EPSG:7755, India TM), intersects each cell with the district
 * geometry, and drops cells that contain zero rice pixels under the primary
 * (RiceAtlas) mask.
 *
 * Returns a FeatureCollection of tile polygons, each carrying:
 *   • tile_id  : zero-padded "tileNN" string (deterministic, row-major
 *                from SW corner of the bbox)
 *   • district : passed through
 */
function buildDistrictTiles(districtGeom, districtName, riceMask) {

  // NOTE (v0.4): riceMask is the PRIMARY mask — the RiceAtlas rice polygon
  // rasterized at 30 m (band name 'riceatlas_polygon', produced by
  // loadRiceAtlasMask30m). It is a rice-polygon mask, not a general-cropland
  // mask; the general-cropland (WorldCereal 2021 temporarycrops at 10 m) mask
  // is only queried in §9 MAIN for the dry-pass table's second pixel-count
  // column, never here.

  var bounds = districtGeom.bounds(1, CONFIG.tileCrs);
  var coords = ee.List(bounds.coordinates().get(0));

  // Rectangle corners in tileCrs (v0.4: EPSG:7755, India TM). The bounds
  // polygon is [SW, SE, NE, NW, SW] — we just need SW + NE.
  var sw = ee.List(coords.get(0));
  var ne = ee.List(coords.get(2));

  var xMin = ee.Number(sw.get(0));
  var yMin = ee.Number(sw.get(1));
  var xMax = ee.Number(ne.get(0));
  var yMax = ee.Number(ne.get(1));

  // Snap to multiples of tileSizeMeters so tile_ids are stable across runs
  // (and across districts that share an edge).
  var step = CONFIG.tileSizeMeters;
  xMin = xMin.divide(step).floor().multiply(step);
  yMin = yMin.divide(step).floor().multiply(step);
  xMax = xMax.divide(step).ceil().multiply(step);
  yMax = yMax.divide(step).ceil().multiply(step);

  var xs = ee.List.sequence(xMin, xMax.subtract(step), step);
  var ys = ee.List.sequence(yMin, yMax.subtract(step), step);

  // Cartesian product of (x, y) corners -> one rectangle per cell.
  var fishnet = xs.map(function (x) {
    return ys.map(function (y) {
      x = ee.Number(x);
      y = ee.Number(y);
      var rect = ee.Geometry.Rectangle(
        [x, y, x.add(step), y.add(step)],
        CONFIG.tileCrs,
        false                                       // do not geodesic-clamp
      );
      return ee.Feature(rect);
    });
  }).flatten();

  fishnet = ee.FeatureCollection(fishnet);

  // 1) intersect each tile with the district -> drop empties
  var intersected = fishnet
    .map(function (f) {
      var g = f.geometry(1, CONFIG.tileCrs).intersection(districtGeom, 1);
      return f.setGeometry(g).set('area_m2', g.area(1));
    })
    .filter(ee.Filter.gt('area_m2', 0));

  // 2) drop tiles that contain zero rice-polygon pixels (primary RiceAtlas mask)
  // Single batched reduceRegions() call over the whole `intersected`
  // collection, instead of one reduceRegion() per tile inside .map().
  // The per-tile pattern fires one aggregation per candidate tile per
  // district; folded into the outer 27-district MAIN loop this exceeded
  // GEE's concurrent-aggregation limit ("Too many concurrent
  // aggregations", caught 2026-09-06 running v0.4.2). reduceRegions()
  // is the canonical batched form -- one aggregation request per
  // district covering all its tiles, instead of one per tile.
  var withRiceRaw = riceMask.reduceRegions({
    collection: intersected,
    reducer: ee.Reducer.sum(),
    scale: CONFIG.scaleMeters,
    tileScale: CONFIG.reduceTileScale
  });
  var withRice = withRiceRaw
    .map(function (f) {
      // reduceRegions() (plural, batched) names its output column after
      // the reducer ('sum') for an unnamed reducer, NOT after the band
      // name the way reduceRegion() (singular) does -- confirmed via a
      // live diagnostic probe on Haora 2026-09-06 (propertyNames() came
      // back ["sum", "area_m2", "system:index"], no "riceatlas_polygon").
      // This was the actual root cause of tile_count: 0 on every single
      // district in the v0.4.6 run, not a genuine no-rice-tiles condition.
      return f.set('rice_px', ee.Number(f.toDictionary().get('sum', 0)));
    })
    .filter(ee.Filter.gt('rice_px', 0));

  // 3) Assign deterministic tile_ids. We use ee.FeatureCollection sorted by
  // (yMin, xMin) so SW->NE row-major. Convert index to "tileNN" client-side
  // via toList + size + map-with-index pattern.
  var sorted = withRice.sort('area_m2', false);   // largest first
  var size = sorted.size();
  // .toList(count) throws "Collection.toList: The value of 'count' must
  // be positive. Got: 0" if count is exactly 0 -- a real, legitimate case
  // for a district whose fishnet tiles all have zero rice-mask pixels
  // after filtering (caught 2026-09-06 on the v0.4.5 batched run: WB
  // districts in batch 1 and AP districts in batch 6 hit this). .max(1)
  // keeps the requested count positive without changing behavior when
  // size > 0; toList() only returns elements that actually exist, so an
  // empty `sorted` still correctly yields an empty list and tile_count
  // correctly reports 0 for that district instead of crashing the batch.
  var tileList = sorted.toList(size.max(1));

  var withIds = ee.FeatureCollection(
    ee.List.sequence(0, size.subtract(1)).map(function (i) {
      i = ee.Number(i);
      var f = ee.Feature(tileList.get(i));
      // tile_id format: "tile" + zero-padded 2-digit index
      var idStr = ee.String('tile').cat(
        ee.Number(i).add(1).format('%02d')
      );
      return f.set({
        'tile_id': idStr,
        'district': districtName
      });
    })
  );

  return withIds;
}

// ============================================================================
// 4. SENTINEL-2 CLOUD MASK + RICE MASK  (restored verbatim from v0.3;
//    param renamed croplandMask -> riceMask, no logic change)
// ============================================================================

function buildMaskedS2(roi, startDate, endDate, riceMask) {

  var s2 = ee.ImageCollection(CONFIG.s2Collection)
              .filterBounds(roi).filterDate(startDate, endDate);

  var s2c = ee.ImageCollection(CONFIG.s2CloudCollection)
              .filterBounds(roi).filterDate(startDate, endDate);

  var joined = ee.Join.saveFirst('cloud_mask').apply({
    primary: s2,
    secondary: s2c,
    condition: ee.Filter.equals({leftField: 'system:index', rightField: 'system:index'})
  });

  function maskOne(img) {
    img = ee.Image(img);
    var cloudProb = ee.Image(img.get('cloud_mask')).select('probability');
    var scl = img.select('SCL');

    var cloudOk = cloudProb.lt(CONFIG.cloudProbMax);
    var sclOk = scl.remap(CONFIG.sclKeepClasses,
                          ee.List.repeat(1, CONFIG.sclKeepClasses.length), 0);

    var validMask = cloudOk.and(sclOk);
    var edgeOk = validMask.focal_min({
      radius: CONFIG.edgeMaskMeters, units: 'meters'
    });

    return img.updateMask(validMask.and(edgeOk).and(riceMask))
              .copyProperties(img, ['system:time_start', 'system:index']);
  }

  return ee.ImageCollection(joined).map(maskOne);
}

// ============================================================================
// 5. VEGETATION INDICES  (restored verbatim from v0.3, no changes)
// ============================================================================

function addVIs(img) {
  var sr = img.select(['B4', 'B8', 'B11']).divide(10000);
  var nir = sr.select('B8');
  var red = sr.select('B4');
  var swir = sr.select('B11');

  var ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI');
  var evi2 = nir.subtract(red).multiply(2.5)
                 .divide(nir.add(red.multiply(2.4)).add(1)).rename('EVI2');
  var lswi = nir.subtract(swir).divide(nir.add(swir)).rename('LSWI');

  return img.addBands([ndvi, evi2, lswi])
            .copyProperties(img, ['system:time_start']);
}

// ============================================================================
// 6. 5-DAY MEDIAN COMPOSITES OVER KHARIF SEASON  (restored verbatim from
//    v0.3, no changes — including the 2026-06-15 dummy-schema armor)
// ============================================================================

function buildSeasonalComposites(maskedColl, year) {

  var binStarts = ee.List.sequence(CONFIG.seasonStartDOY,
                                   CONFIG.seasonEndDOY - CONFIG.binWidthDays + 1,
                                   CONFIG.binWidthDays);
  var yearStart = ee.Date.fromYMD(year, 1, 1);

  // -----------------------------------------------------------------
  // DUMMY-SCHEMA ARMOR (added 2026-06-15)
  // Pre-Dec-2018 S2 L2A is empty globally. An empty median() yields an
  // image with no bands, which crashes Export.table.toDrive with
  // "Image has no bands". We build a fully-masked dummy image carrying
  // the four expected band names and overlay any real composite onto it
  // using addBands(..., null, true). Empty bins/years now export as
  // masked rows instead of failing the entire task.
  // -----------------------------------------------------------------
  var dummy = ee.Image.constant([0, 0, 0, 0])
                .rename(['NDVI_med', 'EVI2_med', 'LSWI_med', 'valid_pixel_count'])
                .updateMask(ee.Image(0));   // fully masked

  var composites = binStarts.map(function (doyStart) {
    doyStart = ee.Number(doyStart);
    var binStart = yearStart.advance(doyStart.subtract(1), 'day');
    var binEnd = binStart.advance(CONFIG.binWidthDays, 'day');

    var bin = maskedColl.filterDate(binStart, binEnd);
    var validCount = bin.select('NDVI').count().rename('valid_pixel_count');
    var med = bin.select(['NDVI', 'EVI2', 'LSWI']).median()
                  .rename(['NDVI_med', 'EVI2_med', 'LSWI_med']);
    var composite = med.addBands(validCount);

    // Overlay real composite on dummy: dummy supplies band schema even when
    // 'composite' has zero bands (empty collection).
    var armored = dummy.addBands(composite, null, true);

    return armored.set({
      'year': year,
      'doy_bin_start': doyStart,
      'doy_bin_end': doyStart.add(CONFIG.binWidthDays - 1),
      'bin_index': binStarts.indexOf(doyStart)
    });
  });

  return ee.ImageCollection.fromImages(composites);
}

// ============================================================================
// 7. FULL 30 m RICE GRID — clipped to a SINGLE tile  (restored from v0.3;
//    param renamed croplandMask -> riceMask; labelProperty renamed
//    'cropland' -> 'riceatlas_polygon', cosmetic only — see CHANGES FROM
//    v0.4.9 at top of file for why this is not a functional bug fix)
// ============================================================================

/**
 * Returns the 30 m rice-mask cell centroids INSIDE the given tile geometry
 * (not the whole district). Memory budget per task drops by ~tileCount×.
 */
// ---------------------------------------------------------------------------
// RETIRED 08 Sep 2026 (v0.6.0) — DO NOT USE. Kept for the record.
// riceMask is a CONSTANT-valued raster (loadRiceAtlasMask30m paints the
// RiceAtlas polygon with 1 and selfMasks), so reduceToVectors() returns its
// connected components: ONE centroid for a solid rice region, not one per
// pixel. Measured on Bhadrak tile01, 08 Sep 2026: 1 cell against 774,673
// rice pixels. Replaced by the §9d candidate cohort. See the CHANGES block
// at the top of this file and analysis/decisions_log.md (2026-09-08).
// ---------------------------------------------------------------------------
function buildCroplandGrid_RETIRED(tileGeom, riceMask) {
  var clipped = riceMask.clip(tileGeom)
                         .reproject({crs: CONFIG.tileCrs, scale: CONFIG.scaleMeters});

  var vectors = clipped.reduceToVectors({
    geometry: tileGeom,
    crs: CONFIG.tileCrs,
    scale: CONFIG.scaleMeters,
    geometryType: 'centroid',
    eightConnected: false,
    labelProperty: 'riceatlas_polygon',
    maxPixels: 1e10,
    tileScale: CONFIG.reduceTileScale
  });

  return vectors.map(function (f) {
    var c = f.geometry().coordinates();
    return f.set({
      'cell_id': ee.Number(c.get(0)).format('%.6f')
                  .cat('_').cat(ee.Number(c.get(1)).format('%.6f')),
      'lon': c.get(0),
      'lat': c.get(1)
    }).select(['cell_id', 'lon', 'lat'], null, false);
  });
}

// ============================================================================
// 8. REDUCE COMPOSITE STACK -> TABLE ROWS  (tagged with tile_id)
//    (restored verbatim from v0.3, no changes)
// ============================================================================

function compositesToTable(compositeColl, gridFc, districtName, year, tileId) {

  var rows = compositeColl.map(function (img) {
    img = ee.Image(img);
    var sampled = img.reduceRegions({
      collection: gridFc,
      reducer: ee.Reducer.first(),
      scale: CONFIG.scaleMeters,
      tileScale: CONFIG.reduceTileScale
    });
    return sampled.map(function (f) {
      return f.set({
        'district': districtName,
        'year': year,
        'tile_id': tileId,
        'bin_index': img.get('bin_index'),
        'doy_bin_start': img.get('doy_bin_start'),
        'doy_bin_end': img.get('doy_bin_end')
      });
    });
  }).flatten();

  return rows.select(
    ['district', 'year', 'tile_id', 'cell_id', 'lon', 'lat',
     'bin_index', 'doy_bin_start', 'doy_bin_end',
     'NDVI_med', 'EVI2_med', 'LSWI_med', 'valid_pixel_count'],
    null, false
  );
}

// ============================================================================
// 0c. PARSE-TIME ASSET SANITY CHECK — all four asset paths
// ============================================================================
// Fails loudly at parse time if any RiceAtlas or WorldCereal asset is missing.
// Runs BEFORE §9 MAIN so a bad path aborts the script before any dry-pass work.
Object.keys(CONFIG.riceAtlasAssetPath).forEach(function (state) {
  var path = CONFIG.riceAtlasAssetPath[state];
  try {
    var info = ee.data.getAsset(path);
    print('[asset OK]', state, '->', path, '(' + info.type + ')');
  } catch (e) {
    print('[asset MISSING]', state, '->', path, '— aborting.');
    throw e;
  }
});
try {
  var wcInfo = ee.data.getAsset(CONFIG.worldCerealAssetPath);
  print('[asset OK] WorldCereal 2021 ->', CONFIG.worldCerealAssetPath,
        '(' + wcInfo.type + ')');
} catch (e) {
  print('[asset MISSING] WorldCereal 2021 ->', CONFIG.worldCerealAssetPath,
        '— aborting.');
  throw e;
}

// ============================================================================
// 9. MAIN — §9a-9b2 always run (27-row dry-pass table + 4 diagnostic
//    Export tasks). §9c (the full scientific export, restored in v0.5.0)
//    only runs when CONFIG.enableRealExports is true (default: false).
// ============================================================================

// ---- 9a. LOUD DRY-PASS BANNER --------------------------------------------
if (!CONFIG.enableRealExports) {
  print('===================================================================');
  print('===   v0.4 DRY-PASS ONLY  —  NO Export.table.toDrive DISPATCHED   ===');
  print('===================================================================');
  print('Script prints a 27-row per-district table only (RiceAtlas primary +');
  print('WorldCereal temporarycrops sensitivity mask, per-district pixel counts).');
  print('Real exports re-enable by setting CONFIG.enableRealExports = true.');
  print('');
  print('NOTE: 4 targeted diagnostic Export.table.toDrive tasks (South 24 ' +
        'Parganas, North 24 Parganas, East Godavari, Nellore) will be ' +
        'QUEUED (not run) further down in this script -- see §9b2. These ' +
        'require manual "Run" in the Tasks tab and are unrelated to the ' +
        'full 27-district scientific export still gated by ' +
        'CONFIG.enableRealExports in §9c.');
}

// ---- 9b. Enumerate 27 districts and build the dry-pass table --------------
var districtRecs = enumerateDistricts();
print('Total districts in v0.4 roster:', districtRecs.length,
      '(expected: 27 = WB 6 + OD 12 + AP 9)');

// Per-district loud [DISTRICT NOT FOUND] check (client-side, one .getInfo()
// per district = 27 round-trips, acceptable at this stage). Runs BEFORE the
// server-side FeatureCollection assembly so a typo in CONFIG.districtsByState
// surfaces at the top of the log rather than buried in feature properties.
districtRecs.forEach(function (rec) {
  var mc = ee.FeatureCollection(rec.assetPath)
              .filter(ee.Filter.eq(rec.filterField, rec.filterValue))
              .size()
              .getInfo();
  if (mc === 0) {
    print('[DISTRICT NOT FOUND] ' + rec.state + '/' + rec.gadmName +
          '  (filter: ' + rec.filterField + ' == "' + rec.filterValue + '"' +
          ', asset: ' + rec.assetPath + ')  — fix CONFIG.districtsByState or ' +
          'CONFIG.WB_NAME_MAP.');
  }
});

// Per-district feature construction, unchanged logic from v0.4.4 --
// extracted into a named function so MAIN can evaluate it in small
// batches instead of all 27 districts in one combined FeatureCollection.
function buildDryPassFeature(rec) {
  var loaded = loadDistrictGeom(rec);
  var geom   = loaded.geom;
  var raMask = loadRiceAtlasMask30m(rec);
  var wcMask = loadWorldCerealTemporaryCropsMask10m(rec, geom);

  // Tile count (primary-mask-filtered fishnet)
  var tiles = buildDistrictTiles(geom, rec.gadmName, raMask);
  var tileCount = tiles.size();

  // Primary-mask (RiceAtlas rice polygon) pixel count at 30 m.
  // maxPixels + bestEffort: reduceRegion() auto-coarsens the requested
  // scale when the pixel budget would exceed CONFIG.reduceMaxPixels
  // (5e7), instead of throwing 'Image.reduceRegion: Too many pixels' --
  // which on very large districts (South 24 Parganas, North 24 Parganas,
  // East Godavari, Nellore, Krishna, Guntur, Prakasam, all timed out on
  // the v0.4.7 real run 2026-09-06) surfaced as compute-graph timeouts.
  // Trades exact 30 m pixel precision for guaranteed completion on the
  // biggest districts; downstream reporting treats these as approximate.
  var raPx = raMask.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geom,
    scale: CONFIG.scaleMeters,               // 30 m
    maxPixels: CONFIG.reduceMaxPixels,
    tileScale: CONFIG.reduceTileScale,
    bestEffort: true
  }).get('riceatlas_polygon', 0);

  // Sensitivity-mask (WorldCereal 2021 temporarycrops) pixel count at 10 m
  // per docs/rice_mask_options.md §5 (corrected 2026-09-06).
  // maxPixels + bestEffort: same auto-coarsen contract as raPx above --
  // when 10 m evaluation over the whole district geometry would exceed
  // CONFIG.reduceMaxPixels (5e7), GEE bumps scale up until it fits
  // instead of throwing 'Too many pixels'. This is where the v0.4.7
  // timeouts most likely originated: a coastal district at 10 m is
  // ~9x more pixels than at 30 m, so the 10 m WorldCereal read is the
  // pixel-budget bottleneck for the biggest coastal districts.
  var wcPx = wcMask.reduceRegion({
    reducer: ee.Reducer.sum(),
    geometry: geom,
    scale: CONFIG.sensitivityScaleMeters,    // 10 m — DO NOT change to 30 m
    maxPixels: CONFIG.reduceMaxPixels,
    tileScale: CONFIG.reduceTileScale,
    bestEffort: true
  }).get('wc_temporarycrops', 0);

  // Per-district match status: "OK" if the RiceAtlas asset returned at least
  // one feature for this (filterField, filterValue) pair, "NOT_FOUND" if
  // .size() == 0. Computed server-side from the same matchCount already used
  // by loadDistrictGeom's found-flag, so no extra .getInfo() round-trip.
  // The [DISTRICT NOT FOUND] client-side print in §9b stays as the loud,
  // top-of-log signal; this column makes the same information machine-
  // readable in the exported dry-pass table.
  var status = ee.Algorithms.If(loaded.matchCount.gt(0), 'OK', 'NOT_FOUND');

  return ee.Feature(null, {
    state:                              rec.state,
    gadm_district:                      rec.gadmName,
    filter_field:                       rec.filterField,
    filter_value:                       rec.filterValue,
    asset_path:                         rec.assetPath,
    status:                             status,
    ra_polygon_feature_count:           loaded.matchCount,
    tile_count:                         tileCount,
    riceatlas_polygon_px_30m:           ee.Number(raPx),
    worldcereal_temporarycrops_px_10m:  ee.Number(wcPx)
  });
}

// Print the dry-pass table one district at a time rather than in one
// combined FeatureCollection.getInfo() call. Each district contributes
// at least 3 aggregation nodes (2 whole-district reduceRegion calls +
// 1 batched reduceRegions call inside buildDistrictTiles); realizing
// all 27 districts together (81 aggregation nodes) hit GEE's
// (undocumented) "Too many concurrent aggregations" limit at v0.4.4,
// and a first attempt at batches of 5 districts (est. 15 nodes/batch)
// still hit the same limit at v0.4.5 -- meaning reduceRegions() likely
// does not collapse to a single aggregation node the way v0.4.3 assumed.
// BATCH_SIZE = 1 (fully serialized) is the maximally conservative
// fallback: if a specific district STILL fails at this setting, that
// would mean a single district's own tile count (not cross-district
// bundling) is the real driver, and buildDistrictTiles() itself needs
// rethinking rather than further batch-size tuning.
var BATCH_SIZE = 1;
print('=== v0.4 dry-pass table (27 rows, printed one district at a time) ===');
for (var i = 0; i < districtRecs.length; i += BATCH_SIZE) {
  var batch = districtRecs.slice(i, i + BATCH_SIZE);
  var batchFeatures = ee.FeatureCollection(batch.map(buildDryPassFeature));
  print('--- rows ' + (i + 1) + '-' + Math.min(i + BATCH_SIZE, districtRecs.length) + ' ---');
  print(batchFeatures);
}

// ============================================================================
// 9b2. DIAGNOSTIC EXPORT -- districts that fail under interactive dry-pass eval
// ============================================================================
// See CONFIG.hardDistrictsForDiagnosticExport above for full rationale.
// NOTE: physically placed between §9b and §9c (hence "9b2") because it
// requires districtRecs from §9b and executes before §9c's gate check.
// Semantically an export, not a dry-pass calculation.

// Each district gets its OWN Export task -- bundling multiple districts
// into one combined FeatureCollection risks the same "Too many concurrent
// aggregations" failure that forced BATCH_SIZE=1 above, and there's no
// evidence Export.table.toDrive() is immune to that same graph-size limit
// even though it has a longer time budget than interactive print().
//
// To run: after this script executes, find these 4 tasks in the Tasks tab
// (top right of the Code Editor), click "Run" on each individually, wait
// for completion, then check CONFIG.driveFolder in Google Drive for the
// resulting CSVs (one row each).
CONFIG.hardDistrictsForDiagnosticExport.forEach(function (districtName) {
  var rec = districtRecs.filter(function (r) { return r.gadmName === districtName; })[0];
  if (!rec) {
    print('[DIAGNOSTIC EXPORT SKIPPED] ' + districtName + ' not found in districtRecs.');
    return;
  }
  var feature = buildDryPassFeature(rec);
  var fc = ee.FeatureCollection([feature]);
  Export.table.toDrive({
    collection: fc,
    description: 'v0_4_dry_pass_HARD_' + districtName.replace(/ /g, '_'),
    folder: CONFIG.driveFolder,
    fileFormat: 'CSV'
  });
});
print('4 diagnostic Export tasks queued for South 24 Parganas, North 24 ' +
      'Parganas, East Godavari, Nellore -- find them in the Tasks tab and ' +
      'click Run on each individually.');

// ---------------------------------------------------------------------------
// buildCohortForDistrict — the fixed candidate cohort (Protocol §3.6).
//
// stratifiedSample() over the selfMasked RiceAtlas raster draws
// CONFIG.cohortPointsPerDistrict points from the single mask class, at
// CONFIG.scaleMeters, with a fixed seed: deterministic, spatially spread
// over the district, and confined to rice-mask pixels. Fewer points come
// back only if the district holds fewer eligible pixels than requested;
// the actual count per district is recorded in the exported cohort CSV.
// ---------------------------------------------------------------------------
function buildCohortForDistrict(rec) {
  var geom = loadDistrictGeom(rec).geom;
  var mask = loadRiceAtlasMask30m(rec);

  var pts = mask.stratifiedSample({
    numPoints:  CONFIG.cohortPointsPerDistrict,
    classBand:  'riceatlas_polygon',
    region:     geom,
    scale:      CONFIG.scaleMeters,
    projection: CONFIG.tileCrs,
    seed:       CONFIG.cohortSeed,
    dropNulls:  true,
    tileScale:  CONFIG.reduceTileScale,
    geometries: true
  });

  return pts.map(function (f) {
    var c = f.geometry().coordinates();
    return ee.Feature(f.geometry(), {
      'state':    rec.state,
      'district': rec.gadmName,
      'tile_id':  CONFIG.cohortId,
      'cell_id':  ee.Number(c.get(0)).format('%.6f')
                    .cat('_').cat(ee.Number(c.get(1)).format('%.6f')),
      'lon':      c.get(0),
      'lat':      c.get(1)
    }).select(['state', 'district', 'tile_id', 'cell_id', 'lon', 'lat'],
              null, false);
  });
}

// ---- 9d. COHORT BUILD — one-time, gated by CONFIG.buildCohort -------------
// Run this ONCE, with CONFIG.buildCohort = true and enableRealExports =
// false. It queues 27 small Export tasks (one per district — separate
// tasks rather than one merged task because North and South 24 Parganas
// cost 13-18x their pixel count in EECU-seconds, see decisions_log
// 2026-09-06). Then:
//   1. download the 27 CSVs;
//   2. merge with python/merge_cohort_exports.py -> docs/candidate_cohort_v1.csv;
//   3. commit that file;
//   4. upload the same file to Earth Engine as a table asset;
//   5. set CONFIG.cohortAssetPath to the asset id and CONFIG.buildCohort = false.
// The committed CSV, not the seed, is the authoritative cohort: §9c reads
// the asset, so the panel does not depend on Earth Engine's RNG staying
// stable across releases.
if (CONFIG.buildCohort) {
  print('=================================================================');
  print('===   COHORT BUILD — dispatching ' + districtRecs.length +
        ' Export.table.toDrive tasks   ===');
  print('=================================================================');
  print('Target points per district:', CONFIG.cohortPointsPerDistrict,
        '| seed:', CONFIG.cohortSeed, '| cohort id:', CONFIG.cohortId);

  districtRecs.forEach(function (rec) {
    var safeName = rec.gadmName.replace(/[^A-Za-z0-9]+/g, '_');
    var description = CONFIG.cohortExportPrefix + CONFIG.cohortId + '_' + safeName;
    Export.table.toDrive({
      collection: buildCohortForDistrict(rec),
      description: description,
      folder: CONFIG.driveFolder,
      fileNamePrefix: description,
      fileFormat: 'CSV'
    });
    print('Queued cohort export:', description);
  });
  print('Merge the 27 CSVs with python/merge_cohort_exports.py, commit as ' +
        'docs/candidate_cohort_v1.csv, upload as an EE table asset, then set ' +
        'CONFIG.cohortAssetPath and CONFIG.buildCohort = false.');
}

// ---- 9c. REAL EXPORTS — cohort path (v0.6.1; geometry rebuilt at load) ---
// v0.3's per-(district, tile, year) export loop, re-implemented over the
// v0.4 27-district architecture. Runs ONLY when CONFIG.enableRealExports
// is true; the dry-pass table (§9b) and diagnostic exports (§9b2) above
// always run regardless, so this section recomputes each district's
// geometry/mask/tiles independently rather than reusing anything from
// §9b — extra one-time compute cost, in exchange for keeping this branch
// fully self-contained and not dependent on §9b's internal variables.
//
// Districts with zero RiceAtlas matches (matchCount == 0) are skipped with
// a loud print rather than crashing buildDistrictTiles on an empty/
// degenerate geometry. As of the 2026-09-06 dry-pass run all 27 districts
// resolved OK, so this is a defensive guard, not an expected path.
//
// Deliberately NOT using CONFIG.reduceMaxPixels / bestEffort here — see
// "CHANGES FROM v0.4.9 (Step 3)" at the top of this file. buildCroplandGrid
// and buildDistrictTiles keep v0.3's original maxPixels: 1e10 with no
// auto-coarsening, so the exported grid is the FULL 30 m rice mask, not an
// approximation calibrated for a scalar pixel-count sanity check.
if (CONFIG.enableRealExports) {

  if (!CONFIG.cohortAssetPath) {
    throw new Error(
      'CONFIG.cohortAssetPath is empty. Run \u00a79d first (CONFIG.buildCohort = ' +
      'true), merge and commit docs/candidate_cohort_v1.csv, upload it as an ' +
      'Earth Engine table asset, then set CONFIG.cohortAssetPath to that asset ' +
      'id. \u00a79c will not export against an un-committed cohort.');
  }

  // Load the committed cohort asset and rebuild each point's geometry from
  // its own lon/lat properties (v0.6.1 — see "CHANGES FROM v0.6.0" above).
  // The asset must be uploaded WITHOUT an X/Y column mapping so that lon
  // and lat survive as properties; this .map() supplies the geometry that
  // upload path leaves empty, using the exact committed coordinates rather
  // than whatever the upload wizard would have built.
  var cohort = ee.FeatureCollection(CONFIG.cohortAssetPath).map(function (f) {
    return f.setGeometry(
      ee.Geometry.Point([ee.Number(f.get('lon')), ee.Number(f.get('lat'))]));
  });

  print('===================================================================');
  print('===   REAL EXPORT PATH ENABLED — dispatching Export.table.toDrive  ===');
  print('===================================================================');
  print('Cohort asset:', CONFIG.cohortAssetPath);
  print('Cohort points (all districts):', cohort.size());
  print('Expected tasks:', districtRecs.length * CONFIG.years.length,
        '= ' + districtRecs.length + ' districts x ' + CONFIG.years.length + ' seasons');

  var realTaskIndex = 0;

  districtRecs.forEach(function (rec) {

    var loaded = loadDistrictGeom(rec);
    if (loaded.matchCount.getInfo() === 0) {
      print('[SKIPPED — NOT FOUND] ' + rec.state + '/' + rec.gadmName +
            ' has zero RiceAtlas matches; no export tasks queued for it.');
      return;
    }
    var geom   = loaded.geom;
    var raMask = loadRiceAtlasMask30m(rec);

    // Cohort points for this district, drawn once by §9d and committed.
    var pts = cohort.filter(ee.Filter.eq('district', rec.gadmName));

    CONFIG.years.forEach(function (year) {

      var seasonStart = ee.Date.fromYMD(year, 1, 1)
                          .advance(CONFIG.seasonStartDOY - 1, 'day');
      var seasonEnd = ee.Date.fromYMD(year, 1, 1)
                          .advance(CONFIG.seasonEndDOY, 'day');

      var maskedS2 = buildMaskedS2(geom, seasonStart, seasonEnd, raMask)
                        .map(addVIs);

      var composites = buildSeasonalComposites(maskedS2, year);
      var table = compositesToTable(composites, pts, rec.gadmName, year,
                                    CONFIG.cohortId);

      var safeName = rec.gadmName.replace(/[^A-Za-z0-9]+/g, '_');
      var description = CONFIG.exportPrefix + safeName + '_' + year;

      Export.table.toDrive({
        collection: table,
        description: description,
        folder: CONFIG.driveFolder,
        fileNamePrefix: description,
        fileFormat: 'CSV'
      });

      realTaskIndex += 1;
      print('[' + realTaskIndex + '] Queued export:', description);
    });
  });

  print('Total real-export tasks queued:', realTaskIndex);
  print('Outputs land in Drive folder:', CONFIG.driveFolder);
  print('Each task = 1 district-season: ' + CONFIG.cohortPointsPerDistrict +
        ' cohort points x 55 five-day bins ~= 22,000 rows.');
  print('REMINDER: Tasks tab — click Run on each, or use earthengine.batch CLI for bulk run.');
  print('REMINDER: North 24 Parganas and South 24 Parganas run noticeably ' +
        'slower than districts of similar size — see analysis/decisions_log.md (2026-09-06).');

} else {
  print('No real exports dispatched. Set CONFIG.enableRealExports = true to re-enable.');
}

// ============================================================================
// END — gee/S2_QC_Ingest.js  (v0.6.1)
// ============================================================================
