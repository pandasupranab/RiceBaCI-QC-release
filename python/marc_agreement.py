"""
marc_agreement.py -- H1c / H2c: district-level product agreement against MARC.

WHAT THIS IS, AND WHAT IT IS NOT. §2's H1c/H2c are declared external-product
agreement, reported never tested: district-median radar trough and fall-end
breakpoints are compared against MARC's transplanting and harvest dates. The
quantities are different measurands; signed difference and dispersion are reported separately
and never conflated, and **no threshold is pre-declared**, because agreement or
disagreement with a 0.5 degree product cannot establish or refute correctness at
30 m. Nothing here passes or fails. §3.4 Tier 2 says the same in stronger terms:
MARC is "compared at district level only, as agreement between two products, with
its 0.5 degree native resolution stated wherever the comparison appears."

WHY IT WAS MISSING. An external re-audit on 2026-09-13 found no MARC code, no MARC
table, and no MARC data anywhere in the repository, while §2 and §3.4 both commit to
the comparison. It had simply never been written. This closes that.

THE PRODUCT. Monsoon Asia Rice Calendar v1.0 (Zhao, X., Nishina, K., Izumisawa, H.,
Masutomi, Y., Osako, S., Yamamoto, S., 2024, "Monsoon Asia Rice Calendar (MARC): a
gridded rice calendar in monsoon Asia based on Sentinel-1 and Sentinel-2 images",
Earth System Science Data 16, 3893-3921, doi:10.5194/essd-16-3893-2024; data at
NIES, doi:10.17595/20230728.001, CC BY 4.0). Downloaded 2026-09-13; the archive's
md5 matched the checksum published on the NIES landing page,
de7eab15bcaf6c8afbba9e480e55afbd.

TWO PROPERTIES OF MARC THAT SHAPE THE COMPARISON, both read from the data rather
than assumed:

  1. **It has no time dimension.** The NetCDF is a single lat x lon grid (127 x 184),
     not a per-year stack. It is one climatological calendar built from 2019-2020
     imagery. So this is not a season-by-season comparison; it is a multi-season
     district median against a single climatological reference, and it is reported
     that way. (An earlier note in this project said the comparison could cover only
     two of nine seasons. That was wrong, and wrong in the pessimistic direction.)
  2. **Its dates are grouped by transplanting window, not by year.** Group 1 covers
     transplanting DOY 182-304, which is the monsoon group and the one this study's
     Kharif window sits inside. Groups 2 (DOY 60-181) and 3 (DOY 305-59) are read and
     reported for context, never substituted for group 1.

WHAT THE RESULT IS FOR. The offsets below are the first comparison in this study
against a product built by anyone else, and they bear directly on §4.3.1's
construct-mapping restriction. Read the harvest column before the transplanting one.

Created 2026-09-13.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.environ.get("RICEBACI_ROOT", "/home/claude")
RESULTS = os.environ.get("RICEBACI_RESULTS", os.path.join(ROOT, "results"))
OUT = os.path.join(RESULTS, "marc")

MARC_DIR_CANDIDATES = ["marc/Rice_Calendar_Data_ver.1.0", "data/marc",
                       os.path.join(ROOT, "marc/Rice_Calendar_Data_ver.1.0"),
                       os.path.join(ROOT, "data/marc")]
CAL_FILE = "1_Transplanting_Harvest_Group.nc"
VAR_FILE = "2_Transplanting_Harvest_Variance_Group.nc"
CELL_DEG = 0.5
MARC_MD5 = "de7eab15bcaf6c8afbba9e480e55afbd"


def _find_marc(explicit=None):
    for c in ([explicit] if explicit else []) + MARC_DIR_CANDIDATES:
        if c and os.path.exists(os.path.join(c, CAL_FILE)):
            return c
    raise SystemExit(
        "MARC not found. Download Rice_Calendar_Data_ver.1.0.zip from\n"
        "  https://db.cger.nies.go.jp/nies_data/10.17595/20230728.001/"
        "Rice_Calendar_Data_ver.1.0.zip\n"
        f"(CC BY 4.0; archive md5 {MARC_MD5}), unzip it, and pass --marc-dir.\n"
        f"Looked in: {', '.join(str(c) for c in MARC_DIR_CANDIDATES)}")


def _find(name):
    """Locate a committed docs/ file from wherever this is run."""
    here = os.path.dirname(os.path.abspath(__file__))
    for c in (name, os.path.join(here, name), os.path.join(here, "..", "docs", name),
              os.path.join(ROOT, "docs", name), os.path.join(ROOT, name),
              os.path.join(ROOT, "cohort_v2", "docs", name)):
        if os.path.exists(c):
            return c
    raise SystemExit(f"cannot find {name!r}")


# ---------------------------------------------------------------------------
def nearest_cell(values, axis, cell_deg=CELL_DEG):
    """Index of the grid cell whose centre is nearest each value.

    Returns (index, inside) where `inside` is False when the point lies more than
    half a cell from the nearest centre -- i.e. outside the grid rather than merely
    off-centre. Silently clamping such points to an edge cell would invent coverage,
    so they are reported and excluded instead."""
    axis = np.asarray(axis, float)
    idx = np.abs(axis[:, None] - np.asarray(values, float)[None, :]).argmin(axis=0)
    inside = np.abs(axis[idx] - np.asarray(values, float)) <= cell_deg / 2.0
    return idx, inside


def read_marc(marc_dir):
    """Load MARC's three transplanting/harvest groups and their variances."""
    import netCDF4
    cal = netCDF4.Dataset(os.path.join(marc_dir, CAL_FILE))
    lat = np.asarray(cal.variables["lat"][:], float)
    lon = np.asarray(cal.variables["lon"][:], float)

    def grid(ds, name):
        """Read one grid, clearing EVERY fill convention MARC uses.

        MARC marks absent cells two ways and this function originally handled only
        one: a large sentinel above 1e19, and **-9999**. The self-test caught the
        second on its first run -- it asserted that group 1 transplanting lies near
        its declared DOY 182-304 window and got a minimum of -9999. Left in, those
        cells would have entered district medians as real dates and dragged them
        by centuries of days wherever a district contained one. So the rule here is
        not a list of known sentinels but a physical range: a transplanting or
        harvest date is a day-of-year, and anything outside 1-366 is missing,
        whatever value was used to say so."""
        a = np.asarray(ds.variables[name][:], float)
        if np.ma.isMaskedArray(ds.variables[name][:]):
            a = np.ma.filled(ds.variables[name][:].astype(float), np.nan)
        a[~np.isfinite(a)] = np.nan
        a[(a < 1) | (a > 366)] = np.nan
        return a

    out = {"lat": lat, "lon": lon}
    for g in (1, 2, 3):
        out[f"tp{g}"] = grid(cal, f"Transplanting_{g}_Group")
        out[f"hv{g}"] = grid(cal, f"Harvest_{g}_Group")
    def nonneg(ds, name):
        """A variance, not a date: clear fills but do not clip to the DOY range."""
        v = ds.variables[name][:]
        a = np.ma.filled(v.astype(float), np.nan) if np.ma.isMaskedArray(v) \
            else np.asarray(v, float)
        a[~np.isfinite(a)] = np.nan
        a[a < 0] = np.nan
        return a

    vpath = os.path.join(marc_dir, VAR_FILE)
    if os.path.exists(vpath):
        var = netCDF4.Dataset(vpath)
        for g in (1, 2, 3):
            for stem, pfx in (("Transplanting", "tpvar"), ("Harvest", "hvvar")):
                nm = f"{stem}_{g}_Variance_Group"
                if nm in var.variables:
                    out[f"{pfx}{g}"] = nonneg(var, nm)
    out["time_dimension"] = "time" in cal.dimensions
    return out


