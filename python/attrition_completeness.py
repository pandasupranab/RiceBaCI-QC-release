#!/usr/bin/env python3
"""§3.10 attrition-completeness gate. FAILS CLOSED.

WHAT "FAILS CLOSED" MEANS HERE, and why it is written in capitals. Three
successive versions of this module passed a table that was broken, each time
because an unanticipated shape fell through to a default that meant "fine". The
rule now is the opposite: anything not explicitly recognised as valid is a
FAILURE. An unknown status value fails. A blank reason on a not-estimable row
fails. A missing bootstrap count fails. A key present in the partial table but
not the final one fails. A shared row whose fields disagree between the two
tables fails. An alias check that was requested but could not run fails -- it
does not skip and report success.

WHAT EACH EARLIER VERSION GOT WRONG (kept, because the pattern is the point):

  2026-09-15 (a): claimed in its docstring to check the exact key set and
      instead counted rows. A valid key replaced by a unique FAKE key at
      unchanged row count returned PASS.
  2026-09-15 (b): fixed the key set, then (i) synthesised `not_estimable` from
      an absent row, (ii) accepted any status string, (iii) let
      `--verify-aliases` report SKIP and still exit 0 when the panel was
      missing, (iv) mapped `cyclone:<NAME>` to the `balanced:*:*:<NAME>` rows as
      its composition comparator. That last one is a SCIENTIFIC error, not a
      plumbing one: those rows carry a coefficient on the CLASS variable
      (S_pre_season / S_harvest_window) with the cyclone selecting only the
      two-season window. They are not a per-cyclone estimand and cannot
      compare with a per-cyclone diagnostic.

THE ESTIMAND MAP IS THE SCIENTIFIC CORE OF THIS MODULE. Three answers are
possible for any comparator and they are NOT interchangeable:

  available:<e>/<n> estimated  every named row exists; exact counts, never a
                               bare "available"
  not_estimable:<n>/<n>        every named row EXISTS and each records
                               not_estimable with a nonblank reason
  NOT_RUN                      a named row is ABSENT: the estimator was never
                               run. A completeness FAILURE, never a result.
  NOT_DEFINED                  the protocol defines no comparator of this kind,
                               so none was ever supposed to exist. Not a
                               failure, and NOT the same as not_estimable.

    python python/attrition_completeness.py --level district \
        --dir results/s310_v2_district --out results/s310_v2_district \
        --verify-aliases
"""
import argparse
import csv
import io
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lf_output  # noqa: F401  -- pins to_csv to LF on every platform.

TABLE = "Table_SX_AttritionDiagnostic.csv"
PARTIAL = "Table_SX_AttritionDiagnostic.partial.csv"
EVENT_STUDY = "Table_SX_EventStudy.csv"
OUT = "Table_SX_AttritionTriggers.csv"

TRIGGER_ALPHA = 0.05
DIAG_PREFIXES = ("class", "cyclone", "phase_attrition")
REQUIRED_BOOT = 9999

# FAIL CLOSED: only these status values are recognised. Anything else fails.
VALID_STATUS = {"estimated", "not_estimable"}

# Every estimated diagnostic row is produced by the same wild-cluster-bootstrap
# routine.  Requiredness must follow from the declared estimator/status, never
# from whether a value happens to be present in the CSV.
DIAGNOSTIC_ESTIMATED_NUMERIC = (
    "coef", "se", "t", "p_cluster", "p_wcb", "wcb_ci_lo", "wcb_ci_hi",
)
DIAGNOSTIC_POSITIVE_INTEGER = (
    "n_obs", "n_clusters", "n_treated_clusters", "n_score_clusters",
)

EVENT_REQUIRED_FIELDS = {
    "outcome", "breakpoint", "cyclone", "t_c", "n_footprint", "n_control",
    "n_flagged", "adjacent_exposure_flag", "predicted_sign", "term", "status",
    "coef", "se", "t", "p_wcb", "wcb_ci_lo", "wcb_ci_hi",
    "degenerate_ci", "reason", "n_obs", "n_clusters", "n_treated_clusters",
    "underpowered", "p_cluster", "n_boot_requested", "n_boot_ok",
    "estimator", "design_id", "sample_sha256",
}

PHENOMETRICS = ("trough", "heading", "drainage", "harvest",
                "veg_days", "plateau_days", "season_days",
                "rise_db", "fall_db", "plateau_db", "fill_days")
CLASS_VARS = ("S_pre_season", "S_harvest_window")
PHASE_VARS = ("S_phase_pre_window", "S_phase_rise", "S_phase_post_heading")
ESTIMABLE_CYCLONES = ("TITLI", "FANI", "BULBUL", "AMPHAN", "YAAS", "REMAL")

NOT_DEFINED = "NOT_DEFINED"
NOT_RUN = "NOT_RUN"

DESIGN_ALIASES = {
    frozenset(("class:pre_season", "phase_attrition:S_phase_pre_window")): {
        "vectors": ("S_pre_season", "S_phase_pre_window"),
        "verified": "elementwise identical on 225/225 district-seasons",
    },
}


def expected_balanced_keys():
    return {f"balanced:{p}:{v}:{c}"
            for p in PHENOMETRICS for v in CLASS_VARS
            for c in ESTIMABLE_CYCLONES}


def expected_keys(level):
    k = set()
    k |= {f"class:{v[2:]}" for v in CLASS_VARS}
    k |= {f"cyclone:{c}" for c in ESTIMABLE_CYCLONES}
    k |= {f"phase_attrition:{v}" for v in PHASE_VARS}
    k |= {f"headline:{p}:{v}" for p in PHENOMETRICS for v in CLASS_VARS}
    k |= {f"pretrend:{p}:Slead_{v[2:]}" for p in PHENOMETRICS for v in CLASS_VARS}
    k |= {f"phase:{p}:{v}" for p in PHENOMETRICS for v in PHASE_VARS}
    k |= {f"phase_pretrend:{p}:Slead_{v[2:]}" for p in PHENOMETRICS
          for v in PHASE_VARS}
    k |= expected_balanced_keys()
    if level == "pixel":
        k |= {f"ipsw:{p}:{v}" for p in PHENOMETRICS for v in CLASS_VARS}
        k |= {f"phase_ipsw:{p}:{v}" for p in PHENOMETRICS for v in PHASE_VARS}
    return k


