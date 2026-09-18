# Re-audit brief — 2026-09-14, covering `2ae1bd2`, `b0f7a17`, `f3eca45`

Successor to `REAUDIT_BRIEF_2026-09-13.md`, which ended at `d14289d`. Three commits have
landed since. Everything the previous re-audit raised is now closed; **two further gaps
were found by auditing the protocol against `results/` rather than waiting to be told**,
and are closed too.

Read §4 first if time is short. It is the list of this project's own errors since the last
brief, four of them mine and one of them a published conclusion I had to withdraw.

---

## 1. The three commits

| commit | what it did |
|---|---|
| `2ae1bd2` | Ran §1.4's pre-declared five-endpoint window sweep; added the MARC agreement arm (H1c/H2c) and the semivariogram arm (§3.1/§3.4 Tier 1); rewrote the hypothesis verdict table; propagated dated corrections into the previous brief |
| `b0f7a17` | Withdrew §3.3's `inundated_frac` after testing it on 71 storm-district rows against 71 matched 2017 nulls |
| `f3eca45` | Ran §3.1's pre-declared Gate 1 justification test; corrected §3.2's false claim that Gate 2 excludes out-of-bounds pixels; refused §3.2's unspecifiable state-bounds sensitivity and recorded the refusal |

222 tracked files. `bash run_all.sh selftest` → **17 self-tests, all PASS, exit 0**.
`python/make_figures.py --verify` → **VERIFY PASSED**, every figure matches the tables it
was drawn from.

---

## 2. Disposition of the previous brief's findings

All closed. The two that needed real work:

- **§1.4's window sweep had never been run.** Now run at all five declared endpoints
  (DOY 365/385/395/410/425) and tabulated in `results/window_sweep/`.
- **The verdict table said "all five predeclared hypotheses fail".** Withdrawn as
  result-aware and replaced by `analysis/hypothesis_verdicts.md`, every figure checked
  against the committed tables. The accurate sentence: **one fails on its declared
  criterion (H4, 2 of 6); two fail on one clause while their other clause passes as
  declared (H1, H2 — clause (a) measures **0.9443 trough / 0.9387 heading / 0.9114
  harvest** against a declared 0.90); one is not estimable as declared (H3); one was
  withdrawn untested (H5).**
  Dated corrections are in the previous brief at §3, §3.2, §3.3 and §7 rather than
  rewrites.

---

## 3. The substantive results

### 3.1 The window sweep's positive finding: the timing placebo is not a design artefact

§4.1 withdraws every causal claim from §3.8 on the strength of §3.9's timing placebo —
β_harv on the trough breakpoint, declared zero. The sweep re-estimated it at all five
endpoints, a 60-day change in the compositing window, with the standing to overturn the
paper's central negative result.

**It measures +7.291 to +8.099 d with cluster-robust *t* between +3.80 and +4.30 at every
one of the five endpoints** — a total spread of **0.807 d**, the tightest cell in the
table. β_harv on heading holds sign and significance at four of five (*t* +1.81 at DOY 365,
the only one below 1.96); both `S_pre_season` cells on trough and heading are zero at every
endpoint (ranges 0.823 and 0.574 d).

### 3.2 The window sweep's defect finding: the harvest breakpoint is sometimes an extrapolation

The five-segment model's last segment falls from the plateau to *b₂* between *t₃* and *t₄*
and is flat afterwards. **A unit with no valid dekad after *t₄* identifies *b₂* only from
the fall slope extrapolated forward** — its harvest date is where the fitted fall *would*
reach baseline. `plsm_fit`'s determinant screen passes such a fit silently, so it cleared
every gate and nothing flagged it.

**17 of 208 estimable district-seasons (8.2%) at the DOY 425 headline; 125 of 204 (61.3%)
at Paper 1's DOY 365 core window.** Consequences: the harvest coefficient cannot be read
across the endpoints, and the 60-day extension is not a preference over Paper 1's window —
it is what identifies the harvest breakpoint at all. Re-estimating on the units with a
post-*t₄* observation preserves every material sign (β_pre on harvest −10.184 → −8.084,
*t* −2.08 → −2.12; β_harv on heading +6.183 → **+7.438**, *t* +2.51 → +3.10), so nothing
reported rests on an extrapolated harvest date. **The headline retention rule was not
changed on this basis** — changing a gate after seeing which units it would drop is the
discretion §3 exists to remove — and the arm is reported alongside.

