"""
event_study.py -- Protocol v1 §3.8 B, the named-cyclone event-level view, and H4.

Created 2026-09-13, after an external audit correctly pointed out that what was
being reported as the per-cyclone view is not the estimator §3.8 B declares.

WHAT WAS WRONG. §3.10 item 3c's "balanced" rows restrict to units retained in
both t_c-1 and t_c and then regress on the exposure CLASS. They are an attrition
check, they are indexed by the cyclone's SEASON and by nothing else, and two
cyclones sharing a season return the same number twice -- Fani and Bulbul are
both 2019 and did so in every committed table. They were labelled per-cyclone,
which invited them to be read as the event-level estimates H4 needs. They are
not, and this module supplies what is.

THE DECLARED DESIGN (§3.8 B, after Cengiz, Dube, Lindner & Zipperer 2019, QJE
134(3), 1405-1454). For each estimable named cyclone c, one stack over seasons
t_c-1, t_c, t_c+1:

    treated  = footprint districts (severe: >= 48 kt within 50 km in t_c)
    controls = clean controls -- no severe exposure to ANY catalogued storm in
               those three seasons -- drawn from all three states, because no
               named cyclone has three clean same-state coastal controls
    fringe   districts are dropped
    k = t - t_c, with k = -1 as the reference

beta_0,c is the per-cyclone estimate whose SIGN enters H4; beta_+1,c is
persistence. Clustering is on districts.

THE STACK MEMBERSHIP IS DERIVED, NOT READ FROM A FILE, AND THE DERIVATION IS
CHECKED AGAINST THE FILE. docs/cyclone_footprints_ibtracs50km.csv carries
footprint and clean-control flags for five cyclones; it predates Titli entering
the estimable set when the panel floor moved to 2017, so it cannot supply the
sixth. Rather than hand-add a row, this module derives every stack from the
exposure catalogue by §3.8 B's own rule and asserts, in --selftest, that the
derivation reproduces the committed file exactly for all five it covers --
footprint sets and clean-control sets both. Only then is it used for Titli.

TWO CONSTRAINTS THE PROTOCOL ITSELF IMPOSES, AND THIS MODULE ENFORCES.
  * With two treated clusters (Bulbul, Remal) no event-level significance claim
    is made (MacKinnon & Webb 2018). Those rows carry point estimate and
    interval and are flagged `underpowered`; H4 reads their SIGN only, which is
    what §3.8 B says it reads.
  * A stack whose footprint districts carry severe exposure to a DIFFERENT storm
    in t_c-1, t_c or t_c+1 is flagged. beta_0 for it is a descriptive contrast
    conditional on the adjacent exposure, not a clean single-storm effect. Amphan,
    Bulbul and eight of Fani's seventeen are flagged; Yaas and Remal are not.

H4's CRITERION, verbatim from §3.8 B as revised 2026-09-09: beta_0,c agrees in
sign with §4 for at least FIVE OF SIX. §4 signs every named cyclone positive,
with Bulbul (and Titli, a harvest-window landfall) declared only for the
harvest-side outcome. Under independent coin-flip signs five-of-six passes about
11% of the time, so it is a consistency check and is reported as one, never as a
test.

OUTCOME NAMES. This module estimates on the radar-trajectory breakpoints, not on
SOS/POS/EOS. The correspondence §4's table assumes -- t1~SOS, t2~POS, t4~EOS --
is an assumption this study has not validated, and is printed alongside every
H4 verdict rather than left implicit.

    python python/event_study.py --panel results/phen_panel_district_season.csv \
        --exposure data/district_cyclone_exposure_ibtracs50km.csv \
        --footprints data/cyclone_footprints_ibtracs50km.csv \
        --out results/
"""
from __future__ import annotations

import argparse
import hashlib
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attrition_diagnostics import (          # noqa: E402
    FEAbsorber, WithinModel, wild_cluster_bootstrap, normal_two_sided_p,
    MIN_TREATED_CLUSTERS, N_BOOT, SEED)

# §1.1 / §3.8 B. Titli enters with the 2017 panel floor.
ESTIMABLE = [("TITLI", 2018), ("FANI", 2019), ("BULBUL", 2019),
             ("AMPHAN", 2020), ("YAAS", 2021), ("REMAL", 2024)]

