#!/usr/bin/env python3
"""Protocol §3.9's timing placebo, at full bootstrap resolution.

§4 declares beta_harv = 0 for the fitted radar trough: a cyclone that makes
landfall in the HARVEST window cannot causally alter observations acquired three
to four months earlier. The trough is not called a field-observed transplanting
date. The coefficient is therefore a falsification test of the
whole §3.8 A design, not an estimand. The §3.10 run reported it at +5.00 d
(district, p_WCB 0.110) and +7.44 d (pixel, p_WCB 0.0010 -- the 999-replication
floor, so unresolved below 0.001).

This script resolves it, and asks the three questions that decide what the
failure means:

  1. Does the p-value remain below the declared threshold at 9,999 draws?
                                                   -> Monte Carlo resolution
  2. Does the association persist in the IPSW and pre-trend specifications?
                                                   -> specification sensitivity
  3. Does the SAME storm set move the trough when
     the trough is measured in the season BEFORE
     the storm's own season?                        -> is it a global reshaping of
                                                       the fitted curve rather than
                                                       a local effect at the marker

Question 3 is an additional falsifiability check. A cyclone landing in season
t's harvest window sits after season t's trough and long after season t-1. A
non-null temporally impossible association rejects the causal interpretation of
this design; it does not identify whether the source is fitting, selection,
unmeasured exposure structure or another mechanism. The fitted trough is a radar
trajectory breakpoint, not an agronomic date.
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attrition_diagnostics import (twfe, build_exposure_table, ESTIMABLE_CYCLONES,
                                   load_panel, SEED)

# --- portable roots ---------------------------------------------------------
# Hard-coded absolute paths made these scripts unrunnable outside the machine
# they were written on. Flagged in an external audit on 2026-09-13 and fixed
# here: one environment variable relocates everything, and the defaults are the
# paths this analysis was actually run with, so nothing silently changes.
ROOT = os.environ.get("RICEBACI_ROOT", "/home/claude")
RESULTS = os.environ.get("RICEBACI_RESULTS", os.path.join(ROOT, "results"))


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

PANEL_PIXEL = os.path.join(RESULTS, "phen_panel_sar_static.csv")
PANEL_DIST = os.path.join(RESULTS, "phen_panel_district_season_static.csv")
EXPOSURE = _find_doc("district_cyclone_exposure_ibtracs50km.csv")
BOOT = 9999

REGS = ["S_pre_season", "S_harvest_window", "Slag_pre_season",
        "Slag_harvest_window", "M_minor"]
REGS_LEAD = REGS + ["Slead_pre_season", "Slead_harvest_window"]


def prep(path, level):
    panel = load_panel(path, level)
    exposure = pd.read_csv(EXPOSURE)
    districts = sorted(panel["district"].unique())
    years = sorted(panel["year"].unique())
    tab = build_exposure_table(exposure, districts, years)
    panel = panel.merge(tab, on=["district", "year"], how="left")
    for c in ["S_pre_season", "S_harvest_window", "M_minor",
              "Slag_pre_season", "Slag_harvest_window"]:
        panel[c] = panel[c].fillna(0).astype(int)
    return panel


def show(tag, r, pred=None):
    if r.get("status") != "estimated":
        print(f"  {tag:<52s} not estimable -- {r.get('reason','')}")
        return
    verdict = ""
    if pred == "0":
        verdict = ("  -> PLACEBO FAILS" if r["p_wcb"] < 0.05
                   else "  -> placebo passes")
    print(f"  {tag:<52s} {r['coef']:+8.3f} d  (se {r['se']:6.3f})  "
          f"p_WCB {r['p_wcb']:.4f}  CI [{r['wcb_ci_lo']:+7.2f}, "
          f"{r['wcb_ci_hi']:+7.2f}]  n={r['n_obs']}{verdict}")


def main():
    for level, path in (("pixel", PANEL_PIXEL), ("district", PANEL_DIST)):
        panel = prep(path, level)
        print("\n" + "=" * 78)
        print(f"§3.9 TIMING PLACEBO -- {level.upper()} level, {BOOT} replications")
        print("=" * 78)
        print("§4: beta_harv = 0 for the earlier fitted radar trough. A "
              "harvest-window landfall cannot causally alter the observations\n"
              "acquired months earlier; the trough is not an agronomic date.\n")

        print("Q1. the placebo itself, declared specification")
        show("beta[S_harvest_window] on radar trough breakpoint",
             twfe(panel, "trough", REGS, BOOT, SEED, "S_harvest_window"), pred="0")

        print("\nQ2. does it survive the adjustments?")
        show("  + lead terms (pre-trend-adjusted)",
             twfe(panel, "trough", REGS_LEAD, BOOT, SEED, "S_harvest_window"),
             pred="0")
        wcol = None
        for c in ("w_ipsw", "ipsw_weight", "weight_ipsw"):
            if c in panel.columns:
                wcol = c
                break
        if wcol:
            show(f"  + IPSW weights ({wcol})",
                 twfe(panel, "trough", REGS, BOOT, SEED, "S_harvest_window",
                      weights=wcol), pred="0")
        else:
            print("    (IPSW weights are built inside the §3.10 driver, not "
                  "carried on the panel;\n     the §3.10 table's ipsw row for "
                  "trough:S_harvest_window is the IPSW answer.)")

        print("\nQ3. THE DISCRIMINATING TEST. Does harvest-window exposure in "
              "season t move\n    the trough of season t-1, which precedes the "
              "storm by a full year?")
        # Slead_harvest_window on trough IS this test: exposure in t+1 against
        # the trough of t. Reported here as the lead coefficient in the
        # lead-augmented specification, i.e. Protocol §3.9's lambda.
        show("  lambda: beta[Slead_harvest_window] on trough",
             twfe(panel, "trough", REGS_LEAD, BOOT, SEED,
                  "Slead_harvest_window"), pred="0")
        show("  lambda: beta[Slead_harvest_window] on heading",
             twfe(panel, "heading", REGS_LEAD, BOOT, SEED,
                  "Slead_harvest_window"), pred="0")
        print("\n    Both are anticipation coefficients: a storm that has not "
              "yet happened\n    cannot move a marker already measured. Either "
              "one non-zero rejects the\n    design, not the hypothesis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
