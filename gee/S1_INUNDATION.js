/**
 * ============================================================================
 * S1_INUNDATION.js -- Protocol §3.3: landfall-window inundation intensity
 * ============================================================================
 * Exports, per cohort pixel x named cyclone, the quantities §3.3 needs to score
 * inundation. It does NOT score it: the threshold must be re-derived on the 2017
 * baseline first, and that calibration belongs in Python where it can be tested.
 *
 * §3.3 verbatim, for each named cyclone c and each cohort pixel p over a +/-14-day
 * window around landfall:
 *   - sigma0_VH and sigma0_VV from COPERNICUS/S1_GRD (IW, dual-polarisation), all
 *     available relative orbits;
 *   - "A **pre-event reference** is the median sigma0_VH over the 30 days ending 5
 *     days before landfall, **on the same orbits**.";
 *   - "A pixel is scored **inundated** for cyclone c if its minimum sigma0_VH within
 *     the landfall window falls at least **3 dB** below its pre-event reference";
 *   - "The 3 dB criterion and the window length are **re-derived on the untreated
 *     2017 baseline season before use**, exactly as §3.1's r values are."
 *
 * WHY PER-ORBIT PAIRING IS NOT OPTIONAL. "On the same orbits" is the whole reason
 * this test can use absolute dB at all. Relative orbits differ in look direction and
 * incidence angle, so their sigma0_VH levels differ by more than 3 dB over the same
 * field; s1_block.js exists to normalise that away for the panel. Comparing a
 * pre-event median from orbit A against a window minimum from orbit B would measure
 * geometry, not water. So the drop is computed WITHIN each orbit that saw both
 * windows, and the exported value is the deepest such drop -- which is also the
 * right statistic for a flood that only one pass may have caught.
 *
 * WHY THE 2017 NULL ARM EXISTS. §3.3 requires the 3 dB criterion re-derived on the
 * untreated 2017 baseline. 2017 carries zero severe exposure on this roster (checked
 * against docs/district_cyclone_exposure_ibtracs50km.csv), so it supplies a clean
 * null -- but a null needs matched windows, not arbitrary ones. Every storm is
 * therefore exported twice: once at its real landfall, and once at the SAME
 * day-of-year in 2017, same district, same machinery. The 2017 arm is what a
 * no-cyclone drop distribution looks like with this instrument, and the operative
 * threshold is read off it rather than taken on trust from Bouvet et al. (2018).
 *
 * WHAT IS EXPORTED, and why scoring is left to Python:
 *   drop_db            deepest within-orbit (pre_median_VH - window_min_VH), in dB
 *   n_orbits_paired    per-pixel count of orbits present in BOTH windows
 *   n_pre, n_win       scene counts, so thin coverage is visible not silent
 *   pre_med_vh         pooled pre-event median VH, for context
 *   win_med_vh/_vv     pooled window medians -- these are §5.1's SAR_sanity_v1.csv
 *
 * A pixel with n_orbits_paired = 0 has NO paired orbit and therefore no drop. It is
 * exported with drop_db null rather than 0, because "no measurement" and "no drop"
 * are different facts and §4.3's zero-support rule says to report the difference.
 *
 * RUN ORDER, as with S1_MASK_FLAG.js: verifyOnly:true first (0 tasks, prints what
 * the catalogue actually contains), then dryRunDistrict for ONE task, then null for
 * all 25. The first version of S1_STATIC_COVARIATES.js was written without this and
 * carried three defects that would each have matched zero features.
 *
 * Created 2026-09-13, after an external re-audit found §3.3 unimplemented.
 * ============================================================================
 */