# §4's declared sign for beta_0, by outcome family. "na" means §4 declares no
# value for that cyclone and outcome; those cells do not enter H4's count.
PREDICTED = {
    "TITLI":  {"onset": "na", "rise_end": "na", "fall_end": "+"},
    "BULBUL": {"onset": "na", "rise_end": "na", "fall_end": "+"},
    "FANI":   {"onset": "+", "rise_end": "+", "fall_end": "+"},
    "AMPHAN": {"onset": "+", "rise_end": "+", "fall_end": "+"},
    "YAAS":   {"onset": "+", "rise_end": "+", "fall_end": "+"},
    "REMAL":  {"onset": "+", "rise_end": "+", "fall_end": "+"},
}
# the breakpoint that stands in for each of §4's optical outcome columns; the
# correspondence is an assumption, printed with every verdict
OUTCOME_MAP = {"onset": "trough", "rise_end": "heading", "fall_end": "harvest"}
H4_OUTCOME = "fall_end"          # the one column every estimable cyclone signs
H4_MIN_AGREE = 5
H4_OF = 6
EVENT_ESTIMATOR = "named_cyclone_stacked_did"
EVENT_DESIGN_ID = (
    "unit=district;window=k-1,k0,k1;reference=k-1;"
    "fe=stack_x_district+stack_x_season;cluster=district;sample=retained"
)


