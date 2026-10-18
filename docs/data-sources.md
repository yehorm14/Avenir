# Data sources: what to fetch and how

*Checked 17 Oct 2026, evening. The machine-readable list is `data/manifest.yaml`; this page explains it.*

## Fetch plan

| Data | How | Command or link | Notes |
| --- | --- | --- | --- |
| ESCO v1.2 (occupations, skills, occupation-skill relations) | Browser (download form, link by email), then `make data-sync` | esco.ec.europa.eu, "Download" page | CSV bundle, English; maps to ISCO-08 |
| ONS ASHE Table 14, 2011 to 2025 | Script | `python scripts/fetch/ons_ashe.py --years 2011-2025` | All editions on one ONS page; zip per edition |
| ONS SOC 2010 ↔ SOC 2020 relationship tables | Script | `python scripts/fetch/ons_files.py soc2010_soc2020` | Two .xlsx files, July 2021 versions |
| ONS SOC 2010 → ISCO-08 | Script | `python scripts/fetch/ons_files.py soc2010_isco08` | The only official ISCO file (see below) |
| APS employment by occupation | Script (Nomis API, no key) | `python scripts/fetch/nomis_aps.py NM_218_1 --describe` then fetch | Two datasets, see below |
| ILO GenAI exposure 2025 | Browser (PDF), then hand-extract | ILO WP140 publication page | No CSV found; Annex Table A1 |
| Occupations in Demand 2025 | Script: `scripts/fetch/oid_demand.py` | Explore Education Statistics | Covers the UK, not just England (see below) |
| Adzuna | Script on a laptop, keys in `.env` | `make adzuna` | Not needed on the cluster |

Then `make data-check` on both machines and compare `data/manifest.lock.json`.

## What changed from the spec after checking

1. **ASHE Table 14.** One ONS page holds every edition from 1997 to **2025 provisional**,
   one zip per edition. Its URL says `soc2010` for every year. The 2011 revised edition is the
   SOC 2010 one (the 2011 provisional is SOC 2000). Editions from 2021 should be SOC 2020:
   check the notes inside the files before joining. The 2026 edition is due this month; check.
2. **APS on Nomis is two datasets, not one.**
   - `NM_218_1` (APS218): SOC 2020, down to 4-digit, latest period Apr 2025 to Mar 2026.
   - `NM_168_1` (APS168): SOC 2010, down to 4-digit, latest period Jan to Dec 2021.
   So the backtest (years 2010 to 2019, demand trend Y−4 to Y) uses APS168 plus the relationship
   tables; the current demand trend uses APS218. APS168's earliest period is not stated on its
   page (revisions start July 2011), so trends before about 2012 may need the ONS EMP04
   spreadsheets (2001 to 2018, discontinued; check their SOC level).
3. **A SOC 2020 → ISCO-08 map can be built from the ONS coding index.** ONS publishes no simple
   mapping file (it says there is none even at unit group level) and links only a SOC 2010 →
   ISCO-08 file. But the ONS SOC 2020 coding index gives each job title both a SOC 2020 and an
   ISCO-08 code, so a SOC 2020 → ISCO-08 map with shares can be built from it (Arsenii's
   `crosswalk_build.py`; source `soc2020_coding_index`). The SOC 2020 → SOC 2010 → ISCO-08 route
   (relationship tables, then `soc2010_isco08`) stays as a cross-check, and a person approves each
   of our 20 occupations in `data/curated/occupations.csv` (`verified_by`).
4. **SOC 2010 ↔ SOC 2020 tables are percentages, not a lookup.** They come from people coded to
   both (LFS 2014 to 2016, 2011 Census 1% sample). Use the largest share for the bridge and mark
   splits and merges low confidence.
5. **ILO WP140 has no downloadable table.** The paper puts occupation means, SDs and gradients
   in Annex Table A1. The author's web page is a chart only. Extract the rows we need into
   `data/curated/ilo_exposure.csv` and check every row against the PDF.
6. **Occupations in Demand is UK-wide.** The data guidance says the index covers the UK labour
   market; the ASHE-based indicators are GB only. The spec labels it "England": label it
   "UK (some indicators GB)" instead. The "Occupations by demand" CSV (supporting file) already
   has demand level, index, worker numbers and imputation and uncertainty flags per 4-digit
   SOC 2020. Keep the 2024 original file for the track-record check. Symbols: `z`, `x`, `c`.

