#!/usr/bin/env python3
"""Field-by-field comparison of result tables between two trees, with EVERY
reported total derived by this code and reproducible by running it.

WHY THIS IS A COMMITTED MODULE AND NOT A SCRATCH SCRIPT. Three patches in a row
quoted comparison totals in their handoffs -- "0 fields with a different value",
"1,018 last-digit differences", "604" -- that a reviewer could not reproduce,
because the code that produced them was thrown away. An audit on 2026-09-15
said so plainly. A number nobody else can recompute is not evidence.

Run it and you get the totals:

    python python/compare_tables.py --base <parent tree> --cand <candidate tree>
    python python/compare_tables.py --base ... --cand ... --scope final
    python python/compare_tables.py --base ... --cand ... \
        --allow-removed-column beta_balanced --allow-removed-column delta_beta
    python python/compare_tables.py --selftest

EVERY FIELD LANDS IN EXACTLY ONE BUCKET, and the buckets are disjoint and
exhaustive, so the counts always sum to fields_compared:

  same_text        byte-identical text
  same_double      different text, identical IEEE double ('225.0' vs '225')
  lastdigit        different doubles, relative difference < --tol
  material         different doubles, relative difference >= --tol
  newly_populated  blank in base, a value in candidate
  now_blank        a value in base, blank in candidate
  nonnumeric       differing text that is not a pair of numbers

FIELDS ARE SPLIT INTO TWO CLASSES because they answer different questions:

  bootstrap-independent  coef, se, t, p_cluster, counts. These must not move.
  bootstrap-dependent    p_wcb, wcb_ci_lo, wcb_ci_hi, n_boot_ok,
                         n_boot_requested. These MOVE when the replication count
                         changes, and that is a correction rather than a defect.

`--scope final` restricts to the two final tables, which is the scope the
2026-09-15 audit used when it counted 604 last-digit differences.
"""
import argparse
import csv
import io
import os
import sys

BOOT_DEPENDENT = ("p_wcb", "wcb_ci_lo", "wcb_ci_hi", "n_boot_ok",
                  "n_boot_requested")

FINAL_TABLES = ("results/s310_v2_district/Table_SX_AttritionDiagnostic.csv",
                "results/s310_v2_pixel/Table_SX_AttritionDiagnostic.csv")
PARTIAL_TABLES = ("results/s310_v2_district/Table_SX_AttritionDiagnostic.partial.csv",
                  "results/s310_v2_pixel/Table_SX_AttritionDiagnostic.partial.csv")

BUCKETS = ("same_text", "same_double", "lastdigit", "material",
           "newly_populated", "now_blank", "nonnumeric")


def load(path, key="stratum"):
    with io.open(path, encoding="utf-8", newline="") as fh:
        rd = csv.DictReader(fh)
        fields = list(rd.fieldnames or ())
        rows, dup = {}, []
        for r in rd:
            k = r.get(key, "")
            if k in rows:
                dup.append(k)
            rows[k] = r
        return fields, rows, sorted(set(dup))


def classify(a, b, tol):
    """Return (bucket, relative_difference_or_None). Buckets are disjoint."""
    if a == b:
        return "same_text", None
    if a == "" and b != "":
        return "newly_populated", None
    if a != "" and b == "":
        return "now_blank", None
    try:
        fa, fb = float(a), float(b)
    except ValueError:
        return "nonnumeric", None
    if fa == fb:
        return "same_double", None
    rel = abs(fa - fb) / max(abs(fa), abs(fb), 1e-300)
    return ("lastdigit" if rel < tol else "material"), rel


