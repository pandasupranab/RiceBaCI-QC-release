"""
gate1_justification.py -- Protocol §3.1's pre-declared Gate 1 justification test.

§3.1 (added 2026-09-09): "Phenometrics are extracted twice on the same cohort and the
same panel, once with Gate 1 applied and once without, and the two are compared on:
fit quality... temporal stability... spatial coherence... orbit agreement... Gate 1 is
retained only if it improves these on the majority of criteria. If it does not, it is
reported as a tested and rejected QC step, which is a result rather than a failure."

WHY THIS MODULE EXISTS, stated plainly. §3.1's third 2026-09-12 entry already decided
that Gate 1 is **not applied at pixel level** on the radar substrate, and justified it
with four summary statistics measured on the **2017 baseline season alone**: median
valid dekads 26 against 24, minimum 19 against 10, the §3.11 fraction 1.0000 against
0.9993, retention 0.2426 against 0.2544. Those are real and they point the same way as
what follows. But they are **not the declared test**: the declaration names four named
criteria, three of which (temporal stability, spatial coherence, orbit agreement) cannot
be evaluated on one season at all, and it asks for them over the whole panel. A decision
taken on narrower evidence than the protocol declared is exactly the kind of thing an
external re-audit converts into "the pre-declared test was not run". It is run here.

OPERATIONALISATION, and it is declared here because §3.1 names the criteria without
fixing the statistics. Each criterion reduces to one directional statistic per marker;
"improves" means the gate-on arm is better by more than TOL on that statistic.

  1. fit quality        median RMSR over retained pixel-seasons   (lower better)
                        + retention share of attempted            (higher better)
  2. temporal stability median over pixels of the within-pixel SD of the marker
                        across seasons, after removing season means (lower better)
  3. spatial coherence  median within-district SD of the marker    (lower better)
                        + the semivariogram nugget at the shortest lag (lower better)
  4. orbit agreement    sigma_single from the paired-orbit difference (lower better)
                        + the share of pairs within the 2017-fixed tolerance (higher)

A criterion counts as improved only if **every** sub-statistic it carries moves
favourably. Where sub-statistics disagree the criterion is **MIXED**, and mixed is not
an improvement: §3.1 says Gate 1 is retained only if it *improves*, so ambiguity
resolves against retention rather than for it.

THE CONFOUND THIS MODULE REFUSES TO IGNORE. Gate 1 deletes five-day bins, which changes
which pixel-seasons are eligible and retained at all. A gate that happens to delete the
noisiest pixels will appear to improve every dispersion statistic **purely by sample
selection**, with no improvement in measurement whatever. So every criterion is computed
twice:

  * `as_is`  -- each arm on its own retained set. This is what the gate delivers in
               practice, and it is the arm §3.1's decision rule should read.
  * `common` -- both arms restricted to the pixel-seasons retained in BOTH. This holds
               the sample fixed and isolates the gate's effect on the estimate.

A gate that improves `as_is` but not `common` is selecting, not measuring, and the
output says so in those words.

    python python/gate1_justification.py --off results/phen_panel_sar.csv \\
        --on results/gate1_on/phen_panel_sar.csv --out results/gate1_justification
    python python/gate1_justification.py --selftest

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

CSV_FLOAT = "%.12g"
MARKERS = ["trough", "heading", "harvest"]
TOL = 1e-9          # a difference at or below this is "unchanged", not an improvement
KEY = ["district", "year", "cell_id"]

# direction[statistic] = -1 if lower is better, +1 if higher is better
DIRECTION = {
    "rmsr_median": -1, "retention_share": +1,
    "within_pixel_sd_median": -1,
    "within_district_sd_median": -1, "nugget_rms_d": -1,
    "sigma_single": -1, "within_tolerance_share": +1,
}
CRITERION_STATS = {
    "fit_quality": ["rmsr_median", "retention_share"],
    "temporal_stability": ["within_pixel_sd_median"],
    "spatial_coherence": ["within_district_sd_median", "nugget_rms_d"],
    "orbit_agreement": ["sigma_single", "within_tolerance_share"],
}


# ---------------------------------------------------------------------------
def load(path, label):
    d = pd.read_csv(path)
    need = KEY + ["retained", "rmse"] + MARKERS
    missing = [c for c in need if c not in d.columns]
    if missing:
        raise SystemExit(f"{label} ({path}): missing columns {missing}")
    d["retained"] = d["retained"].astype(int)
    print(f"  {label:8s} {len(d):,} pixel-seasons, {int(d['retained'].sum()):,} "
          f"retained ({d['retained'].mean():.4f})")
    return d


def fit_quality(d):
    r = d[d["retained"] == 1]
    return {"rmsr_median": float(np.nanmedian(r["rmse"])) if len(r) else np.nan,
            "retention_share": float(d["retained"].mean()) if len(d) else np.nan,
            "n_retained": int(len(r)), "n_attempted": int(len(d))}


def within_pixel_sd(d, marker):
    """Median over pixels of the within-pixel SD across seasons, season means removed.

    Season means are removed first because a genuine coast-wide shift between years is
    not instability of the instrument. Pixels with fewer than two retained seasons
    carry no within-pixel dispersion and are excluded, and the count is reported --
    the gate changes how many pixels qualify, and that is itself informative.
    """
    r = d[(d["retained"] == 1) & d[marker].notna()].copy()
    if not len(r):
        return np.nan, 0
    r["_dm"] = r[marker] - r.groupby("year")[marker].transform("mean")
    g = r.groupby("cell_id")["_dm"]
    sd = g.std(ddof=1)[g.count() >= 2]
    return (float(np.nanmedian(sd)) if len(sd) else np.nan), int(len(sd))


def within_district_sd(d, marker):
    r = d[(d["retained"] == 1) & d[marker].notna()]
    if not len(r):
        return np.nan, 0
    sd = r.groupby(["district", "year"])[marker].std(ddof=1)
    sd = sd[r.groupby(["district", "year"])[marker].count() >= 2]
    return (float(np.nanmedian(sd)) if len(sd) else np.nan), int(len(sd))


def nugget(d, marker, max_cells=1200, seed=20260913):
    """Semivariogram nugget at the shortest lag, via python/semivariance.py.

    Imported rather than reimplemented so that the number here is the same estimator
    §3.4 Tier 1 reports. Subsamples cells for tractability with a fixed seed, and the
    SAME cells are used for both arms by the caller.
    """
    try:
        import semivariance as SV
    except Exception as e:                                   # pragma: no cover
        print(f"    semivariance unavailable ({e}); nugget skipped")
        return np.nan, 0
    if not {"lon", "lat"} <= set(d.columns):
        return np.nan, 0
    r = d[(d["retained"] == 1) & d[marker].notna()
          & d["lon"].notna() & d["lat"].notna()]
    if len(r) < 50:
        return np.nan, 0
    edges = SV.LAG_EDGES_KM
    nlag = len(edges) - 1
    sums = np.zeros(nlag)
    cnts = np.zeros(nlag, dtype=np.int64)
    rng = np.random.default_rng(seed)
    for _, g in r.groupby(["district", "year"], sort=True):
        if len(g) > max_cells:
            g = g.iloc[np.sort(rng.choice(len(g), max_cells, replace=False))]
        # NOTE the argument order: semivariogram_cell(lat, lon, z). Passing lon
        # first silently computes a distance matrix with the axes swapped, which
        # still returns numbers. The first version of this call did exactly that.
        sc, cc = SV.semivariogram_cell(g["lat"].to_numpy(float),
                                       g["lon"].to_numpy(float),
                                       g[marker].to_numpy(float), edges)
        sums += sc
        cnts += cc
    # gamma = 0.5 * sum of squared differences / pair count, pooled pair-weighted,
    # exactly as semivariance.pool forms it; the nugget is the shortest lag with
    # at least MIN_PAIRS_PER_LAG pairs, exactly as nugget_and_sill selects it.
    for k in range(nlag):
        if cnts[k] >= SV.MIN_PAIRS_PER_LAG:
            gam = 0.5 * sums[k] / cnts[k]
            if np.isfinite(gam):
                return float(np.sqrt(max(gam, 0.0))), int(cnts[k])
    return np.nan, 0


# ---------------------------------------------------------------------------
def compare(off, on, orbit=None):
    """One row per (criterion, statistic, marker, sample) with the verdict."""
    common = (off.loc[off["retained"] == 1, KEY]
              .merge(on.loc[on["retained"] == 1, KEY], on=KEY, how="inner"))
    print(f"  retained in BOTH arms: {len(common):,}")

    def restrict(d):
        m = d.merge(common.assign(_k=1), on=KEY, how="left")
        m["retained"] = np.where(m["_k"].eq(1), 1, 0)
        return m.drop(columns=["_k"])

    arms = {"as_is": (off, on), "common": (restrict(off), restrict(on))}
    rows = []

    def add(sample, crit, stat, marker, v_off, v_on, n_off=None, n_on=None):
        d = DIRECTION[stat]
        delta = v_on - v_off if np.isfinite(v_on) and np.isfinite(v_off) else np.nan
        if not np.isfinite(delta):
            verdict = "not evaluable"
        elif abs(delta) <= TOL:
            verdict = "unchanged"
        else:
            verdict = "improves" if (delta * d) > 0 else "worsens"
        rows.append({"sample": sample, "criterion": crit, "statistic": stat,
                     "marker": marker, "gate_off": v_off, "gate_on": v_on,
                     "delta_on_minus_off": delta,
                     "better_direction": "lower" if d < 0 else "higher",
                     "verdict": verdict, "n_off": n_off, "n_on": n_on})

    for sample, (a, b) in arms.items():
        fa, fb = fit_quality(a), fit_quality(b)
        add(sample, "fit_quality", "rmsr_median", "all",
            fa["rmsr_median"], fb["rmsr_median"], fa["n_retained"], fb["n_retained"])
        if sample == "as_is":      # retention is meaningless on a fixed common subset
            add(sample, "fit_quality", "retention_share", "all",
                fa["retention_share"], fb["retention_share"],
                fa["n_attempted"], fb["n_attempted"])
        for mk in MARKERS:
            va, na = within_pixel_sd(a, mk)
            vb, nb = within_pixel_sd(b, mk)
            add(sample, "temporal_stability", "within_pixel_sd_median", mk,
                va, vb, na, nb)
            va, na = within_district_sd(a, mk)
            vb, nb = within_district_sd(b, mk)
            add(sample, "spatial_coherence", "within_district_sd_median", mk,
                va, vb, na, nb)
            va, na = nugget(a, mk)
            vb, nb = nugget(b, mk)
            add(sample, "spatial_coherence", "nugget_rms_d", mk, va, vb, na, nb)

    if orbit is not None and len(orbit):
        for _, r in orbit.iterrows():
            add("as_is", "orbit_agreement", r["statistic"], r["marker"],
                float(r["gate_off"]), float(r["gate_on"]))
    return pd.DataFrame(rows)


def verdict(cmp_df, sample="as_is"):
    """Criterion-level and overall verdicts under §3.1's majority rule."""
    sub = cmp_df[cmp_df["sample"] == sample]
    rows = []
    for crit, stats in CRITERION_STATS.items():
        c = sub[sub["criterion"] == crit]
        if not len(c) or (c["verdict"] == "not evaluable").all():
            rows.append({"criterion": crit, "verdict": "NOT EVALUABLE",
                         "n_improves": 0, "n_worsens": 0, "n_unchanged": 0,
                         "n_not_evaluable": int(len(c))})
            continue
        ni = int((c["verdict"] == "improves").sum())
        nw = int((c["verdict"] == "worsens").sum())
        nu = int((c["verdict"] == "unchanged").sum())
        nn = int((c["verdict"] == "not evaluable").sum())
        if nw == 0 and ni > 0:
            v = "IMPROVES"
        elif ni == 0 and nw > 0:
            v = "WORSENS"
        elif ni and nw:
            v = "MIXED"
        else:
            v = "UNCHANGED"
        rows.append({"criterion": crit, "verdict": v, "n_improves": ni,
                     "n_worsens": nw, "n_unchanged": nu, "n_not_evaluable": nn})
    cv = pd.DataFrame(rows)
    ev = cv[cv["verdict"] != "NOT EVALUABLE"]
    n_imp = int((ev["verdict"] == "IMPROVES").sum())
    n_eval = int(len(ev))
    overall = ("RETAIN Gate 1" if n_eval and n_imp * 2 > n_eval
               else "REJECT Gate 1 as a tested QC step")
    return cv, overall, n_imp, n_eval


