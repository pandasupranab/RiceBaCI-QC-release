"""HISTORICAL one-time protocol migration; not current executable analysis."""
import re, sys
p = open('Protocol_v1.md').read()
def rep(old, new, count=1, regex=False):
    global p
    if regex:
        n = len(re.findall(old, p, flags=re.S))
        assert n == count, (old[:60], n)
        p = re.sub(old, lambda m: new, p, flags=re.S)
    else:
        n = p.count(old); assert n == count, (old[:60], n)
        p = p.replace(old, new)

# ---------- §1.1: replace the stacked "Control set" paragraph ----------
rep(r'Control set \(revised 2026-09-07; stacked clean-control design, see §3\.8\)\..*?\(column `n_clean_control_districts`\)\.',
'''**Exposure, treatment and controls (revised 2026-09-07; supersedes both the "same-district t ± 1, t ± 2 control years" rule and a stacked-clean-control wording drafted earlier the same day).** Treatment in Objective 4 is not assigned by hand from the table above. It is derived, before any phenology is extracted, from the full IBTrACS v04r01 North-Indian-basin catalogue by a fixed rule implemented in `python/build_cyclone_exposure.py` and committed as `docs/district_cyclone_exposure_ibtracs50km.csv`:

- A roster district is *exposed* to a storm in season *t* if its GADM v4.1 Level-2 polygon lies within 50 km of any segment of that storm's best track at which the IMD sustained wind (IBTrACS `WMO_WIND`; JTWC `USA_WIND` only where IMD is missing) is ≥ 34 kt — Paper 1's 50-km exposure buffer (RSASE-D-26-02830 §2.3), computed in EPSG:7755. Exposure is *severe* if that wind is ≥ 48 kt (IMD Severe Cyclonic Storm or stronger) and *minor* at 34–47 kt (IMD Cyclonic Storm).
- Each exposure carries a *timing class* from the month of the closest ≥ 34-kt fix: *pre-season* (April–July: disturbs land preparation and transplanting), *mid-season* (August–September) or *harvest window* (October–February of the following calendar year: disturbs maturation and harvest).
- The district × season exposure indicators used in §3.8 are the maxima over all catalogued storms in that season, so every district-season carries an exposure status and nothing is assumed untreated. Over the 27 extracted districts and seasons 2019–2025 (189 district-seasons) the catalogue gives 29 severe pre-season, 14 severe harvest-window and no severe mid-season district-season exposures (41 distinct district-seasons with severe exposure, from Fani, Bulbul, Amphan, Yaas, Michaung 2023, Dana 2024, Remal and Montha 2025) and 18 district-seasons with minor exposure only (Nivar 2020, Gulab 2021, Asani 2022, an unnamed 2022 storm).
- The six named cyclones in the table are the severe events with Indian landfall on this coast that motivated the study; they are the units of the event-level view (§3.8 B) and of the §4 sign table. `docs/cyclone_footprints_ibtracs50km.csv` lists, for each of them, every roster district's footprint status (severe exposure to that storm = treated), fringe status (minor exposure to that storm = dropped from that event's comparison) and clean-control status (no severe exposure to *any* catalogued storm in seasons t − 1, t, t + 1). Under this rule **Sitrang** (24 Oct 2022, landfall at Barisal, Bangladesh) exposes no roster district — its ≥ 34-kt track stays more than 50 km from every Indian roster polygon — and is therefore **not estimable as a treatment for this roster**; it remains in the table as a named event and is excluded from the H4 count (§2). Fani and Bulbul both fall in analysis year 2019, so Bulbul's two footprint districts (North and South 24 Parganas) also carry severe pre-season exposure from Fani; the exposure panel handles this additively and the event-level Bulbul estimate is flagged multi-exposure (§3.8 B).

**Analysis seasons.** Sentinel-2 seasons 2019–2025 (`CONFIG.years` in `gee/S2_QC_Ingest.js`; the 2025 season closes at the end of February 2026 and is complete). Remal's t + 1 season is 2025; no event window extends beyond the data. The HLS panel (§3.7) covers 2016–2025 and supplies the seasons before the §1.2 floor.''', regex=True)