### 3.3 §3.3's `inundated_frac` is withdrawn, on 18 units, against a rule fixed before the data existed

Full execution: 25 districts, 71 storm-district rows, each paired with the same calendar
window shifted to the untreated 2017 season, **113,600 pixel rows**, 19 columns, every
per-district row count matching its predicted value exactly.

| criterion | τ | median per-unit excess | perm p |
|---|---:|---:|---:|
| §3.3's declared 3 dB | 3.00 dB | **−0.0063** | 0.9385 |
| re-derived, null 95th | 5.45 dB | +0.00375 | 0.0845 |
| re-derived, null 99th | 8.11 dB | +0.0000 | 0.2594 |

The rule (in `python/inundation_intensity.py`'s docstring) required median excess
≥ +0.05 **and** p ≤ 0.05. Four independent lines:

> **Corrected 2026-09-14.** This sentence read "written before the export existed". That
> is **not accurate**: the rule was fixed after the Baleshwar two-probe verify run, whose
> output already showed the cyclone-arm and 2017-arm percentiles for a severe
> harvest-window storm, and **before the full 25-district export**. The threshold was
> deliberately weak and the author's judgement is that it was not tuned to the outcome,
> but the claim about *when* was stronger than the facts and was repeated in the protocol
> amendment and in `b0f7a17`'s commit message. Both are corrected.

1. The declared criterion's excess is **negative** — the untreated year flags more pixels.
2. **Not one unit of 18 reaches the threshold.** Largest anywhere +0.0375; 7 positive, 10
   negative, 1 zero.
3. **No threshold works.** Swept 15 values from 1 to 12 dB; best median excess +0.00375 at
   5 dB, negative below 3.5 dB. The failure is of the statistic, not the 3 dB value.
4. **The flagged drop has no physical timing.** Median flagged minimum **6.01 d** after
   landfall in the cyclone arm against **6.51 d** in the untreated arm (39.4% against 36.1%
   within five days). Uses no threshold and no rate comparison, so it is independent of 1–3.

Most favourable reading available anywhere, sought deliberately: 5.45 dB on the 16
scene-balanced units gives p **0.0418** with a median excess of **+0.0063** — six tenths of
one percent of pixels. Reported as the best case; two orders of magnitude below what an
intensity variable needs.

**Why it fails**: the criterion flags **3.3% to 22.3% of pixels in years with no cyclone at
all**. **Bibliographic correction, 2026-09-16:** the cited “Bouvet et al. 2018”
identity could not be resolved and is withdrawn; the physical signal statement
is now sourced to Phan, Le Toan & Bouvet (2021), DOI `10.3390/rs13050921`.
The low-backscatter water response is real, but transplanted Kharif paddy is
deliberately flooded every season.

**No reported estimate changes** — `inundated_frac` was to be *offered* to §3.8 A as a
secondary term and was never in any reported specification.

### 3.4 Gate 1 is rejected on the test §3.1 declared, not on a narrower measurement

| criterion | own retained set | fixed common subset |
|---|---|---|
| fit quality | **WORSENS** (0 / 2) | **WORSENS** |
| temporal stability | MIXED (1 / 2) | **WORSENS** (0 / 3) |
| spatial coherence | MIXED (2 / 4) | MIXED (2 / 4) |
| orbit agreement | MIXED (2 / 4), negligible | not evaluable at this level |

**0 of 4 improve.** The gate degrades the measurement rather than merely failing to help:
retention 0.3527 → 0.3378, median RMSR 1.9847 → 2.0292 dB, and on the **28,612
pixel-seasons retained by both arms** within-pixel dispersion rises on all three markers
(trough 22.68 → 23.24, heading 17.66 → 17.92, harvest 23.16 → 23.27 d).

### 3.5 One external comparison and one internal one — neither a validation

- **MARC (H1c/H2c).** Harvest breakpoint **+50.4 d** later than MARC's harvest date,
  positive in **all 25 districts**, MAD 3.1 d, 22 of 25 within ten days of the median.
  A near-constant seven-week lag is what a return-to-baseline breakpoint looks like against
  a cutting date.
- **Semivariogram (§3.1/§3.4 Tier 1).** Nugget **25.68 / 20.57 / 25.30 d** against the
  between-orbit σ of **25.90 / 19.82 / 25.79 d** — agreement within **0.8 d**. Coherence is
  regional, not field-scale: 0–4 km lags flat (spreads 1.78 / 0.61 / 0.54 d) against
  30.36 / 22.37 / 29.34 d at 64 km+.

  **What this comparison is, stated after three passes of correction.** The two numbers are
  **similar in this dataset**, and that is the whole claim. They are **not the same
  estimand**: a short-lag spatial semivariance mixes local variation in the true field with
  the spatially uncorrelated part of the error, while a between-orbit difference cancels
  whatever the two paths share, so there is no reason in principle for them to agree. Both
  read the **same Sentinel-1 panel** through the **same breakpoint estimator**, so neither is
  independent of a defect in the other and **neither validates the other**. Earlier versions
  of this brief called them "two independent confirmations", then "corroboration"; both are
  withdrawn, as is the phrase "an error scale" — the between-orbit quantity is a **scaled
  disagreement statistic**, not a measured error.

  **Corrected again 2026-09-14 (sixth pass), and this one was a direction error.** The
  paragraph above continued: "the nugget is an **upper bound** on structure-free error —
  it also contains genuine sub-kilometre field variability **and any spatially correlated
  component of the measurement error**." The clause in bold is the wrong way round. A
  spatially correlated error component very largely **cancels** from a difference between
  neighbouring pixels, so it is **missing** from the short-lag semivariance, not contained
  in it — which is exactly why that statistic cannot bound total measurement error.
  Simulated on 2026-09-14: constant true field, district-season shared error sd 25 d,
  independent error sd 5 d → short-lag root **5.0 d** against a per-pixel total error sd of
  **25.50 d**. What the statistic does bound from above, under an additive
  signal-independent model and at the population level, is the **spatially uncorrelated
  error component**, because genuine local field variation sits inside it. It is also the
  shortest interpretable **bin**, not a fitted zero-distance intercept. `semivariance.py`
  was closer than this brief but not exact either, and is corrected in the same pass.

### 3.6 §3.2's Gate 2 claim was false and is corrected

§3 says "Gate 2 (§3.2) and Gate 3 (§3.11) apply unchanged"; §3.2 says out-of-bounds pixels
are "flagged and excluded from the panel". **Neither is true of the primary estimator** —
`plsm_retain` applies no calendar window, deliberately, for the reason §3.2 itself gives.
§3.11 got this correction on 2026-09-12; §3.2 did not, until now.

Gate 2 rejects **0 of 5,184 / 0 of 17,886 / 0 of 8,671** pixel-seasons reaching it. Had the
bounds applied, **2 of 9 state × marker medians lie outside them** (trough in Odisha and
West Bengal, each 14.5 d above the 240 ceiling) and **9 of 9** have a 95th percentile beyond
the upper bound.

**The measured radar distribution sits outside Paper 1's optical bounds.** Measured trough
median **254.5**, mid-range of the 245–265 interval §3.2 predicted before this panel was
fitted, and above Paper 1's 240 SOS ceiling. Paper 1's optical calendar bounds do not align with Paper 2's radar breakpoint distribution and would censor many radar estimates if transferred across sensors. This demonstrates **non-transferability between these different measurands**. It does **not** establish that Paper 1's optical SOS bound was mis-specified, identify a true agronomic onset, or reinterpret Paper 1's support loss. Those questions require analysis of Paper 1's own optical measurements or an independent field reference.

*Withdrawn 2026-09-14 (eighth pass):* this paragraph read "**This confirms §3.2's own
prediction**", quoting "The ceiling sat below the **true onset**." Withdrawn — a radar
breakpoint cannot locate a true onset, and §4.3.1 authorises no identity between it and
Paper 1's optical SOS.

---

## 4. This project's own errors since the last brief

Listed because they are the best available evidence of where this work fails, and because
one of them is a conclusion that was published to the user and then withdrawn.

1. **A published conclusion, withdrawn.** After the first §3.3 dry-run export I reported
   that the drop statistic "carries no flood signal on this coast" and called the
   comparison clean because the scene counts were balanced. They were, and that confound
   was genuinely absent — but a **second, larger confound was present and unchecked**: the
   declared reference window [L−35, L−5] and event window [L−14, L+14] **overlap by 9
   days**, and an orbit whose scenes in both windows are the same acquisition yields a drop
   of exactly 0. The export carried that point mass on 9.8% of rows, **arm-asymmetric by up
   to 38×** (Fani 9.50% actual against 0.25% null). A comparison of two differently
   contaminated arms is not a comparison. **The negative result was withdrawn and
   re-derived on a corrected window.** The overlap was computable by arithmetic from the
   two declared window definitions before any export ran, and I did not do that arithmetic.
2. **A defect I authored in the protocol's own terms, and half of it is the protocol's.**
   Half the declared ±14-day event window lies *before* landfall, so the "flood minimum"
   could be a pre-storm acquisition. Measured once `win_min_day_off` existed: the median
   flagged minimum on the declared window fell **5.5 days before the storm**. Fixed to
   [L, L+14] under §3.3's own clause that "the window length [is] re-derived on the
   untreated 2017 baseline"; both specifications are exported and the declared one is
   marked inadmissible rather than silently replaced.
3. **I read approximate output as measurement, twice.** `ee.Reducer.percentile` is
   histogram-based. Across two runs of identical code over identical scenes the null arm's
   reported p50 moved **1.1149 → 1.0493 dB**, and neither equals the exact value from the
   exported CSV (**1.0235**). The gaps I was interpreting (0.44 dB, then 0.30 dB) are two
   to four times that instability. The verify block now reports **exact pixel counts** and
   labels percentiles as shape only. The mechanism for why one arm moved and the other did
   not is recorded as **unresolved** rather than guessed.
4. **A verification block that reported nothing, silently.** On the full 25-district run
   `dryRunDistrict` is `null`, and the verify probe keyed off that field — so it printed
   "none in null" for both probes. **The verify output was blank on the single run that
   mattered most, and it failed quietly rather than complaining.** Same class as a test
   that cannot fail. `CONFIG.probeDistrict` is now separate.
5. **A queued explanation that was wrong.** The decisions log recorded, explicitly as an
   untested hypothesis, that machine-epsilon differences between the committed panel and
   the sweep control came from multiprocessing chunk order. **Tested and refuted**: six
   runs crossing `--jobs` ∈ {1,2,4} with BLAS threads free and pinned give one md5. What
   replaced it is the measurement — every breakpoint, retention flag, failure reason and
   failure class bit-identical across 90,000 pixel-seasons, only dB levels differing at
   ≤ 3.55 × 10⁻¹⁵ — rather than another guess.
6. **A comparison that invented differences.** The first control-versus-committed check
   reported 31,741 differing rows in `fail_reason`, exactly the retained count. Artefact:
   `pd.NA != pd.NA` is `pd.NA`, which `.sum()` counted. Both sides were null on all 31,741
   rows. Guarded with a self-test.
7. **A verdict that answered a question nobody asked.** `gate2_state_sensitivity.py` first
   returned one verdict conflating differential screening with calendar plausibility, and
   reported "state-specific bounds MAY be needed" whenever a marker sat near a bound — even
   though nothing is excluded on those bounds. Split into two questions with self-tests.
8. **I mis-mapped my own numbers while verifying this brief, and the ambiguity that let
   me is real.** Checking every quoted figure against the committed tables, I asserted
   that clause (a)'s triple "0.9443 / 0.9114 / 0.9387" was ordered trough / heading /
   harvest and flagged it as wrong. It is not wrong: `Table_SX_OrbitAgreement.csv` carries
   its rows as **trough, harvest, heading**, and every place the triple appears with
   marker names attached — `analysis/hypothesis_verdicts.md`, §4.3 of the protocol,
   `analysis/decisions_log.md` — is correct. My assertion was wrong. **But the reason I
   made it is a genuine defect in the writing:** the σ triples in the same documents
   ("25.90 / 19.82 / 25.79", "25.68 / 20.57 / 25.30") *are* trough / heading / harvest,
   so two orderings are used for bare triples side by side. Where the triple appears
   without marker names — the 2026-09-13 brief at §3 and §3.3, and the deviation log's
   2026-09-13 correction note — a reader can mis-map it exactly as I did. The ordering is
   now stated explicitly at the head of the clause (a) table in
   `analysis/hypothesis_verdicts.md`, and this brief names the markers inline. Recorded
   because the author mis-reading his own table on re-reading is the strongest evidence
   that a reviewer would.
9. **A self-test that failed for a reason in the test.** `gate1_justification`'s
   sample-selection check selected quiet pixels on `trough` alone while the criterion spans
   three markers, so it read MIXED and failed. The code was right. Recorded in a comment
   beside it: a self-test that fails wrongly is as much a defect as one that cannot fail.

---

## 4b. What the 2026-09-14 external re-audit found, and how it was resolved

The brief above claimed the repository was closed. **It was not, and an external re-audit
was right about six findings out of seven** — the seventh could not be checked from the
author's environment. Every one was verified against the code and the committed tables
before being accepted. They are listed here rather than quietly fixed, because the
pattern matters: five of the six are places where the *writing* claimed more than the
*work* supported.

1. **Three files carried the withdrawn "all five hypotheses fail" verdict.** `README.md`,
   `analysis/test_classification.md` and `osf/README.md`. The 2026-09-13 correction was
   propagated into the previous brief and **nowhere else**, so the repository held three
   contradicting answers to its own central question. `README.md` also still claimed
   "eleven of eleven" self-tests against a runner carrying 17. All corrected, in place,
   each with a dated note saying what it used to say.
2. **§3.5's per-unit arm was not a DiD, and was confounded.** Detailed in §3.6 below;
   this is the substantive finding and it required new analysis, not new wording.
3. **"Rule fixed before the export existed" was inaccurate** — see the correction in §3.3
   above.
4. **Gate 1's statistics were a retrospective operationalisation** of predeclared domains
   — see §3.4 and the protocol's §3.1 correction of this date.
5. **Semivariance was oversold as independent validation** — corrected in §3.5 above.
6. **Reproduction documentation was stale**: `--per-unit` was never called by
   `run_all.sh`; the runner's closing line said "no remaining Earth Engine dependency"
   although five stages call `need()` on excluded export directories and one needs the
   external MARC NetCDF; `DATA_AVAILABILITY.md` said `gee/` held 7 files against an
   actual 9. All corrected.
7. **Crop-calendar evidence for West Bengal and coastal Andhra Pradesh** — reported as
   incomplete. **VERIFIED AND CONFIRMED, and it opened two further defects the re-audit did
   not raise.** The file was retrieved, checked byte-for-byte against the committed blob
   (`60d81d7`), and read in full. Confirmed as reported: no endorsed West Bengal source, no
   endorsed coastal Andhra Pradesh source (its one ANGRAU candidate explicitly dropped on
   agro-climatic-zone grounds), and CRRI Technology Bulletin 62 endorsed but **not archived**
   (`icar-nrri.in` unreachable). So the re-audit was **7 for 7**. The two further findings,
   both from reading the file rather than from the re-audit:

   **(a) The PDF folder inverted the catalogue, and nothing said so.**
   `docs/field_reference_pdfs/` holds nine PDFs. Three are endorsed, one is auxiliary, and
   **five are not endorsed** — including two West Bengal plans sitting in a repository whose
   catalogue says West Bengal is NOT FOUND, and one Andhra document the catalogue says in bold
   must not be added. The one document the catalogue *does* endorse but could not retrieve is
   the one **absent**. A reader browsing the directory would have drawn the opposite conclusion
   to the catalogue's. Retaining rejected candidates is deliberate and useful; leaving them
   unlabelled was not. Fixed by an **archive manifest** naming the status of each file and the
   rule that presence in the folder is not endorsement.

   **(b) §3.4 cites a source the catalogue does not contain — the AICRP calendar.** §3.4
   Tier 2 bounds the fitted phenometrics against "the AICRP Agrometeorology crop-weather
   calendars … SMW 25–42, approximately DOY 170–294". **AICRP appears zero times in the
   catalogue**; nothing AICRP has been retrieved or archived. The endorsed Odisha sources give
   something different in kind — monthly *sowing* windows and harvest only as "physiological
   maturity" — so no endorsed source supports an SMW range or a calendar-date harvest window.
   The attribution is now **suspended** in §3.4.

   **How far (b) reaches was traced, not assumed, and the answer narrowed twice.** The
   constant is `TROUGH_WINDOW = (170.0, 294.0)`. First reading: it defaults the superseded
   crossing arm, so no primary coefficient touches it. Checking the call site refuted even
   that — the one production call passes `GATE2["trough"] = (155.0, 240.0)` **explicitly**, so
   the `xr_*` columns do not use it either. It is a **dead default** whose only remaining
   callers are four self-tests, and **no committed number in this study depends on it**. The
   first draft of the catalogue's own gap section carried the wider claim and was corrected
   before being committed; the correction is dated in that file.

   **(c) That trace exposed a third defect, of the kind §5 item 5 asks for.** Protocol line
   155 describes the trough as "minimum within the transplanting window (DOY 170–294, §3.4's
   AICRP calendar)". **No live code path searches DOY 170–294** — the crossing arm searches
   §3.2's 155–240, the trapezoid is bounded by §3.2 structurally, and the primary PLSM
   estimator has no calendar window at all (`PIXEL_GRID_DOY["t1"] = (184.5, 304.5)`, derived
   from the untreated 2017 baseline, padded two dekads). That sentence was a protocol claim
   about behaviour the code does not perform. Withdrawn as a description, with what each arm
   actually searches stated in its place.

   **Also re-attached: the §6 field-reference precondition.** It required a three-state
   catalogue "before H1 is claimed for any state" — written when H1 was an *accuracy* claim.
   §2's rewrite of 2026-09-09 made H1/H2 measurement-consistency claims needing no field
   reference, and §4.2 resolved both without one. The precondition does not gate H1/H2 as they
   stand; it gates **H1c/H2c** and **§3.4 Tier 2**, where it now binds harder: the calendar
   leg is available for **Odisha only**, attributed to the named contingency plans rather than
   to "the state extension crop calendar", and **no three-state calendar-validation statement
   may be written**.