def compare_one(base, cand, tol, allowed_added=(), allowed_removed=()):
    bf, B, bd = load(base)
    cf, C, cd = load(cand)
    issues = []
    if bd:
        issues.append("duplicate key(s) in base: %s" % ";".join(bd[:6]))
    if cd:
        issues.append("duplicate key(s) in candidate: %s" % ";".join(cd[:6]))
    shared = sorted(set(B) & set(C))
    if not shared:
        raise SystemExit("no shared keys between %s and %s" % (base, cand))
    added_fields = sorted(set(cf) - set(bf))
    removed_fields = sorted(set(bf) - set(cf))
    unexplained_added = sorted(set(added_fields) - set(allowed_added))
    unexplained_removed = sorted(set(removed_fields) - set(allowed_removed))
    if unexplained_removed:
        issues.append("candidate removed unexplained column(s): %s" %
                      ",".join(unexplained_removed))
    if unexplained_added:
        issues.append("candidate added unexplained column(s): %s" %
                      ",".join(unexplained_added))
    fields = list(dict.fromkeys(bf + cf))
    indep = [f for f in fields if f not in BOOT_DEPENDENT]
    dep = [f for f in fields if f in BOOT_DEPENDENT]
    res = {}
    for name, fl in (("bootstrap_independent", indep),
                     ("bootstrap_dependent", dep)):
        c = dict.fromkeys(BUCKETS, 0)
        worst, worst_at, examples = 0.0, None, []
        for s in shared:
            for f in fl:
                bucket, rel = classify((B[s].get(f) or "").strip(),
                                       (C[s].get(f) or "").strip(), tol)
                c[bucket] += 1
                if rel is not None and rel > worst:
                    worst, worst_at = rel, (s, f, B[s].get(f), C[s].get(f))
                if bucket == "material" and len(examples) < 5:
                    examples.append((s, f, B[s].get(f), C[s].get(f), rel))
        res[name] = dict(counts=c, n_fields=len(fl), worst=worst,
                         worst_at=worst_at, examples=examples,
                         total=sum(c.values()))
    added_keys = sorted(set(C) - set(B))
    removed_keys = sorted(set(B) - set(C))
    if removed_keys:
        issues.append("candidate removed row key(s): %s" %
                      ";".join(removed_keys[:6]))
    return dict(shared=len(shared), added=added_keys, removed=removed_keys,
                base_fields=bf, candidate_fields=cf,
                added_fields=added_fields, removed_fields=removed_fields,
                duplicate_base=bd, duplicate_candidate=cd,
                issues=issues, blocks=res)


def run(base_root, cand_root, tol, scope, allowed_added=(), allowed_removed=()):
    tabs = FINAL_TABLES + (() if scope == "final" else PARTIAL_TABLES)
    out, grand, issues = [], {}, []
    for rel in tabs:
        pb, pc = os.path.join(base_root, rel), os.path.join(cand_root, rel)
        if not (os.path.exists(pb) and os.path.exists(pc)):
            out.append((rel, None))
            issues.append("required comparison table is not present in both trees: %s" % rel)
            continue
        r = compare_one(pb, pc, tol, allowed_added, allowed_removed)
        out.append((rel, r))
        issues += ["%s: %s" % (rel, x) for x in r["issues"]]
        for name, blk in r["blocks"].items():
            g = grand.setdefault(name, dict.fromkeys(BUCKETS, 0))
            for k, v in blk["counts"].items():
                g[k] += v
    return out, grand, issues


def report(out, grand, tol, scope, issues=(), w=sys.stdout.write):
    w("=" * 78 + "\n")
    w("TABLE COMPARISON -- every total below is produced by this file\n")
    w("  python/compare_tables.py --scope %s --tol %g\n" % (scope, tol))
    w("=" * 78 + "\n\n")
    for rel, r in out:
        w("-" * 78 + "\n%s\n" % rel + "-" * 78 + "\n")
        if r is None:
            w("  not present in both trees\n\n")
            continue
        w("  shared keys %d ; added %d ; removed %d\n"
          % (r["shared"], len(r["added"]), len(r["removed"])))
        if r["added"]:
            allbal = all(k.startswith("balanced:") for k in r["added"])
            w("    added%s: %s%s\n"
              % (" (all balanced:*)" if allbal else "",
                 ";".join(r["added"][:3]),
                 " ..." if len(r["added"]) > 3 else ""))
        if r["removed"]:
            w("    removed: %s\n" % ";".join(r["removed"][:3]))
        w("  columns base/candidate %d/%d ; added %d ; removed %d\n"
          % (len(r["base_fields"]), len(r["candidate_fields"]),
             len(r["added_fields"]), len(r["removed_fields"])))
        if r["added_fields"]:
            w("    added columns: %s\n" % ",".join(r["added_fields"]))
        if r["removed_fields"]:
            w("    removed columns: %s\n" % ",".join(r["removed_fields"]))
        for name, blk in r["blocks"].items():
            c = blk["counts"]
            w("\n  %s  (%d field(s) x %d keys = %d fields)\n"
              % (name.replace("_", "-").upper(), blk["n_fields"], r["shared"],
                 blk["total"]))
            for k in BUCKETS:
                if c[k]:
                    w("    %-18s %6d\n" % (k, c[k]))
            assert sum(c.values()) == blk["total"]
            w("    %-18s %6d  (sum of the buckets above)\n"
              % ("fields_compared", blk["total"]))
            if blk["worst_at"]:
                w("    largest relative difference %.3g at %s / %s : %s -> %s\n"
                  % ((blk["worst"],) + blk["worst_at"]))
            for s, f, a, b, rel in blk["examples"]:
                w("      MATERIAL %s / %s : %s -> %s  (rel %.3g)\n"
                  % (s, f, a, b, rel))
        w("\n")
    w("=" * 78 + "\nTOTALS\n" + "=" * 78 + "\n")
    for name, g in grand.items():
        w("\n%s\n" % name.replace("_", "-").upper())
        for k in BUCKETS:
            w("  %-18s %6d\n" % (k, g[k]))
        w("  %-18s %6d\n" % ("fields_compared", sum(g.values())))
    w("\nEvery number above is a sum over the per-table blocks, and every\n")
    w("per-table block is a partition of its fields. Re-run this file to\n")
    w("reproduce all of them.\n")
    if issues:
        w("\nCOMPARISON INTEGRITY FAILURES:\n")
        for issue in issues:
            w("  - %s\n" % issue)


