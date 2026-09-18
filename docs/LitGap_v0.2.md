# Literature map v0.2 — Sentinel-1 rice phenology measurement limits

**Search and screening completed: 2026-09-16.** This file replaces
`LitGap_v0.1.md` for current positioning. It is a structured, reproducible
scoping refresh, not a PRISMA systematic review and not evidence for a
`first`, `novel`, or `unique` priority claim.

## Frozen search protocol

Scope: peer-reviewed primary research from 2015 through 16 September 2026 on
Sentinel-1 crop/rice phenology timing, multi-orbit or acquisition-geometry
effects, smoothing/breakpoint fragility, external timing validation, and
cross-sensor timing differences. Include a record when its title or abstract
reports a phenological date/stage, a timing-error or uncertainty quantity, or
an acquisition/smoothing effect on phenology. Exclude crop-extent mapping with
no timing outcome, non-Sentinel-1 studies, secondary commentary, and duplicate
publisher/repository records.

The search interface was the OpenAI web search index, followed by the primary
publisher or DOI record for every included identity. The four exact queries and
result-link counts were:

| Query | Result links screened |
|---|---:|
| `"Sentinel-1" rice phenology multi-orbit acquisition geometry uncertainty` | 28 |
| `"Sentinel-1" rice transplanting harvest dates validation field phenology` | 19 |
| `"Sentinel-1" breakpoint rice phenology smoothing uncertainty` | 21 |
| `rice phenology Sentinel-1 Sentinel-2 breakpoint Bangladesh climatic zones` | 22 |

Thus 90 result links were screened at title/abstract level. Counts are links,
not deduplicated studies: publisher pages, repositories and mirrors can repeat
one article. Nine unique primary studies were retained for direct comparison;
the other 81 links were duplicate/mirror records or failed at least one scope
criterion. This search is date-bounded and cannot establish that no other study
exists.

## Included evidence and what it permits

| Study | Verified identity | Relevant evidence | Boundary for Paper 2 |
|---|---|---|---|
| Löw et al. (2026) | *Science of Remote Sensing* 13, 100370; DOI `10.1016/j.srs.2026.100370` | Multi-orbit, multi-feature Sentinel-1 phenology framework; reports orbit-dependent differences and uncertainty windows. | Directly prevents any broad claim that multi-orbit phenology uncertainty is unstudied. It is field-scale and not rice. |
| Cauba et al. (2025) | *Remote Sensing Applications: Society and Environment* 37, 101435; DOI `10.1016/j.rsase.2024.101435` | 99 rice fields in three Philippine provinces; farmer-interview reference; transplanting and harvest RMSD in days. | External accuracy against field information is a different quantity from Paper 2's between-orbit repeatability. |
| Yang et al. (2021) | *Remote Sensing of Environment* 259, 112394; DOI `10.1016/j.rse.2021.112394` | Dynamic-threshold/hierarchical-tree/particle-filter Sentinel-1 rice phenology method without prior transplanting dates. | Prevents a claim that Sentinel-1 rice phenology estimation itself is new. |
| Zhao et al. (2023) | *Agricultural and Forest Meteorology* 329, 109283; DOI `10.1016/j.agrformet.2022.109283` | Feature-based S1/S2 algorithm for planting, heading and harvest dates, validated at multiple scales. | Shows existing multi-scale timing validation; Paper 2 must not call its breakpoints externally validated. |
| Zhao et al. (2024), MARC | *Earth System Science Data* 16, 3893–3922; DOI `10.5194/essd-16-3893-2024` | 0.5-degree monsoon-Asia calendar using S1/S2, with site-scale literature validation. | Paper 2 makes a district comparison against this coarse external product; it is neither pixel validation nor a field reference. |
| Hoque et al. (2026) | *Agricultural Research* 15, 717–740; DOI `10.1007/s40003-025-00921-z` | S1 cross-ratio and S2 EVI breakpoints across seven Bangladesh climate zones; systematic sensor offsets; six field parcels. | Direct evidence that radar and optical dates are different measurands and that limited field checks do not validate all parcels. |
| Wang et al. (2022a) | *Sustainability* 14, 8009; DOI `10.3390/su14138009` | Growth-curve simulation with Sentinel-1 and field phenological observations. | Existing timing-accuracy evidence must be distinguished from Paper 2's internal repeatability. |
| Wang et al. (2022b) | *Open Geosciences* 14, 414–428; DOI `10.1515/geo-2022-0369` | Unified dynamic-programming framework for rice mapping and Sentinel-1 phenology. | Further prevents method-priority claims; smoothing/interpolation choices remain method-specific. |
| Phan, Le Toan & Bouvet (2021) | *Remote Sensing* 13, 921; DOI `10.3390/rs13050921` | Dense Sentinel-1 rice backscatter series with in-situ seasons; documents minima, rise and late-season VH/VV behaviour. | Supports the physical interpretation of the signal shape, not a universal agronomic-date identity. |

## Corrected contribution statement

Paper 2 does **not** introduce Sentinel-1 rice phenology estimation, multi-orbit
crop-phenology analysis, or timing uncertainty in days. Its defensible
contribution is narrower: it measures between-orbit repeatability of one frozen
piecewise-linear breakpoint estimator at 30 m across 25 coastal districts and
nine Kharif seasons, tests the sensitivity of its own outputs to repeat coverage
and marker-blind orbit-pair choices, and follows the measurement limitations into
a cyclone-response analysis whose causal interpretation is rejected after the
predeclared timing placebo fails. Attrition diagnostics are reported as additional
selection evidence, not as proof of the placebo's cause.

The study has no field reference. Between-orbit disagreement is not accuracy;
agreement is not validation; and radar breakpoints are not optical or agronomic
dates merely because their ordering is compatible with a crop calendar.

## Withdrawn bibliographic identity

The v0.1 entry `Bouvet et al. 2018 — Sentinel-1 InSAR coherence for early crop
monitoring: applied to a rice paddy, Remote Sensing of Environment` could not be
resolved as a real publication under that title, year, sensor and journal. It
appears to conflate multiple works and is withdrawn rather than silently
repaired. Current signal-shape statements use Phan, Le Toan & Bouvet (2021), DOI
`10.3390/rs13050921`; historical ENVISAT rice mapping by Bouvet & Le Toan is a
different paper (2011, DOI `10.1016/j.rse.2010.12.014`); neither is an invented
2018 Sentinel-1 coherence article.

## Source-to-claim rule

The identities above were checked against publisher pages or DOI-resolving
primary records. They support only the claims in the third column. No source in
this map supports calling Paper 2 first, unique, externally validated, or a
measurement-error estimate. Manuscript references must be generated later from
these verified identities; this protocol file does not pretend that a current
`refs.bib` already exists.
