#!/usr/bin/env python3
"""Semantic guard against reinstating withdrawn Paper 2 claims.

This is deliberately broader than a literal-string grep.  It scans current
repository text by paragraph and rejects several repeatedly revived claim
families: global hypothesis-failure summaries, automatic measurement-error
cancellation, agronomic identity for fitted radar breakpoints, independent-
accuracy language for relative orbit paths, unearned mechanism or registration
claims, and overstatements about test coverage. It also rejects optical
SOS/peak/EOS labels in live radar result-table cells. Paragraphs that
explicitly mark the wording withdrawn, superseded, historical or unsupported
are retained as audit history and are not treated as live assertions. Generated
text logs are scanned too: a corrected generator does not make an older,
contradictory committed transcript current.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

TEXT_EXT = {".md", ".txt", ".log", ".py", ".sh", ".js", ".json", ".csv"}
HISTORICAL_FILES = {
    "analysis/decisions_log.md",
    "analysis/deviation_log.md",
    "docs/LitGap_v0.1.md",
    "python/apply_round2.py",
    "python/apply_round3.py",
}
HISTORY_MARKERS = re.compile(
    r"\b(withdrawn|superseded|historical|correction|incorrect|false|"
    r"not true|not\s+called|does not support|does not prove|does not validate|"
    r"cannot establish|not sufficient|replaced)\b", re.I)
FORBIDDEN = {
    "all-hypotheses-fail": re.compile(
        r"\b(?:all|every)\s+(?:(?:five|5)\s+)?(?:predeclared\s+)?"
        r"hypoth(?:esis|eses)\b.{0,100}\b(?:fail|failed|not\s+met)\b", re.I | re.S),
    "five-hypotheses-fail": re.compile(
        r"\b(?:five|5)\s+(?:predeclared\s+)?hypotheses\s+"
        r"(?:all\s+)?(?:fail|failed|are\s+not\s+met)\b", re.I | re.S),
    "automatic-did-cancellation": re.compile(
        r"(?:\b(?:removed|cancel(?:s|led)?)\b.{0,80}"
        r"\b(?:any\s+)?difference[- ]in[- ]differences\b|"
        r"\bsystematic\s+measurement\s+bias\b.{0,100}\bcancels?\b|"
        r"\bmeasurement\s+consistency\b.{0,80}\b(?:is\s+)?sufficient\b)",
        re.I | re.S),
    "radar-breakpoint-as-agronomic-date": re.compile(
        r"(?:transplanting\s+date\s+estimated\s+independently\s+from\s+"
        r"separate\s+sentinel-1|cannot\s+move\s+(?:the\s+)?same\s+season(?:'s)?\s+"
        r"transplanting\s+date|(?:units['’]?\s+)?harvest\s+dates\s+are\s+"
        r"extrapolat|whose\s+harvest\s+date\s+is\s+therefore)", re.I | re.S),
    "orbit-independence-overclaim": re.compile(
        r"(?:implied\s+single[- ]measurement\s+sigma|most\s+(?:nearly\s+)?"
        r"independent\s+geometry|genuinely\s+independent.{0,80}different\s+orbit|"
        r"agreement\s+between\s+independent\s+relative\s+orbits|"
        r"orbits?\s+must\s+(?:stay|remain)\s+independent|"
        r"independent\s+instrument\s+path|estimated\s+independently.{0,80}relative\s+orbit)",
        re.I | re.S),
    "selftest-coverage-overclaim": re.compile(
        r"(?:every\s+analysis\s+script\s+carries.{0,40}--selftest|"
        r"every\s+file\s+has.{0,40}--selftest|"
        r"all\s+analysis\s+code\s*,?\s+each\s+with.{0,40}--selftest|"
        r"runner\s+discovers\s+its\s+current\s+roster)", re.I | re.S),
    "censoring-mechanism-overclaim": re.compile(
        r"(?:censoring\s+(?:test|diagnostic).{0,60}(?:attributes?|proves?|"
        r"diagnoses?|shows?\b.{0,60}\bresponds?)\b|"
        r"(?:the\s+)?mechanism\s+(?:is\s+)?(?:measured|"
        r"established|confirmed)\b|"
        r"coefficient\s+(?:is|therefore)\s+measuring\s+(?:the\s+)?"
        r"(?:fit|selection))", re.I | re.S),
    "registration-overclaim": re.compile(
        r"(?:\bthis\s+study\s+(?:was|is)\s+pre[- ]?registered\b|"
        r"\bpre[- ]?registered\s+IBTrACS\s+rule\b)", re.I | re.S),
    "coarse-product-identity-overclaim": re.compile(
        r"(?:\bMARC\b.{0,100}\b(?:proves?|confirms?|establishes?)\b.{0,80}"
        r"(?:true|agronomic|harvest|transplant)|"
        r"\bextrapolation\b.{0,80}\bcannot\s+be\s+a\s+cutting\s+date\b)",
        re.I | re.S),
    "mask-validation-overclaim": re.compile(
        r"(?:\bindependent\s+validation\s+of\s+the\s+(?:rice\s+)?layer\b|"
        r"\brice\s+extent\s+is\s+(?:consequently\s+)?independent\b|"
        r"\b2018\b.{0,80}\bpre[- ]treatment\s+(?:layer|mask)\b|"
        r"\b(?:breakpoints?|dates?)\b.{0,80}\bagronomically\s+correct\b)",
        re.I | re.S),
    "inundation-identification-overclaim": re.compile(
        r"(?:criterion\s+separates?\s+flood\s+from\s+speckle|"
        r"inundated_frac\s+carries\s+no\s+signal)", re.I | re.S),
}
OLD_RADAR_RESULT_LABEL = re.compile(
    r"(?:H3 family: beta_(?:pre|harv) on (?:SOS|peak|EOS)|"
    r"TIMING PLACEBO: beta_harv on SOS|"
    r"declares no value\): beta_harv on peak|"
    r"H1 clause \(b\): transplanting / onset|"
    r"H2 clause \(b\): harvest(?:,|$)|"
    r"supplementary: heading(?:,|$))")


def text_files(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {".git", "__pycache__"}]
        for name in files:
            if os.path.splitext(name)[1].lower() in TEXT_EXT:
                yield os.path.join(base, name)


def scan(root):
    hits = []
    for path in text_files(root):
        relpath = os.path.relpath(path, root).replace(os.sep, "/")
        # These two append-only logs intentionally preserve superseded wording.
        # Current claims live in the protocol, verdict file, code and reports,
        # all of which remain in scope.
        if relpath in HISTORICAL_FILES:
            continue
        if relpath.startswith("results/superseded"):
            continue
        try:
            text = open(path, encoding="utf-8").read()
        except UnicodeDecodeError as exc:
            hits.append((relpath, 1, "invalid-utf8",
                         "tracked text is not valid UTF-8: %s" % exc))
            continue
        if "\ufffd" in text:
            line = text[:text.index("\ufffd")].count("\n") + 1
            hits.append((relpath, line, "encoding-replacement-character",
                         "tracked text contains U+FFFD; regenerate it with an "
                         "explicitly compatible output encoding"))
        # Result tables must name the radar variables they actually contain.
        # Optical hypothesis wording (SOS/peak/EOS) belongs in the protocol,
        # never in a live CSV cell that stores trough/heading/harvest output.
        if relpath.endswith(".csv"):
            for line, value in enumerate(text.splitlines(), 1):
                if OLD_RADAR_RESULT_LABEL.search(value):
                    hits.append((relpath, line, "radar-output-optical-label",
                                 value[:220]))
            continue
        # Markdown/code comments typically keep one assertion inside one blank-
        # line paragraph.  This lets a dated withdrawal preserve the old text
        # without allowing the same words to stand alone elsewhere.
        paragraphs = re.split(r"\n\s*\n", text)
        offset = 0
        for paragraph in paragraphs:
            start = text.find(paragraph, offset)
            offset = start + len(paragraph)
            line = text.count("\n", 0, start) + 1
            for family, pattern in FORBIDDEN.items():
                if pattern.search(paragraph) and not HISTORY_MARKERS.search(paragraph):
                    hits.append((relpath, line, family,
                                 " ".join(paragraph.split())[:220]))
    return hits


def selftest():
    import tempfile
    cases = {
        "literal": "All five predeclared hypotheses fail for measured reasons.",
        "paraphrase": "Every hypothesis failed under the study criteria.",
        "did": "The same-direction error is removed by any difference-in-differences.",
        "construct": "A harvest-window storm cannot move the same season's transplanting date.",
        "construct_log": "A harvest-window storm cannot move the same season's transplanting date.",
        "encoding_log": "a damaged section marker: \ufffd3.9",
        "orbit": "This is genuinely independent -- different orbit and look direction.",
        "orbit_agreement": "Agreement between independent relative orbits establishes consistency.",
        "test_coverage": "Every analysis script carries a --selftest.",
        "censoring": "The censoring test attributes the association to estimator deformation.",
        "censoring_response": "The censoring test shows fitted breakpoints respond to the storm.",
        "mechanism_attribution": "The coefficient is measuring the fit or selection process.",
        "registration": "This study was pre-registered before analysis.",
        "coarse_identity": "MARC confirms the true agronomic harvest date.",
        "mask_validation": "Independent validation of the rice layer over this roster.",
        "mask_independence": "Rice extent is consequently independent of the study events.",
        "mask_pretreatment": "The 2018 rice mask is a pre-treatment layer.",
        "calendar_accuracy": "These breakpoint dates are agronomically correct.",
        "orbit_js": "// the orbits must stay independent for H1 to be a test.",
        "mask_json": '{"note": "The 2018 rice mask is a pre-treatment layer."}',
        "inundation": "The criterion separates flood from speckle on this coast.",
        "dispersion_labels": "trough,H1 clause (b): transplanting / onset,1.0",
        "result_labels": "pixel,trough,S_pre_season,H3 family: beta_pre on SOS,1.0",
    }
    ok = True
    with tempfile.TemporaryDirectory() as td:
        for name, value in cases.items():
            extension = {"result_labels": ".csv", "dispersion_labels": ".csv",
                         "construct_log": ".log", "encoding_log": ".log",
                         "orbit_js": ".js",
                         "mask_json": ".json"}.get(name, ".md")
            p = os.path.join(td, name + extension)
            open(p, "w", encoding="utf-8").write(value)
        open(os.path.join(td, "invalid_utf8.log"), "wb").write(b"\xff")
        hits = scan(td)
        families = {h[2] for h in hits}
        sabotaged_files = {h[0] for h in hits}
        cond = sabotaged_files == {"literal.md", "paraphrase.md", "did.md",
                                   "construct.md", "construct_log.log", "encoding_log.log",
                                   "invalid_utf8.log", "orbit.md", "orbit_agreement.md",
                                   "test_coverage.md", "censoring.md",
                                   "censoring_response.md", "mechanism_attribution.md",
                                   "registration.md",
                                   "coarse_identity.md", "mask_validation.md",
                                   "mask_independence.md", "mask_pretreatment.md",
                                   "calendar_accuracy.md",
                                   "orbit_js.js", "mask_json.json",
                                   "inundation.md",
                                   "dispersion_labels.csv",
                                   "result_labels.csv"} and \
            {"automatic-did-cancellation",
             "radar-breakpoint-as-agronomic-date",
             "orbit-independence-overclaim",
             "selftest-coverage-overclaim",
             "censoring-mechanism-overclaim", "registration-overclaim",
             "coarse-product-identity-overclaim",
             "mask-validation-overclaim",
             "inundation-identification-overclaim",
             "encoding-replacement-character",
             "invalid-utf8",
             "radar-output-optical-label"}.issubset(families)
        ok &= cond
        print("[%s] twenty-four claim/encoding sabotages are detected" %
              ("PASS" if cond else "FAIL"))
        p = os.path.join(td, "history.md")
        open(p, "w", encoding="utf-8").write(
            "Correction: the sentence 'all five hypotheses fail' is withdrawn.")
        remaining = scan(td)
        cond = {h[0] for h in remaining} == sabotaged_files
        ok &= cond
        print("[%s] an explicit withdrawal remains permissible history" %
              ("PASS" if cond else "FAIL"))
    return 0 if ok else 1


def main(argv=None):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=root)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    hits = scan(a.root)
    for path, line, family, excerpt in hits:
        print("[FAIL] %s:%d [%s] %s" % (path, line, family, excerpt))
    print("claim guard: %s" % ("clean" if not hits else "%d live hit(s)" % len(hits)))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