def selftest():
    import tempfile
    print("=" * 74)
    print("SELF-TEST -- compare_tables.py")
    print("=" * 74)
    ok_all = True

    def write(path, rows, fields):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            wr = csv.DictWriter(fh, fieldnames=fields)
            wr.writeheader()
            for r in rows:
                wr.writerow(r)

    flds = ["stratum", "coef", "p_wcb", "n_boot_ok", "note"]
    base = [dict(stratum="a", coef="1.0", p_wcb="0.5", n_boot_ok="", note="x"),
            dict(stratum="b", coef="2.0", p_wcb="0.25", n_boot_ok="999",
                 note="y"),
            dict(stratum="c", coef="0.126031746031746", p_wcb="0.1",
                 n_boot_ok="999", note="z")]
    cand = [dict(stratum="a", coef="1", p_wcb="0.5", n_boot_ok="9999", note="x"),
            dict(stratum="b", coef="2.0", p_wcb="0.9", n_boot_ok="9999",
                 note="y"),
            dict(stratum="c", coef="0.12603174603174605", p_wcb="0.1",
                 n_boot_ok="9999", note="")]
    with tempfile.TemporaryDirectory() as td:
        bt = os.path.join(td, "base")
        ct = os.path.join(td, "cand")
        for root, rows in ((bt, base), (ct, cand)):
            for rel in FINAL_TABLES:
                write(os.path.join(root, rel), rows, flds)
        out, grand, issues = run(bt, ct, 1e-9, "final")
        ok_all &= not issues

        gi = grand["bootstrap_independent"]
        gd = grand["bootstrap_dependent"]
        # per table: coef -> a same_double, b same_text, c lastdigit
        #            note -> a,b same_text, c now_blank
        #            stratum -> 3 same_text
        # x2 tables
        ok = (gi["same_double"] == 2 and gi["lastdigit"] == 2
              and gi["now_blank"] == 2 and gi["same_text"] == 2 * 6)
        ok_all &= ok
        print("\n  bootstrap-independent buckets: %s"
              % {k: v for k, v in gi.items() if v})
        print("  [%s] '1.0' vs '1' is same_double; 15-digit vs 17-digit is "
              "lastdigit; a value going blank is now_blank; none is silently "
              "absorbed" % ("PASS" if ok else "FAIL"))

        # Worked by hand, per table: p_wcb -> a same_text, b material
        # (0.25 -> 0.9), c same_text; n_boot_ok -> a newly_populated, b and c
        # material (999 -> 9999). So 3 material and 1 newly_populated per table.
        ok = (gd["newly_populated"] == 2 and gd["material"] == 2 * 3
              and gd["same_text"] == 2 * 2)
        ok_all &= ok
        print("\n  bootstrap-dependent buckets: %s"
              % {k: v for k, v in gd.items() if v})
        print("  [%s] a blank n_boot_ok filled in is newly_populated, NOT a "
              "value change; 999 -> 9999 and 0.25 -> 0.9 are material"
              % ("PASS" if ok else "FAIL"))

        tot = sum(gi.values()) + sum(gd.values())
        exp = 2 * 3 * len(flds)
        ok = tot == exp
        ok_all &= ok
        print("\n  fields compared %d, expected %d keys x %d fields x %d tables"
              % (tot, 3, len(flds), 2))
        print("  [%s] the buckets PARTITION the fields: they sum to exactly the "
              "number compared, so no field is counted twice or dropped"
              % ("PASS" if ok else "FAIL"))

        out2, grand2, issues2 = run(bt, ct, 1e-9, "all")
        ok = (sum(grand2["bootstrap_independent"].values()) == sum(gi.values())
              and len(issues2) == 2
              and all("not present in both trees" in x for x in issues2))
        ok_all &= ok
        print("\n  [%s] --scope all with no partial tables present reports both "
              "missing tables as integrity failures rather than silently skipping"
              % ("PASS" if ok else "FAIL"))

        # At --tol 1.0 every difference here is below tolerance: p_wcb
        # 0.25 -> 0.9 is rel 0.722 and n_boot_ok 999 -> 9999 is rel 0.900. All
        # three material fields become lastdigit; nothing else moves.
        big, _, _ = run(bt, ct, 1.0, "final")
        c = big[0][1]["blocks"]["bootstrap_dependent"]["counts"]
        ok = (c["material"] == 0 and c["lastdigit"] == 3
              and c["newly_populated"] == 1 and c["same_text"] == 2)
        ok_all &= ok
        print("\n  with --tol 1.0 the same data give material=%d lastdigit=%d"
              % (c["material"], c["lastdigit"]))
        print("  [%s] the tolerance is a REPORTED PARAMETER, not a hidden "
              "default: changing it moves fields between two named buckets and "
              "changes no other count" % ("PASS" if ok else "FAIL"))

        # Removing a column must be visible and make the comparison nonzero.
        badct = os.path.join(td, "bad_removed")
        reduced = [dict((k, v) for k, v in r.items() if k != "coef") for r in cand]
        for rel in FINAL_TABLES:
            write(os.path.join(badct, rel), reduced,
                  [f for f in flds if f != "coef"])
        _, _, badissues = run(bt, badct, 1e-9, "final")
        ok = sum("removed unexplained column(s): coef" in x for x in badissues) == 2
        ok_all &= ok
        print("\n  [%s] deleting coef from both candidate tables is reported twice "
              "and makes the comparison fail" % ("PASS" if ok else "FAIL"))

        # An explicitly retired column remains counted, but does not make the
        # integrity gate fail. This is needed when a scientifically invalid
        # derived field is deliberately removed rather than silently retained.
        _, _, allowed_issues = run(bt, badct, 1e-9, "final",
                                   allowed_removed={"coef"})
        ok = not allowed_issues
        ok_all &= ok
        print("  [%s] --allow-removed-column makes an intentional retirement "
              "explicit without hiding it from the field counts"
              % ("PASS" if ok else "FAIL"))

        # Duplicate keys must not be collapsed silently by dictionary loading.
        dupct = os.path.join(td, "bad_duplicate")
        for rel in FINAL_TABLES:
            write(os.path.join(dupct, rel), cand + [dict(cand[0])], flds)
        _, _, dupissues = run(bt, dupct, 1e-9, "final")
        ok = sum("duplicate key(s) in candidate" in x for x in dupissues) == 2
        ok_all &= ok
        print("  [%s] duplicate candidate keys are detected before comparison"
              % ("PASS" if ok else "FAIL"))

    print("=" * 74)
    print("SELF-TEST " + ("PASSED" if ok_all else "FAILED"))
    print("=" * 74)
    return 0 if ok_all else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base")
    ap.add_argument("--cand")
    ap.add_argument("--tol", type=float, default=1e-9)
    ap.add_argument("--scope", choices=("final", "all"), default="all")
    ap.add_argument("--allow-added-column", action="append", default=[],
                    help="candidate-only column explicitly expected by this "
                         "comparison; repeat for multiple columns")
    ap.add_argument("--allow-removed-column", action="append", default=[],
                    help="base-only column explicitly retired in the candidate; "
                         "repeat for multiple columns")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.base and a.cand):
        ap.error("--base and --cand are required unless --selftest")
    out, grand, issues = run(a.base, a.cand, a.tol, a.scope,
                             set(a.allow_added_column),
                             set(a.allow_removed_column))
    report(out, grand, a.tol, a.scope, issues)
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