def _rows(path):
    return _table(path)[1]


def _table(path):
    with io.open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader.fieldnames or ()), list(reader)


def _f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _finite(x):
    v = _f(x)
    return v if v is not None and math.isfinite(v) else None


def _exact_int(x):
    """Return an integer only when the input is finite and exactly integral."""
    v = _finite(x)
    if v is None or not v.is_integer():
        return None
    return int(v)


def _valid_p(x, *, bootstrap=False, n_boot=REQUIRED_BOOT):
    v = _finite(x)
    if v is None or v < 0.0 or v > 1.0:
        return None
    # The implementation uses the plus-one correction, so zero is impossible.
    if bootstrap and v < 1.0 / (n_boot + 1.0):
        return None
    return v


def holm(ps):
    idx = sorted(range(len(ps)), key=lambda i: ps[i])
    m, out, run = len(ps), [0.0] * len(ps), 0.0
    for r, i in enumerate(idx):
        run = max(run, (m - r) * ps[i])
        out[i] = min(run, 1.0)
    return out


def bh(ps):
    idx = sorted(range(len(ps)), key=lambda i: ps[i])
    m, out, run = len(ps), [0.0] * len(ps), 1.0
    for r in range(m - 1, -1, -1):
        i = idx[r]
        run = min(run, m / (r + 1) * ps[i])
        out[i] = min(run, 1.0)
    return out


def alias_of(stratum):
    for pair in DESIGN_ALIASES:
        if stratum in pair:
            return sorted(pair - {stratum})
    return []


def needs_boot(row):
    """Does this row carry a WCB estimate, so a bootstrap count is required?"""
    return (row.get("status") or "").strip() == "estimated"


def row_problems(level, where, rows):
    """FAIL-CLOSED per-row validation. Applied to BOTH tables."""
    probs, seen = [], {}
    for r in rows:
        s = (r.get("stratum") or "").strip()
        if not s:
            probs.append("%s [%-7s]: BLANK stratum key" % (level, where))
        if s in seen:
            probs.append("%s/%s: DUPLICATE stratum key in %s" % (level, s, where))
        seen[s] = r
        st = (r.get("status") or "").strip()
        if st not in VALID_STATUS:
            probs.append("%s/%s [%s]: status %r is not one of %s"
                         % (level, s, where, st, sorted(VALID_STATUS)))
            continue
        if st == "not_estimable" and not (r.get("reason") or "").strip():
            probs.append("%s/%s [%s]: not_estimable with a BLANK reason -- a "
                         "not-estimable record must say why"
                         % (level, s, where))
        if st == "estimated":
            for fld in DIAGNOSTIC_ESTIMATED_NUMERIC:
                if _finite(r.get(fld)) is None:
                    probs.append("%s/%s [%s]: estimated row has non-finite or "
                                 "missing %s=%r" %
                                 (level, s, where, fld, r.get(fld)))
            for fld in DIAGNOSTIC_POSITIVE_INTEGER:
                val = _exact_int(r.get(fld))
                if val is None or val <= 0:
                    probs.append("%s/%s [%s]: estimated row requires positive "
                                 "integer %s, got %r" %
                                 (level, s, where, fld, r.get(fld)))
            if (r.get("estimator") or "").strip() != "attrition_diagnostic":
                val = _exact_int(r.get("n_pixels"))
                if val is None or val <= 0:
                    probs.append("%s/%s [%s]: estimator %r requires positive "
                                 "integer n_pixels, got %r" %
                                 (level, s, where, r.get("estimator"),
                                  r.get("n_pixels")))
            if _valid_p(r.get("p_cluster")) is None:
                probs.append("%s/%s [%s]: invalid p_cluster=%r" %
                             (level, s, where, r.get("p_cluster")))
            if _valid_p(r.get("p_wcb"), bootstrap=True) is None:
                probs.append("%s/%s [%s]: invalid plus-one p_wcb=%r" %
                             (level, s, where, r.get("p_wcb")))

        if needs_boot(r):
            req = _exact_int(r.get("n_boot_requested"))
            ok = _exact_int(r.get("n_boot_ok"))
            if req is None or ok is None:
                probs.append("%s/%s [%s]: WCB estimate with a missing "
                             "or non-integer n_boot_requested/n_boot_ok (%r/%r)"
                             % (level, s, where, r.get("n_boot_requested"),
                                r.get("n_boot_ok")))
            elif req != REQUIRED_BOOT or ok != REQUIRED_BOOT:
                probs.append("%s/%s [%s]: n_boot_requested=%s n_boot_ok=%s; "
                             "Protocol §3.8 declares %d at both levels"
                             % (level, s, where, r.get("n_boot_requested"),
                                r.get("n_boot_ok"), REQUIRED_BOOT))
    return probs, seen


def _event_design():
    """Read the expected event cells from the executable estimator design."""
    try:
        import event_study as ev
    except Exception as exc:
        return None, ["cannot import event_study.py to define the required "
                      "event roster: %s" % exc]
    years = dict(ev.ESTIMABLE)
    cells = {(cyclone, outcome, term)
             for cyclone in tuple(years) + ("POOLED",)
             for outcome in ev.OUTCOME_MAP
             for term in ("k0", "k1")}
    return dict(module=ev, years=years, cells=cells), []


