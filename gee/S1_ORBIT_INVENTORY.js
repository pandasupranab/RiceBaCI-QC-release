/**
 * ============================================================================
 * S1_ORBIT_INVENTORY.js  --  RiceBaCI-QC, go/no-go check before S1_PER_ORBIT.js
 * ----------------------------------------------------------------------------
 * RUN THIS FIRST. It creates NO export tasks and takes well under a minute.
 *
 * WHY. H1 and H2 compare a phenometric fitted SEPARATELY FROM DISTINCT
 * Sentinel-1 relative orbits. That needs at least TWO relative orbits covering
 * the same cohort points in the same season. If most district-seasons have only
 * one, S1_PER_ORBIT.js's 225 export tasks produce nothing H1 can use, and the
 * hypothesis needs rethinking rather than data.
 *
 * WHAT THE COMMITTED PANEL ALREADY IMPLIES, measured 2026-09-13. The committed
 * export is orbit-COMBINED so it cannot name orbits, but it can count scenes.
 * Over the 55 five-day bins of the DOY 150-425 window, per district-season:
 *
 *     median scenes            ~44        (stable, 2017 through 2025)
 *     bin occupancy            ~0.65      (12-day revisit predicts 0.42,
 *                                          6-day predicts 0.83)
 *     seasons with some bin
 *       holding 2+ scenes      132 of 225
 *
 * A single relative orbit repeats every 12 days, so it yields about 23 scenes
 * and 0.42 occupancy, and it can NEVER put two acquisitions inside one 5-day
 * bin. Observed is about double the scene count, and 132 seasons do contain such
 * a pair. So the panel is consistent with roughly TWO relative orbits per
 * district-season and is not consistent with one. Note also that the totals do
 * not fall after Sentinel-1B failed on 2021-12-23, which means the effective
 * revisit here never depended on S1B -- the 6-day two-satellite scenario was not
 * realised over this coast.
 *
 * That is an inference from combined data. This script measures it directly.
 *
 * HOW TO READ THE OUTPUT. One row per district-season:
 *
 *     district  year  n_orbits  orbits            passes        scenes_per_orbit
 *     Ganjam    2019  2         [33, 106]         [DESC, ASC]   [23, 22]
 *
 *   n_orbits >= 2 with both counts >= 14 in most rows
 *       -> H1 and H2 are testable. Run S1_PER_ORBIT.js.
 *   n_orbits >= 2 but one orbit thin (< 14 scenes) in most rows
 *       -> testable only on the thicker orbit pair; 14 is MIN_VALID_DEKADS, the
 *          §3.11 eligibility floor, so an orbit below it cannot be fitted at all.
 *   n_orbits == 1 in most rows
 *       -> STOP. Do not run the export. H1/H2 as written are not testable on
 *          this cohort and need a dated amendment, not 225 tasks.
 *
 * An ASCENDING/DESCENDING pair supplies the most geometrically distinct views
 * available here -- different look direction and incidence angle -- so the
 * `passes` column matters as much as the count. Distinct geometry does not make
 * the two fits' errors independent: estimator, grid and crop-state components
 * remain shared.
 *
 * Two seasons are checked, one on each side of the Sentinel-1B failure, because
 * that is the one event that could have changed orbit availability mid-panel.
 *
 * ----------------------------------------------------------------------------
 * v2, 2026-09-13 -- CORRECTED. v1 COUNTED THE WRONG THING.
 * ----------------------------------------------------------------------------
 * v1's `n_orbits_usable` counted SCENES per orbit and compared that to 14. The
 * floor it was standing in for is MIN_VALID_DEKADS = 14, which plsm_fit applies
 * to the number of DEKADS carrying an observation -- a different quantity, and
 * larger than the scene count only by accident.
 *
 * A Sentinel-1 relative orbit repeats every 12 days, so over the DOY 150-425
 * window it yields 22 or 23 passes. But `ImageCollection.size()` counts IMAGES,
 * and a district wide enough to span a frame boundary receives two or three
 * images from a single pass, at the same timestamp. v1's output shows exactly
 * that fingerprint: its scene counts cluster at 22, 23, 44, 46, 63, 66 -- the
 * 22-23 pattern and then two and three times it. So 46 scenes can be 23 passes
 * counted twice, not 46 dates, and v1 could not tell the difference. 45 of the
 * orbit-seasons it reported sit in a band where that decides whether the orbit
 * can be fitted at all: Visakhapatnam 2024 showed 18 and 17 scenes, which is
 * either 18 and 17 dates (both fittable) or 9 and 8 (neither is).
 *
 * v2 counts, per orbit, the number of DISTINCT DEKADS carrying an acquisition,
 * at actual cohort points rather than over the district polygon. Frames of the
 * same pass collapse, because they share a timestamp and therefore a dekad.
 * That is the quantity §3.11's floor governs.
 *
 * ----------------------------------------------------------------------------
 * v3, 2026-09-13 -- CORRECTED AGAIN. v2 AGGREGATED IN THE WRONG ORDER.
 * ----------------------------------------------------------------------------
 * v2 took, for each orbit, the median dekad count across three probe points, and
 * then counted the orbits clearing the floor. That is the wrong order. H1 needs
 * two fittable orbits AT A PIXEL, so the count must be formed per point and then
 * summarised across points -- not summarised per orbit and then counted.
 *
 * The two differ whenever a district straddles a swath edge, and v2's own output
 * shows it happening. Mayurbhanj 2019 came back dekads_min [0, 23, 0] against
 * dekads_med [26, 23, 24]: at the worst probe point only orbit 85 clears the
 * floor, so H1 has ONE orbit there, while the per-orbit medians report three. The
 * error inflates, never deflates, so v2's headline of 26 of 50 is an upper bound.
 *
 * v3 computes, for each probe point, how many orbits clear the floor at THAT
 * point, then reports the fraction of points with two or more. That fraction is
 * what determines H1's usable sample -- not a yes/no per district -- so it is the
 * number the amendment has to quote. The probe is widened from 3 points to 12 for
 * the same reason.
 *
 * WHAT v2 ESTABLISHED AND v3 DOES NOT CHANGE. v1 counted orbits by filtering the
 * image collection against the DISTRICT polygon. A Sentinel-1 relative orbit
 * covers a swath roughly 250 km wide, so a district can be grazed by an orbit
 * that reaches none of its cohort points -- Cuttack 2019's orbit 48 has 44 scenes
 * and zero dekads at every probe point. District-level orbit availability
 * therefore never described what a pixel sees, and v1's 44-of-50 was not a
 * measurement of anything H1 can use.
 *
 * Created 2026-09-13.
 * ============================================================================
 */

