# /manuscript — drafting authorised 2026-09-16

**No manuscript text exists in this repository yet.** The independent acceptance
audit is now green for drafting. Claude may prepare the manuscript and supplement
only from `analysis/manuscript_source_of_truth_2026-09-16.md` and the evidence
tables it names. Drafting does not authorise a commit, public deposit or journal
submission.

Corrected 2026-09-13. The previous version listed `scoping_memo.md`, `main.tex`,
`main.docx`, `supplement.tex`, `supplement.docx` and `refs.bib`, and said the memo
and bibliography were "the only Week-1 deliverables here". **None of those files
exists** and none has been committed at any point.

When drafting does begin, the substantive constraints already fixed by the analysis
are, at minimum:

- Every causal claim from §3.8 is withdrawn (§4.1). The design fails its own §3.9
  timing placebo at pixel level in 4 of 5 robustness arms.
- Outcomes are named as fitted breakpoints — trough, heading, drainage, harvest —
  never as SOS / peak NDVI / EOS. §4.3.1 authorises the H3 mapping for direction
  only, never identity.
- Of the five predeclared hypotheses, H4 fails on its declared criterion; H1 and
  H2 each fail one clause while the other clause passes only as the permissive
  pooled-baseline rule was written; H3 is not estimable as declared; and H5 was
  withdrawn untested. The authoritative classifications are in
  `analysis/hypothesis_verdicts.md`; absence or withdrawal is never called failure.
- What the study reports positively is a set of **measured disagreement statistics with
  their scope attached**: between-orbit disagreement of 25.90 / 19.82 / 25.79 d on a
  single pixel-season in the selected paired sample, and — separately — a Monte Carlo
  that recovered its planted breakpoints to ±1.3 d on a **synthetic** district-season
  trajectory under its assumed 0.122 dB noise level. The two are **not commensurable**
  and no ratio between them is reported.

*Corrected 2026-09-14 (eighth pass): the last bullet read "The positive contribution is
the located measurement boundary: ±1.3 d on a district-season mean marker against σ ≈ 26 d
on a pixel-season." The scale boundary was withdrawn on 2026-09-14 (§1.5.4 item 1) and a
simulation is not a measured precision.*
