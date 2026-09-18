"""
classify_exposure_phase.py -- re-classify severe exposure against the MEASURED
season, as the robustness arm named in the 2026-09-12 (third entry) deviation
log. Created 2026-09-13.

WHY. The exposure catalogue's `timing_class` is Paper 1's, built on the optical
calendar, and it does not describe when a storm lands relative to the radar
season. Measured, against the FITTED BREAKPOINTS and nothing else: of the 21 severe
rows labelled `harvest_window`, **14 fall inside the fitted t1-t2 rise phase**
(between the district's baseline t1 and its baseline t2), 4 between t2 and t3,
and 3 after t4.

WHAT THAT IS AND IS NOT. It is a statement about where a storm date sits
relative to four fitted breakpoints in a backscatter trajectory. It is NOT a
statement about whether an agronomic harvest had or had not occurred when the
storm arrived: this study holds no field reference, t4 is the end of the fall
and not an observed harvest date (§4.3.1), and a catalogue label and a fitted
phase are two different things rather than one right and one wrong. So the
measured disagreement between the two is reported as a disagreement, and
`harvest_window` is carried throughout as THE CATALOGUE'S LABEL. The 31 severe
`pre_season` rows are all before DOY 150, which is before every fitted t1 in
the panel, and that label is unchanged by this module.

    storm         season   storm DOY        phase against baseline markers
    FANI          2019     123             pre_window   (18 district-rows)
    AMPHAN        2020     141             pre_window   (6)
    YAAS          2021     146             pre_window   (5)
    REMAL         2024     147             pre_window   (2)
    TITLI         2018     283-284         rise         (6)
    DANA          2024     298-299         rise         (6)
    MONTHA        2025     301             rise (1), plateau (2)
    BULBUL:MATMO  2019     313             rise (1), plateau (1)
    MICHAUNG      2023     338-339         plateau (1), post_harvest (2)
    VARDAH        2016     347             post_harvest (1)

WHAT MAKES THIS NON-CIRCULAR. A storm is classified against the district's
BASELINE markers -- the mean of that district's fitted markers over its
district-seasons with NO catalogued exposure of any severity -- never against
the markers of the season being classified. If a storm shifts a season's
markers, classifying on those markers would move the class with the effect and
the estimate would be defined in terms of its own outcome. Every district has a
baseline from 2 to 7 unexposed estimable seasons (median 6).

THE COLLAPSE RULE, STATED BEFORE ANY COEFFICIENT WAS LOOKED AT. Phases are
collapsed toward the heading boundary until every retained phase carries at
least MIN_TREATED_CLUSTERS treated districts; a phase that still falls short is
reported as not estimable rather than as a null (MacKinnon & Webb 2018).
Measured cluster counts: pre_window 18, rise 14, plateau 4, post_harvest 2.
post_harvest alone is below three, so plateau, fall and post_harvest collapse
into one post-heading phase carrying 6 districts. The result is three phases:

    S_phase_pre_window    before the §1.4 season window opens (DOY < 150)
    S_phase_rise          from the window opening to baseline HEADING
    S_phase_post_heading  from baseline heading onward

No phase is dropped, split or merged after seeing an estimate.

THIS IS A ROBUSTNESS ARM, NOT THE HEADLINE. §3.8's frozen classes stay the
headline, because re-classifying exposure after seeing results is exactly the
discretion the protocol exists to remove. This arm is reported alongside.

    python python/classify_exposure_phase.py \
        --exposure data/district_cyclone_exposure_ibtracs50km.csv \
        --panel results/phen_panel_district_season.csv \
        --out results/exposure_phase.csv
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
ROOT = os.environ.get("RICEBACI_ROOT", "/home/claude")


def _find_doc(name):
    """Locate a committed docs/ file from wherever the script is run.

    The repository keeps the exposure catalogue and footprint table in docs/ while
    the scripts live in python/, so a bare filename resolves only when the working
    directory happens to hold both. An external audit on 2026-09-13 found three
    scripts unrunnable for exactly this reason. Candidates are searched in order
    and the first hit wins; a miss raises with the list, rather than failing later
    inside pandas with a bare filename that says nothing about where it looked.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    cands = [name,
             os.path.join(here, name),
             os.path.join(here, "..", "docs", name),
             os.path.join(ROOT, "docs", name),
             os.path.join(ROOT, name)]
    for c in cands:
        if os.path.exists(c):
            return c
    raise SystemExit(
        "cannot find %r. Looked in:\n  %s\nSet RICEBACI_ROOT, or run from a "
        "directory holding it." % (name, "\n  ".join(os.path.abspath(c)
                                                     for c in cands)))

