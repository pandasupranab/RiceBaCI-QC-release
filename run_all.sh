#!/usr/bin/env bash
# =============================================================================
# run_all.sh -- reproduce every reported result for RiceBaCI-QC (Paper 2)
# =============================================================================
# Set RICEBACI_ROOT to the directory holding results/ and the export folders.
# Everything defaults to the paths the analysis was run with.
#
#   export RICEBACI_ROOT=/path/to/data
#   bash run_all.sh selftest      # every self-test, no data needed (~3 min)
#   bash run_all.sh all           # full analysis; 9,999-bootstrap pixel arm takes hours
#
# STAGES ARE IN DEPENDENCY ORDER. Slow stages expose resume only where the code
# can verify it safely; the shipped attrition tables come from clean no-resume
# runs. Several stages need Earth Engine exports or other external inputs that
# cannot be produced from this repository alone. Each such stage names and
# checks its required inputs, and the script stops rather than pretending.
# =============================================================================
set -euo pipefail
ROOT="${RICEBACI_ROOT:-/home/claude}"
RES="${RICEBACI_RESULTS:-$ROOT/results}"
PY="${PYTHON:-python}"
export RICEBACI_ROOT="$ROOT" RICEBACI_RESULTS="$RES"
FIGPY="${FIGURE_PYTHON:-$PY}"
REPO="$(cd "$(dirname "$0")" && pwd)"
DOCS="$REPO/docs"
cd "$(dirname "$0")/python" 2>/dev/null || cd "$(dirname "$0")"

say() { printf '\n=== %s ===\n' "$*"; }
need() { [ -e "$1" ] || { echo "MISSING INPUT: $1"; echo "  $2"; exit 2; }; }