var CONFIG = {
  s1Collection: 'COPERNICUS/S1_GRD',
  cohortAssetPath: 'projects/durable-pulsar-486209-b5/assets/RiceBaCI_cohort_v2',

  // one season each side of the Sentinel-1B failure (2021-12-23)
  years: [2019, 2024],
  seasonStartDOY: 150,
  seasonEndDOY: 425,

  // Verbatim from S1_STATIC_COVARIATES.js, which ran successfully and created
  // all 25 tasks, so these asset ids, filter fields and the name map are
  // confirmed against the real assets rather than assumed.
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

var MIN_VALID_DEKADS = 14;   // §3.11 eligibility floor
var N_PROBE = 12;            // cohort points probed per district-season

var districtRecs = [];
Object.keys(CONFIG.districtsByState).forEach(function (state) {
  CONFIG.districtsByState[state].forEach(function (gadmName) {
    districtRecs.push({
      state: state, gadmName: gadmName,
      filterValue: (CONFIG.WB_NAME_MAP[gadmName] || gadmName),
      assetPath: CONFIG.riceAtlasAssetPath[state],
      filterField: CONFIG.filterField[state]
    });
  });
});

// The cohort is loaded PLAIN and geometry rebuilt from the committed lon/lat,
// for the reason recorded in S1_STATIC_COVARIATES.js: an X/Y-mapped upload gives
// every feature an empty geometry and every sample comes back null.
var cohort = ee.FeatureCollection(CONFIG.cohortAssetPath).map(function (f) {
  return f.setGeometry(
    ee.Geometry.Point([ee.Number(f.get('lon')), ee.Number(f.get('lat'))]));
});

/**
 * Orbit inventory for one district-season, built entirely SERVER-SIDE.
 *
 * Coverage is tested at the COHORT POINTS, not at the district polygon. A swath
 * can clip a district's edge and contribute an orbit that touches none of the
 * 400 sampled pixels; counting that orbit would overstate what H1 can use. So
 * each orbit's scene count is the count over the cohort's own bounding geometry.
 */
/**
 * Dekad index of an acquisition, on the §1.4 grid.
 *
 * The panel's 55 five-day bins start at seasonStartDOY and dekads pair them, so
 * dekad = floor(floor(days_since_start / 5) / 2), capped at 27 (bin 54 stands
 * alone as dekad 27). Computed from days since the season start rather than from
 * day-of-year, because the window runs past DOY 365 into the following calendar
 * year and a DOY would wrap.
 */
function dekadOf(millis, startMillis) {
  var days = ee.Number(millis).subtract(startMillis)
               .divide(86400000).floor();
  return days.divide(5).floor().divide(2).floor().min(27).max(0);
}

function inventory(rec, year) {
  var pts = cohort.filter(ee.Filter.eq('district', rec.gadmName));
  var probe = pts.randomColumn('r', 42).limit(N_PROBE, 'r');
  var probeList = probe.toList(N_PROBE);
  var roi = pts.geometry();
  var start = ee.Date.fromYMD(year, 1, 1)
                .advance(CONFIG.seasonStartDOY - 1, 'day');
  var end = ee.Date.fromYMD(year, 1, 1).advance(CONFIG.seasonEndDOY, 'day');
  var startMillis = start.millis();

  var coll = ee.ImageCollection(CONFIG.s1Collection)
    .filterBounds(roi)
    .filterDate(start, end)
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'));

  /**
   * Per probe point: how many relative orbits clear the dekad floor AT THAT
   * POINT. This is the quantity H1 needs, and forming it here -- before any
   * aggregation across points -- is the correction v3 exists to make.
   */
  var perPoint = ee.List.sequence(0, N_PROBE - 1).map(function (i) {
    var g = ee.Feature(probeList.get(i)).geometry();
    var at = coll.filterBounds(g);
    var orbs = ee.List(at.aggregate_array('relativeOrbitNumber_start'))
                 .distinct();
    var flags = orbs.map(function (o) {
      var sub = at.filter(ee.Filter.eq('relativeOrbitNumber_start', o));
      var nd = ee.List(sub.aggregate_array('system:time_start'))
                 .map(function (t) { return dekadOf(t, startMillis); })
                 .distinct().size();
      return ee.Algorithms.If(ee.Number(nd).gte(MIN_VALID_DEKADS), 1, 0);
    });
    // reduce on an empty list returns null, so guard it
    return ee.Number(ee.Algorithms.If(orbs.size().gt(0),
        ee.List(flags).reduce(ee.Reducer.sum()), 0));
  });

  var pp = ee.List(perPoint);
  var nGe2 = pp.filter(ee.Filter.gte('item', 2)).size();
  var frac = ee.Number(nGe2).divide(N_PROBE);

  // pass diversity, at the point level too: an ASC/DESC pair supplies the most
  // geometrically distinct views available here; it does not make their errors
  // independent. AP was shown to have almost none.
  var pointPasses = ee.List.sequence(0, N_PROBE - 1).map(function (i) {
    var g = ee.Feature(probeList.get(i)).geometry();
    var at = coll.filterBounds(g);
    return ee.List(at.aggregate_array('orbitProperties_pass')).distinct().size();
  });
  var nBoth = ee.List(pointPasses).filter(ee.Filter.gte('item', 2)).size();

  return ee.Feature(null, {
    state: rec.state, district: rec.gadmName, year: year,
    n_probe: N_PROBE,
    points_ge2_fittable: nGe2,
    frac_ge2_fittable: frac,
    fittable_per_point: pp,
    min_fittable: pp.reduce(ee.Reducer.min()),
    median_fittable: pp.reduce(ee.Reducer.median()),
    points_with_asc_and_desc: nBoth,
    label: ee.String(rec.gadmName).cat(' ').cat(ee.Number(year).format('%d'))
             .cat('  ').cat(ee.Number(nGe2).format('%d')).cat('/')
             .cat(ee.Number(N_PROBE).format('%d'))
             .cat(' points have >=2 fittable orbits; ')
             .cat(ee.Number(nBoth).format('%d')).cat('/')
             .cat(ee.Number(N_PROBE).format('%d'))
             .cat(' have ASC+DESC; per-point counts=')
             .cat(ee.String.encodeJSON(pp))
  });
}

var feats = [];
districtRecs.forEach(function (rec) {
  CONFIG.years.forEach(function (year) {
    feats.push(inventory(rec, year));
  });
});

print('===================================================================');
print('===  S1 ORBIT INVENTORY v3  --  go/no-go for H1 and H2           ===');
print('===================================================================');
print('v1 counted orbits against the DISTRICT polygon, which a 250 km swath can');
print('graze without reaching any cohort point. v2 fixed that but aggregated per');
print('orbit before counting. v3 counts fittable orbits AT EACH of ' + N_PROBE);
print('cohort points, then summarises. See the header for why each pass mattered.');
print('No export tasks are created by this script.');
print('');

var fc = ee.FeatureCollection(feats);

print('--- THE DECISION ---');
print('H1 needs >= 2 orbits with >= ' + MIN_VALID_DEKADS +
      ' distinct dekads AT A PIXEL.');
print('district-seasons where MOST cohort points (>= 50%) qualify:',
      fc.filter(ee.Filter.gte('frac_ge2_fittable', 0.5)).size(), 'of', fc.size());
print('district-seasons where EVERY probed point qualifies:',
      fc.filter(ee.Filter.gte('frac_ge2_fittable', 0.999)).size(), 'of', fc.size());
print('district-seasons where NO probed point qualifies:',
      fc.filter(ee.Filter.eq('points_ge2_fittable', 0)).size(), 'of', fc.size());
print('mean fraction of cohort points with >= 2 fittable orbits:',
      fc.aggregate_mean('frac_ge2_fittable'));
print('');
print('--- BY STATE: mean fraction of points with >= 2 fittable orbits ---');
['Odisha', 'West Bengal', 'Andhra Pradesh'].forEach(function (st) {
  var s = fc.filter(ee.Filter.eq('state', st));
  print('  ' + st + ':', s.aggregate_mean('frac_ge2_fittable'),
        ' rows >=50%:', s.filter(ee.Filter.gte('frac_ge2_fittable', 0.5)).size(),
        'of', s.size());
});
print('');
print('--- ROWS WHERE H1 IS NOT AVAILABLE (fewer than half the points qualify) ---');
print(fc.filter(ee.Filter.lt('frac_ge2_fittable', 0.5)).aggregate_array('label'));
print('');
print('--- ROWS WHERE IT IS AVAILABLE ---');
print(fc.filter(ee.Filter.gte('frac_ge2_fittable', 0.5)).aggregate_array('label'));
print('');
print('--- ASC/DESC PAIRING AT THE PIXEL (weaker independence without it) ---');
print('mean fraction of points seeing both passes:',
      fc.aggregate_mean('points_with_asc_and_desc'), '/ ' + N_PROBE);
print('===================================================================');
print('Send the four SUMMARY blocks above. The two lists name exactly what the');
print('H1/H2 amendment must say is and is not estimable.');
print('===================================================================');
