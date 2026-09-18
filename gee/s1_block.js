// ============================================================================
// 4b. SENTINEL-1 PHENOMETRIC SUBSTRATE  (added v0.7.0, 2026-09-09)
// ----------------------------------------------------------------------------
// Protocol v1 §3 lead-in. Replaces the Sentinel-2 NDVI path as the source of
// SOS/POS/EOS. Sentinel-2 is retained only for the post-monsoon EOS
// cross-check of §3.4.
//
// Index is the CROSS-POLARISATION RATIO VH/VV, not VH alone. Over a rice
// field VH rises through the season with local minima rather than forming a
// single peak, and VV DECREASES by up to 10 dB through tillering as the
// canopy becomes erectophile and attenuates the return; neither is shaped for
// a double-logistic. The ratio traces one bell curve across roughly 10 dB and
// is reported to be largely independent of rice variety, which matters across
// three states with different cultivars.
//
// COPERNICUS/S1_GRD is already log-scaled, so the ratio in dB is the
// DIFFERENCE VH_dB - VV_dB. Do not divide.
// ============================================================================

function buildS1Collection(roi, startDate, endDate) {
  return ee.ImageCollection(CONFIG.s1Collection)
           .filterBounds(roi)
           .filterDate(startDate, endDate)
           .filter(ee.Filter.eq('instrumentMode', 'IW'))
           .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
           .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'));
}

function addRatio(img) {
  // dB ratio = VH_dB - VV_dB. Bands in S1_GRD are already in dB.
  return img.addBands(
      img.select('VH').subtract(img.select('VV')).rename('VHVV'))
    .copyProperties(img, ['system:time_start', 'relativeOrbitNumber_start',
                          'orbitProperties_pass']);
}

/**
 * Per-orbit normalisation (Protocol §3 lead-in).
 *
 * Backscatter depends on incidence angle and look direction, so the same
 * pixel sits at a different level on different relative orbits. Combining
 * orbits without correcting that injects step changes into the time series
 * that the fitter would read as phenology.
 *
 * For each orbit o and pixel p: subtract that orbit's own within-season
 * median at that pixel, then add back the median across all orbits at that
 * pixel. This removes the constant per-orbit offset while preserving the
 * temporal shape each orbit records, and restores a common absolute level so
 * the fitted amplitude stays interpretable.
 *
 * Per-pixel rather than per-district because incidence angle varies across
 * the swath, so the offset is not constant within a district.
 */
function normaliseByOrbit(coll) {
  var withRatio = coll.map(addRatio).select('VHVV');
  var allOrbitMedian = withRatio.median();                 // per-pixel, all orbits
  var orbits = ee.List(withRatio.aggregate_array('relativeOrbitNumber_start'))
                 .distinct();

  var perOrbit = orbits.map(function (o) {
    var sub = withRatio.filter(ee.Filter.eq('relativeOrbitNumber_start', o));
    var orbitMedian = sub.median();                        // per-pixel, this orbit
    return sub.map(function (img) {
      return ee.Image(img).subtract(orbitMedian).add(allOrbitMedian)
               .rename('VHVV_norm')
               .copyProperties(img, ['system:time_start',
                                     'relativeOrbitNumber_start']);
    });
  });

  // ImageCollection is a FeatureCollection subclass, so flatten() merges the
  // per-orbit collections back into one.
  return ee.ImageCollection(ee.FeatureCollection(perOrbit).flatten());
}

/**
 * 5-day bin composites of the normalised VH/VV ratio, on the §1.4 grid.
 *
 * Carries the same dummy-schema armor as the optical path: an empty bin must
 * export as masked rows rather than crash Export.table.toDrive with "Image has
 * no bands". Sentinel-1 gaps are far rarer than optical ones (median gap 3-7
 * days with orbits combined) but orbit gaps do occur -- East Godavari's orbit
 * 19 carried a 36-day gap in 2024 -- so the armor is retained.
 */
function buildS1Composites(normColl, year) {

  var binStarts = ee.List.sequence(CONFIG.seasonStartDOY,
                                   CONFIG.seasonEndDOY - CONFIG.binWidthDays + 1,
                                   CONFIG.binWidthDays);
  var yearStart = ee.Date.fromYMD(year, 1, 1);

  var dummy = ee.Image.constant([0, 0])
                .rename(['VHVV_med', 'valid_obs_count'])
                .updateMask(ee.Image(0));

  var composites = binStarts.map(function (doyStart) {
    doyStart = ee.Number(doyStart);
    var binStart = yearStart.advance(doyStart.subtract(1), 'day');
    var binEnd = binStart.advance(CONFIG.binWidthDays, 'day');

    var bin = normColl.filterDate(binStart, binEnd);
    var med = bin.median().rename('VHVV_med');
    var cnt = bin.count().rename('valid_obs_count');
    var armored = dummy.addBands(med.addBands(cnt), null, true);

    return armored.set({
      'year': year,
      'doy_bin_start': doyStart,
      'doy_bin_end': doyStart.add(CONFIG.binWidthDays - 1),
      'bin_index': binStarts.indexOf(doyStart)
    });
  });

  return ee.ImageCollection.fromImages(composites);
}