## Sources checked

- [ASHE Table 14 dataset page (ONS)](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/earningsandworkinghours/datasets/occupation4digitsoc2010ashetable14)
- [SOC 2010 and SOC 2020 relationship (ONS)](https://www.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/therelationshipbetweenstandardoccupationalclassification2010andstandardoccupationalclassification2020)
- [SOC 2020 to ISCO-08 (ONS)](https://cy.ons.gov.uk/methodology/classificationsandstandards/standardoccupationalclassificationsoc/soc2020/classifyingthestandardoccupationalclassification2020soc2020totheinternationalstandardclassificationofoccupationsisco08)
- [Nomis APS218, SOC 2020](https://www.nomisweb.co.uk/datasets/aps218) and [Nomis APS168, SOC 2010](https://www.nomisweb.co.uk/datasets/aps168)
- [ONS EMP04, employment by occupation](https://www.ons.gov.uk/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/datasets/employmentbyoccupationemp04)
- [ILO Working Paper 140](https://www.ilo.org/publications/generative-ai-and-jobs-refined-global-index-occupational-exposure) and [WP140 web page](https://webapps.ilo.org/static/english/intserv/working-papers/wp140/index.html)
- [Occupations in Demand 2025 data guidance](https://explore-education-statistics.service.gov.uk/find-statistics/occupations-in-demand/2025/data-guidance)

## ILO Working Paper 140: attribution and disclaimer

Checked 18 Oct 2026 against the copyright page of the [WP140 PDF](https://www.ilo.org/sites/default/files/2025-05/WP140_web.pdf); the publication page itself states no licence.

- **Licence:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)), © International Labour Organization 2025.
- **Citation:** Gmyrek, P., Berg, J., Kamiński, K., Konopczyński, F., Ładna, A., Nafradi, B., Rosłaniec, K., Troszyński, M. *Generative AI and Jobs: A Refined Global Index of Occupational Exposure.* ILO Working Paper 140. Geneva: International Labour Office, 2025. © ILO. https://doi.org/10.54394/HETP0387
- **What we changed:** Avenir's exposure score is an adaptation. ILO occupation scores are averaged over the ISCO-08 codes that each UK occupation maps to, then mapped to SOC 2020 (`packages/ml/README.md`, M2).
- **Disclaimer the licence requires with any adaptation:**

  > This is an adaptation of a copyrighted work of the International Labour Organization (ILO). This adaptation has not been prepared, reviewed or endorsed by the ILO and should not be considered an official ILO adaptation. The ILO disclaims all responsibility for its content and accuracy. Responsibility rests solely with the author(s) of the adaptation.

- The same page says the ILO emblem, name and logo may not be used in connection with adaptations: credit the source as above, but do not put the ILO logo or emblem next to Avenir's adapted score.


## Jobs evidence added 18 October 2026

- Skills England, Occupations in Demand 2025: latest release, updated 8 January 2026; next release December 2026. Exact categories for every rated SOC code are generated into apps/web/src/occupationDemand.ts by scripts/fetch/oid_demand.py. The index measures demand pressure, not proof of a worker shortage. https://explore-education-statistics.service.gov.uk/find-statistics/occupations-in-demand/2025
- Migration Advisory Committee, Temporary Shortage List Stage 2, 23 July 2026: relatively strong historical shortage evidence for electricians; mixed historical evidence and future shortage risk for plumbers. https://www.gov.uk/government/publications/temporary-shortage-list-stage-2-report/temporary-shortage-list-stage-2-report-accessible
- National Careers Service: starter-to-experienced salary guides, linked per role. No official two-year salary statistic is claimed. The editable scenario compounds starting pay with assumed annual increases and inflation; the default 5%/2% values are illustrative assumptions.
- Outlooks: Skills England's 2030 assessment and 2026 sector assessments; CITB's 2026–2030 construction outlook; explicitly labelled NHS and DfE sources. Published dates, horizons and geography remain visible. No forecast is extended to 2031. https://www.gov.uk/government/publications/assessment-of-priority-skills-to-2030/assessment-of-priority-skills-to-2030
- Pay and employment history: unchanged Arsenii ASHE/CPIH data. Plumber SOC 5315 uses its own metrics and history. Max's mis-coded SOC 5314 plumbing content is not used. The affinity model lacks 5315, so plumbing remains catalogue-only and links to the official training guide.