def event_study_problems(es, fields):
    """Validate every declared event-study cell, not only surviving rows."""
    probs = []
    design, dprobs = _event_design()
    probs += dprobs
    if es is None:
        probs.append("Table_SX_EventStudy.csv is absent")
        return probs, {}
    missing_fields = sorted(EVENT_REQUIRED_FIELDS - set(fields or ()))
    if missing_fields:
        probs.append("Table_SX_EventStudy.csv is missing required field(s): %s"
                     % ",".join(missing_fields))
    if design is None:
        return probs, {}

    ev = design["module"]
    by, duplicate = {}, []
    for r in es:
        key = tuple((r.get(k) or "").strip()
                    for k in ("cyclone", "outcome", "term"))
        if key in by:
            duplicate.append(key)
        by[key] = r
    for key in duplicate:
        probs.append("event-study DUPLICATE cell: %s/%s/%s" % key)
    got, exp = set(by), design["cells"]
    for key in sorted(exp - got):
        probs.append("event-study REQUIRED cell missing: %s/%s/%s" % key)
    for key in sorted(got - exp):
        probs.append("event-study UNEXPECTED cell present: %s/%s/%s" % key)

    # These fields define the stack/sample and must agree for both terms and all
    # three outcomes for a named cyclone.  A label swap therefore cannot pass by
    # merely preserving the row count.
    design_fields = ("t_c", "n_footprint", "n_control", "n_flagged",
                     "adjacent_exposure_flag", "n_obs", "n_clusters",
                     "n_treated_clusters", "sample_sha256")
    signature = {}
    for key in sorted(exp & got):
        cyclone, outcome, term = key
        r = by[key]
        tag = "%s/%s/%s" % key
        expected_year = -1 if cyclone == "POOLED" else design["years"][cyclone]
        if _exact_int(r.get("t_c")) != expected_year:
            probs.append("event-study %s has t_c=%r; executable design requires %d"
                         % (tag, r.get("t_c"), expected_year))
        if (r.get("breakpoint") or "").strip() != ev.OUTCOME_MAP[outcome]:
            probs.append("event-study %s breakpoint=%r; expected %r" %
                         (tag, r.get("breakpoint"), ev.OUTCOME_MAP[outcome]))
        expected_sign = "+" if cyclone == "POOLED" else ev.PREDICTED[cyclone][outcome]
        if (r.get("predicted_sign") or "").strip() != expected_sign:
            probs.append("event-study %s predicted_sign=%r; expected %r" %
                         (tag, r.get("predicted_sign"), expected_sign))
        if (r.get("estimator") or "").strip() != ev.EVENT_ESTIMATOR:
            probs.append("event-study %s estimator=%r; expected %r" %
                         (tag, r.get("estimator"), ev.EVENT_ESTIMATOR))
        if (r.get("design_id") or "").strip() != ev.EVENT_DESIGN_ID:
            probs.append("event-study %s design_id does not match the executable design"
                         % tag)
        sample_hash = (r.get("sample_sha256") or "").strip().lower()
        if len(sample_hash) != 64 or any(c not in "0123456789abcdef" for c in sample_hash):
            probs.append("event-study %s invalid sample_sha256=%r" %
                         (tag, r.get("sample_sha256")))

        st = (r.get("status") or "").strip()
        if st not in VALID_STATUS:
            probs.append("event-study %s status=%r is invalid" % (tag, st))
            continue
        if st == "not_estimable" and not (r.get("reason") or "").strip():
            probs.append("event-study %s not_estimable with a BLANK reason" % tag)

        for fld in ("n_obs", "n_clusters", "n_treated_clusters"):
            val = _exact_int(r.get(fld))
            if val is None or val <= 0:
                probs.append("event-study %s requires positive integer %s, got %r"
                             % (tag, fld, r.get(fld)))
        for fld in ("underpowered", "degenerate_ci"):
            if _exact_int(r.get(fld)) not in (0, 1):
                probs.append("event-study %s requires binary %s, got %r"
                             % (tag, fld, r.get(fld)))
        if cyclone != "POOLED":
            for fld in ("n_footprint", "n_control"):
                val = _exact_int(r.get(fld))
                if val is None or val <= 0:
                    probs.append("event-study %s requires positive integer %s, got %r"
                                 % (tag, fld, r.get(fld)))
            if _exact_int(r.get("n_flagged")) is None or _exact_int(r.get("n_flagged")) < 0:
                probs.append("event-study %s requires nonnegative integer n_flagged, got %r"
                             % (tag, r.get("n_flagged")))
            if _exact_int(r.get("adjacent_exposure_flag")) not in (0, 1):
                probs.append("event-study %s requires binary adjacent_exposure_flag, got %r"
                             % (tag, r.get("adjacent_exposure_flag")))

        req, ok = _exact_int(r.get("n_boot_requested")), _exact_int(r.get("n_boot_ok"))
        if req != REQUIRED_BOOT:
            probs.append("event-study %s n_boot_requested=%r; expected %d" %
                         (tag, r.get("n_boot_requested"), REQUIRED_BOOT))
        if ok is None or ok < 0 or ok > REQUIRED_BOOT:
            probs.append("event-study %s invalid n_boot_ok=%r" %
                         (tag, r.get("n_boot_ok")))

        if st == "estimated":
            for fld in ("coef", "se", "t", "wcb_ci_lo", "wcb_ci_hi"):
                if _finite(r.get(fld)) is None:
                    probs.append("event-study %s estimated row has non-finite %s=%r"
                                 % (tag, fld, r.get(fld)))
            if _finite(r.get("se")) is not None and _finite(r.get("se")) <= 0:
                probs.append("event-study %s estimated row has nonpositive se=%r"
                             % (tag, r.get("se")))
            if _valid_p(r.get("p_cluster")) is None:
                probs.append("event-study %s invalid p_cluster=%r" %
                             (tag, r.get("p_cluster")))
            if _valid_p(r.get("p_wcb"), bootstrap=True) is None:
                probs.append("event-study %s invalid plus-one p_wcb=%r" %
                             (tag, r.get("p_wcb")))
            if ok != REQUIRED_BOOT:
                probs.append("event-study %s estimated row has n_boot_ok=%r; expected %d"
                             % (tag, r.get("n_boot_ok"), REQUIRED_BOOT))

        sig = tuple((r.get(f) or "").strip() for f in design_fields)
        if cyclone in signature and signature[cyclone] != sig:
            probs.append("event-study %s changes the declared stack/sample identity "
                         "within cyclone %s" % (tag, cyclone))
        signature.setdefault(cyclone, sig)
    return probs, by


