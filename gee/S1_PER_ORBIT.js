/**
 * ============================================================================
 * S1_PER_ORBIT.js  --  RiceBaCI-QC, Protocol v1 §2 H1 and H2
 * ----------------------------------------------------------------------------
 * WHAT THIS IS FOR
 * ----------------------------------------------------------------------------
 * CURRENT STATUS (2026-09-16). The export has been completed and the accepted
 * orbit-agreement tables are in results/orbit_agreement/. The two orbit fits
 * are separate repeat measurements, not independent errors and not accuracy
 * observations. The run instructions below are retained for reproduction.
 *
 * H1 and H2 are the study's remaining LIVE hypotheses. The 2026-09-13 amendment
 * (Protocol §4.1) withdrew every causal claim about cyclone exposure, because
 * the design fails its own §3.9 timing placebo and lead test. H1 and H2 are
 * untouched by that: they are MEASUREMENT-CONSISTENCY claims and contain no
 * causal claim about cyclones.
 *
 *   H1  For eligible pixels, the fitted end-of-dark-phase breakpoint estimated
 *       SEPARATELY FROM DISTINCT SENTINEL-1 RELATIVE ORBITS agrees within a
 *       pre-declared tolerance, and each pixel's inter-seasonal dispersion
 *       about its own mean, after removing season effects, is smaller than the
 *       between-pixel dispersion within its district.
 *   H2  As H1, for the fitted end-of-fall breakpoint.
 *
 * The committed panel export cannot test either. It builds ONE series per
 * pixel-season by normalising the relative orbits onto a common level and then
 * compositing them together (s1_block.js, normaliseByOrbit). That is the right
 * substrate for a single best estimate and the wrong one for an agreement test:
 * once the orbits are merged there are no longer two estimates to compare.
 *
 * THIS SCRIPT PRODUCES ONE SERIES PER (PIXEL, SEASON, RELATIVE ORBIT), so the
 * phenometric estimator can be run separately on each orbit and the resulting
 * dates compared. Those exports now supply H1(a) and H2(a).
 *
 * ----------------------------------------------------------------------------
 * THREE DESIGN DECISIONS, EACH OF WHICH COULD HAVE GONE THE OTHER WAY
 * ----------------------------------------------------------------------------
 * 1. NO PER-ORBIT NORMALISATION IS APPLIED. s1_block.js subtracts each orbit's
 *    own within-season per-pixel median and adds back the across-orbit median,
 *    to remove the incidence-angle level offset before compositing. Here the
 *    orbits must remain separate, so each one's raw VH/VV is exported as that
 *    orbit records it. Applying a normalisation derived jointly across the
 *    orbits would mechanically couple the two series. Omitting it does not make
 *    their errors independent: estimator, grid and crop-state components remain
 *    shared. This costs nothing for H1/H2: PLSM's four levels are
 *    free parameters profiled out by weighted least squares, so a constant
 *    level offset cannot move a breakpoint. It is the SHAPE in time that is
 *    being compared, and the shape is what each orbit records separately.
 *
 * 2. THE 55-BIN FIVE-DAY GRID IS KEPT UNCHANGED (§1.4, DOY 150-425). Per orbit
 *    the repeat is 6 days while Sentinel-1B was flying and 12 days after it
 *    failed on 2021-12-23, so most five-day bins hold no observation for any
 *    single orbit. Aggregating to dekads in Earth Engine would have produced
 *    smaller files, and was rejected: Gate 1 (§3.1) is a sampling-density rule
 *    on the five-day bins, and pre-aggregating would either bypass it or force
 *    a second, differently-behaved version of it. Keeping the grid means the
 *    ENTIRE existing Python path -- read_export, gate1_admitted_bins,
 *    aggregate_to_dekads, whittaker_gcv, plsm_fit -- applies to each orbit's
 *    series with no new estimator code and no risk of the per-orbit path
 *    drifting from the panel path.
 *
 * 3. ROWS WITH NO OBSERVATION ARE DROPPED, NOT EXPORTED AS NULLS. With one
 *    orbit most bins are empty, and exporting them would triple the file size
 *    to carry nothing. This is safe because python/extract_phenometrics_sar.py
 *    read_export() builds a full (n_pixels x 55) array of NaN and scatters the
 *    rows it finds into it, so an absent row and a null row are already the
 *    same thing to the reader. The dummy-band armor is still applied to the
 *    composites, because that guards a different failure -- a bin empty across
 *    ALL pixels making the image bandless and crashing the export.
 *
 * ----------------------------------------------------------------------------
 * TWO THINGS COPIED DELIBERATELY FROM v0.7.1, BOTH OF WHICH WERE BUGS ONCE
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
 * WHAT IT EXPORTS
 * ----------------------------------------------------------------------------
 * One CSV per (district, season) -- 25 x 9 = 225 tasks -- each holding every
 * relative orbit that district-season has, with columns
 *
 *     district, year, cell_id, orbit, orbit_pass,
 *     bin_index, VHVV_med, valid_obs_count, n_orbit_images
 *
 * orbit           relativeOrbitNumber_start. The unit H1 compares across.
 * orbit_pass      ASCENDING or DESCENDING, constant within a relative orbit.
 *                 An ascending/descending pair gives the most geometrically
 *                 distinct views available and the Python side prefers such a
 *                 pair; this does not imply independent errors.
 * n_orbit_images  scenes contributing to that orbit in that season, so a thin
 *                 orbit is visible rather than silently producing a bad fit.
 *
 * lon/lat and tile_id are NOT repeated on every row. They are constant per
 * cell_id and already committed in docs/candidate_cohort_v2.csv, which the
 * Python consumer joins on. This is what keeps the files small enough to move.
 *
 * ----------------------------------------------------------------------------
 * HOW TO RUN
 * ----------------------------------------------------------------------------
 *   0. RUN gee/S1_ORBIT_INVENTORY.js FIRST. It creates no tasks and takes under
 *      a minute, and it answers the question that decides whether this export is
 *      worth running at all: do two or more relative orbits cover the same
 *      cohort points in the same season? H1 compares orbits against each other,
 *      so one orbit per district-season makes these 225 tasks useless. The
 *      committed panel's scene counts imply about two orbits throughout, but
 *      that is an inference from orbit-combined data; the inventory measures it.
 *   1. Paste the whole file into the Earth Engine Code Editor.
 *   2. Confirm CONFIG.cohortAssetPath is the SAME asset id the panel export
 *      used. If it is not, STOP -- a different cohort means cell_id is not a
 *      stable key and nothing will join.
 *   2b. LEAVE CONFIG.dryRunDistrict SET for the first run. It queues ONE task
 *      instead of 225 so a structural defect in this file's per-orbit logic
 *      costs one export, not a day. The original dry run and full export have
 *      been completed; this remains the safe reproduction sequence.
 *   3. Run. Read the printed lines FIRST. 225 tasks should appear. If the
 *      final block prints *** STOP ***, fix CONFIG before running any task:
 *      a short export is missing for exactly the districts it failed on,
 *      which is not missing at random.
 *   4. Run the tasks. They land in Drive folder CONFIG.driveFolder.
 *   5. Then, on the downloaded directory:
 *        python python/orbit_agreement.py --exports <dir> --out results/
 *
 * NOTE FOR THE PYTHON CONSUMER, not enforceable here: §2 requires H1's and
 * H2's tolerances to be "fixed on the untreated 2017 baseline season before
 * any treated season is fitted". The consumer must derive the tolerance on
 * 2017 only and then apply it unchanged to 2018-2025. Deriving it on the
 * pooled panel would make the test circular.
 *
 * Created 2026-09-13.
 * ============================================================================
 */