# ---------------------------------------------------------------------------
# THE FIRST VERSION OF THIS FUNCTION COULD NOT FAIL.
#
# It printed PASS or FAIL per script and returned 0 either way, because every
# check was `if ... then echo PASS else echo FAIL fi`, whose exit status is that
# of the echo. The caller then read `selftest) selftests; exit 0 ;;` -- a
# hardcoded success. So `bash run_all.sh selftest` reported success even if all
# ten scripts failed, and the `all` path ran the whole analysis on code whose
# self-tests it had just watched fail. Every "self-tests pass" claim in this
# repository was unsupported by this runner.
#
# Found by an external audit on 2026-09-13, which had to invoke each script
# separately and read its exit code because this runner's verdict was worthless.
#
# Two states are now distinguished, because that audit's tenth script exposed the
# difference: make_figures.py did not fail an assertion, it could not start --
# `ModuleNotFoundError: No module named 'matplotlib'`. A missing dependency and a
# broken invariant are different facts and the old output called both FAIL. The
# same distinction was made in make_figures.py --verify for MISSING versus
# CHANGED, one hour before this defect was pointed out.
#
#   PASS   exit 0
#   FAIL   ran, an assertion did not hold  -> the code is wrong
#   ERROR  could not start (import error)  -> the environment is incomplete
#
# Either FAIL or ERROR returns non-zero and stops the pipeline.
#
# HOW TO VERIFY THIS GATE, correctly. The injection point matters and getting it
# wrong produces a test that cannot fail -- which is what the handoff shipped with
# this very patch, and what the executor caught:
#
#   WRONG:  printf '\nassert False\n' >> python/dispersion_test.py
#           Dead code. The module body ends with `if __name__ == "__main__":
#           sys.exit(main())`; main() returns, sys.exit raises SystemExit, the
#           process ends, and nothing after that line is ever reached. Measured:
#           exit 0, "PASS", gate silent.
#
#   RIGHT:  insert the failure INSIDE a code path --selftest executes, e.g. as the
#           first statement of selftest():
#             python3 - <<'EOF'
#             import re; p='python/dispersion_test.py'; s=open(p).read()
#             open(p,'w').write(re.sub(r'(def selftest\(\):\n)',
#                                      r'\1    assert False, "gate test"\n', s, 1))
#             EOF
#           Measured: dispersion_test.py FAIL, "1 FAILED", exit 1.
#
# For the ERROR branch, insert `import nonexistent_module_xyz` AFTER the
# `from __future__` line -- before it is a SyntaxError, which is a FAIL, not an
# ERROR, and miscounts.
# ---------------------------------------------------------------------------
selftests() {
  say "self-tests (no data required)"
  local nfail=0 nerr=0 out rc
  local bad_exposure_paths
  local selftest_modules=(
    lf_output extract_phenometrics_sar fit_phenometrics
    attrition_diagnostics attrition_completeness compare_tables claim_guard
    environment_check
    classify_exposure_phase make_figures event_study censoring_test
    permutation_test dispersion_test repeat_coverage_sensitivity
    orbit_agreement orbit_state_sensitivity orbit_pair_selection_sensitivity
    mask_sensitivity
    marc_agreement semivariance window_sweep inundation_intensity
    gate1_justification gate2_state_sensitivity robustness_arms
  )
  # Every Python file must be accounted for. These files deliberately sit
  # outside the synthetic-test roster: two historical one-time migrations,
  # external-input builders/mergers, one long null-table generator, and two
  # long result drivers whose constituent estimators are tested elsewhere.
  # This is disclosure, not a claim that these files have self-tests. A new
  # module in neither list stops the runner before any PASS is printed.
  local exempt_modules=(
    apply_round2 apply_round3 build_coastal_districts build_cyclone_exposure
    calibrate_plsm_null merge_cohort_exports merge_static_covariates
    placebo_check
  )
  local unknown=() f stem found item
  for f in *.py; do
    stem="${f%.py}"
    found=0
    for item in "${selftest_modules[@]}" "${exempt_modules[@]}"; do
      if [ "$stem" = "$item" ]; then found=1; break; fi
    done
    if [ "$found" -eq 0 ]; then unknown+=("$f"); fi
  done
  if [ "${#unknown[@]}" -ne 0 ]; then
    echo "  UNREGISTERED Python module(s): ${unknown[*]}"
    echo "  add a --selftest or document the module in exempt_modules"
    return 1
  fi
  # The runner changes directory to python/ before executing stages.  A bare
  # docs filename therefore cannot resolve.  This exact defect previously made
  # the attrition stage die before it reached any of its scientific checks.
  bad_exposure_paths=$(grep -n -E '^[[:space:]]*--exposure[[:space:]]+.*district_cyclone_exposure_ibtracs50km.csv' \
      "$REPO/run_all.sh" | grep -v '\$DOCS/' || true)
  if [ -n "$bad_exposure_paths" ]; then
    echo "  RUNNER PATH FAILURE: exposure catalogue is not rooted at \$DOCS"
    printf '%s\n' "$bad_exposure_paths" | sed 's/^/        /'
    return 1
  fi
  echo "  registry: ${#selftest_modules[@]} self-tested; ${#exempt_modules[@]} explicitly exempt"
  # lf_output runs FIRST: it is the guard that keeps every committed CSV and JSON
  # LF-terminated on every platform, and its self-test scans the other modules'
  # source to confirm none of them can bypass it. Added 2026-09-14 after an
  # external auditor regenerated three tables on Windows and got CRLF, the same
  # values and a different md5 -- which would have broken every md5 check in
  # every handoff for any Windows reproducer.
  for s in "${selftest_modules[@]}"; do
    printf '  %-28s ' "$s.py"
    # `if out=$(...)` keeps set -e out of this, and captures output either way.
    local testpy="$PY"
    [ "$s" = make_figures ] && testpy="$FIGPY"
    if out=$("$testpy" "$s.py" --selftest 2>&1); then
      rc=0
    else
      rc=$?
    fi
    if [ "$rc" -eq 0 ]; then
      echo PASS
    elif printf '%s' "$out" | grep -qE "ModuleNotFoundError|ImportError"; then
      echo "ERROR -- could not start"
      printf '%s' "$out" | grep -m1 -E "ModuleNotFoundError|ImportError" \
        | sed 's/^/        /'
      nerr=$((nerr + 1))
    else
      echo "FAIL"
      # Show the FAILING lines, not just the tail. Until 2026-09-14 this printed
      # `tail -4`, which for a module whose failures are early in the output showed
      # only the closing banner -- a receive-only executor reported "FAIL" with no
      # way to say what failed, and the round trip cost a patch. Print every [FAIL]
      # line, then the tail for context.
      { printf '%s' "$out" | grep -F "[FAIL]" | sed 's/^/        /'; } || true
      printf '%s' "$out" | tail -3 | sed 's/^/        /'
      nfail=$((nfail + 1))
    fi
  done
  if [ "$nfail" -gt 0 ] || [ "$nerr" -gt 0 ]; then
    echo ""
    echo "  $nfail FAILED (an assertion did not hold -- the code is wrong)"
    echo "  $nerr ERRORED (could not start -- install requirements.txt)"
    return 1
  fi
  echo "  all ${#selftest_modules[@]} registered self-tests passed"
  return 0
}