/**
 * Sample the composites at the committed cohort points and build the export
 * table. Mirrors compositesToTable() so the panel schema stays parallel to
 * the optical one: same keys, same bin fields, VHVV_med in place of the three
 * optical indices.
 */
function s1CompositesToTable(compositeColl, pts, districtName, year, tileId) {

  var rows = compositeColl.map(function (img) {
    img = ee.Image(img);
    var sampled = img.reduceRegions({
      collection: pts,
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
     'VHVV_med', 'valid_obs_count'],
    null, false
  );
}

// ============================================================================
// 9e. SENTINEL-1 REAL EXPORTS  (v0.7.0) -- one CSV per (district, season)
// ----------------------------------------------------------------------------
// 25 districts x 9 seasons = 225 tasks. Gated behind CONFIG.enableS1Exports.
// Refuses to run until the committed cohort asset is set, for the same reason
// §9c did: the panel must be extracted at the committed cohort, never a
// re-draw, or cell_id ceases to be a stable key across seasons.
// ============================================================================
if (CONFIG.enableS1Exports) {

  if (!CONFIG.cohortAssetPath) {
    throw new Error(
      'CONFIG.cohortAssetPath is empty. Upload docs/candidate_cohort_v2.csv as ' +
      'a PLAIN attribute table (no X/Y column mapping, so lon and lat survive ' +
      'as properties) and set this to that asset id. §9e will not export ' +
      'against an un-committed cohort.');
  }

  // Same load-and-rebuild as v0.6.1: the asset is uploaded without an X/Y
  // mapping so that lon/lat survive as properties, and the geometry is built
  // here from those exact committed coordinates.
  var s1Cohort = ee.FeatureCollection(CONFIG.cohortAssetPath).map(function (f) {
    return f.setGeometry(
      ee.Geometry.Point([ee.Number(f.get('lon')), ee.Number(f.get('lat'))]));
  });

  print('===================================================================');
  print('===   SENTINEL-1 EXPORT PATH ENABLED (Protocol §3 lead-in)       ===');
  print('===================================================================');
  print('Cohort asset:', CONFIG.cohortAssetPath);
  print('Cohort points (all districts):', s1Cohort.size());
  print('Expected tasks:', districtRecs.length * CONFIG.years.length,
        '= ' + districtRecs.length + ' districts x ' + CONFIG.years.length + ' seasons');

  var s1TaskIndex = 0;

  districtRecs.forEach(function (rec) {

    var loaded = loadDistrictGeom(rec);
    if (loaded.matchCount.getInfo() === 0) {
      print('[SKIPPED — NOT FOUND] ' + rec.state + '/' + rec.gadmName);
      return;
    }
    var geom = loaded.geom;
    var pts = s1Cohort.filter(ee.Filter.eq('district', rec.gadmName));

    CONFIG.years.forEach(function (year) {

      var seasonStart = ee.Date.fromYMD(year, 1, 1)
                          .advance(CONFIG.seasonStartDOY - 1, 'day');
      var seasonEnd = ee.Date.fromYMD(year, 1, 1)
                          .advance(CONFIG.seasonEndDOY, 'day');

      var raw = buildS1Collection(geom, seasonStart, seasonEnd);
      var norm = normaliseByOrbit(raw);
      var table = s1CompositesToTable(buildS1Composites(norm, year),
                                      pts, rec.gadmName, year, CONFIG.cohortId);

      var safeName = rec.gadmName.replace(/[^A-Za-z0-9]+/g, '_');
      var description = CONFIG.s1ExportPrefix + safeName + '_' + year;

      Export.table.toDrive({
        collection: table,
        description: description,
        folder: CONFIG.s1DriveFolder,
        fileNamePrefix: description,
        fileFormat: 'CSV'
      });

      s1TaskIndex += 1;
      print('[' + s1TaskIndex + '] Queued S1 export:', description);
    });
  });

  print('Total Sentinel-1 export tasks queued:', s1TaskIndex);
  print('Outputs land in Drive folder:', CONFIG.s1DriveFolder);
  print('Each task = 1 district-season: ' + CONFIG.cohortPointsPerDistrict +
        ' cohort points x 55 five-day bins = ' +
        (CONFIG.cohortPointsPerDistrict * 55) + ' rows.');

} else {
  print('No Sentinel-1 exports dispatched. Set CONFIG.enableS1Exports = true.');
}