### 3.6 §3.5's per-unit estimate was rebuilt as a real DiD, and the correction was large

The first per-unit attempt computed **the exposed season minus that same district's other
seasons** — no comparison district. Measured harm: **38 of the 47 estimable units (81%)**
drew at least one control season from **another severe exposure of the same district**.
Re-estimated as a canonical 2 × 2 DiD against clean contemporaneous controls, the median
difference from the superseded quantity is **+5.6 d** on trough (max 25.4 d), +1.2 d on
heading, +3.4 d on harvest — so this was a wrong number, not a mislabelled one, and
relabelling it "descriptive" was rejected for that reason.

A control district counts as clean only with **no severe exposure in either the pre or the
post season**; median 8 clean controls survive per unit (range 5–24). **8 of 47** units
have a treated district that was itself severely exposed in its own pre-season and are
flagged accordingly. No inference is reported — one treated cluster.

**The §3.5 conclusion survives the correction**, which is why both estimates are reported
side by side: intersection minus primary has mean **+0.110 / −0.256 / −0.401 d** across
trough / heading / harvest, with signs agreeing in **46/47, 47/47 and 45/47** units. It now
runs for all three markers instead of trough alone, and from `run_all.sh` instead of only
by hand. Ten self-tests cover it, including one that plants a common trend and confirms
the DiD returns the planted effect (+8.000 d) where the superseded contrast returns
+11.333 d.