var CONFIG = {
  // MUST match the panel export exactly. Committed cohort, 25 districts x 400.
  cohortAssetPath: 'projects/durable-pulsar-486209-b5/assets/RiceBaCI_cohort_v2',
  cohortId: 'cohort_v2',

  s1Collection: 'COPERNICUS/S1_GRD',
  scaleMeters: 30,            // the panel's cell size; see S1_MASK_FLAG.js
  reduceTileScale: 16,

  // §3.3's windows, in days relative to landfall.
  winBeforeDays: 14,          // event window: [L-14, L+14]
  winAfterDays: 14,
  preEndOffsetDays: 5,        // pre-event reference ends 5 days before landfall
  preLengthDays: 30,          // ...and covers the 30 days before that

  // TWO WINDOW SPECIFICATIONS, BOTH EXPORTED. Added 2026-09-13 after the
  // Baleshwar dry run, which measured a defect in the declared one.
  //
  // §3.3 declares an event window of "+/-14 days around landfall" AND a
  // pre-event reference of "the median over the 30 days ending 5 days before
  // landfall". Those two windows OVERLAP BY 9 DAYS -- 30% of the reference --
  // and it is arithmetic, not data: reference [L-35, L-5] against event
  // [L-14, L+14] share [L-14, L-5]. Two consequences, both measured on the
  // Baleshwar export:
  //
  //   (a) An orbit whose only scenes in both windows are the same acquisition
  //       gives pre-median minus event-minimum EXACTLY 0. The export carries a
  //       point mass at exactly 0.0 on 235 of 2,400 rows (9.8%), and the mass
  //       is ARM-ASYMMETRIC: Fani 9.50% in the actual arm against 0.25% in the
  //       matched null, a factor of 38. A point mass that differs 38-fold
  //       between the two arms being compared is not a property of flooding.
  //
  //   (b) Half the declared event window lies BEFORE landfall, so the minimum
  //       that defines "inundated" can be an acquisition taken up to 14 days
  //       before the storm. A flood signature attributed to a storm cannot be
  //       measured from a scene predating it.
  //
  // §3.3's own sentence -- "the 3 dB criterion AND THE WINDOW LENGTH are
  // re-derived on the untreated 2017 baseline season before use" -- authorises
  // fixing the window as part of that calibration rather than by fiat. The
  // corrected spec keeps both declared numbers (a 14-day event span, a 30-day
  // reference ending 5 days before landfall) and only moves the event window to
  // start AT landfall, which removes the overlap and the pre-landfall minimum in
  // one change. The declared spec is exported alongside, unchanged, so the
  // protocol's own version is reported as declared and the correction is visible
  // as a difference rather than a substitution.
  windowSpecs: [
    {name: 'postlandfall', before: 0, after: 14},   // corrected; no overlap
    {name: 'declared', before: 14, after: 14}       // as §3.3 declares it
  ],

  // The 2017 matched-null arm. §3.3 requires the criterion re-derived on the
  // untreated baseline; 2017 carries zero severe exposure on this roster.
  nullYear: 2017,
  emitNullArm: true,

  driveFolder: 'RiceBaCI-QC_inundation',
  exportPrefix: 'S1_INUND_',

  // VERIFY BEFORE EXPORTING. 0 tasks; prints scene counts and one worked pixel.
  // RUN 2026-09-13 on Baleshwar. VERIFY 1-3 pass structurally: 71 rows, 25
  // districts, 400 cohort points, real Point (86.38, 21.23), 14 pre / 10 event
  // scenes on 3 orbits each with all 3 paired, pre_med_vh median -17.21 dB.
  //
  // VERIFY 4-5 IS THE CONSEQUENTIAL ONE AND ITS ANSWER IS NEGATIVE. Dana 2024,
  // a SEVERE HARVEST-WINDOW storm making landfall in this district over a
  // standing crop -- the best available test case on this coast -- against its
  // own matched 2017 window, drop_db percentiles:
  //
  //          p50     p75     p90     p95     p99
  //   ACTUAL 0.909   2.041   3.379   4.195   5.718
  //   NULL   1.115   2.120   3.371   4.123   5.277
  //
  // The null is HIGHER at the median and the quartile and the two are equal to
  // within a few tenths of a dB in the tail. Scene counts are comparable across
  // the arms (14/10 actual against 12/11 null), so the S1A+S1B revisit asymmetry
  // that would have inflated the null is not operating here -- the comparison is
  // fair and it still finds nothing. The pre-season control behaves identically
  // (Fani 2019: actual p50 1.437 / p95 5.322 against null p50 1.713 / p95 5.709).
  //
  // What this means for the criterion §3.3 declares. A 3 dB threshold sits at
  // roughly the 90th percentile of BOTH arms, so it would flag about a tenth of
  // pixels in a cyclone year and about a tenth in an untreated year. It does not
  // distinguish cyclone-window flagged drops from the matched untreated-window
  // flags on this coast. Neither arm supplies field confirmation of flooding.
  //
  // HISTORICAL PRE-EXPORT NOTE. The paragraph below records the one-district
  // dry-run state. The completed 71-row comparison subsequently failed the
  // predeclared separation rule and the inundation-intensity variable was
  // withdrawn; Protocol §3.3 is the current result. Do not quote the future
  // tense below as project status.
  //
  // THIS IS NOT YET THE WITHDRAWAL. It is one storm in one district, and
  // withdrawing a declared protocol variable on n = 1 would be the same
  // under-powered reasoning this protocol refuses elsewhere. The full export
  // gives all 71 storm-district rows a matched null, and
  // python/inundation_intensity.py decides it there across every row. The
  // expected verdict is withdrawal by dated amendment; the point of running the
  // export anyway is that "the criterion separates nothing, measured on 71 rows
  // against 71 matched nulls" is a reportable result, and "we did not test it"
  // is not.
  // BACK TO true 2026-09-13 after the Baleshwar dry run found the window-overlap
  // defect. The script now exports two window specifications and a new
  // win_min_day_off band; those are structural changes and must be verified
  // before any task is spent again. The dry-run CSV that found the defect is not
  // wasted -- it is what the correction is measured against.
  verifyOnly: true,
  // Then ONE task, so a structural defect costs one export. null for all 25.
  // CHANGED 2026-09-13 after the first verify run. 'Puri' was the original choice
  // and it is the WORST available probe: Puri's only severe storm is Fani, landfall
  // 3 May 2019 -- DOY 123, before transplanting. Fields are bare, there is no rice
  // to flood, and the measured drop is speckle. Verifying an inundation test on a
  // storm that cannot have inundated a rice crop proves nothing either way, and the
  // first run nearly produced a general conclusion from it.
  // Baleshwar carries severe PRE-SEASON storms (Fani 2019, Yaas 2021) and a severe
  // HARVEST-WINDOW storm (Dana, 24 Oct 2024) -- fields standing, flooding
  // plausible. The verify block probes both, so the comparison that decides whether
  // this variable carries any signal is visible before 25 tasks are spent.
  dryRunDistrict: 'Baleshwar',

  // The district the VERIFY block probes. Kept separate from dryRunDistrict
  // because the two answer different questions: dryRunDistrict limits the
  // EXPORT, and is set to null for the full run, whereas the probe must always
  // name a real district. The 2026-09-13 full run set dryRunDistrict to null and
  // the probe silently degraded to "none in null" -- the verify block reported
  // nothing on the run that mattered most. Must be a district carrying BOTH a
  // severe pre-season and a severe harvest-window storm, so the control and the
  // test are both available; Baleshwar is one of eleven that do.
  probeDistrict: 'Baleshwar'
};

