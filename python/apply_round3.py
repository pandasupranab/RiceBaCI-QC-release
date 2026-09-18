"""HISTORICAL one-time source migration; not current executable analysis."""
import re

# ============================ gee/S2_QC_Ingest.js ============================
g = open('S2_QC_Ingest.js').read()

def rg(a, b, n=1):
    global g
    c = g.count(a); assert c == n, (a[:70], c)
    g = g.replace(a, b)

# ---- version header ----
rg(""" * VERSION : v0.5.1 (07 Sep 2026 — CONFIG season window corrected to
 *           DOY 150–425 per Protocol v1 §1.4; comments only otherwise.
 *           Supersedes v0.5.0 of the same day: Part 2 Step 3, §§4-8
 *           helpers restored from v0.3, real Export.table.toDrive dispatch
 *           loop wired into §9c, CONFIG.enableRealExports throw-guard
 *           replaced by live code)
""",
""" * VERSION : v0.6.0 (08 Sep 2026 — candidate-cohort export path. §9c no
 *           longer exports one reduceToVectors centroid per 25 km tile;
 *           it samples a fixed, seeded, committed cohort of candidate
 *           pixels per district (Protocol v1 §3.6) and exports one CSV per
 *           (district, season). New §9d builds and exports that cohort.
 *           Supersedes v0.5.1 (CONFIG window DOY 150–425) and v0.5.0
 *           (Part 2 Step 3: §§4-8 helpers restored from v0.3, real
 *           Export.table.toDrive dispatch loop wired into §9c))
""")

rg(""" * CHANGES FROM v0.5.0 (window correction):""",
""" * CHANGES FROM v0.5.1 (candidate cohort — Part 2 Step 3b):
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
 * CHANGES FROM v0.5.0 (window correction):""")

# ---- CONFIG additions ----
rg("""  driveFolder: 'RiceBaCI-QC_S2_exports',
  exportPrefix: 'S2_QC_',""",
"""  driveFolder: 'RiceBaCI-QC_S2_exports',
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
  // Filled in AFTER §9d's CSVs are merged, committed as
  // docs/candidate_cohort_v1.csv, and uploaded as an EE table asset.
  // §9c refuses to run while this is empty.
  cohortAssetPath: '',
  buildCohort: false,                               // true = run §9d cohort export only""")

# ---- retire buildCroplandGrid ----
rg("""function buildCroplandGrid(tileGeom, riceMask) {""",
"""// ---------------------------------------------------------------------------
// RETIRED 08 Sep 2026 (v0.6.0) — DO NOT USE. Kept for the record.
// riceMask is a CONSTANT-valued raster (loadRiceAtlasMask30m paints the
// RiceAtlas polygon with 1 and selfMasks), so reduceToVectors() returns its
// connected components: ONE centroid for a solid rice region, not one per
// pixel. Measured on Bhadrak tile01, 08 Sep 2026: 1 cell against 774,673
// rice pixels. Replaced by the §9d candidate cohort. See the CHANGES block
// at the top of this file and analysis/decisions_log.md (2026-09-08).
// ---------------------------------------------------------------------------
function buildCroplandGrid_RETIRED(tileGeom, riceMask) {""")

# ---- new cohort builder function, inserted before MAIN §9c ----
rg("""// ---- 9c. REAL EXPORTS — restored Step 3 (v0.5.0) --------------------------""",
"""// ---------------------------------------------------------------------------
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

// ---- 9c. REAL EXPORTS — cohort path (v0.6.0; supersedes v0.5.0 per-tile) --""")

# ---- replace the §9c body ----
i = g.index("if (CONFIG.enableRealExports) {\n\n  var COST_WARNING_DISTRICTS")
j = g.index("  print('No real exports dispatched. Set CONFIG.enableRealExports = true to re-enable.');\n}")
new9c = """if (CONFIG.enableRealExports) {

  if (!CONFIG.cohortAssetPath) {
    throw new Error(
      'CONFIG.cohortAssetPath is empty. Run \\u00a79d first (CONFIG.buildCohort = ' +
      'true), merge and commit docs/candidate_cohort_v1.csv, upload it as an ' +
      'Earth Engine table asset, then set CONFIG.cohortAssetPath to that asset ' +
      'id. \\u00a79c will not export against an un-committed cohort.');
  }

  var cohort = ee.FeatureCollection(CONFIG.cohortAssetPath);

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
"""
g = g[:i] + new9c + g[j:]

