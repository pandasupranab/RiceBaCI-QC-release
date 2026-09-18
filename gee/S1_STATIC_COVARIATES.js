/**
 * ============================================================================
 * S1_STATIC_COVARIATES.js  --  RiceBaCI-QC, Protocol v1 §3.10 item 3a
 * ----------------------------------------------------------------------------
 * WHAT THIS IS FOR
 * ----------------------------------------------------------------------------
 * §3.10 item 3a declares an inverse-probability-of-selection-weighted estimate
 * whose score is a set of pre-declared covariates. That set was frozen against
 * the Sentinel-2 substrate -- cloud_freq_clim, dist_to_track_km, elevation_m --
 * and under the Sentinel-1 substrate two of the three do not apply: cloud is
 * not the operative mechanism, and the terrain quantity that drives VH/VV is
 * local geometry rather than height alone. The radar declaration, closed in
 * python/attrition_diagnostics.py on 2026-09-12, is
 *
 *     obs_total, n_valid_dekads, dist_to_track_km,
 *     elevation_m, slope_deg, incidence_deg
 *
 * The first three come from the panel and the exposure file and need no export.
 * THIS SCRIPT PRODUCES THE LAST THREE. They do not vary by season, so this is
 * 25 tasks -- one per district -- not 225.
 *
 * ----------------------------------------------------------------------------
 * WHAT IT EXPORTS
 * ----------------------------------------------------------------------------
 * One CSV per district, at the COMMITTED cohort points (cohort_v2), with
 *
 *     district, tile_id, cell_id, lon, lat,
 *     elevation_m, slope_deg, incidence_deg, n_angle_images
 *
 * elevation_m     NASA/NASADEM_HGT/001 'elevation', sampled at the cell.
 * slope_deg       ee.Terrain.slope of that elevation band, in degrees.
 * incidence_deg   mean of the Sentinel-1 GRD 'angle' band over every IW
 *                 VV+VH scene intersecting the district in the nine analysis
 *                 seasons -- the same collection and the same filters
 *                 buildS1Collection uses in the panel export, so the angle is
 *                 the angle the panel was measured at.
 * n_angle_images  how many scenes went into that mean, so a thin sample is
 *                 visible rather than silent.
 *
 * ----------------------------------------------------------------------------
 * TWO THINGS DELIBERATELY COPIED FROM v0.7.1, BOTH OF WHICH WERE BUGS ONCE
 * ----------------------------------------------------------------------------
 * 1. The cohort asset is loaded PLAIN and the point geometry is rebuilt here
 *    from the committed lon/lat properties. Uploading it with an X/Y mapping
 *    gives every feature an empty MultiPoint geometry and reduceRegions then
 *    returns nulls for every band -- the v0.6.0 failure.
 * 2. Export.table.toDrive is given an explicit `selectors` list. Without it
 *    Earth Engine infers the CSV header from the leading features, and an
 *    all-null leading block drops those columns from the ENTIRE file. That is
 *    the defect that silently emptied 97 of 225 S1 files on 2026-09-10 and
 *    175 of 189 S2 files on 2026-09-08. Never omit it.
 *
 * ----------------------------------------------------------------------------
 * HOW TO RUN
 * ----------------------------------------------------------------------------
 *   1. Paste the whole file into the Earth Engine Code Editor.
 *   2. Check that CONFIG.cohortAssetPath below is the same asset id the panel
 *      export used. If it is not, STOP -- a different cohort means cell_id is
 *      not a stable key and the covariates will not join.
 *   3. Run. 25 tasks appear in the Tasks tab. Run them all.
 *   4. The CSVs land in Drive folder CONFIG.driveFolder.
 *   5. Then:
 *        python python/merge_static_covariates.py \
 *            --static <downloaded dir> --panel <panel.csv> --out <panel2.csv>
 *
 * Created 2026-09-12.
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

  driveFolder: 'RiceBaCI-QC_S1_static',
  exportPrefix: 'S1_STATIC_',

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

print('===================================================================');
print('===  S1 STATIC COVARIATES  (§3.10 item 3a, radar declaration)    ===');
print('===================================================================');
print('Cohort asset:', CONFIG.cohortAssetPath);
print('Cohort points (all districts):', cohort.size());
print('Expected tasks:', districtRecs.length,
      '(one per district, not per season)');

var taskIndex = 0;

districtRecs.forEach(function (rec) {

  var loaded = loadDistrictGeom(rec);
  var nMatch = loaded.matchCount.getInfo();
  if (nMatch === 0) {
    print('[DISTRICT NOT FOUND] ' + rec.state + ' / ' + rec.gadmName +
          '  -- filtered ' + rec.filterField + ' == "' + rec.filterValue +
          '" on ' + rec.assetPath + '. No task created for this district. ' +
          'Fix the CONFIG line rather than letting it export short.');
    return;
  }
  var geom = loaded.geom;
  // The cohort asset carries the GADM canonical name, not the asset-local one.
  var pts = cohort.filter(ee.Filter.eq('district', rec.gadmName));
  var nPts = pts.size().getInfo();
  if (nPts === 0) {
    print('[NO COHORT POINTS] ' + rec.gadmName + ' matched ' + nMatch +
          ' geometry feature(s) but 0 cohort points. No task created.');
    return;
  }

  var ang = angleMean(geom);
  var stack = terrain.addBands(ang.image);

  // ee.Reducer.first() matches the panel export: a 30 m cell at 30 m scale is
  // one pixel, so first() and mean() coincide, and first() is what the panel
  // used. Keeping them identical is the point.
  var sampled = stack.reduceRegions({
    collection: pts,
    reducer: ee.Reducer.first(),
    scale: CONFIG.scaleMeters,
    tileScale: CONFIG.reduceTileScale
  }).map(function (f) {
    return f.set({
      'district': rec.gadmName,
      'tile_id': CONFIG.cohortId,
      'n_angle_images': ang.n
    });
  });

  var table = sampled.select(
    ['district', 'tile_id', 'cell_id', 'lon', 'lat',
     'elevation_m', 'slope_deg', 'incidence_deg', 'n_angle_images'],
    null, false);

  var safeName = rec.gadmName.replace(/[^A-Za-z0-9]+/g, '_');
  var description = CONFIG.exportPrefix + safeName;

  Export.table.toDrive({
    collection: table,
    description: description,
    folder: CONFIG.driveFolder,
    fileNamePrefix: description,
    fileFormat: 'CSV',
    // REQUIRED, not cosmetic. See the header note.
    selectors: ['district', 'tile_id', 'cell_id', 'lon', 'lat',
                'elevation_m', 'slope_deg', 'incidence_deg', 'n_angle_images']
  });

  taskIndex += 1;
  print('[TASK ' + taskIndex + '] ' + description + '   (' + nPts +
        ' cohort points)');
});

print('-------------------------------------------------------------------');
print('Tasks created:', taskIndex, '(expected ' + districtRecs.length + ')');
print('Drive folder:', CONFIG.driveFolder);
if (taskIndex !== districtRecs.length) {
  print('*** STOP. ' + (districtRecs.length - taskIndex) + ' district(s) ' +
        'produced no task. Read the [DISTRICT NOT FOUND] or [NO COHORT ' +
        'POINTS] lines above and fix CONFIG before running any task: a ' +
        'short export becomes a covariate that is missing for exactly the ' +
        'districts it failed on, which is not missing at random. ***');
}
print('-------------------------------------------------------------------');
