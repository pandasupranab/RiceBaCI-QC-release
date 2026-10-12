"""grid_sensitivity_compare.py -- Addition B: compare the free-grid fits (G2) with the released restricted-grid cache (G0).

Inputs: the released G0 cache (inputs/staged/per_orbit_fits.csv), the G2 fits
(results/B_free_grid/per_orbit_fits_pixel_free.csv), the released pair rule
(orbit_agreement.choose_pair / build_pairs / tolerance_from_baseline, imported
from the verified release copy) and the released district-to-state table.

Outputs (results/B_free_grid/):
  orbit_pairs_pixel_free.csv          pairs under G2 by the released rule
  B_retention_accounting.csv          series / pixel-season / pair counts per arm, by year and state
  B_transitions.csv                   pixel-season transitions between arms
  B_fullsample_stats.csv              each arm on its own full pair sample: Table S1 statistics with the
                                      fixed 70/50/60 d tolerance and with the arm's OWN 2017-calibrated tolerance
  B_common_sample_stats.csv           both arms on the common sample (same physical orbit pair) with paired
                                      differences G2 - G0 and district-cluster bootstrap percentile intervals
  B_grid_limit_occupancy.csv          share of evaluation pairs with a fit on a grid limit, per arm (G0 reproduces Table S24)
  B_series_shifts.csv                 G2 - G0 marker shifts for series retained in both arms, by G0 bound status
  B_RECORD.json, B_log.txt
Nothing here is a test; no threshold is applied.
"""
from __future__ import annotations

import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ext_common as X  # noqa: E402
import orbit_agreement as OA              # noqa: E402  released, verified copy
import extract_phenometrics_sar as SAR    # noqa: E402
import fit_phenometrics as FP             # noqa: E402

OUT = os.path.join(X.RESULTS, "B_free_grid")
G2_STORE = os.path.join(OUT, "per_orbit_fits_pixel_free.csv")
MARKERS = ["trough", "heading", "harvest"]
MK_LABEL = {"trough": "t1", "heading": "t2", "harvest": "t4"}
FIXED_T = {"trough": 70.0, "heading": 50.0, "harvest": 60.0}
DEKAD = 10.0
KEY = ["district", "year", "cell_id", "orbit"]
PS = ["district", "year", "cell_id"]
SEED_BOOT = 20261012
B_REPS = 2000
BOOT_SCOPES = ["ALL", "Andhra Pradesh", "Odisha", "West Bengal", "ASC/DESC pairs only", "same-pass pairs only"]
STATS = ["frac_within_T", "frac_within_10d", "frac_within_20d", "mean_diff", "sd_diff_over_sqrt2", "median_abs_diff", "pearson_r"]


def stats(a, b, T):
    d = b - a; n = d.size
    if n < 2:
        return dict(n=n, **{s: np.nan for s in STATS})
    ad = np.abs(d); sd = d.std(ddof=1)
    ac = a - a.mean(); bc = b - b.mean(); den = np.sqrt((ac ** 2).sum() * (bc ** 2).sum())
    return dict(n=int(n), frac_within_T=float((ad <= T).mean()), frac_within_10d=float((ad <= DEKAD).mean()),
                frac_within_20d=float((ad <= 2 * DEKAD).mean()), mean_diff=float(d.mean()),
                sd_diff_over_sqrt2=float(sd / np.sqrt(2.0)), median_abs_diff=float(np.median(ad)),
                pearson_r=float((ac * bc).sum() / den) if den > 0 else np.nan)


def scope_masks(df, states):
    st = df["district"].map(states)
    out = {"ALL": np.ones(len(df), bool)}
    for s in ("Andhra Pradesh", "Odisha", "West Bengal"):
        out[s] = (st == s).to_numpy()
    out["ASC/DESC pairs only"] = (df["asc_desc"] == 1).to_numpy()
    out["same-pass pairs only"] = (df["asc_desc"] == 0).to_numpy()
    return out


def grid_limits_free():
    keys = SAR.plsm_designs_free()[0]
    k = np.asarray(keys)
    lim = {}
    for pos, mk in ((0, "trough"), (1, "heading"), (3, "harvest")):
        lim[mk] = (float(FP.DEKAD_DOY[k[:, pos].min()]), float(FP.DEKAD_DOY[k[:, pos].max()]))
    return lim


