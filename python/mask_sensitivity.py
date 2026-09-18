"""
mask_sensitivity.py -- Protocol §3.5 / §4.3.4 mask-comparison arm.

THE QUESTION. Every phenometric in this paper is measured on cohort points that
were selected by this project's own criteria. Nothing outside the project has
ever agreed that those points are cropland. §3.5 declared a sensitivity arm
against an independent classifier: restrict the cohort to points that ESA
WorldCereal 2021 v100 `temporarycrops` also calls cropland, re-run, and report
whether the reported results survive.

WHAT THIS SCRIPT DOES AND DELIBERATELY DOES NOT DO.

It does NOT re-implement the panel construction. The district-season panel is
not an average of pixel phenometrics -- extract_phenometrics_sar.py fits the
five-segment PLSM to the district-season MEAN CURVE. So a pixel mask cannot be
applied to the committed district panel after the fact; the mean curve has to be
rebuilt from masked pixels and refitted. Re-implementing that here would put a
second, unaudited copy of the estimator in the repository, and the arm would
then test the copy rather than the paper.

Instead this script filters the RAW exports to the masked cell_ids and leaves
the committed estimator to do the rest:

    python python/mask_sensitivity.py --filter              # writes s1full_masked/
    python python/extract_phenometrics_sar.py \
        --exports $ROOT/s1full_masked --out $RES/masked     # committed estimator
    python python/merge_static_covariates.py \
        --static $ROOT/s1static_masked --panel ... --out ..._static.csv
    python python/mask_sensitivity.py --compare             # both levels

Every number in the arm is therefore produced by the same code that produced the
headline, on a subset of the same inputs. That is the only version of this arm
worth reporting.

THE AMBIGUITY THIS ARM CARRIES, MEASURED RATHER THAN ASSUMED. WorldCereal ships
overlapping per-AEZ tiles and the export mosaicked them, taking the last unmasked
tile at each pixel. Where two tiles disagree the choice is arbitrary. The export
carries worldcereal_pixels_sampled for exactly this reason, and on the committed
run 62 of 10,000 points (0.62%) fall under two tiles -- 54 in Guntur, 7 in
Krishna, 1 in Mayurbhanj. That cannot be resolved from a mosaicked export, so it
is bounded instead: --exclude-overlap drops those 62 points as well, and the arm
is reported both ways. If the two agree, the arbitrariness does not matter at
this sample size, and that is a statement about the result rather than a hope.

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

MASK_DIR = os.path.join(ROOT, "s1_maskflag")
EXPORTS = os.path.join(ROOT, "s1full")
STATIC = os.path.join(ROOT, "s1static")
OUT = os.path.join(RESULTS, "mask_sensitivity")

# Every table this script writes goes out with this float format, so that a
# table written and read back is the SAME table. pandas' default formatting is
# not idempotent: it wrote -2.07850496703054 for -2.0785049670305398, and a
# combined table built by re-reading the per-arm tables then disagreed with them
# in the 16th digit. Measured on this data, %.12g and %.15g are idempotent and
# %.17g is not. 12 significant digits is far beyond anything this study reports,
# and the point is not precision but that a hash of a table means something --
# the same standard patch 3 applied to the figures.
CSV_FLOAT = "%.12g"

MASK_GLOB = "S1_MASKFLAG_*.csv"
MASK_COLS = ["district", "tile_id", "cell_id",
             "in_worldcereal_temporary", "worldcereal_pixels_sampled"]
FLAG = "in_worldcereal_temporary"
NTILES = "worldcereal_pixels_sampled"

# The committed cohort. Both are structural and neither is a tuning knob: 25
# roster districts, 400 points each. A mask table that does not cover exactly
# this set is not a mask for this paper.
N_DISTRICTS = 25
N_POINTS_PER_DISTRICT = 400
N_POINTS = N_DISTRICTS * N_POINTS_PER_DISTRICT


# ---------------------------------------------------------------------------
def _resolve_mask_dir(mask_dir):
    """Find the mask exports whether they sit beside the data or in the repo.

    The 25 mask CSVs are committed under data/s1_maskflag/ -- they total under
    500 KB and committing them is what makes this arm reproducible from a clone
    with no Earth Engine account, which the 225 panel exports are not. So the
    repo-relative location is searched too, and the first hit wins."""
    here = os.path.dirname(os.path.abspath(__file__))
    for c in (mask_dir,
              os.path.join(here, "..", "data", "s1_maskflag"),
              os.path.join(here, "..", "s1_maskflag"),
              os.path.join(ROOT, "s1_maskflag")):
        if glob.glob(os.path.join(c, MASK_GLOB)):
            return c
    return mask_dir


def read_mask(mask_dir=MASK_DIR):
    """Load the 25 per-district mask exports into one table."""
    mask_dir = _resolve_mask_dir(mask_dir)
    files = sorted(glob.glob(os.path.join(mask_dir, MASK_GLOB)))
    if not files:
        raise SystemExit(
            f"no {MASK_GLOB} in {mask_dir} (nor in data/s1_maskflag/ beside "
            f"this script). Run gee/S1_MASK_FLAG.js (25 tasks) and put the CSVs "
            f"in one of those, or set RICEBACI_ROOT.")
    frames = []
    for f in files:
        d = pd.read_csv(f, dtype={"cell_id": str})
        missing = [c for c in MASK_COLS if c not in d.columns]
        if missing:
            raise SystemExit(
                f"{os.path.basename(f)} is missing {missing}. That is the "
                f"signature of an export written without an explicit "
                f"`selectors` list; re-run the task rather than patching it.")
        frames.append(d[MASK_COLS])
    return pd.concat(frames, ignore_index=True), files


def gate(mask, files, panel_path=None, verbose=True):
    """Structural checks. Every one of these has to hold or the arm is not a
    subset of the analysis and comparing it to the headline is meaningless.

    Returns (ok, report) and never raises on a data problem, so --selftest can
    exercise the failure branches."""
    rep = {}
    ok = True

    def chk(name, passed, detail):
        nonlocal ok
        rep[name] = dict(passed=bool(passed), detail=detail)
        ok = ok and bool(passed)
        if verbose:
            print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")

    chk("files", len(files) == N_DISTRICTS,
        f"{len(files)} mask exports, expected {N_DISTRICTS}")
    chk("rows", len(mask) == N_POINTS,
        f"{len(mask)} rows, expected {N_DISTRICTS} x "
        f"{N_POINTS_PER_DISTRICT} = {N_POINTS}")
    chk("districts", mask["district"].nunique() == N_DISTRICTS,
        f"{mask['district'].nunique()} distinct districts, expected "
        f"{N_DISTRICTS}")
    per = mask.groupby("district").size()
    chk("points_per_district", bool((per == N_POINTS_PER_DISTRICT).all()),
        f"min {int(per.min())}, max {int(per.max())}, expected "
        f"{N_POINTS_PER_DISTRICT} everywhere")
    chk("cell_id_unique", mask["cell_id"].nunique() == len(mask),
        f"{len(mask) - mask['cell_id'].nunique()} duplicate cell_id")
    chk("tile_id", mask["tile_id"].nunique() == 1,
        f"tile_id = {sorted(mask['tile_id'].unique())}; the mask must describe "
        f"one cohort")

    # A null flag means WorldCereal did not cover the point. That is a THIRD
    # state, not a zero, and silently treating it as "not cropland" would
    # confuse missing coverage with a negative classification.
    n_null = int(mask[FLAG].isna().sum())
    chk("coverage", n_null == 0,
        f"{n_null} points outside WorldCereal coverage (null flag). A null is "
        f"not a zero; if this is non-zero the arm needs a declared rule for "
        f"those points before it can be reported")

    vals = sorted(pd.unique(mask[FLAG].dropna()))
    chk("flag_coding", set(vals) <= {0, 1}, f"flag values {vals}, expected 0/1")

    # Overlap: bounded, not assumed away. See the module docstring.
    ovl = mask.loc[mask[NTILES] > 1]
    rep["overlap"] = dict(passed=True, detail=f"{len(ovl)} points under >1 tile")
    if verbose:
        by = ovl.groupby("district").size().sort_values(ascending=False)
        print(f"  [note] {len(ovl)} of {len(mask)} points "
              f"({100 * len(ovl) / max(len(mask), 1):.2f}%) fall under more "
              f"than one WorldCereal tile"
              + (f": {', '.join(f'{k} {v}' for k, v in by.items())}"
                 if len(by) else ""))
        print("         where two tiles disagree the mosaic pick is arbitrary; "
              "--exclude-overlap bounds it")

    if panel_path and os.path.exists(panel_path):
        p = pd.read_csv(panel_path, dtype={"cell_id": str},
                        usecols=lambda c: c in ("cell_id", "district"))
        pi = set(p["cell_id"])
        mi = set(mask["cell_id"])
        chk("join", pi == mi,
            f"mask {len(mi)} ids, panel {len(pi)} ids, "
            f"in both {len(mi & pi)}, mask-only {len(mi - pi)}, "
            f"panel-only {len(pi - mi)}")
        j = (p.drop_duplicates("cell_id").merge(
            mask[["cell_id", "district"]], on="cell_id",
            suffixes=("_panel", "_mask")))
        bad = int((j["district_panel"] != j["district_mask"]).sum())
        chk("district_labels", bad == 0,
            f"{bad} cell_id with different district in panel and mask")
    elif verbose:
        print(f"  [SKIP] join against the panel: {panel_path} not present")

    return ok, rep


def whitelist(mask, exclude_overlap=False):
    """The cell_ids the arm keeps."""
    keep = mask[FLAG].fillna(0).astype(int) == 1
    if exclude_overlap:
        keep &= mask[NTILES] <= 1
    return set(mask.loc[keep, "cell_id"])


# ---------------------------------------------------------------------------
def _check_retention(kept, expect, name):
    """The retained set must be EXACTLY the whitelist restricted to this file --
    not merely a subset of it.

    A strict set equality rather than a count or a subset test, because the
    failure mode that matters is a silent shortfall: a few cell_ids lost to a
    dtype coercion or a stray space would make the arm a smaller sample than the
    one it reports, and every comparison against the headline would then be
    against a sample nobody described. Raises rather than warns."""
    if kept != expect:
        raise SystemExit(
            f"{name}: retained {len(kept)} cell_id but the whitelist "
            f"restricted to this file has {len(expect)}. Missing "
            f"{len(expect - kept)}, unexpected {len(kept - expect)}. "
            f"Nothing further was written.")


def filter_one(path, keep, dest):
    """Write `path` keeping only rows whose cell_id is in `keep`.

    Read and written with pandas, not with a line filter: the raw exports carry
    a `.geo` column holding quoted JSON with embedded commas, and a naive
    text filter corrupts it."""
    d = pd.read_csv(path, dtype={"cell_id": str})
    if "cell_id" not in d.columns:
        raise SystemExit(f"{path} has no cell_id column")
    before_cells = set(d["cell_id"])
    out = d[d["cell_id"].isin(keep)]
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    # NO float_format here, deliberately. This writes the masked RAW exports,
    # and its job is to subset rows, not to reformat values: truncating VHVV_med
    # to 12 digits would silently change an analysis input, and the committed
    # masked panels were produced from default-formatted files. CSV_FLOAT applies
    # to the RESULT tables this script writes, not to the data it passes through.
    out.to_csv(dest, index=False)
    kept_cells = set(out["cell_id"])
    _check_retention(kept_cells, before_cells & keep, os.path.basename(path))
    return dict(file=os.path.basename(path),
                rows_in=len(d), rows_out=len(out),
                cells_in=len(before_cells), cells_out=len(kept_cells))


def filter_exports(keep, exports=EXPORTS, static=STATIC, suffix="_masked",
                   verbose=True):
    """Write masked copies of the raw panel exports and the static covariates."""
    rows = []
    ex_dest = exports.rstrip("/") + suffix
    files = sorted(glob.glob(os.path.join(exports, "S1_PHEN_*.csv")))
    if not files:
        raise SystemExit(f"no S1_PHEN_*.csv in {exports}")
    if verbose:
        print(f"\nfiltering {len(files)} panel exports -> {ex_dest}")
    for f in files:
        rows.append(filter_one(f, keep,
                               os.path.join(ex_dest, os.path.basename(f))))
    if verbose:
        t = pd.DataFrame(rows)
        print(f"  {int(t.rows_in.sum()):,} rows in -> "
              f"{int(t.rows_out.sum()):,} rows out "
              f"({100 * t.rows_out.sum() / t.rows_in.sum():.2f}%)")

    # The static covariates must be masked too. merge_static_covariates.py
    # aggregates them to the district mean over that district's cohort points;
    # left unmasked, the district-level covariate would describe a different
    # set of points from the district's phenometric.
    st_rows = []
    st_dest = static.rstrip("/") + suffix
    st_files = sorted(glob.glob(os.path.join(static, "*.csv")))
    if st_files:
        if verbose:
            print(f"filtering {len(st_files)} static covariate files -> "
                  f"{st_dest}")
        for f in st_files:
            st_rows.append(filter_one(
                f, keep, os.path.join(st_dest, os.path.basename(f))))
        if verbose:
            t = pd.DataFrame(st_rows)
            print(f"  {int(t.rows_in.sum()):,} rows in -> "
                  f"{int(t.rows_out.sum()):,} rows out")
    elif verbose:
        print(f"  [SKIP] no static covariate CSVs in {static}; run "
              f"merge_static_covariates.py against the unmasked set only if "
              f"you accept the district-mean mismatch documented above")
    return ex_dest, st_dest, pd.DataFrame(rows), pd.DataFrame(st_rows)


# ---------------------------------------------------------------------------
# The comparison. Cells are the declared ones, imported rather than retyped so
# they cannot drift from §3.9 and the H3 family.
def _cells():
    from permutation_test import CELLS
    return list(CELLS)


def permute_cell(panel0, tab, districts, states, phen, var, fe_cols,
                 n_perm, boot, seed, verbose=True):
    """Within-state permutation p for one cell, on one panel.

    §3.9's conditional spatial sensitivity, also reported for the masked arm
    to hold the reference scheme fixed. Exchangeability within state remains
    unverified. This relabelling exercise does not test bootstrap calibration
    or identify a causal mechanism."""
    from robustness_arms import fit
    from permutation_test import attach, make_permutations
    obs = fit(attach(panel0, tab), phen, var, fe_cols, boot, seed)
    if not obs or obs.get("status") != "estimated" or not n_perm:
        return None
    ts = []
    for i, m in enumerate(make_permutations(districts, states, n_perm, seed), 1):
        r = fit(attach(panel0, tab, m), phen, var, fe_cols, boot, seed)
        if r and r.get("status") == "estimated" and np.isfinite(r["t"]):
            ts.append(r["t"])
        if verbose and i % 250 == 0:
            print(f"      {i}/{n_perm} draws", flush=True)
    if not ts:
        return None
    p = (1 + sum(abs(v) >= abs(obs["t"]) for v in ts)) / (1 + len(ts))
    return dict(t_obs=float(obs["t"]), coef_obs=float(obs["coef"]),
                p_perm=float(p), n_perm_ok=len(ts),
                abs_t_q95=float(np.quantile(np.abs(ts), 0.95)))


def compare(level, committed_panel, masked_panel, exposure_csv, boot, seed,
            fe_cols=("district", "year"), verbose=True, n_perm=0):
    """Fit every declared cell on the committed panel and on the masked panel,
    and report the difference.

    Both sides go through robustness_arms.fit, which is the same function the
    other five arms use, so a difference between the two columns is a difference
    in the SAMPLE and not in the estimator."""
    from robustness_arms import fit
    from attrition_diagnostics import build_exposure_table, load_panel
    from permutation_test import attach

    from permutation_test import district_state_map

    fe_cols = list(fe_cols)
    expo = pd.read_csv(exposure_csv)
    states = district_state_map(expo)
    rows = []
    panels, bare, tabs = {}, {}, {}
    for tag, path in (("committed", committed_panel), ("masked", masked_panel)):
        if not os.path.exists(path):
            raise SystemExit(
                f"{tag} panel not found: {path}\nRun the extraction step in the "
                f"module docstring before --compare; this script will not "
                f"substitute a panel it did not ask for.")
        pan0 = load_panel(path, level, verbose=False)
        tab = build_exposure_table(expo, sorted(pan0["district"].unique()),
                                   sorted(pan0["year"].unique()))
        bare[tag], tabs[tag] = pan0, tab
        panels[tag] = attach(pan0, tab)

    # Whether the masked sample is NESTED in the committed one is a fact about
    # the level, not a property of masking, and it was asserted wrongly here
    # before being measured. At PIXEL level the PLSM is fitted per pixel, so
    # dropping other pixels cannot change a pixel's own fit and the retained set
    # can only shrink. At DISTRICT level the fit is to the district-season MEAN
    # CURVE, so removing pixels changes the curve and a district-season that
    # could not be fitted before can become fittable. Measured on the committed
    # run: pixel 30,293 of 31,741 retained, 1,448 lost and 0 gained, strictly
    # nested; district 4 gained and 2 lost for a net +2, NOT nested. So the
    # district arm is a different sample, not a subsample, and any language about
    # "the same district-seasons" would be false there.
    key = ["district", "year"] if level == "district" else ["cell_id", "year"]
    ret_sets = {t: set(map(tuple, p.loc[p["retained"] == 1, key].values))
                for t, p in panels.items()}
    nested = ret_sets["masked"] <= ret_sets["committed"]
    gained = len(ret_sets["masked"] - ret_sets["committed"])
    lost = len(ret_sets["committed"] - ret_sets["masked"])
    if verbose:
        for tag, p in panels.items():
            print(f"  {tag:<10s} {len(p):6d} rows, "
                  f"{int((p['retained'] == 1).sum()):6d} retained, "
                  f"{p['district'].nunique():2d} districts")
        print(f"  retained set: {lost} lost, {gained} gained under the mask "
              f"-> {'NESTED (a subsample)' if nested else 'NOT NESTED (a different sample)'}")
        print()

    for phen, var, label in _cells():
        r = {t: fit(panels[t], phen, var, fe_cols, boot, seed)
             for t in ("committed", "masked")}
        row = dict(level=level, phenometric=phen, test_var=var, cell=label,
                   fe="+".join(fe_cols), retained_nested=bool(nested),
                   retained_lost=lost, retained_gained=gained)
        for t in ("committed", "masked"):
            v = r[t]
            if v is None or v.get("status") != "estimated":
                row[f"{t}_status"] = (v or {}).get("status", "no_fit")
                row[f"{t}_reason"] = (v or {}).get("reason", "")
                continue
            row[f"{t}_status"] = "estimated"
            for k in ("coef", "se", "t", "n_obs", "n_clusters",
                      "n_treated_clusters"):
                row[f"{t}_{k}"] = v[k]
        if row.get("committed_status") == "estimated" \
                and row.get("masked_status") == "estimated":
            row["d_coef"] = row["masked_coef"] - row["committed_coef"]
            # Is the shift large relative to the committed precision? This is a
            # descriptive ratio, NOT a test: the two samples are nested, so the
            # difference has no standard error of this form and no p-value is
            # reported for it. Stated so nobody reads one in.
            row["d_coef_in_committed_se"] = (
                row["d_coef"] / row["committed_se"]
                if row["committed_se"] > 0 else np.nan)
            row["sign_preserved"] = bool(
                np.sign(row["masked_coef"]) == np.sign(row["committed_coef"]))
            row["both_abs_t_over_2"] = bool(
                abs(row["masked_t"]) > 2 and abs(row["committed_t"]) > 2)
            # A sign flip between two estimates that are both indistinguishable
            # from zero is not a robustness failure, it is noise changing sign,
            # and reporting the bare flip invites exactly the wrong reading. So
            # the flip is qualified by whether the COMMITTED cell was
            # distinguishable from zero in the first place: only then does the
            # sign carry information the mask could have overturned.
            row["sign_flip_material"] = bool(
                not row["sign_preserved"] and abs(row["committed_t"]) > 2)
            # Did the cell cross the conventional threshold in either direction?
            # Recorded rather than narrated, and |t| > 2 is a reference line and
            # not the declared inference -- for the placebo that is p_perm.
            row["crossed_abs_t_2"] = bool(
                (abs(row["committed_t"]) > 2) != (abs(row["masked_t"]) > 2))
        # §3.9's placebo gets the declared inference on BOTH sides, so the
        # masked arm is compared like with like rather than against a p_WCB.
        if n_perm and (phen, var) == ("trough", "S_harvest_window"):
            for tag in ("committed", "masked"):
                if verbose:
                    print(f"    permutation, {tag} ({n_perm} draws):",
                          flush=True)
                pr = permute_cell(bare[tag], tabs[tag],
                                  sorted(bare[tag]["district"].unique()),
                                  states, phen, var, fe_cols, n_perm, boot,
                                  seed, verbose=verbose)
                if pr:
                    for k, v in pr.items():
                        row[f"{tag}_perm_{k}"] = v
                    if verbose:
                        print(f"      p_perm {pr['p_perm']:.4f}   |t|_obs "
                              f"{abs(pr['t_obs']):.3f} vs 95th pct "
                              f"{pr['abs_t_q95']:.3f}  ({pr['n_perm_ok']} ok)")
        rows.append(row)
        if verbose:
            c, m = row.get("committed_coef"), row.get("masked_coef")
            if c is None or m is None:
                print(f"    {label:<58s} "
                      f"committed {row.get('committed_status')}, "
                      f"masked {row.get('masked_status')}")
            else:
                print(f"    {label:<58s} {c:+8.3f} -> {m:+8.3f} d "
                      f"(delta {row['d_coef']:+7.3f}, "
                      f"{row['d_coef_in_committed_se']:+5.2f} committed SE)  "
                      f"t {row['committed_t']:+6.2f} -> {row['masked_t']:+6.2f}")
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Columns whose presence in a results table depends on a run SETTING rather than
# on the data. Keyed on the setting's actual reason, so it cannot drift from
# compare(): the permutation block exists if and only if --n-perm was given.
def _settings_columns(n_perm):
    return {"_perm_": ("--n-perm 2000 (§3.9's declared count)", n_perm > 0)}


def _preflight_columns(dest, n_perm, allow=False):
    """Check the contract BEFORE doing any work, not after.

    _refuse_poorer below is the backstop and catches any column loss, but it can
    only fire once the fits are done -- and `compare` loads both panels first, so
    in a checkout with no panels it is never reached at all. The executor's run of
    patch 5 proved that: the demonstration I asked for stopped at the
    missing-panel guard and never reached the column guard, so the guard
    protecting the committed tables could not be confirmed from the repository.
    That was a defect in the ordering, not in the executor's run.

    This check needs no panels and no fits. It reads the existing table's header,
    asks whether this invocation's SETTINGS can produce those columns, and refuses
    in about a tenth of a second. As a side effect it also stops a user who forgot
    the flag from waiting through 8,000 permutation draws to be told."""
    if allow or not os.path.exists(dest):
        return
    try:
        have = list(pd.read_csv(dest, nrows=0).columns)
    except Exception:
        return
    for marker, (remedy, will_produce) in _settings_columns(n_perm).items():
        present = [c for c in have if marker in c]
        if present and not will_produce:
            raise SystemExit(
                f"REFUSING to overwrite {dest}\n"
                f"  it has {len(present)} column(s) matching {marker!r} that this "
                f"invocation cannot produce:\n    {', '.join(present)}\n"
                f"  The committed table was made with a setting this run did not "
                f"use. Add {remedy}.\n"
                f"  Checked before any fitting, so nothing was computed and "
                f"nothing was written.\n"
                f"  Pass --allow-poorer only if dropping those columns is "
                f"intended.")


def _refuse_poorer(dest, new, allow=False):
    """Refuse to overwrite an existing table with one that has fewer columns.

    Added after a real defect: run_all.sh's first version of this stage called
    --compare with no --n-perm, so a full pipeline run would have silently
    replaced the committed tables -- which carry ten permutation columns -- with
    column-poorer ones, and the repository would no longer have reproduced its own
    results. The comment in run_all.sh is not the guard; this is. A missing column
    means the run was made with weaker settings than the committed result used,
    and that is a stop, not a warning."""
    if allow or not os.path.exists(dest):
        return
    try:
        old_cols = list(pd.read_csv(dest, nrows=0).columns)
    except Exception:
        return
    missing = [c for c in old_cols if c not in new.columns]
    if not missing:
        return
    raise SystemExit(
        f"REFUSING to overwrite {dest}\n"
        f"  the existing table has {len(missing)} column(s) this run did not "
        f"produce:\n    {', '.join(missing)}\n"
        f"  That means this run used weaker settings than the committed result. "
        f"If the missing columns are the permutation ones, add --n-perm 2000 "
        f"(§3.9's declared count). Nothing was written.\n"
        f"  Pass --allow-poorer only if dropping those columns is intended.")


# ---------------------------------------------------------------------------
# §3.5's DISCLOSURE RULE, which the pooled arm does not satisfy.
#
# §3.5 verbatim: "both the primary-mask (RiceAtlas rice polygons) and
# intersection-mask (RiceAtlas n WorldCereal 2021 `temporarycrops`, a
# general-cropland classifier) DiD coefficients are computed for **every district x
# cyclone unit** and reported side by side before either is discussed."
#
# The pooled arm reports 24 level x variant cells. That is a different object. An
# external re-audit on 2026-09-13 said so and was right; test_classification.md now
# records the arm as narrower than its own commitment. This closes it.
#
# §4.3's zero-treated-support rule governs the many units that cannot yield an
# estimate: "If treated support in a district x cyclone x season stratum is zero, or
# the wild-cluster bootstrap is not computable for that stratum, the DiD/TWFE
# coefficient for that stratum is reported as 'not estimable' rather than omitted
# silently or imputed." So every unit appears, with a reason.
#
# WHAT A SINGLE UNIT'S COEFFICIENT CAN BE. A district x cyclone unit has exactly one
# treated season, so the within-district estimate is the difference between the
# marker in that season and the same district's other retained seasons -- a two-group
# mean difference, not a regression with usable standard errors. With one treated
# cluster, cluster-robust inference cannot reject at any level whatever the true
# effect (MacKinnon & Webb 2018), which §2's H4 note already gives as the reason the
# four-of-six significance criterion was retired. The point estimate is reported and
# INFERENCE IS MARKED UNAVAILABLE RATHER THAN MANUFACTURED.
PRIMARY_LABEL = "primary mask (RiceAtlas n Chen et al. rice, the committed cohort)"
INTERSECT_LABEL = "intersection mask (primary n WorldCereal temporarycrops)"


def district_curve_panel(path, marker):
    """The COMMITTED district-season panel, indexed by (district, year).

    §3.5's own amendment (docs/Protocol_v1.md, 2026-09-13) and the header of this
    module both say the district-season value is a PLSM fit to the district-season
    MEAN CURVE, not an average of pixel phenometrics. This function therefore READS
    `phen_panel_district_season.csv` -- the committed estimator's own output, for
    whichever mask produced it -- and does no aggregation of its own.

    WHY THIS FUNCTION EXISTS AT ALL (2026-09-14, second pass). It replaces
    `district_season_means`, which grouped the PIXEL panel by district and year and
    took the mean. That was wrong, and it was wrong against a rule written at the top
    of this same file 570 lines above the violation. Measured on the committed
    panels, switching to the declared estimand moves the median per-unit coefficient
    by 9.6 d on trough, 7.5 d on heading and 12.4 d on harvest, with maxima of 63.2,
    34.3 and 70.6 d, and flips the sign of 6 of 44 trough units, 12 of 44 heading and
    19 of 44 harvest. So it was a different number, not a differently-labelled one.
    The superseded function is kept below, marked, so the withdrawn table can be
    reproduced and the size of the error checked.
    """
    d = pd.read_csv(path)
    for col in ("district", "year", "estimable", marker):
        if col not in d.columns:
            raise SystemExit(f"{path}: expected column {col!r} in the district-season "
                             f"panel; got {list(d.columns)[:8]}...")
    d = d[d["estimable"].astype(int) == 1].copy()
    d[marker] = pd.to_numeric(d[marker], errors="coerce")
    d = d[np.isfinite(d[marker])]
    d["year"] = d["year"].astype(int)
    n = (d["n_pixels"] if "n_pixels" in d.columns
         else pd.Series(np.nan, index=d.index))
    out = pd.DataFrame({"m": d[marker].values, "n": n.values},
                       index=pd.MultiIndex.from_arrays(
                           [d["district"].values, d["year"].values],
                           names=["district", "year"]))
    return out.sort_index()


def district_season_means(panel, marker):
    """SUPERSEDED 2026-09-14 (second pass). Mean of the marker over retained PIXELS.

    This is NOT the declared district-season estimand and must never be used as one.
    `extract_phenometrics_sar.py` fits the PLSM to the district-season mean curve; an
    average of separately-fitted pixel dates is a different quantity, and this
    module's own header says so. Kept only so the withdrawn 2026-09-14 per-unit table
    can be reproduced and the error measured. Use `district_curve_panel`.
    """
    d = panel[panel["retained"].astype(int) == 1].copy()
    d[marker] = pd.to_numeric(d[marker], errors="coerce")
    d = d[np.isfinite(d[marker])]
    g = d.groupby(["district", "year"])[marker].agg(["mean", "size"])
    return g.rename(columns={"mean": "m", "size": "n"})


def unit_did(panel, district, season, controls, flagged=(), pre_offset=1):
    """A genuine 2x2 difference-in-differences for ONE district x cyclone unit.

    (treated_post - treated_pre) - mean over the DECLARED clean-control districts of
    (control_post - control_pre), on the committed district-season panel, with post
    the exposure season and pre the k = -1 reference §3.8 B already uses.

    `controls` and `flagged` ARE NOT COMPUTED HERE. They come from
    `event_study.derive_stack`, which is this repository's audited implementation of
    §3.8 B's stack rule: clean controls are roster districts with severe exposure to
    NO catalogued storm in t-1, t or t+1; same-storm fringe districts are dropped;
    and a treated district severely exposed to a different storm inside the window is
    flagged. `event_study --selftest` asserts that derivation reproduces the
    committed `docs/cyclone_footprints_ibtracs50km.csv` exactly for all five
    cyclones that file covers, which is why it -- and not a local copy -- is used.

    WHAT THIS REPLACED, TWICE, EACH TIME MEASURED RATHER THAN ASSERTED.

    1. `unit_before_after` (superseded 2026-09-14, first pass) computed the exposed
       season minus that same district's OTHER seasons, with no comparison district
       anywhere in it. Confounded: 38 of 47 estimable units (81%) drew at least one
       control season from another severe exposure of the same district.

    2. The first DiD (superseded 2026-09-14, second pass) fixed that but got three
       things wrong at once, and an external audit caught all three. It averaged
       pixel phenometrics instead of reading the district mean-curve fit; it tested
       controls over t-1 and t only, not t-1, t and t+1, which left Titli with 19
       controls where the declared rule leaves 5, fourteen of them Fani- or
       Bulbul-exposed in 2019; and it swept all nine severe storms in the catalogue
       rather than §3.8 B's six declared named cyclones, so Michaung, Dana and
       Montha entered a table reported against a six-cyclone design.

    One treated cluster, so NO inference: MacKinnon & Webb (2018). The point estimate
    is the deliverable, which is what §3.5 asks for.
    """
    pre = season - pre_offset
    idx = panel.index

    def cell(dist, yr):
        return panel.loc[(dist, yr)] if (dist, yr) in idx else None

    tp, tq = cell(district, season), cell(district, pre)
    if tp is None:
        return dict(status="not_estimable",
                    reason=f"zero treated support: no estimable district-season for "
                           f"{district} {season}")
    if tq is None:
        return dict(status="not_estimable",
                    reason=f"no pre-season ({pre}) for {district}; the k=-1 "
                           f"reference is unavailable")
    diffs, missing = [], []
    for dist in controls:
        if dist == district:
            continue
        cp, cq = cell(dist, season), cell(dist, pre)
        if cp is None or cq is None:
            missing.append(dist)
            continue
        diffs.append(float(cp["m"]) - float(cq["m"]))
    if not diffs:
        return dict(status="not_estimable",
                    reason=f"none of the {len(controls)} declared clean controls has "
                           f"both {pre} and {season} estimable")
    d_treated = float(tp["m"]) - float(tq["m"])
    d_control = float(np.mean(diffs))
    return dict(status="estimated",
                coef=d_treated - d_control,
                d_treated=d_treated, d_control=d_control,
                pre_season=pre,
                n_declared_controls=int(len(controls)),
                n_control_used=int(len(diffs)),
                n_control_unestimable=int(len(missing)),
                treated_other_severe_exposure=bool(district in set(flagged)),
                inference="unavailable: one treated cluster (MacKinnon & Webb 2018)")


def unit_before_after(panel, district, season):
    """SUPERSEDED 2026-09-14 (first pass). Exposed season minus the district's others.

    Kept so the pre-2026-09-14 table can be reproduced and so the DiD can be read
    against it, and for no other purpose. It is NOT a difference-in-differences and
    must never be reported as one: it has no comparison district, and 81% of its
    estimable units drew at least one control season from another severe exposure of
    the same district. Now takes the same (district, year) -> m panel as `unit_did`
    so the two are read off identical inputs.
    """
    idx = panel.index
    have = [(d, y) for (d, y) in idx if d == district]
    if (district, season) not in idx:
        return dict(status="not_estimable",
                    reason=f"zero treated support: no estimable row for {district} "
                           f"{season}")
    others = [float(panel.loc[(d, y), "m"]) for (d, y) in have if y != season]
    if not others:
        return dict(status="not_estimable",
                    reason=f"no other estimable season for {district}")
    return dict(status="estimated",
                coef=float(panel.loc[(district, season), "m"]) - float(np.mean(others)),
                n_other_seasons=int(len(others)),
                inference="unavailable: one treated cluster (MacKinnon & Webb 2018)")


def declared_roster(exposure, roster, years):
    """The cyclone roster, in two explicitly separated blocks.

    PRIMARY: §3.8 B's six estimable named cyclones, taken from
    `event_study.ESTIMABLE` so there is one roster in the repository and not two --
    TITLI 2018, FANI 2019, BULBUL 2019, AMPHAN 2020, YAAS 2021, REMAL 2024.

    ADDITIONAL: every other storm in the catalogue with severe exposure to a roster
    district inside the panel years -- MICHAUNG 2023, DANA 2024, MONTHA 2025 as the
    catalogue now stands. These are reported because §3.5 asks for every unit and
    because hiding them would be worse, but they are labelled `additional_severe`
    and are NOT part of §3.5's claim or of any §4 sign test. §4 declares no sign for
    them and §3.8 B does not build stacks for them.

    Superseded 2026-09-14 (second pass): the previous version enumerated all nine
    severe storms into a single undifferentiated table and reported it against a
    design §3.8 B states over six. An external audit caught it.
    """
    from event_study import ESTIMABLE
    primary = [(nm, int(ay)) for nm, ay in ESTIMABLE if int(ay) in years]
    sev = exposure[(exposure["severity_class"].astype(str).str.strip().str.lower()
                    == "severe")
                   & exposure["district_gadm_name"].isin(roster)
                   & exposure["season"].astype(int).isin(sorted(years))]
    have = {(_norm_storm(nm), ay) for nm, ay in primary}
    extra = []
    for nm, ay in (sev[["storm_name", "season"]].drop_duplicates()
                   .sort_values(["season", "storm_name"])
                   .itertuples(index=False)):
        key = (_norm_storm(nm), int(ay))
        if not any(k[0] in key[0] or key[0] in k[0] for k in have if k[1] == key[1]):
            extra.append((str(nm), int(ay)))
    return primary, extra


def _norm_storm(s):
    return "".join(ch for ch in str(s).upper() if ch.isalpha())


def per_unit(primary_panel, intersect_panel, exposure_csv, marker="trough",
             verbose=True, superseded_panels=None):
    """See the body's docstring below; `superseded_panels` is OPT-IN and off by default.

    IT MUST STAY OPT-IN. The withdrawn pixel-average comparison needs the masked PIXEL
    panels, which are ~117 MiB per variant and are NOT committed. When it was computed
    unconditionally the committed per-unit tables could not be regenerated from a clone
    -- they carried two extra columns that no committed input can produce. Found by
    running this arm against a directory holding only committed files, after an external
    audit pointed out that the masked district panels themselves were missing from the
    repository. The main tables must depend on committed inputs only.
    """
    """Every district x cyclone unit, both masks, side by side.

    Reads the COMMITTED district-season panels (a PLSM fit to each mask's own mean
    curve) and takes the stack membership from `event_study.derive_stack`. Nothing
    about the estimand or the control rule is re-implemented here; that was the
    defect of the withdrawn version and this module's header forbids it.

    `superseded_panels` optionally supplies the two PIXEL panels so the withdrawn
    pixel-average coefficient can be reported alongside for the declared units --
    the measurement that makes the supersession checkable rather than asserted.
    """
    from event_study import derive_stack
    expo = pd.read_csv(exposure_csv)
    dsm = {"primary": district_curve_panel(primary_panel, marker),
           "intersection": district_curve_panel(intersect_panel, marker)}
    roster = sorted({d for (d, _y) in dsm["primary"].index}
                    | {d for (d, _y) in dsm["intersection"].index})
    years = {int(y) for (_d, y) in dsm["primary"].index}
    primary_storms, extra_storms = declared_roster(expo, roster, years)

    sup = None
    if superseded_panels:
        from attrition_diagnostics import load_panel
        sup = {}
        for tag, path in superseded_panels.items():
            if path and os.path.exists(path):
                sup[tag] = district_season_means(
                    load_panel(path, "pixel", verbose=False), marker)

    rows = []
    for block, storms in (("declared_named", primary_storms),
                          ("additional_severe", extra_storms)):
        for storm, t_c in storms:
            footprint, controls, flagged = derive_stack(expo, roster, storm, t_c)
            for dist in roster:
                row = dict(district=dist, storm=storm, season=int(t_c),
                           marker=marker, roster_block=block,
                           district_exposed=bool(dist in footprint),
                           n_declared_clean_controls=len(controls))
                if not row["district_exposed"]:
                    row.update(status="not_estimable",
                               reason=f"zero treated support: {dist} is not in the "
                                      f"severe footprint of {storm} {t_c}")
                    rows.append(row)
                    continue
                for tag in ("primary", "intersection"):
                    r = unit_did(dsm[tag], dist, int(t_c), controls, flagged)
                    for k, v in r.items():
                        row[f"{tag}_{k}"] = v
                    ba = unit_before_after(dsm[tag], dist, int(t_c))
                    row[f"{tag}_superseded_before_after_coef"] = ba.get("coef", np.nan)
                    if sup and tag in sup:
                        w = unit_did(sup[tag], dist, int(t_c), controls, flagged)
                        row[f"{tag}_withdrawn_pixelavg_coef"] = w.get("coef", np.nan)
                both = (row.get("primary_status") == "estimated"
                        and row.get("intersection_status") == "estimated")
                row["status"] = "estimated" if both else "not_estimable"
                if both:
                    row["d_coef_intersection_minus_primary"] = (
                        row["intersection_coef"] - row["primary_coef"])
                    row["sign_agrees"] = bool(np.sign(row["intersection_coef"])
                                              == np.sign(row["primary_coef"]))
                    for tag in ("primary", "intersection"):
                        b = pd.to_numeric(
                            row.get(f"{tag}_superseded_before_after_coef"),
                            errors="coerce")
                        row[f"{tag}_did_minus_superseded"] = (
                            row[f"{tag}_coef"] - b if np.isfinite(b) else np.nan)
                        # Only emit the withdrawn-comparison delta when the
                        # comparison was actually computed. Emitting it as all-NaN
                        # put two empty columns in the committed tables -- schema
                        # debris that a reader has to rule out. Found by an external
                        # audit, 2026-09-14.
                        if f"{tag}_withdrawn_pixelavg_coef" in row:
                            w = pd.to_numeric(row[f"{tag}_withdrawn_pixelavg_coef"],
                                              errors="coerce")
                            row[f"{tag}_did_minus_withdrawn_pixelavg"] = (
                                row[f"{tag}_coef"] - w if np.isfinite(w) else np.nan)
                else:
                    row["reason"] = "; ".join(
                        str(row.get(f"{t}_reason", "")) for t in
                        ("primary", "intersection") if row.get(f"{t}_reason"))
                rows.append(row)
    t = pd.DataFrame(rows)
    if verbose:
        _per_unit_report(t, marker, primary_storms, extra_storms, roster)
    return t


def _per_unit_report(t, marker, primary_storms, extra_storms, roster):
    est = t[t["status"] == "estimated"]
    dec = est[est["roster_block"] == "declared_named"]
    add = est[est["roster_block"] == "additional_severe"]
    print(f"\n  {PRIMARY_LABEL}\n  {INTERSECT_LABEL}")
    print(f"\n  ESTIMAND: the committed district-season panel for each mask -- a PLSM")
    print(f"  fit to that mask's district-season MEAN CURVE. Not an average of pixel")
    print(f"  phenometrics; see district_curve_panel's docstring for why that matters.")
    print(f"  STACKS: event_study.derive_stack, §3.8 B's rule (clean controls carry no")
    print(f"  severe exposure in t-1, t or t+1; same-storm fringe dropped).")
    print(f"\n  declared named cyclones (§3.8 B): "
          f"{', '.join(f'{n} {y}' for n, y in primary_storms)}")
    print(f"  additional severe storms, reported but NOT part of the §3.5 claim: "
          f"{', '.join(f'{n} {y}' for n, y in extra_storms) or '(none)'}")
    print(f"\n  {len(t)} district x cyclone rows over "
          f"{len(primary_storms) + len(extra_storms)} storms x {len(roster)} districts")
    print(f"    estimated     {len(est)}   ({len(dec)} declared, {len(add)} additional)")
    print(f"    not estimable {len(t) - len(est)}  (reported, not omitted -- "
          f"§4.3 zero-treated-support rule)")
    for label, blk in (("DECLARED NAMED CYCLONES -- this is the §3.5 result", dec),
                       ("additional severe storms -- exploratory, not the claim", add)):
        if not len(blk):
            continue
        print(f"\n  {label}, {len(blk)} units")
        d = blk["d_coef_intersection_minus_primary"]
        print(f"    intersection minus primary: mean {d.mean():+.3f} d   "
              f"median {d.median():+.3f} d   sd {d.std(ddof=1):.3f} d   "
              f"max |delta| {d.abs().max():.3f} d")
        print(f"    sign agrees in {int(blk['sign_agrees'].sum())} of {len(blk)}")
        nc = pd.to_numeric(blk["primary_n_control_used"], errors="coerce").dropna()
        if len(nc):
            print(f"    declared clean controls used per unit: median {nc.median():.0f}"
                  f", min {nc.min():.0f}, max {nc.max():.0f}")
        fl = blk["primary_treated_other_severe_exposure"].astype(bool).sum()
        print(f"    treated district itself severely exposed inside t-1..t+1: "
              f"{int(fl)} of {len(blk)} (§3.8 B's flag; those read as an increment)")
        for col, what in (("primary_did_minus_superseded",
                           "the SUPERSEDED before-after contrast"),
                          ("primary_did_minus_withdrawn_pixelavg",
                           "the WITHDRAWN pixel-average DiD")):
            if col not in blk:
                continue
            dd = pd.to_numeric(blk[col], errors="coerce").dropna()
            if len(dd):
                print(f"    DiD minus {what}, primary mask, {len(dd)} units: "
                      f"median {dd.median():+.3f} d, max |delta| {dd.abs().max():.3f} d")
    if len(dec):
        print(f"\n  per declared unit, both masks side by side, before either is "
              f"discussed:")
        for _, r in dec.sort_values(["season", "storm", "district"]).iterrows():
            print(f"    {r.storm:<10} {r.season}  {r.district:<19} "
                  f"primary {r.primary_coef:+8.2f} d   "
                  f"intersection {r.intersection_coef:+8.2f} d   "
                  f"delta {r.d_coef_intersection_minus_primary:+7.2f} d"
                  f"   (ctl {int(r.primary_n_control_used):2d}"
                  f"{', FLAGGED' if r.primary_treated_other_severe_exposure else ''})")


def selftest():
    """Two halves. The first needs no data at all and always runs; the second
    runs only where the exports are present and says [SKIP] otherwise.

    The rule this follows was set after permutation_test.py --selftest was found
    to require a pipeline output: a self-test that needs the analysis to have
    been run is not a self-test. Verified by relocating the code AND removing
    the data, not by relocating alone."""
    print("=" * 74)
    print("SELF-TEST -- mask_sensitivity.py")
    print("=" * 74)
    ok_all = True

    def _chk(cond, msg):
        nonlocal ok_all
        ok_all &= bool(cond)
        print(f"  [{'PASS' if cond else 'FAIL'}] {msg}")

    # ---- §3.5's per-unit DiD -------------------------------------------
    # Four districts, 2018-2021. A COMMON TREND of +5 d from 2019 to 2020 affects
    # every district; the treated district D0 additionally gets +8 d in 2020. A
    # correct DiD returns +8 and a before-after contrast does not, which is the
    # whole reason §3.5 asks for a DiD.
    def _panel(effect=8.0, trend=5.0, dirty_pre=False):
        rows = []
        for dist in ("D0", "D1", "D2", "D3"):
            for yr in (2018, 2019, 2020, 2021):
                base = 210.0
                if yr >= 2020:
                    base += trend
                if dist == "D0" and yr == 2020:
                    base += effect
                for cid in range(5):
                    rows.append({"district": dist, "year": yr,
                                 "cell_id": f"{dist}_{cid}", "retained": 1,
                                 "trough": base})
        return pd.DataFrame(rows)

    # The panel above is a PIXEL panel, which is what the WITHDRAWN version read.
    # The declared estimand is the district-season mean-curve fit, so the tests below
    # build the (district, year) -> m panel directly, as district_curve_panel returns
    # it, and a separate test pins that district_curve_panel refuses a pixel panel.
    def _dpanel(effect=8.0, trend=5.0):
        rows = []
        for dist in ("D0", "D1", "D2", "D3"):
            for yr in (2018, 2019, 2020, 2021):
                base = 210.0
                if yr >= 2020:
                    base += trend
                if dist == "D0" and yr == 2020:
                    base += effect
                rows.append({"district": dist, "year": yr, "m": base, "n": 5})
        d = pd.DataFrame(rows)
        return d.set_index(["district", "year"])[["m", "n"]].sort_index()

    CTL = ["D1", "D2", "D3"]
    r = unit_did(_dpanel(), "D0", 2020, CTL)
    _chk(r["status"] == "estimated" and abs(r["coef"] - 8.0) < 1e-9,
         f"a planted +8 d effect under a +5 d common trend gives DiD "
         f"{r.get('coef', float('nan')):+.3f} -- the trend cancels")
    _chk(r["pre_season"] == 2019 and r["n_control_used"] == 3,
         f"pre-season is the k=-1 reference ({r['pre_season']}) and all 3 declared "
         f"controls are used")

    ba = unit_before_after(_dpanel(), "D0", 2020)
    _chk(abs(ba["coef"] - 8.0) > 1.0,
         f"the SUPERSEDED before-after contrast gives {ba['coef']:+.3f} on the same "
         f"data -- wrong by {abs(ba['coef'] - 8.0):.2f} d, because the common trend "
         f"does not cancel")

    # DEFECT 1 (withdrawn 2026-09-14, second pass): the pixel-average estimand.
    # district_curve_panel must read the committed district-season panel and must
    # REFUSE a pixel panel, so the wrong input cannot be passed silently again.
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        good = os.path.join(td, "phen_panel_district_season.csv")
        pd.DataFrame([{"district": "D0", "year": 2020, "n_pixels": 7,
                       "estimable": 1, "trough": 215.0},
                      {"district": "D0", "year": 2019, "n_pixels": 7,
                       "estimable": 0, "trough": 999.0}]).to_csv(good, index=False)
        g = district_curve_panel(good, "trough")
        _chk(list(g.index) == [("D0", 2020)] and abs(float(g.loc[("D0", 2020), "m"])
                                                     - 215.0) < 1e-9,
             "district_curve_panel reads the committed mean-curve fit and drops "
             "estimable=0 rows without averaging anything")
        bad = os.path.join(td, "phen_panel_sar.csv")
        pd.DataFrame([{"district": "D0", "year": 2020, "cell_id": "x",
                       "retained": 1, "trough": 215.0}]).to_csv(bad, index=False)
        try:
            district_curve_panel(bad, "trough")
            refused = False
        except SystemExit:
            refused = True
        _chk(refused,
             "handed a PIXEL panel, district_curve_panel refuses instead of "
             "averaging it -- the defect an external audit caught on 2026-09-14")

    # DEFECT 2: the control window. The declared rule is t-1, t AND t+1, and the
    # control sets must come from event_study.derive_stack, not from a local copy.
    from event_study import derive_stack as _ds, ESTIMABLE as _EST
    _expo = pd.DataFrame([
        # D3 is severely exposed in t+1 only: the two-season rule keeps it, the
        # declared three-season rule drops it. This is the Titli 19-vs-5 defect.
        dict(district_gadm_name="D0", season=2020, storm_name="STORMA",
             severity_class="severe", max_wind_kt_within_50km=90),
        dict(district_gadm_name="D3", season=2021, storm_name="STORMB",
             severity_class="severe", max_wind_kt_within_50km=90),
    ])
    fp, ctl, flg = _ds(_expo, ["D0", "D1", "D2", "D3"], "STORMA", 2020)
    _chk(fp == ["D0"] and ctl == ["D1", "D2"] and "D3" not in ctl,
         "derive_stack drops a control severely exposed in t+1 -- the declared "
         f"three-season window; controls {ctl} exclude D3")
    r_decl = unit_did(_dpanel(), "D0", 2020, ctl)
    r_two = unit_did(_dpanel(), "D0", 2020, ["D1", "D2", "D3"])
    _chk(r_decl["n_control_used"] == 2 and r_two["n_control_used"] == 3,
         "and the DiD uses exactly the declared controls it is handed (2, not 3) -- "
         "it no longer computes its own")

    # DEFECT 3: the roster. The primary block must be §3.8 B's six named cyclones,
    # and any other severe storm must land in a separately labelled block.
    _exp2 = pd.DataFrame([
        dict(district_gadm_name="Ganjam", season=2018, storm_name="TITLI",
             severity_class="severe", max_wind_kt_within_50km=90),
        dict(district_gadm_name="Puri", season=2019, storm_name="FANI",
             severity_class="severe", max_wind_kt_within_50km=90),
        dict(district_gadm_name="Puri", season=2024, storm_name="DANA",
             severity_class="severe", max_wind_kt_within_50km=90),
    ])
    prim, extra = declared_roster(_exp2, ["Ganjam", "Puri"],
                                  {2018, 2019, 2020, 2021, 2023, 2024, 2025})
    _chk([n for n, _ in prim] == [n for n, _ in _EST],
         f"the primary roster is §3.8 B's declared six from event_study.ESTIMABLE: "
         f"{[n for n, _ in prim]}")
    _chk(("DANA", 2024) in extra and not any(n == "DANA" for n, _ in prim),
         "DANA lands in the separately labelled additional_severe block, never in "
         "the declared one -- the withdrawn table mixed all nine severe storms")

    # the treated district's own adjacent exposure is flagged, not hidden
    fp2, ctl2, flg2 = _ds(pd.DataFrame([
        dict(district_gadm_name="D0", season=2020, storm_name="STORMA",
             severity_class="severe", max_wind_kt_within_50km=90),
        dict(district_gadm_name="D0", season=2019, storm_name="STORMC",
             severity_class="severe", max_wind_kt_within_50km=90),
    ]), ["D0", "D1", "D2", "D3"], "STORMA", 2020)
    r3 = unit_did(_dpanel(), "D0", 2020, ctl2, flg2)
    _chk(r3["treated_other_severe_exposure"] is True and r3["status"] == "estimated",
         "a treated district severely exposed to a DIFFERENT storm inside t-1..t+1 "
         "is FLAGGED and still reported, per §3.8 B")

    # no pre-season at all -> not estimable, with the reason named
    r4 = unit_did(_dpanel(), "D0", 2018, CTL)
    _chk(r4["status"] == "not_estimable" and "k=-1" in r4["reason"],
         "the first season has no k=-1 reference and is reported not estimable")

    # no declared control has both seasons -> not estimable, and it says so
    r5 = unit_did(_dpanel(), "D0", 2020, ["D9"])
    _chk(r5["status"] == "not_estimable" and "declared clean controls" in r5["reason"],
         "with no usable declared control the unit is not estimable, never silently "
         "estimated from whatever happens to be in the panel")

    # zero treated support is still caught
    r6 = unit_did(_dpanel(), "D9", 2020, CTL)
    _chk(r6["status"] == "not_estimable" and "zero treated support" in r6["reason"],
         "a district absent from the panel gives zero-treated-support, not a crash")

    # no planted effect -> zero, not the trend
    r7 = unit_did(_dpanel(effect=0.0), "D0", 2020, CTL)
    _chk(abs(r7["coef"]) < 1e-9,
         f"with no planted effect the DiD returns {r7['coef']:+.3g}, not the trend")

    def check(name, passed, detail=""):
        nonlocal ok_all
        ok_all = ok_all and bool(passed)
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}"
              + (f" -- {detail}" if detail else ""))

    # ---- data-free: the gate must FAIL on each defect it exists to catch ----
    def synth(n_dist=N_DISTRICTS, n_pts=N_POINTS_PER_DISTRICT, **kw):
        rows = []
        for i in range(n_dist):
            for j in range(n_pts):
                rows.append(dict(district=f"D{i:02d}", tile_id="cohort_v2",
                                 cell_id=f"{i:02d}_{j:04d}",
                                 in_worldcereal_temporary=int(j % 5 > 0),
                                 worldcereal_pixels_sampled=1))
        d = pd.DataFrame(rows)
        for k, v in kw.items():
            d = v(d)
        return d

    good = synth()
    files = [f"S1_MASKFLAG_D{i:02d}.csv" for i in range(N_DISTRICTS)]
    ok, _ = gate(good, files, panel_path=None, verbose=False)
    check("gate accepts a well-formed mask table", ok)

    ok, rep = gate(good, files[:-1], panel_path=None, verbose=False)
    check("gate rejects 24 files", not ok and not rep["files"]["passed"])

    ok, rep = gate(synth(n_pts=399), files, panel_path=None, verbose=False)
    check("gate rejects 399 points in a district",
          not ok and not rep["points_per_district"]["passed"])

    dup = good.copy()
    dup.loc[dup.index[-1], "cell_id"] = dup["cell_id"].iloc[0]
    ok, rep = gate(dup, files, panel_path=None, verbose=False)
    check("gate rejects a duplicated cell_id",
          not ok and not rep["cell_id_unique"]["passed"])

    nul = good.copy()
    nul.loc[nul.index[:3], FLAG] = np.nan
    ok, rep = gate(nul, files, panel_path=None, verbose=False)
    check("gate rejects points outside WorldCereal coverage (null != 0)",
          not ok and not rep["coverage"]["passed"])

    bad = good.copy()
    bad.loc[bad.index[:3], FLAG] = 100
    ok, rep = gate(bad, files, panel_path=None, verbose=False)
    check("gate rejects a flag that is not 0/1 (the raw class code, unmapped)",
          not ok and not rep["flag_coding"]["passed"])

    # ---- data-free: the whitelist and the overlap bound -------------------
    ovl = good.copy()
    ovl.loc[ovl.index[:10], NTILES] = 2
    w_all = whitelist(ovl, exclude_overlap=False)
    w_cln = whitelist(ovl, exclude_overlap=True)
    n_ovl_crop = int(((ovl[NTILES] > 1) & (ovl[FLAG] == 1)).sum())
    check("whitelist keeps only flagged points",
          len(w_all) == int(good[FLAG].sum()),
          f"{len(w_all)} == {int(good[FLAG].sum())}")
    check("--exclude-overlap drops exactly the multi-tile flagged points",
          len(w_all) - len(w_cln) == n_ovl_crop,
          f"{len(w_all)} - {len(w_cln)} == {n_ovl_crop}")
    check("--exclude-overlap never keeps a point the plain arm dropped",
          w_cln <= w_all)

    # ---- data-free: the filter, including its refusal --------------------
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        raw = pd.DataFrame([
            dict(cell_id=cid, bin_index=b, VHVV_med=-9.0 + 0.1 * b,
                 district="D00", year=2017,
                 **{".geo": '{"type":"MultiPoint","coordinates":[]}'})
            for cid in ("00_0000", "00_0001", "00_0002") for b in range(5)])
        src = os.path.join(td, "S1_PHEN_D00_2017.csv")
        raw.to_csv(src, index=False)
        dst = os.path.join(td, "out", "S1_PHEN_D00_2017.csv")
        st = filter_one(src, {"00_0001", "00_0002", "99_9999"}, dst)
        back = pd.read_csv(dst, dtype={"cell_id": str})
        check("filter keeps whole cell_id blocks, all bins",
              st["rows_out"] == 10 and st["cells_out"] == 2
              and sorted(back["cell_id"].unique()) == ["00_0001", "00_0002"],
              f"{st['rows_out']} rows, {st['cells_out']} cells")
        check("filter preserves the quoted .geo column intact",
              ".geo" in back.columns
              and back[".geo"].iloc[0].startswith('{"type"'),
              "embedded JSON with commas survives the round trip")
        check("filter tolerates a whitelist id absent from the file",
              st["cells_out"] == 2, "99_9999 is simply not present")
    # The shortfall guard, called directly so the test exercises the shipped
    # code rather than a restatement of its condition.
    def guard_raises(kept, expect):
        try:
            _check_retention(set(kept), set(expect), "test")
            return False
        except SystemExit:
            return True

    check("shortfall guard passes on an exact match",
          not guard_raises({"a", "b"}, {"a", "b"}))
    check("shortfall guard REJECTS a subset (a silently smaller sample)",
          guard_raises({"a"}, {"a", "b"}),
          "this is the failure that would make the arm a sample nobody "
          "described")
    check("shortfall guard rejects an unexpected extra id",
          guard_raises({"a", "b", "c"}, {"a", "b"}))

    # The column-poverty guard, which exists because run_all.sh shipped without
    # --n-perm and would have silently degraded the committed tables.
    with tempfile.TemporaryDirectory() as td:
        rich = pd.DataFrame([dict(a=1, b=2, committed_perm_p_perm=0.04)])
        poor = pd.DataFrame([dict(a=1, b=2)])
        dst = os.path.join(td, "t.csv")
        rich.to_csv(dst, index=False, float_format=CSV_FLOAT)

        def refuses(frame, allow=False):
            try:
                _refuse_poorer(dst, frame, allow)
                return False
            except SystemExit:
                return True

        check("column guard REFUSES a table missing a committed column",
              refuses(poor), "this is the run_all.sh --n-perm defect")
        check("column guard allows an equally rich table", not refuses(rich))
        check("column guard allows a RICHER table",
              not refuses(pd.DataFrame([dict(a=1, b=2, c=3,
                                             committed_perm_p_perm=0.04)])))
        check("column guard can be overridden deliberately",
              not refuses(poor, allow=True))
        # A real test, not a restatement: the guard must not raise when there is
        # no existing file to degrade, because a first run has nothing to protect.
        def raises_on_absent():
            try:
                _refuse_poorer(os.path.join(td, "absent.csv"), poor)
                return False
            except SystemExit:
                return True

        check("column guard is silent when there is no file to overwrite",
              not raises_on_absent(), "a first run has nothing to protect")

        # The PRE-FLIGHT form of the same contract: it must reach a verdict from
        # the header alone, with no panels and no fits anywhere in sight. This is
        # what makes the guard demonstrable in a checkout that has only the repo.
        def pre(n_perm, allow=False, path=dst):
            try:
                _preflight_columns(path, n_perm, allow)
                return False
            except SystemExit:
                return True

        rich_perm = pd.DataFrame([dict(a=1, committed_perm_p_perm=0.04,
                                       masked_perm_p_perm=0.02)])
        dst2 = os.path.join(td, "t2.csv")
        rich_perm.to_csv(dst2, index=False, float_format=CSV_FLOAT)
        check("pre-flight REFUSES --n-perm 0 against a table with perm columns",
              pre(0, path=dst2),
              "reached with no panels present, which the post-hoc guard cannot be")
        check("pre-flight allows --n-perm 2000 against the same table",
              not pre(2000, path=dst2))
        # A genuinely perm-free table. The first draft of this check used `dst`,
        # which already carries committed_perm_p_perm, so it asserted the guard
        # would stay silent on a table that should trip it -- and the self-test
        # caught that, which is the whole point of writing the fixture explicitly.
        plain = pd.DataFrame([dict(a=1, b=2, coef=0.5)])
        dst3 = os.path.join(td, "t3.csv")
        plain.to_csv(dst3, index=False, float_format=CSV_FLOAT)
        check("pre-flight is silent on a table with no settings-dependent "
              "columns", not pre(0, path=dst3))
        check("pre-flight can be overridden deliberately",
              not pre(0, allow=True, path=dst2))
        check("pre-flight is silent when there is no file to overwrite",
              not pre(0, path=os.path.join(td, "nope.csv")))

    # ---- conditional: the real mask table, if it is here -----------------
    if glob.glob(os.path.join(_resolve_mask_dir(MASK_DIR), MASK_GLOB)):
        mask, files = read_mask()
        panel = os.path.join(RESULTS, "phen_panel_sar.csv")
        ok, rep = gate(mask, files,
                       panel_path=panel if os.path.exists(panel) else None,
                       verbose=False)
        check("the committed mask table passes the gate", ok,
              "; ".join(k for k, v in rep.items() if not v["passed"]) or "all")
        w = whitelist(mask)
        check("committed mask retains a usable fraction",
              0.5 < len(w) / len(mask) < 1.0,
              f"{len(w)} of {len(mask)} = {len(w) / len(mask):.4f}")
    else:
        print(f"  [SKIP] no {MASK_GLOB} found; the checks above need "
              f"no data and are the ones that must hold anywhere")

    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


# ---------------------------------------------------------------------------
def main(argv=None):
    from attrition_diagnostics import SEED
    ap = argparse.ArgumentParser(
        description="§3.5 mask-comparison arm against ESA WorldCereal.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--gate", action="store_true",
                    help="run the structural checks on the mask exports and "
                         "stop; exits non-zero on any failure")
    ap.add_argument("--filter", action="store_true",
                    help="write masked copies of the raw exports and static "
                         "covariates, for the committed estimator to consume")
    ap.add_argument("--collect", action="store_true",
                    help="merge the per-level, per-variant tables into "
                         "Table_SX_MaskSensitivity_ALL.csv. Follows "
                         "robustness_arms.py's --collect convention so the "
                         "combined table is a declared output of committed code "
                         "rather than an ad-hoc concatenation.")
    ap.add_argument("--per-unit", action="store_true",
                    help="§3.5's disclosure rule: primary-mask and "
                         "intersection-mask coefficients for EVERY district x "
                         "cyclone unit, side by side, every non-estimable unit "
                         "reported per §4.3 rather than omitted.")
    ap.add_argument("--marker", default="trough",
                    help="phenometric for --per-unit")
    ap.add_argument("--withdrawn-comparison", action="store_true",
                    help="also compute the WITHDRAWN pixel-average DiD alongside, and "
                         "write to Table_SX_MaskPerUnit_withdrawnCompare_<marker>.csv. "
                         "Needs the masked PIXEL panels, which are ~117 MiB and are NOT "
                         "committed, so the main table is produced without this flag.")
    ap.add_argument("--compare", action="store_true",
                    help="fit every declared cell on the committed and masked "
                         "panels and tabulate the difference")
    ap.add_argument("--exclude-overlap", action="store_true",
                    help="also drop points under more than one WorldCereal "
                         "tile, bounding the mosaic arbitrariness")
    ap.add_argument("--level", choices=["district", "pixel"], default="district")
    ap.add_argument("--mask-dir", default=MASK_DIR)
    ap.add_argument("--exports", default=EXPORTS)
    ap.add_argument("--static", default=STATIC)
    ap.add_argument("--masked-results", default=os.path.join(RESULTS, "masked"))
    ap.add_argument("--exposure",
                    default="district_cyclone_exposure_ibtracs50km.csv")
    ap.add_argument("--allow-poorer", action="store_true",
                    help="permit overwriting an existing results table with one "
                         "that has fewer columns. Off by default: a column-poorer "
                         "table means the run used weaker settings than the "
                         "committed result.")
    ap.add_argument("--boot", type=int, default=999)
    ap.add_argument("--n-perm", type=int, default=0,
                    help="within-state permutation draws for the §3.9 placebo "
                         "cell, run on BOTH panels. 0 skips it; 2000 is §3.9's "
                         "declared count.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args(argv)
    if a.seed is None:
        a.seed = SEED

    if a.selftest:
        return selftest()

    if a.per_unit:
        from robustness_arms import _find_doc
        mdir = a.masked_results + ("_noovl" if a.exclude_overlap else "")
        # THE DECLARED ESTIMAND: the district-season panel, which is a PLSM fit to
        # each mask's own district-season MEAN CURVE. Until 2026-09-14 (second pass)
        # this read phen_panel_sar.csv -- the PIXEL panel -- and averaged it, which
        # is a different quantity and is forbidden by this module's own header.
        pri = os.path.join(RESULTS, "phen_panel_district_season.csv")
        ints = os.path.join(mdir, "phen_panel_district_season.csv")
        for p_, lab, src in ((pri, "primary", None), (ints, "intersection", mdir)):
            if os.path.exists(p_):
                continue
            # The primary panel is COMMITTED; the intersection panel is committed
            # too as of 2026-09-14. So a miss here means a partial checkout, and
            # the message must say which panel and how to get THAT one -- the
            # earlier version named the masked export path whichever panel was
            # missing, which sent a reader after the wrong file.
            if src is None:
                how = ("This panel is committed at results/"
                       "phen_panel_district_season.csv. A miss means an incomplete "
                       "checkout: verify the file is present in your clone. To "
                       "rebuild it you need the 225 raw exports (gee/s1_block.js):\n"
                       "    python python/extract_phenometrics_sar.py "
                       "--exports $RICEBACI_ROOT/s1full --out $RICEBACI_ROOT/results")
            else:
                how = (f"This panel is committed at {os.path.relpath(p_, RESULTS)} "
                       f"under results/. A miss means an incomplete checkout. To "
                       f"rebuild it you need the masked exports, which require the "
                       f"225 raw exports first (run_all.sh stage 13):\n"
                       f"    python python/mask_sensitivity.py --filter\n"
                       f"    python python/extract_phenometrics_sar.py "
                       f"--exports $RICEBACI_ROOT/s1full_masked --out {src}")
            raise SystemExit(
                f"{lab} district-season panel not found: {p_}\n"
                f"  The per-unit arm reads the district-season MEAN-CURVE fit, never "
                f"the pixel panel.\n  {how}")
        # The withdrawn pixel-average quantity is OPT-IN (--withdrawn-comparison)
        # because it needs the masked PIXEL panels, which are ~117 MiB and are not
        # committed. Including it unconditionally made the committed tables
        # unreproducible from a clone; they now depend on committed inputs only.
        sup = None
        if a.withdrawn_comparison:
            sup = {"primary": os.path.join(RESULTS, "phen_panel_sar.csv"),
                   "intersection": os.path.join(mdir, "phen_panel_sar.csv")}
            for p_, lab in sup.items():
                if not os.path.exists(lab):
                    raise SystemExit(
                        f"--withdrawn-comparison needs the {p_} PIXEL panel at {lab}, "
                        f"which this repository does not commit (~117 MiB). Omit the "
                        f"flag to produce the reproducible table.")
        print("=" * 78)
        print("§3.5 DISCLOSURE RULE -- every district x cyclone unit, both masks")
        print("=" * 78)
        t = per_unit(pri, ints, _find_doc(a.exposure), marker=a.marker,
                     superseded_panels=sup)
        os.makedirs(a.out, exist_ok=True)
        dest = os.path.join(
            a.out, (f"Table_SX_MaskPerUnit_withdrawnCompare_{a.marker}.csv"
                    if a.withdrawn_comparison
                    else f"Table_SX_MaskPerUnit_{a.marker}.csv"))
        t.to_csv(dest, index=False, float_format=CSV_FLOAT)
        print(f"\n  wrote {dest}")
        return 0

    if a.collect:
        fs = sorted(f for f in glob.glob(os.path.join(
            a.out, "Table_SX_MaskSensitivity_*.csv"))
            if not f.endswith("_ALL.csv"))
        if not fs:
            raise SystemExit(f"nothing to collect in {a.out}")
        parts = []
        for f in fs:
            d = pd.read_csv(f)
            d.insert(0, "arm", "noovl" if f.endswith("_noovl.csv") else "plain")
            parts.append(d)
        df = pd.concat(parts, ignore_index=True).sort_values(
            ["arm", "level", "phenometric", "test_var"])
        dest = os.path.join(a.out, "Table_SX_MaskSensitivity_ALL.csv")
        df.to_csv(dest, index=False, float_format=CSV_FLOAT)
        print(f"wrote {dest} ({len(df)} rows from {len(fs)} file(s))")
        return 0

    # One suffix drives the export dirs, the results dir and the table name, so
    # the plain arm and the overlap-excluded arm can never overwrite each other.
    suffix = "_masked_noovl" if a.exclude_overlap else "_masked"
    res_suffix = "_noovl" if a.exclude_overlap else ""

    if a.gate or a.filter:
        mask, files = read_mask(a.mask_dir)
        print(f"mask exports: {len(files)} files, {len(mask)} rows")
        panel = os.path.join(RESULTS, "phen_panel_sar.csv")
        ok, _ = gate(mask, files,
                     panel_path=panel if os.path.exists(panel) else None)
        if not ok:
            print("\n*** STOP *** the mask table is not a clean subset of the "
                  "committed cohort, so comparing a masked result to the "
                  "headline would compare two different samples. Nothing was "
                  "written.")
            return 2
        w = whitelist(mask, a.exclude_overlap)
        print(f"\n  whitelist: {len(w)} of {len(mask)} points "
              f"({100 * len(w) / len(mask):.2f}%)"
              + ("  [overlap points excluded]" if a.exclude_overlap else ""))
        os.makedirs(a.out, exist_ok=True)
        # The merged flag table, written as a declared output rather than left as
        # something a reader has to reconstruct by concatenating 25 files.
        merged = os.path.join(a.out, "mask_flag_all.csv")
        mask.to_csv(merged, index=False, float_format=CSV_FLOAT)
        print(f"  wrote {merged} ({len(mask)} rows)")
        if a.gate and not a.filter:
            return 0
        ex, st, t1, t2 = filter_exports(w, a.exports, a.static, suffix)
        t1.to_csv(os.path.join(a.out, f"filter_report{suffix}.csv"), index=False)
        print(f"\nwrote {os.path.join(a.out, f'filter_report{suffix}.csv')}")
        print("\nNEXT, with the committed estimator -- this script will not "
              "re-implement it:")
        print(f"  python python/extract_phenometrics_sar.py \\\n"
              f"      --exports {ex} --out {a.masked_results}{res_suffix}")
        print(f"  python python/merge_static_covariates.py --static {st} \\\n"
              f"      --panel {a.masked_results}{res_suffix}/"
              f"phen_panel_sar.csv \\\n"
              f"      --out {a.masked_results}{res_suffix}/"
              f"phen_panel_sar_static.csv")
        print(f"  (and the same for phen_panel_district_season.csv)")
        print(f"  python python/mask_sensitivity.py --compare --level "
              f"{a.level}")
        return 0

    if a.compare:
        from robustness_arms import _find_doc
        stem = ("phen_panel_district_season_static.csv" if a.level == "district"
                else "phen_panel_sar_static.csv")
        committed = os.path.join(RESULTS, stem)
        masked = os.path.join(a.masked_results + res_suffix, stem)
        print("=" * 78)
        print(f"{a.level.upper()}  §3.5 mask-comparison arm"
              + ("  [overlap points excluded]" if a.exclude_overlap else ""))
        print("=" * 78)
        os.makedirs(a.out, exist_ok=True)
        dest = os.path.join(
            a.out, f"Table_SX_MaskSensitivity_{a.level}{suffix}.csv")
        # Settings contract first: needs no panels, no fits, and is reachable in a
        # checkout that has nothing but this repository.
        _preflight_columns(dest, a.n_perm, a.allow_poorer)
        t = compare(a.level, committed, masked, _find_doc(a.exposure),
                    a.boot, a.seed, n_perm=a.n_perm)
        _refuse_poorer(dest, t, a.allow_poorer)
        t.to_csv(dest, index=False, float_format=CSV_FLOAT)
        print(f"\nwrote {dest}")
        print("\nNOTE on the delta column: no standard error and NO p-value is "
              "reported for it, and none should be read in. At pixel level the "
              "masked sample is strictly nested in the committed one, so the "
              "difference has no standard error of the usual form. At district "
              "level it is not even nested -- the mean curve changes when pixels "
              "are dropped, so some district-seasons become fittable and others "
              "stop being fittable -- which makes the district arm a different "
              "sample rather than a subsample. The delta is a descriptive shift, "
              "expressed in committed SE units. The inferential question is "
              "answered by the permutation columns, not by the delta.")
        return 0

    ap.error("nothing to do: pass --selftest, --gate, --filter or --compare")


if __name__ == "__main__":
    sys.exit(main())