var CONFIG = {

  // MUST match the panel export exactly. Committed cohort, 25 districts x 400.
  cohortAssetPath: 'projects/durable-pulsar-486209-b5/assets/RiceBaCI_cohort_v2',
  cohortId: 'cohort_v2',

  s1Collection: 'COPERNICUS/S1_GRD',

  scaleMeters: 30,
  reduceTileScale: 16,

  // §1.4 season window and bin grid. Identical to the panel export: 55 bins.
  years: [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
  seasonStartDOY: 150,
  seasonEndDOY: 425,
  binWidthDays: 5,

  driveFolder: 'RiceBaCI-QC_S1_perorbit',
  exportPrefix: 'S1_ORBIT_',

  // DRY RUN. Set to a district name and a year to queue ONE task instead of 225,
  // so a structural defect costs one export rather than a day. 225 tasks is a
  // large commitment and this file's per-orbit logic -- the server-side orbit
  // enumeration, the empty-bin pre-filter, the notNull row drop -- has never run
  // against real data. Verify the single CSV first: it should carry two or more
  // distinct `orbit` values, `bin_index` spread across 0-54, and no null
  // VHVV_med. Then set both back to null and run the full set.
  // Pashchim Medinipur 2024 deliberately: the inventory shows it carrying FOUR
  // relative orbits with both passes present, so it is the district most likely
  // to expose a defect in the server-side orbit enumeration. Ganjam, the first
  // choice, turned out to have only ONE orbit, which would have made a clean dry
  // run prove nothing about the two-orbit case this export exists to produce.
  // SET TO null FOR THE FULL 225-TASK RUN. Left as a named district during the
  // 2026-09-13 dry run and NOT reset in the saved copy, which an external audit
  // correctly flagged as a provenance gap: the file as saved queued one task, not
  // the 225 that produced the committed exports. Now null, so the saved script
  // reproduces what was actually run.
  dryRunDistrict: null,
  dryRunYear: null,

  // District geometry, copied VERBATIM from S1_STATIC_COVARIATES.js, which was
  // itself corrected on 2026-09-13 after a first version invented GADM asset
  // ids and used NAME_2 for all three states. These are the verified values;
  // do not "tidy" them.
  riceAtlasAssetPath: {
    'West Bengal':    'users/supranab/RiceAtlas_WB',
    'Odisha':         'projects/durable-pulsar-486209-b5/assets/RiceAtlas_OD',
    'Andhra Pradesh': 'projects/durable-pulsar-486209-b5/assets/RiceAtlas_AP_coastal'
  },
  filterField: {
    'West Bengal':    'SUB_REGION',
    'Odisha':         'GADM_NAME',
    'Andhra Pradesh': 'GADM_NAME'
  },
  WB_NAME_MAP: {
    'Purba Medinipur':    'East Midnapore',
    'Pashchim Medinipur': 'West Midnapore'
  },

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

var EXPORT_COLS = ['district', 'year', 'cell_id', 'orbit', 'orbit_pass',
                   'bin_index', 'VHVV_med', 'valid_obs_count',
                   'n_orbit_images'];

// ---------------------------------------------------------------------------
// district roster, flattened
// ---------------------------------------------------------------------------
var districtRecs = [];
Object.keys(CONFIG.districtsByState).forEach(function (state) {
  CONFIG.districtsByState[state].forEach(function (gadmName) {
    districtRecs.push({
      state: state,
      gadmName: gadmName,                                      // name used everywhere else
      filterValue: (CONFIG.WB_NAME_MAP[gadmName] || gadmName), // name ON the asset
      assetPath: CONFIG.riceAtlasAssetPath[state],
      filterField: CONFIG.filterField[state]
    });
  });
});

function loadDistrictGeom(rec) {
  var src = ee.FeatureCollection(rec.assetPath)
              .filter(ee.Filter.eq(rec.filterField, rec.filterValue));
  return { geom: src.geometry(), matchCount: src.size() };
}

// ---------------------------------------------------------------------------
// collection, ratio. Same filters as buildS1Collection in the panel export, so
// the per-orbit series is drawn from exactly the scenes the panel could use.
// ---------------------------------------------------------------------------
function buildS1Collection(roi, startDate, endDate) {
  return ee.ImageCollection(CONFIG.s1Collection)
           .filterBounds(roi)
           .filterDate(startDate, endDate)
           .filter(ee.Filter.eq('instrumentMode', 'IW'))
           .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
           .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'));
}

function addRatio(img) {
  // S1_GRD is already in dB, so the ratio in dB is the DIFFERENCE. Do not divide.
  return img.addBands(
      img.select('VH').subtract(img.select('VV')).rename('VHVV'))
    .copyProperties(img, ['system:time_start', 'relativeOrbitNumber_start',
                          'orbitProperties_pass']);
}

// ---------------------------------------------------------------------------
// 55 five-day composites of ONE orbit's ratio, on the §1.4 grid.
// ---------------------------------------------------------------------------
function buildBins(coll, year) {
  var binStarts = ee.List.sequence(CONFIG.seasonStartDOY,
                                   CONFIG.seasonEndDOY - CONFIG.binWidthDays + 1,
                                   CONFIG.binWidthDays);
  var yearStart = ee.Date.fromYMD(year, 1, 1);

  // Armor: a bin empty across every pixel yields a bandless image and
  // Export.table.toDrive fails with "Image has no bands". Masked constants give
  // it bands whose values are all null instead.
  var dummy = ee.Image.constant([0, 0])
                .rename(['VHVV_med', 'valid_obs_count'])
                .updateMask(ee.Image(0));

  var all = ee.ImageCollection.fromImages(binStarts.map(function (doyStart) {
    doyStart = ee.Number(doyStart);
    var binStart = yearStart.advance(doyStart.subtract(1), 'day');
    var bin = coll.filterDate(binStart, binStart.advance(CONFIG.binWidthDays, 'day'));
    var armored = dummy.addBands(
        bin.median().rename('VHVV_med')
           .addBands(bin.count().rename('valid_obs_count')), null, true);
    return armored.set({'bin_index': binStarts.indexOf(doyStart),
                        'n_in_bin': bin.size()});
  }));

  // Drop the bins this orbit has no scene in, BEFORE sampling. Per orbit the
  // repeat is 6 days with Sentinel-1B flying and 12 days after it failed on
  // 2021-12-23, so roughly 23 of the 55 five-day bins hold anything and the
  // other 32 would be sampled at 400 points each to produce nothing. This is
  // the difference between ~22,000 and ~9,000 sampled features per orbit, and
  // with three or four orbits per district-season it is what keeps a task
  // inside Earth Engine's computation limits. bin_index is already set, so the
  // surviving bins keep their true position on the 55-bin grid and the Python
  // reader still lands them in the right column.
  //
  // The dummy armor is kept on the survivors: a bin can hold scenes that are
  // all masked at the cohort points, which is a different failure from a bin
  // holding no scene at all.
  return all.filter(ee.Filter.gt('n_in_bin', 0));
}

// ---------------------------------------------------------------------------
// One table per district-season, holding every orbit.
//
// The orbit list is built SERVER-SIDE with aggregate_array().distinct() and
// mapped over with ee.List.map, exactly as normaliseByOrbit does in
// s1_block.js. That matters: enumerating orbits client-side would need a
// getInfo() per district-season -- 225 blocking round trips in the Code Editor
// -- and would make the script's behaviour depend on when it was run.
// ---------------------------------------------------------------------------
function perOrbitTable(raw, pts, districtName, year) {
  var withRatio = raw.map(addRatio).select('VHVV');
  var orbits = ee.List(withRatio.aggregate_array('relativeOrbitNumber_start'))
                 .distinct().sort();

  var perOrbit = orbits.map(function (o) {
    var sub = withRatio.filter(ee.Filter.eq('relativeOrbitNumber_start', o));
    var nImg = sub.size();
    // constant within a relative orbit; taken from the first scene of it
    var pass = ee.Image(sub.first()).get('orbitProperties_pass');

    return buildBins(sub, year).map(function (img) {
      img = ee.Image(img);
      return img.reduceRegions({
        collection: pts,
        reducer: ee.Reducer.first(),
        scale: CONFIG.scaleMeters,
        tileScale: CONFIG.reduceTileScale
      }).map(function (f) {
        return f.set({
          'district': districtName,
          'year': year,
          'orbit': o,
          'orbit_pass': pass,
          'bin_index': img.get('bin_index'),
          'n_orbit_images': nImg
        });
      });
    }).flatten();
  });

  // Drop the empty bins. read_export() reconstructs them as NaN -- see design
  // decision 3 in the header.
  return ee.FeatureCollection(perOrbit).flatten()
           .filter(ee.Filter.notNull(['VHVV_med']))
           .select(EXPORT_COLS, null, false);
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
print('===  S1 PER-ORBIT SERIES  (Protocol §2 H1 and H2)                ===');
print('===================================================================');
print('Cohort asset:', CONFIG.cohortAssetPath);
print('Cohort points (all districts):', cohort.size());
print('Expected tasks:', districtRecs.length * CONFIG.years.length,
      '= ' + districtRecs.length + ' districts x ' + CONFIG.years.length +
      ' seasons');
print('NOTE: no jointly derived per-orbit normalisation is applied. See header');
print('      decision 1: the series remain separate; error independence is not claimed.');

var taskIndex = 0;
var skipped = [];
var DRY = (CONFIG.dryRunDistrict !== null && CONFIG.dryRunDistrict !== undefined);
if (DRY) {
  print('');
  print('*** DRY RUN *** only ' + CONFIG.dryRunDistrict + ' ' +
        CONFIG.dryRunYear + ' will be queued -- ONE task, not ' +
        (districtRecs.length * CONFIG.years.length) + '.');
  print('Run it, open the CSV, and check three things:');
  print('  1. two or more distinct values in the `orbit` column');
  print('  2. `bin_index` spread across 0-54, not clustered at one end');
  print('  3. no empty VHVV_med cells');
  print('Then set CONFIG.dryRunDistrict and dryRunYear to null and re-run this');
  print('script to queue the full set.');
  print('');
}

districtRecs.forEach(function (rec) {
  if (DRY && rec.gadmName !== CONFIG.dryRunDistrict) { return; }

  var loaded = loadDistrictGeom(rec);
  var nMatch = loaded.matchCount.getInfo();
  if (nMatch === 0) {
    print('[DISTRICT NOT FOUND] ' + rec.state + ' / ' + rec.gadmName +
          '  -- filtered ' + rec.filterField + ' == "' + rec.filterValue +
          '" on ' + rec.assetPath + '. No tasks created for this district. ' +
          'Fix the CONFIG line rather than letting it export short.');
    skipped.push(rec.gadmName + ' (geometry)');
    return;
  }
  var geom = loaded.geom;
  // The cohort asset carries the GADM canonical name, not the asset-local one.
  var pts = cohort.filter(ee.Filter.eq('district', rec.gadmName));
  var nPts = pts.size().getInfo();
  if (nPts === 0) {
    print('[NO COHORT POINTS] ' + rec.gadmName + ' matched ' + nMatch +
          ' geometry feature(s) but 0 cohort points. No tasks created.');
    skipped.push(rec.gadmName + ' (cohort)');
    return;
  }

  CONFIG.years.forEach(function (year) {
    if (DRY && year !== CONFIG.dryRunYear) { return; }
    var seasonStart = ee.Date.fromYMD(year, 1, 1)
                        .advance(CONFIG.seasonStartDOY - 1, 'day');
    var seasonEnd = ee.Date.fromYMD(year, 1, 1)
                        .advance(CONFIG.seasonEndDOY, 'day');

    var raw = buildS1Collection(geom, seasonStart, seasonEnd);
    var table = perOrbitTable(raw, pts, rec.gadmName, year);

    var safeName = rec.gadmName.replace(/[^A-Za-z0-9]+/g, '_');
    var description = CONFIG.exportPrefix + safeName + '_' + year;

    Export.table.toDrive({
      collection: table,
      description: description,
      folder: CONFIG.driveFolder,
      fileNamePrefix: description,
      fileFormat: 'CSV',
      // REQUIRED, not cosmetic. See the header note.
      selectors: EXPORT_COLS
    });

    taskIndex += 1;
    print('[TASK ' + taskIndex + '] ' + description + '   (' + nPts +
          ' cohort points)');
  });
});

var expected = DRY ? 1 : districtRecs.length * CONFIG.years.length;
print('-------------------------------------------------------------------');
print('Tasks created:', taskIndex, '(expected ' + expected + ')');
print('Drive folder:', CONFIG.driveFolder);
if (taskIndex !== expected) {
  print('*** STOP. ' + (expected - taskIndex) + ' task(s) were not created: ' +
        skipped.join(', ') + '. Read the [DISTRICT NOT FOUND] or [NO COHORT ' +
        'POINTS] lines above and fix CONFIG before running any task. A short ' +
        'export makes H1 and H2 untestable for exactly the districts that ' +
        'failed, which is not missing at random. ***');
} else {
  print('All ' + expected + ' tasks created. Run them, then:');
  print('  python python/orbit_agreement.py --exports <dir> --out results/');
}
print('-------------------------------------------------------------------');