def main():
    os.makedirs(OUT, exist_ok=True)
    logf = open(os.path.join(OUT, "B_log.txt"), "w", encoding="utf-8")

    def log(m):
        print(m, flush=True); logf.write(m + "\n"); logf.flush()

    t_all = time.time()
    log(f"environment {X.environment_record()}")
    g0 = pd.read_csv(X.CACHE_G0)
    g2 = pd.read_csv(G2_STORE)
    log(f"G0 cache {X.sha256_file(X.CACHE_G0)[:16]} rows {len(g0)}; G2 fits {X.sha256_file(G2_STORE)[:16]} rows {len(g2)}")
    assert not g0.duplicated(KEY).any() and not g2.duplicated(KEY).any()
    m = g0.merge(g2, on=KEY, suffixes=("_g0", "_g2"), how="outer", indicator=True)
    assert (m["_merge"] == "both").all(), m["_merge"].value_counts().to_dict()
    assert (m["n_valid_g0"] == m["n_valid_g2"]).all() and (m["orbit_pass_g0"] == m["orbit_pass_g2"]).all()
    gad = pd.read_csv(os.path.join(X.RELEASE_SRC, "docs", "coastal_districts_gadm41.csv"))
    states = dict(zip(gad["district_gadm_name"], gad["state"]))
    m["state"] = m["district"].map(states)
    G0L = {"trough": (184.5, 304.5), "heading": (274.5, 354.5), "harvest": (324.5, 422.0)}
    G2L = grid_limits_free()
    log(f"G0 restricted bounds {G0L}; G2 free design limits {G2L}")

    # ---- 1. retention accounting ----------------------------------------------------------------
    rows = []
    for arm, col in (("G0", "retained_g0"), ("G2", "retained_g2")):
        for by, grp in (("ALL", [("ALL", m)]), ("year", list(m.groupby("year"))), ("state", list(m.groupby("state")))):
            for name, sub in grp:
                ret = sub[sub[col] == 1]
                ps_ret = ret.groupby(PS).size()
                rows.append(dict(arm=arm, by=by, level=str(name), series=int(len(sub)), series_retained=int(len(ret)),
                                 retention_share=float(len(ret) / len(sub)),
                                 pixel_seasons=int(sub.groupby(PS).ngroups),
                                 pixel_seasons_ge2_retained=int((ps_ret >= 2).sum())))
    fr = {}
    for arm, col, rc in (("G0", "retained_g0", "fail_reason_g0"), ("G2", "retained_g2", "fail_reason_g2")):
        fr[arm] = m.loc[m[col] == 0, rc].fillna("").str.split(":").str[0].value_counts()
    frd = pd.DataFrame(fr).fillna(0).astype(int).reset_index().rename(columns={"index": "failure_reason"})
    frd.to_csv(os.path.join(OUT, "B_failure_reasons.csv"), index=False, lineterminator="\n")

    # pairs under each arm with the released rule
    fits0 = g0.copy(); fits2 = g2.copy()
    pairs0, ne0 = OA.build_pairs(fits0)
    pairs2, ne2 = OA.build_pairs(fits2)
    pairs2.to_csv(os.path.join(OUT, "orbit_pairs_pixel_free.csv"), index=False, lineterminator="\n")
    P_rel = pd.read_csv(X.PAIRS_RELEASED)
    same = len(pairs0) == len(P_rel)
    log(f"pairs: G0 rebuilt {len(pairs0)} (released {len(P_rel)}, equal count {same}); G2 {len(pairs2)}; not estimable G0 {len(ne0)} G2 {len(ne2)}")
    for arm, pp in (("G0", pairs0), ("G2", pairs2)):
        pp = pp.copy(); pp["state"] = pp["district"].map(states)
        rows.append(dict(arm=arm, by="pairs", level="ALL", series=np.nan, series_retained=np.nan, retention_share=np.nan,
                         pixel_seasons=int(len(pp)), pixel_seasons_ge2_retained=int(len(pp))))
        for y, s in pp.groupby("year"):
            rows.append(dict(arm=arm, by="pairs_year", level=str(y), pixel_seasons=int(len(s)), pixel_seasons_ge2_retained=int(len(s)),
                             series=np.nan, series_retained=np.nan, retention_share=np.nan))
        for st, s in pp.groupby("state"):
            rows.append(dict(arm=arm, by="pairs_state", level=str(st), pixel_seasons=int(len(s)), pixel_seasons_ge2_retained=int(len(s)),
                             series=np.nan, series_retained=np.nan, retention_share=np.nan))
        rows.append(dict(arm=arm, by="pairs_pass", level="ASC/DESC", pixel_seasons=int(pp.asc_desc.sum()), pixel_seasons_ge2_retained=int(pp.asc_desc.sum()),
                         series=np.nan, series_retained=np.nan, retention_share=np.nan))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "B_retention_accounting.csv"), index=False, lineterminator="\n")

    # ---- 2. transitions --------------------------------------------------------------------------
    k0 = pairs0.set_index(PS); k2 = pairs2.set_index(PS)
    allps = m.groupby(PS).size().index
    tr = pd.DataFrame(index=allps)
    tr["in_G0"] = tr.index.isin(k0.index); tr["in_G2"] = tr.index.isin(k2.index)
    j = k0[["orbit_a", "orbit_b"]].join(k2[["orbit_a", "orbit_b"]], lsuffix="_0", rsuffix="_2", how="inner")
    same_pair = (j["orbit_a_0"] == j["orbit_a_2"]) & (j["orbit_b_0"] == j["orbit_b_2"])
    tr["same_pair"] = False
    tr.loc[j.index[same_pair.to_numpy()], "same_pair"] = True
    def cls(r):
        if r.in_G0 and r.in_G2:
            return "paired in both, same orbit pair (common sample)" if r.same_pair else "paired in both, different orbit pair"
        if r.in_G0:
            return "paired in G0 only"
        if r.in_G2:
            return "paired in G2 only"
        return "paired in neither"
    tr["transition"] = tr.apply(cls, axis=1)
    tr = tr.reset_index()
    tr["state"] = tr["district"].map(states)
    tcounts = []
    for by, grp in (("ALL", [("ALL", tr)]), ("year", list(tr.groupby("year"))), ("state", list(tr.groupby("state")))):
        for name, sub in grp:
            vc = sub["transition"].value_counts()
            for t, n in vc.items():
                tcounts.append(dict(by=by, level=str(name), transition=t, pixel_seasons=int(n)))
    pd.DataFrame(tcounts).to_csv(os.path.join(OUT, "B_transitions.csv"), index=False, lineterminator="\n")
    common_keys = tr.loc[tr.transition.str.startswith("paired in both, same"), PS]
    log(f"transitions: {tr.transition.value_counts().to_dict()}")

    # ---- 3. full-sample statistics per arm (fixed T and own-2017 T) --------------------------------
    full = []
    own_T = {}
    for arm, pp in (("G0", pairs0), ("G2", pairs2)):
        pp = pp.reset_index(drop=True)
        later = pp[pp.year != OA.BASELINE_SEASON].reset_index(drop=True)
        base = pp[pp.year == OA.BASELINE_SEASON]
        masks = scope_masks(later, states)
        own_T[arm] = {}
        for mk in MARKERS:
            T_own, n_base = OA.tolerance_from_baseline(pp, mk)
            own_T[arm][mk] = (T_own, n_base)
            for sc, mask in masks.items():
                a = later.loc[mask, f"{mk}_a"].to_numpy(float); b = later.loc[mask, f"{mk}_b"].to_numpy(float)
                s = stats(a, b, FIXED_T[mk])
                s_own = float((np.abs(b - a) <= T_own).mean()) if (T_own is not None and s["n"] >= 2) else np.nan
                full.append(dict(arm=arm, scope=sc, marker=MK_LABEL[mk], n_pairs=s["n"], n_districts=int(later.loc[mask, "district"].nunique()),
                                 fixed_T_d=FIXED_T[mk], own_2017_T_d=T_own, n_baseline_pairs=n_base,
                                 frac_within_fixed_T=s["frac_within_T"], frac_within_own_T=s_own,
                                 frac_within_10d=s["frac_within_10d"], frac_within_20d=s["frac_within_20d"],
                                 mean_diff=s["mean_diff"], sd_diff_over_sqrt2=s["sd_diff_over_sqrt2"],
                                 median_abs_diff=s["median_abs_diff"], pearson_r=s["pearson_r"]))
    pd.DataFrame(full).to_csv(os.path.join(OUT, "B_fullsample_stats.csv"), index=False, lineterminator="\n")
    log(f"own-2017 tolerances: {own_T}")

    # ---- 4. common sample: both arms, paired differences, district bootstrap ------------------------
    c0 = pairs0.merge(common_keys, on=PS).set_index(PS).sort_index()
    c2 = pairs2.merge(common_keys, on=PS).set_index(PS).sort_index()
    assert (c0.index == c2.index).all() and (c0.orbit_a == c2.orbit_a).all() and (c0.orbit_b == c2.orbit_b).all()
    c0 = c0.reset_index(); c2 = c2.reset_index()
    out_c = []
    rng = np.random.default_rng(SEED_BOOT)
    for arm_sel, (ev0, ev2) in (("evaluation", (c0[c0.year != 2017].reset_index(drop=True), c2[c2.year != 2017].reset_index(drop=True))),
                                ("baseline", (c0[c0.year == 2017].reset_index(drop=True), c2[c2.year == 2017].reset_index(drop=True)))):
        masks = scope_masks(ev0, states)
        districts = sorted(ev0.district.unique())
        drows = {d: np.flatnonzero((ev0.district == d).to_numpy()) for d in districts}
        boots = [rng.choice(len(districts), size=len(districts), replace=True) for _ in range(B_REPS)] if arm_sel == "evaluation" else []
        for sc, mask in masks.items():
            nd = int(ev0.loc[mask, "district"].nunique())
            for mk in MARKERS:
                A0 = ev0[f"{mk}_a"].to_numpy(float); B0 = ev0[f"{mk}_b"].to_numpy(float)
                A2 = ev2[f"{mk}_a"].to_numpy(float); B2 = ev2[f"{mk}_b"].to_numpy(float)
                s0 = stats(A0[mask], B0[mask], FIXED_T[mk]); s2 = stats(A2[mask], B2[mask], FIXED_T[mk])
                ci = {}
                if boots and sc in BOOT_SCOPES and s0["n"] >= 2:
                    t0 = time.time()
                    acc = {s: [] for s in STATS}; acc0 = {s: [] for s in STATS}; acc2 = {s: [] for s in STATS}
                    for draw in boots:
                        idx = np.concatenate([drows[districts[i]] for i in draw])
                        sel = idx[mask[idx]]
                        if sel.size < 2:
                            continue
                        r0 = stats(A0[sel], B0[sel], FIXED_T[mk]); r2 = stats(A2[sel], B2[sel], FIXED_T[mk])
                        for s in STATS:
                            acc[s].append(r2[s] - r0[s]); acc0[s].append(r0[s]); acc2[s].append(r2[s])
                    for s in STATS:
                        v = np.asarray(acc[s], float)
                        ci[s] = (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5)),
                                 float(np.nanpercentile(acc0[s], 2.5)), float(np.nanpercentile(acc0[s], 97.5)),
                                 float(np.nanpercentile(acc2[s], 2.5)), float(np.nanpercentile(acc2[s], 97.5)), len(v))
                for s in STATS:
                    c = ci.get(s, (np.nan,) * 6 + (0,))
                    out_c.append(dict(sample=arm_sel, scope=sc, marker=MK_LABEL[mk], statistic=s, n_pairs=s0["n"], n_districts=nd,
                                      G0=s0[s], G2=s2[s], diff_G2_minus_G0=s2[s] - s0[s],
                                      diff_boot_p025=c[0], diff_boot_p975=c[1], G0_boot_p025=c[2], G0_boot_p975=c[3],
                                      G2_boot_p025=c[4], G2_boot_p975=c[5], boot_replicates=c[6]))
    pd.DataFrame(out_c).to_csv(os.path.join(OUT, "B_common_sample_stats.csv"), index=False, lineterminator="\n")
    log(f"common sample: evaluation {int((c0.year != 2017).sum())} pairs, baseline {int((c0.year == 2017).sum())} pairs; bootstrap {B_REPS} replicates")

    # ---- 5. grid-limit occupancy per arm (evaluation pairs) ----------------------------------------
    occ = []
    for arm, pp, lim in (("G0", pairs0, G0L), ("G2", pairs2, G2L)):
        ev = pp[pp.year != 2017]
        for mk in MARKERS:
            lo, hi = lim[mk]
            at_lo = (ev[f"{mk}_a"] == lo) | (ev[f"{mk}_b"] == lo)
            at_hi = (ev[f"{mk}_a"] == hi) | (ev[f"{mk}_b"] == hi)
            any_ = at_lo | at_hi
            rem = ev[~any_]
            d_all = (ev[f"{mk}_b"] - ev[f"{mk}_a"]).to_numpy(float); d_rem = (rem[f"{mk}_b"] - rem[f"{mk}_a"]).to_numpy(float)
            occ.append(dict(arm=arm, marker=MK_LABEL[mk], limit_lo_doy=lo, limit_hi_doy=hi, evaluation_pairs=int(len(ev)),
                            either_fit_at_lower=int(at_lo.sum()), either_fit_at_upper=int(at_hi.sum()), either_fit_at_any=int(any_.sum()),
                            share_at_any_pct=float(100 * any_.mean()), remaining_pairs=int(len(rem)),
                            sd_over_sqrt2_all=float(d_all.std(ddof=1) / np.sqrt(2)), sd_over_sqrt2_remaining=float(d_rem.std(ddof=1) / np.sqrt(2)) if len(rem) > 1 else np.nan,
                            within_10d_all_pct=float(100 * (np.abs(d_all) <= 10).mean()), within_10d_remaining_pct=float(100 * (np.abs(d_rem) <= 10).mean()) if len(rem) else np.nan))
    pd.DataFrame(occ).to_csv(os.path.join(OUT, "B_grid_limit_occupancy.csv"), index=False, lineterminator="\n")

    # ---- 6. series-level shifts for series retained in both arms -----------------------------------
    both = m[(m.retained_g0 == 1) & (m.retained_g2 == 1)]
    sh = []
    for mk in MARKERS:
        lo, hi = G0L[mk]
        g0v = both[f"{mk}_g0"].to_numpy(float); g2v = both[f"{mk}_g2"].to_numpy(float)
        status = np.where(g0v == lo, "G0 at lower bound", np.where(g0v == hi, "G0 at upper bound", "G0 interior"))
        for stt in ("all", "G0 interior", "G0 at lower bound", "G0 at upper bound"):
            sel = np.ones(len(both), bool) if stt == "all" else (status == stt)
            if sel.sum() == 0:
                continue
            d = g2v[sel] - g0v[sel]
            sh.append(dict(marker=MK_LABEL[mk], g0_status=stt, series=int(sel.sum()), share_unchanged=float((d == 0).mean()),
                           mean_shift_d=float(d.mean()), median_shift_d=float(np.median(d)), p10_shift_d=float(np.percentile(d, 10)),
                           p90_shift_d=float(np.percentile(d, 90)), share_abs_shift_gt_10d=float((np.abs(d) > 10).mean()),
                           share_abs_shift_gt_30d=float((np.abs(d) > 30).mean()),
                           share_G2_outside_G0_range=float(((g2v[sel] < lo) | (g2v[sel] > hi)).mean())))
    pd.DataFrame(sh).to_csv(os.path.join(OUT, "B_series_shifts.csv"), index=False, lineterminator="\n")
    allg2 = m[m.retained_g2 == 1]
    outside = {MK_LABEL[mk]: float(((allg2[f"{mk}_g2"] < G0L[mk][0]) | (allg2[f"{mk}_g2"] > G0L[mk][1])).mean()) for mk in MARKERS}
    log(f"share of all G2-retained series with the marker outside the G0 range: {outside}")

    rec = dict(environment=X.environment_record(), g0_cache_sha256=X.sha256_file(X.CACHE_G0), g2_fits_sha256=X.sha256_file(G2_STORE),
               pairs_released_sha256=X.sha256_file(X.PAIRS_RELEASED), g2_pairs_sha256=X.sha256_file(os.path.join(OUT, "orbit_pairs_pixel_free.csv")),
               seed_boot=SEED_BOOT, bootstrap_replicates=B_REPS, g0_bounds=G0L, g2_design_limits=G2L, own_2017_tolerances=own_T,
               share_G2_retained_outside_G0_range=outside, series_retained_both=int(len(both)), seconds=time.time() - t_all,
               pairs_G0_rebuilt_equals_released_count=bool(same))
    X.write_json(os.path.join(OUT, "B_RECORD.json"), rec)
    log(f"done in {time.time()-t_all:.0f}s")
    logf.close()


if __name__ == "__main__":
    main()