SEASON_START_DOY = 150          # §1.4
MIN_TREATED_CLUSTERS = 3        # MacKinnon & Webb (2018), as in §3.10
BASELINE_MARKERS = ["trough", "heading", "drainage", "harvest"]
PHASES = ["pre_window", "rise", "post_heading"]


def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def season_doy(iso, season):
    """Storm date as a day-of-year on the season's own axis.

    The §1.4 season runs DOY 150 of the analysis year to DOY 425, so a date in
    the following calendar year carries a DOY above 365 -- which is how the
    fitted markers are expressed too. Returns NaN for a date more than one year
    either side, which is reported rather than silently coerced.
    """
    t = pd.Timestamp(iso)
    if pd.isna(t):
        return np.nan
    d = float(t.timetuple().tm_yday)
    if t.year == season:
        return d
    if t.year == season + 1:
        return d + (366.0 if is_leap(season) else 365.0)
    if t.year == season - 1:
        return d - (366.0 if is_leap(season - 1) else 365.0)
    return np.nan


def baseline_markers(panel, exposure):
    """District baseline markers: the mean over UNEXPOSED estimable seasons.

    Unexposed means the district-season appears nowhere in the exposure
    catalogue, at any severity. A district with no such season gets NaN and its
    storms are reported unclassifiable rather than classified on exposed data.
    """
    pairs = set(zip(exposure["district_gadm_name"].astype(str),
                    exposure["season"].astype(int)))
    exposed = [(str(d), int(y)) in pairs
               for d, y in zip(panel["district"], panel["year"])]
    ok = panel["estimable"].astype(int) == 1 if "estimable" in panel.columns \
        else panel["retained"].astype(int) == 1
    un = panel[(~np.asarray(exposed)) & ok]
    base = un.groupby("district")[BASELINE_MARKERS].mean()
    n = un.groupby("district").size().rename("n_baseline_seasons")
    return base.join(n)


def phase_of(storm_doy, heading):
    if not np.isfinite(storm_doy) or not np.isfinite(heading):
        return "unclassifiable"
    if storm_doy < SEASON_START_DOY:
        return "pre_window"
    if storm_doy < heading:
        return "rise"
    return "post_heading"


