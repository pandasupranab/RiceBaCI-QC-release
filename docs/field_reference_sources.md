# Field reference sources for H1

Author-endorsed 2026-09-04. This is the working H1 field-reference catalogue
for `docs/Protocol_v1.md` §2 (H1a: transplanting-date bias against Zhao et al.
2024 MARC; H1b: transplanting-date RMSE against MARC; H2a/H2b: same for harvest
date). Every entry has been retrieved and opened, and the direct quote below
comes from the retrieved PDF. Entries marked **NOT FOUND — to be revisited**
are gaps in the catalogue that further research passes should try to fill
before the manuscript's field-reference section is finalized.

## Provenance and confidence

- The three Odisha ICAR-CRIDA / OUAT district Agricultural Contingency Plans
  (Cuttack, Ganjam, Kendrapara) have been opened, and the "Section 1.12 Sowing
  window for 5 major field crops" table has been spot-checked against the
  downloaded PDF. High confidence.
- ICAR-NRRI / CRRI Technology Bulletin 62 (Sep 2009) has been opened via the
  Perplexity content-fetch gateway; the sandbox could not resolve the
  `icar-nrri.in` host for a direct `curl`, so the PDF is NOT locally archived
  under `docs/field_reference_pdfs/`. The URL resolves from a normal browser.
  Content confidence high; archival status incomplete — retry the download
  from a network that can reach `icar-nrri.in` and place the file next to the
  other archived PDFs.
- Every Odisha entry is jointly attributed to ICAR-CRIDA and the collaborating
  state agricultural university (OUAT Bhubaneswar) or ICAR institute (CRRI /
  ICAR-NRRI Cuttack). None of these are standalone "Package of Practices" or
  "Recommended Crop Calendar" documents issued directly by the Odisha
  Directorate of Agriculture & Farmers' Empowerment. This is a real caveat
  and any downstream manuscript sentence citing these should say
  "ICAR-CRIDA / OUAT Agricultural Contingency Plan for X district" rather than
  "the state extension crop calendar".
- West Bengal and coastal Andhra Pradesh have no endorsed entries in this
  pass — see the NOT FOUND sections below.

## Odisha

### Source 1: State: ODISHA Agriculture Contingency Plan for District: CUTTACK
- URL: https://www.icar-crida.res.in/CP/Orissa/OUAT,%20Bhubaneswar/Orissa%202-Cuttack%2031.05.2011.pdf
- Publisher / issuing body: ICAR-CRIDA in collaboration with OUAT, Bhubaneswar
  (URL path segment reads `.../OUAT, Bhubaneswar/...`). The PDF's page 1 lists
  sources including "SREP, ATMA Cuttack 2008-09" and "Orissa Agril. Statistic
  2008-09."
- Publication date: filename stamp `31.05.2011`; no publication date is
  explicitly printed on the extracted first page. Retrieved 2026-09-04.
- Geographic coverage: Cuttack district (coastal Odisha, East and South-Eastern
  Coastal Plain agro-climatic zone).
- What it gives: Section 1.12 "Sowing window for 5 major crops" gives rainfed
  and irrigated sowing windows for Paddy, Groundnut, Blackgram, Greengram,
  Sugarcane. No calendar-date harvest window; harvest recommendation is stated
  in physiological terms ("at physiological maturity stage").
- Direct quote (Paddy row):
  > "Kharif- Rainfed  May – June"
  > "Kharif- Irrigated  June – July"
- File format: PDF
- Locally archived: `docs/field_reference_pdfs/CRIDA_Odisha_Cuttack_31.05.2011.pdf` (483 KB)
- Citation form for the manuscript: ICAR-CRIDA in collaboration with OUAT
  Bhubaneswar. State: Odisha — Agriculture Contingency Plan for District:
  Cuttack. Dated 31 May 2011. Retrieved from icar-crida.res.in on 2026-09-04.

### Source 2: State: ODISHA Agricultural Contingency Plan for District: GANJAM
- URL: https://www.icar-crida.res.in/CP/Orissa/OUAT,%20Bhubaneswar/Orissa%2014-%20Ganjam%2031.05.2011.pdf
- Publisher / issuing body: ICAR-CRIDA in collaboration with OUAT, Bhubaneswar
  (URL path segment reads `.../OUAT, Bhubaneswar/...`).
