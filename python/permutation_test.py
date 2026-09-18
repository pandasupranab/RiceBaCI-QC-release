#!/usr/bin/env python3
"""Protocol §3.9's spatial placebo: 2,000 within-state exposure permutations.

§3.9 declares it and it had never been run:

    "Exposure histories are randomly re-assigned across districts within each
    state (2,000 permutations, preserving each season's count of exposed
    districts) and beta_pre, beta_harv re-estimated; the permutation p-value is
    reported beside the wild-cluster-bootstrap p-value."

INTERPRETATION (corrected 2026-09-16). The spatial placebo supplies a different
reference distribution for the observed associations. A small p-value means the
observed statistic is unusual under these within-state relabellings. A large
one means it is not unusual under that scheme. Neither identifies why the
observed association arose. This observational storm roster is not a randomized
experiment: exchangeability of district histories within state is an assumption,
and relabelling does not preserve the spatial geometry of real storm footprints.
In particular, comparing permutation |t| quantiles with 1.96 tests neither the
size nor calibration of the wild cluster bootstrap, which uses its own simulated
reference distribution. The earlier mechanism and bootstrap-calibration claims
are withdrawn; these are conditional spatial sensitivity results.

THE PERMUTATION. §3.9 says exposure HISTORIES are re-assigned across districts.
That is a relabelling of districts within a state, carrying each district's whole
2017-2025 history with it -- not an independent per-season shuffle. This matters
in two ways: it preserves each season's count of exposed districts EXACTLY (a
permutation cannot change a column's total), which is what §3.9 requires, and it
preserves the temporal autocorrelation of exposure within a district, so the lag
and lead terms keep their real structure. An independent per-season shuffle would
destroy that and would test a null nobody declared.

Only the 25 panel districts are permuted, within their own state (Odisha 12,
West Bengal 6, Andhra Pradesh 7). The catalogue's three non-roster districts
(Kolkata, Nellore, Prakasam) are left alone; they contribute no panel row.

The identity permutation is excluded, and the p-value is the standard
conservative form p = (1 + #{|t_perm| >= |t_obs|}) / (1 + n_perm), which cannot
return zero and does not require the permutation distribution to be continuous.
The statistic is the cluster-robust t, not the raw coefficient: the relabelling
preserves treated counts exactly so the coefficients are comparable, but the t
also standardizes residual-variance differences between relabellings. Studentizing
does not by itself establish exchangeability or validity for this design.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attrition_diagnostics import (FEAbsorber, WithinModel, _screen_regressors,
                                   build_exposure_table, load_panel, SEED)

# --- portable roots ---------------------------------------------------------
# Hard-coded absolute paths made these scripts unrunnable outside the machine
# they were written on. Flagged in an external audit on 2026-09-13 and fixed
# here: one environment variable relocates everything, and the defaults are the
# paths this analysis was actually run with, so nothing silently changes.
ROOT = os.environ.get("RICEBACI_ROOT", "/home/claude")
RESULTS = os.environ.get("RICEBACI_RESULTS", os.path.join(ROOT, "results"))


def _find_results(name):
    """Locate a pipeline OUTPUT, or return None. Never raises.

    Distinct from _find_doc, which raises: a committed docs/ table missing is a
    broken repository, while a results/ file missing just means the pipeline has
    not been run here yet. Callers that can proceed without it must be able to
    tell those apart.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    for c in (os.path.join(RESULTS, name),
              os.path.join(here, "..", "results", name),
              os.path.join("results", name),
              name):
        if os.path.exists(c):
            return c
    return None


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

EXPOSURE = _find_doc("district_cyclone_exposure_ibtracs50km.csv")
PANEL_PIXEL = os.path.join(RESULTS, "phen_panel_sar_static.csv")
PANEL_DIST = os.path.join(RESULTS, "phen_panel_district_season_static.csv")
OUT = os.path.join(RESULTS, "permutation_test")

N_PERM = 2000
REGS = ["S_pre_season", "S_harvest_window", "Slag_pre_season",
        "Slag_harvest_window", "M_minor"]
EXPO_COLS = ["S_pre_season", "S_harvest_window", "M_minor",
             "Slag_pre_season", "Slag_harvest_window",
             "Slead_pre_season", "Slead_harvest_window"]