# ---------------------------------------------------------------------------
def write_summary(out_dir, cmp_df, cv, overall, n_imp, n_eval, cv_c, ov_c):
    L, A = [], None
    A = L.append
    A("# §3.1 Gate 1 justification test")
    A("")
    A("Pre-declared in §3.1 (2026-09-09): the panel is extracted twice, with Gate 1")
    A("applied and without, and compared on four named criteria. **Gate 1 is retained")
    A("only if it improves these on the majority of criteria.** The statistics that")
    A("stand for each criterion are declared in `python/gate1_justification.py`'s")
    A("docstring, because §3.1 names the criteria without fixing them.")
    A("")
    A(f"## Verdict: **{overall}** — improves {n_imp} of {n_eval} evaluable criteria")
    A("")
    A("| criterion | verdict | improves | worsens | unchanged |")
    A("|---|---|---:|---:|---:|")
    for _, r in cv.iterrows():
        A(f"| {r['criterion'].replace('_',' ')} | **{r['verdict']}** | "
          f"{r['n_improves']} | {r['n_worsens']} | {r['n_unchanged']} |")
    A("")
    A("A criterion counts as improved only if every statistic it carries moves")
    A("favourably. Where they disagree it is MIXED, and mixed is not an improvement:")
    A("§3.1 retains Gate 1 only if it *improves*, so ambiguity resolves against")
    A("retention.")
    A("")
    A("## The sample-selection confound, and what it shows")
    A("")
    A("Gate 1 deletes five-day bins, which changes which pixel-seasons are retained at")
    A("all. A gate that deletes the noisiest pixels improves every dispersion")
    A("statistic by **sample selection alone**, with no better measurement. So each")
    A("criterion is computed twice: `as_is` on each arm's own retained set, and")
    A("`common` on the pixel-seasons retained in both.")
    A("")
    A(f"On the fixed common subset the verdict is **{ov_c}**.")
    A("")
    A("| criterion | as_is | common |")
    A("|---|---|---|")
    cvi = cv.set_index("criterion"); cci = cv_c.set_index("criterion")
    for crit in CRITERION_STATS:
        a = cvi.loc[crit, "verdict"] if crit in cvi.index else "--"
        b = cci.loc[crit, "verdict"] if crit in cci.index else "--"
        A(f"| {crit.replace('_',' ')} | {a} | {b} |")
    A("")
    A("Read the two columns together. A criterion that improves `as_is` but not")
    A("`common` is the gate **selecting** rather than measuring.")
    A("")
    A("## Every statistic")
    A("")
    A("| sample | criterion | statistic | marker | gate off | gate on | Δ | better | verdict |")
    A("|---|---|---|---|---:|---:|---:|---|---|")
    for _, r in cmp_df.iterrows():
        f = lambda x: "--" if not np.isfinite(x) else f"{x:.4f}"
        A(f"| {r['sample']} | {r['criterion'].replace('_',' ')} | "
          f"`{r['statistic']}` | {r['marker']} | {f(r['gate_off'])} | "
          f"{f(r['gate_on'])} | {f(r['delta_on_minus_off'])} | "
          f"{r['better_direction']} | {r['verdict']} |")
    A("")
    p = os.path.join(out_dir, "gate1_justification_summary.md")
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"  wrote {p}")


