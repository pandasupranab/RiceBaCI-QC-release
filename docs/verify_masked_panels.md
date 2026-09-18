# Provenance and verification of the §3.5 masked district-season panels

**Written 2026-09-14 because an external audit was right and this project was wrong.**

## The claim that was wrong

On 2026-09-14 this project stated, in `analysis/decisions_log.md` and in correspondence,
that the correctly fitted district-season panels "already existed on disk for both masks",
offered as the reason the §3.5 per-unit arm needed no re-export. **That was true of the
author's working environment and false of this repository.** An audit of the full local
copy of the project, ZIP archives included, found only the primary panel
`results/phen_panel_district_season.csv`; nothing under `results/masked*` was committed at
`292c4c0`, and `git ls-files` confirms it. So the per-unit arm as shipped in patch18 could
not have been reproduced from a clone, while the amendment describing it implied it could.

This is the same failure this repository has already recorded once: `README.md`'s original
"nine of nine self-tests pass" was true only in the environment it was written in. An
environment-specific claim stated as a repository property is the recurring defect, not a
one-off.

## The fix

The four masked **district-season** panels are now committed. They are district-level
(225 rows = 25 districts x 9 seasons), so the total is 274 KiB rather than the ~117 MiB of
the masked **pixel** panels, which remain excluded and which this arm does not read.
`python/mask_sensitivity.py --per-unit` therefore now runs **from a clone with no Earth
Engine account**, which is what §3.5's per-unit rule needs in order to be a reproducible
disclosure rather than a reported number nobody else can recompute.

## How a third party verifies these files WITHOUT trusting this document

Every check below uses files that were **already committed before this patch**, so the new
panels can be validated against the existing repository rather than against my word.

**1. The intersection mask's own size, from a committed file.**

    python - <<'EOF'
    import pandas as pd
    m = pd.read_csv("results/mask_sensitivity/mask_flag_all.csv")
    print(len(m), int(m.in_worldcereal_temporary.sum()))
    print(dict(m.worldcereal_pixels_sampled.value_counts()))
    print(int(m[m.worldcereal_pixels_sampled > 1].in_worldcereal_temporary.sum()))
    EOF

Expected: `10000 8085`, then `{1: 9938, 2: 62}`, then `59`. So the intersection mask
admits **8,085** of 10,000 cohort points; **62** points fall under two WorldCereal tiles;
and **59** of those 62 are inside the intersection, which is why the `_noovl` variant holds
8,085 - 59 = **8,026** points and not 8,085 - 62. (§3.5's wording implied 62 left the
sample; corrected in the protocol this date.)

**2. The filter report, also already committed, must agree across nine seasons.**

    python -c "import pandas as pd; f=pd.read_csv('results/mask_sensitivity/filter_report_masked.csv'); print(int(f.cells_out.sum()))"
    python -c "import pandas as pd; f=pd.read_csv('results/mask_sensitivity/filter_report_masked_noovl.csv'); print(int(f.cells_out.sum()))"

Expected `72765` and `72234`, which are exactly 8,085 x 9 and 8,026 x 9.

**3. The new panels must carry those same totals, per season, and be nested.**

*What this check does and does not establish — narrowed 2026-09-14 after an auditor said so,
and the auditor is right.* Checks 1–3 are **consistency** checks, not construction proofs. A
panel built the wrong way — by averaging separately-fitted pixel dates — could also have 225
rows, the correct per-season pixel totals and correct nesting, because those properties come
from the mask, not from the estimator.

*Narrowed again, later the same day, after the auditor said the first narrowing did not go far
enough. It did not.* The earlier wording claimed checks 1–3 "rule out a panel masked at the
wrong step **or built over the wrong sample**". **They rule out neither.** A different set of
8,085 cohort points would give the same totals and the same nesting, so counts cannot establish
**sample identity**; and nothing in a count reveals at which **stage** the mask was applied.
What checks 1–3 establish is exactly one thing: **count consistency between the committed mask
flags and the committed panels** — now at district resolution (check 3b, 75 constraints) rather
than three totals. They do not prove the sample members, the masking stage, or that the PLSM
was fitted to the district mean curve. The **defensible statement of scope**, which now governs every
reproducibility sentence in this repository:

> **The per-unit calculation is reproducible from the committed fitted district panels;
> reconstructing those panels still requires the archived raw exports.**

