/**
 * ============================================================================
 * S1_MASK_FLAG.js  --  RiceBaCI-QC, Protocol v1 §3.5 mask-sensitivity arm
 * ----------------------------------------------------------------------------
 * WHY THIS EXISTS
 * ----------------------------------------------------------------------------
 * §3.5's disclosure rule requires the primary-mask and intersection-mask results
 * "computed for every district x cyclone unit and reported side by side before
 * either is discussed". It had never been run; an external audit on 2026-09-13
 * found no script and no output, correctly.
 *
 * The obvious implementation -- re-draw a cohort inside RiceAtlas n WorldCereal
 * and re-export everything -- is a second complete data campaign, and worse, it
 * breaks cell_id as a stable key between the two arms, which is the one thing
 * that makes them comparable. This script does the cheap and better version:
 * it holds the COMMITTED cohort fixed and exports, for each of the 10,000
 * points, whether that point also falls inside the sensitivity mask. The
 * analyses then re-run on the in-both-masks subset and the two are reported
 * side by side, at identical cell_ids. 25 tasks, one row per cohort point.
 *
 * WHAT §3.5 REQUIRES BE SAID, VERBATIM, WHEREVER THIS IS REPORTED
 * ----------------------------------------------------------------------------
 * The intersection is with ESA WorldCereal 2021 `temporarycrops`, a GENERAL
 * CROPLAND classifier, and NOT an independent rice product: the v100 collection
 * contains no rice layer. The disagreement this arm measures is therefore
 * cropland-versus-rice, not rice-versus-rice. §3.5's 2026-09-09 note already
 * says so; it must appear in the manuscript body too.
 *
 * WHAT IT EXPORTS
 * ----------------------------------------------------------------------------
 * One CSV per district: district, tile_id, cell_id, in_worldcereal_temporary,
 * worldcereal_pixels_sampled. The flag is 1 when the cohort point falls in a
 * WorldCereal temporarycrops pixel classified as cropland, 0 when it does not,
 * and null where WorldCereal has no coverage -- null and 0 are NOT the same and
 * the Python side must not conflate them.
 *
 * TWO THINGS COPIED DELIBERATELY, BOTH OF WHICH WERE BUGS ONCE
 * ----------------------------------------------------------------------------
 * 1. The cohort asset is loaded PLAIN and the geometry rebuilt from the
 *    committed lon/lat. An X/Y-mapped upload gives every feature an empty
 *    geometry and every sample returns null -- the v0.6.0 failure.
 * 2. Export.table.toDrive is given an explicit `selectors` list. Without it
 *    Earth Engine infers the header from the leading features and an all-null
 *    leading block drops those columns from the entire file -- the defect that
 *    silently emptied 97 of 225 S1 files on 2026-09-10.
 *
 * HOW TO RUN
 * ----------------------------------------------------------------------------
 *   1. Paste into the Earth Engine Code Editor and Run.
 *   2. Read the printed lines. 25 tasks should appear; if the closing block
 *      prints *** STOP ***, fix CONFIG before running any task.
 *   3. Run the tasks; CSVs land in CONFIG.driveFolder.
 *   4. Then: python python/mask_sensitivity.py --flags <dir>
 *
 * Created 2026-09-13.
 * ============================================================================
 */

