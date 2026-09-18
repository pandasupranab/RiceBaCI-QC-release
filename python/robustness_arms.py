#!/usr/bin/env python3
"""§3.8 A's declared robustness arms — "reported, never headline".

§3.8 A: "Robustness (reported, never headline): state x season fixed effects in
place of gamma_t (identification then uses within-state, within-season contrasts
only); exposure buffer 75 km and 100 km in place of 50 km; severity threshold
64 kt (IMD Very Severe Cyclonic Storm) in place of 48 kt; the HLS panel 2016-2025
in place of Sentinel-2 (adds seasons 2016-2018, including Titli 2018)."

Four of the five are run here. The HLS arm is not: §3.4's 2026-09-09 amendment
removed HLS as a substrate entirely (it is Landsat plus Sentinel-2 and sits under
the same monsoon cloud), and the radar panel already spans 2017-2025 including
Titli 2018, which is what that arm existed to add. Withdrawn by dated amendment
rather than silently skipped.

WHAT EACH ARM IS FOR, and it is not the same thing for all four:

  state x season FE   Identification from within-state, within-season contrasts
                      only. This is the arm that matters most for a coastal
                      roster, because a cyclone season is a shared shock: with a
                      plain season effect, a storm that hits Odisha is compared
                      against Andhra Pradesh in the same season, and any
                      state-level difference in that season loads onto the
                      exposure coefficient.

  buffer 75 / 100 km  The 50 km buffer is Paper 1's and is arbitrary at the
                      margin. Widening it adds district-storm pairs whose
                      >= 34 kt track passed between 50 and 100 km. Severe rows
                      go 52 -> 71 -> 89 and severe harvest-window rows 21 -> 29
                      -> 39, so this arm adds treated support rather than
                      reshuffling it. Agreement under these tested buffers is
                      a sensitivity result, not identification of the cause.

  severity 64 kt      The opposite direction: it REMOVES support, taking severe
                      harvest-window rows from 21 to 7. With so few, §3.10's
                      MacKinnon-Webb rule is expected to bind and a null here
                      will be uninformative rather than contrary. Reported for
                      that reason, and read that way.

HOW THE VARIANT CATALOGUES ARE CHECKED. The buffer and
severity arms need exposure recomputed from IBTrACS, not re-derived from the 50 km
file, which records only winds within 50 km. `build_cyclone_exposure.py` was
therefore parameterised (2026-09-13) so one implementation of the rule serves all
four. Use --rebuild with the roster, GADM shapefile and IBTrACS source to generate
all four definitions in an empty directory. The gate requires a separately
generated baseline matching the frozen exposure CSV and a receipt covering the
generator and all eight generated catalogues. The previous self-comparison gate
did not establish any rebuild equivalence; its PASS is withdrawn (2026-09-16).

INFERENCE. Bootstrap and permutation reference distributions are different.
Comparing permutation |t| quantiles with 1.96 does not establish bootstrap size
distortion. Within-state history relabelling is a spatial sensitivity under an
exchangeability assumption, not a test identifying the source of an association.
WCB is reported for district+season FE; state+season FE WCB is not implemented
and is explicitly marked unavailable. The placebo permutation is optional via
--n-perm, with 2,000 draws used for the reported analysis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attrition_diagnostics import (FEAbsorber, WithinModel, _screen_regressors,
                                   build_exposure_table, load_panel, twfe, SEED)

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
from permutation_test import (district_state_map, make_permutations, attach,
                             CELLS)

VAR_DIR = os.path.join(RESULTS, "expo_var")
FROZEN = _find_doc("district_cyclone_exposure_ibtracs50km.csv")
PANEL_PIXEL = os.path.join(RESULTS, "phen_panel_sar_static.csv")
PANEL_DIST = os.path.join(RESULTS, "phen_panel_district_season_static.csv")
OUT = os.path.join(RESULTS, "robustness")
REGS = ["S_pre_season", "S_harvest_window", "Slag_pre_season",
        "Slag_harvest_window", "M_minor"]

ARMS = [
    ("frozen", FROZEN, ["district", "year"],
     "declared headline: 50 km buffer, 48 kt, district + season FE"),
    ("state_x_season", FROZEN, ["district", "state_year"],
     "state x season FE in place of season FE"),
    ("buffer75", "district_cyclone_exposure_ibtracs75km_48kt.csv",
     ["district", "year"], "exposure buffer 75 km"),
    ("buffer100", "district_cyclone_exposure_ibtracs100km_48kt.csv",
     ["district", "year"], "exposure buffer 100 km"),
    ("severity64", "district_cyclone_exposure_ibtracs50km_64kt.csv",
     ["district", "year"], "severity threshold 64 kt"),
]
PLACEBO = ("trough", "S_harvest_window")


def digest(path):
    data = Path(path).read_bytes()
    if Path(path).suffix == ".py":
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def gate(var_dir=None, frozen=None, builder=None):
    """Check a separately stored baseline and every recorded generated catalogue.

    The old absolute-path join compared FROZEN with itself and passed even with
    an empty variant directory. A baseline match alone also cannot authenticate
    the other variants. The rebuild receipt records each of the eight outputs.
    Hash integrity is evidence of this recorded run, not scientific validation.
    """
    folder = Path(var_dir or VAR_DIR)
    original = Path(frozen or FROZEN).resolve()
    generated = folder / original.name
    generator = Path(builder or Path(__file__).with_name("build_cyclone_exposure.py"))
    try:
        if not generated.is_file() or os.path.samefile(original, generated):
            raise ValueError("missing separate frozen rebuild, or self-comparison")
        if digest(original) != digest(generated):
            raise ValueError("rebuilt baseline differs from frozen catalogue")
        receipt = json.loads((folder / "rebuild_receipt.json").read_text(encoding="utf-8"))
        if receipt.get("schema") != 1 or receipt.get("generator_sha256_lf") != digest(generator):
            raise ValueError("missing or stale generator receipt")
        expected = {f"{prefix}_{suffix}.csv"
                    for prefix in ("district_cyclone_exposure", "cyclone_footprints")
                    for suffix in ("ibtracs50km", "ibtracs75km_48kt",
                                   "ibtracs100km_48kt", "ibtracs50km_64kt")}
        outputs = receipt.get("outputs_sha256", {})
        if set(outputs) != expected:
            raise ValueError("receipt does not cover the exact eight generated outputs")
        for name, expected_hash in outputs.items():
            if digest(folder / name) != expected_hash:
                raise ValueError(f"stale rebuilt output: {name}")
    except (OSError, ValueError, TypeError) as exc:
        print(f"[FAIL] exposure rebuild gate: {exc}")
        return False
    print("[PASS] separate baseline matches; recorded generator and eight outputs unchanged")
    return True


def rebuild_catalogues(roster, gadm, ibtracs, out):
    """Run the same generator four times and record source and output hashes."""
    folder = Path(out)
    if folder.exists() and any(folder.iterdir()):
        raise SystemExit("--rebuild requires an empty output directory; preserve earlier evidence")
    folder.mkdir(parents=True, exist_ok=True)
    builder = Path(__file__).with_name("build_cyclone_exposure.py")
    builder_hash = digest(builder)
    inputs = [Path(roster), Path(ibtracs)] + [Path(gadm).with_suffix(s)
                                               for s in (".shp", ".shx", ".dbf", ".prj")]
    source_hashes = {str(p.resolve()): digest(p) for p in inputs}
    for buffer, severity in ((50, 48), (75, 48), (100, 48), (50, 64)):
        subprocess.run([sys.executable, str(builder), roster, gadm, ibtracs,
                        str(folder), str(buffer), str(severity)], check=True)
    if digest(builder) != builder_hash or any(digest(p) != h for p, h in source_hashes.items()):
        raise RuntimeError("source changed during rebuild; no verification receipt written")
    receipt = {"schema": 1, "generator_sha256_lf": builder_hash,
               "input_sha256": source_hashes,
               "outputs_sha256": {p.name: digest(p) for p in sorted(folder.glob("*.csv"))}}
    (folder / "rebuild_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0 if gate(folder) else 2


def fit(panel, phen, test_var, fe_cols, n_boot, seed):
    """Point estimate, cluster-robust SE and t. Restricts to retained == 1."""
    if "retained" in panel.columns:
        panel = panel[panel["retained"].astype(int) == 1]
    d = panel.dropna(subset=[phen] + REGS)
    if d.empty or d[test_var].nunique() < 2:
        return dict(status="not_estimable", reason="empty sample or constant exposure")
    fe = FEAbsorber(d, fe_cols)
    Xd, kept, dropped = _screen_regressors(fe, d, REGS, test_var)
    if test_var not in kept:
        return dict(status="not_estimable",
                    reason=f"{test_var} carries no identifying variation after "
                           f"{'+'.join(fe_cols)} ({'; '.join(dropped)})")
    yd = fe.demean(d[phen].astype(float).values)
    cl, _ = pd.factorize(d["district"], sort=False)
    cl = np.asarray(cl, np.int64)
    G = int(cl.max()) + 1
    ti = kept.index(test_var)
    m = WithinModel(Xd, cl, G, fe.k_absorbed)
    beta, se, _ = m.fit(yd)
    b, s = float(beta[ti]), float(se[ti])
    if not np.isfinite(b) or not np.isfinite(s) or s <= 0:
        return dict(status="not_estimable", reason="nonfinite coefficient or nonpositive variance")
    return dict(status="estimated", coef=b, se=s,
                t=(b / s if np.isfinite(s) and s > 0 else np.nan),
                n_obs=int(len(d)), n_clusters=G,
                n_treated_clusters=int(d.loc[d[test_var] == 1,
                                             "district"].nunique()),
                n_score_clusters=int(m.score_clusters(yd, ti)),
                regressors_dropped="|".join(dropped))


def run(level, n_perm, seed, out_dir, boot, only_arm=None):
    panel0 = load_panel(PANEL_DIST if level == "district" else PANEL_PIXEL,
                        level, verbose=False)
    states = district_state_map(pd.read_csv(FROZEN))
    panel0["state"] = panel0["district"].map(states)
    if panel0["state"].isna().any():
        raise SystemExit("a panel district has no state in the exposure "
                         "catalogue; refusing to guess")
    panel0["state_year"] = panel0["state"] + "_" + panel0["year"].astype(str)
    districts = sorted(panel0["district"].unique())
    years = sorted(panel0["year"].unique())

    rows = []
    arms = [a for a in ARMS if (not only_arm or a[0] == only_arm)]
    if only_arm and not arms:
        raise SystemExit(f"no arm named {only_arm!r}; have "
                         + ", ".join(a[0] for a in ARMS))
    for name, cat, fe_cols, label in arms:
        expo = pd.read_csv(os.path.join(VAR_DIR, cat))
        tab = build_exposure_table(expo, districts, years)
        pan = attach(panel0, tab)
        print(f"\n{'=' * 78}\n{level.upper()}  arm '{name}' -- {label}\n{'=' * 78}")
        ret = pan[pan["retained"] == 1]
        print(f"  severe exposure among retained rows: "
              f"pre_season {int(ret['S_pre_season'].sum())}, "
              f"harvest_window {int(ret['S_harvest_window'].sum())}; "
              f"FE = {'+'.join(fe_cols)}")
        for phen, var, cell_label in CELLS:
            r = fit(pan, phen, var, fe_cols, boot, seed)
            if r is None or r.get("status") != "estimated":
                print(f"    {cell_label:<58s} not estimable"
                      + (f" -- {r['reason']}" if r else ""))
                rows.append(dict(level=level, arm=name, arm_label=label,
                                 phenometric=phen, test_var=var,
                                 cell=cell_label, status="not_estimable",
                                 reason=(r or {}).get("reason", "")))
                continue
            # p_WCB from the project estimator, on this arm's FE
            tw = (twfe(pan, phen, REGS, boot, seed, var)
                  if fe_cols == ["district", "year"] else {})
            p_wcb = tw.get("p_wcb", np.nan)
            if tw and (tw.get("n_boot_ok") != boot or
                       tw.get("n_boot_requested") != boot or not np.isfinite(p_wcb)):
                raise RuntimeError(f"{name}/{phen}/{var}: incomplete bootstrap; no final table written")
            flag = ("  [<3 treated clusters: MacKinnon-Webb, a null here is "
                    "uninformative]" if r["n_treated_clusters"] < 3 else "")
            print(f"    {cell_label:<58s} {r['coef']:+8.3f} d  (se {r['se']:6.3f})"
                  f"  t {r['t']:+6.3f}  treated_cl {r['n_treated_clusters']:2d}"
                  f"{flag}")
            rows.append(dict(level=level, arm=name, arm_label=label,
                             phenometric=phen, test_var=var, cell=cell_label,
                             status="estimated", p_wcb=p_wcb,
                             n_boot_requested=tw.get("n_boot_requested", 0),
                             n_boot_ok=tw.get("n_boot_ok", 0),
                             bootstrap_status=("complete" if tw else "not_implemented_for_state_year_FE"),
                             fe="+".join(fe_cols), **{
                    k: r[k] for k in ("coef", "se", "t", "n_obs", "n_clusters",
                                      "n_treated_clusters", "n_score_clusters",
                                      "regressors_dropped")}))

        # §3.9 permutation for the placebo cell of this arm
        obs = fit(pan, PLACEBO[0], PLACEBO[1], fe_cols, boot, seed)
        if obs and obs.get("status") == "estimated" and n_perm:
            perms = make_permutations(districts, states, n_perm, seed)
            bare = panel0.copy()
            ts = []
            for m in perms:
                rr = fit(attach(bare, tab, m), PLACEBO[0], PLACEBO[1],
                         fe_cols, boot, seed)
                if rr and rr.get("status") == "estimated" \
                        and np.isfinite(rr["t"]):
                    ts.append(rr["t"])
            if len(ts) != n_perm:
                raise RuntimeError(f"{name}: {len(ts)}/{n_perm} valid permutations; no final table written")
            p = (1 + sum(abs(v) >= abs(obs["t"]) for v in ts)) / (1 + len(ts))
            q = float(np.quantile(np.abs(ts), 0.95)) if ts else np.nan
            print(f"    SS3.9 placebo permutation ({len(ts)} draws): "
                  f"p_perm {p:.4f}   |t|_obs {abs(obs['t']):.3f} vs 95th pct "
                  f"{q:.3f}")
            for rw in rows:
                if rw.get("arm") == name and rw.get("phenometric") == PLACEBO[0] \
                        and rw.get("test_var") == PLACEBO[1]:
                    rw["p_perm"] = p
                    rw["perm_abs_t_q95"] = q
                    rw["n_perm_ok"] = len(ts)
                    rw["n_perm_requested"] = n_perm

    os.makedirs(out_dir, exist_ok=True)
    dest = os.path.join(
        out_dir, f"Table_SX_RobustnessArms_{level}"
                 + (f".{only_arm}" if only_arm else "") + ".csv")
    pd.DataFrame(rows).to_csv(dest, index=False)
    print(f"\nwrote {dest}")
    return 0


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        original = root / "source" / "district_cyclone_exposure_ibtracs50km.csv"
        original.parent.mkdir()
        original.write_bytes(b"synthetic fixture\n")
        folder = root / "rebuilt"
        folder.mkdir()
        builder = root / "builder.py"
        builder.write_bytes(b"# synthetic generator\n")
        assert not gate(folder, original, builder), "empty rebuild accepted"
        assert not gate(original.parent, original, builder), "self-comparison accepted"
        outputs = {}
        for prefix in ("district_cyclone_exposure", "cyclone_footprints"):
            for suffix in ("ibtracs50km", "ibtracs75km_48kt", "ibtracs100km_48kt", "ibtracs50km_64kt"):
                p = folder / f"{prefix}_{suffix}.csv"
                p.write_bytes(original.read_bytes())
                outputs[p.name] = digest(p)
        assert not gate(folder, original, builder), "missing receipt accepted"
        receipt = {"schema": 1, "generator_sha256_lf": digest(builder), "outputs_sha256": outputs}
        (folder / "rebuild_receipt.json").write_text(json.dumps(receipt), encoding="utf-8")
        assert gate(folder, original, builder)
        variant = folder / "district_cyclone_exposure_ibtracs75km_48kt.csv"
        variant.write_bytes(b"changed\n")
        assert not gate(folder, original, builder), "variant drift accepted"
        variant.write_bytes(original.read_bytes())
        builder.write_bytes(b"# changed generator\n")
        assert not gate(folder, original, builder), "generator drift accepted"
    print("[PASS] six exposure-gate cases (five refusals, one valid fixture)")
    return 0


def main(argv=None):
    global VAR_DIR
    ap = argparse.ArgumentParser(description="§3.8 A declared robustness arms.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rebuild", action="store_true", help="build all four exposure definitions from raw sources")
    ap.add_argument("--verify-catalogues", action="store_true")
    ap.add_argument("--roster")
    ap.add_argument("--gadm")
    ap.add_argument("--ibtracs")
    ap.add_argument("--variant-dir", default=VAR_DIR)
    ap.add_argument("--level", choices=["district", "pixel"], default="district")
    ap.add_argument("--boot", type=int, default=9999)
    ap.add_argument("--n-perm", type=int, default=0,
                    help="permutation draws for each arm's placebo cell. 0 "
                         "skips it; 2000 is §3.9's declared count.")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--only-arm", default=None,
                    help="run one arm, so a long permutation run fits in a "
                         "single call and writes its own separate table.")
    ap.add_argument("--collect", action="store_true",
                    help="retired; refused because old collection mixed unverified runs")
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    VAR_DIR = a.variant_dir
    if a.rebuild:
        if not all((a.roster, a.gadm, a.ibtracs)):
            ap.error("--rebuild requires --roster, --gadm and --ibtracs")
        return rebuild_catalogues(a.roster, a.gadm, a.ibtracs, VAR_DIR)
    if a.verify_catalogues:
        return 0 if gate() else 2
    if a.boot != 9999:
        ap.error("reported robustness tables require the declared 9,999 bootstrap draws")
    if a.collect:
        ap.error("--collect retired: last-file-wins could mix stale runs; run all arms in one invocation")
    if not gate():
        return 2
    return run(a.level, a.n_perm, a.seed, a.out, a.boot, a.only_arm)


if __name__ == "__main__":
    sys.exit(main())
