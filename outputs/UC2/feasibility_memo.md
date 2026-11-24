## 1. Executive summary

**Verdict: Feasible with conditions.** All five needs can be served, but the two must-priority needs (N1 daily sales, N3 temperature) and the other must-priority need (N2 product code mapping) each require conditions. N1 has a 34-day gap and a product-code break. N2 is only partially resolvable because no mapping table exists and some product names are not unique. N3 needs a paid commercial subscription. The should-priority needs (N4, N5) are fully met without conditions.

## 2. Need coverage

| Need ID | Need | Priority | Status | Best source(s) | Gap |
|---|---|---|---|---|---|
| N1 | Daily ice-cream sales by product | must | met_with_conditions | internal.sales.daily_by_product, internal.sales.products | 34-day gap (2024-02-05 to 2024-03-10) from till migration; product code discontinuity on 2024-04-01 with no mapping table |
| N2 | Mapping of product codes before/after 2024 code change | must | partially_met | internal.sales.products, internal.sales.daily_by_product | No mapping table exists; name-based matching is possible but some product names are not unique — mapping will be incomplete |
| N3 | Daily maximum temperature | must | met_with_conditions | api.open_meteo_archive | No data gap, but commercial subscription required (free tier is non-commercial only) |
| N4 | Public holidays in Italy | should | met | api.nager_public_holidays | None |
| N5 | Shop opening days and local events | should | met | internal.store.calendar | None |

## 3. Source assessments

### api.nager_public_holidays
**Source:** Free public REST API (MIT licence) providing Italian national public holidays by year (Nager.Date). No API key required.
**Verdict: Feasible.** Returns all ~13–14 Italian public holidays per year for 2023–2026 at daily grain. All entries are marked global (nationwide). Registered and approved for UC2 prototyping and production. Serves N4 (should priority) with no blockers or conditions.

### internal.store.calendar
**Source:** Internal daily calendar with `is_open` flag and optional `event_name` field for the Valdena shop, covering 2022-01-01 onward, refreshed weekly.
**Verdict: Feasible.** Serves N5 (should priority). Access is classified as "internal, open to analytics roles" (standard request process). No red flags beyond the standard access restriction. The event_name field may be sparse, which is acceptable for a supplementary need.

### api.open_meteo_archive
**Source:** Open-Meteo Historical Weather API (ERA5 reanalysis). Delivers daily `temperature_2m_max` for any GPS coordinates from 1940 to near-realtime.
**Verdict: Feasible with conditions.**
- **Key flags:** (1) ACC-RESTRICTED (major) — free tier is non-commercial only; Valdena Gelato Shop, as a commercial entity, needs a paid subscription. (2) LIC-ATTRIBUTION (minor) — CC BY 4.0 requires attribution text. (3) LIC-MIXED (major) — upstream data from ERA5/ERA5-Land (Copernicus ECMWF) and ECMWF IFS with different terms, though the API provides CC BY 4.0 terms.
- **Conditions:** Obtain a paid commercial subscription; attribute weather data per CC BY 4.0; provide the shop's exact GPS coordinates for nearest grid-cell temperature.
- Resolvable by: Project lead (purchase subscription), Data analyst (coordinates, attribution).

### internal.sales.daily_by_product
**Source:** Daily units_sold and revenue_eur per product from the Valdena till system, covering 2022-01-01 to present, refreshed daily.
**Verdict: Feasible with conditions.**
- **Key flags:** (1) ACC-RESTRICTED (major) — confidential classification, approval needed from Retail Operations. (2) COV-PARTIAL-WINDOW (major) — 34-day data gap from 2024-02-05 to 2024-03-10 due to till replacement (wiki: till_migration_2024). (3) INT-JOIN-KEY-MISMATCH (major) — product codes changed on 2024-04-01 with no mapping table. (4) DQ-SEMANTIC-ENCODING (major) — old codes (ending 'L') vs new codes encode the same product differently across the break.
- **Conditions:** Obtain access from Retail Operations; treat the 34-day gap as missing data (not zero sales); match old/new product codes via name from internal.sales.products, accepting incomplete mappings.
- Resolvable by: Data analyst/Engineer (access request), Marco Bianchi / Retail Operations (approval), Data analyst (name matching).

### internal.sales.products
**Source:** Static reference of 64 current (post-2024) product codes with names and categories, last refreshed 2025-03-31.
**Verdict: Feasible with conditions.**
- **Key flags:** (1) ACC-RESTRICTED (major) — internal classification, open to analytics roles. (2) INT-JOIN-KEY-MISMATCH (major) — contains only current codes; pre-2024 'L' codes not present; no mapping table exists; some product names are not unique (wiki: product_codes_2024).
- **Conditions:** Use product_name to attempt matching old/new codes; document which names are non-unique and exclude those from cross-period analysis; if full mapping is needed, manual reconciliation with shop owner may be required.
- Resolvable by: Data analyst (name matching), Retail Operations / Marco Bianchi (manual reconciliation of non-unique names).

## 4. Red-flag register