def compare_tables(level, final, partial):
    """Every shared row must agree field by field. Any difference fails."""
    probs = []
    only_partial = sorted(set(partial) - set(final))
    if only_partial:
        probs.append("%s: %d key(s) present in the PARTIAL table but not the "
                     "final one -- a resumed run would carry rows the final "
                     "table does not contain: %s"
                     % (level, len(only_partial), ";".join(only_partial[:6])))
    only_final = sorted(set(final) - set(partial))
    if only_final:
        probs.append("%s: %d key(s) in the final table are absent from the "
                     "partial one, so a resumed run would not rebuild them: %s"
                     % (level, len(only_final), ";".join(only_final[:6])))
    ndiff = 0
    for s in sorted(set(final) & set(partial)):
        a, b = final[s], partial[s]
        for fld in sorted(set(a) | set(b)):
            va = (a.get(fld) or "").strip()
            vb = (b.get(fld) or "").strip()
            if va == vb:
                continue
            fa, fb = _f(va), _f(vb)
            if fa is not None and fb is not None and fa == fb:
                continue
            ndiff += 1
            if ndiff <= 6:
                probs.append("%s/%s: field %r differs between the final and "
                             "partial tables (%r vs %r)"
                             % (level, s, fld, va, vb))
    if ndiff > 6:
        probs.append("%s: %d field differences in total between the final and "
                     "partial tables" % (level, ndiff))
    return probs


def block_status(keys, by):
    if keys is NOT_DEFINED:
        return NOT_DEFINED, "the protocol defines no comparator of this kind here"
    keys = sorted(keys)
    if not keys:
        return NOT_DEFINED, "no comparator keys named"
    missing = [k for k in keys if k not in by]
    if missing:
        return NOT_RUN, ("%d of %d comparator rows absent (estimator not run): %s"
                         % (len(missing), len(keys), ";".join(missing[:4])))
    est, ne, reasons = [], [], []
    for k in keys:
        st = (by[k].get("status") or "").strip()
        if st == "estimated":
            est.append(k)
        elif st == "not_estimable":
            ne.append(k)
            r = (by[k].get("reason") or "").strip()
            if r and r not in reasons:
                reasons.append(r)
        else:
            return "INVALID_STATUS", "%s carries status %r" % (k, st)
    if not est:
        return ("not_estimable:%d/%d" % (len(ne), len(keys)),
                "all not estimable; reasons: " + " | ".join(reasons[:3]))
    detail = "%d estimated, %d not estimable" % (len(est), len(ne))
    if reasons:
        detail += "; reasons: " + " | ".join(reasons[:3])
    return "available:%d/%d estimated" % (len(est), len(keys)), detail


def event_study_rows(es, cyclone):
    """Rows of Table_SX_EventStudy.csv for one cyclone, if that file exists."""
    if es is None:
        return None
    return [r for r in es if (r.get("cyclone") or "").strip() == cyclone]


def comparators(level, prefix, key, by, es):
    """§3.10's declared comparators, per diagnostic type.

    class    -> class-level headline (unbalanced) and class-level IPSW. The
                POOLED composition estimate is NOT_DEFINED: item 3c fixes the
                balanced restriction per cyclone and specifies no pooled form.
    cyclone  -> the per-cyclone EVENT STUDY in Table_SX_EventStudy.csv. Its
                COMPOSITION-RESTRICTED counterpart is NOT_DEFINED, because no
                such arm exists anywhere in this package.

                The `balanced:<phen>:<class var>:<cyclone>` rows are NOT this
                comparator and must not be used as one. Their coefficient is on
                the CLASS variable; the cyclone selects only the two-season
                window. Different estimand, so not comparable with a per-cyclone
                retention diagnostic. Carried in their own column as a
                descriptive sensitivity.
    phase    -> phase unbalanced and phase IPSW. Composition NOT_DEFINED: no
                balanced arm is declared for the measured-phase design.
    """
    if prefix == "class":
        v = "S_" + key
        return {
            "unbalanced": {f"headline:{p}:{v}" for p in PHENOMETRICS},
            "ipsw": ({f"ipsw:{p}:{v}" for p in PHENOMETRICS}
                     if level == "pixel" else NOT_DEFINED),
            "composition": NOT_DEFINED,
            "descriptive": {f"balanced:{p}:{v}:{c}" for p in PHENOMETRICS
                            for c in ESTIMABLE_CYCLONES},
        }
    if prefix == "phase_attrition":
        return {
            "unbalanced": {f"phase:{p}:{key}" for p in PHENOMETRICS},
            "ipsw": ({f"phase_ipsw:{p}:{key}" for p in PHENOMETRICS}
                     if level == "pixel" else NOT_DEFINED),
            "composition": NOT_DEFINED,
            "descriptive": NOT_DEFINED,
        }
    return {
        "unbalanced": ("EVENT_STUDY", key),
        "ipsw": NOT_DEFINED,
        "composition": NOT_DEFINED,
        "descriptive": {f"balanced:{p}:{v}:{key}"
                        for p in PHENOMETRICS for v in CLASS_VARS},
    }


def event_block(es, cyclone):
    if es is None:
        return NOT_RUN, ("Table_SX_EventStudy.csv is absent, so the per-cyclone "
                         "event-study comparator could not be read")
    rows = event_study_rows(es, cyclone)
    if not rows:
        return NOT_RUN, "no event-study rows for cyclone %s" % cyclone
    est = [r for r in rows if (r.get("status") or "").strip() == "estimated"]
    ne = [r for r in rows if (r.get("status") or "").strip() == "not_estimable"]
    if len(est) + len(ne) != len(rows):
        return "INVALID_STATUS", "event-study rows for %s carry an unknown status" % cyclone
    if not est:
        return "not_estimable:%d/%d" % (len(ne), len(rows)), "all not estimable"
    d = "%d estimated, %d not estimable" % (len(est), len(ne))
    return "available:%d/%d estimated" % (len(est), len(rows)), d