def build(exposure, panel):
    exp = exposure.copy()
    for c in ("severity_class", "timing_class"):
        if c in exp.columns:
            exp[c] = exp[c].astype(str).str.strip().str.lower()
    base = baseline_markers(panel, exp)

    sev = exp[exp["severity_class"] == "severe"].copy()
    sev["storm_doy"] = [season_doy(r.maxwind_fix_iso_time, int(r.season))
                        for r in sev.itertuples()]
    sev = sev.merge(base.reset_index().rename(
        columns={"district": "district_gadm_name"}),
        on="district_gadm_name", how="left")
    sev["phase"] = [phase_of(d, h)
                    for d, h in zip(sev["storm_doy"], sev["heading"])]

    roster = set(panel["district"].astype(str))
    bad = sev[sev["phase"] == "unclassifiable"]
    if len(bad):
        off = bad[~bad["district_gadm_name"].isin(roster)]
        on = bad[bad["district_gadm_name"].isin(roster)]
        if len(off):
            print(f"{len(off)} severe rows are in catalogue districts that are "
                  f"NOT in the panel roster, so they have no baseline markers "
                  f"and contribute nothing. Expected, not a failure: "
                  f"{sorted(set(off['district_gadm_name']))}")
        if len(on):
            print(f"WARNING: {len(on)} severe rows in ROSTER districts could "
                  "not be classified -- no baseline markers, or a storm date "
                  "more than a year from its season. Investigate before using "
                  "this arm:")
            print(on[["district_gadm_name", "season", "storm_name",
                      "maxwind_fix_iso_time"]].to_string(index=False))

    print("\nseverity=severe rows, protocol timing_class against the measured "
          "phase:")
    print(pd.crosstab(sev["timing_class"], sev["phase"]).to_string())

    # district x season indicator panel over the union of catalogue and panel
    years = sorted(set(panel["year"].astype(int)))
    cat_years = sorted(set(exp["season"].astype(int)))
    span = list(range(min(min(years), min(cat_years)),
                      max(max(years), max(cat_years)) + 1))
    districts = sorted(set(panel["district"].astype(str)))
    idx = pd.MultiIndex.from_product([districts, span],
                                     names=["district", "year"])
    tab = pd.DataFrame(index=idx).reset_index()
    for ph in PHASES:
        hit = (sev[sev["phase"] == ph][["district_gadm_name", "season"]]
               .drop_duplicates())
        hit.columns = ["district", "year"]
        hit["S_phase_" + ph] = 1
        tab = tab.merge(hit, on=["district", "year"], how="left")
        tab["S_phase_" + ph] = tab["S_phase_" + ph].fillna(0).astype(int)

    # lags read the catalogue at t-1 and leads at t+1, as §3.8 A specifies; the
    # lead for the final catalogue season is NaN, not 0, so the pretrend test
    # drops it rather than treating it as unexposed
    tab = tab.sort_values(["district", "year"]).reset_index(drop=True)
    g = tab.groupby("district")
    last = max(cat_years)
    for ph in PHASES:
        c = "S_phase_" + ph
        tab["Slag_phase_" + ph] = g[c].shift(1).fillna(0).astype(int)
        lead = g[c].shift(-1)
        tab["Slead_phase_" + ph] = np.where(tab["year"] >= last, np.nan, lead)

    tab = tab[tab["year"].isin(years)].reset_index(drop=True)

    # Treated-cluster counts are reported on the FINAL table -- restricted to
    # roster districts and panel seasons -- because that is what the estimator
    # sees. Counting them on the raw catalogue would report clusters the
    # regression never gets (VARDAH 2016 is outside the panel; MICHAUNG's
    # post-harvest rows are in non-roster districts).
    print("\ntreated clusters (districts) per phase, as the estimator sees them:")
    for ph in PHASES:
        c = "S_phase_" + ph
        n = int(tab.loc[tab[c] == 1, "district"].nunique())
        flag = "" if n >= MIN_TREATED_CLUSTERS else (
            f"  BELOW {MIN_TREATED_CLUSTERS} -- must be reported not estimable, "
            f"never as a null (MacKinnon & Webb 2018)")
        print(f"  {ph:<14s} {n:3d}{flag}")
    return tab, sev, base