## 5. Where scrutiny is most wanted

1. **The §3.3 withdrawal.** Is the corrected window [L, L+14] against [L−35, L−5] the right
   fix, or does starting the event window exactly at landfall lose a same-day flood? Is
   14 days too short given a median of 4 acquisitions (6 of 36 unit-arms carry ≤ 2)? Would
   a per-orbit paired design beat max-over-orbits?
2. **The operationalisation of §3.1's four criteria.** §3.1 names them without fixing
   statistics; I chose one directional statistic per criterion and declared the choice in
   the module docstring. Are those the right statistics, and is "MIXED is not an
   improvement" the right reading of "retained only if it improves"?
3. **Refusing §3.2's state-bounds sensitivity.** Is refusing to invent unspecified bounds
   correct, or should bounds be derived from the §3.4 published calendars and the
   sensitivity run — accepting that the derivation happens after the results exist?
4. **The harvest-extrapolation share at the headline (8.2%).** I reported it and left the
   retention rule alone. Is that the right call, or does §3.11 need a declared amendment
   requiring a post-*t₄* observation, applied to all five endpoints together?
5. **Whether any test remains that cannot fail**, and whether any remaining claim in the
   protocol describes behaviour the code does not perform. §3.2 was one such; the audit
   method that found it (enumerate every sentence carrying declaration language, check each
   against `results/`) is recorded in the decisions log so it can be repeated.