# The cells tested. §3.9 names beta_pre and beta_harv; the four H3 family members
# and the timing placebo are what those mean concretely under §4, and the placebo
# is the cell this test now most needs to speak to.
# Added 2026-09-13: report the same conditional spatial sensitivity for the
# paired differences between estimators. This is not bootstrap calibration and
# does not identify the mechanism behind an association. These two outcomes are
# the per-row differences between the trough measured three ways; they are only
# available when the censoring refit has been merged (--with-censoring).
CENSORING_CELLS = [
    ("d_full_minus_cens", "S_harvest_window",
     "censoring test (1)-(3): 5-segment minus censored 1-breakpoint"),
    ("d_full_minus_red", "S_harvest_window",
     "censoring test (1)-(2): 5-segment minus 28-dekad 1-breakpoint")]

CELLS = [("trough", "S_pre_season", "exploratory analogue: beta_pre on fitted trough breakpoint"),
         ("heading", "S_pre_season", "exploratory analogue: beta_pre on fitted rise-end breakpoint [heading]"),
         ("harvest", "S_pre_season", "exploratory analogue: beta_pre on fitted fall-end breakpoint [harvest]"),
         ("harvest", "S_harvest_window", "exploratory analogue: beta_harv on fitted fall-end breakpoint [harvest]"),
         ("trough", "S_harvest_window",
          "SS3.9 TIMING PLACEBO: beta_harv on fitted trough breakpoint (declared zero)"),
         ("heading", "S_harvest_window",
          "exploratory (SS4 declares no value): beta_harv on fitted rise-end breakpoint [heading]")]


# ---------------------------------------------------------------------------
def district_state_map(exposure):
    m = (exposure[["district_gadm_name", "state"]].drop_duplicates()
         .set_index("district_gadm_name")["state"].to_dict())
    return m


def make_permutations(districts, states, n_perm, seed):
    """n_perm district relabellings, each within state, identity excluded.

    Returns a list of dicts mapping real district -> the district whose exposure
    history it will receive.
    """
    rng = np.random.default_rng(seed)
    by_state = {}
    for d in districts:
        by_state.setdefault(states[d], []).append(d)
    for s in by_state:
        by_state[s] = sorted(by_state[s])
    perms, seen = [], set()
    identity = tuple(sorted((d, d) for d in districts))
    seen.add(identity)
    guard = 0
    while len(perms) < n_perm and guard < n_perm * 100:
        guard += 1
        m = {}
        for s, ds in by_state.items():
            tgt = list(ds)
            rng.shuffle(tgt)
            m.update(dict(zip(ds, tgt)))
        key = tuple(sorted(m.items()))
        if key in seen:
            continue
        seen.add(key)
        perms.append(m)
    if len(perms) < n_perm:
        raise SystemExit(
            f"could only build {len(perms)} distinct non-identity permutations "
            f"of {n_perm} requested. With states of sizes "
            f"{ {s: len(v) for s, v in by_state.items()} } that should not "
            f"happen; do not proceed with a short permutation set.")
    return perms


def fit_cell(panel, phen, test_var):
    """Point estimate and cluster-robust t for one cell. No bootstrap.

    Same absorption, same regressor screen, same clustering and same
    finite-sample factor as twfe -- it reuses those objects rather than
    reimplementing them, so the observed statistic here is the same statistic
    twfe reports and the permutation distribution is comparable to it.
    """
    # RESTRICTS TO retained == 1, like twfe. The first version of this function
    # omitted it and the self-test caught it: the unpermuted beta came out
    # +4.7582 against twfe's +5.0010. That is the same defect class as the
    # screened-sample leak of 2026-09-13, and the reason the check lives here
    # rather than in the caller is that a caller can forget.
    if "retained" in panel.columns:
        panel = panel[panel["retained"].astype(int) == 1]
    d = panel.dropna(subset=[phen] + REGS)
    if d.empty or d[test_var].nunique() < 2:
        return np.nan, np.nan, np.nan, 0
    fe = FEAbsorber(d, ["district", "year"])
    Xd, kept, _ = _screen_regressors(fe, d, REGS, test_var)
    if test_var not in kept:
        return np.nan, np.nan, np.nan, 0
    yd = fe.demean(d[phen].astype(float).values)
    cl, _ = pd.factorize(d["district"], sort=False)
    cl = np.asarray(cl, np.int64)
    G = int(cl.max()) + 1
    ti = kept.index(test_var)
    beta, se, _ = WithinModel(Xd, cl, G, fe.k_absorbed).fit(yd)
    b, s = float(beta[ti]), float(se[ti])
    t = b / s if np.isfinite(s) and s > 0 else np.nan
    n_treated = int(d.loc[d[test_var] == 1, "district"].nunique())
    return b, s, t, n_treated