def build_orbit_criterion(off_dir, on_dir, out_path):
    """Assemble the orbit-agreement criterion from two orbit_agreement output dirs.

    Lives here rather than as inline shell in run_all.sh: a pipeline stage that
    reduces two result directories to a comparison is analysis, and analysis in a
    shell heredoc cannot be self-tested. Reads the ALL scope only, which is the
    scope §2's clause (a) is stated on.
    """
    rows = []
    for lab, base in (("gate_off", off_dir), ("gate_on", on_dir)):
        ap_ = os.path.join(base, "Table_SX_OrbitAgreement.csv")
        dp_ = os.path.join(base, "Table_SX_DispersionSingleOrbit.csv")
        for q in (ap_, dp_):
            if not os.path.exists(q):
                raise SystemExit(
                    f"{q} absent. The orbit-agreement criterion needs both arms; run "
                    "orbit_agreement.py --fit --agree for each, the gate-on arm with "
                    "--gate1-r 0.50.")
        a = pd.read_csv(ap_)
        a = a[a["scope"] == "ALL"].set_index("marker")
        d = pd.read_csv(dp_).set_index("marker")
        for mk in MARKERS:
            rows.append({"arm": lab, "marker": mk,
                         "sigma_single": float(d.loc[mk, "sigma_single"]),
                         "within_tolerance_share": float(a.loc[mk, "frac_within_T"])})
    w = pd.DataFrame(rows).pivot(index="marker", columns="arm")
    out = [{"statistic": st, "marker": mk,
            "gate_off": float(w[(st, "gate_off")][mk]),
            "gate_on": float(w[(st, "gate_on")][mk])}
           for mk in MARKERS
           for st in ("sigma_single", "within_tolerance_share")]
    t = pd.DataFrame(out)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    t.to_csv(out_path, index=False, float_format=CSV_FLOAT)
    print(f"  wrote {out_path}  ({len(t)} rows: the fourth criterion)")
    return t