- Publication date: filename stamp `31.05.2011`; no publication date explicitly
  printed on the extracted first page. Retrieved 2026-09-04.
- Geographic coverage: Ganjam district (coastal Odisha, North-Eastern Ghats
  and East and South-Eastern Coastal Plain zones).
- What it gives: Section 1.12 "Sowing window for 5 major crops" gives rainfed
  and irrigated sowing windows for Paddy, Groundnut, Blackgram, Greengram,
  Sugarcane. Also gives transplanting seedling age. Harvest window is stated
  as a physiological criterion, not a calendar-date range.
- Direct quotes (Paddy row + harvest criterion):
  > "Kharif – Rainfed  June-July"
  > "Kharif – irrigated  July –Aug"
  > "Harvesting of kharif rice at physiological maturity will realize 80-85%
  > of normal yield."
- File format: PDF
- Locally archived: `docs/field_reference_pdfs/CRIDA_Odisha_Ganjam_31.05.2011.pdf` (717 KB)
- Citation form for the manuscript: ICAR-CRIDA in collaboration with OUAT
  Bhubaneswar. State: Odisha — Agricultural Contingency Plan for District:
  Ganjam. Dated 31 May 2011. Retrieved from icar-crida.res.in on 2026-09-04.

### Source 3: State: ODISHA Agriculture Contingency Plan for District: KENDRAPARA
- URL: http://www.icar-crida.res.in/CP/Orissa/OUAT,%20Bhubaneswar/Orissa%2028-%20Kendrapara%2004.10.2011.pdf
- Publisher / issuing body: ICAR-CRIDA in collaboration with OUAT, Bhubaneswar.
- Publication date: filename stamp `04.10.2011`; no publication date explicitly
  printed on the extracted first page. Retrieved 2026-09-04.
- Geographic coverage: Kendrapara district (coastal Odisha, East and
  South-Eastern Coastal Plain zone).
- What it gives: Section 1.12 "Sowing window" (columns are 5 major field
  crops); rice row for Kharif-Rainfed given as a monthly range. Harvest
  recommendation stated in physiological terms; also describes "Completely
  drain the water from the field 15 days before harvesting period."
- Direct quote:
  > "Kharif- Rainfed  June – July"
  > "Rice may be harvest at physiological maturity stage."
- File format: PDF
- Locally archived: `docs/field_reference_pdfs/CRIDA_Odisha_Kendrapara_04.10.2011.pdf` (314 KB)
- Citation form for the manuscript: ICAR-CRIDA in collaboration with OUAT
  Bhubaneswar. State: Odisha — Agriculture Contingency Plan for District:
  Kendrapara. Dated 4 October 2011. Retrieved from icar-crida.res.in on
  2026-09-04.

### Source 4: CRRI Technology Bulletin 62 — Monthly Crop Calendar for Rice Cultivation
- URL: https://icar-nrri.in/wp-content/uploads/2018/07/75.-Crop-CalenderMonthly-Crop-Calender-for-Rice-Cultivation-_English.pdf
- Publisher / issuing body: "Published by The Director, for Central Rice
  Research Institute, Cuttack (Orissa) 753 006." CRRI was renamed ICAR-NRRI in
  2015; the document is currently hosted on the ICAR-NRRI domain.
- Publication date: printed "September, 2009" on the document. Retrieved
  2026-09-04.
- Geographic coverage: CRRI Cuttack — coastal Odisha as the primary field
  context; applicable across rainfed upland, transplanted wet-season, and
  rainfed lowland ecologies as classified in the bulletin.
- What it gives: month-by-month calendar of operations for transplanted
  wet-season rice, rainfed upland direct-sown rice, and rainfed lowland
  direct-sown rice. Includes nursery preparation month, transplanting month,
  and a harvest criterion tied to a calendar month (October for transplanted
  wet-season rice, at 95–100 DAT).
- Direct quotes:
  > "Do nursery bed preparation during early June for transplanting in
  > favourable lowlands / irrigated medium lands / coastal saline areas"
  > "Sow seed at 20 cm apart rows behind the country plough or by seed drill
  > during middle of June." (rainfed upland)
  > "Harvest the crop when 80 per cent of the grains in panicles got matured
  > (at physiological maturity stage)" — listed under October, 95–100 DAT for
  > transplanted wet-season rice.