// ---------------------------------------------------------------------------
// Landfall table, generated from the committed exposure catalogue
// docs/district_cyclone_exposure_ibtracs50km.csv on 2026-09-13 -- 71 rows, every
// named storm that exposes a roster district in 2017-2025, both severity classes.
// NOT retyped by hand: emitted programmatically so it cannot drift from the
// catalogue. `sev` and `tc` are carried through so the consumer can subset without
// re-joining, and are never used to filter here -- §3.3 says "each named cyclone".
// ---------------------------------------------------------------------------
var LANDFALL = [
  {d:"Gajapati", s:"DAYE", y:2018, t:"2018-09-20", sev:"minor", tc:"mid_season"},
  {d:"Ganjam", s:"DAYE", y:2018, t:"2018-09-20", sev:"minor", tc:"mid_season"},
  {d:"Puri", s:"DAYE", y:2018, t:"2018-09-20", sev:"minor", tc:"mid_season"},
  {d:"Srikakulam", s:"DAYE", y:2018, t:"2018-09-20", sev:"minor", tc:"mid_season"},
  {d:"East Godavari", s:"PHETHAI", y:2018, t:"2018-12-17", sev:"minor", tc:"harvest_window"},
  {d:"Visakhapatnam", s:"PHETHAI", y:2018, t:"2018-12-17", sev:"minor", tc:"harvest_window"},
  {d:"West Godavari", s:"PHETHAI", y:2018, t:"2018-12-17", sev:"minor", tc:"harvest_window"},
  {d:"Cuttack", s:"TITLI", y:2018, t:"2018-10-11", sev:"severe", tc:"harvest_window"},
  {d:"Gajapati", s:"TITLI", y:2018, t:"2018-10-11", sev:"severe", tc:"harvest_window"},
  {d:"Ganjam", s:"TITLI", y:2018, t:"2018-10-11", sev:"severe", tc:"harvest_window"},
  {d:"Nayagarh", s:"TITLI", y:2018, t:"2018-10-11", sev:"severe", tc:"harvest_window"},
  {d:"Srikakulam", s:"TITLI", y:2018, t:"2018-10-10", sev:"severe", tc:"harvest_window"},
  {d:"Vizianagaram", s:"TITLI", y:2018, t:"2018-10-11", sev:"severe", tc:"harvest_window"},
  {d:"North 24 Parganas", s:"BULBUL:MATMO", y:2019, t:"2019-11-09", sev:"severe", tc:"harvest_window"},
  {d:"South 24 Parganas", s:"BULBUL:MATMO", y:2019, t:"2019-11-09", sev:"severe", tc:"harvest_window"},
  {d:"Baleshwar", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Bhadrak", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Cuttack", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Ganjam", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Haora", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Hugli", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Jagatsinghapur", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Jajapur", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Kendrapara", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Khordha", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Mayurbhanj", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Nayagarh", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"North 24 Parganas", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Pashchim Medinipur", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Purba Medinipur", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Puri", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"South 24 Parganas", s:"FANI", y:2019, t:"2019-05-03", sev:"severe", tc:"pre_season"},
  {d:"Haora", s:"AMPHAN", y:2020, t:"2020-05-20", sev:"severe", tc:"pre_season"},
  {d:"Hugli", s:"AMPHAN", y:2020, t:"2020-05-20", sev:"severe", tc:"pre_season"},
  {d:"North 24 Parganas", s:"AMPHAN", y:2020, t:"2020-05-20", sev:"severe", tc:"pre_season"},
  {d:"Purba Medinipur", s:"AMPHAN", y:2020, t:"2020-05-20", sev:"severe", tc:"pre_season"},
  {d:"South 24 Parganas", s:"AMPHAN", y:2020, t:"2020-05-20", sev:"severe", tc:"pre_season"},
  {d:"Gajapati", s:"GULAB:SHAHEEN-GU", y:2021, t:"2021-09-26", sev:"minor", tc:"mid_season"},
  {d:"Srikakulam", s:"GULAB:SHAHEEN-GU", y:2021, t:"2021-09-26", sev:"minor", tc:"mid_season"},
  {d:"Visakhapatnam", s:"GULAB:SHAHEEN-GU", y:2021, t:"2021-09-26", sev:"minor", tc:"mid_season"},
  {d:"Vizianagaram", s:"GULAB:SHAHEEN-GU", y:2021, t:"2021-09-26", sev:"minor", tc:"mid_season"},
  {d:"Baleshwar", s:"YAAS", y:2021, t:"2021-05-26", sev:"severe", tc:"pre_season"},
  {d:"Bhadrak", s:"YAAS", y:2021, t:"2021-05-26", sev:"severe", tc:"pre_season"},
  {d:"Kendrapara", s:"YAAS", y:2021, t:"2021-05-26", sev:"severe", tc:"pre_season"},
  {d:"Mayurbhanj", s:"YAAS", y:2021, t:"2021-05-26", sev:"severe", tc:"pre_season"},
  {d:"Pashchim Medinipur", s:"YAAS", y:2021, t:"2021-05-26", sev:"severe", tc:"pre_season"},
  {d:"East Godavari", s:"ASANI", y:2022, t:"2022-05-11", sev:"minor", tc:"pre_season"},
  {d:"Guntur", s:"ASANI", y:2022, t:"2022-05-11", sev:"minor", tc:"pre_season"},
  {d:"Krishna", s:"ASANI", y:2022, t:"2022-05-11", sev:"minor", tc:"pre_season"},
  {d:"West Godavari", s:"ASANI", y:2022, t:"2022-05-11", sev:"minor", tc:"pre_season"},
  {d:"North 24 Parganas", s:"UNNAMED", y:2022, t:"2022-08-19", sev:"minor", tc:"mid_season"},
  {d:"Purba Medinipur", s:"UNNAMED", y:2022, t:"2022-08-19", sev:"minor", tc:"mid_season"},
  {d:"South 24 Parganas", s:"UNNAMED", y:2022, t:"2022-08-19", sev:"minor", tc:"mid_season"},
  {d:"Guntur", s:"MICHAUNG", y:2023, t:"2023-12-05", sev:"severe", tc:"harvest_window"},
  {d:"Krishna", s:"MICHAUNG", y:2023, t:"2023-12-05", sev:"minor", tc:"harvest_window"},
  {d:"Baleshwar", s:"DANA", y:2024, t:"2024-10-24", sev:"severe", tc:"harvest_window"},
  {d:"Bhadrak", s:"DANA", y:2024, t:"2024-10-24", sev:"severe", tc:"harvest_window"},
  {d:"Jagatsinghapur", s:"DANA", y:2024, t:"2024-10-24", sev:"severe", tc:"harvest_window"},
  {d:"Jajapur", s:"DANA", y:2024, t:"2024-10-24", sev:"severe", tc:"harvest_window"},
  {d:"Kendrapara", s:"DANA", y:2024, t:"2024-10-24", sev:"severe", tc:"harvest_window"},
  {d:"Mayurbhanj", s:"DANA", y:2024, t:"2024-10-25", sev:"severe", tc:"harvest_window"},
  {d:"North 24 Parganas", s:"REMAL", y:2024, t:"2024-05-26", sev:"severe", tc:"pre_season"},
  {d:"South 24 Parganas", s:"REMAL", y:2024, t:"2024-05-26", sev:"severe", tc:"pre_season"},
  {d:"East Godavari", s:"MONTHA", y:2025, t:"2025-10-28", sev:"severe", tc:"harvest_window"},
  {d:"Krishna", s:"MONTHA", y:2025, t:"2025-10-28", sev:"severe", tc:"harvest_window"},
  {d:"West Godavari", s:"MONTHA", y:2025, t:"2025-10-28", sev:"severe", tc:"harvest_window"},
  {d:"Gajapati", s:"UNNAMED", y:2025, t:"2025-10-02", sev:"minor", tc:"harvest_window"},
  {d:"Ganjam", s:"UNNAMED", y:2025, t:"2025-10-02", sev:"minor", tc:"harvest_window"},
  {d:"Khordha", s:"UNNAMED", y:2025, t:"2025-10-02", sev:"minor", tc:"harvest_window"},
  {d:"Puri", s:"UNNAMED", y:2025, t:"2025-10-02", sev:"minor", tc:"harvest_window"},
  {d:"Srikakulam", s:"UNNAMED", y:2025, t:"2025-10-02", sev:"minor", tc:"harvest_window"},];

