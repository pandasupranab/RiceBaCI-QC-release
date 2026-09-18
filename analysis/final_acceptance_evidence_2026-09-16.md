# Paper 2 final drafting-acceptance evidence — 2026-09-16

## Decision

**GREEN FOR MANUSCRIPT AND SUPPLEMENT DRAFTING.** This is not permission to
commit, push, publish a repository/deposit, or submit to a journal. The accepted
scientific scope and wording contract are in
`manuscript_source_of_truth_2026-09-16.md`.

The audit found no unresolved defect that changes a reported result, denominator,
estimand, uncertainty statement or permitted interpretation within that bounded
scope. “Green” does not mean field accuracy or causal identification has been
created, nor that a future reviewer cannot find a minor issue.

## Source and remote state

- Candidate base: `fc5eadb6292dfba945cf53c2b1f4eea9b8d75019`.
- A fresh `git fetch origin main` on 2026-09-16 returned that same commit for
  local `HEAD`, `origin/main` and `FETCH_HEAD`; the canonical checkout was clean.
- Work was performed in an isolated candidate. Nothing was committed, pushed,
  published to Zenodo or submitted.
- NOAA IBTrACS v04r01 NI source SHA-256:
  `1E892624F97F5481CDDF6B8E9E65BE2925FA0A3336F399F5B9FD87FBB463FB78`.

## Clean numerical replays

1. Attrition diagnostics were run without resume at 9,999 draws:
   district 253/253 expected rows; pixel 308/308; 132 balanced keys at each
   level. Final and partial tables agree field by field. Alias verification
   reproduced 225/225 district-season exposure values.
2. Trigger accounting is two district labels/designs plus five pixel labels/four
   pixel designs: seven labels and six distinct designs overall.
3. Comparison with the preceding candidate removes exactly the retired
   `beta_balanced` and `delta_beta` columns and preserves every key. All retained
   coefficient/SE/t/count fields agree within 1e-9. `cyclone:REMAL` p_WCB changes
   by one draw, 0.7134 to 0.7135; it is underpowered and non-triggering. A
   separate clean targeted run returned 0.7135 again.
4. Both robustness tables were cleanly regenerated at 9,999 draws and match the
   accepted candidate bytes. The district/pixel tables retain 30 keys each; the
   six state-by-season cells without an implemented WCB are explicit.
5. The three 2,000-draw permutation tables, event-study table, NOAA exposure
   rebuild and MARC replay were independently reproduced. Event-study H4 remains
   2/6. No scientific verdict was changed to improve the paper.
6. The placebo log was regenerated from corrected source at 9,999 draws. A fresh
   district run reproduced both district attrition CSVs byte for byte.

## Fail-closed and independent checks

- All 26 registered self-tests passed; eight named utilities remain explicitly
  outside that roster.
- The attrition gate rejected external copies with a deleted key, duplicate key,
  whitespace-only reason, partial-only key and absent event-study comparator.
- The claim guard scans Markdown, text, logs, Python, shell, JavaScript, JSON and
  CSV. Its 24 claim/encoding sabotages pass; the live tree is clean. Invalid
  UTF-8 and U+FFFD are failures rather than silently skipped text.
- Both recorded environment profiles passed. `bash -n run_all.sh`, the LF-output
  scan, Python compilation, JSON parsing and active-CSV structural checks passed.
- Figure verification passed for one generator, ten inputs and fourteen outputs.
  Seven PDF text layers were scanned and all seven PDF/PNG pairs were visually
  inspected. These audit figures are not the final 1000-dpi journal JPGs.
- In a clean clone, all 26 self-tests and the semantic guard pass. Figure
  verification reports zero changed artifacts and the one expected missing
  large pixel-panel input; strict mode refuses that missing input.

## Accepted hashes (SHA-256)

```text
BDA8292F1C6CAB00A8FAA3F694FB710ECF49212975457CCB59A5B9C388AB9CAA  results/s310_v2_district/Table_SX_AttritionDiagnostic.csv
6A0D8AD6F0A57D3D3C949C9528E43D32283522538C174443058FD50E1FEFEAD8  results/s310_v2_pixel/Table_SX_AttritionDiagnostic.csv
4F93FBF6040B70BF8268A06CE76A6C4CB13C32D484A901AA7B149E0CF0962608  results/robustness/Table_SX_RobustnessArms_district.csv
E796C37A98E8CC4C020EE6979F487184D83053DB6AA6CCDD4AC5AD1B103F28F6  results/robustness/Table_SX_RobustnessArms_pixel.csv
727A6F8B90D32524F049AFAAC10F0248FD439E9094C27C8A95CF8B30520299CF  results/permutation_test/Table_SX_Permutation_district.csv
62ABAC804892C03F7A08D0D942BEB606CD85C2FB0EBA00CE427581599D4AB407  results/permutation_test/Table_SX_Permutation_pixel.csv
7020FF626C13BDD75DA2F7DD55A3CACE0ADA15C94114EBE40B965201B1D31B0C  results/permutation_test/Table_SX_Permutation_pixel_cens.csv
288602917C33AD94EB0A9D16F176679523E64449C504212FBCB2F0BCB4FF903C  results/Table_SX_EventStudy.csv
65A4E062D7FCC55B36BE734C40EAA5754C40DC223B3DFE58AA4532A3A9D6B66D  results/dispersion/Table_SX_Dispersion.csv
D7BFA253059BB8647154AB4686172332298DA891104390C451B75C5BEB436AAD  results/placebo_check.log
B51984D02172ECFC6C27AF02ECA07BCF76F4505F1D26C13DA12DF56CBB33F508  figures/figure_provenance.json
```

## Limits that remain and must not be “fixed” by wording

- no independent field reference: repeatability is not accuracy;
- selected usable orbit pairs and a marker-blind but potentially
  representation-affecting best-covered-pair rule;
- pooled baseline tolerances are permissive and Andhra Pradesh has only 15
  baseline pairs in the post-hoc state check;
- the 2018 product mask includes Titli and aggregate counts do not establish
  pixel identity;
- small/contaminated event controls, detected differential attrition and a
  rejected pixel timing placebo prohibit causal cyclone-effect claims;
- H3's optical constructs and H5's MODIS input are unavailable;
- permutation inference depends on unverified within-state exchangeability;
- a Git clone alone lacks the archived raw exports/large pixel panel, and no
  universal cross-environment byte identity is claimed.

These limitations are compatible with a full measurement-science article if the
manuscript stays within the accepted repeatability-and-interpretation question.
New field data would be required for accuracy or causal-effect claims, but are not
required for this bounded manuscript.

## Remaining release and submission work

The full `run_all.sh all` command was not executed as one uninterrupted command;
its major result-producing stages were instead replayed and gated independently.
Before submission, the accepted draft/supplement must pass numerical, citation,
cross-reference and visual QA; the repository must be committed/tagged and public;
the matching Zenodo record must be published with a resolving DOI; all hashes and
data statements must agree; and the author must confirm the exact final package.