---

## 6. Standing status

- **No manuscript Results, Abstract, Discussion or Conclusions have been written**, by
  instruction, pending this re-audit.
- Every item from the 2026-09-13 re-audit is closed, and the two gaps found by self-audit
  are closed.
- **Superseded 2026-09-14.** That claim was wrong: an external re-audit found six real
  problems, listed in §4b. The accurate statement after those fixes is narrower —
  every declared test has now been run, the three contradicting verdict files are
  synchronised, and the one known unverified item is the crop-calendar evidence of §4b.7.
- **Superseded again 2026-09-14, later the same day.** §4b.7 is now verified. The re-audit was
  right **7 of 7**, and verifying its seventh claim produced three further defects it had not
  raised — an unlabelled PDF archive that inverted its own catalogue, an unsourced AICRP
  citation in §3.4, and a protocol sentence (line 155) describing a search window no live code
  path uses. All three are fixed in place with dated notes. None touches a reported number: the
  constant behind the second and third was traced to a **dead default** overridden at its only
  production call site. The accurate statement now is that **no item from either re-audit is
  open**, and that the remaining gaps are the ones this project already declares of itself —
  no endorsed West Bengal or coastal Andhra calendar source, CRRI Bulletin 62 not locally
  archived, and no archival DOI before submission.
