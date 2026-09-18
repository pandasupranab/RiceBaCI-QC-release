# Paper 2 correction and acceptance ledger

Status at 2026-09-16: **GREEN FOR MANUSCRIPT DRAFTING.**

This is an isolated candidate based on patch20l and parent
`fc5eadb6292dfba945cf53c2b1f4eea9b8d75019`, not a committed or released version.
Claude's descriptions are leads to test, not acceptance evidence. Codex is now
implementing the corrections directly; Claude's next role is drafting from the
authoritative source-of-truth file. No guarantee can be made about what future
reviewers will find, and this is not yet a release or submission approval.

## Acceptance conditions

1. No known unresolved defect that could change the reported result, its
   denominator, uncertainty, estimand or interpretation.
2. Clean runs reproduce the accepted tables from the declared inputs, with
   explicit numerical tolerances, complete keys and no silent missing tests.
3. Tests reject planted defects, not just accept the normal example.
4. Protocol, code, tables, figures, summaries and drafting instructions agree.
5. Result-aware changes and remaining scientific limitations are explicit.
6. A frozen, inspected evidence package supports each manuscript claim.

Public GitHub and a resolving published Zenodo DOI are additional **submission**
conditions. They are not satisfied by an unpublished draft or a promised DOI.
Release and journal submission require the author's final confirmation of the
exact contents. No such public action is part of this correction pass.

## Evidence obtained so far

| Check | Current result |
|---|---|
| Registered self-tests | 26 passed; 8 named utilities are explicitly outside that roster. This is not proof of complete scientific correctness. |
| Completeness and runner safeguards | Missing/invalid status, reasons, numeric fields, key sets, partial/final disagreement, alias evidence and missing registered modules are tested. Five independent external table sabotages and the registered internal cases fail as required. Both accepted final tables pass their own gates. |
| District attrition clean run | 253 rows; completed at 9,999 draws and passed the gate with live alias verification. |
| Pixel attrition clean run | 308 rows; completed at 9,999 draws without resume and passed the exact-key, field-by-field and live-alias gate. It has 132 balanced keys, five triggered labels and four distinct triggered designs. |
| Attrition comparison | Exact key sets are preserved and only the two explicitly retired columns disappear. All retained coefficient/SE/t/count fields agree within 1e-9. One underpowered non-trigger WCB p-value is 0.7135 rather than 0.7134 (one draw); a separate targeted clean recomputation returns 0.7135. No conclusion changes. |
| Event-study replay | Completed; provenance fields are present; H4 remains 2 of 6. |
| Repeat-coverage sensitivity | Run across minimum 2/4/6/8/9 seasons; observed within/between ratios remain above 1 in the tested samples. Post-analysis sensitivity, not a redefinition of H1/H2. |
| Orbit-pair choice | Declared best coverage, lowest eligible orbit numbers and unit-weighted all pairs tested. Pooled fixed-tolerance shares remain above 0.90 under those alternatives; accuracy and independent errors are not established. |
| State tolerance check | Run; the small Andhra Pradesh baseline and lack of pooled-to-state transfer are disclosed. |
| MARC replay | Both comparison tables reproduced byte-identically using the archived reference and replayed panel. This is product agreement, not field validation. |
| Exposure rebuild gate | Actual defect reproduced: old gate passed with an empty rebuild directory. Fixed; six synthetic cases tested. |
| Raw exposure rebuild | NOAA v04r01 NI CSV retrieved 2026-09-16; baseline and all three exposure variants reproduced exactly. Three variant footprint tables have identical values after key sorting, not identical bytes. A second run used unchanged inputs/generator and recorded eight output hashes. |
| Robustness arm inference | Old default was 999 rather than declared 9,999. Both levels were rerun cleanly: 30 keys per level are preserved; coefficients/SE/t differ by at most 4e-15; all 24 available WCB p-values at each level were recomputed; five placebo permutation p-values are unchanged. Six state-by-season FE cells explicitly have no WCB implementation. No 0.05/0.10 verdict reverses. |
| Figure generation | All seven regenerated, including the latest figure-7 correction; strict verification checks 1 generator, 10 inputs and 14 outputs. All seven PNGs and all seven PDF renders inspected. PDF text scan found none of the four specifically withdrawn phrase families tested. These are audit figures, not the final journal layout: full-width JPGs, larger labels and external captions remain a drafting task. |
| Full runner | Missing static-panel merge, missing phase-classification arguments, censoring dependency order, catalogue check and environment routing corrected. The major stages were replayed independently; one end-to-end invocation from raw exports was not run and remains a release-reproducibility task, not a drafting claim. |
| Orbit fitting cache | Filename-only resume replaced by content/source/option and output-integrity checks. Legacy, stale, incomplete and interrupted caches refuse reuse; partial fitting exits 3, not success. No numerical fitting rule changed. |
| Window control gate | Corrected finite-to-missing/infinite changes, duplicate/missing keys and self-comparisons; failure stops before sweep tabulation. Five new sabotage checks pass. Comparison now explicitly reports parsed-value equality, not byte equality. Runner requires a separately archived pre-run reference. |