# ---------- §2: H3 / H4 ----------
rep('''- **H3.** Difference-in-differences coefficients β for (Treated × Post) on SOS, peak NDVI date, and EOS are statistically significant at *p* < 0.05 by wild-cluster bootstrap (9,999 replications, district-clustered). Direction of the coefficient is a cyclone-specific hypothesis stated at §4 below.
- **H4.** The framework transfers across cyclones without re-tuning. Specifically, r values fixed in §3.1 hold for all six cyclones, and the null hypothesis "framework does not transfer" is rejected iff H3 holds for **at least four of six cyclones** at the *p* < 0.05 level.''',
'''- **H3 (revised 2026-09-07; pre-revision wording preserved in `analysis/decisions_log.md`).** In the exposure panel of §3.8 A, the severe pre-season exposure coefficient β_pre is positive and significant at *p* < 0.05 by wild-cluster bootstrap (9,999 replications, district-clustered, 27 clusters) for SOS, peak NDVI date and EOS, and the severe harvest-window coefficient β_harv is positive and significant at *p* < 0.05 for EOS. Directions are the timing-class hypotheses stated at §4 below.
- **H4 (revised 2026-09-07).** The framework transfers across states and cyclones without re-tuning. Specifically, (i) the r values fixed in §3.1 are used unchanged for all three states and all seasons, and (ii) in the event-level view of §3.8 B the point estimate β₀ for each estimable named cyclone (Fani, Bulbul, Amphan, Yaas, Remal; Sitrang is not estimable, §1.1) agrees in sign with §4 for **at least four of the five**. The earlier criterion — H3 significance for at least four of six cyclones — is retired: two of the named cyclones expose only two roster districts each, and cluster-robust inference with two treated clusters cannot reject at any conventional level whatever the true effect (MacKinnon & Webb, 2018, *Econometrics Journal* 21(2), 114–135), so that criterion could not have been met by construction. Significance is tested once, on the pooled panel (H3).''')

# ---------- §3.1 window note: DOY 150–304 ----------
rep('computed over the 31 core Kharif bins (DOY 152–304, bins 1–31 of the 55-bin window) exactly as locked above.',
    'computed over the 31 core Kharif bins (bins 1–31 of the 55-bin window, DOY 150–304; the locked rule\'s core window was written as 152–304 and moves two days earlier so that its bin edges coincide with the §1.4 grid — the r-values and the admission rule are untouched) exactly as locked above.')

# ---------- §3.7 / §5.1 HLS range ----------
rep('- HLS analysis year range: **2016–2023** (pre-2016 lacks S30 overlap).',
    '- HLS analysis year range: **2016–2025** (pre-2016 lacks S30 overlap; extended from 2016–2023 on 2026-09-07 to match the Sentinel-2 seasons of §1.1). Same §1.4 window.')
rep('- `RiceBaCI_QC_panel_HLS_v1.csv` — full HLS panel, same schema, 2016–2023.',
    '''- `RiceBaCI_QC_panel_HLS_v1.csv` — full HLS panel, same schema, 2016–2025.
- `docs/district_cyclone_exposure_ibtracs50km.csv` and `docs/cyclone_footprints_ibtracs50km.csv` — the pre-declared exposure and named-cyclone footprint tables of §1.1, generated by `python/build_cyclone_exposure.py` from IBTrACS v04r01 and GADM v4.1 and committed before extraction.''')