- **Superseded a third time, same day — and this one is the most embarrassing of the three.**
  Sweeping the repository *by meaning* rather than by phrase found the withdrawn "all five
  predeclared hypotheses fail" verdict still standing in **three further files**: §4.2.6 of the
  protocol, headed "Per-hypothesis status, **final**", which contradicts §4.2.2 above
  it and §4.2.7 three paragraphs below it; §4.3.1's "the verdict is unchanged: H3 NOT MET",
  which *argues* for the wrong verdict rather than merely stating it; and item 1 of
  `analysis/test_classification.md`'s reviewer checklist — a line telling the reviewer the
  withdrawn answer, inside a file whose table the first pass of this date had just corrected.
  **So it was six files, not three.** The external re-audit's finding 1 was therefore an
  understatement, and the first correction pass was incomplete in the same way it was
  correcting. All six now carry dated corrections and all point at
  `analysis/hypothesis_verdicts.md`, whose own claim that the protocol's amendments "point
  here" was false when written and is now true. No number changes. The method failure is
  recorded because it is the reusable part: **a phrase sweep does not find a claim restated in
  another shape, and the sweep must include the files already corrected in the same pass.**
- **Superseded a fourth time, 2026-09-14 — a SECOND external audit, on the pushed commit
  `292c4c0`, found three real defects in the §3.5 per-unit DiD that the first audit's fix had
  introduced.** The estimand was an average of pixel dates instead of the declared
  district-mean-curve fit (a rule written in the header of the very file the violation was
  added to, 570 lines above it); the clean-control window was two seasons instead of §3.8 B's
  three, which gave Titli 19 controls where the rule allows 5; and the roster was all nine
  severe storms instead of the declared six. All three verified and fixed. **The §3.5 per-unit
  conclusion is withdrawn**: over the 35 declared units the intersection-minus-primary
  difference is mean −7.39 / −0.67 / −1.59 d with signs agreeing 31/35, 22/35, 21/35, against
  the withdrawn 46/47, 47/47, 45/47. The district- and pixel-level §3.5 results are untouched
  and still hold. Two further findings came out of verifying it: §3.8 B's stated clean-control
  counts are inflated by two districts that are not in this study's panel (and
  `results/Table_SX_EventStudy.csv` has silently disagreed with them all along), and the
  structural fact underneath the whole thing — **§3.8 B's control rule leaves Titli with one
  usable control district, Fani and Bulbul with two** — which neither audit asked about and
  which matters more than any of the three defects. Full record in `analysis/deviation_log.md`.
