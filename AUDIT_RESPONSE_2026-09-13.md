# Response to the external audit of 2026-09-13

> **HISTORICAL RESPONSE, NOT CURRENT STATUS.** This file records what was known on
> 2026-09-13. Later audits changed several conclusions and found additional defects.
> Use `analysis/current_audit_status.md`, `analysis/hypothesis_verdicts.md`, the
> dated protocol amendments and current result tables for the accepted position.
> In particular, “independently” below means a separate audit calculation, not an
> independent scientific reference or validation dataset.

An external audit compared GitHub `main` (`a59f5fa`) and the local PhD folder
against the protocol. Its findings are answered here point by point, because
several were correct and the record should show which.

## Confirmed by the audit, independently

It reproduced the retained-only correction from the repository using its own
corrected filter and obtained **+7.11 → +6.18 d**, plateau p **.0488 → ~.095**,
fill p **.0449 → ~.060**. The regenerated tables in `results/s310_v2_district/`
give **+6.183 d, 0.0907, 0.0565**. A third party working independently landed on
the same numbers, which is the strongest single item in the audit.

## Correct, and fixed here

| finding | action |
|---|---|
| regression QC bug on GitHub | fixed; every estimate regenerated on 208/31,741 retained; self-test added that plants a +40 d effect in screened-out rows |
| hard-coded `/home/claude/...` paths in six scripts | replaced by `RICEBACI_ROOT` / `RICEBACI_RESULTS`; defaults unchanged, all self-tests re-verified |
| `S1_PER_ORBIT.js` saved with `dryRunDistrict: 'Pashchim Medinipur'` — queues 1 task, not 225 | reset to `null`, with a comment recording the gap |
| `orbit_agreement.py` imports a `load_panel` that does not exist on `main` | `load_panel` was extracted from `attrition_diagnostics.main()` on 2026-09-13; that change is in this snapshot |
| `dispersion_test.py` referenced but absent | included |
| H3 predeclared on SOS/POS/EOS, estimator produces trough/heading/drainage/harvest | Protocol §4.3.1: mapping authorised for **direction only, never identity**; verdict unchanged at 0 of 4 |
| H5 withdrawal never a dated amendment | Protocol §4.3.2 |
| §3.9 r-value grid neither run nor withdrawn | Protocol §4.3.3, withdrawn as inapplicable — `plsm_fit`/`plsm_retain` reference no amplitude ratio |
| §3.5 mask comparison absent | Protocol §4.3.4 + `gee/S1_MASK_FLAG.js`. **Still open**, now a 25-task job |
| README describes the obsolete optical design; no `requirements.txt` or `run_all.sh` | all three written |
| GitHub not a reproducible source of record | this snapshot |
| don't freeze Results/Abstract/Conclusions | agreed; not started |

## Correct about the record, mistaken about the analysis

The audit reported the orbit analysis as having "inputs but no results", and H1,
H2, H4 and the robustness arms as absent. Those existed when it looked, but only
in a working environment it could not see, and had never been delivered. The
conclusion was the right one to draw from the available evidence. The cause was a
delivery failure, and the audit's own principle — *a claim inside a script is not a
reproducible result* — applied to the project with more force than it knew. That
is what this snapshot exists to end.

Present here: 170,321 per-orbit PLSM fits and the clause (a) tables; the six H4
event stacks; four of five declared robustness arms; the 2,000-draw permutation
test at both levels; the censoring test; Protocol §4.1–§4.3.

## One item judged differently

The audit implied §3.1's Gate 1 needs a sensitivity run. It is **deliberately
inert at pixel level** on the radar substrate and applied at 0.5 to the
district-mean curve, documented in §3.1's 2026-09-12 note with measured
justification: no gate against r = 0.50 gives median valid dekads 26 vs 24,
minimum 19 vs 10, and the gate manufactures the only §3.11 ineligibility in the
entire untreated baseline. The comparison the audit asks for has been run and
reported; nothing further is owed.

## Adopted from the audit's closing advice

Its recommendation to separate original confirmatory tests, pre-result protocol
deviations, and result-aware robustness is correct and is not yet reflected in a
single table. The logs record this chronologically; a classified index will be
added before any Results text is written.