rg("// END — gee/S2_QC_Ingest.js  (v0.5.1)", "// END — gee/S2_QC_Ingest.js  (v0.6.0)")
open('S2_QC_Ingest.js', 'w').write(g)


# ============================== Protocol_v1.md ==============================
p = open('Protocol_v1.md').read()
def rp(a, b, n=1):
    global p
    c = p.count(a); assert c == n, (a[:70], c)
    p = p.replace(a, b)

rp("**Date locked:** to be filled at git commit time (`git commit --date` will set it).\n**Commit hash:** to be filled by the commit that adds this file to `main`.",
   "**Date locked:** 2026-09-07.\n**Commit hash:** `2cf493a` — the freezing commit for §3's QC thresholds and hypotheses on `main`. These two lines were filled by the next commit, which cannot contain its own hash; `2cf493a` remains the freeze point of record, and every later change is logged in `analysis/deviation_log.md`.")

rp("(commit `<hash>`, dated `<date>`)", "(commit `2cf493a`, dated 2026-09-07)")

rp("- Empty bins carry a dummy-schema mask row via `dummy.addBands(composite, null, true)` — never crash `Export.table.toDrive`.",
   """- Empty bins carry a dummy-schema mask row via `dummy.addBands(composite, null, true)` — never crash `Export.table.toDrive`.

**Candidate cohort (added 2026-09-08; post-freeze amendment, `analysis/deviation_log.md`).** The panel is extracted at a **fixed candidate cohort** of rice-mask pixels per district, not at every 30 m pixel and not at one point per sub-tile. For each of the 27 extracted districts, 400 pixels are drawn once from the district's RiceAtlas 30 m mask by `stratifiedSample` with seed 42 (`gee/S2_QC_Ingest.js` §9d, `CONFIG.cohortPointsPerDistrict` / `cohortSeed`), exported, committed as `docs/candidate_cohort_v1.csv`, and re-uploaded as an Earth Engine table asset that the extraction path reads. The committed file, not the seed, is authoritative: the panel does not depend on Earth Engine's random number generator remaining stable. The cohort is identical in every season, so `cell_id` is a stable per-pixel key across years by construction — which is what §3.10's balanced-composition check and §3.8's pixel-year panel require. Any change of seed, size or draw method creates a new cohort id and a new decisions-log entry; the old cohort file is never overwritten.

This mirrors Paper 1, which extracted a fixed candidate cohort of 210–453 pixels per district, static across years (RSASE-D-26-02830 §2.4, Table 1: 2,527 candidate pixels per year, 15,162 candidate pixel-years over eight districts). At 400 pixels × 27 districts × 7 seasons, Paper 2's frame is 75,600 candidate pixel-years. Density beyond a few hundred per district buys little: inference is clustered on 27 districts (§3.8), so the cluster count, not the within-district pixel count, governs the standard errors.

**Why not every pixel, and why not the previous grid.** Exporting the full mask is infeasible — East Godavari's rice mask alone is 12.6 million 30 m pixels, which at 55 bins is tens of millions of rows for one district-season. The path committed in `2cf493a` instead built its grid with `reduceToVectors(geometryType: 'centroid')` over a constant-valued mask, which returns connected components rather than pixels: measured on a Bhadrak tile on 2026-09-08, one cell against 774,673 rice pixels. That would have yielded roughly 570 arbitrary pixels for the whole study. `CONFIG.enableRealExports` was never `true`, so nothing had been extracted under it.

**Export unit.** One CSV per (district, season) — 27 × 7 = 189 tasks — replacing the per-(district, tile, season) loop, which the 25 km fishnet would have made roughly 4,000 tasks (570 rice-bearing tiles × 7 seasons). The 13-column schema of this section is unchanged; `tile_id` carries the cohort id (`cohort_v1`) rather than a 25 km sub-tile label, since the cohort is drawn district-wide. `gee/S2_QC_Ingest.js` remains the authority for what is extracted.""")

rp("1. Group all valid Sentinel-2 pixel-day observations within the season window (DOY 152–304) into 5-day DOY bins (31 bins total).",
   "1. Group all valid Sentinel-2 pixel-day observations at the district's candidate-cohort pixels (§3.6) within the season window (DOY 150–304) into 5-day DOY bins (31 bins total; bins 1–31 of the 55-bin §1.4 window).")

open('Protocol_v1.md', 'w').write(p)
print('protocol + gee patched')