- **Superseded a fifth time, 2026-09-14 — two reproducibility claims failed, and neither was
  caught by reading.** (a) The masked district-season panel that §3.5's per-unit arm reads was
  **never committed**; it existed only in the author's working environment, so the arm could not
  be reproduced from a clone while the amendment implied it could. Found by an external auditor
  running `git ls-files` across the whole project. The four district-level panels (274 KiB) are
  now committed; the masked *pixel* panels (~117 MiB) stay out. (b) Committing them was not
  sufficient: tested against a directory holding only committed files, the tables still differed,
  because two columns were computed from those uncommitted pixel panels. Those moved to an
  opt-in side file. (c) A third, wider defect came from the same audit: `pandas` defaults
  `to_csv`'s line terminator to `os.linesep`, so **every** committed CSV — 65 call sites in 22
  modules — would have regenerated with CRLF and a different md5 on Windows, as would four
  committed JSON files including `figure_provenance.json`. `python/lf_output.py` now pins LF and
  its self-test scans the other modules' source to keep it that way; the roster is 18.
  (d) Scope correction accepted from the auditor: row counts, pixel totals and nesting are
  consistency checks, not construction proofs — **the per-unit calculation is reproducible from
  the committed fitted district panels; reconstructing those panels still requires the archived
  raw exports.** The record of all of it is `docs/verify_masked_panels.md` and the fifth- and
  sixth-pass entries in `analysis/deviation_log.md`.