case "${1:-all}" in
selftest) if selftests; then exit 0; else exit 1; fi ;;
all) : ;;
*) echo "usage: run_all.sh [selftest|all]"; exit 1 ;;
esac

# A gate, not a greeting. The previous version printed the results and carried on
# regardless, so the analysis could run on code that had just failed its own
# invariants.
if ! selftests; then
  echo ""
  echo "*** STOP *** refusing to run the analysis on code whose self-tests do not"
  echo "pass. Fix a FAIL; for an ERROR, install requirements.txt. Nothing was run."
  exit 1
fi
$PY environment_check.py --profile analysis --receipt "$RES/analysis-environment.json"
$PY claim_guard.py --root ..

say "1. verify separately rebuilt exposure catalogues"
VARIANTS="${EXPOSURE_VARIANT_DIR:-$RES/expo_var}"
echo "  build with robustness_arms.py --rebuild using the archived roster, GADM and IBTrACS."
$PY robustness_arms.py --verify-catalogues --variant-dir "$VARIANTS"
REFERENCE_RESULTS="${FROZEN_REFERENCE_RESULTS:?set FROZEN_REFERENCE_RESULTS to the archived pre-run panel directory}"
need "$REFERENCE_RESULTS/phen_panel_sar.csv" "the archived reference pixel panel, separate from the new run's results"
if [ "$RES" -ef "$REFERENCE_RESULTS" ]; then
  echo "STOP: frozen reference must not be the directory this run overwrites"
  exit 2
fi

say "2. phenometrics: PLSM on the combined-orbit exports"
need "$ROOT/s1full" "the 225 S1 panel exports (gee/s1_block.js)"
$PY extract_phenometrics_sar.py --exports "$ROOT/s1full" --out "$RES"
need "$ROOT/s1static" "the cohort static-covariate exports required by both analysis panels"
for base in phen_panel_sar phen_panel_district_season; do
  $PY merge_static_covariates.py --static "$ROOT/s1static" \
      --panel "$RES/$base.csv" --out "$RES/${base}_static.csv"
done

say "3. exposure phase against baseline markers (§3.8 robustness arm)"
$PY classify_exposure_phase.py \
    --exposure "$DOCS/district_cyclone_exposure_ibtracs50km.csv" \
    --panel "$RES/phen_panel_district_season_static.csv" \
    --out "$RES/exposure_phase.csv" --storms-out "$RES/exposure_phase_storms.csv"

say "4. §3.8 B named-cyclone event stacks (H4)"
$PY event_study.py \
    --panel "$RES/phen_panel_district_season_static.csv" \
    --exposure "$DOCS/district_cyclone_exposure_ibtracs50km.csv" \
    --out "$RES" --boot 9999

