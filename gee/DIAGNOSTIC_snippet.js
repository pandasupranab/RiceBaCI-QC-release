// ============================================================================
// TEMP DIAGNOSTIC — paste at the VERY BOTTOM of gee/S2_QC_Ingest.js
// Set CONFIG.enableRealExports = false FIRST, or Run will queue 189 tasks.
// Queues no exports of its own. Delete this block once the question is settled.
// ============================================================================
// Compares one district-season that came out BROKEN (11 columns, no VI data)
// against one that came out GOOD (14 columns, ~5% of rows populated), using
// the current v0.6.1 code and the current cohort asset. If the broken one now
// returns data, the broken files came from a stale pre-fix dispatch and a
// clean re-run fixes them. If it returns nothing while the good one does,
// the problem is in the imagery/masking for that district-season, and a
// re-run would fail identically.
// ============================================================================
[{ d: 'Baleshwar', y: 2019, was: 'BROKEN' },
 { d: 'Ganjam',    y: 2019, was: 'GOOD'   }].forEach(function (t) {

  print('================ DIAG: ' + t.d + ' ' + t.y + ' (was ' + t.was + ') ================');

  var rec = districtRecs.filter(function (r) { return r.gadmName === t.d; })[0];
  if (!rec) { print('DIAG ERROR: ' + t.d + ' not in districtRecs'); return; }

  var geom   = loadDistrictGeom(rec).geom;
  var raMask = loadRiceAtlasMask30m(rec);

  // Same cohort load as v0.6.1 section 9c.
  var pts = ee.FeatureCollection(CONFIG.cohortAssetPath).map(function (f) {
    return f.setGeometry(
      ee.Geometry.Point([ee.Number(f.get('lon')), ee.Number(f.get('lat'))]));
  }).filter(ee.Filter.eq('district', rec.gadmName));

  print('cohort points in district (expect 400):', pts.size());
  print('first point geometry (expect a real Point):', pts.first().geometry());

  var seasonStart = ee.Date.fromYMD(t.y, 1, 1).advance(CONFIG.seasonStartDOY - 1, 'day');
  var seasonEnd   = ee.Date.fromYMD(t.y, 1, 1).advance(CONFIG.seasonEndDOY, 'day');

  // THE KEY NUMBER: how many cloud-masked S2 scenes exist for this
  // district-season at all. If this is 0, no cohort geometry could ever have
  // produced a value and the defect is upstream of the cohort.
  var maskedS2 = buildMaskedS2(geom, seasonStart, seasonEnd, raMask).map(addVIs);
  print('masked S2 scenes in season:', maskedS2.size());

  // Small slice so this stays inside the Code Editor's interactive limit:
  // 25 points x 55 bins = 1,375 rows. At the ~5% yield seen in the good
  // files, expect roughly 70 populated rows if sampling works.
  var table = compositesToTable(buildSeasonalComposites(maskedS2, t.y),
                                pts.limit(25), rec.gadmName, t.y, CONFIG.cohortId);

  print('rows built (expect 1375):', table.size());
  print('rows carrying NDVI_med:', table.filter(ee.Filter.notNull(['NDVI_med'])).size());
  print('one populated row:', table.filter(ee.Filter.notNull(['NDVI_med'])).first());
});