- **Five consecutive "closed" claims have now been falsified** — by an
  external re-audit, then by tracing a citation, then by sweeping a withdrawn verdict by
  meaning. No closure claim is made here. What is claimed is narrower and checkable: the two
  sweeps that found today's defects are named in `analysis/decisions_log.md` so a reviewer can
  re-run them, and both should be re-run before the manuscript's Methods are drafted.
- §4.1's withdrawal of every causal claim from §3.8 stands and is **strengthened**: the
  placebo it rests on is now the most window-robust cell in the study.
- What the study reports positively is a set of **measured disagreement statistics with their
  scope attached**: between-orbit disagreement of **25.90 / 19.82 / 25.79 d** on a single
  pixel-season in the selected paired sample, a **separate** Monte Carlo recovering planted
  breakpoints to **±1.3 d** on a *synthetic* district-season trajectory at an assumed 0.122 dB
  noise level, and MARC's **+50.4 d** harvest offset in all 25 districts. The two internal figures
  are **not commensurable and no ratio between them is reported**. *(Rewritten 2026-09-14, seventh
  pass: this bullet said "the instrument **resolves** district-season timing to about ±1.3 d …
  and **fails at a 30 m pixel** with σ ≈ 26 d". Both halves are withdrawn — a simulation is not a
  resolution, and the scale boundary was retired on the fourth pass, §1.5.4 item 1.)*
  *Corrected 2026-09-14 (third pass): this bullet read "that σ now confirmed by
  two methods sharing no arithmetic, with an external product (MARC, +50.4 d) and a withdrawn
  intensity variable both independently saying the fitted quantities are not the named ones."
  **§3.5 of this same brief withdrew exactly that phrase**, 270 lines above, and this bullet
  kept it — the identical propagation failure the re-audit found across three files, recurring
  a third time inside the file that documents it. Found by an external audit.* The defensible
  wording: an **internal spatial diagnostic** (the semivariogram's shortest-lag value) is
  **numerically similar** to the between-orbit statistic in this dataset. It is not the same
  estimand, not independent of it, and not a validation of it — both read one panel through one
  estimator. **MARC (+50.4 d) is genuinely external**; the withdrawn intensity variable is not,
  and "independently" is withdrawn for it. *(Corrected 2026-09-14, sixth pass, twice over: this
  bullet also ended "and the nugget is an upper bound", which §3.5 withdraws — that statistic
  bounds only the spatially uncorrelated error component, not total error — and it called the
  between-orbit quantity "an error scale", which §1.5.6 constraint 2 declines to grant. The same
  propagation failure, in the same file, a fourth and fifth time.)*