def selftest():
    """Checks on the parts that a wrong answer would look plausible in."""
    print("=" * 74)
    print("SELF-TEST -- classify_exposure_phase.py")
    print("=" * 74)
    ok_all = True

    # ---- season_doy across the calendar boundary and a leap year ----------
    cases = [
        ("2019-05-03 18:00:00", 2019, 123.0, "May of the season year"),
        ("2018-10-11 00:00:00", 2018, 284.0, "October of the season year"),
        ("2017-01-19 00:00:00", 2016, 19.0 + 366.0, "January after a leap season"),
        ("2024-01-19 00:00:00", 2023, 19.0 + 365.0, "January after a common season"),
        ("2019-12-31 00:00:00", 2019, 365.0, "31 December of the season year"),
        ("2020-12-31 00:00:00", 2020, 366.0, "31 December of a leap season"),
    ]
    bad = []
    for iso, season, want, why in cases:
        got = season_doy(iso, season)
        if not (np.isfinite(got) and abs(got - want) < 1e-9):
            bad.append(f"{why}: {iso} in season {season} -> {got}, want {want}")
    ok = not bad
    ok_all &= ok
    for line in bad:
        print("    " + line)
    print(f"  [{'PASS' if ok else 'FAIL'}] a storm date is placed on the "
          f"season's own DOY axis, including across 31 December and across a "
          f"leap year")

    far = season_doy("2022-10-01 00:00:00", 2019)
    ok = not np.isfinite(far)
    ok_all &= ok
    print(f"  [{'PASS' if ok else 'FAIL'}] a date more than a year from its "
          f"season returns NaN rather than a silently wrapped DOY")

    # ---- phase boundaries -------------------------------------------------
    H = 314.5
    checks = [(149.9, "pre_window"), (150.0, "rise"), (314.4, "rise"),
              (314.5, "post_heading"), (400.0, "post_heading")]
    bad = [f"{d} -> {phase_of(d, H)}, want {w}"
           for d, w in checks if phase_of(d, H) != w]
    ok = not bad and phase_of(np.nan, H) == "unclassifiable" \
        and phase_of(200.0, np.nan) == "unclassifiable"
    ok_all &= ok
    for line in bad:
        print("    " + line)
    print(f"  [{'PASS' if ok else 'FAIL'}] the phase boundaries are "
          f"[<150 pre_window), [150, heading) rise, [heading, inf) "
          f"post_heading, and a missing date or missing baseline is refused")

    # ---- the baseline uses only UNEXPOSED estimable seasons ---------------
    exp = pd.DataFrame({
        "district_gadm_name": ["D", "D"],
        "season": [2019, 2020],
        "severity_class": ["severe", "minor"],
        "timing_class": ["harvest_window", "mid_season"],
        "maxwind_fix_iso_time": ["2019-10-11 00:00:00", "2020-09-01 00:00:00"],
    })
    pan = pd.DataFrame({
        "district": ["D"] * 4,
        "year": [2017, 2018, 2019, 2020],
        "estimable": [1, 1, 1, 1],
        "trough": [250.0, 250.0, 900.0, 900.0],      # the exposed seasons carry
        "heading": [310.0, 320.0, 900.0, 900.0],     # absurd values on purpose
        "drainage": [330.0, 330.0, 900.0, 900.0],
        "harvest": [380.0, 380.0, 900.0, 900.0],
    })
    base = baseline_markers(pan, exp)
    got_h = float(base.loc["D", "heading"])
    ok = (abs(got_h - 315.0) < 1e-9
          and int(base.loc["D", "n_baseline_seasons"]) == 2)
    ok_all &= ok
    print(f"\n  baseline heading for D = {got_h} from "
          f"{int(base.loc['D', 'n_baseline_seasons'])} seasons "
          f"(2017 and 2018 only; 2019 severe and 2020 minor are excluded)")
    print(f"  [{'PASS' if ok else 'FAIL'}] the baseline is built from "
          f"unexposed seasons only, at ANY severity -- a minor-exposure season "
          f"is excluded too, and the season being classified can never enter "
          f"its own baseline")

    # ---- a season with no estimable fit does not enter the baseline -------
    pan2 = pan.copy()
    pan2.loc[pan2["year"] == 2018, "estimable"] = 0
    b2 = baseline_markers(pan2, exp)
    ok = (abs(float(b2.loc["D", "heading"]) - 310.0) < 1e-9
          and int(b2.loc["D", "n_baseline_seasons"]) == 1)
    ok_all &= ok
    print(f"  [{'PASS' if ok else 'FAIL'}] a non-estimable season is excluded "
          f"from the baseline rather than contributing NaN")

    # ---- the indicator table: lags, leads, and the final-season NaN -------
    pan3 = pd.DataFrame({
        "district": ["D"] * 4, "year": [2017, 2018, 2019, 2020],
        "estimable": [1, 1, 1, 1],
        "trough": [250.0] * 4, "heading": [315.0] * 4,
        "drainage": [330.0] * 4, "harvest": [380.0] * 4,
    })
    tab, sev, _ = build(exp, pan3)
    r19 = tab[tab["year"] == 2019].iloc[0]
    r20 = tab[tab["year"] == 2020].iloc[0]
    r18 = tab[tab["year"] == 2018].iloc[0]
    ok = (int(r19["S_phase_rise"]) == 1
          and int(r20["Slag_phase_rise"]) == 1
          and int(r18["S_phase_rise"]) == 0
          and not np.isfinite(r20["Slead_phase_rise"]))
    ok_all &= ok
    print(f"\n  2019 storm at DOY 284 with baseline heading 315 -> "
          f"S_phase_rise 2019 = {int(r19['S_phase_rise'])}, "
          f"Slag 2020 = {int(r20['Slag_phase_rise'])}, "
          f"Slead 2020 = {r20['Slead_phase_rise']}")
    print(f"  [{'PASS' if ok else 'FAIL'}] the indicator, its lag and its lead "
          f"line up, and the lead is NaN for the final catalogue season rather "
          f"than 0 -- coding it 0 would assert 'not exposed next season' for a "
          f"season whose successor is unobserved")

    # ---- a storm in a non-roster district contributes nothing -------------
    exp2 = pd.concat([exp, pd.DataFrame({
        "district_gadm_name": ["NotInPanel"], "season": [2019],
        "severity_class": ["severe"], "timing_class": ["harvest_window"],
        "maxwind_fix_iso_time": ["2019-10-11 00:00:00"]})], ignore_index=True)
    tab2, sev2, _ = build(exp2, pan3)
    ok = ("NotInPanel" not in set(tab2["district"])
          and int(tab2["S_phase_rise"].sum()) == 1)
    ok_all &= ok
    print(f"\n  [{'PASS' if ok else 'FAIL'}] a severe storm in a district "
          f"outside the panel roster is reported and then contributes no "
          f"indicator, rather than being classified on absent baseline markers")

    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Re-classify severe exposure against the measured season.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--exposure")
    ap.add_argument("--panel",
                    help="district-season panel, for the baseline markers")
    ap.add_argument("--out")
    ap.add_argument("--storms-out", default=None,
                    help="optional per-storm classification table")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not (a.exposure and a.panel and a.out):
        ap.error("--exposure, --panel and --out are all required "
                 "(or run --selftest)")

    exposure = pd.read_csv(a.exposure)
    panel = pd.read_csv(a.panel)
    tab, sev, base = build(exposure, panel)

    print("\ndistrict baseline markers (mean over unexposed estimable seasons):")
    print(base.round(1).to_string())

    tab.to_csv(a.out, index=False)
    print(f"\nwrote {a.out}  ({len(tab)} district-seasons)")
    for ph in PHASES:
        c = "S_phase_" + ph
        print(f"  {c:<26s} exposed district-seasons {int(tab[c].sum()):3d}   "
              f"districts {tab.loc[tab[c] == 1, 'district'].nunique():3d}")
    if a.storms_out:
        cols = ["district_gadm_name", "season", "storm_name",
                "maxwind_fix_iso_time", "storm_doy", "timing_class", "phase",
                "trough", "heading", "drainage", "harvest",
                "n_baseline_seasons"]
        sev[[c for c in cols if c in sev.columns]].to_csv(a.storms_out,
                                                         index=False)
        print(f"wrote {a.storms_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