var CONFIG = {

  // MUST match the panel export exactly. Committed cohort, 25 districts x 400.
  cohortAssetPath: 'projects/durable-pulsar-486209-b5/assets/RiceBaCI_cohort_v2',
  cohortId: 'cohort_v2',

  scaleMeters: 30,
  reduceTileScale: 16,

  s1Collection: 'COPERNICUS/S1_GRD',
  demCollection: 'NASA/NASADEM_HGT/001',

  // The nine analysis seasons, over the full §1.4 season window, so the angle
  // mean is taken over exactly the scenes the panel could have used.
  years: [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
  seasonStartDOY: 150,
  seasonEndDOY: 425,

  driveFolder: 'RiceBaCI-QC_mask_flag',
  exportPrefix: 'S1_MASKFLAG_',

  // §3.5's sensitivity mask. v100 codes cropland as 100 in `classification`.
  worldCerealCollection: 'ESA/WorldCereal/2021/MODELS/v100',
  worldCerealCroplandValue: 100,

  // VERIFIED AGAINST THE LIVE CATALOGUE 2026-09-13. The three values above --
  // the asset id, the `product` filter value and the cropland code -- were
  // originally written from memory and unchecked; the first version of
  // S1_STATIC_COVARIATES.js was written the same way and carried three defects,
  // each of which would have matched zero features in every district. So this
  // file was run with verifyOnly:true first. What the catalogue returned:
  //   VERIFY 1  'ESA/WorldCereal/2021/MODELS/v100' resolves, 591 images.
  //   VERIFY 2  products = irrigation, maize, springcereals, temporarycrops,
  //             wintercereals. 'temporarycrops' present; 106 tiles.
  //   VERIFY 3  bands = ['classification','confidence']. Histogram of
  //             `classification` over Puri's bounds at 100 m has exactly two
  //             keys, 0 and 100 (710268 : 317975 weighted px, 30.9% cropland).
  //             So worldCerealCroplandValue = 100 is correct.
  //   VERIFY 4  Puri: 400/400 cohort points covered, 346 coded 100 (86.5%),
  //             distinct values at the points exactly {0, 100} -- so sampling a
  //             10 m categorical band at scale 30 returns no interpolated
  //             values, in 400 independent draws.
  // The 86.5% at cohort points against 30.9% over the district bounding box is
  // a 2.8x enrichment. That is the direction it must go if the cohort selection
  // is finding agricultural land at all, and it is the one piece of external
  // corroboration of the cohort in this file. It is not a rice check; see the
  // GENERAL CROPLAND note printed below.
  verifyOnly: false,

  // DRY RUN COMPLETED AND VALIDATED 2026-09-13. The Puri export was checked
  // before this was set to null; S1_MASKFLAG_Puri.csv gave:
  //   400 rows, one per cohort point, no nulls in any column.
  //   Exactly the 5 declared columns -- no `system:index`, no `.geo`. The
  //     explicit `selectors` list documented in the header did its job.
  //   cell_id unique 400/400, and joins 400/400 BOTH WAYS against
  //     results/phen_panel_sar.csv (3600 rows = 400 x 9 seasons) and
  //     results/s1_static_covariates.csv. The arm is mergeable.
  //   in_worldcereal_temporary: 346 ones, 54 zeros = 86.5%, matching VERIFY 4
  //     to the unit. VERIFY 4 and the export compute the flag by DIFFERENT code
  //     paths (an inline reduceRegions in the print block, versus the
  //     ee.Algorithms.If tri-state mapping used here), so agreement is a real
  //     cross-check on the tri-state logic, not a tautology.
  //   worldcereal_pixels_sampled == 1 at all 400 points. This settles the
  //     mosaic-arbitrariness caveat noted below: no Puri cohort point falls
  //     under overlapping WorldCereal tiles, so mosaic() had nothing to choose
  //     between. Re-check this column per district on the full run; it is
  //     exported for that purpose.
  // Set back to a district name to re-dry-run.
  dryRunDistrict: null,

  // District geometry, copied VERBATIM from S2_QC_Ingest v0.7.1's CONFIG.
  // CORRECTED 2026-09-13: the first version of this file invented GADM asset
  // ids and used NAME_2 for all three states. Both were wrong and every
  // district would have matched zero features. These are the real values.
  riceAtlasAssetPath: {
    'West Bengal':    'users/supranab/RiceAtlas_WB',
    'Odisha':         'projects/durable-pulsar-486209-b5/assets/RiceAtlas_OD',
    'Andhra Pradesh': 'projects/durable-pulsar-486209-b5/assets/RiceAtlas_AP_coastal'
  },
  // WB filters on SUB_REGION, the only name field on the legacy asset; OD and
  // AP-coastal carry the GADM 4.1 canonical spelling as a first-class column.
  filterField: {
    'West Bengal':    'SUB_REGION',
    'Odisha':         'GADM_NAME',
    'Andhra Pradesh': 'GADM_NAME'
  },
  // The two Midnapore districts are transliterated differently on the WB
  // legacy asset. Without this map both match zero features and their 800
  // cohort points get no covariates. Crosswalk: docs/coastal_districts_crosswalk.csv
  WB_NAME_MAP: {
    'Purba Medinipur':    'East Midnapore',
    'Pashchim Medinipur': 'West Midnapore'
  },

  // The 25-district roster of the panel export. If this list and the cohort
  // asset disagree, the script says so per district rather than exporting a
  // short file.
  districtsByState: {
    'Odisha': ['Baleshwar', 'Bhadrak', 'Cuttack', 'Gajapati', 'Ganjam',
               'Jagatsinghapur', 'Jajapur', 'Kendrapara', 'Khordha',
               'Mayurbhanj', 'Nayagarh', 'Puri'],
    'West Bengal': ['Haora', 'Hugli', 'North 24 Parganas',
                    'Pashchim Medinipur', 'Purba Medinipur',
                    'South 24 Parganas'],
    'Andhra Pradesh': ['East Godavari', 'Guntur', 'Krishna', 'Srikakulam',
                       'Visakhapatnam', 'Vizianagaram', 'West Godavari']
  }
};

// ---------------------------------------------------------------------------
// district roster, flattened, with the state each name came from
// ---------------------------------------------------------------------------
var districtRecs = [];
Object.keys(CONFIG.districtsByState).forEach(function (state) {
  CONFIG.districtsByState[state].forEach(function (gadmName) {
    districtRecs.push({
      state: state,
      gadmName: gadmName,                       // the name used everywhere else
      filterValue: (CONFIG.WB_NAME_MAP[gadmName] || gadmName),  // the name ON the asset
      assetPath: CONFIG.riceAtlasAssetPath[state],
      filterField: CONFIG.filterField[state]
    });
  });
});

function loadDistrictGeom(rec) {
  // Filters on filterValue, not gadmName: see CONFIG.WB_NAME_MAP.
  var src = ee.FeatureCollection(rec.assetPath)
              .filter(ee.Filter.eq(rec.filterField, rec.filterValue));
  return { geom: src.geometry(), matchCount: src.size() };
}

// ---------------------------------------------------------------------------
// district roster, flattened, with the state each name came from
// ---------------------------------------------------------------------------
var districtRecs = [];
Object.keys(CONFIG.districtsByState).forEach(function (state) {
  CONFIG.districtsByState[state].forEach(function (gadmName) {
    districtRecs.push({
      state: state,
      gadmName: gadmName,                       // the name used everywhere else
      filterValue: (CONFIG.WB_NAME_MAP[gadmName] || gadmName),  // the name ON the asset
      assetPath: CONFIG.riceAtlasAssetPath[state],
      filterField: CONFIG.filterField[state]
    });
  });
});

function loadDistrictGeom(rec) {
  // Filters on filterValue, not gadmName: see CONFIG.WB_NAME_MAP.
  var src = ee.FeatureCollection(rec.assetPath)
              .filter(ee.Filter.eq(rec.filterField, rec.filterValue));
  return { geom: src.geometry(), matchCount: src.size() };
}

// ---------------------------------------------------------------------------
// terrain: one image, two bands, computed once
// ---------------------------------------------------------------------------
var dem = ee.Image(CONFIG.demCollection).select('elevation');
var terrain = dem.rename('elevation_m')
                 .addBands(ee.Terrain.slope(dem).rename('slope_deg'));

// ---------------------------------------------------------------------------
// Sentinel-1 incidence angle, averaged over the scenes the panel could use.
// Same collection and same filters as buildS1Collection in the panel export.
// ---------------------------------------------------------------------------
function angleMean(geom) {
  var dateFilters = CONFIG.years.map(function (y) {
    return ee.Filter.date(
      ee.Date.fromYMD(y, 1, 1).advance(CONFIG.seasonStartDOY - 1, 'day'),
      ee.Date.fromYMD(y, 1, 1).advance(CONFIG.seasonEndDOY, 'day'));
  });
  var coll = ee.ImageCollection(CONFIG.s1Collection)
    .filterBounds(geom)
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
    .filter(ee.Filter.or.apply(null, dateFilters))
    .select('angle');
  return { image: coll.mean().rename('incidence_deg'), n: coll.size() };
}

// ---------------------------------------------------------------------------
// cohort: loaded PLAIN, geometry rebuilt from the committed lon/lat
// ---------------------------------------------------------------------------
if (!CONFIG.cohortAssetPath) {
  throw new Error(
    'CONFIG.cohortAssetPath is empty. Set it to the SAME asset id the panel ' +
    'export used. This script will not sample a re-drawn cohort.');
}
var cohort = ee.FeatureCollection(CONFIG.cohortAssetPath).map(function (f) {
  return f.setGeometry(
    ee.Geometry.Point([ee.Number(f.get('lon')), ee.Number(f.get('lat'))]));
});


// ---------------------------------------------------------------------------
// The sensitivity mask. ESA WorldCereal 2021 temporarycrops (Van Tricht et al.
// 2023, ESSD 15, 5491-5515). The collection is per-AEZ tiles; mosaicking the
// 'classification' band over the roster gives cropland = 100 in v100's coding.
// ---------------------------------------------------------------------------
var WC = ee.ImageCollection(CONFIG.worldCerealCollection)
           .filter(ee.Filter.eq('product', 'temporarycrops'))
           .select('classification');
var wcMosaic = WC.mosaic().rename('wc_class');
var wcCount = WC.count().rename('wc_n');   // 0 where WorldCereal has no coverage

print('===================================================================');
print('===  S1 MASK FLAG  (Protocol §3.5 mask-sensitivity arm)          ===');
print('===================================================================');

// ---------------------------------------------------------------------------
// VERIFICATION BLOCK -- runs first, always, and creates no tasks.
// It answers the four questions the CONFIG values above assume the answers to.
// ALL FOUR PASSED 2026-09-13; the returned values are recorded in CONFIG above.
// The block is deliberately left in place and still runs on every execution, so
// a later catalogue revision that changes the coding cannot pass silently.
// ---------------------------------------------------------------------------
// `cohort`, NOT the raw asset. The first version of this block read
// ee.FeatureCollection(CONFIG.cohortAssetPath) directly and every geometry came
// back empty, so filterBounds matched nothing and VERIFY 3 died on a null image.
// That is precisely the v0.6.0 failure this file's own header warns about: the
// asset is uploaded without an X/Y mapping, so lon/lat are PROPERTIES and the
// geometry must be rebuilt before any spatial operation. Written 2026-09-13,
// found by running it.
var probe = cohort.filter(ee.Filter.eq('district', 'Puri')).geometry();
var wcAll = ee.ImageCollection(CONFIG.worldCerealCollection);
print('--- VERIFY 1: does the asset id resolve, and how many images? ---');
print('  collection:', CONFIG.worldCerealCollection);
print('  total images:', wcAll.size());
print('  IF THIS ERRORS OR SHOWS 0, the asset id is wrong. STOP.');
print('--- VERIFY 2: what `product` values exist? ---');
print('  distinct product:',
      wcAll.aggregate_array('product').distinct().sort().join(', '));
print('  the code filters product == "temporarycrops". It must appear above.');
print('--- VERIFY 3: what does `classification` actually contain? ---');
var oneTile = ee.Image(wcAll.filter(ee.Filter.eq('product', 'temporarycrops'))
                            .filterBounds(probe).first());
print('  band names of one temporarycrops image:', oneTile.bandNames());
print('  distinct classification values over a roster district (histogram):',
      oneTile.select('classification').reduceRegion({
        reducer: ee.Reducer.frequencyHistogram(),
        geometry: probe.bounds(),
        scale: 100, maxPixels: 1e8, bestEffort: true}));
print('  the code treats ' + CONFIG.worldCerealCroplandValue + ' as cropland.');
print('  IF the histogram keys are not 0 and 100, correct');
print('  CONFIG.worldCerealCroplandValue before exporting.');
print('--- VERIFY 4: what the flag would be, for one district ---');
var _wcM = WC.mosaic().rename('wc_class');
var _wcN = WC.count().rename('wc_n');
var _s = _wcM.addBands(_wcN).reduceRegions({
  collection: cohort.filter(ee.Filter.eq('district', 'Puri')),
  reducer: ee.Reducer.first(), scale: CONFIG.scaleMeters,
  tileScale: CONFIG.reduceTileScale});
print('  Puri cohort points:', _s.size());
print('  points with WorldCereal coverage (wc_n > 0):',
      _s.filter(ee.Filter.gt('wc_n', 0)).size());
print('  of those, classification == ' + CONFIG.worldCerealCroplandValue + ':',
      _s.filter(ee.Filter.and(ee.Filter.gt('wc_n', 0),
                ee.Filter.eq('wc_class', CONFIG.worldCerealCroplandValue))).size());
print('  distinct wc_class values at the cohort points:',
      _s.aggregate_array('wc_class').distinct().sort().join(', '));
print('  IF the share flagged as cropland is implausibly 0% or 100%, or the');
print('  distinct values are not what CONFIG assumes, STOP and report.');
print('===================================================================');

if (CONFIG.verifyOnly) {
  print('*** verifyOnly is TRUE -- no export tasks created. ***');
  print('Read VERIFY 1-4 above. If all four match what CONFIG assumes, set');
  print('CONFIG.verifyOnly = false and re-run: that queues ONE task for ' +
        CONFIG.dryRunDistrict + '. Check that CSV, then set dryRunDistrict to');
  print('null for the full 25.');
}
print('Cohort asset:', CONFIG.cohortAssetPath);
print('WorldCereal temporarycrops tiles (whole collection, not clipped to the '
      + 'roster):', WC.size());
print('Expected tasks:', districtRecs.length, '(one per district)');
print('NOTE: the intersection is with a GENERAL CROPLAND classifier, not an');
print('      independent rice product. WorldCereal v100 has no rice layer.');
print('NOTE: WorldCereal ships overlapping per-AEZ tiles and wcMosaic takes the');
print('      last unmasked tile at each pixel, so where tiles disagree the');
print('      choice is arbitrary. worldcereal_pixels_sampled is exported for');
print('      exactly this reason: if it is 1 everywhere there is no ambiguity');
print('      to resolve, and if it is not, the disagreement rate is measurable');
print('      from the CSV without re-running anything here.');

var taskIndex = 0;
var skipped = [];

var DRY = (CONFIG.dryRunDistrict !== null && CONFIG.dryRunDistrict !== undefined);
districtRecs.forEach(function (rec) {
  if (CONFIG.verifyOnly) { return; }
  if (DRY && rec.gadmName !== CONFIG.dryRunDistrict) { return; }
  var loaded = loadDistrictGeom(rec);
  var nMatch = loaded.matchCount.getInfo();
  if (nMatch === 0) {
    print('[DISTRICT NOT FOUND] ' + rec.state + ' / ' + rec.gadmName +
          '  -- filtered ' + rec.filterField + ' == "' + rec.filterValue +
          '" on ' + rec.assetPath + '. No task created.');
    skipped.push(rec.gadmName + ' (geometry)');
    return;
  }
  var pts = cohort.filter(ee.Filter.eq('district', rec.gadmName));
  var nPts = pts.size().getInfo();
  if (nPts === 0) {
    print('[NO COHORT POINTS] ' + rec.gadmName + ' matched ' + nMatch +
          ' geometry feature(s) but 0 cohort points. No task created.');
    skipped.push(rec.gadmName + ' (cohort)');
    return;
  }

  // ee.Reducer.first() at CONFIG.scaleMeters, matching the panel export: a
  // 30 m cell at 30 m scale is one pixel, so first() and mean() coincide, and
  // first() is what the panel used. Keeping them identical is the point.
  var sampled = wcMosaic.addBands(wcCount).reduceRegions({
    collection: pts,
    reducer: ee.Reducer.first(),
    scale: CONFIG.scaleMeters,
    tileScale: CONFIG.reduceTileScale
  }).map(function (f) {
    var n = ee.Number(ee.Algorithms.If(f.get('wc_n'), f.get('wc_n'), 0));
    var cls = f.get('wc_class');
    // null where WorldCereal does not cover the point; 0/1 where it does.
    // These are different states and the consumer must not conflate them.
    var flag = ee.Algorithms.If(n.gt(0),
        ee.Algorithms.If(ee.Number(ee.Algorithms.If(cls, cls, 0))
                           .eq(CONFIG.worldCerealCroplandValue), 1, 0),
        null);
    return f.set({
      'district': rec.gadmName,
      'tile_id': CONFIG.cohortId,
      'in_worldcereal_temporary': flag,
      'worldcereal_pixels_sampled': n
    });
  });

  var cols = ['district', 'tile_id', 'cell_id',
              'in_worldcereal_temporary', 'worldcereal_pixels_sampled'];
  var safeName = rec.gadmName.replace(/[^A-Za-z0-9]+/g, '_');
  var description = CONFIG.exportPrefix + safeName;

  Export.table.toDrive({
    collection: sampled.select(cols, null, false),
    description: description,
    folder: CONFIG.driveFolder,
    fileNamePrefix: description,
    fileFormat: 'CSV',
    selectors: cols                // REQUIRED, not cosmetic. See the header.
  });

  taskIndex += 1;
  print('[TASK ' + taskIndex + '] ' + description + '   (' + nPts + ' points)');
});

var expected = CONFIG.verifyOnly ? 0 : (DRY ? 1 : districtRecs.length);
print('-------------------------------------------------------------------');
print('Tasks created:', taskIndex, '(expected ' + expected + ')');
print('Drive folder:', CONFIG.driveFolder);
if (!CONFIG.verifyOnly && taskIndex !== expected) {
  print('*** STOP. ' + (expected - taskIndex) + ' district(s) ' +
        'produced no task: ' + skipped.join(', ') + '. A short export makes ' +
        'the mask arm missing for exactly the districts that failed, which is ' +
        'not missing at random. Fix CONFIG before running any task. ***');
}
print('-------------------------------------------------------------------');
