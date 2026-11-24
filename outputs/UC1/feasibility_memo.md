## 1. Executive summary

The project is feasible with conditions. All three "must" needs (hourly air pollutants, hourly traffic, hourly weather) can be met, and the "should" need (daily clinic visits) is already approved. Key facts: (1) the prototype can proceed on UCI 360 (2004–2005 Italian-city hourly readings) once the licence contradiction is resolved and sentinel values (-200) are handled; (2) production air quality and traffic data exist internally but require access requests to the Environment Monitoring Unit and Mobility Office respectively, plus a counter-to-station mapping table; (3) patient-level clinic records are blocked by policy (acceptable for a "could" need); (4) Open-Meteo covers hourly weather for both windows with an attribution condition; (5) the traffic counter replacement on 2024-03-18 broke data comparability and needs an adjustment factor.

## 2. Need coverage

| Need id | Need | Priority | Status | Best source(s) | Gap |
|---|---|---|---|---|---|
| N1 | Hourly air-pollutant concentrations | must | met_with_conditions | link.uci_360 (prototype); internal.airq.station_readings (production) | Prototype: licence ambiguity and sentinel values. Production: access not yet granted; station VR-03 stopped 2024-06-30 |
| N2 | Hourly vehicle traffic near monitoring stations | must | met_with_conditions | internal.traffic.hourly_counts | Access not yet granted; counter-to-station mapping missing; 2024-03-18 counter replacement breaks comparability |
| N3 | Hourly temperature and humidity | must | met_with_conditions | api.open_meteo_archive | Attribution required (CC BY 4.0); mixed upstream licences need documentation |
| N4 | Daily respiratory clinic visits by district | should | met | internal.clinic.resp_visits_daily; api.nager_public_holidays | None |
| N5 | Patient-level clinic visit records | could | unmet | — | Prohibited by clinic data policy for this analysis; DPO approval not granted |
| N6 | National yearly context: deaths linked to PM2.5 | could | partially_met | link.europa_sdg_11_52_099aa6 | Data starts 2005 (misses 1 month of prototype window 2004-03); production window 2024–2025 not yet published |

## 3. Source assessments

### api.nager_public_holidays
MIT-licensed public API for Italian national public holidays. Daily grain, all years. Supplementary context for N4 (interpreting zero/low counts on holidays). No conditions. **Feasible.**

### api.open_meteo_archive
Public reanalysis API (ERA5-Land / ECMWF IFS) providing hourly temperature_2m and relative_humidity_2m for Milan-area coordinates. Covers both windows gap-free. **Feasible with conditions:** (1) attribution text must be included ("Weather data by Open-Meteo.com"); (2) mixed upstream licences (DWD, ECMWF, NOAA, CMC, MeteoFrance, JMA – CC-BY, CC-BY-SA, other open) must be documented for compliance. The model switch between windows (ERA5-Land for prototype, ECMWF IFS for production) is documented and acceptable.

### internal.airq.station_readings
Hourly NO₂ and PM₂.₅ readings from Valdena's own monitoring stations. Covers production window (2024–2025) at hourly grain. ~4.2M rows. **Feasible with conditions:** (1) access approval from the Environment Monitoring Unit (Giulia Rossi, steward); (2) station VR-03 readings stop on 2024-06-30 per wiki (catalog has no note – GOV-CATALOG-WIKI-CONFLICT), so modelling must account for the reduced station count after that date; (3) clarify whether a data-sharing agreement is already in place or needs to be newly requested.

### internal.clinic.patient_visits
Patient-level visit records with pseudonymised key, age band, postcode. **Not feasible.** Clinic data policy (last edited 2025-02-01) explicitly prohibits using this table for this analysis. DPO approval not granted. Contains PII. The aggregated table (clinic.resp_visits_daily) is the approved alternative. N5 is "could" priority so this does not block the project.

### internal.clinic.resp_visits_daily
Daily respiratory visit counts by district, no PII, explicitly approved by clinic data policy for this analysis. Covers production window (2024–2025). ~40k rows. Some unknowns (district boundary version, respiratory coding definition) but no blockers. **Feasible.**