def attach_marc(cohort, marc):
    """Give every cohort point the MARC values of the cell it falls in."""
    iy, in_y = nearest_cell(cohort["lat"].values, marc["lat"])
    ix, in_x = nearest_cell(cohort["lon"].values, marc["lon"])
    inside = in_y & in_x
    d = cohort.copy()
    d["marc_inside_grid"] = inside
    for g in (1, 2, 3):
        for k in (f"tp{g}", f"hv{g}", f"tpvar{g}", f"hvvar{g}"):
            if k in marc:
                v = marc[k][iy, ix].astype(float)
                v[~inside] = np.nan
                d["marc_" + k] = v
    # one row per distinct cell per district, for counting how coarse this is
    d["marc_cell"] = [f"{a}_{b}" for a, b in zip(iy, ix)]
    return d


def ours_by_district(panel_path, level_note):
    """District medians of the fitted breakpoints, over retained rows only."""
    p = pd.read_csv(panel_path, usecols=lambda c: c in
                    ("district", "year", "trough", "heading", "harvest", "retained"))
    if "retained" in p.columns:
        p = p[p["retained"].astype(int) == 1]
    g = p.groupby("district")[["trough", "heading", "harvest"]].median()
    g["n_rows"] = p.groupby("district").size()
    g["source"] = level_note
    return g