say "5. §3.10 attrition diagnostics, BOTH levels, retained-only"
for lvl in district pixel; do
  panel="$RES/phen_panel_sar_static.csv"
  [ "$lvl" = district ] && panel="$RES/phen_panel_district_season_static.csv"
  # 9,999 at BOTH levels. Protocol section 3.8 and this script's own
  # attrition_diagnostics.py declare 9,999; until 2026-09-15 the pixel level
  # silently ran 999, so every pixel WCB p-value and interval in the package
  # came from a tenth of the declared resolution. n_boot_requested is now
  # recorded in every row so the shortfall cannot recur unnoticed.
  boot=9999
  # NO --resume HERE. The tables shipped with this package come from CLEAN
  # runs. (Corrected 2026-09-15: this comment used to call --resume "safe and
  # idempotent", which was never demonstrated. What --resume actually does is
  # compare a content-based run key and recompute the attrition-diagnostic
  # strata; the twfe-based families -- headline, ipsw, balanced, pretrend,
  # phase -- are NOT re-verified. That is a sampled provenance check, not
  # idempotence, and the difference matters for acceptance.)
  #
  # --balanced is mandatory because the declared descriptive sensitivity must
  # be reproducible. It is NOT a same-estimand cyclone composition comparator
  # and is not a primary robustness estimate.
  $PY attrition_diagnostics.py --level "$lvl" --panel "$panel" \
      --exposure "$DOCS/district_cyclone_exposure_ibtracs50km.csv" \
      --phase-exposure "$RES/exposure_phase.csv" \
      --out "$RES/s310_v2_$lvl" --boot $boot --balanced

  # The completeness gate, FAIL-CLOSED. Stops the pipeline on an unrecognised
  # status, a not-estimable row with no reason, a WCB estimate at any bootstrap
  # count other than 9,999, a duplicate key, a partial-only key, a field that
  # disagrees between the final and partial tables, a missing or extra stratum
  # key, or a comparator that was never run.
  #
  # --verify-aliases re-checks the hard-coded design alias against the live
  # panel. If it cannot run, that is a FAILURE, not a skip: an unverified
  # constant is exactly what the flag exists to prevent. `set -e` at the top of
  # this script means a nonzero exit here stops the pipeline.
  $PY attrition_completeness.py --level "$lvl" --dir "$RES/s310_v2_$lvl" \
      --out "$RES/s310_v2_$lvl" --event-study "$RES/Table_SX_EventStudy.csv" \
      --verify-aliases
done

say "5. §3.9 falsifiability: timing placebo at full bootstrap resolution"
$PY placebo_check.py | tee "$RES/placebo_check.log"

say "6. §3.9 spatial permutation, 2000 draws, both levels"
for lvl in district pixel; do $PY permutation_test.py --level "$lvl" --n-perm 2000; done

say "7. construct validity: the censoring test"
$PY censoring_test.py --refit
for lvl in pixel district; do $PY censoring_test.py --estimate --level "$lvl" --own; done
$PY censoring_test.py --collect
$PY permutation_test.py --level pixel --n-perm 2000 --with-censoring

say "8. §3.8 A declared robustness arms"
echo "  needs the variant catalogues from build_cyclone_exposure.py at"
echo "  75/48, 100/48 and 50/64 -- see §4.1.8."
for lvl in district pixel; do
  $PY robustness_arms.py --level "$lvl" --n-perm 2000 --boot 9999 \
      --variant-dir "$VARIANTS"
done

say "10. H1/H2 clause (b): within- vs between-pixel dispersion"
$PY dispersion_test.py
$PY repeat_coverage_sensitivity.py \
    --panel "$RES/phen_panel_sar_static.csv" --out "$RES/dispersion"

say "11. H1/H2 clause (a): between-orbit agreement"
need "$ROOT/s1_perorbit" "the 225 per-orbit exports (gee/S1_PER_ORBIT.js)"
$PY orbit_agreement.py --fit          # resumable per file
$PY orbit_agreement.py --agree
$PY orbit_state_sensitivity.py \
    --pairs "$RES/orbit_agreement/orbit_pairs.csv" \
    --exposure "$DOCS/district_cyclone_exposure_ibtracs50km.csv" \
    --out "$RES/orbit_agreement"
$PY orbit_pair_selection_sensitivity.py \
    --fits "$RES/orbit_agreement/per_orbit_fits.csv" \
    --state-map "$DOCS/candidate_cohort_v2.csv" \
    --out "$RES/orbit_agreement"

say "12. figures"
"$FIGPY" environment_check.py --profile figures --receipt "$RES/figure-environment.json"
"$FIGPY" make_figures.py --results "$RES" --out "$ROOT/figures"

# Gate, not decoration. --verify re-hashes every table each figure was drawn
# from and every figure file written, and exits non-zero on any mismatch. It is
# what catches a figure left behind by a corrected table -- the defect fixed in
# 1a93678, where fig5 was drawn at 11:08 against tables corrected at 15:15 and
# 15:52. Running it immediately after the figures should always pass; its value
# is on a later run, against a working tree someone has since changed.
# --strict here, but NOT for a reader on a fresh checkout: in a full run every
# figure input exists, so a missing one is a real problem. On a clean clone some
# inputs are excluded on size and a plain --verify correctly reports INCOMPLETE
# rather than FAILED. See DATA_AVAILABILITY.md.
"$FIGPY" make_figures.py --verify --strict --out "$ROOT/figures"