### internal.traffic.hourly_counts
Hourly vehicle counts from road counters, covering production window (2024–2025) at hourly grain. ~15M rows. **Feasible with conditions:** (1) access approval from the Mobility Office (Luca Ferri, steward); (2) obtain a counter-to-station mapping table (no geolocation columns in the data); (3) handle the 2024-03-18 break: before that date counts are per-direction, after are combined-direction (wiki documents this; catalog has no note – DQ-METADATA-CONTRADICTION); (4) verify DST handling for the local-time timestamp column against UTC-based air quality data.

### link.data_open_air_chicago_hour_aggre_d4970b
Chicago (USA) air quality data on a host not on the allowlist. Wrong geography, unreachable, no licence. **Not feasible.**

### link.europa_sdg_11_52_099aa6
Eurostat SDG 11_52: annual premature deaths attributable to PM2.5 for Italy. 2005–2023 (18 data years). Open-data reuse. N6 is "could" priority. Per Calibration Rule 1, historical context for a supplementary need does not require perfectly fresh data. 2004 is missing (prototype window starts 2004-03-10) but 2005 onward is covered. **Feasible** (partially covers the windows, which is acceptable for a "could" need).

### link.uci_360
Hourly gas multisensor and reference analyzer readings from an Italian city, 2004-03-10 to 2005-04-04. 9,357 rows. Perfect temporal match for the prototype window. **Feasible with conditions:** (1) resolve licence contradiction – CC BY 4.0 badge vs "research purposes only" note; for a public health body the research restriction is likely acceptable; (2) implement systematic handling of –200 sentinel values (1,592 in CO(GT), 1,642 in NO2(GT), 8,443 in NMHC(GT), 366 in temperature/humidity); (3) document that the city is not identified; validate through De Vito et al. (2008) paper; (4) apply US-to-ISO date parsing (MM/DD/YYYY). NMHC(GT) is 90% missing. Sensor drift documented.

### vendor.atmosdata_pro
Vendor weather feed, contract expired 2025-12-31, API key revoked 2026-01-01, status deprecated. No approved purposes. **Not feasible.** N3 is already covered by Open-Meteo.

## 4. Red-flag register