## Interpretation corrections in this pass

- The permutation |t| comparison with 1.96 did **not** calibrate the wild cluster
  bootstrap. Within-state relabelling requires exchangeability and changes real
  storm-footprint geometry. Neither method identifies the cause of an association.
  Both conditional procedures must be reported without choosing validity from
  the size of the resulting p-value.
- The mask summary in `test_classification.md` was stale. The declared named-event
  block has 35 paired estimates and sign agreement 31/35, 22/35 and 21/35 for
  trough, heading and harvest. Additional storms are a separate exploratory block.
- Figure 7's claim of a strictly monotonic elevation pattern was false: the last
  two observed means are 0.1667 and 0.1687. The label is corrected and naive error
  bars are explicitly qualified for unaccounted spatial dependence.
- A bootstrap/permutation result cannot turn radar breakpoints into agronomic
  dates. Shared errors remain invisible to orbit differencing. Conditional Monte
  Carlo recovery is not field accuracy. No variance subtraction is reinstated.

## Drafting authorisation and remaining gates

Manuscript and supplement drafting may begin from
`analysis/manuscript_source_of_truth_2026-09-16.md`. Every scientific statement
must stay inside its permitted scope. Final journal artwork, references,
cross-references and disclosures are drafting deliverables and will receive a
separate independent audit.

Commit/push, publication of a Zenodo deposit and journal submission remain
withheld. They require an accepted draft, a clean release candidate, matching
public GitHub tag and Zenodo archive/DOI, and the author's confirmation of the
exact files and metadata.

Scientific limitations such as absence of a field reference, selected usable
pairs and unverified exchangeability need not make a descriptive measurement
paper unpublishable. They do prohibit claims that depend on those missing
properties. The green signal means the paper is defensible **within its stated
scope**, not that all uncertainty has been eliminated.

## Run evidence location

The audit workspace is `D:/Documents/Phd-2024/_work_tmp/paper2_codex_corrections_20260916`.
Commands, logs and provisional outputs are under `final_rerun_20260916`.
GitHub `main` was rechecked live after the final replay on 2026-09-16 and still
equals `fc5eadb6292dfba945cf53c2b1f4eea9b8d75019`; the canonical local
checkout is clean at the same commit. Nothing has been applied there.
The downloaded NI source SHA-256 is
`1e892624f97f5481cddf6b8e9e65be2925fa0a3336f399f5b9fd87fbb463fb78`.
Its source is NOAA's [IBTrACS v04r01 CSV directory](https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/v04r01/access/csv/).
This is a dated source snapshot, not a claim that a future live download will
have identical bytes.

For the inference correction, the [boottest authors' documentation](https://github.com/droodman/boottest/blob/master/boottest.sthlp)
describes comparison with a bootstrapped reference distribution, not a universal
1.96 critical value. The correction also follows directly from this repository's
`wild_cluster_bootstrap()` implementation.
