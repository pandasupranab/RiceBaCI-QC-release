# Orbit-pair selection sensitivity: execution receipt

**Run date:** 2026-09-16  
**Status:** post-hoc robustness diagnostic; not an accuracy analysis

The analysis was executed twice in the checked numerical environment. Both runs
produced the same output bytes.

## Inputs and code

| item | bytes | MD5 | SHA-256 |
|---|---:|---|---|
| archived `per_orbit_fits.csv` | 26,215,859 | `05f4e849164a22ddc6b6a65cc1fdc2c0` | `31b96b6ea2521dce7ee4b9adabd32d9870ea34fff88468e20084073e49f089cf` |
| `docs/candidate_cohort_v2.csv` | 876,602 | `b04e3a5b57215985c89217ab659a543b` | `dc6670f33a85c9da00c435bba0b9c584e7aca9fca26870bec01311411d3e16bb` |
| `python/orbit_pair_selection_sensitivity.py` | 11,226 | `4e2aa602e3643fe0442662f950536d66` | `1ba251b0e67818c1de95fe953b07000ac6e094a007b6bd96b124e4b66122868c` |

The fitted input is outside Git because of size. Its source is the archived 225
per-orbit Earth Engine exports; stage 11 of `run_all.sh` regenerates it.

## Output

`results/orbit_agreement/Table_SX_OrbitPairSelectionSensitivity.csv`

- bytes: 7,998
- MD5: `d0ca83393b2dcdab71535fe25784230f`
- SHA-256, both runs: `7bbbfbc1eecb8d63203eae476b1c9d7031b860e0d97a045a16d2c65dde360279`

At pooled scope, scaled disagreement for trough / rise-end (`heading`) /
fall-end (`harvest`) was:

| marker-blind rule | scaled disagreement (days) | share within the fixed declared 2017 tolerance |
|---|---|---|
| declared best coverage | 25.900 / 19.817 / 25.789 | 0.9443 / 0.9387 / 0.9114 |
| lowest eligible orbit numbers | 25.848 / 19.852 / 25.777 | 0.9444 / 0.9379 / 0.9121 |
| all eligible pairs, each pixel-season weighted to one | 26.177 / 20.029 / 25.834 | 0.9443 / 0.9372 / 0.9113 |

All values remain above the declared 0.90 stability criterion under these three
tested selection rules. This is robustness to those alternatives, not proof that
pair selection has no effect. It does not establish accuracy, independent errors,
or state-level transferability.