| Source id | Code | Severity | Evidence | Raised by |
|---|---|---|---|---|
| internal.airq.station_readings | ACC-RESTRICTED | major | auth_required=True, classification=internal, request to Environment Monitoring Unit required | rule |
| internal.airq.station_readings | GOV-CATALOG-WIKI-CONFLICT | major | Catalog entry lists network as active; wiki page station_network (2024-07-01) states station VR-03 switched off 2024-06-30 | judgement |
| internal.traffic.hourly_counts | ACC-RESTRICTED | major | auth_required=True, classification=internal, request to Mobility Office required | rule |
| internal.traffic.hourly_counts | DQ-METADATA-CONTRADICTION | major | Catalog has no note about 2024-03-18 counter replacement; wiki (2024-04-02) states per-direction before, combined-direction after | judgement |
| internal.traffic.hourly_counts | INT-NO-JOIN-KEY | major | Table has no geolocation columns; counter_id cannot be linked to stations without a separate mapping table | judgement |
| internal.clinic.patient_visits | ACC-RESTRICTED | blocker | auth_required=True, classification=restricted, DPO approval not granted for this use case | rule |
| internal.clinic.patient_visits | GOV-PII | major | PII fields: patient_key (pseudonymised), age_band, postcode | rule |
| internal.clinic.patient_visits | GOV-PURPOSE-LIMITATION | blocker | Wiki clinic_data_policy (2025-02-01) prohibits patient-level records for this analysis | judgement |
| internal.clinic.patient_visits | GOV-CONSENT-GAP | blocker | DPO approval required but not granted for this use case | judgement |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | CC BY 4.0 requires attribution link to open-meteo.com | rule |
| api.open_meteo_archive | LIC-MIXED | major | Upstream providers have their own licences (CC-BY, CC-BY-SA, other open) | rule |
| link.uci_360 | LIC-ATTRIBUTION | minor | CC BY 4.0 badge requires attribution | rule |
| link.uci_360 | LIC-NONCOMMERCIAL | blocker | Dataset notes state "research purposes only" contradicting CC BY 4.0 badge | judgement |
| link.uci_360 | DQ-SENTINEL-VALUES | major | Missing values coded as –200 across all columns | judgement |
| link.uci_360 | DQ-METADATA-CONTRADICTION | major | Variable table says missing_values: no; dataset notes say "Has Missing Values? Yes"; sample confirms –200 | judgement |
| link.uci_360 | COV-GEO-MISMATCH | major | Location described only as "an Italian city"; Valdena proximity unconfirmed | judgement |
| link.uci_360 | FRS-METADATA-DATE-MISLEADING | minor | metadata_last_updated=2024-03-10 refers to repository page, not data period (2004–2005) | judgement |
| link.europa_sdg_11_52_099aa6 | COV-PARTIAL-WINDOW | major | Data covers 2005–2023; prototype window starts 2004-03-10; production window extends to 2025-12-31 (not yet published) | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | ACC-UNREACHABLE | blocker | Host catalog.data.gov not on allowlist | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | LIC-UNKNOWN | blocker | No licence could be read | rule |
| link.data_open_air_chicago_hour_aggre_d4970b | COV-GEO-MISMATCH | major | Chicago, USA – use case geography is Italy | judgement |
| vendor.atmosdata_pro | LIC-UNKNOWN | blocker | No licence established; no terms_url | rule |
| vendor.atmosdata_pro | LIC-AGREEMENT-NOT-ACTIVE | blocker | Contract expired 2025-12-31, renewal not signed | rule |
| vendor.atmosdata_pro | ACC-RESTRICTED | major | API key revoked 2026-01-01 | rule |
| vendor.atmosdata_pro | ACC-UNREACHABLE | blocker | Key revoked; feed cannot be reached | rule |
| vendor.atmosdata_pro | GOV-DEPRECATED | major | status=deprecated in external register | rule |

## 5. Conditions and owners

| Condition | Source(s) | Who can resolve it | Blocking which need |
|---|---|---|---|
| Obtain access approval (data-sharing agreement or equivalent) from the Environment Monitoring Unit | internal.airq.station_readings | Environment Monitoring Unit (Giulia Rossi); Procurement / Data Governance | N1 (production) |
| Document that station VR-03 readings stop on 2024-06-30 and adjust modelling | internal.airq.station_readings | Data engineering team | N1 (production) |
| Resolve the UCI 360 licence contradiction (CC BY 4.0 badge vs "research purposes only" notes) | link.uci_360 | Legal team | N1 (prototype) |
| Implement systematic handling of –200 sentinel values for all columns | link.uci_360 | Data engineering team | N1 (prototype) |
| Validate geographic relevance of UCI 360 data (identify city from De Vito et al. 2008) | link.uci_360 | Domain expert | N1 (prototype) |
| Apply US-to-ISO date parsing (MM/DD/YYYY) | link.uci_360 | Data engineering team | N1 (prototype) |
| Obtain access approval from the Mobility Office | internal.traffic.hourly_counts | Mobility Office (Luca Ferri) | N2 |
| Obtain counter-to-station mapping table | internal.traffic.hourly_counts | Mobility Office (Luca Ferri); Data engineering team | N2 |
| Handle 2024-03-18 break: apply adjustment factor or treat as two periods | internal.traffic.hourly_counts | Domain expert (directional-to-combined conversion factor) | N2 |
| Verify DST handling for local-time timestamp vs UTC | internal.traffic.hourly_counts | Data engineering team | N2 |
| Include attribution text in any outputs/products using Open-Meteo data | api.open_meteo_archive | Data governance / legal team | N3 |
| Document mixed upstream licences for compliance | api.open_meteo_archive | Data governance / legal team | N3 |