// ---------------------------------------------------------------------------
// cohort: loaded PLAIN, geometry rebuilt from the committed lon/lat.
// The asset was uploaded without an X/Y mapping, so lon/lat are PROPERTIES and
// every feature's geometry is empty. S1_MASK_FLAG.js's VERIFY 3 died on exactly
// this on 2026-09-13 -- the file's own header warned of it and the warning was not
// applied. Rebuild first, always, before any spatial operation.
// ---------------------------------------------------------------------------
if (!CONFIG.cohortAssetPath) {
  throw new Error('CONFIG.cohortAssetPath is empty.');
}
var cohort = ee.FeatureCollection(CONFIG.cohortAssetPath).map(function (f) {
  return f.setGeometry(
    ee.Geometry.Point([ee.Number(f.get('lon')), ee.Number(f.get('lat'))]));
});

var S1 = ee.ImageCollection(CONFIG.s1Collection)
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'));

function shiftYear(dateStr, year) {
  // Same month and day, different year: the matched-null window.
  var d = ee.Date(dateStr);
  return ee.Date.fromYMD(year, d.get('month'), d.get('day'));
}

/**
 * Per-orbit drop for one district x storm x arm.
 * Returns an image with bands drop_db, n_orbits_paired, pre_med_vh, win_med_vh,
 * win_med_vv, plus scalars n_pre / n_win as properties.
 */