def sample_sha256(d):
    """Hash the exact rows that define an event-study estimation sample."""
    cols = ["stack", "cyclone", "district", "year", "k", "treated"]
    x = d.dropna(subset=["y"])[cols].copy()
    x = x.sort_values(cols, kind="mergesort").reset_index(drop=True)
    raw = x.to_csv(index=False, lineterminator="\n").encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _flag(v):
    """int(...) on a value that may be NaN, None or a numpy float."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0
    return 0 if not np.isfinite(f) else int(f)


def _norm(s):
    return str(s).strip().upper()


def severe_rows(exposure):
    e = exposure.copy()
    e["severity_class"] = e["severity_class"].astype(str).str.strip().str.lower()
    return e[e["severity_class"] == "severe"]


def derive_stack(exposure, roster, storm, t_c):
    """Footprint, clean controls and the adjacent-exposure flag for one stack.

    Footprint: roster districts with severe exposure to THIS storm in t_c.
    Clean controls: roster districts with severe exposure to NO catalogued storm
    in t_c-1, t_c or t_c+1. Fringe districts -- severe to this storm but outside
    the footprint -- do not arise in this catalogue and are dropped if they do.
    """
    sev = severe_rows(exposure)
    nm = _norm(storm)
    hit = sev[(sev["season"].astype(int) == t_c)
              & sev["storm_name"].map(lambda s: nm in _norm(s))]
    footprint = sorted(set(hit["district_gadm_name"]) & set(roster))
    window = [t_c - 1, t_c, t_c + 1]
    dirty = set(sev[sev["season"].astype(int).isin(window)]["district_gadm_name"])
    controls = sorted(set(roster) - dirty)
    # a footprint district severely exposed to a DIFFERENT storm inside the
    # window -- §3.8 B's treated_other_severe_exposure
    other = sev[sev["season"].astype(int).isin(window)
                & ~sev["storm_name"].map(lambda s: nm in _norm(s))]
    flagged = sorted(set(other["district_gadm_name"]) & set(footprint))
    return footprint, controls, flagged


def build_stack_frame(panel, exposure, roster, outcome, cyclones=ESTIMABLE):
    """Long frame of every stack: one row per (stack, district, k)."""
    rows, meta = [], []
    years = set(panel["year"].astype(int))
    for storm, t_c in cyclones:
        fp, cc, fl = derive_stack(exposure, roster, storm, t_c)
        ks = [k for k in (-1, 0, 1) if (t_c + k) in years]
        m = dict(cyclone=storm, t_c=t_c, n_footprint=len(fp),
                 n_control=len(cc), n_flagged=len(fl),
                 k_available="|".join(str(k) for k in ks))
        if -1 not in ks or 0 not in ks:
            m["status"] = "not_estimable"
            m["reason"] = (f"the stack needs k=-1 and k=0; seasons available "
                           f"are {sorted(t_c + k for k in ks)}")
            meta.append(m)
            continue
        if len(fp) == 0:
            m["status"] = "not_estimable"
            m["reason"] = "no roster district in the footprint"
            meta.append(m)
            continue
        m["status"] = "estimable"
        m["reason"] = ""
        meta.append(m)
        for dist in fp + cc:
            for k in ks:
                sub = panel[(panel["district"] == dist)
                            & (panel["year"].astype(int) == t_c + k)]
                if sub.empty:
                    continue
                y = float(sub.iloc[0][outcome]) if pd.notna(
                    sub.iloc[0][outcome]) else np.nan
                rows.append(dict(stack=f"{storm}_{t_c}", cyclone=storm,
                                 district=dist, year=t_c + k, k=k,
                                 treated=int(dist in fp), y=y,
                                 flagged=int(dist in fl)))
    return pd.DataFrame(rows), pd.DataFrame(meta)


def _fit(d, n_boot, seed, want=("k0", "k1")):
    """Stacked DiD on one frame. Reference k = -1, absorbed stack x district
    and stack x season effects, clustered on district."""
    d = d.dropna(subset=["y"]).copy()
    out = {}
    if d.empty or d["treated"].nunique() < 2:
        return {w: dict(status="not_estimable",
                        reason="no treated/control contrast in the stack",
                        n_boot_requested=int(n_boot), n_boot_ok=0)
                for w in want}
    d["sd"] = d["stack"] + "|" + d["district"]
    d["sk"] = d["stack"] + "|" + d["k"].astype(str)
    regs = []
    for k, nm in ((0, "k0"), (1, "k1")):
        col = f"treated_x_k{k}"
        d[col] = ((d["k"] == k) & (d["treated"] == 1)).astype(float)
        if d[col].nunique() > 1:
            regs.append((nm, col))
    if not regs:
        return {w: dict(status="not_estimable",
                        reason="no post-period interaction with variation",
                        n_boot_requested=int(n_boot), n_boot_ok=0)
                for w in want}
    cols = [c for _, c in regs]
    fe = FEAbsorber(d, ["sd", "sk"])
    X = np.column_stack([fe.demean(d[c].astype(float).values) for c in cols])
    y = fe.demean(d["y"].astype(float).values)
    cl, _ = pd.factorize(d["district"], sort=False)
    cl = np.asarray(cl, np.int64)
    G = int(cl.max()) + 1
    n_treated = int(d.loc[d["treated"] == 1, "district"].nunique())
    for i, (nm, col) in enumerate(regs):
        res = wild_cluster_bootstrap(y, X, fe, cl, G, i, n_boot=n_boot,
                                     seed=seed)
        # A percentile-t interval of zero width means every bootstrap draw
        # returned the same statistic: with two treated clusters the wild
        # bootstrap has almost no support, and an interval of [b, b] is a
        # degenerate artefact, not a precise estimate. Same policy as §3.10's
        # degenerate-variance guard -- the point estimate is kept, the interval
        # is refused.
        width = float(res["ci_hi"] - res["ci_lo"]) if np.isfinite(
            res["ci_hi"]) and np.isfinite(res["ci_lo"]) else np.nan
        # relative tolerance: an interval narrower than a thousandth of the
        # coefficient's own standard error is not an interval
        scale = float(res["se"]) if np.isfinite(res["se"]) else abs(
            float(res["coef"]))
        tol = max(1e-9, 1e-3 * (scale if np.isfinite(scale) else 0.0))
        degen = int((not np.isfinite(width)) or width <= tol)
        r = dict(status="not_estimable" if degen else "estimated",
                 coef=res["coef"], se=res["se"],
                 t=res["t"], p_wcb=np.nan if degen else res["p_wcb"],
                 wcb_ci_lo=np.nan if degen else res["ci_lo"],
                 wcb_ci_hi=np.nan if degen else res["ci_hi"],
                 degenerate_ci=degen,
                 reason=("the percentile-t interval has zero width: every "
                         "bootstrap draw returned the same statistic, which "
                         "with %d treated cluster(s) is a degenerate artefact "
                         "and not a precise estimate. The point estimate is in "
                         "`coef`." % n_treated) if degen else "",
                 n_obs=int(len(d)), n_clusters=G,
                 n_treated_clusters=n_treated,
                 n_boot_requested=int(res["n_boot_requested"]),
                 n_boot_ok=int(res["n_boot_ok"]),
                 underpowered=int(n_treated < MIN_TREATED_CLUSTERS))
        if np.isfinite(res["se"]):
            r["p_cluster"] = normal_two_sided_p(res["t"])
        out[nm] = r
    for w in want:
        out.setdefault(w, dict(status="not_estimable",
                               reason="interaction absent from this stack",
                               n_boot_requested=int(n_boot), n_boot_ok=0))
    return out


def run(panel, exposure, outcome_key, n_boot, seed, roster=None):
    outcome = OUTCOME_MAP[outcome_key]
    roster = roster or sorted(panel["district"].unique())
    frame, meta = build_stack_frame(panel, exposure, roster, outcome)
    rows = []
    for storm, t_c in ESTIMABLE:
        m = meta[meta["cyclone"] == storm].iloc[0]
        base = dict(outcome=outcome_key, breakpoint=outcome, cyclone=storm,
                    t_c=t_c, n_footprint=int(m["n_footprint"]),
                    n_control=int(m["n_control"]),
                    n_flagged=int(m["n_flagged"]),
                    adjacent_exposure_flag=int(m["n_flagged"] > 0),
                    predicted_sign=PREDICTED[storm][outcome_key],
                    estimator=EVENT_ESTIMATOR, design_id=EVENT_DESIGN_ID)
        sub = frame[frame["cyclone"] == storm]
        base["sample_sha256"] = sample_sha256(sub)
        if m["status"] != "estimable":
            for term in ("k0", "k1"):
                rows.append(dict(base, term=term, status="not_estimable",
                                 reason=m["reason"],
                                 n_boot_requested=int(n_boot), n_boot_ok=0))
            continue
        res = _fit(sub, n_boot, seed)
        for term in ("k0", "k1"):
            rows.append(dict(base, term=term, **res[term]))
    pooled = _fit(frame, n_boot, seed)
    for term in ("k0", "k1"):
        rows.append(dict(outcome=outcome_key, breakpoint=outcome,
                          cyclone="POOLED", t_c=-1, term=term,
                          predicted_sign="+", estimator=EVENT_ESTIMATOR,
                          design_id=EVENT_DESIGN_ID,
                          sample_sha256=sample_sha256(frame), **pooled[term]))
    return pd.DataFrame(rows), meta, frame


def h4_verdict(res):
    """§3.8 B's five-of-six sign agreement. A consistency check, not a test."""
    d = res[(res["term"] == "k0") & (res["cyclone"] != "POOLED")
            & (res["outcome"] == H4_OUTCOME)]
    agree, counted, detail = 0, 0, []
    for _, r in d.iterrows():
        pred = r["predicted_sign"]
        if r.get("status") != "estimated" and not np.isfinite(
                r.get("coef", np.nan)):
            detail.append((r["cyclone"], "not estimable", str(r.get("reason", ""))[:40]))
            counted += 1
            continue
        if not np.isfinite(r.get("coef", np.nan)):
            detail.append((r["cyclone"], "no point estimate", ""))
            counted += 1
            continue
        got = "+" if r["coef"] > 0 else ("-" if r["coef"] < 0 else "0")
        counted += 1
        ok = (pred in ("+", "-") and got == pred)
        agree += int(ok)
        detail.append((r["cyclone"], f"{r['coef']:+.2f} d ({got})",
                       "agrees" if ok else f"predicted {pred}"))
    return agree, counted, detail