def classify(trig, unb, ipsw, comp):
    if not trig:
        return "trigger_not_fired:standard_reporting"
    if NOT_RUN in (unb, ipsw, comp) or "INVALID_STATUS" in (unb, ipsw, comp):
        return "INCOMPLETE:comparator_not_run_or_invalid"
    if comp == NOT_DEFINED:
        return ("not_point_identified_under_differential_attrition:"
                "no_same_estimand_composition_comparator_is_defined")
    if comp.startswith("not_estimable"):
        return ("not_point_identified_under_differential_attrition:"
                "composition_comparator_not_estimable")
    return ("not_point_identified_under_differential_attrition:"
            "composition_comparator_available")


def build(level, d, event_path=None):
    final_rows = _rows(os.path.join(d, TABLE))
    probs, by = row_problems(level, "final", final_rows)

    pp = os.path.join(d, PARTIAL)
    if os.path.exists(pp):
        prows = _rows(pp)
        pprob, pby = row_problems(level, "partial", prows)
        probs += pprob
        probs += compare_tables(level, by, pby)
    else:
        probs.append("%s: the partial table is absent; it is written by every "
                     "run and its absence cannot be checked away" % level)

    ad = os.path.abspath(d)
    cands = ([event_path] if event_path else []) + [
        os.path.join(ad, EVENT_STUDY),
        os.path.join(os.path.dirname(ad), EVENT_STUDY),
        os.path.join(os.path.dirname(os.path.dirname(ad)), "results", EVENT_STUDY)]
    esp = next((c for c in cands if c and os.path.exists(c)), None)
    if event_path and not os.path.exists(event_path):
        probs.append("explicit --event-study path is absent: %s" % event_path)
    if esp:
        es_fields, es = _table(esp)
    else:
        es_fields, es = [], None
    eprobs, _ = event_study_problems(es, es_fields)
    probs += eprobs

    exp, got = expected_keys(level), set(by)
    missing, extra = sorted(exp - got), sorted(got - exp)
    if missing:
        probs.append("%s: %d EXPECTED STRATUM KEY(S) MISSING: %s"
                     % (level, len(missing), ";".join(missing[:6])))
    if extra:
        probs.append("%s: %d UNEXPECTED STRATUM KEY(S) PRESENT: %s"
                     % (level, len(extra), ";".join(extra[:6])))

    diags = [r for r in final_rows if r["stratum"].split(":")[0] in DIAG_PREFIXES]

    canon = {r["stratum"]: sorted([r["stratum"]] + alias_of(r["stratum"]))[0]
             for r in diags}
    uniq = sorted(set(canon.values()))
    def safe_p(row):
        p = _valid_p(row.get("p_wcb"), bootstrap=True)
        return 1.0 if p is None else p

    # A missing canonical alias key is already a completeness failure above.  Do
    # not let it turn that controlled failure into a KeyError before the full
    # diagnostic can be printed.  The placeholder p=1 is used only while
    # constructing a report that will exit non-zero.
    pu = [safe_p(by.get(u, {})) for u in uniq]
    hu, bu = holm(pu), bh(pu)
    hmap = {u: hu[i] for i, u in enumerate(uniq)}
    bmap = {u: bu[i] for i, u in enumerate(uniq)}
    pa = [safe_p(r) for r in diags]
    ha, ba = holm(pa), bh(pa)

    out = []
    for i, r in enumerate(diags):
        st = r["stratum"]
        pre, key = st.split(":", 1)
        p = _f(r.get("p_wcb"))
        trig = p is not None and p < TRIGGER_ALPHA
        cmp_ = comparators(level, pre, key, by, es)

        u = cmp_["unbalanced"]
        if isinstance(u, tuple) and u[0] == "EVENT_STUDY":
            unb, unb_d = event_block(es, u[1])
            unb_src = "Table_SX_EventStudy.csv"
        else:
            unb, unb_d = block_status(u, by)
            unb_src = TABLE
        ips, ips_d = block_status(cmp_["ipsw"], by)
        com, com_d = block_status(cmp_["composition"], by)
        des, des_d = block_status(cmp_["descriptive"], by)
        cls = classify(trig, unb, ips, com)

        if trig:
            for nm, v, dd in (("unbalanced", unb, unb_d), ("ipsw", ips, ips_d),
                              ("composition", com, com_d),
                              ("descriptive", des, des_d)):
                if v in (NOT_RUN, "INVALID_STATUS"):
                    probs.append("%s/%s: %s comparator %s -- %s"
                                 % (level, st, nm, v, dd))
            if cls.startswith("INCOMPLETE"):
                probs.append("%s/%s: cannot be classified while a comparator is "
                             "missing or invalid" % (level, st))

        aff = []
        for grp in ("unbalanced", "ipsw", "composition"):
            g = cmp_[grp]
            if isinstance(g, tuple):
                aff.append("EventStudy[cyclone=%s]" % g[1])
            elif g is not NOT_DEFINED:
                aff += sorted(g)

        cu = canon[st]
        out.append(dict(
            level=level, stratum=st, estimator=r.get("estimator", ""),
            n_boot_requested=r.get("n_boot_requested", ""),
            n_boot_ok=r.get("n_boot_ok", ""),
            p_wcb_raw="" if p is None else f"{p:.6g}",
            trigger_fires=int(bool(trig)),
            affected_coefficients=";".join(aff) or NOT_DEFINED,
            unbalanced_status=unb, unbalanced_source=unb_src,
            unbalanced_detail=unb_d,
            ipsw_status=ips, ipsw_detail=ips_d,
            composition_status=com, composition_detail=com_d,
            descriptive_status=des, descriptive_detail=des_d,
            descriptive_note=(
                "The balanced:<phen>:<class var>:<cyclone> rows are a "
                "DESCRIPTIVE SENSITIVITY, not a composition comparator for this "
                "diagnostic. Their coefficient is on the CLASS variable; the "
                "cyclone selects only the two-season window. delta_beta is "
                "RETIRED: it compares a two-season balanced fit with an "
                "all-season pooled headline, changing the time window as well as "
                "the composition, so it identifies neither."),
            reporting_classification=cls,
            p_wcb_holm_distinct=f"{hmap[cu]:.6g}",
            p_wcb_bh_distinct=f"{bmap[cu]:.6g}",
            p_wcb_holm_all_labels=f"{ha[i]:.6g}",
            p_wcb_bh_all_labels=f"{ba[i]:.6g}",
            verified_design_alias=";".join(alias_of(st)) or "",
        ))
    return out, probs, final_rows