- File format: PDF
- Locally archived: **NOT** archived locally in `docs/field_reference_pdfs/`.
  The sandbox could not resolve `icar-nrri.in` for a direct `curl` in this
  pass. The URL resolves and returns the document from a normal browser and
  from the Perplexity content-fetch gateway. Action item: retry the download
  from a network that can reach `icar-nrri.in` and archive the file under
  `docs/field_reference_pdfs/CRRI_TB62_Monthly_Crop_Calendar_Rice_Sep2009.pdf`
  before this catalogue is treated as fully archived.
- Citation form for the manuscript: Central Rice Research Institute (CRRI),
  Cuttack. Technology Bulletin 62 — Monthly Crop Calendar for Rice Cultivation
  (English). September 2009. Retrieved from icar-nrri.in on 2026-09-04.

## West Bengal

**NOT FOUND — to be revisited.**

No West Bengal source is endorsed in this pass. The ICAR-CRIDA / BCKV
Agricultural Contingency Plans for Murshidabad and North 24-Parganas that the
research pass surfaced (`.../BCKVV, Kalyani/...` on icar-crida.res.in, both
stamped 31-12-2011) are candidate future sources of the same joint-attribution
class as the Odisha entries above. They have not been endorsed here because a
West Bengal source that gives a calendar-date harvest window or is directly
attributable to the West Bengal Directorate of Agriculture is still preferred
before entry into the catalogue.

Search domains attempted so far (in the DRAFT research pass, 2026-09-04):
`agriculture.wb.gov.in`, `banglashasyabima.net`, `bckv.edu.in`,
`icar-crida.res.in` (WB series). None returned a state-DoA-issued district
crop calendar PDF within this pass. Next research pass should widen to
DAE-WB block-wise / sub-divisional publications and to Rice Research Station,
Chinsurah publications; if only ICAR-CRIDA / BCKV joint contingency plans are
findable after a second pass, promote them here with the same caveat as the
Odisha entries.

## Coastal Andhra Pradesh

**NOT FOUND — to be revisited.**

No coastal AP source is endorsed in this pass. The DRAFT research pass
identified three candidates but none survives endorsement:

- ICAR-CRIDA / ANGRAU Agricultural Contingency Plans for East Godavari
  (`.../AndhraPradesh/East Godavari.pdf`) and Krishna
  (`.../AndhraPradesh/Krishna.pdf`) on icar-crida.res.in. Both cover the
  Godavari and Krishna deltas and are candidate future sources of the same
  joint-attribution class as the Odisha entries. Not endorsed here pending
  either explicit ANGRAU issuance metadata on the first page or a companion
  ANGRAU zonal publication for the Godavari-Krishna-Guntur belt.
- ANGRAU RARS Tirupati "Recommendations for Rice Crop Production and Package
  of Practices for Kharif 2014 & Rabi 2014-15" (rarstpt.org). **Dropped:**
  zone mismatch. The document is scoped to ANGRAU's Southern Zone
  (Chittoor / Nellore / Kadapa / Anantapur / Kurnool), which is a distinct
  agro-climatic zone from the coastal AP Godavari-Krishna-Guntur delta belt
  where any Paper 2 pilot districts would sit. Not a distance issue — an
  agro-climatic-zone issue. Do not add to the catalogue.

Search domains attempted so far (in the DRAFT research pass, 2026-09-04):
`des.ap.gov.in`, `angrau.ac.in`, `rarstpt.org`, `icar-crida.res.in`
(AP series). None returned a coastal-AP-specific state-issued PDF within this
pass. Next research pass should target ANGRAU Regional Agricultural Research
Stations that serve the Godavari-Krishna-Guntur belt directly (RARS
Maruteru, RARS Lam / Guntur) and their public "Package of Practices" or
"Kharif crop plan" publications.

## Auxiliary / cross-state (not endorsed for H1 yet)

### PMFBY National Crop Calendar (2018)
- URL: https://pmfby.gov.in/pdf/New_Crop_Calendar_20.09.18.pdf
- Publisher / issuing body: Not printed on the document (hosted by Pradhan
  Mantri Fasal Bima Yojana at pmfby.gov.in). The `20.09.18` in the filename
  appears to be a version date (20 Sep 2018).