def run(off_path, on_path, out_dir, orbit_path=None):
    os.makedirs(out_dir, exist_ok=True)
    off = load(off_path, "gate OFF")
    on = load(on_path, "gate ON")
    orbit = pd.read_csv(orbit_path) if orbit_path and os.path.exists(orbit_path) \
        else None
    cmp_df = compare(off, on, orbit)
    cv, overall, n_imp, n_eval = verdict(cmp_df, "as_is")
    cv_c, ov_c, _, _ = verdict(cmp_df, "common")
    for nm, df in (("Table_SX_Gate1Justification.csv", cmp_df),
                   ("Table_SX_Gate1Verdict.csv",
                    cv.assign(sample="as_is")._append(cv_c.assign(sample="common"))
                    if hasattr(cv, "_append")
                    else pd.concat([cv.assign(sample="as_is"),
                                    cv_c.assign(sample="common")],
                                   ignore_index=True))):
        p = os.path.join(out_dir, nm)
        df.to_csv(p, index=False, float_format=CSV_FLOAT)
        print(f"  wrote {p}  ({len(df)} rows)")
    write_summary(out_dir, cmp_df, cv, overall, n_imp, n_eval, cv_c, ov_c)
    print()
    print("=" * 74)
    print(f"§3.1 GATE 1 VERDICT: {overall}")
    print(f"  improves {n_imp} of {n_eval} evaluable criteria on its own retained set")
    print(f"  on the fixed common subset: {ov_c}")
    print("=" * 74)
    return cmp_df, cv, overall