# ---------- §3.8 full replacement ----------
start = p.index('### 3.8 Difference-in-differences specification')
end = p.index('### 3.9 Falsifiability checks')
old38 = p[start:end]
pixel_bullet = [l for l in old38.split('\n') if l.startswith('- **Pixel fixed effects are deliberately not used')][0]
loa_note = [l for l in old38.split('\n') if l.startswith('**Level-of-analysis note')][0]
new38 = '''### 3.8 Objective 4 specification — exposure-panel TWFE (headline) and named-cyclone event-level view (revised 2026-09-07)

**A. Headline: district-season exposure panel.** All 27 extracted districts, all seasons 2019–2025, pixel-year observations; exposure indicators from `docs/district_cyclone_exposure_ibtracs50km.csv` (§1.1). For each phenometric *Y* (SOS, peak NDVI date, EOS), pixel *p* in district *i(p)* and season *t*:

\\[
Y_{pt} = \\alpha_{i(p)} + \\gamma_t + \\beta_{\\text{pre}}\\, S^{\\text{pre}}_{i(p),t} + \\beta_{\\text{harv}}\\, S^{\\text{harv}}_{i(p),t} + \\delta_{\\text{pre}}\\, S^{\\text{pre}}_{i(p),t-1} + \\delta_{\\text{harv}}\\, S^{\\text{harv}}_{i(p),t-1} + \\lambda_{\\text{pre}}\\, S^{\\text{pre}}_{i(p),t+1} + \\lambda_{\\text{harv}}\\, S^{\\text{harv}}_{i(p),t+1} + \\mu\\, M_{i(p),t} + \\varepsilon_{pt}
\\]

- `S^pre_{d,t} = 1` if district *d* had severe (≥ 48 kt within 50 km) pre-season exposure in season *t*; `S^harv_{d,t} = 1` for severe harvest-window exposure; `M_{d,t} = 1` for any minor (34–47 kt) exposure in season *t*, any timing class. No severe mid-season exposure occurs in the catalogue for 2016–2025, so no mid-season term is estimable and none is included; minor mid-season exposures enter *M*.
- **β_pre and β_harv are the headline coefficients (H3).** δ (lag-1) tests persistence into the following season. λ (lead-1) is the pre-trend test: exposure in the *next* season cannot move this season's phenology, so a non-zero λ flags a violated parallel-trends assumption for that class (§3.9). μ is reported and carries no pre-declared sign.
- `α_{i(p)}` is a **district** fixed effect and `γ_t` a **season** fixed effect; the unit of observation is the pixel-year. This is the structure of Paper 1's Model 2 (RSASE-D-26-02830 §3: "the same equation at pixel-year resolution … α_d and γ_t retained as district and year fixed effects, and standard errors clustered at district level (G = 8)"; 6,850 retained pixel-years from 2,195 unique pixels), with Paper 1's single Treated × Post indicator replaced by catalogue-derived exposure indicators so that no district-season is assumed untreated. This closes the control-year contamination question recorded in `analysis/decisions_log.md`: Bulbul 2019 inside Amphan-2020's window, Fani 2019 and Yaas 2021 two seasons apart, and five further catalogued storms (Nivar 2020, Gulab 2021, Asani 2022, Michaung 2023, Dana 2024) striking roster districts in seasons the earlier rule treated as untreated controls.
''' + pixel_bullet + '''
- Standard errors clustered at **district** level (`i(p)`, 27 clusters), not pixel level — exposure is assigned at district level, and pixel-level clustering would understate the correct standard errors.
- **Wild-cluster bootstrap** with 9,999 replications (Roodman et al. 2019, `boottest`), clustered by district, reported as the headline inference.
- **Robustness (reported, never headline):** state × season fixed effects in place of `γ_t` (identification then uses within-state, within-season contrasts only); exposure buffer 75 km and 100 km in place of 50 km; severity threshold 64 kt (IMD Very Severe Cyclonic Storm) in place of 48 kt; the HLS panel 2016–2025 in place of Sentinel-2 (adds seasons 2016–2018, including Titli 2018).
- §3.10 (attrition diagnostic, IPSW, Lee bounds, balanced-composition check) applies with "treated" read as "severely exposed" and the stratum as district × season; the five estimable named cyclones remain the per-cyclone reporting units of §3.10 item 1.

**B. Event-level view: named-cyclone stacks.** For each estimable named cyclone *c* (§1.1: Fani, Bulbul, Amphan, Yaas, Remal), one stack is built following Cengiz, Dube, Lindner & Zipperer (2019, *Quarterly Journal of Economics* 134(3), 1405–1454): seasons *t_c* − 1, *t_c*, *t_c* + 1; treated = footprint districts; controls = clean-control districts of `docs/cyclone_footprints_ibtracs50km.csv` (no severe exposure to any catalogued storm in those three seasons), drawn from all three states because no named cyclone has three clean same-state coastal controls; fringe districts are dropped. With *k* = *t* − *t_c* and *k* = −1 as reference:

\\[
Y_{ptc} = \\alpha_{i(p),c} + \\gamma_{t,c} + \\beta_{0,c}\\,\\big(\\text{Treated}_{i(p),c} \\times \\mathbf{1}[k = 0]\\big) + \\beta_{+1,c}\\,\\big(\\text{Treated}_{i(p),c} \\times \\mathbf{1}[k = +1]\\big) + \\varepsilon_{ptc}
\\]

clustered by district across stacks. β₀,c is the per-cyclone estimate whose sign enters H4; β₊₁,c is persistence. The 2019 stacks (Fani, Bulbul) have no Sentinel-2 pre-season (§1.2 floor), so their headline substrate is the HLS panel; the Sentinel-2 version, which has only *k* ∈ {0, +1} and cannot separately identify β₀, is reported descriptively. Bulbul's two footprint districts are also Fani-exposed in 2019: the Bulbul estimate is flagged multi-exposure and read as the additional harvest-window effect. Per-cyclone counts (footprint / fringe / clean controls; Kolkata excluded): Fani 17 / 0 / 7; Bulbul 2 / 0 / 7; Amphan 5 / 0 / 10; Yaas 5 / 0 / 17; Remal 2 / 0 / 13. With two treated clusters for Bulbul and for Remal, no event-level significance claim is made (MacKinnon & Webb, 2018); event-level results are reported as point estimate, wild-cluster-bootstrap interval and flags.

''' + loa_note + '''

**Design history (2026-09-07).** This section was revised three times on one day, each time before any extraction: from district-year to pixel-year level; from a pixel fixed effect to Paper 1's district + year fixed effects; and from a drafted stacked clean-control design with hand-assigned footprints and same-state clean controls to the exposure panel above. The last step was forced by computing that draft from the IBTrACS catalogue before committing it: Fani's ≥ 48-kt track exposes 17 of the 18 Odisha and West Bengal roster districts, so no Odisha or West Bengal district is a clean control for any 2019–2021 event, and seven further catalogued storms strike roster districts in seasons the earlier rule treated as untreated. The exposure panel is the design that survives that check; the stacks are retained as the per-cyclone view.

'''
p = p[:start] + new38 + p[end:]