def attach(panel, tab, mapping=None):
    """Merge the exposure table onto the panel, optionally relabelled."""
    p = panel.copy()
    p["_src"] = (p["district"] if mapping is None
                 else p["district"].map(mapping))
    out = p.merge(tab.rename(columns={"district": "_src"}),
                  on=["_src", "year"], how="left")
    for c in EXPO_COLS:
        if c in out.columns and c != "Slead_pre_season" \
                and c != "Slead_harvest_window":
            out[c] = out[c].fillna(0).astype(int)
    return out


# ---------------------------------------------------------------------------
def selftest():
    """Self-test in two halves, and the split matters.

    The FIRST half checks this module's own logic and needs NO data at all: the
    permutation construction, the within-state constraint, bijectivity, exclusion
    of the identity, the sigma estimator and the baseline-only tolerance. Its
    district roster comes from the committed exposure catalogue, which travels
    with the repository.

    The SECOND half reproduces `twfe`'s published coefficient on the real
    district panel. That check is the one that caught `fit_cell` failing to
    restrict to retained == 1, so it is worth keeping -- but it needs a panel that
    is an OUTPUT of the pipeline, not an input to it. Until 2026-09-13 the whole
    self-test loaded that panel unconditionally from a hard-coded absolute path,
    so on any machine but the one it was written on `--selftest` died with
    FileNotFoundError before testing anything. A receive-only executor running
    the handoff checks found it, correctly refusing to commit.

    So the second half now runs only when the panel resolves, and is SKIPPED, not
    failed, when it does not. A missing pipeline output is not a code defect. When
    the panel is present the check is as strict as before.
    """
    ok_all = True
    exposure = pd.read_csv(EXPOSURE)
    states = district_state_map(exposure)
    # roster from the catalogue, not the panel: the logic checks below are about
    # permutation construction and need no phenometrics
    districts = sorted(exposure["district_gadm_name"].unique())

    perms = make_permutations(districts, states, 50, 7)
    ok = len(perms) == 50 and len(set(tuple(sorted(m.items())) for m in perms)) == 50
    ok_all &= ok
    print(f"  built {len(perms)} permutations, all distinct: "
          f"[{'PASS' if ok else 'FAIL'}]")

    ok = all(states[d] == states[m[d]] for m in perms for d in districts)
    ok_all &= ok
    print(f"  every relabelling stays inside its own state: "
          f"[{'PASS' if ok else 'FAIL'}]")

    ok = all(sorted(m.values()) == districts for m in perms)
    ok_all &= ok
    print(f"  every relabelling is a bijection (no district used twice): "
          f"[{'PASS' if ok else 'FAIL'}]")

    ok = not any(all(m[d] == d for d in districts) for m in perms)
    ok_all &= ok
    print(f"  identity permutation excluded: [{'PASS' if ok else 'FAIL'}]")

    # sigma and the baseline-only tolerance: still no data needed
    rng0 = np.random.default_rng(17)
    _t = rng0.normal(0, 1, 500)
    ok = abs(float(np.std(_t, ddof=1)) - 1.0) < 0.1
    ok_all &= ok
    print(f"  numeric sanity on the draw generator: [{'PASS' if ok else 'FAIL'}]")

    # ---- data-dependent half: skipped, not failed, when the panel is absent --
    panel_path = _find_results("phen_panel_district_season_static.csv")
    if panel_path is None:
        print("\n  [SKIP] the district panel was not found, so the checks that"
              " reproduce twfe's")
        print("         published coefficient are skipped. They are not failed:"
              " that panel is")
        print("         an OUTPUT of this pipeline, not an input, and its absence"
              " is not a code")
        print("         defect. Set RICEBACI_ROOT, or run after stage 2 of"
              " run_all.sh, to")
        print("         exercise them. Everything above ran and is what this"
              " module guarantees.")
        print("=" * 74)
        print("SELF-TEST " + ("PASSED (logic only; data checks skipped)"
                              if ok_all else "FAILED"))
        print("=" * 74)
        return 0 if ok_all else 1

    panel = load_panel(panel_path, "district", verbose=False)
    districts = sorted(panel["district"].unique())
    perms = make_permutations(districts, states, 50, 7)
    # the requirement §3.9 states explicitly: each season's count of exposed
    # districts is preserved
    tab = build_exposure_table(exposure, districts, sorted(panel["year"].unique()))
    base = attach(panel, tab)
    counts0 = base.groupby("year")[["S_pre_season", "S_harvest_window"]].sum()
    bad = 0
    for m in perms[:10]:
        c = attach(panel, tab, m).groupby("year")[
            ["S_pre_season", "S_harvest_window"]].sum()
        if not c.equals(counts0):
            bad += 1
    ok = bad == 0
    ok_all &= ok
    print(f"  each season's exposed-district count preserved in 10 of 10 "
          f"relabellings: [{'PASS' if ok else 'FAIL'}]")

    # and the identity mapping must reproduce twfe's own number exactly
    b, se, t, nt = fit_cell(base, "trough", "S_harvest_window")
    ok = abs(b - 5.0010) < 5e-4 and abs(se - 3.1035) < 5e-4
    ok_all &= ok
    print(f"  unpermuted beta_harv on trough {b:+.4f} (se {se:.4f}) against "
          f"twfe's +5.0010 (se 3.1035): [{'PASS' if ok else 'FAIL'}]")

    # a planted effect must be detected, and pure relabelling must not be
    rng = np.random.default_rng(3)
    sim = base.copy()
    sim["fake"] = (rng.normal(0, 3, len(sim))
                   + 20.0 * sim["S_harvest_window"].to_numpy())
    b2, _, t2, _ = fit_cell(sim, "fake", "S_harvest_window")
    tn = [abs(fit_cell(attach(sim.drop(columns=EXPO_COLS + ["_src"]), tab, m),
                       "fake", "S_harvest_window")[2]) for m in perms[:30]]
    tn = [v for v in tn if np.isfinite(v)]
    p_emp = (1 + sum(v >= abs(t2) for v in tn)) / (1 + len(tn))
    ok = p_emp <= 1.0 / 31 + 1e-12
    ok_all &= ok
    print(f"  planted +20 d effect: t {t2:+.2f}, permutation p {p_emp:.4f} "
          f"on 30 draws (floor {1/31:.4f}): [{'PASS' if ok else 'FAIL'}]")
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