function dropImage(geom, landfall, spec) {
  spec = spec || CONFIG.windowSpecs[0];
  var winStart = landfall.advance(-spec.before, 'day');
  var winEnd = landfall.advance(spec.after, 'day');
  var preEnd = landfall.advance(-CONFIG.preEndOffsetDays, 'day');
  var preStart = preEnd.advance(-CONFIG.preLengthDays, 'day');

  var base = S1.filterBounds(geom);
  var pre = base.filterDate(preStart, preEnd);
  var win = base.filterDate(winStart, winEnd);

  // Orbits present in BOTH windows -- the pairing §3.3 requires.
  var winOrbits = win.aggregate_array('relativeOrbitNumber_start').distinct();
  var paired = pre.aggregate_array('relativeOrbitNumber_start').distinct()
                  .filter(ee.Filter.inList('item', winOrbits));

  // Days from landfall to each scene, carried as a band so the DATE of the
  // window minimum survives the reduction. Without it there is no way to check
  // whether the minimum that defines "inundated" came before or after the storm
  // -- which is precisely the defect the declared window hides. `qualityMosaic`
  // on the negated VH picks, per pixel, the scene with the lowest VH and takes
  // its day offset along with it.
  var winDated = win.map(function (im) {
    // updateMask to VH's own mask: a constant band is valid everywhere, and an
    // unmasked day offset sitting under a masked VH would let a pixel report a
    // date for a scene that had no data there.
    var dd = ee.Image.constant(
      ee.Date(im.get('system:time_start')).difference(landfall, 'day'))
      .toFloat().rename('win_min_day_off')
      .updateMask(im.select('VH').mask());
    return im.select('VH').addBands(dd)
             .addBands(im.select('VH').multiply(-1).rename('negVH'))
             .copyProperties(im, ['relativeOrbitNumber_start',
                                  'system:time_start']);
  });

  var perOrbit = ee.ImageCollection(ee.List(paired).map(function (o) {
    o = ee.Number(o);
    var pm = pre.filter(ee.Filter.eq('relativeOrbitNumber_start', o))
                .select('VH').median();
    var wo = winDated.filter(ee.Filter.eq('relativeOrbitNumber_start', o));
    var wq = wo.qualityMosaic('negVH');          // the lowest-VH scene per pixel
    var wm = wq.select('VH');
    // pre median minus window minimum: positive where backscatter fell.
    return pm.subtract(wm).rename('drop_db')
             .addBands(wq.select('win_min_day_off'));
  }));

  // max over orbits: the deepest drop any paired pass saw. count(): per-PIXEL
  // number of paired orbits with data, not a district-wide constant, so thin
  // coverage shows up per pixel.
  // The orbit with the deepest drop wins, and its day offset comes with it, so
  // win_min_day_off always describes the scene that produced the reported drop.
  var best = perOrbit.qualityMosaic('drop_db');
  var drop = best.select('drop_db');
  var dayOff = best.select('win_min_day_off');
  var nOrb = perOrbit.select('drop_db').count().rename('n_orbits_paired')
                     .unmask(0).toInt16();

  var img = drop
    .addBands(nOrb)
    .addBands(dayOff)
    .addBands(pre.select('VH').median().rename('pre_med_vh'))
    .addBands(win.select('VH').median().rename('win_med_vh'))
    .addBands(win.select('VV').median().rename('win_med_vv'));

  return img.set({
    n_pre: pre.size(), n_win: win.size(),
    n_orbits_pre: pre.aggregate_array('relativeOrbitNumber_start')
                     .distinct().size(),
    n_orbits_win: winOrbits.size(),
    n_orbits_paired_scenes: ee.List(paired).size(),
    win_start: winStart.format('YYYY-MM-dd'),
    win_end: winEnd.format('YYYY-MM-dd'),
    pre_start: preStart.format('YYYY-MM-dd'),
    pre_end: preEnd.format('YYYY-MM-dd'),
    window_spec: spec.name,
    // Overlap between the reference and the event window, in days. 0 is the
    // only acceptable value; the declared spec reports 9.
    overlap_days: preEnd.difference(winStart, 'day').max(0)
  });
}

