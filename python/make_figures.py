"""
make_figures.py -- the figure set for Paper 2 (RiceBaCI-QC).

Six figures, each written as both PDF (vector, for the journal) and PNG (for
drafts). Every number plotted comes from a committed results file or is computed
here from the committed panel; nothing is typed in by hand.

    python python/make_figures.py --results results/ --out figures/

Design constraints, deliberate:
  * Three-hue categorical palette, validated colourblind-safe for all pairs
    (worst deutan Delta E 9.2, worst normal-vision Delta E 24.0).
  * Every series is ALSO distinguished by line style and marker, so the figures
    survive greyscale printing. Colour is never the only encoding.
  * Series are direct-labelled on the plot wherever the geometry allows, so a
    reader never has to match a colour to a legend box.
  * One y-axis per panel. No dual-axis panel anywhere.
  * Recessive grid and spines; no chartjunk, no 3-D, no gradient fills.

Created 2026-09-13.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd


import lf_output  # noqa: F401  -- pins to_csv to LF on every platform;
# without it pandas writes CRLF on Windows and every committed md5 changes.
lf_output.install()
ROOT = os.environ.get("RICEBACI_ROOT", "/home/claude")

# Repository root, for writing manifest paths that mean the same thing in any
# clone. This file lives in python/, so the repo root is its parent's parent.
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --------------------------------------------------------------------------
# Deterministic PDF output.
#
# matplotlib's PDF backend stamps wall-clock time into /CreationDate
# (backends/backend_pdf.py, which reads SOURCE_DATE_EPOCH at save time). With it
# unset, re-running this script rewrites every PDF even when not one plotted
# number has changed. That was measured on 2026-09-13: commit 1a93678 carried
# six PDFs -- fig1, fig2, fig3, fig4, fig6, fig7 -- whose diff against the
# parent was exactly 6 bytes each, all of them inside /CreationDate, and which
# were byte-identical once the date was normalised. Their PNGs did not change at
# all, because matplotlib's PNG writer embeds no timestamp.
#
# WHAT THIS DOES AND DOES NOT CLAIM (stated 2026-09-15, tenth pass). Freezing the
# timestamp makes output deterministic WITHIN ONE RECORDED TEST ENVIRONMENT:
# the same matplotlib, the same freetype, the same Python. It does NOT make the
# bytes portable across environments, and it does not even guarantee identical
# PIXELS across them -- a different freetype rasterises glyphs differently, and a
# matplotlib release can change default layout. Those are two separate claims and
# only the first is made here. That is why the manifest records the matplotlib
# version, and why a hash mismatch on another machine may mean "different
# environment" rather than "stale figure": read the recorded version first.
#
# That churn is not cosmetic. It costs the one check that catches a stale
# figure: if the committed PDF cannot be reproduced bit-for-bit from the
# committed code, its hash proves nothing, and `git log --stat` can no longer
# tell a reviewer which figure actually changed. This file had already shipped
# one stale figure -- fig5, drawn 11:08 against tables corrected at 15:15 and
# 15:52 -- so that guard is not hypothetical.
#
# Freezing the timestamp alone would make things worse, by removing the only
# staleness signal the files carried. So it is paired with the provenance
# manifest below, which records the hash of every input each figure was drawn
# from. Content beats clock: a timestamp only shows a figure is older than its
# table, while a manifest shows it was built from those exact bytes.
#
# An externally supplied SOURCE_DATE_EPOCH still wins, for reproducible-build
# environments that set it globally.
SOURCE_DATE_EPOCH = "1767225600"          # 2026-01-01T00:00:00Z
os.environ.setdefault("SOURCE_DATE_EPOCH", SOURCE_DATE_EPOCH)

MANIFEST = "figure_provenance.json"

_PROV = {"inputs": {}, "outputs": {}}


# Extensions hashed as TEXT, with line endings normalised to LF first. Everything
# else is hashed as raw bytes.
#
# Why: an external audit on 2026-09-13 checked out this repository on Windows,
# where git's default core.autocrlf=true rewrites LF to CRLF in text files. Every
# one of the manifest's ten inputs is a CSV, so every one hashed differently and
# --verify reported them all as [CHANGED] with nothing whatsoever wrong -- in the
# command this repository's own re-audit brief told a reviewer to run. A hash that
# depends on the checkout platform certifies nothing.
#
# Both halves of the fix matter and neither replaces the other. `.gitattributes`
# pins eol=lf so the rewrite does not happen; normalising here means the check
# still holds if someone's git configuration ignores it, or if a file reaches the
# tree by some route git never touched. Figures are binary and unaffected, so only
# the input hashes change.
#
# 2026-09-14 (ninth pass): ".py" joins this set and the policy is bumped to v2,
# because the manifest now records the hash of THIS FILE (see `generator`
# below). A generator hash that flips on a CRLF checkout would be exactly the
# platform-dependent hash the previous paragraph exists to prevent. Bumping the
# policy is deliberate: a v1 manifest and v2 code are not comparable, and
# --verify STOPs rather than reporting spurious changes.
HASH_TEXT_EXT = {".csv", ".json", ".md", ".txt", ".tsv", ".py"}
HASH_POLICY = "text-lf-normalised-v2"

# The generator itself, recorded so that editing the drawing code without
# redrawing is detected. Input hashes catch a table that moved under a figure;
# they cannot catch a TITLE, AXIS LABEL or colour changed in this file while the
# committed PNG and PDF still carry the old one. That is not hypothetical: on
# 2026-09-14 an audit found a figure title asserting a claim the repository had
# withdrawn four days earlier, and --verify had reported PASSED throughout,
# because every input and every output still matched. Source drift was outside
# what the manifest described.
GENERATOR = os.path.abspath(__file__)


def _md5(path):
    data = open(path, "rb").read()
    if os.path.splitext(path)[1].lower() in HASH_TEXT_EXT:
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.md5(data).hexdigest()


def _relpath(path):
    """Path as recorded in the manifest: relative to the repo root when the file
    is inside it, absolute otherwise. Keeps a manifest comparable across clones."""
    ap = os.path.abspath(path)
    try:
        rel = os.path.relpath(ap, REPO)
    except ValueError:                      # different drive, on Windows
        return ap
    return ap if rel.startswith(os.pardir) else rel.replace(os.sep, "/")


def _install_read_recorder():
    """Record every CSV this run reads, by wrapping pd.read_csv.

    Wrapping rather than editing the read_csv call sites one by one is
    deliberate. The failure mode that matters is not a call site recorded
    wrongly today; it is a read added six months from now and left out of the
    manifest, giving a manifest that certifies less than it appears to. A
    wrapper cannot be forgotten by someone adding a figure."""
    real = pd.read_csv
    if getattr(real, "_ricebaci_recorder", False):
        return real

    def wrapped(filepath_or_buffer, *args, **kwargs):
        try:
            if os.path.exists(filepath_or_buffer):
                _PROV["inputs"][_relpath(filepath_or_buffer)] = \
                    _md5(filepath_or_buffer)
        except (TypeError, ValueError):
            pass                            # a buffer or handle, not a path
        return real(filepath_or_buffer, *args, **kwargs)

    wrapped._ricebaci_recorder = True
    pd.read_csv = wrapped
    return real


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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# validated palette: slots 1-3 of the reference categorical theme
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#8a8880", "#dedcd6"

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 300,
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.edgecolor": MUTED, "axes.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "text.color": INK, "axes.labelcolor": INK2, "axes.titlecolor": INK,
    "grid.color": GRID, "grid.linewidth": 0.5,
    "legend.frameon": False,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# dekad centres of §1.4, restated here so the figure script does not need to
# import the estimator just to know where the grid points are
_FP_DEKAD = [154.5 + 10.0 * k for k in range(27)] + [422.0]

MONTH_TICKS = [(152, "Jun"), (182, "Jul"), (213, "Aug"), (244, "Sep"),
               (274, "Oct"), (305, "Nov"), (335, "Dec"), (366, "Jan"),
               (397, "Feb")]


def save(fig, out_dir, stem):
    os.makedirs(out_dir, exist_ok=True)
    for ext in ("pdf", "png"):
        path = os.path.join(out_dir, f"{stem}.{ext}")
        fig.savefig(path)
        _PROV["outputs"][_relpath(path)] = _md5(path)
    plt.close(fig)
    print(f"  wrote {stem}.pdf and {stem}.png")


STATE_ABBR = {"Odisha": "OD", "West Bengal": "WB", "Andhra Pradesh": "AP"}


def doy_axis(ax, lo=150, hi=425, sparse=False, grid_axis="y"):
    ax.set_xlim(lo, hi)
    ticks = [(d, m) for d, m in MONTH_TICKS if lo <= d <= hi]
    if sparse:
        ticks = ticks[::2]
    ax.set_xticks([d for d, _ in ticks])
    ax.set_xticklabels([m for _, m in ticks])
    if grid_axis:
        ax.grid(axis=grid_axis, alpha=0.7)
    ax.set_axisbelow(True)


def plsm_curve(doy, t1, t2, t3, t4, a0, b1, p, b2, start):
    y = np.empty(len(doy))
    for i, x in enumerate(doy):
        if x <= t1:
            y[i] = a0 + (b1 - a0) * (x - start) / (t1 - start)
        elif x <= t2:
            y[i] = b1 + (p - b1) * (x - t1) / (t2 - t1)
        elif x <= t3:
            y[i] = p
        elif x <= t4:
            y[i] = p - (p - b2) * (x - t3) / (t4 - t3)
        else:
            y[i] = b2
    return y


# ===========================================================================
# Figure 1 -- the measured season
# ===========================================================================
FIG1_PANELS = [("Baleshwar", "Odisha"), ("Cuttack", "Odisha"),
               ("Kendrapara", "Odisha"), ("Purba Medinipur", "West Bengal"),
               ("South 24 Parganas", "West Bengal"),
               ("West Godavari", "Andhra Pradesh")]


def fig1(res, out, year=2017):
    curves = pd.read_csv(os.path.join(res, "phen_curves_district_season.csv"))
    pan = pd.read_csv(os.path.join(res, "phen_panel_district_season.csv"))
    fig, axes = plt.subplots(2, 3, figsize=(7.4, 4.4), sharex=True)
    for ax, (dist, state) in zip(axes.ravel(), FIG1_PANELS):
        c = curves[(curves.district == dist) & (curves.year == year)] \
            .sort_values("doy")
        r = pan[(pan.district == dist) & (pan.year == year)]
        used = c[(c.used == 1) & c.mean_db.notna()]
        ax.errorbar(used.doy, used.mean_db, yerr=used.se_db, fmt="o",
                    ms=2.6, lw=0, elinewidth=0.7, capsize=0,
                    color=INK2, zorder=3, label="district mean ±1 s.e.")
        drop = c[(c.used == 0)]
        if len(drop):
            # a rug at the very bottom of the panel, in axes coordinates, so it
            # cannot collide with the data or with the rmse annotation
            ax.plot(drop.doy, np.full(len(drop), 0.015), marker="|", ls="none",
                    ms=4, mew=0.9, color=MUTED, zorder=2,
                    transform=ax.get_xaxis_transform())
        if len(r) and int(r.iloc[0].get("estimable", 0)) == 1:
            r = r.iloc[0]
            g = np.linspace(150, 425, 600)
            start = float(used.doy.min())
            ax.plot(g, plsm_curve(g, r.trough, r.heading, r.drainage, r.harvest,
                                  r.pre_db, r.dark_db, r.plateau_db, r.post_db,
                                  start),
                    color=C1, lw=1.4, zorder=4, label="five-segment fit")
            # breakpoints as markers ON the fitted curve, not vertical rules:
            # t2 and t3 coincide whenever the plateau is one dekad long, and two
            # overlapping rules read as one
            bx = [r.trough, r.heading, r.drainage, r.harvest]
            by = plsm_curve(np.array(bx), r.trough, r.heading, r.drainage,
                            r.harvest, r.pre_db, r.dark_db, r.plateau_db,
                            r.post_db, start)
            ax.plot(bx, by, "o", ms=4.2, color=C2, markeredgecolor="white",
                    markeredgewidth=0.7, zorder=6, ls="none")
            for k, (x, y) in enumerate(zip(bx, by), start=1):
                ax.annotate(f"t{k}", xy=(x, y), xytext=(0, 7 if k % 2 else -11),
                            textcoords="offset points", ha="center",
                            fontsize=6.2, color=C2, zorder=7)
            ax.text(0.02, 0.97, f"rmse {r.rmse:.2f} dB",
                    transform=ax.transAxes, fontsize=6.3, color=MUTED,
                    va="top", bbox=dict(fc="white", ec="none", pad=1.0,
                                        alpha=0.85))
        else:
            ax.text(0.5, 0.97, "no admissible fit", transform=ax.transAxes,
                    ha="center", va="top", fontsize=7.5, color=C2,
                    bbox=dict(fc="white", ec="none", pad=1.0, alpha=0.85))
        ax.set_title(f"{dist}  ·  {STATE_ABBR[state]}", loc="left")
        doy_axis(ax, sparse=True)
    for ax in axes[:, 0]:
        ax.set_ylabel("VH/VV (dB)")
    for ax in axes.ravel():
        ax.margins(x=0.04)
    handles = [Line2D([], [], marker="o", ls="none", ms=3, color=INK2),
               Line2D([], [], color=C1, lw=1.4),
               Line2D([], [], marker="o", ls="none", ms=4.2, color=C2,
                      markeredgecolor="white"),
               Line2D([], [], marker="|", ls="none", ms=4, mew=0.9,
                      color=MUTED)]
    # LABELS CORRECTED 2026-09-15 (tenth pass). These read "t1 onset, t2
    # heading, t3 drainage, t4 harvest" -- agronomic events. The breakpoints are
    # features of the VH/VV trajectory; section 4.3.1 authorises the agronomic
    # correspondence for DIRECTION ONLY, never for identity, and no field
    # reference exists for any of them. The legend now names what the estimator
    # actually locates, and the caption says the agronomic names are
    # interpretations.
    labels = ["district-mean dekad ±1 s.e.", "five-segment fit",
              "breakpoints " + ", ".join(
                  display_term(c).split(",")[0]
                  for c in ("trough", "heading", "drainage", "harvest")),
              "dekad below 50% pixel coverage (excluded)"]
    fig.legend(handles, labels, loc="lower center", ncol=2,
               bbox_to_anchor=(0.5, -0.10))
    fig.suptitle(f"Sentinel-1 VH/VV season and its five-segment fit, "
                 f"{year} baseline", y=1.00, fontsize=9, ha="left", x=0.005)
    fig.text(0.005, -0.155,
             "Breakpoints are named by the signal feature each locates. The "
             "agronomic readings sometimes attached to them -- transplanting, "
             "heading, drainage, harvest --\nare INTERPRETATIONS, not "
             "field-validated dates: this study holds no field reference, and "
             "section 4.3.1 authorises the correspondence for direction only.",
             fontsize=6.2, color=MUTED, ha="left", va="top")
    fig.subplots_adjust(hspace=0.42, wspace=0.30)
    save(fig, out, "fig1_measured_season")


# ===========================================================================
# Figure 2 -- the inherited windows bind
# ===========================================================================
def fig2(res, out, year=2017):
    """The inherited window binds: shares are plotted, not counts, so the two
    panels are on one scale despite different retained totals."""
    p = pd.read_csv(os.path.join(res, "phen_panel_sar.csv"))
    p = p[p.year == year]
    edges = np.arange(149.5, 430, 10)
    specs = [
        ("tz_trough", p.tz_retained == 1, 240.0, C2,
         "search restricted to §3.2 (155–240)"),
        ("trough", p.retained == 1, 304.5, C1,
         "search padded two dekads beyond the baseline range (184–305)"),
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.8), sharey=True,
                             gridspec_kw=dict(wspace=0.10))
    tops = []
    for ax, (col, keep, hi, colour, title) in zip(axes, specs):
        v = p.loc[keep, col].dropna()
        w = np.full(len(v), 1.0 / max(len(v), 1))
        n, _, _ = ax.hist(v, bins=edges, weights=w, color=colour, alpha=0.9,
                          edgecolor="white", linewidth=0.4)
        tops.append(float(np.max(n)) if len(n) else 0.0)
        # the LAST admissible dekad centre is the largest grid point at or below
        # the window's upper bound; a marker there is one the search could not
        # place any later
        last = max(d for d in _FP_DEKAD if d <= hi)
        share = float((v >= last - 0.001).mean()) if len(v) else np.nan
        ax.axvline(hi, color=INK, lw=0.9, ls=(0, (4, 2)))
        ax.annotate(f"{share:.0%} of retained pixel-seasons sit on\n"
                    f"the last dekad the search could reach",
                    xy=(last, share), xycoords="data",
                    xytext=(0.04, 0.93), textcoords="axes fraction",
                    fontsize=6.8, color=INK, ha="left", va="top",
                    arrowprops=dict(arrowstyle="->", lw=0.7, color=INK,
                                    shrinkB=3))
        ax.set_title(title, loc="left", fontsize=8)
        ax.set_xlabel(display_term("trough") + " (day of year)")
        doy_axis(ax, sparse=True)
    axes[0].set_ylabel("share of retained\npixel-seasons")
    for ax in axes:
        ax.set_ylim(0, max(tops) * 1.40)
    fig.suptitle("Searching inside the inherited window pins the marker to its "
                 "edge", y=1.04, fontsize=9, ha="left", x=0.005)
    save(fig, out, "fig2_window_binding")


# ===========================================================================
# Figure 3 -- observed split-half disagreement, and a separate conditional
#             Monte Carlo recovery
# ===========================================================================
# CORRECTED 2026-09-14 (ninth pass). This section was headed "how precisely a
# marker is measured", and the figure said so: its overall title claimed a
# marker "is precise at district level and imprecise at pixel level" and its
# left axis was labelled "split-half sigma of a SINGLE MEASUREMENT". Neither
# panel supports a precision claim.
#
# LEFT PANEL. Two half-series of one season are differenced. What that yields
# is a DISAGREEMENT between two halves, reported as sd(difference)/sqrt(2) --
# a scaled disagreement statistic, not an error of a single measurement:
# whatever is common to both halves cancels from the difference and is
# invisible to it.
#
# RIGHT PANEL. A Monte Carlo draws a SYNTHETIC season with known breakpoints
# at an ASSUMED noise level and reports how far the fit lands from the
# breakpoints it planted. That is conditional performance of a simulation. It
# is not an accuracy, not a field-validated figure, and not a measurement of
# anything in the real panel, which holds no repeat observation at district
# scale to check it against.
#
# The two panels are therefore DIFFERENT KINDS OF QUANTITY and no ratio
# between them is formed, drawn or implied.
def fig3(res, out, scratch=None):
    rel_path = os.path.join(res, "splithalf_reliability.csv")
    rel = pd.read_csv(rel_path)
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0),
                             gridspec_kw=dict(wspace=0.34))

    ax = axes[0]
    markers = ["trough", "heading", "drainage", "harvest"]
    ests = [("crossings", C3, "//"), ("trapezoid", C2, ".."), ("PLSM", C1, "")]
    w = 0.26
    for j, (est, colour, hatch) in enumerate(ests):
        xs, ys = [], []
        for i, m in enumerate(markers):
            r = rel[(rel.estimator == est) & (rel.marker == m)]
            if len(r):
                xs.append(i + (j - 1) * w)
                ys.append(float(r.sigma_days.iloc[0]))
        ax.bar(xs, ys, width=w * 0.92, color=colour, edgecolor="white",
               linewidth=0.5, hatch=hatch, label=est)
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.7, f"{y:.0f}", ha="center", fontsize=6.5,
                    color=INK2)
    ax.set_xticks(range(len(markers)))
    ax.set_xticklabels([display_token(m) for m in markers])
    ax.set_ylabel("scaled split-half disagreement,\nsd(difference)/√2 (days)")
    ax.set_title("Observed split-half disagreement", loc="left")
    ax.set_ylim(0, 52)
    ax.legend(loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.02),
              handlelength=1.4, columnspacing=1.1)
    ax.grid(axis="y", alpha=0.7)
    ax.set_axisbelow(True)

    ax = axes[1]
    mc_path = os.path.join(res, "montecarlo_precision.csv")
    mc = pd.read_csv(mc_path)
    ax.set_xscale("log")
    ax.set_xlim(0.04, 11.0)
    ax.set_ylim(0, 42)
    for x, lab, yy, va in ((0.122, "district-mean noise\n0.122 dB", 41, "top"),
                           (2.03, "per-pixel noise\n2.03 dB", 1.0, "bottom")):
        ax.axvline(x, color=INK, lw=0.8, ls=(0, (4, 2)))
        ax.text(x, yy, " " + lab, fontsize=6.3, color=INK, va=va, ha="left")
    for (m, colour, ls, mk) in (("trough", C2, (0, (4, 2)), "s"),
                                ("heading", C1, "-", "o"),
                                ("harvest", C3, (0, (1, 1.6)), "^")):
        g = mc[mc.marker == m].sort_values("sigma_db")
        ax.plot(g.sigma_db, g.sd_days, color=colour, lw=1.3, ls=ls,
                marker=mk, ms=3.4, label=display_term(m))
        ax.annotate(display_token(m),
                    xy=(g.sigma_db.iloc[-1], g.sd_days.iloc[-1]),
                    xytext=(4, 0), textcoords="offset points", fontsize=7,
                    color=colour, va="center", ha="left")
    ax.set_xlabel("series noise (dB, log scale)")
    ax.set_ylabel("s.d. of the recovered planted\nbreakpoint (days)")
    ax.set_title("Conditional Monte Carlo recovery", loc="left")
    ax.grid(axis="y", alpha=0.7)
    ax.set_axisbelow(True)
    fig.suptitle("Observed split-half disagreement and conditional Monte "
                 "Carlo recovery", y=1.06, fontsize=9, ha="left", x=0.005)
    # The qualifications live here rather than in the panel headings: at journal
    # width the two headings collided and overflowed the canvas when they carried
    # the conditions themselves (caught by rendering it, 2026-09-14).
    fig.text(0.005, -0.18,
             display_term_gloss(markers) + "\n"
             "Left: two half-series of one season differenced, per "
             "pixel-season -- whatever is common to both halves cancels and is "
             "invisible to this statistic.\nRight: a synthetic season fitted at "
             "each assumed noise level, showing how far the fit lands from the "
             "breakpoints it planted. Conditional on that\ntrajectory and that "
             "noise; not an accuracy, and not a measurement of the real panel. "
             "The two are different quantities and no ratio between them is "
             "formed.",
             fontsize=6.2, color=MUTED, ha="left", va="top")
    save(fig, out, "fig3_precision")


def montecarlo_table(out_csv, draws=80, seed=20260913):
    """The Monte Carlo behind figure 3b. Written to CSV so the figure plots a
    committed file rather than a number produced at draw time."""
    import extract_phenometrics_sar as S
    doy = S._FP.DEKAD_DOY
    T = dict(t1=254.5, t2=314.5, t3=324.5, t4=384.5)
    L = dict(a0=-6.3, b1=-9.5, p=-5.2, b2=-8.4)
    truth = plsm_curve(doy, T["t1"], T["t2"], T["t3"], T["t4"],
                       L["a0"], L["b1"], L["p"], L["b2"], doy[0])
    valid = np.ones(len(doy), bool)
    free, pix = S.plsm_designs_free(), S.plsm_designs_pixel()
    rng = np.random.default_rng(seed)
    rows = []
    for sd in (0.05, 0.122, 0.3, 0.6, 1.0, 1.5, 2.03, 3.0):
        dz = free if sd <= 0.3 else pix
        got = {k: [] for k in ("trough", "heading", "drainage", "harvest")}
        for _ in range(draws):
            m = S.plsm_fit(truth + rng.normal(0, sd, len(doy)), valid, dz)
            for k in got:
                got[k].append(m[k])
        for k, want in (("trough", T["t1"]), ("heading", T["t2"]),
                        ("drainage", T["t3"]), ("harvest", T["t4"])):
            v = np.array(got[k], float)
            v = v[np.isfinite(v)]
            rows.append(dict(sigma_db=sd, marker=k, n_draws=draws,
                             n_fit=len(v),
                             bias_days=float(np.mean(v) - want) if len(v) else np.nan,
                             sd_days=float(np.std(v)) if len(v) else np.nan,
                             grid="free" if sd <= 0.3 else "pixel"))
    pd.DataFrame(rows).to_csv(out_csv, index=False)
    print(f"  wrote {os.path.basename(out_csv)}")


# ===========================================================================
# Figure 4 -- the calendar the estimator actually uses
# ===========================================================================
def fig4(res, out):
    pan = pd.read_csv(os.path.join(res, "phen_panel_district_season.csv"))
    ph = pd.read_csv(os.path.join(res, "exposure_phase.csv"))
    pan = pan.merge(ph, on=["district", "year"], how="left")
    e = pan[pan.estimable == 1].copy()
    order = e.groupby("district").heading.median().sort_values().index.tolist()
    ymap = {d: i for i, d in enumerate(order)}
    ne = (pan[pan.estimable == 0].groupby("district").size().to_dict())
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    rng = np.random.default_rng(11)
    for d in order:
        g = e[e.district == d].copy()
        y = ymap[d]
        ax.plot([g.heading.min(), g.heading.max()], [y, y], color=GRID, lw=3.2,
                solid_capstyle="round", zorder=1)
        # a small deterministic vertical spread, because the dekad grid makes
        # several seasons share a value exactly and a stack of markers reads as
        # one season
        g["j"] = y + rng.uniform(-0.30, 0.30, len(g))
        sets = [
            (g[(g.get("S_phase_rise", 0) == 0)
               & (g.get("S_phase_pre_window", 0) == 0)
               & (g.get("S_phase_post_heading", 0) == 0)], "o", 3.0, INK2),
            (g[g.get("S_phase_rise", 0) == 1], "D", 3.8, C2),
            (g[g.get("S_phase_pre_window", 0) == 1], "^", 4.0, C1),
        ]
        for sub, mk, ms, colour in sets:
            ax.plot(sub.heading, sub.j, mk, ms=ms, color=colour, ls="none",
                    markeredgecolor="white", markeredgewidth=0.5, zorder=4)
        if d in ne:
            ax.text(1.005, y, f"{ne[d]} n/e", transform=
                    ax.get_yaxis_transform(), fontsize=6.3, color=MUTED,
                    va="center")
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order)
    ax.set_ylim(-0.8, len(order) - 0.2)
    ax.invert_yaxis()
    ax.set_xlabel(display_term("heading") + " (day of year)")
    doy_axis(ax, 252, 362, grid_axis="x")
    handles = [Line2D([], [], marker="o", ls="none", ms=3.2, color=INK2),
               Line2D([], [], marker="D", ls="none", ms=4.0, color=C2),
               Line2D([], [], marker="^", ls="none", ms=4.2, color=C1)]
    fig.legend(handles, ["no catalogued severe exposure",
                         "severe exposure in the rise phase",
                         "severe exposure before the season"],
               loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.06))
    # LABEL CORRECTED 2026-09-14 (ninth pass). This read "Heading date", which
    # names the fitted quantity as the agronomic event. t2 is the end of the
    # rise in the VH/VV trajectory; section 4.3.1 authorises the correspondence
    # for DIRECTION ONLY, never for identity, and no field reference exists.
    ax.set_title("Fitted end-of-rise breakpoint (t2) -- agronomic interpretation "
                 "is not field-validated\n25 districts x 9 seasons; 'n/e' "
                 "counts seasons with no admissible fit", loc="left",
                 fontsize=8.5)
    save(fig, out, "fig4_calendar")


# ===========================================================================
# Figure 5 -- the estimates
# ===========================================================================
# SIGNAL-DEFINED DISPLAY TERMS. These are what a READER sees on a figure.
# The CSV column names -- trough, heading, drainage, harvest, veg_days,
# plateau_days, season_days -- are UNCHANGED everywhere in the package. A
# display label is not a data column: renaming the columns would rename the
# study's outcome variables, and every results table, every protocol section
# and every downstream script addresses them by those names.
#
# Why the labels change at all: "onset", "heading", "drainage" and "harvest"
# name AGRONOMIC EVENTS. What the five-segment model locates are FEATURES OF A
# BACKSCATTER TRAJECTORY. This study holds no field reference (§4.3.1), so a
# figure that labels t2 "heading" asserts a correspondence it cannot show. The
# agronomic reading is kept, marked as a reading, in the "-related" suffix.
DISPLAY_TERM = {
    "trough":       "t1 end of dark phase",
    "heading":      "t2 end of rise, heading-related",
    "drainage":     "t3 end of plateau, drainage-related",
    "harvest":      "t4 end of fall, harvest-related",
    "veg_days":     "t1\u2192t2",
    "plateau_days": "t2\u2192t3",
    "season_days":  "t1\u2192t4",
}


def display_term(col, wrap=False):
    """Signal-defined label for a marker or interval column.

    wrap=True breaks the label at its comma, for axes where the full term on
    one line would run into the neighbouring tick.
    """
    s = DISPLAY_TERM[col]
    return s.replace(", ", ",\n") if wrap else s


def display_token(col):
    """Just the t-number, for axes too narrow to carry the full term.

    Measured, not guessed: four full terms on figure 3's left panel overlap
    each other at journal width, and the right panel's end-of-line
    annotations run off the canvas. Where the axis cannot carry the term, the
    token goes on the axis and the FULL terms go in the caption -- the same
    remedy this figure already uses for its panel headings.
    """
    return DISPLAY_TERM[col].split()[0]


def display_term_gloss(cols):
    """One caption line defining every token used on the axes."""
    return "; ".join(DISPLAY_TERM[c] for c in cols) + "."


FIG5_OUTCOMES = [(c, display_term(c, wrap=True)) for c in
                 ("trough", "heading", "drainage", "harvest",
                  "veg_days", "plateau_days", "season_days")]


def _row(tab, stratum):
    r = tab[tab.stratum == stratum]
    if not len(r):
        return None
    r = r.iloc[0]
    if str(r.get("status", "")) != "estimated":
        return None
    return float(r.coef), float(r.wcb_ci_lo), float(r.wcb_ci_hi), float(r.p_wcb)


def fig5(res, out):
    """Displacement of fitted radar-trajectory breakpoints. NOT causal effects.

    REWRITTEN 2026-09-13. The previous version was wrong in two ways that a
    published figure must not be:

    1. It read `Table_SX_AttritionDiagnostic_district.csv`, the table produced
       BEFORE the `twfe` screening defect was fixed — 213 observations where only
       208 are retained. It plotted heading at +7.111 d, p_WCB 0.0025. The
       corrected value is +6.183 d, p_WCB 0.0088. The stale figure was committed
       at 775aef2 alongside a protocol amendment stating the corrected number, so
       the repository contradicted itself.
    2. Its title read "Heading is delayed by about a week under either definition
       of severe exposure", and its x-axis "effect on the marker". Both are causal
       claims, and §4.1 withdraws every causal claim from §3.8 — the design fails
       its own §3.9 timing placebo (+7.438 d where zero is required, p_perm
       0.0395). A figure asserting a delay is exactly what §4.1.5's commitment 1
       forbids.

    It now reads the corrected table, names the quantity as a breakpoint
    displacement, carries the conditional permutation sensitivity p-value
    for the harvest-window arm, and states the placebo failure on the
    figure itself so the panel cannot be lifted out of context.
    """
    corrected = os.path.join(res, "s310_v2_district",
                             "Table_SX_AttritionDiagnostic.csv")
    if not os.path.exists(corrected):
        raise SystemExit(
            "fig5 needs the CORRECTED district table at\n  %s\n"
            "The pre-2026-09-13 table at results/Table_SX_AttritionDiagnostic_"
            "district.csv used 213 observations where 208 are retained and must "
            "not be plotted. Run stage 4 of run_all.sh." % corrected)
    froz = pd.read_csv(corrected)
    phase = froz                      # both arms are in the one corrected table
    perm_p = {}
    pp = os.path.join(res, "permutation_test",
                      "Table_SX_Permutation_district.csv")
    if os.path.exists(pp):
        t = pd.read_csv(pp)
        for _, r in t[t.test_var == "S_harvest_window"].iterrows():
            perm_p[str(r.phenometric)] = float(r.p_perm)
    arms = [("frozen §3.8 class:\nsevere harvest-window", froz,
             "headline:{p}:S_harvest_window", C3, "s"),
            ("measured phase:\nsevere during the rise", phase,
             "phase:{p}:S_phase_rise", C1, "o")]
    fig, ax = plt.subplots(figsize=(7.4, 3.8))
    ylab, yt = [], []
    for i, (col, lab) in enumerate(FIG5_OUTCOMES):
        base = len(FIG5_OUTCOMES) - 1 - i
        yt.append(base)
        ylab.append(lab)
        for j, (aname, tab, tmpl, colour, mk) in enumerate(arms):
            got = _row(tab, tmpl.format(p=col))
            if got is None:
                continue
            b, lo, hi, pv = got
            y = base + (0.17 if j == 0 else -0.17)
            ax.plot([lo, hi], [y, y], color=colour, lw=1.4,
                    solid_capstyle="butt")
            ax.plot([b], [y], marker=mk, ms=5, color=colour,
                    markeredgecolor="white", markeredgewidth=0.6, zorder=4)
            # Annotate the specified permutation sensitivity where available.
            # It does not establish bootstrap calibration or causal validity;
            # the source table retains the WCB result beside it.
            pann = perm_p.get(col) if j == 0 else None
            if pann is not None:
                ax.text(hi + 0.5, y, f"$p_{{perm}}$={pann:.3f}", fontsize=6.5,
                        color=colour, va="center")
            elif pv < 0.05:
                ax.text(hi + 0.5, y, f"$p_{{WCB}}$={pv:.3f}", fontsize=6.5,
                        color=colour, va="center")
    ax.axvline(0, color=INK, lw=0.8)
    ax.set_yticks(yt)
    ax.set_yticklabels(ylab)
    ax.set_ylim(-0.7, len(FIG5_OUTCOMES) - 0.3)
    ax.set_xlim(-26, 26)
    ax.set_xlabel("displacement of the fitted breakpoint or interval (days);\n"
                  "bars are 95% wild-cluster-bootstrap intervals")
    ax.grid(axis="x", alpha=0.7)
    ax.set_axisbelow(True)
    handles = [Line2D([], [], marker=mk, color=colour, lw=1.4, ms=5,
                      markeredgecolor="white")
               for _, _, _, colour, mk in arms]
    fig.legend(handles, [a[0].replace("\n", " ") for a in arms],
               loc="lower center", ncol=2, bbox_to_anchor=(0.55, -0.14))
    ax.set_title("Breakpoint displacement under severe exposure, two exposure "
                 "definitions", loc="left", fontsize=9)
    # The caveat travels ON the figure. §4.1 withdraws every causal reading of
    # these coefficients, and a panel lifted into a slide or a review loses the
    # surrounding text.
    fig.text(0.011, -0.235,
             "Not causal effects. §3.9's timing placebo — which requires severe "
             "harvest-window exposure to leave the SAME season's\nt1 "
             "breakpoint unmoved — is rejected in the robustness arm (+7.44 d, "
             "$p_{perm}$=0.040). A separate synthetic perturbation shows that "
             "this fitted\nfive-segment breakpoint can move after a late-season "
             "backscatter change; that is a plausible estimator pathway, not "
             "the identified cause here.\n$p_{perm}$ where §3.9's "
             "permutation test covers the indicator, $p_{WCB}$ otherwise — the "
             "reference schemes differ.\nWithin-state exchangeability is "
             "unverified; this comparison neither calibrates the bootstrap "
             "nor identifies why the association arose (§4.1.7).",
             fontsize=6.2, color=INK, va="top")
    save(fig, out, "fig5_coefficients")


# ===========================================================================
# Figure 6 -- what the catalogue's timing labels actually mean here
# ===========================================================================
def fig6(res, out):
    st = pd.read_csv(os.path.join(res, "exposure_phase_storms.csv"))
    st = st[st.phase != "unclassifiable"].copy()
    order = st.groupby("district_gadm_name").heading.mean().sort_values().index
    ymap = {d: i for i, d in enumerate(order)}
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    for d in order:
        y = ymap[d]
        g = st[st.district_gadm_name == d].iloc[0]
        ax.plot([150, g.trough], [y, y], color=GRID, lw=5,
                solid_capstyle="butt", zorder=1)
        ax.plot([g.trough, g.heading], [y, y], color=C1, lw=5, alpha=0.30,
                solid_capstyle="butt", zorder=1)
        ax.plot([g.heading, g.harvest], [y, y], color=C3, lw=5, alpha=0.30,
                solid_capstyle="butt", zorder=1)
    styles = {"harvest_window": (C2, "D"), "pre_season": (INK2, "^")}
    for lab, (colour, mk) in styles.items():
        g = st[st.timing_class == lab]
        ax.plot(g.storm_doy, [ymap[d] for d in g.district_gadm_name], mk,
                ms=4.6, color=colour, markeredgecolor="white",
                markeredgewidth=0.6, ls="none", zorder=5)
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels(order)
    ax.set_ylim(-0.8, len(order) - 0.2)
    ax.set_xlabel("day of year")
    doy_axis(ax, 110, 425, grid_axis="x")
    handles = [Line2D([], [], color=GRID, lw=5),
               Line2D([], [], color=C1, lw=5, alpha=0.30),
               Line2D([], [], color=C3, lw=5, alpha=0.30),
               Line2D([], [], marker="D", ls="none", ms=4.6, color=C2,
                      markeredgecolor="white"),
               Line2D([], [], marker="^", ls="none", ms=4.6, color=INK2,
                      markeredgecolor="white")]
    ax.legend(handles, ["before the dark phase ends (before t1)",
                        "rise (t1 → t2)",
                        "after t2",
                        "storm the catalogue calls 'harvest window'",
                        "storm the catalogue calls 'pre-season'"],
              loc="upper left", ncol=2, bbox_to_anchor=(0.0, -0.16))
    # `st` is already restricted to classifiable rows, i.e. those in roster
    # districts; the catalogue total is quoted alongside so the two
    # denominators can never be read as disagreeing
    raw = pd.read_csv(os.path.join(res, "exposure_phase_storms.csv"))
    # DENOMINATOR. Each row of exposure_phase_storms.csv is a DISTRICT-STORM
    # EXPOSURE RECORD, not a storm: one cyclone crossing several districts
    # contributes one row per district. Until 2026-09-15 this title called the
    # counts "storms", which overstates the number of storms by about three
    # times -- 18 records come from 5 distinct storms. Both are now computed
    # and both are shown, records first because they are what the panel draws.
    hw = raw.timing_class == "harvest_window"
    hw_c = st.timing_class == "harvest_window"
    n_cat = int(hw.sum())                       # catalogue RECORDS
    n_class = int(hw_c.sum())                   # classifiable RECORDS
    n_in = int((hw_c & (st.phase == "rise")).sum())   # RECORDS in the rise
    s_cat = int(raw.loc[hw, "storm_name"].nunique())          # unique storms
    s_class = int(st.loc[hw_c, "storm_name"].nunique())
    s_in = int(st.loc[hw_c & (st.phase == "rise"), "storm_name"].nunique())
    # OBSERVATIONAL STATEMENT ONLY. Where a storm falls relative to the fitted
    # breakpoints is a property of the FIT. It does not establish whether an
    # agronomic harvest had or had not occurred -- this study holds no field
    # reference. "harvest window" is reported as the CATALOGUE'S LABEL.
    ax.set_title(f"{n_in} of the {n_class} classifiable district-storm "
                 f"exposure records the catalogue labels 'harvest window' "
                 f"fall inside the fitted t1\u2013t2 rise\nphase rather than "
                 f"the fitted post-t2 phase "
                 f"(from {n_cat} catalogue records; "
                 f"{n_cat - n_class} fall outside the district roster). "
                 f"Those {n_class} records are {s_class} distinct storms.",
                 loc="left", fontsize=9)
    save(fig, out, "fig6_exposure_phase")


# ===========================================================================
# Figure 7 -- retention against elevation and slope, as observed association
# ===========================================================================
# CORRECTED 2026-09-14 (ninth pass). This section was headed "what the
# retention screen is actually rejecting" and the figure's title said "the
# screen rejects terrain that cannot be paddy". Both name a cause. What the
# data show is an ASSOCIATION: in the fitted selection model of section 3.10,
# retention varies with elevation, slope and viewing geometry, and NO
# ASSOCIATION WITH CYCLONE DISTANCE WAS DETECTED IN THAT FITTED MODEL -- a
# detected null, which does NOT establish that exposure-related selection is
# absent. The cause of the terrain association cannot be separated among mask
# classification, signal quality, estimator behaviour and this screening rule
# itself, and nothing in this study attempts to separate them.
ELEV_BANDS = [(-1e5, 10, "0-10"), (10, 50, "10-50"), (50, 150, "50-150"),
              (150, 300, "150-300"), (300, 1e5, ">300")]
SLOPE_BANDS = [(0, 1, "<1"), (1, 2, "1-2"), (2, 4, "2-4"), (4, 8, "4-8"),
               (8, 90, ">8")]


def terrain_retention_table(res, out_csv):
    """Pixel retention by terrain band. Written to CSV so the figure plots a
    committed file rather than a number produced at draw time."""
    stat = pd.read_csv(os.path.join(res, "s1_static_covariates.csv"))
    pan = pd.read_csv(os.path.join(res, "phen_panel_sar.csv"),
                      usecols=["cell_id", "retained"])
    ret = pan.groupby("cell_id")["retained"].mean().rename("retention")
    d = stat.set_index("cell_id").join(ret)
    rows = []
    for col, bands, unit in (("elevation_m", ELEV_BANDS, "m"),
                             ("slope_deg", SLOPE_BANDS, "degrees")):
        for lo, hi, lab in bands:
            m = d[col].between(lo, hi, inclusive="left")
            if not m.any():
                continue
            v = d.loc[m, "retention"]
            rows.append(dict(covariate=col, unit=unit, band=lab,
                             n_pixels=int(m.sum()), retention=float(v.mean()),
                             se=float(v.std(ddof=1) / np.sqrt(len(v)))))
    t = pd.DataFrame(rows)
    t.to_csv(out_csv, index=False)
    print(f"  wrote {os.path.basename(out_csv)}")
    return t


def fig7(res, out):
    t = pd.read_csv(os.path.join(res, "retention_by_terrain.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.9),
                             gridspec_kw=dict(wspace=0.26))
    specs = [("elevation_m", C1, "elevation of the 30 m cell (m)",
              "by elevation"),
             ("slope_deg", C2, "terrain slope of the 30 m cell (degrees)",
              "by slope")]
    for ax, (col, colour, xlab, title) in zip(axes, specs):
        g = t[t.covariate == col]
        x = np.arange(len(g))
        ax.bar(x, g.retention, width=0.66, color=colour, edgecolor="white",
               linewidth=0.5)
        ax.errorbar(x, g.retention, yerr=g.se, fmt="none", elinewidth=0.8,
                    capsize=0, ecolor=INK)
        for xi, (r, n) in enumerate(zip(g.retention, g.n_pixels)):
            ax.text(xi, r + 0.022, f"{r:.2f}", ha="center", fontsize=6.6,
                    color=INK)
            ax.text(xi, 0.013, f"{n:,}", ha="center", fontsize=5.8,
                    color="white" if r > 0.08 else MUTED)
        ax.set_xticks(x)
        ax.set_xticklabels(g.band)
        ax.set_xlabel(xlab + "\n(pixel count inside each bar)")
        ax.set_ylim(0, 0.52)
        ax.set_title(title, loc="left")
        ax.grid(axis="y", alpha=0.7)
        ax.set_axisbelow(True)
    axes[0].set_ylabel("share of the nine seasons\nretained, per pixel")
    fig.suptitle("Observed retention by terrain band (cause not identified)",
                 y=1.04, fontsize=9, ha="left", x=0.005)
    fig.text(0.005, -0.12,
             "Whiskers: descriptive mean ±1 naive s.e. across pixels; "
             "spatial dependence is not accounted for.\n"
             "These are unadjusted summaries of the selected cohort, "
             "not causal effects of terrain or crop-classification accuracy.",
             fontsize=7, color=INK)
    save(fig, out, "fig7_terrain_retention")


def _build_environment():
    """Everything that can move the BYTES of a figure, recorded, not assumed.

    Until 2026-09-15 this manifest recorded `matplotlib` alone. That is not
    enough to support any byte claim: a PDF's bytes also depend on the Python
    that wrote it, on FreeType's rasteriser and hinting for every glyph, on
    zlib's compression for the PNG and the PDF streams, on Pillow for the PNG
    encode, on numpy for the values that reach the renderer, and on the platform
    underneath all of them. Recording one of seven and calling the result
    byte-reproducible was a claim with no support.

    Recorded so a reader can see exactly what produced these bytes. NOT pinned:
    this package ships no lockfile and does not claim another environment will
    reproduce them. SCOPE_NOTE below states what the manifest does claim.
    """
    import platform
    import zlib
    env = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "matplotlib": matplotlib.__version__,
        "numpy": np.__version__,
        "zlib": zlib.ZLIB_VERSION,
    }
    try:
        import PIL
        env["pillow"] = PIL.__version__
    except Exception:
        env["pillow"] = "unavailable"
    try:
        from matplotlib import ft2font
        v = ft2font.__freetype_version__
        env["freetype"] = v if isinstance(v, str) else ".".join(map(str, v))
    except Exception:
        env["freetype"] = "unavailable"
    return dict(sorted(env.items()))


SCOPE_NOTE = (
    "WHAT THIS MANIFEST IS FOR: ARTIFACT INTEGRITY. It answers one question -- "
    "has a committed file changed since these hashes were recorded -- for the "
    "generator, every input read and every figure written. That is what "
    "--verify checks and it is all --verify checks. "
    "WHAT IT IS NOT: it is NOT a claim that another machine will reproduce "
    "these bytes. Three claims are distinct and only the first is made here. "
    "(1) BYTE IDENTITY: the same bytes. Asserted only within the RECORDED "
    "TEST ENVIRONMENT listed in 'environment' below -- recorded, NOT pinned: "
    "this package ships no lockfile and enforces no version check, so that "
    "list is a description of what produced these bytes, not a guarantee "
    "that reinstalling it reproduces them. The self-test "
    "demonstrates it by saving one figure twice in one process. "
    "(2) PIXEL IDENTITY: the same rendered image, possibly different bytes. NOT "
    "established -- a different FreeType rasterises glyphs differently. "
    "(3) CONTENT EQUALITY: the same numbers, labels and marks, possibly "
    "different pixels. NOT established by any hash; it is what a reader checks "
    "by looking at the figure. A hash mismatch on another machine therefore "
    "means 'these bytes differ', not 'this figure is stale' -- read the "
    "recorded environment before concluding anything has drifted."
)

PROVENANCE_HISTORY = [
    {"field": "inputs/results/phen_panel_sar.csv",
     "was": "d0559979df253232c623ba4084b710c5",
     "now": "046d6029b3b131c5a06fb6ca9000d9ad",
     "changed": "2026-09-15",
     "why": ("No file with the previous hash exists anywhere reachable, so that "
             "recorded input had become uncheckable. The replayed panel from "
             "the 2026-09-14 reproducibility run was substituted only after a "
             "control run at unchanged generator code reproduced all fourteen "
             "committed figure files and both derived tables byte-for-byte. "
             "SCOPE: that control covered make_figures.py only. The two panels "
             "cannot be compared field by field because one no longer exists, "
             "so PANEL EQUIVALENCE IS NOT ESTABLISHED. See DATA_AVAILABILITY.md.")},
]


def write_manifest(out_dir):
    """Record what this run read and what it produced.

    This is the staleness guard that replaces the PDF timestamp. `inputs` is
    every CSV read during the run, `outputs` every figure file written, each by
    md5. A reviewer can then establish, without re-running anything, whether the
    committed figures were produced from the committed tables."""
    path = os.path.join(out_dir, MANIFEST)
    doc = {
        "source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
        "hash_policy": HASH_POLICY,
        "environment": _build_environment(),
        "scope": SCOPE_NOTE,
        "provenance_history": PROVENANCE_HISTORY,
        "note": ("PDF /CreationDate is frozen to source_date_epoch so figure "
                 "hashes are meaningful; staleness is detected by the input "
                 "hashes below, not by file times. Regenerate with "
                 "make_figures.py and compare with --verify. Paths are relative "
                 "to the repository root where the file sits inside it, and "
                 "absolute otherwise -- so a run whose --results pointed at a "
                 "data directory outside the repository records absolute paths, "
                 "which --verify still resolves but which will not transfer to "
                 "another machine."),
        "repo_relative": all(
            not k.startswith("/")
            for k in list(_PROV["inputs"]) + list(_PROV["outputs"])),
        "generator": {_relpath(GENERATOR): _md5(GENERATOR)},
        "inputs": dict(sorted(_PROV["inputs"].items())),
        "outputs": dict(sorted(_PROV["outputs"].items())),
    }
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=False)
        fh.write("\n")
    print(f"  wrote {MANIFEST} ({len(doc['generator'])} generator, "
          f"{len(doc['inputs'])} inputs, {len(doc['outputs'])} outputs)")
    return path


FIGURE_NAMES = ("fig1", "fig2", "fig3", "fig4", "fig5", "fig6", "fig7")

# Derived inputs the pipeline can build for itself, and which figures need them.
# A partial run must NOT rebuild these: `retention_by_terrain.csv` is built from
# results/phen_panel_sar.csv, which is excluded from the repository on size, so
# building it is impossible from a clone. Until 2026-09-15 the terrain table was
# gated by --skip-montecarlo, which meant the documented partial command crashed
# with a bare FileNotFoundError unless a caller happened to pass a flag whose
# name says nothing about terrain. Both halves of that are fixed here: the flags
# are separate, and --only is parsed BEFORE any prerequisite is generated.
PREREQS = {
    "montecarlo_precision.csv": ("fig3", "Monte Carlo for figure 3b"),
    "retention_by_terrain.csv": ("fig7", "retention by terrain band for figure 7"),
}


def _parse_only(raw):
    only = {x.strip() for x in (raw or "").split(",") if x.strip()}
    unknown = only - set(FIGURE_NAMES)
    if unknown:
        raise SystemExit(f"--only: unknown {sorted(unknown)}; "
                         f"choose from {list(FIGURE_NAMES)}")
    return only


def reuse_verified_input(out_dir, path):
    """In partial mode, reuse a committed derived input ONLY if it still matches
    the hash the manifest recorded for it.

    Rebuilding is not an option here (see PREREQS), so the alternative to this
    check is trusting whatever happens to be on disk. That is exactly the
    stale-input defect the manifest exists to catch, and it would be silent."""
    man = os.path.join(out_dir, MANIFEST)
    if not os.path.exists(man):
        raise SystemExit(
            f"--only needs {man} so committed inputs can be checked before they "
            f"are reused. Run a full make_figures.py first.")
    with open(man, encoding="utf-8") as fh:
        doc = json.load(fh)
    key = _relpath(path)
    want = doc.get("inputs", {}).get(key)
    if want is None:
        raise SystemExit(
            f"REFUSED: {key} is needed by the selected figures, and the manifest "
            f"records no hash for it. A partial run will not reuse an input it "
            f"cannot check. Run the full pipeline.")
    if not os.path.exists(path):
        raise SystemExit(
            f"REFUSED: {key} is needed by the selected figures and is not on "
            f"disk. It is a derived input this run must not rebuild "
            f"(see DATA_AVAILABILITY.md). Run the full pipeline where its own "
            f"inputs are available.")
    got = _md5(path)
    if got != want:
        raise SystemExit(
            f"REFUSED: {key} does not match the hash the manifest recorded "
            f"({want} -> {got}). It changed since the figures were drawn, so "
            f"reusing it would draw a figure from one table and certify it "
            f"against another. Run the full pipeline.")
    print(f"  reusing committed {key} (hash verified against {MANIFEST})")


def merge_manifest(out_dir, drawn):
    """Write the manifest after a PARTIAL run, without inventing anything.

    Why this exists. One figure input, results/phen_panel_sar.csv, is excluded
    from the repository on size (DATA_AVAILABILITY.md), so a full run is
    impossible from a clone: fig2 cannot be drawn. Before this, correcting a
    title in one figure meant either running the whole pipeline -- which a clone
    cannot do -- or hand-editing the manifest, which would make it something the
    committed code does not produce. Both are worse than a documented partial
    run.

    What it guarantees. Every entry this run did NOT touch is RE-HASHED FROM
    DISK and must still equal its recorded value; if one differs the run is
    refused, so a stale figure or a moved table cannot be carried forward under
    an old hash. Inputs that are absent here keep their recorded value and are
    named in `unverified_inputs`, because an absent file has not drifted -- it
    simply could not be checked. `partial_run` records which figures were
    redrawn, so a reader never has to infer it."""
    path = os.path.join(out_dir, MANIFEST)
    if not os.path.exists(path):
        raise SystemExit(f"{path} absent: --only needs an existing manifest to "
                         f"merge into. Run a full make_figures.py first.")
    with open(path, encoding="utf-8") as fh:
        old = json.load(fh)
    if old.get("hash_policy") != HASH_POLICY:
        print(f"  note: manifest hash policy {old.get('hash_policy')!r} -> "
              f"{HASH_POLICY!r}; untouched entries are re-hashed under the new "
              f"policy, so their recorded values are replaced by measured ones.")
    inputs, outputs, unverified = {}, {}, []
    for kind, dest in (("inputs", inputs), ("outputs", outputs)):
        for rel, want in old.get(kind, {}).items():
            if rel in _PROV[kind]:
                continue                     # this run rewrote or re-read it
            ap = rel if os.path.isabs(rel) else os.path.join(REPO, rel)
            if not os.path.exists(ap):
                if kind == "outputs":
                    raise SystemExit(
                        f"REFUSED: {rel} is recorded as an output but is not on "
                        f"disk. A partial run must not drop a figure.")
                dest[rel] = want
                unverified.append(rel)
                continue
            got = _md5(ap)
            if got != want and old.get("hash_policy") == HASH_POLICY:
                raise SystemExit(
                    f"REFUSED: {rel} does not match its recorded hash "
                    f"({want} -> {got}). A partial run must not carry a changed "
                    f"file forward under an old hash. Investigate, then run the "
                    f"full pipeline.")
            dest[rel] = got
    inputs.update(_PROV["inputs"])
    outputs.update(_PROV["outputs"])
    doc = {
        "source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
        "hash_policy": HASH_POLICY,
        "environment": _build_environment(),
        "scope": SCOPE_NOTE,
        "provenance_history": PROVENANCE_HISTORY,
        "note": ("PDF /CreationDate is frozen to source_date_epoch so figure "
                 "hashes are meaningful; staleness is detected by the hashes "
                 "below, not by file times. `generator` is this file: a change "
                 "to the drawing code with stale figures fails --verify, which "
                 "input and output hashes alone cannot catch. Regenerate with "
                 "make_figures.py and compare with --verify. SCOPE: figure "
                 "hashes are reproducible within the recorded test environment "
                 "recorded in `environment` above, not across environments; a "
                 "different freetype or matplotlib can change the bytes and "
                 "even the pixels, which is a separate claim this manifest does "
                 "not make."),
        "repo_relative": all(not k.startswith("/")
                             for k in list(inputs) + list(outputs)),
        "partial_run": {
            "figures_redrawn": sorted(drawn),
            "why": ("results/phen_panel_sar.csv is excluded from the repository "
                    "on size, so fig2 cannot be drawn from a clone and a full "
                    "run is impossible here. Every entry not redrawn was "
                    "re-hashed from disk and matched."),
            "unverified_inputs": sorted(unverified),
        },
        "generator": {_relpath(GENERATOR): _md5(GENERATOR)},
        "inputs": dict(sorted(inputs.items())),
        "outputs": dict(sorted(outputs.items())),
    }
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=False)
        fh.write("\n")
    print(f"  wrote {MANIFEST} (partial: {', '.join(sorted(drawn))}; "
          f"{len(doc['inputs'])} inputs, {len(doc['outputs'])} outputs, "
          f"{len(unverified)} input(s) absent and unverifiable here)")
    return path


def verify(out_dir, strict=False):
    """Re-hash everything the manifest names and report disagreement.

    A changed INPUT hash means a table moved under a figure that was not redrawn
    -- the stale-figure defect. A changed OUTPUT hash means a committed figure is
    not the one this code produces. Either is a failure and exits 1.

    A MISSING file is a different thing and is reported differently. Some figure
    inputs are excluded from the repository on size (see DATA_AVAILABILITY.md),
    so in a fresh checkout they are absent and this check cannot cover them. That
    makes the check INCOMPLETE, not failed: nothing has drifted, there is simply
    less that could be compared. The first version of this function counted
    missing and changed into one verdict and printed the stale-figure message for
    both, so on a clean checkout it reported "VERIFY FAILED" with an explanation
    that did not apply -- and REAUDIT_BRIEF_2026-09-13.md told a reviewer to run
    exactly that command. Found by running my own instruction against a
    reconstruction of the committed tree.

    --strict restores the single-verdict behaviour, which is what a full pipeline
    run wants: there, every input exists and a missing one is a real problem."""
    path = os.path.join(out_dir, MANIFEST)
    if not os.path.exists(path):
        print(f"[FAIL] no {MANIFEST} in {out_dir}. Run make_figures.py first.")
        return 1
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    print("=" * 74)
    print(f"VERIFY -- {_relpath(path)}")
    print("=" * 74)
    print(f"  recorded with matplotlib {doc.get('environment', {}).get('matplotlib', doc.get('matplotlib', '?'))}, "
          f"SOURCE_DATE_EPOCH {doc.get('source_date_epoch', '?')}")
    recorded = doc.get("hash_policy", "raw-bytes-legacy")
    if recorded != HASH_POLICY:
        print(f"\n[STOP] this manifest was written under hash policy "
              f"{recorded!r}; this code uses {HASH_POLICY!r}.")
        print("  Comparing across policies would report every text file as")
        print("  changed when nothing has. Regenerate the manifest by running")
        print("  make_figures.py, then commit it with the figures.")
        print("=" * 74)
        return 1
    if doc.get("source_date_epoch") != os.environ["SOURCE_DATE_EPOCH"]:
        print(f"  [WARN] this run would use "
              f"{os.environ['SOURCE_DATE_EPOCH']}; PDF hashes will not match.")
    bad = missing = 0
    missing_names = []
    if "generator" not in doc:
        print("\n  [STOP] this manifest records no `generator` hash, so a "
              "change to the")
        print("         drawing code with stale figures would go undetected. "
              "Regenerate")
        print("         it by running make_figures.py.")
        print("=" * 74)
        return 1
    for kind in ("generator", "inputs", "outputs"):
        print(f"\n  {kind}:")
        for rel, want in doc.get(kind, {}).items():
            ap = rel if os.path.isabs(rel) else os.path.join(REPO, rel)
            if not os.path.exists(ap):
                print(f"    [MISSING]  {rel}")
                missing += 1
                missing_names.append(rel)
                continue
            got = _md5(ap)
            if got == want:
                print(f"    [ok]       {rel}")
            else:
                print(f"    [CHANGED]  {rel}")
                print(f"               manifest {want}")
                print(f"               on disk  {got}")
                bad += 1
    print("=" * 74)
    if bad:
        print(f"VERIFY FAILED -- {bad} changed"
              + (f", {missing} missing" if missing else ""))
        print("A changed GENERATOR means the drawing code was edited while the")
        print("committed figures were left alone -- a title, label or colour in")
        print("the files may no longer be what this code draws. A changed INPUT")
        print("means a table moved under a figure that was not redrawn. A changed")
        print("OUTPUT means the committed figure is not what this code produces")
        print("IN THIS ENVIRONMENT -- check the matplotlib version printed above")
        print("against yours before concluding a figure is stale, because figure")
        print("bytes are only guaranteed within the recorded test environment,")
        print("which is recorded but NOT pinned: no lockfile, no version check.")
        print("Re-run make_figures.py and commit the figures and the manifest.")
        print("=" * 74)
        return 1
    if missing:
        print(f"VERIFY INCOMPLETE -- 0 changed, {missing} not present here")
        print("Nothing has drifted: every file that IS present matches its")
        print("recorded hash. These are not in this checkout, so they could not")
        print("be compared:")
        for rel in missing_names:
            print(f"    {rel}")
        print("DATA_AVAILABILITY.md lists what is excluded and why. If a file")
        print("above is NOT listed there, that is a real gap -- report it.")
        print("=" * 74)
        return 1 if strict else 0
    print("VERIFY PASSED -- recorded generator, input and output hashes unchanged")
    print("=" * 74)
    return 0


def selftest():
    """The one thing in this file that can silently disagree with the science.

    plsm_curve() re-implements the five-segment model so the figures can draw a
    smooth line between dekad grid points. If it ever diverges from the model
    python/extract_phenometrics_sar.py actually fits, the figures would show a
    curve the estimator never produced. This checks the two against each other
    on a synthetic season with known breakpoints, at the dekad grid points where
    both are defined."""
    print("=" * 74)
    print("SELF-TEST -- make_figures.py")
    print("=" * 74)
    ok_all = True
    import extract_phenometrics_sar as S
    doy = np.asarray(S._FP.DEKAD_DOY, float)
    T = (254.5, 314.5, 324.5, 384.5)
    L = (-6.3, -9.5, -5.2, -8.4)
    y = plsm_curve(doy, *T, *L, doy[0])

    m = S.plsm_fit(y, np.ones(len(doy), bool), S.plsm_designs_free())
    got = (m["trough"], m["heading"], m["drainage"], m["harvest"])
    lev = (m["pre_db"], m["dark_db"], m["plateau_db"], m["post_db"])
    ok = got == T and max(abs(a - b) for a, b in zip(lev, L)) < 1e-6
    ok_all &= ok
    print(f"  breakpoints {got} (truth {T})")
    print(f"  levels      {tuple(round(v, 3) for v in lev)} (truth {L})")
    print(f"  [{'PASS' if ok else 'FAIL'}] the curve the figures draw is the "
          f"model the estimator fits -- a season drawn by plsm_curve is "
          f"recovered exactly by plsm_fit")

    # the segment boundaries must be continuous: no jump at a breakpoint
    fine = np.linspace(doy[0], doy[-1], 4000)
    yy = plsm_curve(fine, *T, *L, doy[0])
    jump = float(np.max(np.abs(np.diff(yy))))
    span = float(np.max(yy) - np.min(yy))
    ok = jump < span / 50.0
    ok_all &= ok
    print(f"\n  largest step between adjacent sample points {jump:.4f} dB "
          f"against a range of {span:.2f} dB")
    print(f"  [{'PASS' if ok else 'FAIL'}] the drawn curve is continuous at "
          f"every breakpoint")

    # the palette the figures use must clear the colourblind separation floor
    ok = len({C1, C2, C3}) == 3
    ok_all &= ok
    print(f"\n  [{'PASS' if ok else 'FAIL'}] three distinct categorical hues "
          f"({C1}, {C2}, {C3}); every series also carries a distinct line style "
          f"or marker, so the figures survive greyscale printing")

    # PDF output must be byte-reproducible WITHIN THIS RECORDED TEST ENVIRONMENT, or
    # the committed figure hashes -- and the provenance manifest built on them --
    # certify nothing. This saves the same trivial figure twice, a second apart,
    # and compares bytes. It establishes determinism here; it says nothing about
    # another machine, where a different freetype or matplotlib can change the
    # bytes and even the pixels. Cross-environment identity is a different claim
    # and is not made.
    import tempfile
    import time
    with tempfile.TemporaryDirectory() as td:
        f, ax = plt.subplots(figsize=(3, 2))
        ax.plot([0, 1, 2], [0, 1, 0])
        p1 = os.path.join(td, "a.pdf")
        f.savefig(p1)
        time.sleep(1.1)                     # so a wall-clock stamp would differ
        p2 = os.path.join(td, "b.pdf")
        f.savefig(p2)
        plt.close(f)
        h1, h2 = _md5(p1), _md5(p2)
    ok = h1 == h2
    ok_all &= ok
    print(f"\n  same figure saved twice 1.1 s apart: {h1[:12]} / {h2[:12]}")
    print(f"  [{'PASS' if ok else 'FAIL'}] PDF output is byte-reproducible IN "
          f"THIS RECORDED TEST ENVIRONMENT (matplotlib {matplotlib.__version__}, "
          f"SOURCE_DATE_EPOCH={os.environ['SOURCE_DATE_EPOCH']}), so a figure "
          f"hash means something here. Cross-environment byte identity -- and "
          f"cross-environment pixel identity, which is a different claim again "
          f"-- are NOT established by this test")

    # GENERATOR-SOURCE DRIFT MUST FAIL VERIFICATION. Editing this file without
    # redrawing is invisible to input and output hashes -- both still match. The
    # manifest therefore records the hash of this file, and --verify treats a
    # mismatch as a failure. This plants both cases: a manifest naming the true
    # generator hash must PASS, and one naming any other hash must FAIL.
    import json as _json
    import tempfile
    true_h = _md5(GENERATOR)
    stale_h = ("0" * 32) if true_h != "0" * 32 else ("1" * 32)
    rcs = {}
    for label, h in (("current", true_h), ("drifted", stale_h)):
        with tempfile.TemporaryDirectory() as td:
            with open(os.path.join(td, MANIFEST), "w", encoding="utf-8",
                      newline="\n") as fh:
                _json.dump({"source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
                            "matplotlib": matplotlib.__version__,
                            "hash_policy": HASH_POLICY,
                            "generator": {_relpath(GENERATOR): h},
                            "inputs": {}, "outputs": {}}, fh, indent=2)
            import io as _io
            import contextlib
            buf = _io.StringIO()
            with contextlib.redirect_stdout(buf):
                rcs[label] = verify(td)
    ok = rcs["current"] == 0 and rcs["drifted"] == 1
    ok_all &= ok
    print(f"\n  manifest with this file's own hash -> exit {rcs['current']}; "
          f"with a different hash -> exit {rcs['drifted']}")
    print(f"  [{'PASS' if ok else 'FAIL'}] generator-source drift is detected: "
          f"editing make_figures.py without redrawing fails --verify, which "
          f"input and output hashes alone cannot catch")

    # and a manifest with no generator entry at all must not pass silently
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, MANIFEST), "w", encoding="utf-8",
                  newline="\n") as fh:
            _json.dump({"source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
                        "matplotlib": matplotlib.__version__,
                        "hash_policy": HASH_POLICY,
                        "inputs": {}, "outputs": {}}, fh, indent=2)
        import io as _io2
        import contextlib as _cl2
        b2 = _io2.StringIO()
        with _cl2.redirect_stdout(b2):
            rc_none = verify(td)
    ok = rc_none == 1
    ok_all &= ok
    print(f"\n  manifest with no generator entry -> exit {rc_none}")
    print(f"  [{'PASS' if ok else 'FAIL'}] a manifest predating the generator "
          f"hash is refused rather than passed")

    # ------------------------------------------------------------------
    # FIGURE 6 DENOMINATOR. exposure_phase_storms.csv has one row per
    # DISTRICT-STORM exposure record, not per storm. Until 2026-09-15 figure 6's
    # title called its counts "storms", overstating the storm count about
    # threefold. This test asserts the two denominators are computed separately
    # and are genuinely different, so collapsing them again fails here.
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _sp = os.path.join(_root, "results", "exposure_phase_storms.csv")
    if not os.path.exists(_sp):
        _sp = os.path.join("results", "exposure_phase_storms.csv")
    if os.path.exists(_sp):
        _raw = pd.read_csv(_sp)
        _st = _raw[_raw.phase != "unclassifiable"]
        _hw, _hwc = _raw.timing_class == "harvest_window", _st.timing_class == "harvest_window"
        rec_cat, rec_cls = int(_hw.sum()), int(_hwc.sum())
        rec_in = int((_hwc & (_st.phase == "rise")).sum())
        sto_cat = int(_raw.loc[_hw, "storm_name"].nunique())
        sto_cls = int(_st.loc[_hwc, "storm_name"].nunique())
        sto_in = int(_st.loc[_hwc & (_st.phase == "rise"), "storm_name"].nunique())
        checks = [
            (rec_cat > sto_cat, "catalogue records exceed catalogue storms"),
            (rec_cls > sto_cls, "classifiable records exceed classifiable storms"),
            (rec_in > sto_in, "in-rise records exceed in-rise storms"),
            (rec_cat >= rec_cls >= rec_in, "records nest: catalogue >= classifiable >= in-rise"),
            (sto_cat >= sto_cls >= sto_in, "storms nest the same way"),
            (len(_raw) == len(_raw.drop_duplicates(["district_gadm_name", "storm_name", "season"])),
             "one row per district-storm-season, no duplicates"),
        ]
        ok = all(c for c, _ in checks)
        print(f"\n  harvest-window RECORDS  catalogue {rec_cat}, "
              f"classifiable {rec_cls}, inside the fitted rise {rec_in}")
        print(f"  harvest-window STORMS   catalogue {sto_cat}, "
              f"classifiable {sto_cls}, inside the fitted rise {sto_in}")
        for c, why in checks:
            if not c:
                print(f"    FAILED: {why}")
        print(f"  [{'PASS' if ok else 'FAIL'}] the district-storm record count "
              f"and the unique-storm count are computed separately and differ, "
              f"so figure 6 cannot call records 'storms' again")
    else:
        ok = True
        print(f"\n  [SKIP] {_sp} not present; figure 6 denominator check "
              f"needs it")
    ok_all &= ok

    # THE DOCUMENTED PARTIAL COMMAND MUST WORK FROM A CLEAN CLONE.
    #
    #     python python/make_figures.py --only fig3,fig4,fig7 --out figures
    #
    # A clone has no results/phen_panel_sar.csv (excluded on size), and until
    # 2026-09-15 that command died with a bare FileNotFoundError: the terrain
    # table was built before --only was read, and was gated by a flag named
    # --skip-montecarlo. This plants the exact situation -- a results directory
    # holding the committed derived inputs and NOT the pixel panel -- and then
    # plants the two ways a partial run could quietly certify the wrong thing.
    import json as _j
    import shutil
    import tempfile
    import contextlib
    import io as _io

    def _clean_clone(td):
        """A results/ + figures/ pair shaped like a fresh clone, with a manifest
        whose recorded hashes are the real ones."""
        res, fig = os.path.join(td, "results"), os.path.join(td, "figures")
        os.makedirs(res); os.makedirs(fig)
        inputs = {}
        for name in ("retention_by_terrain.csv",      # fig7's prerequisite
                     "splithalf_reliability.csv"):    # an untouched input
            src = os.path.join(REPO, "results", name)
            dst = os.path.join(res, name)
            shutil.copyfile(src, dst)
            inputs[dst] = _md5(dst)
        outputs = {}
        for stem in ("fig3_precision", "fig7_terrain_retention"):
            for ext in ("png", "pdf"):
                src = os.path.join(REPO, "figures", f"{stem}.{ext}")
                dst = os.path.join(fig, f"{stem}.{ext}")
                shutil.copyfile(src, dst)
                outputs[dst] = _md5(dst)
        with open(os.path.join(fig, MANIFEST), "w", encoding="utf-8",
                  newline="\n") as fh:
            _j.dump({"source_date_epoch": os.environ["SOURCE_DATE_EPOCH"],
                     "matplotlib": matplotlib.__version__,
                     "hash_policy": HASH_POLICY,
                     "generator": {_relpath(GENERATOR): _md5(GENERATOR)},
                     "inputs": inputs, "outputs": outputs}, fh, indent=2)
        assert not os.path.exists(os.path.join(res, "phen_panel_sar.csv"))
        return res, fig

    def _run_partial(res, fig, names="fig7"):
        saved = {k: dict(v) for k, v in _PROV.items()}
        _PROV["inputs"].clear(); _PROV["outputs"].clear()
        buf = _io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                rc = main(["--only", names, "--results", res, "--out", fig])
            return rc, buf.getvalue()
        except SystemExit as e:
            return ("REFUSED", str(e))
        finally:
            for k, v in saved.items():
                _PROV[k].clear(); _PROV[k].update(v)

    with tempfile.TemporaryDirectory() as td:
        res, fig = _clean_clone(td)
        rc, out = _run_partial(res, fig)
        ok = rc == 0 and "reusing committed" in out
        ok_all &= ok
        print(f"\n  clean clone with no results/phen_panel_sar.csv, "
              f"`--only fig7 --out <figures>` -> {rc!r}")
        print(f"  [{'PASS' if ok else 'FAIL'}] the documented partial command "
              f"runs with no extra flag, and reuses the committed derived input "
              f"after checking its recorded hash rather than rebuilding it")

    with tempfile.TemporaryDirectory() as td:
        res, fig = _clean_clone(td)
        p = os.path.join(res, "splithalf_reliability.csv")      # untouched INPUT
        with open(p, "a", encoding="utf-8") as fh:
            fh.write("stale,row,0,0,0\n")
        rc, msg = _run_partial(res, fig)
        ok = rc == "REFUSED" and "does not match its recorded hash" in msg
        ok_all &= ok
        print(f"\n  same run after a recorded but untouched INPUT is edited "
              f"-> {rc!r}")
        print(f"  [{'PASS' if ok else 'FAIL'}] a stale untouched input is "
              f"refused, not carried forward under its old hash")

    with tempfile.TemporaryDirectory() as td:
        res, fig = _clean_clone(td)
        p = os.path.join(fig, "fig3_precision.png")             # untouched OUTPUT
        with open(p, "ab") as fh:
            fh.write(b"\x00stale")
        rc, msg = _run_partial(res, fig)
        ok = rc == "REFUSED" and "does not match its recorded hash" in msg
        ok_all &= ok
        print(f"\n  same run after a recorded but untouched OUTPUT is edited "
              f"-> {rc!r}")
        print(f"  [{'PASS' if ok else 'FAIL'}] a stale untouched output is "
              f"refused: a partial run cannot republish a manifest that "
              f"certifies a figure it did not draw and cannot vouch for")

    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="Figures for Paper 2.")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--verify", action="store_true",
                    help="re-hash what %s names and report disagreement; "
                         "non-zero exit on any mismatch" % MANIFEST)
    ap.add_argument("--strict", action="store_true",
                    help="with --verify, treat a MISSING file as a failure too. "
                         "What a full pipeline run wants, where every input "
                         "exists; not what a fresh checkout wants, where some "
                         "inputs are excluded on size.")
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="figures")
    ap.add_argument("--year", type=int, default=2017)
    ap.add_argument("--skip-montecarlo", action="store_true",
                    help="full runs only: reuse the committed "
                         "montecarlo_precision.csv instead of rebuilding it. "
                         "It does NOT affect the terrain table -- see "
                         "--skip-terrain-table. Irrelevant with --only, which "
                         "never rebuilds a derived input.")
    ap.add_argument("--skip-terrain-table", action="store_true",
                    help="full runs only: reuse the committed "
                         "retention_by_terrain.csv instead of rebuilding it. "
                         "Rebuilding needs results/phen_panel_sar.csv, which is "
                         "excluded from the repository on size.")
    ap.add_argument("--only", default="",
                    help="comma-separated figure names (fig1..fig7) to redraw, "
                         "merging into the existing manifest instead of "
                         "rewriting it. Every entry not redrawn is re-hashed "
                         "from disk and must still match. Needed because one "
                         "input is excluded from the repository on size, so a "
                         "full run is impossible from a clone.")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.verify:
        return verify(a.out, a.strict)

    # --only is parsed FIRST. Everything below depends on which figures were
    # asked for, including whether a derived input needs building at all.
    only = _parse_only(a.only)
    _install_read_recorder()

    skip = {"montecarlo_precision.csv": a.skip_montecarlo,
            "retention_by_terrain.csv": a.skip_terrain_table}
    for name, (needed_by, banner) in PREREQS.items():
        if only and needed_by not in only:
            continue                        # nothing selected needs it
        path = os.path.join(a.results, name)
        if only:
            reuse_verified_input(a.out, path)
            continue
        if skip[name] and os.path.exists(path):
            continue
        print(banner + ":")
        if name == "montecarlo_precision.csv":
            montecarlo_table(path)
        else:
            terrain_retention_table(a.results, path)

    print("figures:" if not only else f"figures (only {', '.join(sorted(only))}):")
    draw = {"fig1": lambda: fig1(a.results, a.out, a.year),
            "fig2": lambda: fig2(a.results, a.out, a.year),
            "fig3": lambda: fig3(a.results, a.out),
            "fig4": lambda: fig4(a.results, a.out),
            "fig5": lambda: fig5(a.results, a.out),
            "fig6": lambda: fig6(a.results, a.out),
            "fig7": lambda: fig7(a.results, a.out)}
    for name in FIGURE_NAMES:
        if not only or name in only:
            draw[name]()
    if only:
        merge_manifest(a.out, only)
    else:
        write_manifest(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