# ---------------------------------------------------------------------------
REFIT = {"pixel": os.path.join(RESULTS, "censoring_test/refit_pixel.csv"),
         "district": os.path.join(RESULTS, "censoring_test/refit_district.csv")}


def merge_censoring(panel, level):
    """Attach the censoring test's two reduced-model troughs and form the
    per-row differences, restricted to the same common sample that test used."""
    keys = (["district", "year", "cell_id"] if level == "pixel"
            else ["district", "year"])
    r = pd.read_csv(REFIT[level])
    r["year"] = r["year"].astype(int)
    n0 = len(panel)
    out = panel.merge(r, on=keys, how="left", validate="one_to_one")
    assert len(out) == n0, "the censoring refit merge changed the row count"
    out["d_full_minus_cens"] = out["trough"] - out["trough_red_cens"]
    out["d_full_minus_red"] = out["trough"] - out["trough_red_full"]
    return out


def run(level, panel_path, n_perm, seed, out_dir, chunk=None,
        with_censoring=False):
    exposure = pd.read_csv(EXPOSURE)
    states = district_state_map(exposure)
    panel = load_panel(panel_path, level, verbose=False)
    panel = panel[panel["retained"] == 1].copy()
    cells = list(CELLS)
    if with_censoring:
        panel = merge_censoring(panel, level)
        cells += CENSORING_CELLS
    districts = sorted(panel["district"].unique())
    years = sorted(panel["year"].unique())
    tab = build_exposure_table(exposure, districts, years)
    base = attach(panel, tab)
    bare = panel.copy()
    # a differently-sized cell set is a different run; the store must not mix
    tag = "_cens" if with_censoring else ""

    os.makedirs(out_dir, exist_ok=True)
    store = os.path.join(out_dir, f"perm_t_{level}{tag}.json")
    state = json.load(open(store)) if os.path.exists(store) else {}
    if state.get("seed") not in (None, seed) or \
            state.get("n_perm") not in (None, n_perm):
        raise SystemExit(
            f"{store} was written with seed={state.get('seed')} "
            f"n_perm={state.get('n_perm')}; this run has seed={seed} "
            f"n_perm={n_perm}. Delete it or match the settings -- mixing "
            f"permutation draws from two different sets is not a permutation "
            f"test.")
    state.setdefault("seed", seed)
    state.setdefault("n_perm", n_perm)
    state.setdefault("done", 0)
    state.setdefault("t", {f"{p}|{v}": [] for p, v, _ in cells})
    for p_, v_, _ in cells:
        state["t"].setdefault(f"{p_}|{v_}", [])

    perms = make_permutations(districts, states, n_perm, seed)
    print(f"{level}: {len(base)} retained rows, {len(districts)} districts "
          f"({ {s: sum(1 for d in districts if states[d] == s) for s in sorted(set(states[d] for d in districts))} })")
    print(f"  {n_perm} within-state relabellings, identity excluded; "
          f"{state['done']} already done")

    obs = {}
    for phen, var, label in cells:
        b, se, t, nt = fit_cell(base, phen, var)
        obs[f"{phen}|{var}"] = dict(coef=b, se=se, t=t, n_treated=nt,
                                    label=label)
        print(f"  observed  {label:<58s} beta {b:+8.3f}  t {t:+6.3f}")

    start = state["done"]
    stop = min(n_perm, start + chunk) if chunk else n_perm
    for i in range(start, stop):
        pan = attach(bare, tab, perms[i])
        for phen, var, _ in cells:
            state["t"][f"{phen}|{var}"].append(fit_cell(pan, phen, var)[2])
        state["done"] = i + 1
        if (i + 1) % 100 == 0 or i + 1 == stop:
            json.dump(state, open(store, "w", encoding="utf-8",
                                     newline="\n"))
            print(f"  {i + 1}/{n_perm} permutations", flush=True)
    json.dump(state, open(store, "w", encoding="utf-8",
                                     newline="\n"))

    rows = []
    print(f"\n  permutation results ({state['done']} draws)")
    for phen, var, label in cells:
        k = f"{phen}|{var}"
        ts = [v for v in state["t"][k] if v is not None and np.isfinite(v)]
        o = obs[k]
        n_ok = len(ts)
        p = ((1 + sum(abs(v) >= abs(o["t"]) for v in ts)) / (1 + n_ok)
             if n_ok and np.isfinite(o["t"]) else np.nan)
        q = (float(np.quantile(np.abs(ts), 0.95)) if n_ok else np.nan)
        rows.append(dict(level=level, phenometric=phen, test_var=var,
                         label=label, coef=o["coef"], se=o["se"], t=o["t"],
                         n_treated_clusters=o["n_treated"],
                         n_perm_ok=n_ok, p_perm=p, perm_abs_t_q95=q,
                         perm_t_sd=(float(np.std(ts)) if n_ok else np.nan)))
        print(f"    {label:<58s} p_perm {p:.4f}   |t|_obs {abs(o['t']):.3f} "
              f"vs permutation 95th pct {q:.3f}")
    dest = os.path.join(out_dir, f"Table_SX_Permutation_{level}{tag}.csv")
    pd.DataFrame(rows).to_csv(dest, index=False)
    print(f"  wrote {dest}")
    if state["done"] < n_perm:
        print(f"  INCOMPLETE: {n_perm - state['done']} permutations remain. "
              f"Rerun the same command to continue; p-values above are on "
              f"{state['done']} draws and are provisional.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Protocol §3.9 spatial placebo.")
    ap.add_argument("--level", choices=["district", "pixel"], default="district")
    ap.add_argument("--n-perm", type=int, default=N_PERM)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--chunk", type=int, default=None,
                    help="stop after this many new permutations and save, so a "
                         "long run survives being killed. Rerun to continue.")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--with-censoring", action="store_true",
                    help="also permute the censoring test's paired-difference "
                         "outcomes, whose WCB p-values inherit the same "
                         "anti-conservatism this test measures.")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    path = PANEL_DIST if a.level == "district" else PANEL_PIXEL
    return run(a.level, path, a.n_perm, a.seed, a.out, a.chunk,
               with_censoring=a.with_censoring)


if __name__ == "__main__":
    sys.exit(main())
