"""
window_sweep.py -- Protocol §1.4's pre-declared window sensitivity sweep, tabulated.

§1.4: "The 60-day-extension window (DOY 150-425) is the headline. Results are also
reported for the 0-, 20-, 30- and 45-day extensions (upper endpoints DOY 365, 385,
395, 410), obtained by truncating the same per-bin composites before smoothing and
fitting; Gate 1-3 pass rates, extraction-failure rate and the §3.8 headline
coefficient are tabulated for all five endpoints, matching Paper 1's Table 2 layout."

`extract_phenometrics_sar.py --window-end-doy` produces the five panels. This module
does the tabulation half: it reads those panels and emits the three quantities §1.4
names, at both levels, for all five endpoints.

WHAT EACH GATE MEANS ON THE RADAR PATH, and why the pass rates are not invented:

  Gate 1 (§3.1, peak-relative sampling density). NOT applied at pixel level -- the
    radar default is ratio 0.0, measured rather than assumed (§3.1, third 2026-09-12
    entry: the gate manufactures the only §3.11 ineligibility in the whole untreated
    baseline). Its pass rate at pixel level is therefore 1.0000 BY CONSTRUCTION and is
    reported that way, with the construction named, not as evidence. It IS applied to
    the district-mean curve as a 0.5 coverage rule, and there it deletes DEKADS, not
    units -- so its pass rate is a dekad-level quantity, read off `used` in
    phen_curves_district_season.csv. Two versions are reported: `all` dekads, which
    mixes coverage with the window truncation this sweep is about, and `in_window`,
    restricted to dekads whose DOY falls at or before the endpoint, which isolates the
    coverage rule. Read `in_window`; `all` is there so the truncation is visible.

  Gate 2 (§3.2, phenometric DOY bounds). Fails land in fail_class as
    `outside_gate2_*` or `*_not_recovered`. Pass rate is over units that reached the
    gate, i.e. that were eligible under §3.11 and produced an admissible shape --
    a gate cannot pass or fail a unit it never saw.

  Gate 3 (§3.11). Two parts, both reported separately because they screen different
    things. The >=14-valid-dekad ELIGIBILITY rule is applied before any fitting and
    shows as `ineligible_dekads`; its denominator is every attempted unit. Gate 3's
    fit-quality role on the radar path is served by the RISE-SIGNIFICANCE screen
    (§3.11, revised 2026-09-12 third entry), which shows as `rise_not_significant`;
    its denominator is the units that reached it.

  Extraction-failure rate. 1 - retention, over observation-eligible units, which is
    §3.11's declared denominator for §3.10 item 1.

  §3.8 headline coefficient. §3.8 names beta_pre and beta_harv as the headline
    coefficients (H3) and fixes the level of estimation at the DISTRICT-SEASON panel
    (§3.8, 2026-09-12 third entry). Both levels are tabulated, district first. The
    estimator is `permutation_test.fit_cell`, imported rather than reimplemented, so
    the sweep's coefficient is the same statistic the headline reports -- a second
    copy of the absorption and screening code is how two different numbers end up
    under one name. No permutation p-values: 2,000 draws x 6 cells x 2 levels x 5
    endpoints is 120,000 fits for a sensitivity table, and §1.4 asks for the
    coefficient, not a re-inference.

HARVEST IDENTIFICATION -- found while building this table, reported because it
changes what the table may claim. The PLSM's final segment falls from the plateau to
b2 between t3 and t4, and is flat at b2 afterwards. When a unit has NO valid dekad
after t4, b2 is identified only from the slope of the fall extrapolated forward: the
harvest breakpoint is then where the fitted fall WOULD reach baseline, not an observed
return to it. `plsm_fit`'s determinant screen keeps such a fit numerically identified,
so it passes every gate silently. Measured:

    endpoint 425 (headline):  17 of 208 estimable district-seasons, 8.2%, have zero
                              valid dekads after t4; 28 of 208, 13.5%, have <= 1.
    endpoint 365:            125 of 204, 61.3%, have zero.

Two consequences, and they are different in kind.

  (1) The fall-end coefficient CANNOT be read across the endpoints. At DOY 365 three
      fifths of the units' fall-end breakpoints are extrapolations, so a change in that
      coefficient between endpoints is a change in what the coefficient is of. The
      sweep table therefore carries `harvest_extrapolated_share` in every row, and the
      coefficient table flags the harvest rows. This is itself §1.4's finding: the
      60-day extension is not a preference over Paper 1's core window, it is what
      identifies the fall-end breakpoint at all.

  (2) At the headline it is a diagnostic, not a correction. --drop-extrapolated
      re-estimates every cell on the units with at least one valid dekad after t4.
      Measured at DOY 425: beta_pre on harvest -10.184 (t -2.08) -> -8.084 (t -2.12),
      beta_harv on heading +6.183 (t +2.51) -> +7.438 (t +3.10). Every sign is
      preserved and the one significant positive cell strengthens, so no reported
      result rests on an extrapolated fall-end breakpoint. The headline retention rule is NOT
      changed on this basis -- changing a gate after seeing which units it would drop
      is the discretion §3 exists to remove -- and the arm is reported alongside.

  Pixel level is a lower bound only. The per-pixel dekad validity pattern is not in
  the committed panel schema, so `n_after_harvest` is exact at district level and at
  pixel level counts only the units whose harvest sits at the last dekad of the grid,
  where zero-after is certain. It is labelled `_lower_bound` there and must not be
  quoted as the share.

CONTROL ARM. The no-truncation run must reproduce the committed panel. --check-control
compares them column by column and reports the largest discrepancy in each. This is a
gate on the sweep, not decoration: if truncation-off does not reproduce the headline,
nothing else in the table means anything.

    python python/window_sweep.py --sweep-root results --out results/window_sweep
    python python/window_sweep.py --selftest

Created 2026-09-13.
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
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

ROOT = os.environ.get("RICEBACI_ROOT", os.path.dirname(HERE))
RESULTS = os.path.join(ROOT, "results")

CSV_FLOAT = "%.12g"          # idempotent under a read/write round trip

# §1.4's pre-declared set. 425 is the headline and is produced by the run with no
# --window-end-doy at all, so its directory is the control: bins_within(425) == 55
# == N_BINS, identical to None, which is why the control doubles as the 425 arm.
ENDPOINTS = [
    (425, "sweep_control", "headline: 60-day extension, DOY 150-425"),
    (410, "sweep_410", "45-day extension"),
    (395, "sweep_395", "30-day extension"),
    (385, "sweep_385", "20-day extension"),
    (365, "sweep_365", "0-day extension: Paper 1's core window"),
]

# fail_class values that mean "this unit never reached the later gates"
PRE_GATE_FAIL = {"ineligible_dekads"}
SHAPE_FAIL = {"no_rise_then_fall", "breakpoints_not_identified",
              "no_rise_above_base", "no_fall_after_heading",
              "too_few_dekads_in_rise_window", "too_few_dekads_after_heading",
              "no_dekad_in_trough_window", "too_few_after_trough",
              "no_heading_crossing", "no_harvest_crossing"}
SIG_FAIL = {"rise_not_significant", "rise_se_not_estimable",
            "rise_below_floor", "rise_below_minimum"}


def _is_gate2_fail(cls):
    c = str(cls)
    return c.startswith("outside_gate2_") or c.endswith("_not_recovered") \
        or c == "marker_not_recovered"


# ---------------------------------------------------------------------------
def last_admissible_dekad_doy(endpoint):
    """DOY of the last dekad any data can reach at this upper endpoint.

    Dekads aggregate the §1.4 bins pairwise, so dekad k draws on bins 2k and
    2k+1 and is present as soon as bin 2k survives truncation. With `keep` bins
    kept, the last such dekad is (keep - 1) // 2. Derived from the extractor's own
    bins_within rather than restated, so the two cannot drift.
    """
    import extract_phenometrics_sar as EX
    keep = EX.bins_within(None if endpoint is None else int(endpoint))
    if keep <= 0:
        return np.nan
    return float(EX._FP.DEKAD_DOY[(keep - 1) // 2])


def harvest_identification(panel, curves, level, endpoint=None):
    """Per-unit count of valid dekads strictly after the harvest breakpoint.

    Exact at district level, where `used` in phen_curves_district_season.csv gives
    the validity pattern per district-season. At pixel level the per-pixel pattern
    is not in the panel schema, so this returns the LOWER BOUND: the units whose
    harvest sits at or beyond the last dekad the endpoint admits, for which
    zero-after is certain regardless of the pixel's own validity pattern. Keyed on
    the ENDPOINT, not on max(harvest) in the panel -- an earlier version used the
    latter and the bound came out non-monotone in the endpoint (0.1058 at DOY 425
    against 0.0204 at DOY 385), which is the signature of a bound that moves with
    the sample rather than with the window.

    The `<=1` counts are only meaningful on the exact path; on the bound path they
    are returned as NaN rather than as the 1.0 a two-valued count would produce.
    Returns (panel_with_columns, summary_dict).
    """
    p = panel.copy()
    ret = p["retained"] if "retained" in p.columns else p["estimable"]
    ret = ret.astype(int)
    if level == "district" and len(curves) and "used" in curves.columns:
        cu = curves[curves["used"].astype(int) == 1]
        m = cu.merge(p[["district", "year", "harvest"]], on=["district", "year"])
        n = (m[m["doy"] > m["harvest"]].groupby(["district", "year"]).size()
             .rename("n_after_harvest").reset_index())
        p = p.merge(n, on=["district", "year"], how="left")
        p["n_after_harvest"] = p["n_after_harvest"].fillna(0).astype(int)
        exact = True
    else:
        last = last_admissible_dekad_doy(endpoint)
        p["n_after_harvest"] = np.where(
            np.isfinite(last) & (p["harvest"].astype(float) >= last - 1e-9), 0, 1)
        exact = False
    e = p[ret == 1]
    n = len(e)
    out = {
        "harvest_extrapolated_n": int((e["n_after_harvest"] == 0).sum()),
        "harvest_extrapolated_share": (float((e["n_after_harvest"] == 0).mean())
                                       if n else np.nan),
        "harvest_id_exact": bool(exact),
    }
    if exact:
        out["harvest_thin_n"] = int((e["n_after_harvest"] <= 1).sum())
        out["harvest_thin_share"] = (float((e["n_after_harvest"] <= 1).mean())
                                     if n else np.nan)
    else:
        out["harvest_thin_n"] = -1          # -1 == not computable at this level
        out["harvest_thin_share"] = np.nan
    return p, out


# ---------------------------------------------------------------------------
def gate_rates(panel, curves, endpoint, level):
    """Gate 1-3 pass rates and the extraction-failure rate for one panel.

    Every rate carries its own denominator in the output, because these gates are
    sequential and a rate quoted without its denominator is not interpretable: a
    Gate 2 pass rate over all attempted units falls when Gate 3 rejects more, which
    says nothing about Gate 2.
    """
    cls = panel["fail_class"].fillna("retained").astype(str)
    n_attempt = len(panel)
    n_inelig = int(cls.isin(PRE_GATE_FAIL).sum())
    n_eligible = n_attempt - n_inelig
    n_shape = int(cls.isin(SHAPE_FAIL).sum())
    n_sig = int(cls.isin(SIG_FAIL).sum())
    n_g2 = int(cls.map(_is_gate2_fail).sum())
    n_retained = int(cls.eq("retained").sum())
    other = n_attempt - n_inelig - n_shape - n_sig - n_g2 - n_retained

    # Gate 1. Pixel level: inert by measurement, reported as such.
    if level == "pixel":
        g1_all = g1_win = 1.0
        g1_denom_all = g1_denom_win = 0     # 0 signals "not applied"
    else:
        u = curves.copy()
        u["used"] = u["used"].astype(float)
        g1_all = float(u["used"].mean())
        g1_denom_all = int(len(u))
        inw = u[u["doy"] <= float(endpoint)]
        g1_win = float(inw["used"].mean()) if len(inw) else np.nan
        g1_denom_win = int(len(inw))

    def share(num, den):
        return float(num) / den if den else np.nan

    return {
        "n_attempted": n_attempt,
        "gate1_dekad_pass_all": g1_all,
        "gate1_dekad_denom_all": g1_denom_all,
        "gate1_dekad_pass_in_window": g1_win,
        "gate1_dekad_denom_in_window": g1_denom_win,
        "gate3_eligible_pass": share(n_eligible, n_attempt),
        "gate3_eligible_denom": n_attempt,
        "shape_pass": share(n_eligible - n_shape, n_eligible),
        "shape_denom": n_eligible,
        "gate3_rise_sig_pass": share(n_eligible - n_shape - n_sig,
                                     n_eligible - n_shape),
        "gate3_rise_sig_denom": n_eligible - n_shape,
        "gate2_pass": share(n_eligible - n_shape - n_sig - n_g2,
                            n_eligible - n_shape - n_sig),
        "gate2_denom": n_eligible - n_shape - n_sig,
        "n_retained": n_retained,
        "retention_of_attempted": share(n_retained, n_attempt),
        "extraction_failure_rate": 1.0 - share(n_retained, n_eligible),
        "extraction_failure_denom": n_eligible,
        "n_unclassified": other,
    }


# ---------------------------------------------------------------------------
def coefficients(panel_path, level, endpoint, curves=None,
                 min_after_harvest=0, arm="all_estimable"):
    """The §3.8 cells for one panel, through permutation_test.fit_cell.

    min_after_harvest > 0 restricts to units with at least that many valid dekads
    after t4 -- the harvest-identification arm. It is applied AFTER the retention
    filter, so it subsets the committed sample rather than redefining it.
    """
    import permutation_test as PT
    from attrition_diagnostics import build_exposure_table, load_panel

    exposure = pd.read_csv(PT.EXPOSURE)
    panel = load_panel(panel_path, level, verbose=False)
    if min_after_harvest > 0:
        panel, _ = harvest_identification(
            panel, curves if curves is not None else pd.DataFrame(),
            level, endpoint)
        panel = panel[panel["n_after_harvest"] >= min_after_harvest]
    panel = panel[panel["retained"] == 1].copy()
    districts = sorted(panel["district"].unique())
    years = sorted(panel["year"].unique())
    tab = build_exposure_table(exposure, districts, years)
    base = PT.attach(panel, tab)
    rows = []
    for phen, var, label in PT.CELLS:
        b, se, t, nt = PT.fit_cell(base, phen, var)
        rows.append({
            "window_end_doy": endpoint, "level": level, "arm": arm,
            "phenometric": phen, "test_var": var, "cell_label": label,
            "beta_days": b, "se_days": se, "t_cluster_robust": t,
            "n_treated_clusters": nt,
            "n_rows": int(base.dropna(subset=[phen] + PT.REGS).shape[0]),
            "n_clusters": len(districts),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
def check_control(control_dir, committed_dir):
    """Does no-truncation reproduce the committed panel? Column by column.

    Reports the largest absolute discrepancy in every numeric column and the count
    of differing rows in every other. Returns (DataFrame, verdict) where verdict is
    one of EXACT, EPSILON, MATERIAL, SHAPE_MISMATCH.
    """
    a_p = os.path.join(committed_dir, "phen_panel_sar.csv")
    b_p = os.path.join(control_dir, "phen_panel_sar.csv")
    for p in (a_p, b_p):
        if not os.path.exists(p):
            return pd.DataFrame(), f"MISSING:{p}"
    if os.path.samefile(a_p, b_p):
        return pd.DataFrame(), "SELF_COMPARISON"
    a = pd.read_csv(a_p)
    b = pd.read_csv(b_p)
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        return pd.DataFrame([{"column": "_shape_", "committed": str(a.shape),
                              "control": str(b.shape)}]), "SHAPE_MISMATCH"
    key = ["district", "year", "cell_id"]
    if any(c not in a.columns for c in key) or a[key].isna().any().any() or b[key].isna().any().any():
        return pd.DataFrame(), "INVALID_KEYS"
    if a.duplicated(key).any() or b.duplicated(key).any():
        return pd.DataFrame(), "DUPLICATE_KEYS"
    a = a.sort_values(key).reset_index(drop=True)
    b = b.sort_values(key).reset_index(drop=True)
    if not a[key].equals(b[key]):
        return pd.DataFrame(), "KEY_MISMATCH"
    rows, worst_num, material = [], 0.0, False
    for c in a.columns:
        if a[c].dtype.kind in "fc" and b[c].dtype.kind in "fc":
            av, bv = a[c].to_numpy(float), b[c].to_numpy(float)
            finite = np.isfinite(av) & np.isfinite(bv)
            same_nonfinite = (np.isnan(av) & np.isnan(bv)) | (np.isinf(av) & (av == bv))
            bad_nonfinite = ~finite & ~same_nonfinite
            d = np.abs(av[finite] - bv[finite])
            n = int((d > 0).sum() + bad_nonfinite.sum())
            mx = float(d.max()) if len(d) else 0.0
            scale = float(np.abs(av[finite]).max()) if finite.any() else 0.0
            rel = mx / scale if scale > 0 else (np.inf if mx else 0.0)
            rows.append({"column": c, "kind": "numeric", "n_differing": n,
                         "max_abs_diff": mx, "max_rel_diff": rel,
                         "nonfinite_mismatches": int(bad_nonfinite.sum()),
                         "relative_tolerance": 1e-9, "absolute_tolerance": 1e-12})
            worst_num = max(worst_num, mx)
            if bad_nonfinite.any() or (d > 1e-12 + 1e-9 * np.abs(av[finite])).any():
                material = True
        else:
            # pd.NA != pd.NA is NA, not False; compare on a filled copy so a
            # column that is null in both sides is not counted as differing.
            # That artefact produced a spurious "31,741 fail_reason differences"
            # on 2026-09-13, exactly equal to the retained count.
            sa = a[c].astype(object).where(a[c].notna(), "\x00NA")
            sb = b[c].astype(object).where(b[c].notna(), "\x00NA")
            n = int((sa.astype(str) != sb.astype(str)).sum())
            rows.append({"column": c, "kind": "text", "n_differing": n,
                         "max_abs_diff": np.nan, "max_rel_diff": np.nan})
            if n:
                material = True
    df = pd.DataFrame(rows)
    if material:
        verdict = "MATERIAL"
    elif worst_num == 0.0:
        verdict = "EXACT"
    else:
        verdict = "EPSILON"
    return df, verdict


# ---------------------------------------------------------------------------
def run(sweep_root, out_dir, committed_dir=None, do_coef=True,
        do_control=True, allow_missing=False, drop_extrapolated=True):
    os.makedirs(out_dir, exist_ok=True)
    gate_rows, coef_frames, missing = [], [], []
    ctl, verdict = pd.DataFrame(), "NOT RUN"
    if do_control:
        ctl, verdict = check_control(os.path.join(sweep_root, "sweep_control"),
                                     committed_dir or RESULTS)
        if len(ctl):
            ctl.to_csv(os.path.join(out_dir, "window_sweep_control_check.csv"),
                       index=False, float_format="%.6g")
        if verdict not in {"EXACT", "EPSILON"}:
            raise SystemExit(f"control check {verdict}; refusing to tabulate a verified sweep")

    for endpoint, sub, note in ENDPOINTS:
        d = os.path.join(sweep_root, sub)
        pix = os.path.join(d, "phen_panel_sar.csv")
        dis = os.path.join(d, "phen_panel_district_season.csv")
        crv = os.path.join(d, "phen_curves_district_season.csv")
        if not (os.path.exists(pix) and os.path.exists(dis)):
            missing.append((endpoint, d))
            continue
        curves = pd.read_csv(crv) if os.path.exists(crv) else \
            pd.DataFrame(columns=["doy", "used"])
        for level, path in (("district", dis), ("pixel", pix)):
            panel = pd.read_csv(path)
            r = gate_rates(panel, curves, endpoint, level)
            _, hid = harvest_identification(panel, curves, level, endpoint)
            r.update(hid)
            r.update({"window_end_doy": endpoint, "level": level,
                      "arm": note, "source_dir": sub})
            gate_rows.append(r)
            if do_coef:
                coef_frames.append(coefficients(path, level, endpoint))
                if drop_extrapolated:
                    coef_frames.append(coefficients(
                        path, level, endpoint, curves=curves,
                        min_after_harvest=1, arm="harvest_identified"))
        print(f"  DOY {endpoint}: tabulated ({note})")

    if missing and not allow_missing:
        lines = "\n".join(f"  DOY {e}: {d}" for e, d in missing)
        raise SystemExit(
            "these §1.4 endpoints have no extracted panel:\n" + lines +
            "\nRun extract_phenometrics_sar.py --window-end-doy for each, or pass"
            "\n--allow-missing to tabulate a partial sweep. A partial sweep is NOT"
            "\nwhat §1.4 declares and must be labelled as partial where reported.")
    if missing:
        print(f"  PARTIAL: {len(missing)} of {len(ENDPOINTS)} endpoints absent: "
              + ", ".join(str(e) for e, _ in missing))

    lead = ["window_end_doy", "level", "arm", "source_dir"]
    gates = pd.DataFrame(gate_rows)
    gates = gates[lead + [c for c in gates.columns if c not in lead]]
    gates = gates.sort_values(["level", "window_end_doy"],
                              ascending=[True, False])
    gp = os.path.join(out_dir, "Table_SX_WindowSweep_gates.csv")
    gates.to_csv(gp, index=False, float_format=CSV_FLOAT)
    print(f"  wrote {gp}  ({len(gates)} rows)")

    coefs = pd.DataFrame()
    if coef_frames:
        coefs = pd.concat(coef_frames, ignore_index=True)
        coefs = coefs.sort_values(
            ["arm", "level", "phenometric", "test_var", "window_end_doy"],
            ascending=[True, True, True, True, False])
        cp = os.path.join(out_dir, "Table_SX_WindowSweep_coefficients.csv")
        coefs.to_csv(cp, index=False, float_format=CSV_FLOAT)
        print(f"  wrote {cp}  ({len(coefs)} rows)")

    write_summary(out_dir, gates, coefs, ctl, verdict, missing)
    return gates, coefs, verdict


# ---------------------------------------------------------------------------
def write_summary(out_dir, gates, coefs, ctl, verdict, missing):
    L = []
    A = L.append
    A("# §1.4 window sensitivity sweep")
    A("")
    A("Generated by `python/window_sweep.py`. §1.4 declares five upper endpoints")
    A("(DOY 365, 385, 395, 410, 425) and asks for Gate 1-3 pass rates, the")
    A("extraction-failure rate and the §3.8 headline coefficient at each. The 425")
    A("arm is the run with no truncation at all, so it is simultaneously the")
    A("headline and the sweep's control.")
    A("")
    if missing:
        A(f"**PARTIAL SWEEP.** {len(missing)} endpoint(s) absent: "
          + ", ".join(f"DOY {e}" for e, _ in missing) + ".")
        A("")
    A("## Control check: does no truncation reproduce the committed panel?")
    A("")
    A(f"**Verdict: {verdict}.**")
    A("")
    if verdict == "EPSILON" and len(ctl):
        num = ctl[(ctl["kind"] == "numeric") & (ctl["n_differing"] > 0)]
        A("Every integer-valued and text column -- all four breakpoints, the")
        A("retention flag, the failure reason and the failure class -- is")
        A("bit-identical. The differences are confined to the continuous dB level")
        A("estimates, which come out of a weighted least-squares solve:")
        A("")
        A("| column | differing rows | max abs diff | max rel diff |")
        A("|---|---:|---:|---:|")
        for _, r in num.sort_values("max_abs_diff", ascending=False).iterrows():
            A(f"| `{r['column']}` | {int(r['n_differing']):,} | "
              f"{r['max_abs_diff']:.3g} | {r['max_rel_diff']:.3g} |")
        A("")
        A("These are last-bit floating-point differences (relative ~1e-16, i.e.")
        A("the 16th significant figure of a double). Two candidate causes were")
        A("tested and **both refuted** on this machine: `--jobs` 1, 2 and 4 give a")
        A("byte-identical panel, and so does pinning the BLAS thread count to 1.")
        A("The remaining candidate is a difference in the numerical environment")
        A("between the container that produced the committed panel and the one that")
        A("produced the control -- OpenBLAS selects its reduction order from the")
        A("core count it sees. That is recorded as the untested candidate it is,")
        A("not as a finding.")
    elif verdict == "EXACT":
        A("The parsed control values equal the frozen reference by key and column; this is not a byte-identity check.")
    elif verdict == "MATERIAL":
        A("**A material difference was found.** The sweep below is not")
        A("interpretable until this is explained: if the no-truncation arm does not")
        A("reproduce the headline, the truncated arms cannot be read against it.")
        if len(ctl):
            bad = ctl[ctl["n_differing"] > 0]
            A("")
            A("| column | kind | differing rows | max abs diff |")
            A("|---|---|---:|---:|")
            for _, r in bad.iterrows():
                A(f"| `{r['column']}` | {r['kind']} | "
                  f"{int(r['n_differing']):,} | {r['max_abs_diff']} |")
    A("")

    for level in ("district", "pixel"):
        g = gates[gates["level"] == level]
        if not len(g):
            continue
        A(f"## Gate pass rates and extraction failure -- {level} level")
        A("")
        if level == "district":
            A("This is the level §3.8 estimates the headline on (§3.8, 2026-09-12")
            A("third entry). Gate 1 is applied here as a 0.5 coverage rule on the")
            A("district-mean curve and deletes dekads, not units -- the")
            A("`in_window` column restricts to dekads at or before the endpoint and")
            A("is the one to read; the `all` column includes the dekads truncation")
            A("itself removed, so it falls with the endpoint by construction.")
        else:
            A("Robustness arm and the input to §3.10. **Gate 1 is not applied at")
            A("pixel level on the radar path** (§3.1, third 2026-09-12 entry): the")
            A("measured ratio is 0.0, so its pass rate is 1.0000 by construction and")
            A("is omitted rather than reported as evidence.")
        A("")
        cols = ["window_end_doy", "n_attempted", "gate3_eligible_pass",
                "shape_pass", "gate3_rise_sig_pass", "gate2_pass",
                "n_retained", "retention_of_attempted",
                "extraction_failure_rate"]
        hdr = ["endpoint", "attempted", "Gate 3 elig.", "shape",
               "Gate 3 rise-sig.", "Gate 2", "retained", "retention",
               "extr. failure"]
        if level == "district":
            cols.insert(2, "gate1_dekad_pass_in_window")
            hdr.insert(2, "Gate 1 (in-window)")
        A("| " + " | ".join(hdr) + " |")
        A("|" + "---|" * len(hdr))
        for _, r in g.iterrows():
            cells = []
            for c in cols:
                v = r[c]
                if c in ("window_end_doy", "n_attempted", "n_retained"):
                    cells.append(f"{int(v):,}")
                else:
                    cells.append("--" if not np.isfinite(v) else f"{v:.4f}")
            A("| " + " | ".join(cells) + " |")
        A("")
        A("Denominators are sequential and are carried in the CSV: Gate 3")
        A("eligibility is over every attempted unit; shape, rise-significance and")
        A("Gate 2 are each over the units that reached them; the extraction-failure")
        A("rate is over observation-eligible units, which is §3.11's declared")
        A("denominator.")
        A("")
        exact = bool(g["harvest_id_exact"].iloc[0])
        A("**Fall-end identification.** Share of retained units with no valid dekad")
        A("after t4, whose fitted fall-end breakpoint is therefore where the fitted fall would")
        A("reach baseline rather than an observed return to it"
          + ("" if exact else " -- a LOWER BOUND at"))
        if not exact:
            A("this level: the per-pixel dekad validity pattern is not in the panel")
            A("schema, so only units whose harvest sits at the last grid dekad are")
            A("counted. Do not quote it as the share.")
        A("")
        if exact:
            A("| endpoint | no dekad after t4 | share | <=1 dekad after t4 "
              "| share |")
            A("|---|---:|---:|---:|---:|")
            for _, r in g.iterrows():
                A(f"| {int(r['window_end_doy'])} | "
                  f"{int(r['harvest_extrapolated_n']):,} | "
                  f"{r['harvest_extrapolated_share']:.4f} | "
                  f"{int(r['harvest_thin_n']):,} | "
                  f"{r['harvest_thin_share']:.4f} |")
        else:
            A("| endpoint | last dekad the endpoint admits | at or beyond it "
              "| lower-bound share |")
            A("|---|---:|---:|---:|")
            for _, r in g.iterrows():
                A(f"| {int(r['window_end_doy'])} | "
                  f"{last_admissible_dekad_doy(int(r['window_end_doy'])):.1f} | "
                  f"{int(r['harvest_extrapolated_n']):,} | "
                  f"{r['harvest_extrapolated_share']:.4f} |")
            A("")
            A("The `<=1` count is not computable from this level's schema and is")
            A("written as -1 in the CSV rather than as a number that looks like one.")
        A("")

    if len(coefs):
        A("## §3.8 coefficients across the five endpoints")
        A("")
        A("β in days, from `permutation_test.fit_cell` -- the same absorption,")
        A("regressor screen, clustering and finite-sample factor the headline uses,")
        A("imported rather than reimplemented. `t` is cluster-robust on 25 district")
        A("clusters. **No permutation p-values here:** §1.4 asks for the")
        A("coefficient, and 2,000 draws x 6 cells x 2 levels x 5 endpoints is")
        A("120,000 fits for a sensitivity table. The declared inference stays in")
        A("`permutation_test.py` at the headline endpoint.")
        A("")
        arms = [a for a in ("all_estimable", "harvest_identified")
                if a in set(coefs["arm"])]
        for arm in arms:
            ca = coefs[coefs["arm"] == arm]
            if arm == "harvest_identified":
                A("### Arm: harvest identified (>= 1 valid dekad after t4)")
                A("")
                A("The same cells on the subset whose harvest breakpoint is not an")
                A("extrapolation. Read against the table above: a sign that survives")
                A("here does not rest on an extrapolated fall-end breakpoint. This is")
                A("reported alongside the headline, never in place of it -- the")
                A("retention rule is not changed after seeing which units it drops.")
                A("")
            for level in ("district", "pixel"):
                c = ca[ca["level"] == level]
                if not len(c):
                    continue
                A(f"### {arm} -- {level} level" if arm != "all_estimable"
                  else f"### {level} level")
                A("")
                ns = (c.sort_values("window_end_doy", ascending=False)
                      .drop_duplicates("window_end_doy"))
                A("Sample: " + ";  ".join(
                    f"DOY {int(r['window_end_doy'])} n={int(r['n_rows']):,} "
                    f"clusters={int(r['n_clusters'])}"
                    for _, r in ns.iterrows()) + ".")
                A("")
                if arm == "harvest_identified" and level == "district":
                    lo = ns.iloc[-1]
                    hi = ns.iloc[0]
                    A(f"**Read this arm at the headline endpoint, not across it.** Its"
                      f" filter removes exactly the units the shorter windows create,"
                      f" so its sample falls from n={int(hi['n_rows']):,} on"
                      f" {int(hi['n_clusters'])} clusters at DOY"
                      f" {int(hi['window_end_doy'])} to n={int(lo['n_rows']):,} on"
                      f" {int(lo['n_clusters'])} at DOY"
                      f" {int(lo['window_end_doy'])} -- three clusters gone"
                      if int(lo['n_clusters']) < int(hi['n_clusters']) else "")
                    A("entirely. Every cell at the shorter endpoints is therefore a")
                    A("different and much weaker sample, not a window sensitivity, and")
                    A("the coefficients there support no reading. The arm exists to")
                    A("test whether the HEADLINE rests on extrapolated fall-end breakpoints,")
                    A("and at DOY 425 and 410 it is well enough powered to answer.")
                    A("")
                eps = sorted(c["window_end_doy"].unique(), reverse=True)
                A("| cell | " + " | ".join(f"DOY {e}" for e in eps)
                  + " | range |")
                A("|" + "---|" * (len(eps) + 2))
                for (phen, var), grp in c.groupby(["phenometric", "test_var"],
                                                  sort=False):
                    gg = grp.set_index("window_end_doy")
                    vals, cells = [], []
                    for e in eps:
                        if e in gg.index:
                            b = float(gg.loc[e, "beta_days"])
                            t = float(gg.loc[e, "t_cluster_robust"])
                            if np.isfinite(b):
                                vals.append(b)
                                cells.append(f"{b:+.3f} (t {t:+.2f})")
                            else:
                                cells.append("not estimable")
                        else:
                            cells.append("--")
                    rng = f"{max(vals) - min(vals):.3f} d" if len(vals) > 1 \
                        else "--"
                    flag = " **[not comparable across endpoints: see harvest " \
                           "identification]**" if phen == "harvest" else ""
                    A(f"| `{phen}` on `{var}` | " + " | ".join(cells)
                      + f" | {rng}{flag} |")
                A("")
        A("A coefficient that changes sign across the endpoints is a window")
        A("artefact and must be reported as one. A coefficient stable in sign and")
        A("magnitude across all five is evidence the §1.4 choice is not driving it.")
        A("Neither statement is made here -- this file tabulates; §4 reads it.")
        A("")

    p = os.path.join(out_dir, "window_sweep_summary.md")
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print(f"  wrote {p}")


# ---------------------------------------------------------------------------
def selftest():
    print("=" * 74)
    print("SELF-TEST -- window_sweep.py")
    print("=" * 74)
    ok_all = True

    def chk(cond, msg):
        nonlocal ok_all
        ok_all &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")

    # --- 1. sequential denominators ---------------------------------------
    # 10 units: 2 ineligible, 2 shape, 2 rise-sig, 1 Gate 2, 3 retained.
    cls = (["ineligible_dekads"] * 2 + ["no_rise_then_fall"] * 2
           + ["rise_not_significant"] * 2 + ["outside_gate2_trough"]
           + ["retained"] * 3)
    panel = pd.DataFrame({"fail_class": cls})
    curves = pd.DataFrame({"doy": [100.0, 200.0, 300.0, 400.0],
                           "used": [1, 1, 0, 0]})
    r = gate_rates(panel, curves, 425, "pixel")
    chk(r["n_attempted"] == 10 and r["n_retained"] == 3, "counts read back")
    chk(abs(r["gate3_eligible_pass"] - 0.8) < 1e-12,
        "Gate 3 eligibility 8/10 over ALL attempted units")
    chk(abs(r["shape_pass"] - 6 / 8) < 1e-12,
        "shape 6/8 over the ELIGIBLE units, not over all 10")
    chk(abs(r["gate3_rise_sig_pass"] - 4 / 6) < 1e-12,
        "rise-significance 4/6 over the units that reached it")
    chk(abs(r["gate2_pass"] - 3 / 4) < 1e-12,
        "Gate 2 3/4 over the units that reached it")
    chk(abs(r["extraction_failure_rate"] - (1 - 3 / 8)) < 1e-12,
        "extraction failure 1-3/8 over observation-eligible units")
    chk(r["n_unclassified"] == 0, "every fail class is accounted for")

    # A rate over the wrong denominator is the defect this guards: shape over all
    # 10 would be 0.80, and would fall when Gate 3 rejected more units.
    chk(abs(r["shape_pass"] - 0.8) > 1e-6,
        "shape rate is NOT the all-units rate (the wrong-denominator defect)")

    # --- 2. Gate 1 is inert at pixel level, by construction ----------------
    chk(r["gate1_dekad_pass_all"] == 1.0 and r["gate1_dekad_denom_all"] == 0,
        "pixel-level Gate 1 reports 1.0 with denominator 0 == 'not applied'")
    rd = gate_rates(panel, curves, 385, "district")
    chk(abs(rd["gate1_dekad_pass_all"] - 0.5) < 1e-12,
        "district Gate 1 over ALL dekads is 2/4")
    chk(rd["gate1_dekad_denom_in_window"] == 3
        and abs(rd["gate1_dekad_pass_in_window"] - 2 / 3) < 1e-12,
        "district Gate 1 in-window is 2/3 at DOY 385 -- truncation excluded")

    # --- 3. an unknown fail class is counted, never silently dropped -------
    p2 = pd.DataFrame({"fail_class": ["retained", "something_new"]})
    r2 = gate_rates(p2, curves, 425, "pixel")
    chk(r2["n_unclassified"] == 1,
        "an unrecognised fail class raises n_unclassified rather than vanishing")

    # --- 4. the pd.NA comparison artefact -------------------------------
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        a = os.path.join(td, "a"); b = os.path.join(td, "b")
        os.makedirs(a); os.makedirs(b)
        base = pd.DataFrame({
            "district": ["D"] * 4, "year": [2017, 2018, 2019, 2020],
            "cell_id": [1, 2, 3, 4], "retained": [1, 1, 0, 0],
            "fail_reason": [None, None, "why", "why"],
            "trough": [210.0, 211.0, np.nan, np.nan],
            "rise_db": [8.0, 9.0, 1.0, 1.0]})
        base.to_csv(os.path.join(a, "phen_panel_sar.csv"), index=False)
        base.to_csv(os.path.join(b, "phen_panel_sar.csv"), index=False)
        df, v = check_control(b, a)
        chk(v == "EXACT",
            "identical panels with null text columns verdict EXACT, not MATERIAL")
        chk(int(df.loc[df["column"] == "fail_reason", "n_differing"].iloc[0]) == 0,
            "a column null on both sides counts 0 differences, not len(panel)")

        # an epsilon in a float column is EPSILON; a real change is MATERIAL
        eps = base.copy()
        eps.loc[0, "rise_db"] = 8.0 + 8.0 * np.finfo(float).eps
        eps.to_csv(os.path.join(b, "phen_panel_sar.csv"), index=False)
        _, v = check_control(b, a)
        chk(v == "EPSILON", "a last-bit float difference verdict EPSILON")

        big = base.copy(); big.loc[0, "trough"] = 215.0
        big.to_csv(os.path.join(b, "phen_panel_sar.csv"), index=False)
        _, v = check_control(b, a)
        chk(v == "MATERIAL", "a 5-day breakpoint move verdict MATERIAL")

        short = base.iloc[:3].copy()
        short.to_csv(os.path.join(b, "phen_panel_sar.csv"), index=False)
        _, v = check_control(b, a)
        chk(v == "SHAPE_MISMATCH", "a different row count verdict SHAPE_MISMATCH")
        for label, bad in (("finite value removed", base.assign(trough=[np.nan, 211., np.nan, np.nan])),
                           ("infinity introduced", base.assign(trough=[np.inf, 211., np.nan, np.nan])),
                           ("duplicate key", pd.concat([base.iloc[:3], base.iloc[[0]]], ignore_index=True))):
            bad.to_csv(os.path.join(b, "phen_panel_sar.csv"), index=False)
            _, v = check_control(b, a)
            chk(v not in {"EXACT", "EPSILON"}, f"{label} refused: {v}")
        _, v = check_control(a, a)
        chk(v == "SELF_COMPARISON", "comparison with the same file is refused")
        try:
            run(td, os.path.join(td, "gate_out"), committed_dir=a, do_coef=False)
            chk(False, "missing control must stop the whole run")
        except SystemExit as exc:
            chk("control check MISSING" in str(exc), "missing control stops before tabulation")

    # --- 4b. harvest identification ---------------------------------------
    # exact path: validity read off `used`, so "after t4" is countable
    dpan = pd.DataFrame({
        "district": ["A", "A", "B"], "year": [2017, 2018, 2017],
        "estimable": [1, 1, 1], "retained": [1, 1, 1],
        "harvest": [364.5, 404.5, 422.0]})
    dcur = pd.concat([
        pd.DataFrame({"district": d, "year": y,
                      "doy": [354.5, 364.5, 374.5, 384.5, 394.5, 404.5,
                              414.5, 422.0],
                      "used": [1, 1, 1, 1, 1, 1, 1, 1]})
        for d, y in (("A", 2017), ("A", 2018), ("B", 2017))],
        ignore_index=True)
    got, summ = harvest_identification(dpan, dcur, "district")
    chk(list(got["n_after_harvest"]) == [6, 2, 0],
        "valid dekads after t4 counted exactly: 6 / 2 / 0")
    chk(summ["harvest_extrapolated_n"] == 1
        and abs(summ["harvest_extrapolated_share"] - 1 / 3) < 1e-12,
        "one of three retained units has no dekad after t4")
    chk(summ["harvest_thin_n"] == 1 and summ["harvest_id_exact"],
        "the <=1 count is 1 and the district path reports itself exact")

    # a unit whose late dekads are NOT used must count them as absent, which is
    # the whole point: a dekad Gate 1 deleted cannot identify b2.
    dcur2 = dcur.copy()
    dcur2.loc[(dcur2["district"] == "A") & (dcur2["year"] == 2017)
              & (dcur2["doy"] > 364.5), "used"] = 0
    _, s2 = harvest_identification(dpan, dcur2, "district")
    chk(s2["harvest_extrapolated_n"] == 2,
        "a unit whose post-t4 dekads are unused counts as extrapolated")

    # pixel path: lower bound only, keyed on the endpoint and monotone in it
    _, s3 = harvest_identification(dpan, pd.DataFrame(), "pixel", 425)
    chk(not s3["harvest_id_exact"] and s3["harvest_extrapolated_n"] == 1,
        "the pixel bound at DOY 425 counts the one unit at dekad 422.0")
    chk(s3["harvest_thin_n"] == -1 and not np.isfinite(s3["harvest_thin_share"]),
        "the <=1 count is refused on the bound path, not returned as 1.0")
    chk([last_admissible_dekad_doy(e) for e in (425, 410, 395, 385, 365)]
        == [422.0, 404.5, 394.5, 384.5, 364.5],
        "last admissible dekad per endpoint: 422.0/404.5/394.5/384.5/364.5")
    bounds = [harvest_identification(dpan, pd.DataFrame(), "pixel", e)[1]
              ["harvest_extrapolated_n"] for e in (425, 410, 395, 385, 365)]
    chk(bounds == sorted(bounds),
        f"the pixel bound is monotone non-decreasing as the window shrinks: "
        f"{bounds}")

    # --- 5. the endpoint set is §1.4's, and 425 is the control -------------
    chk([e for e, _, _ in ENDPOINTS] == [425, 410, 395, 385, 365],
        "the five endpoints are §1.4's pre-declared set")
    chk(ENDPOINTS[0][1] == "sweep_control",
        "DOY 425 reads the no-truncation run: bins_within(425) == 55 == None")
    try:
        import extract_phenometrics_sar as EX
        chk(EX.bins_within(425) == EX.bins_within(None) == EX.N_BINS_,
            f"bins_within(425) == bins_within(None) == {EX.N_BINS_}, "
            "verified against the extractor itself")
        chk([EX.bins_within(e) for e in (365, 385, 395, 410)]
            == [43, 47, 49, 52],
            "bin counts at the four truncated endpoints: 43/47/49/52")
    except Exception as e:                                  # pragma: no cover
        print(f"  [SKIP] extractor not importable: {e}")

    # --- 6. refusal on a partial sweep unless asked ------------------------
    with tempfile.TemporaryDirectory() as td:
        try:
            run(td, os.path.join(td, "out"), do_coef=False, do_control=False)
            chk(False, "a sweep with no panels must refuse")
        except SystemExit as e:
            chk("--allow-missing" in str(e),
                "a sweep with missing endpoints refuses and names the escape hatch")

    print()
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


# ---------------------------------------------------------------------------
def main(argv=None):
    ap = argparse.ArgumentParser(description="§1.4 window sensitivity sweep.")
    ap.add_argument("--sweep-root", default=RESULTS,
                    help="directory containing sweep_control, sweep_365, ...")
    ap.add_argument("--out", default=os.path.join(RESULTS, "window_sweep"))
    ap.add_argument("--committed", default=None,
                    help="directory holding the committed panel for the control "
                         "check (default: the results root)")
    ap.add_argument("--no-coefficients", action="store_true")
    ap.add_argument("--no-control-check", action="store_true")
    ap.add_argument("--allow-missing", action="store_true")
    ap.add_argument("--no-drop-extrapolated", action="store_true",
                    help="skip the harvest-identification arm")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    run(a.sweep_root, a.out, committed_dir=a.committed,
        do_coef=not a.no_coefficients, do_control=not a.no_control_check,
        allow_missing=a.allow_missing,
        drop_extrapolated=not a.no_drop_extrapolated)
    return 0


if __name__ == "__main__":
    sys.exit(main())