say "13. §3.5 mask-comparison arm against ESA WorldCereal"
need "$ROOT/s1_maskflag" "the 25 mask exports (gee/S1_MASK_FLAG.js)"
# Added 2026-09-14: --filter rewrites the RAW exports, so this stage needs them too.
# DATA_AVAILABILITY.md said the masked panels came "from the committed mask flags",
# which implied the flags were sufficient. They are not, and this gate now says so
# before the stage runs rather than failing several commands later.
need "$ROOT/s1full" "the 225 S1 panel exports (gee/s1_block.js) -- --filter masks these"
# The arm re-runs the COMMITTED estimator on a masked subset rather than masking
# the panel: the district panel is a PLSM fit to the district-season mean curve,
# not an average of pixel phenometrics, so the mean curve has to be rebuilt from
# masked pixels. See the module docstring for why this is not negotiable.
for ov in "" "--exclude-overlap"; do
  sfx=""; rsfx=""
  [ -n "$ov" ] && sfx="_masked_noovl" && rsfx="_noovl"
  [ -z "$ov" ] && sfx="_masked"
  $PY mask_sensitivity.py --filter $ov
  $PY extract_phenometrics_sar.py --exports "$ROOT/s1full$sfx"       --out "$RES/masked$rsfx" --jobs "${JOBS:-4}"
  for base in phen_panel_sar phen_panel_district_season; do
    $PY merge_static_covariates.py --static "$ROOT/s1static$sfx"         --panel "$RES/masked$rsfx/$base.csv"         --out "$RES/masked$rsfx/${base}_static.csv"
  done
  # --n-perm 2000 is REQUIRED, not optional. §3.9's declared inference for the
  # placebo cell includes the within-state permutation sensitivity. The
  # committed tables carry the ten permutation columns; without this flag a run
  # would silently write column-poorer tables and fail to reproduce them. The
  # first version of this stage omitted it. mask_sensitivity.py now refuses such
  # an overwrite rather than relying on this comment.
  for lvl in district pixel; do
    $PY mask_sensitivity.py --compare --level "$lvl" --n-perm 2000 $ov
  done
done
$PY mask_sensitivity.py --collect
# §3.5's per-unit arm. Requires a DiD coefficient for every district x cyclone unit;
# the 2026-09-13 attempt computed a before-after contrast instead and was confounded
# (81% of estimable units drew a control season from another severe exposure of the
# same district). Superseded by unit_did on 2026-09-14 and run for ALL THREE markers,
# not just trough. It was also absent from this runner until now, so the pipeline did
# not reproduce its own table -- see docs/Protocol_v1.md §3.5's amendment.
for mk in trough heading harvest; do
  # The COMMITTED table: committed inputs only (the district-season mean-curve panels),
  # so it regenerates from a clone with no Earth Engine account. Verified byte-identical
  # against a directory holding only committed files -- docs/verify_masked_panels.md.
  $PY mask_sensitivity.py --per-unit --marker "$mk"
  # The side table carrying the WITHDRAWN pixel-average comparison. Needs the masked
  # PIXEL panels, which exist at this point in the pipeline but are NOT committed, so it
  # is a separate file and a separate flag. Keeping it in the main table is what made
  # that table unreproducible from a clone.
  $PY mask_sensitivity.py --per-unit --withdrawn-comparison --marker "$mk"
done

say "14. H1c/H2c product agreement against MARC v1.0"
need "$ROOT/marc" "the MARC v1.0 NetCDF (NIES doi:10.17595/20230728.001, CC BY 4.0)"
$PY marc_agreement.py --marc-dir "${MARC_DIR:-$ROOT/marc/Rice_Calendar_Data_ver.1.0}" --out "$RES/marc"

say "15. §3.1/§3.4 Tier 1: semivariogram nugget against the between-orbit sigma"
$PY semivariance.py --out "$RES/semivariance"