var COLS = ['district', 'tile_id', 'cell_id', 'storm', 'season', 'arm',
            'severity_class', 'timing_class', 'landfall_date',
            'window_spec', 'overlap_days',
            'drop_db', 'win_min_day_off', 'n_orbits_paired',
            'pre_med_vh', 'win_med_vh', 'win_med_vv', 'n_pre', 'n_win'];

function sampleUnit(rec, arm, spec) {
  spec = spec || CONFIG.windowSpecs[0];
  var pts = cohort.filter(ee.Filter.eq('district', rec.d));
  var lf = (arm === 'actual') ? ee.Date(rec.t)
                              : shiftYear(rec.t, CONFIG.nullYear);
  var img = dropImage(pts.geometry(), lf, spec);
  return img.reduceRegions({
    collection: pts,
    reducer: ee.Reducer.first(),
    scale: CONFIG.scaleMeters,
    tileScale: CONFIG.reduceTileScale
  }).map(function (f) {
    return f.set({
      district: rec.d, tile_id: CONFIG.cohortId,
      storm: rec.s, season: rec.y, arm: arm,
      severity_class: rec.sev, timing_class: rec.tc,
      landfall_date: lf.format('YYYY-MM-dd'),
      window_spec: spec.name,
      overlap_days: img.get('overlap_days'),
      n_pre: img.get('n_pre'), n_win: img.get('n_win')
    });
  });
}

// ---------------------------------------------------------------------------
// VERIFICATION BLOCK -- runs first, always, and creates no tasks.
// Answers the questions CONFIG assumes the answers to, on one worked unit.
// ---------------------------------------------------------------------------
print('===================================================================');
print('===  S1 INUNDATION  (Protocol §3.3 intensity variable)           ===');
print('===================================================================');

// Two probes, deliberately contrasting. A pre-season storm hits bare fields and can
// only show speckle; a harvest-window storm hits a standing crop and is the only
// case where an inundation signature is even possible. Probing one and not the other
// is how the first verify run almost concluded that §3.3's 3 dB criterion is
// unusable, on the strength of a May storm over unplanted ground.
function pickProbe(timing) {
  var want = CONFIG.probeDistrict || CONFIG.dryRunDistrict;
  for (var q = 0; q < LANDFALL.length; q++) {
    if (LANDFALL[q].d === want
        && LANDFALL[q].sev === 'severe'
        && LANDFALL[q].tc === timing) { return LANDFALL[q]; }
  }
  return null;
}
var probePre = pickProbe('pre_season');
var probeHarv = pickProbe('harvest_window');
var probeRec = probeHarv !== null ? probeHarv
             : (probePre !== null ? probePre : LANDFALL[0]);

print('--- VERIFY 1: landfall table ---');
print('  rows:', LANDFALL.length, '(expect 71)');
print('  probe unit:', probeRec.d + ' / ' + probeRec.s + ' ' + probeRec.y
      + ' (' + probeRec.sev + ', ' + probeRec.tc + ') landfall ' + probeRec.t);
print('  IF rows is not 71, the table drifted from the catalogue. STOP.');

print('--- VERIFY 2: does the cohort resolve, with real geometry? ---');
var probePts = cohort.filter(ee.Filter.eq('district', probeRec.d));
print('  cohort points in ' + probeRec.d + ':', probePts.size(), '(expect 400)');
print('  first point geometry (must NOT be an empty MultiPoint):',
      ee.Feature(probePts.first()).geometry());

print('--- VERIFY 3: scene counts in both windows, and the pairing ---');
var vimg = dropImage(probePts.geometry(), ee.Date(probeRec.t));
print('  pre window ', vimg.get('pre_start'), 'to', vimg.get('pre_end'),
      ' scenes:', vimg.get('n_pre'), ' orbits:', vimg.get('n_orbits_pre'));
print('  event window', vimg.get('win_start'), 'to', vimg.get('win_end'),
      ' scenes:', vimg.get('n_win'), ' orbits:', vimg.get('n_orbits_win'));
print('  orbits present in BOTH windows:', vimg.get('n_orbits_paired_scenes'));
print('  IF paired orbits is 0, no drop is computable for this unit and every');
print('  pixel will export drop_db null. That is a real state, not a bug, but');
print('  if it happens for MOST units the window lengths need revisiting.');

print('--- VERIFY 4 & 5: actual against its own 2017 matched null ---');
print('  Read the HARVEST-WINDOW block first. A pre-season storm lands before');
print('  transplanting, so its fields are bare and its drop is speckle by');
print('  construction -- it is a control, not a test.');

function reportUnit(rec, label) {
  if (rec === null) {
    print('  [' + label + '] none in '
          + (CONFIG.probeDistrict || CONFIG.dryRunDistrict));
    return;
  }
  for (var w = 0; w < CONFIG.windowSpecs.length; w++) {
    reportUnitSpec(rec, label, CONFIG.windowSpecs[w]);
  }
}