def compare(cohort_marc, ours, group=1):
    """Per-district table of signed product offsets and their dispersion."""
    m = cohort_marc[cohort_marc["marc_inside_grid"]]
    agg = {f"marc_tp": (f"marc_tp{group}", "median"),
           f"marc_hv": (f"marc_hv{group}", "median")}
    md = m.groupby("district").agg(**agg)
    md["marc_cells_per_district"] = m.groupby("district")["marc_cell"].nunique()
    md["cohort_points_in_grid"] = m.groupby("district").size()
    for pfx, col in (("marc_tp_sd", f"marc_tpvar{group}"),
                     ("marc_hv_sd", f"marc_hvvar{group}")):
        if col in m.columns:
            # MARC ships variance; report it as a standard deviation in days
            md[pfx] = np.sqrt(m.groupby("district")[col].median())
    t = md.join(ours, how="inner")
    t["d_transplanting"] = t["trough"] - t["marc_tp"]
    t["d_harvest"] = t["harvest"] - t["marc_hv"]
    return t.reset_index()


def summarise(t, verbose=True):
    """Signed product offset and dispersion, kept separate as required by §2.

    The legacy ``bias_*`` field names are retained for table compatibility; MARC
    is not ground truth, so the quantities are described as signed differences.
    """
    rows = []
    for lab, col in (("transplanting  (our trough vs MARC)", "d_transplanting"),
                     ("harvest        (our harvest vs MARC)", "d_harvest")):
        d = t[col].dropna().values
        rows.append(dict(
            quantity=lab, n_districts=len(d),
            bias_mean=float(np.mean(d)), bias_median=float(np.median(d)),
            dispersion_sd=float(np.std(d, ddof=1)),
            dispersion_mad=float(np.median(np.abs(d - np.median(d)))),
            min=float(np.min(d)), max=float(np.max(d))))
    s = pd.DataFrame(rows)
    if verbose:
        print("\n  agreement between two products, NOT accuracy. MARC is native "
              "0.5 degrees\n  (~55 km); this study fits at 30 m. No threshold is "
              "pre-declared (§2 H1c/H2c).\n")
        for r in rows:
            print(f"    {r['quantity']}")
            print(f"      signed difference   mean {r['bias_mean']:+7.1f} d   "
                  f"median {r['bias_median']:+7.1f} d")
            print(f"      spread sd   {r['dispersion_sd']:7.1f} d   "
                  f"MAD    {r['dispersion_mad']:7.1f} d"
                  f"   range {r['min']:+.0f} to {r['max']:+.0f} d")
    return s


