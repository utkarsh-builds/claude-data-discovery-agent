# Assignment Walkthrough

**1. One rule I wrote and applied**
I wrote a verdict calibration rule (G5) stating: "If a source triggers a staleness flag (`FRS-STALE`) but is only fulfilling a supplementary or historical context role, the verdict should be `feasible`." This was applied to the Eurostat PM2.5 dataset (`link.europa_sdg_11_52_099aa6`), which ended in 2023. Because it served a "could" priority historical benchmark need (N6), the assessor correctly downgraded the blocker and marked it `feasible_with_conditions`.

**2. One claim traced to its record field**
In my `signoff.json` for UC1, I traced the conclusion that the traffic dataset (`internal.traffic.hourly_counts`) requires a mathematical adjustment factor. I traced this directly to the `red_flag_details` field in the source's catalog record, which surfaced a `DQ-METADATA-CONTRADICTION` noting that the wiki documented a shift from per-direction to combined-direction counting on 2024-03-18. 

**3. One rejected source and why**
I rejected `internal.clinic.patient_visits`. Despite having perfect daily visit data, the agent correctly identified a `GOV-PURPOSE-LIMITATION` blocker. The `clinic_data_policy` wiki page explicitly prohibits using patient-level records with PII (patient key, postcode) for this specific analysis, mandating the use of the aggregated `resp_visits_daily` table instead.

**4. One memo conclusion**
A major conclusion from the UC1 feasibility memo is that the project is `feasible_with_conditions`. While the "must" needs can be met, the project cannot proceed until three conditions are resolved: (1) Legal must clear the CC-BY/Non-Commercial contradiction for the UCI 360 dataset, (2) the Mobility Office must provide a mapping table for the traffic counters, and (3) Data Engineering must implement a fix for the `-200` sentinel values in the air quality data.