# ---------- §3.9 ----------
rep(r'- \*\*Placebo cyclones \(spatial\)\.\*\* For each treatment cyclone, re-estimate its stack.*?β₊₁ and β₊₂ are reported as persistence estimates, not as placebos\.',
'''- **Lead test (pre-trends).** λ_pre and λ_harv in §3.8 A must be indistinguishable from zero (wild-cluster bootstrap *p* > 0.10). A non-null lead for a class flags that class's β as descriptive only.
- **Timing placebo (built into the design).** Severe harvest-window exposure cannot move the same season's transplanting date or peak: β_harv on SOS and on peak NDVI date must be indistinguishable from zero. A non-null β_harv on SOS indicates selection or mis-specification, not a cyclone effect.
- **Permutation inference (spatial placebo).** Exposure histories are randomly re-assigned across districts within each state (2,000 permutations, preserving each season's count of exposed districts) and β_pre, β_harv re-estimated; the permutation *p*-value is reported beside the wild-cluster-bootstrap *p*-value. This replaces the earlier "interior district" placebo, which presupposed unexposed interior districts that the coastal roster does not contain, and the earlier "shift the treatment year" placebo, which under the retired control-year rule often landed on another storm's season.''', regex=True)

# ---------- §3.10 item 1 ----------
rep('Replicate Paper 1\'s Table S4 specification independently for each of the six cyclones (Fani, Bulbul, Amphan, Yaas, Sitrang, Remal), reporting',
    'Replicate Paper 1\'s Table S4 specification for each severe-exposure class (pre-season, harvest window; §3.8 A) and independently for each of the five estimable named cyclones (Fani, Bulbul, Amphan, Yaas, Remal; Sitrang exposes no roster district, §1.1), reporting')

# ---------- §3.11 implementation note ----------
rep(r'\*\*Implementation note \(2026-09-07\)\.\*\* This requires one new numeric column \(`rmsr`\).*?at no cost to work already done\.',
'''**Implementation note (2026-09-07; corrected the same day).** `rmsr` and `gate3_pass` are computed in the Python fitting stage, not in Earth Engine — `gee/S2_QC_Ingest.js` is extraction-only (its own architecture note: no fits, no Gate 1, no DiD; all of that runs locally in Python), and curve fitting happens after the dekadal aggregation of the §3 lead-in. They are columns of the per-pixel phenometric output table alongside SOS/POS/EOS, not of the 13-column export schema (§3.6), which is unchanged. An earlier version of this note placed them in the export path; that was wrong.''', regex=True)

# ---------- §4 ----------
rep('''Each treatment coefficient β is signed a priori:

| Cyclone | Expected β_SOS | Expected β_peak | Expected β_EOS |''',
'''**Exposure-class predictions (headline, §3.8 A; tested by H3).** β_pre > 0 for SOS, peak NDVI date and EOS (delayed transplanting, delayed peak, delayed harvest). β_harv > 0 for EOS (harvest disruption) and β_harv = 0 for SOS and peak NDVI date (the timing placebo of §3.9). No sign is declared for δ, λ or μ.

**Named-cyclone predictions (event-level, §3.8 B; enter H4 as sign agreement of β₀,c).** Each named cyclone's coefficient is signed a priori:

| Cyclone | Expected β_SOS | Expected β_peak | Expected β_EOS |''')
rep('| Sitrang (Oct 2022, harvest window) | Not applicable | Not applicable | Positive |',
    '| Sitrang (Oct 2022, harvest window) | Not estimable | Not estimable | Not estimable — no roster district within 50 km of the ≥ 34-kt track (§1.1) |')
rep('Cyclones that make landfall in the harvest window are tested only against β_EOS.',
    'Cyclones that make landfall in the harvest window are tested only against β_EOS. Sitrang is retained in the table as a named event but contributes nothing to H4 (§2).')

open('Protocol_v1.md', 'w').write(p)

# ---------- GEE years ----------
g = open('S2_QC_Ingest.js').read()
old = '  years: [2019, 2020, 2021, 2022, 2023],'
assert g.count(old) == 1
g = g.replace(old, '  years: [2019, 2020, 2021, 2022, 2023, 2024, 2025],  // Protocol §1.1: S2 seasons 2019–2025 (2025 closes Feb 2026)')
open('S2_QC_Ingest.js', 'w').write(g)
print('protocol + gee edits applied')
