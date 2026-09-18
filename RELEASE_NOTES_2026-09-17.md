# Paper 2 clean public code/results release

Prepared on 17 September and authorized for public release on 18 September 2026.
Repository: https://github.com/pandasupranab/RiceBaCI-QC-release
The author approved a new clean repository, MIT for code and CC BY 4.0 for
author-created data/results. The original private repository remains untouched.
The raw-data deposit is NOT yet public; no DOI resolution, author manuscript
approval, or full end-to-end replay is asserted by this release.

## Origin and scientific scope

Source: the independently accepted analysis tree at
`_work_tmp/paper2_codex_corrections_20260916/repo`, derived from private historical
commit `fc5eadb6292dfba945cf53c2b1f4eea9b8d75019`. The manuscript is a descriptive
measurement and interpretation study, not field validation or causal cyclone
effect identification. All result CSVs in this release copy retain the accepted
bytes. No estimator, hypothesis, numerical threshold, or result was changed.

The two accepted `results/s310_v2_{district,pixel}/Table_SX_AttritionTriggers.csv`
files contain CRLF. Two path-specific `.gitattributes` exceptions preserve
their exact accepted bytes in Git. This is a storage exception for frozen
evidence, not a change to any estimator or the general LF output policy.

## Monte Carlo wording correction (2026-09-17)

The older common "±1.3 d" summary is not supported by the specific archived
`results/montecarlo_precision.csv` used in the accepted manuscript. For
`sigma_db = 0.122`, `grid = free`, and 80 draws, t1/t2/t3/t4 standard deviations
are 0.000000/0.000000/2.179449/1.899836 d and signed errors are
0.000/0.000/-0.500/+0.375 d. These are conditional recovery results for one
on-grid synthetic trajectory, not a bound, confidence interval, field accuracy,
empirical district-panel precision, or a comparison with orbit repeatability.

This correction governs all mentions in historical protocol and audit entries.
Those dated records preserve their original wording; they are not current
interpretations. Current README, source-of-truth, verdict summary, active
protocol framing, and extraction-code comments have been reconciled. The code
changes are comments only. The accepted manuscript already reports these
per-marker results, so this does not request new manuscript analysis.

## Third-party reference documents

The nine PDFs under `docs/field_reference_pdfs/` are deliberately excluded from
this clean public copy. ICAR-CRIDA and PMFBY require permission for
redistribution; no permission record has been verified. The catalogue in
`docs/field_reference_sources.md` preserves citations and acquisition URLs.
Its references to locally archived PDFs describe the private research archive,
not files in this public release. Private originals and Git history
remain untouched. Exclusion changes no computation or source citation.

- ICAR-CRIDA: https://www.icar-crida.res.in/disclaimer.html
- PMFBY: https://pmfby.gov.in/copyrightPolicy
- GADM boundary data are not included; obtain them from https://gadm.org/data.html
  under https://gadm.org/license.html. An academic map is distinct from
  redistribution of the underlying shapefile.

## Release conditions still open

- Clean-repository strategy and licences were approved on 18 September 2026.
  `LICENSE`, `LICENSE-DATA.md` and `THIRD_PARTY_NOTICES.md` define the scope.
- Refresh the old replay kit, metadata, checksums and reconstruction instructions
  against this release's exact commit/tag before publishing the dataset.
- Verify all intended uploaded files and publish the permitted final dataset.
  `10.5281/zenodo.22750338` is RESERVED, not a published or resolving dataset DOI.
- Recheck anonymous access and matching GitHub/Zenodo identifiers after release.
- Author CRediT, human review/responsibility and final manuscript approval remain
  separate from data release. Only the user will click final journal Submit.