## 6. Recommended next steps

1. **Raise access requests.** Submit access requests to the Environment Monitoring Unit (Giulia Rossi) for `internal.airq.station_readings` and to the Mobility Office (Luca Ferri) for `internal.traffic.hourly_counts`. Confirm whether data-sharing agreements already exist or must be newly drawn up.

2. **Resolve the UCI 360 licence question.** Ask the legal team to determine whether the "research purposes only" restriction applies to a public health authority prototyping a warning system, and whether this is compatible with the CC BY 4.0 badge.

3. **Request the counter-to-station mapping table** from the Mobility Office, so traffic counter_id values can be linked to specific air-quality monitoring stations.

4. **Engage a domain expert** to identify the city from the De Vito et al. (2008) paper associated with UCI 360, to confirm geographic relevance to Valdena.

5. **Once access is granted, profile the internal datasets first:** (a) `internal.airq.station_readings` – verify station coverage post-VR-03 shutdown, check missing patterns; (b) `internal.traffic.hourly_counts` – quantify the impact of the 2024-03-18 counter change, develop the adjustment factor; (c) `internal.clinic.resp_visits_daily` – confirm district boundaries and respiratory coding definitions.

6. **For the prototype**, prepare the UCI 360 dataset: parse dates, replace/set aside –200 sentinel values, and extract NO2(GT), temperature and humidity columns.

## 7. Open questions for the human reviewer

1. Has the Valdena Civic Health Office confirmed that "research purposes only" is acceptable for a public-health prototype using the UCI 360 dataset, or does the licence need to be formally clarified by the UCI repository maintainers?
2. Which specific Italian city does the UCI 360 dataset come from (per the De Vito et al. 2008 paper), and is it close enough to Valdena to be representative for method-building?
3. For the traffic counter replacement on 2024-03-18, does the Mobility Office have documentation on how to convert per-direction counts to combined-direction counts (a scaling factor), or should the data be treated as two separate modelling periods?
4. Does the existing internal data-sharing agreement between the Health Office and the Environment Monitoring Unit already cover `internal.airq.station_readings`, or must a new one be drafted?
5. Are the district boundaries used in `internal.clinic.resp_visits_daily` stable for 2024–2025, or have there been boundary changes that would affect time-series consistency?
6. What is the respiratory diagnosis code definition used in `internal.clinic.resp_visits_daily` – does it cover all ICD-10 J-codes or a subset?
7. Should the Open-Meteo mixed upstream licence documentation be raised with the data governance board before the prototype starts, or can it be handled in parallel?

---

## Human review gate

Draft generated by the discovery agents for UC1 on 2026-11-18T12:38:14Z (model DeepSeek-V4-Flash). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Blocker flags on sources not rejected (resolve or justify):**

- link.uci_360: LIC-NONCOMMERCIAL

**Open questions:**

1. Has the Valdena Civic Health Office confirmed that "research purposes only" is acceptable for a public-health prototype using the UCI 360 dataset, or does the licence need to be formally clarified by the UCI repository maintainers?
2. Which specific Italian city does the UCI 360 dataset come from (per the De Vito et al. 2008 paper), and is it close enough to Valdena to be representative for method-building?
3. For the traffic counter replacement on 2024-03-18, does the Mobility Office have documentation on how to convert per-direction counts to combined-direction counts (a scaling factor), or should the data be treated as two separate modelling periods?
4. Does the existing internal data-sharing agreement between the Health Office and the Environment Monitoring Unit already cover internal.airq.station_readings, or must a new one be drafted?
5. Are the district boundaries used in internal.clinic.resp_visits_daily stable for 2024–2025, or have there been boundary changes that would affect time-series consistency?
6. What is the respiratory diagnosis code definition used in internal.clinic.resp_visits_daily – does it cover all ICD-10 J-codes or a subset?
7. Should the Open-Meteo mixed upstream licence documentation be raised with the data governance board before the prototype starts, or can it be handled in parallel?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