# ---------------------------------------------------------------------------
def selftest():
    print("=" * 74)
    print("SELF-TEST -- gate1_justification.py")
    print("=" * 74)
    ok_all = True

    def chk(cond, msg):
        nonlocal ok_all
        ok_all &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")

    rng = np.random.default_rng(5)

    def panel(n_cell=60, n_year=6, sd=6.0, rmsr=1.0, keep=1.0, seed=0):
        r2 = np.random.default_rng(seed)
        rows = []
        for c in range(n_cell):
            base = 210.0 + r2.normal(0, 10)
            for y in range(2017, 2017 + n_year):
                rows.append({
                    "district": f"D{c % 3}", "year": y, "cell_id": f"c{c}",
                    "lon": 85.0 + 0.01 * (c % 20), "lat": 20.0 + 0.01 * (c // 20),
                    "retained": int(r2.random() < keep), "rmse": rmsr,
                    "trough": base + r2.normal(0, sd),
                    "heading": base + 70 + r2.normal(0, sd),
                    "harvest": base + 150 + r2.normal(0, sd)})
        return pd.DataFrame(rows)

    # --- 1. an unambiguously better gate-on arm is called IMPROVES ---------
    off = panel(sd=9.0, rmsr=1.20, seed=1)
    on = off.copy()
    for mk in MARKERS:                      # halve the noise about each pixel's mean
        m = on.groupby("cell_id")[mk].transform("mean")
        on[mk] = m + (on[mk] - m) * 0.4
    on["rmse"] = 0.80
    cmp_df = compare(off, on)
    cv, overall, ni, ne = verdict(cmp_df, "as_is")
    chk(cv.set_index("criterion").loc["temporal_stability", "verdict"] == "IMPROVES",
        "halving within-pixel scatter reads as temporal_stability IMPROVES")
    chk(cv.set_index("criterion").loc["fit_quality", "verdict"] == "IMPROVES",
        "lower RMSR with equal retention reads as fit_quality IMPROVES")
    chk(overall.startswith("RETAIN"), f"and the overall verdict is RETAIN ({overall})")

    # --- 2. an identical arm is UNCHANGED and therefore REJECT -------------
    cmp2 = compare(off, off.copy())
    cv2, ov2, _, _ = verdict(cmp2, "as_is")
    chk((cv2["verdict"].isin(["UNCHANGED", "NOT EVALUABLE"])).all(),
        "an identical gate-on arm is UNCHANGED on every criterion")
    chk(ov2.startswith("REJECT"),
        "unchanged is not an improvement, so the rule REJECTS -- §3.1 retains Gate 1 "
        "only if it IMPROVES")

    # --- 3. a worse arm WORSENS -------------------------------------------
    worse = off.copy()
    for mk in MARKERS:
        m = worse.groupby("cell_id")[mk].transform("mean")
        worse[mk] = m + (worse[mk] - m) * 2.5
    worse["rmse"] = 1.9
    cv3, ov3, _, _ = verdict(compare(off, worse), "as_is")
    chk(cv3.set_index("criterion").loc["temporal_stability", "verdict"] == "WORSENS"
        and ov3.startswith("REJECT"),
        "an arm with inflated scatter WORSENS and is REJECTED")

    # --- 4. MIXED is not an improvement -----------------------------------
    rows = pd.DataFrame([
        {"sample": "as_is", "criterion": "spatial_coherence",
         "statistic": "within_district_sd_median", "marker": "trough",
         "gate_off": 5.0, "gate_on": 4.0, "delta_on_minus_off": -1.0,
         "better_direction": "lower", "verdict": "improves", "n_off": 1, "n_on": 1},
        {"sample": "as_is", "criterion": "spatial_coherence",
         "statistic": "nugget_rms_d", "marker": "trough",
         "gate_off": 20.0, "gate_on": 25.0, "delta_on_minus_off": 5.0,
         "better_direction": "lower", "verdict": "worsens", "n_off": 1, "n_on": 1}])
    cv4, ov4, ni4, ne4 = verdict(rows, "as_is")
    chk(cv4.set_index("criterion").loc["spatial_coherence", "verdict"] == "MIXED",
        "one statistic improving and one worsening gives MIXED")
    chk(ni4 == 0 and ov4.startswith("REJECT"),
        "MIXED does not count toward the majority")

    # --- 5. the sample-selection confound is caught -----------------------
    # gate-on retains only the quietest half; per-pixel scatter is IDENTICAL on the
    # pixels both arms keep, so `as_is` must improve while `common` does not.
    off5 = panel(sd=9.0, seed=3)
    on5 = off5.copy()
    # select on the MEAN within-pixel SD across all three markers, not on one:
    # the criterion spans three markers, so a gate that quietens only `trough`
    # leaves the other two unchanged and the criterion reads MIXED. The first
    # version of this test did that and failed for a reason in the test, not the
    # code -- recorded because a self-test that fails wrongly teaches nothing.
    dev = sum(off5.groupby("cell_id")[mk].transform("std") for mk in MARKERS) / 3.0
    quiet = dev <= dev.median()
    on5["retained"] = np.where(quiet, off5["retained"], 0)
    c5 = compare(off5, on5)
    v_as, o_as, _, _ = verdict(c5, "as_is")
    v_cm, o_cm, _, _ = verdict(c5, "common")
    chk(v_as.set_index("criterion").loc["temporal_stability", "verdict"] == "IMPROVES",
        "a gate that keeps only the quietest pixels IMPROVES on its own retained set")
    chk(v_cm.set_index("criterion").loc["temporal_stability", "verdict"]
        in ("UNCHANGED", "NOT EVALUABLE"),
        "and does NOT improve on the fixed common subset -- selection, not measurement")

    # --- 6. season means are removed before measuring stability ----------
    shifted = panel(sd=0.0, seed=7)         # zero within-pixel noise...
    for i, y in enumerate(sorted(shifted["year"].unique())):
        shifted.loc[shifted["year"] == y, MARKERS] += i * 20.0   # ...big season shifts
    v, n = within_pixel_sd(shifted, "trough")
    chk(np.isfinite(v) and v < 1e-6,
        f"a coast-wide season shift is removed and leaves SD {v:.2e}, not ~20 d")

    # --- 6b. the orbit criterion is assembled, not hand-copied -----------
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        for lab, sig, frac in (("off", 25.9, 0.944), ("on", 26.4, 0.930)):
            dd = os.path.join(td, lab)
            os.makedirs(dd)
            pd.DataFrame([{"marker": mk, "scope": sc, "frac_within_T": frac,
                           "tolerance_d": 70.0, "n": 100}
                          for mk in MARKERS
                          for sc in ("ALL", "Odisha")]).to_csv(
                os.path.join(dd, "Table_SX_OrbitAgreement.csv"), index=False)
            pd.DataFrame([{"marker": mk, "sigma_single": sig} for mk in MARKERS]
                         ).to_csv(os.path.join(
                dd, "Table_SX_DispersionSingleOrbit.csv"), index=False)
        t = build_orbit_criterion(os.path.join(td, "off"), os.path.join(td, "on"),
                                  os.path.join(td, "o", "orbit_criterion.csv"))
        chk(len(t) == 6 and set(t["statistic"]) == {"sigma_single",
                                                   "within_tolerance_share"},
            "the orbit criterion is six rows: two statistics x three markers")
        chk(bool((t["gate_on"] > t["gate_off"]).sum() == 3),
            "and it carries both arms' values rather than a difference")
        # it must read the ALL scope, not the first row it finds
        chk(abs(float(t[t["statistic"] == "within_tolerance_share"]
                      ["gate_off"].iloc[0]) - 0.944) < 1e-12,
            "the ALL scope is selected, which is the scope §2 clause (a) is stated on")
        cvo, ovo, _, _ = verdict(
            pd.concat([pd.DataFrame([{
                "sample": "as_is", "criterion": "orbit_agreement",
                "statistic": r["statistic"], "marker": r["marker"],
                "gate_off": r["gate_off"], "gate_on": r["gate_on"],
                "delta_on_minus_off": r["gate_on"] - r["gate_off"],
                "better_direction": "lower", "verdict": "worsens",
                "n_off": 1, "n_on": 1}]) for _, r in t.iterrows()],
                ignore_index=True), "as_is")
        chk(cvo.set_index("criterion").loc["orbit_agreement", "verdict"] == "WORSENS"
            and ovo.startswith("REJECT"),
            "a gate that raises sigma and lowers the tolerance share WORSENS on "
            "orbit agreement")
        try:
            build_orbit_criterion(os.path.join(td, "off"), os.path.join(td, "absent"),
                                  os.path.join(td, "x", "o.csv"))
            chk(False, "a missing arm must stop the run")
        except SystemExit as e:
            chk("--gate1-r 0.50" in str(e),
                "a missing orbit arm refuses and names how to produce it")

    # --- 7. direction table covers every statistic used -------------------
    used = {s for stats in CRITERION_STATS.values() for s in stats}
    chk(used <= set(DIRECTION),
        "every statistic named by a criterion has a declared better-direction")

    print()
    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Protocol §3.1 Gate 1 justification test.")
    ap.add_argument("--off", default=os.path.join(RESULTS, "phen_panel_sar.csv"))
    ap.add_argument("--on", default=os.path.join(RESULTS, "gate1_on",
                                                 "phen_panel_sar.csv"))
    ap.add_argument("--orbit", default=None,
                    help="optional CSV with columns statistic,marker,gate_off,gate_on "
                         "carrying the orbit-agreement criterion")
    ap.add_argument("--out", default=os.path.join(RESULTS, "gate1_justification"))
    ap.add_argument("--orbit-off-dir", default=None,
                    help="orbit_agreement output dir for the gate-OFF arm; with "
                         "--orbit-on-dir this builds the fourth criterion first")
    ap.add_argument("--orbit-on-dir", default=None,
                    help="orbit_agreement output dir for the gate-ON arm "
                         "(run with --gate1-r 0.50)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    orbit = a.orbit
    if a.orbit_off_dir and a.orbit_on_dir:
        orbit = os.path.join(a.out, "orbit_criterion.csv")
        build_orbit_criterion(a.orbit_off_dir, a.orbit_on_dir, orbit)
    run(a.off, a.on, a.out, orbit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