function reportUnitSpec(rec, label, spec) {
  var act = sampleUnit(rec, 'actual', spec);
  var nul = sampleUnit(rec, 'null2017', spec);
  var pc = ee.Reducer.percentile([50, 75, 90, 95, 99]);
  print('  [' + label + ' | window ' + spec.name + ' = L'
        + (spec.before ? '-' + spec.before : '') + ' to L+' + spec.after + ']  '
        + rec.s + ' ' + rec.y + '  landfall ' + rec.t + '   (' + rec.tc + ')');
  print('      overlap, reference vs event window, DAYS -- must be 0;'
        + ' the declared spec gives 9:',
        act.aggregate_array('overlap_days').distinct());
  print('      pixels with drop EXACTLY 0 (the overlap artefact) -- actual:',
        act.filter(ee.Filter.eq('drop_db', 0)).size(),
        ' null:', nul.filter(ee.Filter.eq('drop_db', 0)).size(),
        ' of', act.size(), 'each');
  print('      day of the window minimum relative to landfall'
        + ' (NEGATIVE = the minimum predates the storm):');
  print('        actual  ', act.reduceColumns(
      {reducer: ee.Reducer.percentile([5, 25, 50, 75, 95]),
       selectors: ['win_min_day_off']}));
  print('        null2017', nul.reduceColumns(
      {reducer: ee.Reducer.percentile([5, 25, 50, 75, 95]),
       selectors: ['win_min_day_off']}));
  print('      points:', act.size(),
        '  paired orbits present:',
        act.aggregate_array('n_orbits_paired').distinct().sort());
  // Revisit asymmetry between the arms. 2017 flew S1A+S1B (6-day repeat);
  // S1B failed 2021-12-23, so 2022-2024 are S1A only (12-day). The event window
  // statistic is a MINIMUM, so an arm with more scenes gets a deeper minimum from
  // speckle alone. If the null arm carries substantially more scenes than the
  // actual arm, the null percentiles are inflated and the comparison is biased
  // AGAINST finding signal -- read any null-exceeds-actual result with that in
  // mind, and expect the Python calibration to match scene counts per orbit.
  print('      scenes  ACTUAL   pre / event:',
        act.aggregate_array('n_pre').distinct(),
        '/', act.aggregate_array('n_win').distinct());
  print('      scenes  NULL2017 pre / event:',
        nul.aggregate_array('n_pre').distinct(),
        '/', nul.aggregate_array('n_win').distinct());
  // EXACT, COUNT-BASED STATISTICS FIRST. ee.Reducer.percentile is histogram-based
  // and its output is APPROXIMATE: on two runs of identical code over identical
  // scenes the null arm's reported p50 moved from 1.1149 to 1.0493 dB, and both
  // differ from the exact value computed on the exported CSV (1.0235). The
  // percentiles below are therefore a shape sketch and NOT measurements -- this
  // session read them as measurements twice and drew a conclusion from them once.
  // A share above a fixed threshold is a COUNT, which is exact, reproducible, and
  // is the quantity §3.3's criterion actually needs.
  print('      EXACT share of pixels at or above each threshold '
        + '(count-based; this is what the criterion uses):');
  [2, 3, 4, 5].forEach(function (thr) {
    print('        >= ' + thr + ' dB   actual:',
          act.filter(ee.Filter.gte('drop_db', thr)).size(),
          ' null:', nul.filter(ee.Filter.gte('drop_db', thr)).size(),
          ' of', act.size(), 'each');
  });
  print('      EXACT mean drop_db   actual:',
        act.reduceColumns({reducer: ee.Reducer.mean(),
                           selectors: ['drop_db']}),
        ' null:', nul.reduceColumns({reducer: ee.Reducer.mean(),
                                     selectors: ['drop_db']}));
  print('      APPROXIMATE drop_db percentiles -- shape only, +/- ~0.1 dB, '
        + 'not a measurement:');
  print('        actual  ', act.reduceColumns({reducer: pc,
                                               selectors: ['drop_db']}));
  print('        null2017', nul.reduceColumns({reducer: pc,
                                               selectors: ['drop_db']}));
  print('      pre_med_vh median (plausible -8 to -18 dB):',
        act.reduceColumns({reducer: ee.Reducer.median(),
                           selectors: ['pre_med_vh']}));
}
reportUnit(probeHarv, 'HARVEST WINDOW -- the real test');
reportUnit(probePre, 'PRE SEASON -- control, expect no signal');