say "16. §1.4 window sensitivity sweep, all five endpoints"
# The sweep is extraction plus tabulation. The 425 arm is the run with NO
# --window-end-doy at all: bins_within(425) == bins_within(None) == 55, so the
# no-truncation run is simultaneously the headline, the 425 endpoint and the
# control the other four are read against. Extracting it separately into
# sweep_control is deliberate -- it is what makes "does truncation-off reproduce
# the committed panel" a check rather than an assumption.
$PY extract_phenometrics_sar.py --exports "$ROOT/s1full" \
    --out "$RES/sweep_control" --jobs "${JOBS:-4}"
for E in 365 385 395 410; do
  $PY extract_phenometrics_sar.py --exports "$ROOT/s1full" \
      --out "$RES/sweep_$E" --jobs "${JOBS:-4}" --window-end-doy "$E"
done
# --committed points at the separately archived pre-run reference, NOT $RES,
# which stage 2 has just overwritten. Parsed equality is not byte identity.
$PY window_sweep.py --sweep-root "$RES" --out "$RES/window_sweep" \
    --committed "$REFERENCE_RESULTS"

say "17. §3.3 inundated_frac: the criterion against its own matched 2017 null"
need "$ROOT/s1_inund" "the 25 inundation exports (gee/S1_INUNDATION.js)"
# The verdict is WITHDRAWAL, measured, not assumed -- see docs/Protocol_v1.md §3.3's
# 2026-09-13 amendment. This stage is what produced it and is what a reader re-runs
# to check it. The module refuses to issue a verdict on the DECLARED window, whose
# reference and event windows overlap by 9 days; only the corrected postlandfall
# window is admissible. That refusal is the point, not an inconvenience.
$PY inundation_intensity.py --exports "$ROOT/s1_inund" --out "$RES/inundation"

say "18. §3.1's pre-declared Gate 1 justification test, all four criteria"
# Declared in §3.1 on 2026-09-09 and unrun until 2026-09-13. The panel is extracted a
# SECOND time with the gate ON, so this is the expensive stage. The verdict is REJECT
# and it is reported as a tested QC step, which §3.1 anticipates as "a result rather
# than a failure". --gate1-r on orbit_agreement runs the fourth criterion through the
# committed estimator rather than a copy of it, and gate1_justification.py assembles
# that criterion itself -- analysis in a shell heredoc cannot be self-tested.
$PY extract_phenometrics_sar.py --exports "$ROOT/s1full" \
    --out "$RES/gate1_on" --jobs "${JOBS:-4}" --gate1-r 0.50
for mode in --fit --agree; do
  $PY orbit_agreement.py --exports "$ROOT/s1_perorbit" \
      --out "$RES/orbit_gate1_on" $mode --gate1-r 0.50
done
$PY gate1_justification.py --off "$RES/phen_panel_sar.csv" \
    --on "$RES/gate1_on/phen_panel_sar.csv" \
    --orbit-off-dir "$RES/orbit_agreement" \
    --orbit-on-dir "$RES/orbit_gate1_on" \
    --out "$RES/gate1_justification"

say "19. §3.2's state-bounds question, in the only form the protocol supports"
# §3.2 declares a state-specific-bounds sensitivity but never specifies the bounds.
# Choosing them now would measure the choice rather than the data, so this reports the
# two questions the sensitivity was for: differential screening by state, and calendar
# plausibility against the bounds. See §3.2's 2026-09-13 amendment.
$PY gate2_state_sensitivity.py --panel "$RES/phen_panel_sar.csv" \
    --out "$RES/gate2_state"

# The earlier wording here was "no remaining Earth Engine dependency", which is false
# of a fresh clone: stages 2, 11, 13, 14 and 17 each call need() on an export directory
# this repository does not contain, and stage 14 needs the external MARC NetCDF. What
# is true is that no stage requires a NEW Earth Engine script to be written or run
# beyond the six in gee/ whose CONFIGs are committed. Corrected 2026-09-14 after an
# external re-audit pointed out that a reader would read the old line as "clone and go".
say "ALL STAGES RUN"
echo "  NOTE: this is not a from-clone reproduction. Stages 2, 11, 13, 14 and 17 need"
echo "  the Earth Engine exports named in DATA_AVAILABILITY.md (excluded on size) and"
echo "  stage 14 needs the MARC v1.0 NetCDF. Every script that produces them is"
echo "  committed in gee/ with the CONFIG that was run; none has to be written."
echo
say "done"