def selftest():
    print("=" * 74)
    print("SELF-TEST -- event_study.py")
    print("=" * 74)
    ok_all = True
    here = os.path.dirname(os.path.abspath(__file__))
    exp = pd.read_csv(os.path.join(here, _find_doc("district_cyclone_exposure_ibtracs50km.csv")))
    fpf = pd.read_csv(os.path.join(here, _find_doc("cyclone_footprints_ibtracs50km.csv")))
    roster = sorted(set(fpf["district_gadm_name"]) - {"Kolkata", "Nellore",
                                                      "Prakasam"})

    # THE CHECK THAT LICENSES USING THE DERIVATION ON TITLI
    bad = []
    for cyc, g in fpf.groupby("cyclone"):
        t_c = int(g["analysis_year"].iloc[0])
        fp, cc, _ = derive_stack(exp, roster, cyc, t_c)
        f_fp = sorted(g.loc[(g["in_footprint"] == 1)
                            & g["district_gadm_name"].isin(roster),
                            "district_gadm_name"])
        f_cc = sorted(g.loc[(g["clean_control"] == 1)
                            & g["district_gadm_name"].isin(roster),
                            "district_gadm_name"])
        if fp != f_fp:
            bad.append(f"{cyc} footprint: {set(fp) ^ set(f_fp)}")
        if cc != f_cc:
            bad.append(f"{cyc} controls: {set(cc) ^ set(f_cc)}")
    ok = not bad
    ok_all &= ok
    for b in bad:
        print("    " + b)
    print(f"  [{'PASS' if ok else 'FAIL'}] the derived footprint and "
          f"clean-control sets reproduce docs/cyclone_footprints_"
          f"ibtracs50km.csv exactly for all {fpf['cyclone'].nunique()} cyclones "
          f"it covers -- which is what licenses deriving Titli, whom the file "
          f"predates")

    fp, cc, fl = derive_stack(exp, roster, "TITLI", 2018)
    ok = len(fp) > 0 and not (set(fp) & set(cc))
    ok_all &= ok
    print(f"\n  TITLI 2018 derived: {len(fp)} footprint, {len(cc)} clean "
          f"controls, {len(fl)} carrying adjacent severe exposure")
    print(f"  [{'PASS' if ok else 'FAIL'}] Titli gets a stack, and no district "
          f"is both treated and control")

    # a planted effect must be recovered at k = 0 and not at k = -1
    rng = np.random.default_rng(7)
    rows = []
    for st, t_c in (("A", 2020), ("B", 2021)):
        for i in range(8):
            dist = f"{st}{i}"
            tr = int(i < 4)
            for k in (-1, 0, 1):
                rows.append(dict(stack=st, cyclone=st, district=dist,
                                 year=t_c + k, k=k, treated=tr, flagged=0,
                                 y=100 + 5 * tr + rng.normal(0, 1)
                                 + (9.0 if (tr and k == 0) else 0.0)))
    d = pd.DataFrame(rows)
    r = _fit(d, 999, 3)
    ok = (abs(r["k0"]["coef"] - 9.0) < 1.5 and r["k0"]["p_wcb"] < 0.05
          and abs(r["k1"]["coef"]) < 2.0 and r["k1"]["p_wcb"] > 0.10)
    ok_all &= ok
    print(f"\n  planted +9 d at k=0 only -> beta_0 {r['k0']['coef']:+.2f} "
          f"(p {r['k0']['p_wcb']:.3f}), beta_+1 {r['k1']['coef']:+.2f} "
          f"(p {r['k1']['p_wcb']:.3f})")
    print(f"  [{'PASS' if ok else 'FAIL'}] the estimator recovers an effect at "
          f"k=0 and reports none at k=+1, with k=-1 as the reference")

    # a level difference between treated and control that is constant in k must
    # NOT be picked up: that is what the k=-1 reference is for
    d2 = d.copy()
    d2["y"] = 100 + 20 * d2["treated"] + rng.normal(0, 1, len(d2))
    r2 = _fit(d2, 999, 3)
    ok = abs(r2["k0"]["coef"]) < 1.5 and r2["k0"]["p_wcb"] > 0.10
    ok_all &= ok
    print(f"\n  constant +20 d treated-control level gap, no event -> beta_0 "
          f"{r2['k0']['coef']:+.2f} (p {r2['k0']['p_wcb']:.3f})")
    print(f"  [{'PASS' if ok else 'FAIL'}] a pre-existing level difference is "
          f"absorbed by the stack x district effects and does not become an "
          f"event estimate")

    # two cyclones sharing a season must NOT return the same number -- the
    # defect this module was written to remove
    exp_r = pd.read_csv(os.path.join(here,
                                     _find_doc("district_cyclone_exposure_ibtracs50km.csv")))
    f_fani, _, _ = derive_stack(exp_r, roster, "FANI", 2019)
    f_bul, _, _ = derive_stack(exp_r, roster, "BULBUL", 2019)
    ok = sorted(f_fani) != sorted(f_bul)
    ok_all &= ok
    print(f"\n  Fani 2019 footprint {len(f_fani)} districts, Bulbul 2019 "
          f"footprint {len(f_bul)} -- same season, different stacks")
    print(f"  [{'PASS' if ok else 'FAIL'}] cyclones sharing a season are "
          f"separated by footprint membership, not collapsed to one number as "
          f"§3.10 3c's balanced rows were")

    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="§3.8 B named-cyclone event study.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--panel")
    ap.add_argument("--exposure")
    ap.add_argument("--out")
    ap.add_argument("--boot", type=int, default=N_BOOT)
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not (a.panel and a.exposure and a.out):
        ap.error("--panel, --exposure and --out are required (or --selftest)")

    panel = pd.read_csv(a.panel)
    if "estimable" in panel.columns and "retained" not in panel.columns:
        panel["retained"] = panel["estimable"].astype(int)
    # §3.8 B estimates on the screened panel, like every other estimator here
    panel = panel[panel["retained"].astype(int) == 1]
    exposure = pd.read_csv(a.exposure)

    allres, allmeta = [], None
    for key in OUTCOME_MAP:
        res, meta, _ = run(panel, exposure, key, a.boot, a.seed)
        allres.append(res)
        allmeta = meta
    res = pd.concat(allres, ignore_index=True)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "Table_SX_EventStudy.csv")
    res.to_csv(path, index=False)

    print(f"§3.8 B named-cyclone stacks, estimated on the RETAINED panel "
          f"({len(panel)} unit-seasons)")
    print(allmeta.to_string(index=False))
    for key in OUTCOME_MAP:
        print(f"\n--- beta_0 and beta_+1 on {OUTCOME_MAP[key]} "
              f"(§4 column '{key}') ---")
        d = res[(res["outcome"] == key)]
        for _, r in d.iterrows():
            if r.get("status") != "estimated":
                print(f"  {r['cyclone']:<8s} {r['term']:<3s} not estimable -- "
                      f"{r.get('reason', '')}")
                continue
            flag = ""
            if _flag(r.get("underpowered")):
                flag += "  [<3 treated clusters: sign only]"
            if _flag(r.get("adjacent_exposure_flag")):
                flag += "  [adjacent severe exposure: incremental]"
            if _flag(r.get("degenerate_ci")):
                flag += "  [zero-width bootstrap interval: not estimable]"
            print(f"  {r['cyclone']:<8s} {r['term']:<3s} "
                  f"{r['coef']:+8.2f} d  (se {r['se']:6.2f})  "
                  f"p_WCB {r['p_wcb']:.4f}  "
                  f"CI [{r['wcb_ci_lo']:+.2f}, {r['wcb_ci_hi']:+.2f}]"
                  f"  pred {r['predicted_sign']}{flag}")

    agree, counted, detail = h4_verdict(res)
    print("\n" + "=" * 74)
    print(f"H4 sign-agreement check on §4's '{H4_OUTCOME}' column "
          f"(breakpoint {OUTCOME_MAP[H4_OUTCOME]})")
    for c, got, note in detail:
        print(f"  {c:<8s} {got:<18s} {note}")
    verdict = "MET" if agree >= H4_MIN_AGREE else "NOT MET"
    print(f"  {agree} of {counted} agree; criterion is {H4_MIN_AGREE} of "
          f"{H4_OF} -> {verdict}")
    print("  This is a consistency check, not a test: under independent "
          "coin-flip signs five-of-six passes about 11% of the time.")
    print("  It also assumes §4's optical outcome columns map onto the radar "
          "breakpoints (t1~SOS, t2~POS, t4~EOS). That correspondence is NOT "
          "validated by this study -- see the construct-validity note in "
          "python/extract_phenometrics_sar.py.")
    print("=" * 74)
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