def verify_aliases():
    """Re-check the hard-coded alias against the live panel.

    Returns (True, why) or (False, why). NEVER a skip-success: if the check was
    requested and cannot run, that is a FAILURE, because an unverified constant
    is exactly what this function exists to prevent.
    """
    try:
        import numpy as np
        import pandas as pd
    except Exception as exc:
        return False, "cannot import pandas/numpy: %s" % exc
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    pan = os.path.join(root, "results", "phen_panel_district_season_static.csv")
    php = os.path.join(root, "results", "exposure_phase.csv")
    for f in (pan, php):
        if not os.path.exists(f):
            return False, ("%s is not present, so the alias cannot be verified. "
                           "An unverifiable alias is a failure, not a skip."
                           % os.path.relpath(f, root))
    sys.path.insert(0, here)
    try:
        import attrition_diagnostics as A
        p = pd.read_csv(pan)
        exp = pd.read_csv(A._resolve_exposure(
            "district_cyclone_exposure_ibtracs50km.csv"))
        tab = A.build_exposure_table(exp, sorted(p["district"].unique()),
                                     sorted(p["year"].unique()))
        p = p.merge(tab, on=["district", "year"], how="left")
        p = p.merge(pd.read_csv(php), on=["district", "year"], how="left")
    except Exception as exc:
        return False, "alias verification raised: %s" % exc
    for spec in DESIGN_ALIASES.values():
        a, b = spec["vectors"]
        if a not in p.columns or b not in p.columns:
            return False, "column %r or %r absent from the merged panel" % (a, b)
        va = p[a].fillna(0).astype(int).values
        vb = p[b].fillna(0).astype(int).values
        if not np.array_equal(va, vb):
            return False, ("%s and %s differ on %d of %d rows"
                           % (a, b, int((va != vb).sum()), len(va)))
    n = len(p)
    ex = int(p[list(DESIGN_ALIASES.values())[0]["vectors"][0]].fillna(0).sum())
    return True, ("elementwise identical on %d/%d district-seasons "
                  "(%d exposed in each)" % (n, n, ex))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", choices=("pixel", "district"))
    ap.add_argument("--dir")
    ap.add_argument("--out")
    ap.add_argument("--event-study", default=None,
                    help="explicit results/Table_SX_EventStudy.csv path; the "
                         "production runner always supplies it")
    ap.add_argument("--verify-aliases", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.level and a.dir and a.out):
        ap.error("--level, --dir and --out are required unless --selftest")

    rows, problems, raw = build(a.level, a.dir, a.event_study)

    if a.verify_aliases:
        ok, why = verify_aliases()
        print("  alias check: %s -- %s" % ("PASS" if ok else "FAIL", why))
        if not ok:
            problems.append("%s: alias verification was requested and did not "
                            "pass: %s" % (a.level, why))

    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, OUT)
    with lf_output.open_lf(path, "w") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    trig = [r for r in rows if r["trigger_fires"]]
    nal = sum(1 for r in trig if r["verified_design_alias"])
    print(f"\n§3.10 ATTRITION COMPLETENESS -- {a.level}")
    print(f"  strata expected / present  {len(expected_keys(a.level))} / {len(raw)}")
    print(f"  balanced keys              "
          f"{sum(1 for r in raw if r['stratum'].startswith('balanced:'))} "
          f"(expected {len(expected_balanced_keys())}, exact set compared)")
    print(f"  triggered output labels    {len(trig)}")
    print(f"  distinct tested designs    {len(trig) - nal // 2}"
          f"  (one verified alias pair collapses to one design)"
          if nal else f"  distinct tested designs    {len(trig)}")
    print(f"  wrote {path}")
    for r in trig:
        print(f"    {r['stratum']:<36} p {r['p_wcb_raw']:<9} "
              f"unbal {r['unbalanced_status']:<26} "
              f"comp {r['composition_status']:<12} -> "
              f"{r['reporting_classification']}")
    if problems:
        print("\n  COMPLETENESS FAILURES:")
        for p in problems:
            print(f"    - {p}")
        print(f"\n  [FAIL] {len(problems)} completeness problem(s)")
        return 1
    print("\n  [PASS] exact key set; every status recognised; every "
          "not-estimable row carries a reason; every WCB estimate at 9,999; no "
          "duplicate or partial-only keys; final and partial agree field by "
          "field")
    return 0