print('  READ THE postlandfall SPEC. The declared +/-14 window shares 9 days with');
print('  its own reference and lets the "event" minimum predate the storm; the');
print('  Baleshwar dry run measured a point mass at exactly 0 dB on 9.8% of rows,');
print('  38x larger in Fani actual than in its matched null. The declared spec is');
print('  exported so SS3.3 is reported as declared, not because it can be read.');
print('  If the two specs disagree, the corrected one is the measurement.');
print('  NOTHING HERE IS THE VERDICT. The exact shares above are one district and,');
print('  for the harvest window, ONE storm -- below the three-unit floor at which a');
print('  null is informative at all. python/inundation_intensity.py decides it on');
print('  all 71 storm-district rows against 71 matched nulls, from the exported');
print('  CSV, with the rule fixed in its docstring before the data existed.');
print('  WHAT DECIDES THIS VARIABLE. If the harvest-window ACTUAL percentiles sit');
print('  above its own NULL percentiles, the drop statistic carries flood signal');
print('  and §3.3 works with a threshold read off the null. If ACTUAL and NULL are');
print('  indistinguishable for a harvest-window storm too, the statistic carries no');
print('  signal on this coast and §3.3 must be withdrawn by dated amendment rather');
print('  than reported as an intensity variable.');
print('  WHAT THE DRY-RUN EXPORT ALREADY MEASURED, on the DECLARED window, and');
print('  why it settles nothing. Baleshwar, 2,400 rows, 3 severe storms x 2 arms:');
print('    Dana 2024 (harvest window) actual p50 0.915 vs null p50 1.024 dB');
print('    exact-zero mass  Dana 19.25% vs 10.50%, Fani 9.50% vs 0.25% (38x),');
print('                     Yaas 15.25% vs 4.00%');
print('  The arms are contaminated to DIFFERENT degrees by the window overlap, so');
print('  the actual-against-null comparison on the declared window is not a');
print('  comparison at all. That is why the corrected spec exists, and why the');
print('  earlier reading of that export as a clean negative was withdrawn.');
print('===================================================================');

if (CONFIG.verifyOnly) {
  print('*** verifyOnly is TRUE -- no export tasks created. ***');
  print('Read VERIFY 1-5. If all five match what CONFIG assumes, set');
  print('CONFIG.verifyOnly = false and re-run: that queues ONE task for '
        + CONFIG.dryRunDistrict + '. Check that CSV, then set dryRunDistrict');
  print('to null for the full 25.');
}

// ---------------------------------------------------------------------------
// Export: one task per district, all its storms and both arms in one table.
// ---------------------------------------------------------------------------
var districts = {};
for (var i = 0; i < LANDFALL.length; i++) { districts[LANDFALL[i].d] = true; }
var districtList = Object.keys(districts).sort();
print('districts in the landfall table:', districtList.length, '(expect 25)');

var DRY = (CONFIG.dryRunDistrict !== null && CONFIG.dryRunDistrict !== undefined);
var taskIndex = 0;
for (var k = 0; k < districtList.length; k++) {
  var dist = districtList[k];
  if (CONFIG.verifyOnly) { break; }
  if (DRY && dist !== CONFIG.dryRunDistrict) { continue; }

  var parts = [];
  for (var j = 0; j < LANDFALL.length; j++) {
    if (LANDFALL[j].d !== dist) { continue; }
    for (var w = 0; w < CONFIG.windowSpecs.length; w++) {
      var sp = CONFIG.windowSpecs[w];
      parts.push(sampleUnit(LANDFALL[j], 'actual', sp));
      if (CONFIG.emitNullArm) {
        parts.push(sampleUnit(LANDFALL[j], 'null2017', sp));
      }
    }
  }
  if (parts.length === 0) { continue; }
  var merged = ee.FeatureCollection(parts).flatten();
  var safeName = dist.replace(/[^A-Za-z0-9]+/g, '_');
  var description = CONFIG.exportPrefix + safeName;

  Export.table.toDrive({
    collection: merged.select(COLS, null, false),
    description: description,
    folder: CONFIG.driveFolder,
    fileNamePrefix: description,
    fileFormat: 'CSV',
    selectors: COLS          // REQUIRED. Without it Earth Engine infers the
                             // header from leading features and an all-null
                             // leading block silently drops columns from the
                             // whole file -- the v0.7.1 defect.
  });
  taskIndex += 1;
  var narms = CONFIG.emitNullArm ? 2 : 1;
  var nspec = CONFIG.windowSpecs.length;
  print('[TASK ' + taskIndex + '] ' + description
        + '   (' + (parts.length / (narms * nspec))
        + ' storms x ' + narms + ' arms x ' + nspec + ' window specs)');
}

var expected = CONFIG.verifyOnly ? 0 : (DRY ? 1 : districtList.length);
print('-------------------------------------------------------------------');
print('Tasks created:', taskIndex, '(expected ' + expected + ')');
print('Drive folder:', CONFIG.driveFolder);
if (!CONFIG.verifyOnly && taskIndex !== expected) {
  print('*** STOP. ' + (expected - taskIndex) + ' district(s) produced no task.');
}
print('NOTE: this script SCORES NOTHING. §3.3 requires the 3 dB criterion');
print('      re-derived on the untreated 2017 baseline, so the threshold is set');
print('      in python/inundation_intensity.py against the null arm exported');
print('      here, and inundated_frac is computed there.');