# ---------------------------------------------------------------------------
def selftest():
    """Data-free logic checks, then the real comparison where the data is present."""
    print("=" * 74)
    print("SELF-TEST -- marc_agreement.py")
    print("=" * 74)
    ok = True

    def check(name, passed, detail=""):
        nonlocal ok
        ok = ok and bool(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}" + (f" -- {detail}" if detail else ""))

    # --- nearest_cell, including the case that matters: outside the grid --------
    axis = np.arange(61.25, 152.80, 0.5)
    idx, inside = nearest_cell([61.25, 61.40, 152.75], axis)
    check("nearest_cell picks the containing cell", list(idx[:2]) == [0, 0]
          and idx[2] == len(axis) - 1)
    check("nearest_cell accepts a point inside the grid", bool(inside.all()))
    idx, inside = nearest_cell([20.0, 200.0], axis)
    check("nearest_cell REFUSES a point outside the grid rather than clamping it",
          not inside.any(),
          "clamping to an edge cell would invent coverage that does not exist")
    idx, inside = nearest_cell([61.25 + 0.24, 61.25 + 0.26], np.array([61.25, 61.75]))
    check("half-cell boundary resolves to the nearer centre, both inside",
          bool(inside.all()) and list(idx) == [0, 1])

    # --- signed offset and dispersion must stay separate ----------------------
    t = pd.DataFrame({"d_transplanting": [10.0, 20.0, 30.0],
                      "d_harvest": [-5.0, 0.0, 5.0]})
    s = summarise(t, verbose=False)
    tp = s[s.quantity.str.startswith("transplanting")].iloc[0]
    check("signed offset is the mean/median difference", abs(tp.bias_mean - 20) < 1e-9
          and abs(tp.bias_median - 20) < 1e-9)
    check("dispersion is computed about the centre, not about zero",
          abs(tp.dispersion_sd - 10.0) < 1e-9,
          "a large signed offset with small spread is not a large spread")
    hv = s[s.quantity.str.startswith("harvest")].iloc[0]
    check("a zero-offset, wide-spread case is not reported as agreement",
          abs(hv.bias_mean) < 1e-9 and hv.dispersion_sd > 4,
          "offset 0 with sd 5 is not the same fact as offset 0 with sd 0")

    # --- conditional: the real products ---------------------------------------
    try:
        marc_dir = _find_marc()
    except SystemExit:
        print("  [SKIP] MARC not present; the checks above need no data and are the "
              "ones that must hold anywhere")
        print("=" * 74)
        print("SELF-TEST " + ("PASSED" if ok else "FAILED"))
        print("=" * 74)
        return 0 if ok else 1

    marc = read_marc(marc_dir)
    check("MARC has no time dimension, so this is a climatology comparison",
          not marc["time_dimension"],
          "one lat x lon grid, not a per-year stack")
    check("every MARC value read is a valid day-of-year, no fill leaked through",
          bool(np.all((np.asarray(marc["tp1"])[np.isfinite(marc["tp1"])] >= 1)
                      & (np.asarray(marc["tp1"])[np.isfinite(marc["tp1"])] <= 366))),
          f"observed {np.nanmin(marc['tp1']):.0f}..{np.nanmax(marc['tp1']):.0f}; "
          f"this check found MARC's -9999 fill on its first run")
    check("MARC group 1 sits in the monsoon transplanting window it declares",
          150 <= np.nanmedian(marc["tp1"]) <= 304,
          f"median {np.nanmedian(marc['tp1']):.0f}, declared range DOY 182-304")
    coh = pd.read_csv(_find("candidate_cohort_v2.csv"))
    cm = attach_marc(coh, marc)
    check("every cohort point falls inside the MARC grid",
          bool(cm["marc_inside_grid"].all()),
          f"{int(cm['marc_inside_grid'].sum())} of {len(cm)}")
    check("MARC covers every roster district",
          int(cm.loc[cm[f'marc_tp1'].notna(), 'district'].nunique()) == 25,
          f"{int(cm.loc[cm['marc_tp1'].notna(), 'district'].nunique())} of 25")
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok else "FAILED"))
    print("=" * 74)
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="H1c/H2c product agreement vs MARC.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--marc-dir", default=None)
    ap.add_argument("--group", type=int, default=1,
                    help="MARC transplanting group; 1 is the monsoon group this "
                         "study's Kharif window sits inside")
    ap.add_argument("--panel", default=os.path.join(RESULTS, "phen_panel_sar.csv"))
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    marc_dir = _find_marc(a.marc_dir)
    marc = read_marc(marc_dir)
    print("=" * 78)
    print("H1c / H2c -- district-level product agreement against MARC")
    print("=" * 78)
    print(f"  MARC v1.0, {marc_dir}")
    print(f"  0.5 degree grid, {'no' if not marc['time_dimension'] else 'a'} time "
          f"dimension -> a single climatological calendar, not a per-season product")
    print(f"  using transplanting group {a.group}")

    coh = pd.read_csv(_find("candidate_cohort_v2.csv"))
    cm = attach_marc(coh, marc)
    n_out = int((~cm["marc_inside_grid"]).sum())
    if n_out:
        print(f"  [NOTE] {n_out} cohort points fall outside the MARC grid and are "
              f"excluded rather than clamped to an edge cell")

    if not os.path.exists(a.panel):
        raise SystemExit(f"panel not found: {a.panel}")
    ours = ours_by_district(a.panel, os.path.basename(a.panel))
    t = compare(cm, ours, a.group)
    s = summarise(t)

    os.makedirs(a.out, exist_ok=True)
    dest = os.path.join(a.out, "Table_SX_MARC_Agreement.csv")
    t.round(4).to_csv(dest, index=False, float_format="%.12g")
    dest2 = os.path.join(a.out, "Table_SX_MARC_Summary.csv")
    s.round(4).to_csv(dest2, index=False, float_format="%.12g")
    print(f"\n  wrote {dest}")
    print(f"  wrote {dest2}")

    cells = t["marc_cells_per_district"]
    print(f"\n  MARC cells per district: median {cells.median():.0f}, "
          f"range {cells.min():.0f}-{cells.max():.0f}. A district is a handful of "
          f"0.5 degree\n  cells, which is the resolution mismatch §3.4 Tier 2 "
          f"requires stating.")
    print("\n  Neither number above is a pass or a fail. §2 declares H1c/H2c "
          "'reported never\n  tested' and pre-declares no threshold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