def selftest():
    import tempfile
    print("=" * 74)
    print("SELF-TEST -- attrition_completeness.py  (fail-closed)")
    print("=" * 74)
    ok_all = True
    hdr = ["stratum", "estimator", "status", "reason", "coef", "se", "t",
           "p_cluster", "p_wcb", "wcb_ci_lo", "wcb_ci_hi", "beta_balanced",
           "delta_beta", "n_obs", "n_pixels", "n_clusters",
           "n_treated_clusters", "n_score_clusters", "n_boot_requested",
           "n_boot_ok"]

    def full_table():
        rows = []

        def add(s, est, **kw):
            r = dict(stratum=s, estimator=est, status="estimated", reason="",
                     coef="1.0", se="0.5", t="2.0", p_cluster="0.04",
                     p_wcb="0.5", wcb_ci_lo="0.1", wcb_ci_hi="1.9",
                     n_obs="100", n_pixels="25", n_clusters="10",
                     n_treated_clusters="5", n_score_clusters="10",
                     n_boot_requested=str(REQUIRED_BOOT),
                     n_boot_ok=str(REQUIRED_BOOT))
            r.update(kw)
            rows.append(r)
        for v in CLASS_VARS:
            add(f"class:{v[2:]}", "attrition_diagnostic",
                p_wcb="0.0397" if v == "S_harvest_window" else "0.3873")
        for c in ESTIMABLE_CYCLONES:
            add(f"cyclone:{c}", "attrition_diagnostic",
                p_wcb="0.004" if c == "FANI" else "0.5")
        for v in PHASE_VARS:
            add(f"phase_attrition:{v}", "attrition_diagnostic", p_wcb="0.3873")
        for p in PHENOMETRICS:
            for v in CLASS_VARS:
                add(f"headline:{p}:{v}", "unbalanced")
                add(f"pretrend:{p}:Slead_{v[2:]}", "pretrend_lead")
                for c in ESTIMABLE_CYCLONES:
                    add(f"balanced:{p}:{v}:{c}", "balanced",
                        beta_balanced="30.16", delta_beta="25.16")
            for v in PHASE_VARS:
                add(f"phase:{p}:{v}", "phase_measured")
                add(f"phase_pretrend:{p}:Slead_{v[2:]}", "phase_pretrend_lead")
        return rows

    def es_table():
        import event_study as ev
        out = []
        years = dict(ev.ESTIMABLE)
        for c in tuple(years) + ("POOLED",):
            for o, bp in ev.OUTCOME_MAP.items():
                for k in ("k0", "k1"):
                    named = c != "POOLED"
                    out.append(dict(
                        outcome=o, breakpoint=bp, cyclone=c,
                        t_c=years[c] if named else -1,
                        n_footprint="5" if named else "",
                        n_control="5" if named else "",
                        n_flagged="0" if named else "",
                        adjacent_exposure_flag="0" if named else "",
                        predicted_sign=(ev.PREDICTED[c][o] if named else "+"),
                        term=k, status="estimated", coef="1", se="1", t="1",
                        p_wcb="0.5", wcb_ci_lo="-1", wcb_ci_hi="3",
                        degenerate_ci="0", reason="", n_obs="30",
                        n_clusters="10", n_treated_clusters="5",
                        underpowered="0", p_cluster="0.3",
                        n_boot_requested=str(REQUIRED_BOOT),
                        n_boot_ok=str(REQUIRED_BOOT),
                        estimator=ev.EVENT_ESTIMATOR,
                        design_id=ev.EVENT_DESIGN_ID,
                        sample_sha256=("a" * 64)))
        return out

    def write(rows, d, es=True, partial=None, event_rows=None):
        for name in (TABLE, PARTIAL):
            src = rows if (name == TABLE or partial is None) else partial
            with lf_output.open_lf(os.path.join(d, name), "w") as fh:
                w = csv.DictWriter(fh, fieldnames=hdr)
                w.writeheader()
                for r in src:
                    w.writerow({k: r.get(k, "") for k in hdr})
        if es:
            erows = es_table() if event_rows is None else event_rows
            with lf_output.open_lf(os.path.join(d, EVENT_STUDY), "w") as fh:
                w = csv.DictWriter(fh, fieldnames=list(erows[0]))
                w.writeheader()
                for r in erows:
                    w.writerow(r)

    def run(rows, partial=None, es=True, event_rows=None):
        with tempfile.TemporaryDirectory() as td:
            write(rows, td, es=es, partial=partial, event_rows=event_rows)
            return build("district", td)

    def case(title, probs, want, shown=2):
        nonlocal ok_all
        ok = any(want.lower() in p.lower() for p in probs)
        ok_all &= ok
        print("\n  %s" % title)
        for p in probs[:shown]:
            print("    %s" % p[:150])
        print("  [%s] nonzero exit: %d problem(s) raised, matching %r"
              % ("PASS" if ok else "FAIL", len(probs), want))
        return ok

    # 0. the clean table passes
    _, probs, _ = run(full_table())
    ok_all &= not probs
    print("\n  a complete, well-formed table")
    print("  [%s] passes with 0 problems (%d raised)"
          % ("PASS" if not probs else "FAIL", len(probs)))

    # 1. unknown status value
    rows = full_table()
    rows[0]["status"] = "ok"
    case("planted status='ok' (not a declared value)", run(rows)[1],
         "is not one of")

    # 2. not_estimable with a blank reason
    rows = full_table()
    for r in rows:
        if r["stratum"] == "balanced:trough:S_pre_season:FANI":
            r.update(status="not_estimable", reason="")
    case("planted not_estimable with a BLANK reason", run(rows)[1],
         "BLANK reason")

    # 3. wrong bootstrap count
    rows = full_table()
    rows[0]["n_boot_requested"] = "999"
    case("planted n_boot_requested=999", run(rows)[1], "declares 9999")

    # 3b. missing bootstrap count on a WCB estimate
    rows = full_table()
    rows[0]["n_boot_ok"] = ""
    case("planted a WCB estimate with a blank n_boot_ok", run(rows)[1],
         "missing or non-integer n_boot_requested")

    # 3c-g. numeric corruptions that formerly suppressed a trigger or passed
    for title, field, value, want in (
        ("blank diagnostic p_wcb", "p_wcb", "", "non-finite or missing p_wcb"),
        ("non-numeric diagnostic coefficient", "coef", "not_a_number",
         "non-finite or missing coef"),
        ("negative diagnostic p-value", "p_cluster", "-0.1", "invalid p_cluster"),
        ("impossible zero plus-one p-value", "p_wcb", "0", "invalid plus-one p_wcb"),
        ("fractional bootstrap count", "n_boot_ok", "9999.9",
         "missing or non-integer"),
    ):
        rows = full_table()
        rows[0][field] = value
        case("planted " + title, run(rows)[1], want)

    # 4. duplicate key
    rows = full_table()
    rows.append(dict(rows[0]))
    case("planted a duplicate stratum key", run(rows)[1], "DUPLICATE")

    # 4a. delete the canonical member of an alias pair.  Older code detected the
    # missing key, then crashed while constructing the multiplicity summary.
    rows = [r for r in full_table() if r["stratum"] != "class:pre_season"]
    case("deleted a canonical alias key", run(rows)[1], "MISSING")

    # 5. partial-only key
    rows = full_table()
    extra = dict(rows[0])
    extra["stratum"] = "balanced:trough:S_pre_season:GHOST"
    case("planted a key present ONLY in the partial table",
         run(rows, partial=rows + [extra])[1], "PARTIAL table but not the final")

    # 6. a shared row that disagrees between the tables
    rows = full_table()
    part = [dict(r) for r in rows]
    part[0]["coef"] = "999.0"
    case("planted a shared row whose coef differs between final and partial",
         run(rows, partial=part)[1], "differs between the final and partial")

    # 7. the FAKE-key sabotage that defeated the first version
    rows = full_table()
    for r in rows:
        if r["stratum"] == "balanced:trough:S_pre_season:FANI":
            r["stratum"] = "balanced:trough:S_pre_season:FAKEZZ"
    part = [dict(r) for r in rows]
    _, probs, raw = run(rows, partial=part)
    nbal = sum(1 for r in raw if r["stratum"].startswith("balanced:"))
    ok = (nbal == 132 and any("MISSING" in p for p in probs)
          and any("UNEXPECTED" in p for p in probs))
    ok_all &= ok
    print("\n  FAKE key at unchanged row count (%d balanced rows)" % nbal)
    for p in probs[:2]:
        print("    %s" % p[:140])
    print("  [%s] nonzero exit: both the missing and the extra key are reported"
          % ("PASS" if ok else "FAIL"))

    # 8. the event-study comparator is absent
    _, probs, _ = run(full_table(), es=False)
    case("removed Table_SX_EventStudy.csv (cyclone comparator unreadable)",
         probs, "event-study")

    # 9. cyclone composition is NOT_DEFINED, and balanced rows are descriptive
    out, _, _ = run(full_table())
    t = {r["stratum"]: r for r in out}["cyclone:FANI"]
    ok = (t["composition_status"] == NOT_DEFINED
          and t["unbalanced_source"] == "Table_SX_EventStudy.csv"
          and t["descriptive_status"].startswith("available:")
          and "not a composition comparator" in t["descriptive_note"])
    ok_all &= ok
    print("\n  cyclone:FANI unbalanced source -> %r" % t["unbalanced_source"])
    print("  cyclone:FANI composition       -> %r" % t["composition_status"])
    print("  cyclone:FANI descriptive       -> %r" % t["descriptive_status"])
    print("  [%s] the cyclone comparator is the EVENT STUDY; the balanced class "
          "rows are descriptive only and composition is NOT_DEFINED"
          % ("PASS" if ok else "FAIL"))

    # 10. alias verification returns failure, never skip-success, when it cannot run
    ok_flag, why = verify_aliases()
    ok = isinstance(ok_flag, bool)
    ok_all &= ok
    print("\n  verify_aliases() -> (%r, %r)" % (ok_flag, why[:70]))
    print("  [%s] returns a boolean, never a skip sentinel: an unverifiable "
          "alias is a FAILURE" % ("PASS" if ok else "FAIL"))

    # 11-21. Event-study roster, values, provenance and bootstrap metadata.
    def event_case(title, mutate, want):
        erows = es_table()
        mutate(erows)
        case(title, run(full_table(), event_rows=erows)[1], want)

    event_case("deleted one required FANI event cell",
               lambda x: x.pop(next(i for i, r in enumerate(x)
                                    if r["cyclone"] == "FANI")),
               "REQUIRED cell missing")

    def duplicate_fani(x):
        x.append(dict(next(r for r in x if r["cyclone"] == "FANI")))
    event_case("duplicated one FANI event cell", duplicate_fani, "DUPLICATE cell")

    def fake_outcome(x):
        next(r for r in x if r["cyclone"] == "FANI")["outcome"] = "FAKE_OUTCOME"
    event_case("relabelled one outcome to FAKE_OUTCOME", fake_outcome,
               "UNEXPECTED cell")

    def blank_coef(x):
        next(r for r in x if r["cyclone"] == "FANI")["coef"] = ""
    event_case("blanked an estimated event coefficient", blank_coef,
               "non-finite coef")

    def zero_sample(x):
        next(r for r in x if r["cyclone"] == "FANI")["n_obs"] = "0"
    event_case("set an event sample size to zero", zero_sample,
               "positive integer n_obs")

    def wrong_year(x):
        next(r for r in x if r["cyclone"] == "FANI")["t_c"] = "2025"
    event_case("changed FANI's event year", wrong_year, "executable design requires")

    def swap_labels(x):
        for r in x:
            if r["cyclone"] == "FANI":
                r["cyclone"] = "TMP"
            elif r["cyclone"] == "BULBUL":
                r["cyclone"] = "FANI"
        for r in x:
            if r["cyclone"] == "TMP":
                r["cyclone"] = "BULBUL"
    event_case("swapped FANI and BULBUL labels without their designs", swap_labels,
               "predicted_sign")

    def class_substitution(x):
        next(r for r in x if r["cyclone"] == "FANI")["estimator"] = "balanced_class"
    event_case("substituted a class-balanced estimator label", class_substitution,
               "estimator=")

    def blank_ne_reason(x):
        for r in x:
            if r["cyclone"] == "FANI":
                r["status"] = "not_estimable"
                r["reason"] = "   "
                r["n_boot_ok"] = "0"
    event_case("made every FANI cell not-estimable with whitespace reasons",
               blank_ne_reason, "BLANK reason")

    def short_bootstrap(x):
        r = next(r for r in x if r["cyclone"] == "FANI")
        r["n_boot_requested"] = "999"
        r["n_boot_ok"] = "999"
    event_case("declared only 999 event-study bootstrap draws", short_bootstrap,
               "n_boot_requested")

    def remove_amphan(x):
        x[:] = [r for r in x if r["cyclone"] != "AMPHAN"]
    event_case("removed the entire non-triggered AMPHAN block", remove_amphan,
               "REQUIRED cell missing")

    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