| Source ID | Code | Severity | Evidence | Raised by |
|---|---|---|---|---|
| internal.sales.daily_by_product | ACC-RESTRICTED | major | auth_required=true, classification=confidential, request_process='Request to Retail Operations' | rule |
| internal.sales.daily_by_product | COV-PARTIAL-WINDOW | major | 34-day gap 2024-02-05 to 2024-03-10 due to till replacement (wiki: till_migration_2024) | judgement |
| internal.sales.daily_by_product | INT-JOIN-KEY-MISMATCH | major | Product codes changed 2024-04-01, no mapping table (wiki: product_codes_2024) | judgement |
| internal.sales.daily_by_product | DQ-SEMANTIC-ENCODING | major | Old codes ending 'L' vs new codes encode same product differently across break | judgement |
| internal.sales.products | ACC-RESTRICTED | major | auth_required=true, classification=internal, request_process='Open to analytics roles' | rule |
| internal.sales.products | INT-JOIN-KEY-MISMATCH | major | Only current (post-2024) codes present; no mapping table; some product names non-unique | judgement |
| api.open_meteo_archive | ACC-RESTRICTED | major | auth_required=true; free tier is non-commercial only; commercial entity needs paid subscription | rule |
| api.open_meteo_archive | LIC-MIXED | major | Mixed upstream sources (ERA5, ECMWF IFS) with different terms | rule |
| api.open_meteo_archive | LIC-ATTRIBUTION | minor | CC BY 4.0 requires attribution text | rule |
| internal.store.calendar | ACC-RESTRICTED | major | auth_required=true, classification=internal | rule |

## 5. Conditions and owners

| Condition | Source(s) | Who can resolve it | Blocking which need |
|---|---|---|---|
| Obtain access approval from Retail Operations | internal.sales.daily_by_product | Data analyst/Engineer (request), Retail Operations / Marco Bianchi (approval) | N1 |
| Handle 34-day gap (2024-02-05 to 2024-03-10) as missing data | internal.sales.daily_by_product | Data analyst | N1 |
| Match old/new product codes via name; accept incomplete mapping | internal.sales.daily_by_product, internal.sales.products | Data analyst (name matching), Retail Operations / Marco Bianchi (manual reconciliation if needed) | N1, N2 |
| Obtain paid commercial subscription for Open-Meteo | api.open_meteo_archive | Project lead / Data Engineering | N3 |
| Attribute weather data per CC BY 4.0 | api.open_meteo_archive | Data analyst | N3 |
| Provide shop's exact GPS coordinates | api.open_meteo_archive | Data analyst / Shop owner | N3 |
| If full product mapping needed, manual reconciliation | internal.sales.products | Retail Operations / Marco Bianchi | N2 |

## 6. Recommended next steps

1. **Raise access request** for `internal.sales.daily_by_product` to Retail Operations (Marco Bianchi), citing the N1 must-priority need.
2. **Raise access request** for `internal.sales.products` to the analytics-role approval process (standard, low friction).
3. **Purchase** a paid commercial subscription to Open-Meteo (Standard/Professional/Enterprise tier) for the API — contact Open-Meteo GmbH at https://open-meteo.com/en/pricing.
4. **Confirm the shop's GPS coordinates** with the Valdena shop owner to set the location for weather data retrieval.
5. **Start name-matching exercise** on the product codes: extract distinct product names from both pre-2024 (from the daily_by_product data) and post-2024 (from internal.sales.products), and document which names are unique versus duplicated. This will determine the extent of the N2 mapping gap.
6. **Once access is granted**, profile `internal.sales.daily_by_product` first — verify row counts per day in each window and quantify the exact number of days affected by the 34-day gap.
7. **Decide with the shop owner** how to treat the 34-day gap: as missing data, by imputation, or by excluding that period from analysis entirely.

## 7. Open questions for the human reviewer

1. What are the exact GPS coordinates of the Valdena Gelato Shop, so we can retrieve the nearest grid-cell temperature from Open-Meteo?
2. Is the 34-day gap (2024-02-05 to 2024-03-10) acceptable as missing data, or does the shop have any backup records (e.g., paper logs) that could fill it?
3. Which products had non-unique names across the 2024 code change? Can the shop owner manually reconcile those mappings?
4. Who is the budget owner for the Open-Meteo commercial subscription, and what is the approval process for a paid external API?
5. The use case does not name the shop's city — should we assume a specific location in northern Italy (e.g., Milan, coordinates 45.4642°N, 9.1900°E) for weather data retrieval, as used for testing the API probes?

---

## Human review gate

Draft generated by the discovery agents for UC2 on 2026-11-18T14:19:44Z (model DeepSeek-V4-Flash). It is a draft for review, not a decision.

Before any profiling or pipeline work, the reviewer confirms:

- [ ] Each verdict is supported by the evidence cited
- [ ] Every licence was read at its source, and the attribution text is recorded
- [ ] Access requests for the feasible-with-conditions sources are raised with the named owners
- [ ] Consent and purpose limits are understood, and the target population is filtered accordingly

**Open questions:**

1. What are the exact GPS coordinates of the Valdena Gelato Shop, so we can retrieve the nearest grid-cell temperature from Open-Meteo?
2. Is the 34-day gap (2024-02-05 to 2024-03-10) acceptable as missing data, or does the shop have any backup records (e.g., paper logs) that could fill it?
3. Which products had non-unique names across the 2024 code change? Can the shop owner manually reconcile those mappings?
4. Who is the budget owner for the Open-Meteo commercial subscription, and what is the approval process for a paid external API?
5. The use case does not name the shop's city — should we assume a specific location in northern Italy (e.g., Milan, coordinates 45.4642°N, 9.1900°E) for weather data retrieval, as used for testing the API probes?

Reviewer: ____________________   Date: __________   Decision: proceed / proceed with conditions / stop