Two things do bear on construction, and neither is a substitute for the raw exports. First,
`results/masked/phen_curves_district_season.csv` — the district-season **mean curves** the fit
was performed on — exists in the pipeline output and could be committed if a reviewer wants
the fit itself re-checkable; it is 508 KiB per variant and is not committed today, which is
recorded here rather than implied away. Second, check 5 below asserts in code that the
estimator **refuses** a pixel panel, so the wrong construction cannot be performed by the
committed code at all. That is a statement about the code, not a proof about these bytes.

    python - <<'EOF'
    import pandas as pd
    pri = pd.read_csv("results/phen_panel_district_season.csv")
    msk = pd.read_csv("results/masked/phen_panel_district_season.csv")
    nov = pd.read_csv("results/masked_noovl/phen_panel_district_season.csv")
    for t, d in (("primary", pri), ("masked", msk), ("noovl", nov)):
        print(t, len(d), sorted(set(d.groupby("year").n_pixels.sum())))
    k = ["district", "year"]
    print("masked <= primary:", bool((msk.set_index(k).n_pixels <= pri.set_index(k).n_pixels).all()))
    print("noovl  <= masked :", bool((nov.set_index(k).n_pixels <= msk.set_index(k).n_pixels).all()))
    EOF

Expected: `primary 225 [10000.0]`, `masked 225 [8085.0]`, `noovl 225 [8026.0]`, then
`True` and `True`. Three constants and two nesting relations, and that is all they are: a panel
built from a *different* 8,085 points, or masked at a different stage, would reproduce every one
of them. Check 3b raises the count from 3 constraints to 75; it does not change their kind.
*Corrected
2026-09-14: this sentence used to end "…or built by averaging pixels instead of fitting the
mean curve, would not reproduce those three constants" — **the exact claim the scope note
above withdraws**, left standing thirty lines below it. A pixel-averaged panel would satisfy
all three constants, because they come from the mask and not from the estimator. Found by an
external auditor. This is the fifth time in three days that a correction was written in one
place and the claim it corrects was left standing nearby.*

**3b. The per-district counts must match the committed mask flags — 75 constraints, not 3.**

    python - <<'EOF'
    import pandas as pd
    m = pd.read_csv("results/mask_sensitivity/mask_flag_all.csv")
    exp = {"results/phen_panel_district_season.csv": m.groupby("district").size(),
           "results/masked/phen_panel_district_season.csv":
               m[m.in_worldcereal_temporary == 1].groupby("district").size(),
           "results/masked_noovl/phen_panel_district_season.csv":
               m[(m.in_worldcereal_temporary == 1)
                 & (m.worldcereal_pixels_sampled == 1)].groupby("district").size()}
    for path, e in exp.items():
        g = pd.read_csv(path).groupby("district").n_pixels
        print(path, "| constant across seasons:", int((g.nunique() == 1).sum()),
              "| mismatches:", int((g.min() != e.reindex(g.min().index)).sum()))
    EOF

Expected: `25` constant and `0` mismatches on each of the three panels. This is a stronger form
of check 3 and it is the strongest statement the committed files support: the per-district
pixel counts in all three panels are reproduced, district by district, from
`mask_flag_all.csv` alone — **75 district-by-panel constraints**, added 2026-09-14 after an auditor
pointed out that three global totals are weak evidence. It pins the mask's spatial
distribution, not merely its size. It remains a **count** check: a permutation of members
within a district would survive it, and no check available from the committed files can
establish sample identity without the raw exports.

**4. The per-unit tables must regenerate byte-identically from the committed inputs, in
the recorded test environment.**

    export RICEBACI_ROOT=/path/holding/results
    for mk in trough heading harvest; do
      python python/mask_sensitivity.py --per-unit --marker "$mk"
    done
    md5sum results/mask_sensitivity/Table_SX_MaskPerUnit_*.csv

Expected, and these are the hashes this patch commits:

    a74c8ac8ef997a0a41357eed97c95064  Table_SX_MaskPerUnit_trough.csv
    dee806072937d3c9df91d560730ec577  Table_SX_MaskPerUnit_heading.csv
    89c9df7398846498b9bda886059b3a35  Table_SX_MaskPerUnit_harvest.csv

**On "byte-identical", and a defect this wording exposed.** Those md5s were produced in the
recorded test environment recorded in `DATA_AVAILABILITY.md`, and they are asserted for that
environment. One source of difference was removed in 2026-09-14 and it was only one:
`pandas`
`DataFrame.to_csv` defaults `lineterminator` to **`os.linesep`**, so on Windows it writes
CRLF. An auditor regenerated these three tables on Windows and got **the same parsed values
with CRLF** — each file 226 bytes larger (225 rows + header), a different md5, byte-identical
only after normalising line endings. Their conclusion was right and the fix belongs in the
code, not in this document's wording.