- Publication date: not printed on the extracted content. Retrieved 2026-09-04.
- Geographic coverage: all-India, resolved to state × district × crop ×
  season, with Sowing Period (From / To) and Harvesting Period (From / To).
- Why it is here but not endorsed: this is the only source in this pass that
  prints district-resolved harvest windows as calendar dates. In principle it
  could fill the Odisha harvest-window gap where CRIDA/OUAT documents stop
  at "physiological maturity." However, the LLM extraction in the research
  pass surfaced only one Bihar row; the specific Odisha / WB / coastal AP
  district rows of interest have NOT been spot-checked yet. Before this file
  is cited as an H1 harvest-window reference, the relevant district rows must
  be read from the PDF and quoted here.
- Locally archived:
  `docs/field_reference_pdfs/PMFBY_New_Crop_Calendar_2018.pdf` (5.21 MB)

## Archive manifest — what is in `docs/field_reference_pdfs/`, and what it means

**Added 2026-09-14 because the folder inverted this catalogue and nothing said so.**
`docs/field_reference_pdfs/` holds nine PDFs. Three are endorsed here, one is auxiliary,
and **five are explicitly NOT endorsed by this catalogue** — including one this catalogue
says in bold must not be added. The single document this catalogue *does* endorse but
could not retrieve is the one **absent** from the folder. So a reader browsing the
directory would find two West Bengal plans in a repository whose catalogue says West
Bengal is NOT FOUND, and an Andhra Pradesh document marked "Do not add". Retaining
retrieved candidates is deliberate and useful; leaving them **unlabelled** was not.

| archived file | status in this catalogue |
|---|---|
| `CRIDA_Odisha_Cuttack_31.05.2011.pdf` | **ENDORSED** — Source 1 |
| `CRIDA_Odisha_Ganjam_31.05.2011.pdf` | **ENDORSED** — Source 2 |
| `CRIDA_Odisha_Kendrapara_04.10.2011.pdf` | **ENDORSED** — Source 3 |
| `PMFBY_New_Crop_Calendar_2018.pdf` | **AUXILIARY, NOT ENDORSED for H1** — district rows of interest not yet read or quoted |
| `CRIDA_WestBengal_Murshidabad_31.12.2011.pdf` | **CANDIDATE, NOT ENDORSED** — West Bengal is NOT FOUND in this pass |
| `CRIDA_WestBengal_North24Parganas_31.12.2011.pdf` | **CANDIDATE, NOT ENDORSED** — as above |
| `CRIDA_AndhraPradesh_EastGodavari.pdf` | **CANDIDATE, NOT ENDORSED** — pending ANGRAU issuance metadata |
| `CRIDA_AndhraPradesh_Krishna.pdf` | **CANDIDATE, NOT ENDORSED** — pending ANGRAU issuance metadata |
| `ANGRAU_RARS_Tirupati_Rice_PoP_Kharif2014.pdf` | **DROPPED** — agro-climatic zone mismatch. This catalogue says "Do not add to the catalogue"; the PDF is retained only as the record of a rejected candidate and must not be cited |
| *(absent)* `CRRI_TB62_Monthly_Crop_Calendar_Rice_Sep2009.pdf` | **ENDORSED, NOT ARCHIVED** — Source 4; `icar-nrri.in` was unreachable from the sandbox. Outstanding action item |

**The rule this manifest sets:** a PDF's presence in `docs/field_reference_pdfs/` is **not**
endorsement. Only the numbered Sources above are endorsed, and only they may be cited.

**This manifest was checked against the repository index, not written from memory.** Every one
of the nine filenames above matches `git ls-files` exactly, and the tenth row's claim — that
CRRI Technology Bulletin 62 is absent — is confirmed by its absence from that index. Checking
it that way also found that `DATA_AVAILABILITY.md` carried no row for this catalogue or its
PDFs at all; one was added the same day.

## Provenance gap found 2026-09-14 — §3.4's AICRP citation is not in this catalogue

`docs/Protocol_v1.md` §3.4 Tier 2 bounds the fitted phenometrics against "the **AICRP
Agrometeorology** crop-weather calendars giving Kharif rice as Standard Meteorological
Weeks 25–42, approximately DOY 170–294". **No AICRP source appears anywhere in this
catalogue**, none has been retrieved, and none is archived. The four endorsed Odisha
sources give something different in kind: monthly *sowing* windows ("May – June",
"June – July", "July –Aug") and harvest stated only as a physiological criterion
("at physiological maturity stage"). **Neither an SMW range nor a calendar-date harvest
window is supported by any endorsed source in this file.**

