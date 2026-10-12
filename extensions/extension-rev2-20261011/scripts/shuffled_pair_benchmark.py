"""shuffled_pair_benchmark.py -- Addition A: a descriptive different-pixel benchmark.

Reads the released results/orbit_agreement/orbit_pairs.csv (nothing is refitted).
Within each eligible cell (district, year, orbit_a, orbit_b; >= 2 rows) the
complete orbit-b marker vector (trough_b, heading_b, harvest_b) of each row is
reassigned to another row of the same cell by a uniformly random derangement.
The same statistics as the released Table S1 are computed on the released
rows and on each deranged copy, on exactly the same eligible rows. Reported:
observed value, benchmark mean/sd/2.5%/97.5% over R draws (a random-
mismatching reference band), the difference observed - benchmark mean, the
Monte Carlo standard error of the benchmark mean, and a district-cluster
bootstrap (B replicates, K derangement draws inside each) for the observed
statistic and the difference. Evaluation (2018-2025) and baseline (2017) are
run separately. No test, no interpretation.

Run:  venv/bin/python -I scripts/shuffled_pair_benchmark.py [--R 1000 --B 2000 --K 50 --pilot]
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="Mean of empty slice")

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ext_common as X  # noqa: E402

MARKERS = ["trough", "heading", "harvest"]
FIXED_T = {"trough": 70.0, "heading": 50.0, "harvest": 60.0}   # published Table 2 tolerances
DEKAD = 10.0
SEED_BENCH = 20261010
SEED_BOOT = 20261011
CELL = ["district", "year", "orbit_a", "orbit_b"]
STATS = ["n", "frac_within_T", "frac_within_10d", "frac_within_20d", "mean_diff", "sd_diff",
         "sd_diff_over_sqrt2", "median_abs_diff", "pearson_r"]
BOOT_SCOPES = {"ALL", "Andhra Pradesh", "Odisha", "West Bengal", "ASC/DESC pairs only", "same-pass pairs only"}


def stats_block(A, Bm, mask):
    """A, Bm: (n,) orbit-a and orbit-b markers; mask: (n,) bool. Released definitions."""
    a = A[mask]; b = Bm[mask]; d = b - a
    n = d.size
    if n < 2:
        return dict(n=n, **{s: np.nan for s in STATS if s != "n"})
    ad = np.abs(d)
    sd = d.std(ddof=1)
    a_c = a - a.mean(); b_c = b - b.mean()
    den = np.sqrt((a_c ** 2).sum() * (b_c ** 2).sum())
    r = float((a_c * b_c).sum() / den) if den > 0 else np.nan
    return dict(n=n, frac_within_T=np.nan, frac_within_10d=float((ad <= DEKAD).mean()),
                frac_within_20d=float((ad <= 2 * DEKAD).mean()), mean_diff=float(d.mean()),
                sd_diff=float(sd), sd_diff_over_sqrt2=float(sd / np.sqrt(2.0)),
                median_abs_diff=float(np.median(ad)), pearson_r=r)


def stats_block_T(A, Bm, mask, T):
    s = stats_block(A, Bm, mask)
    if s["n"] >= 2:
        s["frac_within_T"] = float((np.abs(Bm[mask] - A[mask]) <= T).mean())
    return s


def stats_matrix(A, BM, mask, T):
    """BM: (P, n) matrix of orbit-b markers for P draws -> dict of (P,) arrays."""
    a = A[mask][None, :]; b = BM[:, mask]; d = b - a
    n = d.shape[1]
    ad = np.abs(d)
    sd = d.std(axis=1, ddof=1)
    a_c = a - a.mean(); b_c = b - b.mean(axis=1, keepdims=True)
    den = np.sqrt((a_c ** 2).sum() * (b_c ** 2).sum(axis=1))
    with np.errstate(invalid="ignore", divide="ignore"):
        r = (a_c * b_c).sum(axis=1) / den
    return dict(n=np.full(d.shape[0], n), frac_within_T=(ad <= T).mean(axis=1),
                frac_within_10d=(ad <= DEKAD).mean(axis=1), frac_within_20d=(ad <= 2 * DEKAD).mean(axis=1),
                mean_diff=d.mean(axis=1), sd_diff=sd, sd_diff_over_sqrt2=sd / np.sqrt(2.0),
                median_abs_diff=np.median(ad, axis=1), pearson_r=r)


def derangement(rng, n):
    """Uniform random derangement of range(n) by rejection sampling of uniform permutations."""
    idx = np.arange(n)
    tries = 0
    while True:
        p = rng.permutation(n); tries += 1
        if not np.any(p == idx):
            return p, tries


def build_pool(df, P, seed):
    """P derangement draws per cell. Returns src (P, n_rows): row index whose orbit-b vector row i takes."""
    n = len(df)
    src = np.empty((P, n), dtype=np.int64)
    ss = np.random.SeedSequence(seed)
    cells = df.groupby(CELL, sort=True).indices
    child = ss.spawn(len(cells))
    tries_total = 0
    two_row = 0
    for (key, rows), cs in zip(sorted(cells.items()), child):
        rows = np.asarray(rows)
        rng = np.random.default_rng(cs)
        m = rows.size
        if m == 2:
            two_row += 1
        for p in range(P):
            perm, t = derangement(rng, m)
            tries_total += t
            src[p, rows] = rows[perm]
    return src, tries_total, two_row, len(cells)


def scopes_for(df, states):
    st = df["district"].map(states)
    out = {"ALL": np.ones(len(df), bool)}
    for s in ("Andhra Pradesh", "Odisha", "West Bengal"):
        m = (st == s).to_numpy()
        if m.any():
            out[s] = m
    out["ASC/DESC pairs only"] = (df["asc_desc"] == 1).to_numpy()
    out["same-pass pairs only"] = (df["asc_desc"] == 0).to_numpy()
    for y in sorted(df["year"].unique()):
        if df["year"].nunique() > 1:
            out[f"year {int(y)}"] = (df["year"] == y).to_numpy()
    return out


def run_arm(df, arm, states, R, B, K, log):
    df = df.reset_index(drop=True)
    n_dist = df["district"].nunique()
    t0 = time.time()
    src, tries, two_row, n_cells = build_pool(df, R, SEED_BENCH)
    t_pool = time.time() - t0
    log(f"[{arm}] {len(df)} rows, {n_cells} cells ({two_row} two-row), {n_dist} districts; "
        f"{R} derangement draws per cell in {t_pool:.1f}s (rejection tries {tries}, {tries/(R*n_cells):.2f} per draw)")
    A = {mk: df[f"{mk}_a"].to_numpy(float) for mk in MARKERS}
    Bv = {mk: df[f"{mk}_b"].to_numpy(float) for mk in MARKERS}
    BM = {mk: Bv[mk][src] for mk in MARKERS}          # (R, n) deranged orbit-b markers, same draw for all markers
    scopes = scopes_for(df, states)
    rows = []
    t1 = time.time()
    for sc, mask in scopes.items():
        nd = int(df.loc[mask, "district"].nunique())
        for mk in MARKERS:
            obs = stats_block_T(A[mk], Bv[mk], mask, FIXED_T[mk])
            bm = stats_matrix(A[mk], BM[mk], mask, FIXED_T[mk])
            for s in STATS:
                v = bm[s]
                rows.append(dict(arm=arm, scope=sc, marker=mk, statistic=s, n_rows=int(mask.sum()),
                                 n_districts=nd, observed=obs[s], bench_mean=float(np.nanmean(v)),
                                 bench_sd=float(np.nanstd(v, ddof=1)), bench_p025=float(np.nanpercentile(v, 2.5)),
                                 bench_p975=float(np.nanpercentile(v, 97.5)),
                                 bench_mc_se=float(np.nanstd(v, ddof=1) / np.sqrt(R)),
                                 diff_obs_minus_bench=obs[s] - float(np.nanmean(v))))
    t_main = time.time() - t1
    log(f"[{arm}] benchmark statistics for {len(scopes)} scopes x 3 markers in {t_main:.1f}s")
    out = pd.DataFrame(rows)

    # ---- district-cluster bootstrap of observed and of (observed - benchmark mean) ----
    t2 = time.time()
    rng = np.random.default_rng(SEED_BOOT + (0 if arm == "evaluation" else 1))
    districts = sorted(df["district"].unique())
    d_rows = {d: np.flatnonzero((df["district"] == d).to_numpy()) for d in districts}
    boot = {}   # (scope, marker, stat) -> (list obs, list diff)
    boot_scopes = [sc for sc in scopes if sc in BOOT_SCOPES]
    max_mult_seen = 0
    for b in range(B):
        draw = rng.choice(len(districts), size=len(districts), replace=True)
        counts = np.bincount(draw, minlength=len(districts))
        idx_parts, drawparts = [], []
        for di, c in enumerate(counts):
            for inst in range(c):           # instance inst of this district uses draws [inst*K, (inst+1)*K)
                r_ = d_rows[districts[di]]
                idx_parts.append(r_)
                drawparts.append(np.arange(inst * K, (inst + 1) * K))
                max_mult_seen = max(max_mult_seen, inst + 1)
        if not idx_parts:
            continue
        idx = np.concatenate(idx_parts)
        # benchmark matrix for this replicate: for each part, K draws from its own instance slice
        for sc in boot_scopes:
            m_full = scopes[sc]
            sel = m_full[idx]
            if sel.sum() < 2:
                continue
            for mk in MARKERS:
                a = A[mk][idx]; bb = Bv[mk][idx]
                bm = np.empty((K, idx.size))
                pos = 0
                for r_, dr in zip(idx_parts, drawparts):
                    bm[:, pos:pos + r_.size] = BM[mk][dr][:, r_]
                    pos += r_.size
                obs = stats_block_T(a, bb, sel, FIXED_T[mk])
                bs = stats_matrix(a, bm, sel, FIXED_T[mk])
                for s in STATS:
                    key = (sc, mk, s)
                    o, dlist = boot.setdefault(key, ([], []))
                    o.append(obs[s]); dlist.append(obs[s] - float(np.nanmean(bs[s])))
        if (b + 1) % 500 == 0:
            log(f"[{arm}] bootstrap {b+1}/{B} ({time.time()-t2:.0f}s)")
    t_boot = time.time() - t2
    if (max_mult_seen * K) > R:
        raise RuntimeError(f"bootstrap needed {max_mult_seen*K} draws per cell but only {R} were generated")
    for (sc, mk, s), (o, dl) in boot.items():
        o = np.asarray(o, float); dl = np.asarray(dl, float)
        sel = (out.arm == arm) & (out.scope == sc) & (out.marker == mk) & (out.statistic == s)
        out.loc[sel, "boot_replicates"] = len(o)
        out.loc[sel, "boot_obs_p025"] = np.nanpercentile(o, 2.5)
        out.loc[sel, "boot_obs_p975"] = np.nanpercentile(o, 97.5)
        out.loc[sel, "boot_diff_p025"] = np.nanpercentile(dl, 2.5)
        out.loc[sel, "boot_diff_p975"] = np.nanpercentile(dl, 97.5)
    log(f"[{arm}] bootstrap: {B} replicates x {K} draws, max district multiplicity {max_mult_seen}, {t_boot:.0f}s")
    rec = dict(rows=int(len(df)), cells=int(n_cells), two_row_cells=int(two_row), districts=int(n_dist),
               R=R, B=B, K=K, rejection_tries=int(tries), seconds_pool=t_pool, seconds_main=t_main,
               seconds_bootstrap=t_boot, max_district_multiplicity=int(max_mult_seen))
    return out, rec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--R", type=int, default=1000)
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--K", type=int, default=50)
    ap.add_argument("--pilot", action="store_true", help="R=100, B=50, K=10; writes to results/_pilot")
    a = ap.parse_args(argv)
    if a.pilot:
        a.R, a.B, a.K = 100, 50, 10
    out_dir = os.path.join(X.RESULTS, "_pilot" if a.pilot else "A_shuffled_pair_benchmark")
    os.makedirs(out_dir, exist_ok=True)
    logf = open(os.path.join(out_dir, "A_log.txt"), "w", encoding="utf-8")

    def log(msg):
        print(msg, flush=True); logf.write(msg + "\n"); logf.flush()

    log(f"environment {X.environment_record()}")
    pairs_hash = X.sha256_file(X.PAIRS_RELEASED)
    log(f"input released orbit_pairs.csv sha256 {pairs_hash}")
    P = pd.read_csv(X.PAIRS_RELEASED)
    gad = pd.read_csv(os.path.join(X.RELEASE_SRC, "docs", "coastal_districts_gadm41.csv"))
    states = dict(zip(gad["district_gadm_name"], gad["state"]))
    missing = sorted(set(P.district) - set(states))
    if missing:
        raise SystemExit(f"districts without a state: {missing}")

    # observed statistics on the FULL released sample (all 7,717 / 798 rows), as a check against Table S1
    chk = []
    for arm, sub in (("evaluation", P[P.year > 2017]), ("baseline", P[P.year == 2017])):
        sub = sub.reset_index(drop=True)
        for sc, mask in scopes_for(sub, states).items():
            for mk in MARKERS:
                s = stats_block_T(sub[f"{mk}_a"].to_numpy(float), sub[f"{mk}_b"].to_numpy(float), mask, FIXED_T[mk])
                chk.append(dict(arm=arm, scope=sc, marker=mk, **s))
    pd.DataFrame(chk).to_csv(os.path.join(out_dir, "A_observed_full_sample_check.csv"), index=False, lineterminator="\n")

    # eligible samples
    cells_all = []
    results = []
    record = dict(environment=X.environment_record(), input_sha256=pairs_hash, seed_bench=SEED_BENCH, seed_boot=SEED_BOOT,
                  derangement_algorithm="numpy default_rng(SeedSequence(seed).spawn per cell), rng.permutation(n), rejected until no fixed point (uniform over derangements); the same draw reassigns trough_b, heading_b and harvest_b together",
                  fixed_tolerances_d=FIXED_T, dekad_d=DEKAD, bootstrap="district-cluster, with replacement, instance-indexed draws per duplicated district", arms={})
    for arm, sub in (("evaluation", P[P.year > 2017]), ("baseline", P[P.year == 2017])):
        cs = sub.groupby(CELL).size().rename("n_cell").reset_index()
        cs["eligible"] = cs["n_cell"] >= 2
        cs["arm"] = arm
        cells_all.append(cs)
        elig = sub.merge(cs[cs.eligible][CELL], on=CELL)
        n_excl = len(sub) - len(elig)
        record["arms"][arm] = dict(rows_total=int(len(sub)), rows_eligible=int(len(elig)), singleton_rows_excluded=int(n_excl),
                                   cells_total=int(len(cs)), cells_eligible=int(cs.eligible.sum()))
        out, rec = run_arm(elig, arm, states, a.R, a.B, a.K, log)
        record["arms"][arm].update(rec)
        results.append(out)
    res = pd.concat(results, ignore_index=True)
    res.to_csv(os.path.join(out_dir, "A_benchmark_results.csv"), index=False, lineterminator="\n")
    pd.concat(cells_all, ignore_index=True).to_csv(os.path.join(out_dir, "A_cells.csv"), index=False, lineterminator="\n")
    X.write_json(os.path.join(out_dir, "A_RECORD.json"), record)
    # a compact view of the headline scopes
    view = res[(res.scope.isin(["ALL", "Andhra Pradesh", "Odisha", "West Bengal", "ASC/DESC pairs only", "same-pass pairs only"]))
               & (res.statistic.isin(["frac_within_T", "frac_within_10d", "frac_within_20d", "sd_diff_over_sqrt2", "median_abs_diff", "mean_diff", "pearson_r"]))]
    view.to_csv(os.path.join(out_dir, "A_benchmark_headline_scopes.csv"), index=False, lineterminator="\n")
    log("done")
    logf.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