`python/lf_output.py` (new, and self-test module 1 of 19 — `attrition_completeness.py` was added 2026-09-15) pins `lineterminator="\n"` for
`DataFrame.to_csv` and `Series.to_csv` on import, and supplies `open_lf()` for text writes.
**Every module in `python/` that writes CSV imports it** — the number is deliberately not
written here, because the self-test counts it at run time and prints it, and a hardcoded count
in prose is exactly what went stale when `build_coastal_districts.py` turned out to be absent
from the author's working copy and therefore uncounted. The defect was **not** limited to the three tables
that were tested: **65 `to_csv` call sites** carried it, and four modules wrote committed
JSON through a bare `open(path, "w")` — including `figures/figure_provenance.json`, the file
`make_figures.py --verify` compares against. Those are pinned too.

The guard is enforced rather than documented: `lf_output.py --selftest` scans the source of
every sibling module and **fails** if a module that calls `.to_csv(` does not import the
guard, or if a committed-JSON writer opens its file without pinning the newline — and both
gates are tested by sabotage, in the style the rest of this repository uses. So the **line
ending** is now a property the build checks rather than a claim this file makes.

*(Scoped 2026-09-15, tenth pass.)* This section previously said the md5s "hold on any
platform that writes LF" and that `"byte-identical on every platform" is now a property the
build checks`. **Both are withdrawn as overstated.** Pinning `lineterminator` removes the
**line-ending** source of byte difference and no other. Byte identity of a CSV also depends
on how the installed `pandas` and `numpy` render floats to text, and on the values
themselves — and this repository has **measured** those values differing between two of its
own containers at the 16th significant figure, traced to the order in which OpenBLAS reduces
sums (`results/window_sweep/window_sweep_summary.md`). A cross-environment claim this file
can make is **value identity to within last-bit floating-point difference**; byte identity is
a separate and stronger claim, and it is asserted only within the recorded test environment. The two
were run together in the earlier wording, which is the same conflation `make_figures.py`
corrected for figures in the same pass.

This is the check that matters, and here is precisely how far it reaches: it closes the loop
from the committed district panels to the committed result tables, with no Earth Engine account
and no file that exists only on the author's machine. It does **not** close the loop back
through the panels to the raw exports — that half cannot be closed from this repository, and
checks 1–3b constrain the panels by count only. *Corrected 2026-09-14: this paragraph read
"from committed mask flags, through the committed district panels, to the committed result
tables", which claims the whole chain.*

**Running this check is what found a second missing dependency, and it is why the hashes
above are not the ones patch18 originally carried.** Committing the district panels was not
sufficient. The per-unit table also carried two columns — `primary_withdrawn_pixelavg_coef`
and `intersection_withdrawn_pixelavg_coef` — computed from the masked **pixel** panels, which
are ~117 MiB and are not committed. Regenerated in a directory holding only committed files,
the table came out with 39 columns instead of 41 and different bytes; every other column was
identical. So the table was still unreproducible, for a second and independent reason, and no
amount of reading the code would have shown it: only running it against committed files only.

The withdrawn comparison is now **opt-in** (`--withdrawn-comparison`) and writes a separate
file, `Table_SX_MaskPerUnit_withdrawnCompare_<marker>.csv`, which `DATA_AVAILABILITY.md`
labels as **not regenerable from this repository**. The main tables depend on committed inputs
only, and the byte-identity above was then confirmed in both directions: generated from the
committed-files-only directory and from the full working environment, the three tables are
`cmp`-identical.

**5. Independently, the estimand can be shown to be the declared one.**

    python python/mask_sensitivity.py --selftest

Among its checks: `district_curve_panel` reads the committed mean-curve fit and **refuses a
pixel panel outright**; `derive_stack` drops a control severely exposed in t+1; the primary
roster equals `event_study.ESTIMABLE`. Those three assertions fail if any of the three
defects found on 2026-09-14 is reintroduced.

## File hashes as committed

| repo path | bytes | rows | cols | md5 |
|---|---|---|---|---|
| `results/masked/phen_panel_district_season.csv` | 64270 | 225 | 26 | `1410450b11bea1fbe742932316f758c4` |
| `results/masked/phen_panel_district_season_static.csv` | 76020 | 225 | 29 | `de1e05854c770060b7b68de595904fba` |
| `results/masked_noovl/phen_panel_district_season.csv` | 64399 | 225 | 26 | `dddaebeba9bfd790adeef25f88d2c777` |
| `results/masked_noovl/phen_panel_district_season_static.csv` | 76119 | 225 | 29 | `49f6e727aab3ef5fb51afe8fce101150` |
| `results/phen_panel_district_season.csv` | 63445 | 225 | 26 | `5911e143606fac3fee111b55e1bd633e` |

Git blob SHA-1 (what `git hash-object <file>` and `git ls-files -s` will print):

    a2da5d4fcc86c4ce37a125934399c6bc48c9fcb6  results/masked/phen_panel_district_season.csv
    a48f00d5acbc50fc9cc4e74efa121063247d68af  results/masked/phen_panel_district_season_static.csv
    441cc5abae1ba3b504ba0754774dad427adb3b10  results/masked_noovl/phen_panel_district_season.csv
    63ee5a88a8b661282177b6ecec5a0030aa4fea4c  results/masked_noovl/phen_panel_district_season_static.csv
    b7e24a10def5699ce4fd5f46bab4495d4350ad4a  results/phen_panel_district_season.csv

SHA-256:

    bfd5c7d8516004840c6e45928e631e52f039f276971df760b962af7369fbfce8  results/masked/phen_panel_district_season.csv
    6000f86b3f9851edff837ee8ffe036e0b85bade5328d33ef8ff88ee61858342b  results/masked/phen_panel_district_season_static.csv
    83d09e2e71c9fa0bfe5c7a0c54ccd0d3b55adff62c9b8051647f837af7770a95  results/masked_noovl/phen_panel_district_season.csv
    93a4cfc815ae78d13bc37657e6bc67c50d695acb674ef5307fcaaa0afe8a86f3  results/masked_noovl/phen_panel_district_season_static.csv
    ed68c7c9190fe316f03118437e106cd8debb4b5abaf823169fb376de92cc6a9b  results/phen_panel_district_season.csv

Internal counts each panel carries:

    results/masked/phen_panel_district_season.csv              rows 225  n_pixels/season 8085 (constant: True)  estimable 210
    results/masked/phen_panel_district_season_static.csv       rows 225  n_pixels/season 8085 (constant: True)  estimable 210
    results/masked_noovl/phen_panel_district_season.csv        rows 225  n_pixels/season 8026 (constant: True)  estimable 211
    results/masked_noovl/phen_panel_district_season_static.csv rows 225  n_pixels/season 8026 (constant: True)  estimable 211
    results/phen_panel_district_season.csv                     rows 225  n_pixels/season 10000 (constant: True)  estimable 208

## What still cannot be reproduced from a clone, stated plainly

The masked **pixel** panels (~117 MiB for both variants) are not committed, so the
pixel-level half of §3.5's comparison still requires regeneration, and regeneration
requires the **225 raw Sentinel-1 exports** (`gee/s1_block.js`), which are also not
committed. `DATA_AVAILABILITY.md` previously said the masked panels came "from the
committed mask flags", which implied the flags were sufficient; they are not, and stage 13
of `run_all.sh` now calls `need()` on the raw exports as well so the runner stops at the
gate with that message instead of failing several commands later.

The **per-unit calculation** of §3.5 — the arm this document exists for — is reproducible from
the repository alone, because it is computed *from* the committed district panels. The
**panels themselves are not**: rebuilding them needs the raw exports. *Corrected 2026-09-14:
this read "the district-level half of §3.5 … is reproducible from the repository alone", which
is broader than the scope sentence this document opens with and contradicted it.*

The three `Table_SX_MaskPerUnit_withdrawnCompare_*` side tables are also not regenerable from
the repository, for the same reason: they exist to hold the withdrawn pixel-average
comparison, which is the whole point of their being separate files rather than columns.

## The method this document is really recording

Two claims of reproducibility failed here in one day, and **neither was caught by reading**.
The first — that the masked district panels existed — was caught by an external auditor running
`git ls-files` over the whole project. The second — that the main tables regenerate — was
caught by running the arm with `RICEBACI_ROOT` pointing at a directory containing only
committed files and comparing byte for byte. The rule that follows, now standing for this
project: **a reproducibility claim is established by executing it against committed files
only, never by inspecting the code, and never from the author's working directory.** That test
is cheap: it took one directory and three commands, and it found something four passes of
reading had not.