That bound is also a constant in live code: `TROUGH_WINDOW = (170.0, 294.0)` in
`python/extract_phenometrics_sar.py`, whose comment attributes it to §3.4's AICRP
calendar. Its reach was traced rather than assumed, and it is **narrower than the first
draft of this section said**. The trace, call site by call site:

| arm | what bounds its trough search | source of that bound |
|---|---|---|
| **PLSM — the primary estimator, every reported coefficient** | `PIXEL_GRID_DOY["t1"] = (184.5, 304.5)` | the untreated 2017 baseline district-mean range, padded two dekads. Not a calendar |
| **crossing rule — superseded arm, `xr_*` panel columns** | `GATE2["trough"] = (155.0, 240.0)`, passed **explicitly** at the one production call site (line 1375) | §3.2's own windows |
| **trapezoid — superseded arm, `tz_*` columns** | §3.2 windows, structural | §3.2 |
| `extract_markers`' **default** | `TROUGH_WINDOW = (170.0, 294.0)` | §3.4's AICRP attribution — **the gap** |

So `TROUGH_WINDOW` is a **dead default**: the only production call overrides it, and the
four remaining callers are self-tests. It reaches **no committed output at all** — not the
primary panel, and not even the superseded `xr_*` columns, which the first draft of this
section wrongly said it produced. No number anywhere in this study rests on the AICRP
attribution. What survives is an unsourced constant carrying a citation this catalogue
cannot support, and it is recorded as one. Either an AICRP source is retrieved, quoted and
archived here, or §3.4's attribution is withdrawn and the default re-derived from an
endorsed source or from the 2017 baseline. Until then no manuscript sentence may attribute
a date bound to AICRP.

**A second defect fell out of the same trace, and it is not about sourcing.**
`docs/Protocol_v1.md` line 155 describes the trough as "minimum within the transplanting
window (DOY 170–294, §3.4's AICRP calendar)". **No live code path searches DOY 170–294.**
That sentence describes the behaviour of a default that is always overridden, so it is a
protocol sentence describing behaviour the code does not perform — the class of defect
§5 item 5 of the re-audit brief asks reviewers to hunt for. Both §3.4 Tier 2 and line 155
are amended this date; this file is the evidence they are amended against.

## Change log

- 2026-09-14: external re-audit confirmed all three gaps this file already declares —
  no endorsed West Bengal source, no endorsed coastal Andhra source, CRRI Bulletin 62 not
  locally archived. No change to any endorsement. Added: the **archive manifest** above,
  because five of the nine archived PDFs are not endorsed and nothing said so; and the
  **AICRP provenance gap**, because §3.4 cites a source this catalogue does not contain.
  Neither was raised by the re-audit; both were found while checking its third claim.
  The provenance-gap section was then **corrected the same day, before being committed**:
  its first draft said `TROUGH_WINDOW` produced the superseded `xr_*` columns. It does
  not — the one production call passes `GATE2["trough"]` explicitly, so the constant is a
  dead default reaching no output. Tracing that also found that `docs/Protocol_v1.md`
  line 155 describes a search window (DOY 170–294) that no live code path uses; §3.4
  Tier 2 and line 155 are both amended 2026-09-14.
- 2026-09-04: promoted from `docs/field_reference_sources_DRAFT.md` with
  author-endorsed decisions:
  - Odisha: accept the three ICAR-CRIDA / OUAT district contingency plans
    (Cuttack, Ganjam, Kendrapara) and CRRI Technology Bulletin 62 (Sep 2009),
    all cited with full joint attribution. CRRI Bulletin 62 kept with the
    note that the PDF is not locally archived (icar-nrri.in DNS could not be
    resolved from the sandbox; document is reachable from a normal browser).
  - Coastal Andhra Pradesh: drop the ANGRAU RARS Tirupati PoP entirely due to
    agro-climatic zone mismatch (Southern Zone vs. coastal delta), not
    distance. Mark the two ICAR-CRIDA / ANGRAU delta plans and the state
    overall as NOT FOUND — to be revisited.
  - West Bengal: mark as NOT FOUND — to be revisited rather than force a
    weak substitute from the DRAFT.
