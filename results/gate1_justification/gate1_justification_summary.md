# §3.1 Gate 1 justification test

Pre-declared in §3.1 (2026-09-09): the panel is extracted twice, with Gate 1
applied and without, and compared on four named criteria. **Gate 1 is retained
only if it improves these on the majority of criteria.** The statistics that
stand for each criterion are declared in `python/gate1_justification.py`'s
docstring, because §3.1 names the criteria without fixing them.

## Verdict: **REJECT Gate 1 as a tested QC step** — improves 0 of 4 evaluable criteria

| criterion | verdict | improves | worsens | unchanged |
|---|---|---:|---:|---:|
| fit quality | **WORSENS** | 0 | 2 | 0 |
| temporal stability | **MIXED** | 1 | 2 | 0 |
| spatial coherence | **MIXED** | 2 | 4 | 0 |
| orbit agreement | **MIXED** | 2 | 4 | 0 |

A criterion counts as improved only if every statistic it carries moves
favourably. Where they disagree it is MIXED, and mixed is not an improvement:
§3.1 retains Gate 1 only if it *improves*, so ambiguity resolves against
retention.

## The sample-selection confound, and what it shows

Gate 1 deletes five-day bins, which changes which pixel-seasons are retained at
all. A gate that deletes the noisiest pixels improves every dispersion
statistic by **sample selection alone**, with no better measurement. So each
criterion is computed twice: `as_is` on each arm's own retained set, and
`common` on the pixel-seasons retained in both.

On the fixed common subset the verdict is **REJECT Gate 1 as a tested QC step**.

| criterion | as_is | common |
|---|---|---|
| fit quality | WORSENS | WORSENS |
| temporal stability | MIXED | WORSENS |
| spatial coherence | MIXED | MIXED |
| orbit agreement | MIXED | NOT EVALUABLE |

Read the two columns together. A criterion that improves `as_is` but not
`common` is the gate **selecting** rather than measuring.

## Every statistic

| sample | criterion | statistic | marker | gate off | gate on | Δ | better | verdict |
|---|---|---|---|---:|---:|---:|---|---|
| as_is | fit quality | `rmsr_median` | all | 1.9847 | 2.0292 | 0.0445 | lower | worsens |
| as_is | fit quality | `retention_share` | all | 0.3527 | 0.3378 | -0.0148 | higher | worsens |
| as_is | temporal stability | `within_pixel_sd_median` | trough | 23.2539 | 23.5921 | 0.3382 | lower | worsens |
| as_is | spatial coherence | `within_district_sd_median` | trough | 31.0929 | 31.4303 | 0.3374 | lower | worsens |
| as_is | spatial coherence | `nugget_rms_d` | trough | 25.6765 | 25.9098 | 0.2333 | lower | worsens |
| as_is | temporal stability | `within_pixel_sd_median` | heading | 18.0054 | 18.0764 | 0.0709 | lower | worsens |
| as_is | spatial coherence | `within_district_sd_median` | heading | 22.4573 | 22.5294 | 0.0721 | lower | worsens |
| as_is | spatial coherence | `nugget_rms_d` | heading | 20.5657 | 20.4136 | -0.1520 | lower | improves |
| as_is | temporal stability | `within_pixel_sd_median` | harvest | 23.5103 | 23.5099 | -0.0004 | lower | improves |
| as_is | spatial coherence | `within_district_sd_median` | harvest | 28.5900 | 28.5272 | -0.0628 | lower | improves |
| as_is | spatial coherence | `nugget_rms_d` | harvest | 25.2987 | 25.3079 | 0.0092 | lower | worsens |
| common | fit quality | `rmsr_median` | all | 1.9948 | 2.0363 | 0.0415 | lower | worsens |
| common | temporal stability | `within_pixel_sd_median` | trough | 22.6790 | 23.2362 | 0.5573 | lower | worsens |
| common | spatial coherence | `within_district_sd_median` | trough | 30.6574 | 30.7207 | 0.0633 | lower | worsens |
| common | spatial coherence | `nugget_rms_d` | trough | 25.0260 | 25.4847 | 0.4587 | lower | worsens |
| common | temporal stability | `within_pixel_sd_median` | heading | 17.6597 | 17.9182 | 0.2585 | lower | worsens |
| common | spatial coherence | `within_district_sd_median` | heading | 22.3678 | 22.4216 | 0.0538 | lower | worsens |
| common | spatial coherence | `nugget_rms_d` | heading | 20.5078 | 20.2976 | -0.2102 | lower | improves |
| common | temporal stability | `within_pixel_sd_median` | harvest | 23.1572 | 23.2731 | 0.1158 | lower | worsens |
| common | spatial coherence | `within_district_sd_median` | harvest | 28.3514 | 28.3514 | -0.0001 | lower | improves |
| common | spatial coherence | `nugget_rms_d` | harvest | 25.1977 | 25.2970 | 0.0993 | lower | worsens |
| as_is | orbit agreement | `sigma_single` | trough | 25.9004 | 25.9168 | 0.0164 | lower | worsens |
| as_is | orbit agreement | `within_tolerance_share` | trough | 0.9443 | 0.9441 | -0.0002 | higher | worsens |
| as_is | orbit agreement | `sigma_single` | heading | 19.8169 | 19.8280 | 0.0111 | lower | worsens |
| as_is | orbit agreement | `within_tolerance_share` | heading | 0.9387 | 0.9389 | 0.0002 | higher | improves |
| as_is | orbit agreement | `sigma_single` | harvest | 25.7894 | 25.7887 | -0.0006 | lower | improves |
| as_is | orbit agreement | `within_tolerance_share` | harvest | 0.9114 | 0.9113 | -0.0000 | higher | worsens |

