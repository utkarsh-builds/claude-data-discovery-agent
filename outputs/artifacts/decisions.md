# Decisions log

## Source suggestions (Step 2b)
One row per suggestion you accepted, rejected or revised, with your reason. Use the page's own wording for the reason.

| Suggestion (publisher, URL) | Need, window | Decision | Reason |
|---|---|---|---|
| N/A for UC1 | (Used prescribed links) | | |

Inspected through the workflow (at least one accepted extra source):
*N/A for UC1; prescribed links used.*

## G1 and G3: one edge case in each function
- **G1, `extract_licence`**: The Kaggle "Unknown" license edge case. The code now explicitly checks if the JSON-LD `licens
e` string or snippet contains the word "unknown" (case-insensitive). If found, it returns `None` for the license name instead of treating "Unknown" as a valid license string. This ensures the pipeline correctly flags it with `LIC-UNKNOWN`.
- **G3, `jsonstat_summary`**: The `status` field format inconsistency. Depending on the JSON-stat dataset, `status` can be formatted as a list or a dictionary. The code now uses `isinstance(status_data, list)` to handle both safely without throwing a TypeError, ensuring the summary generation never crashes.

## G4–G5: feasible for one need or window, not another
- Source and the rule or calibration decision: UCI Air Quality Dataset (rule_temporal_coverage)
- Feasible for (need, window), and why: Feasible for the `prototype` window because the data covers 2004-2005.
- Not feasible for (need, window), and why: Not feasible for the `production` window (2024-2025) because the dataset ends in 2005, triggering a massive `COV-OUT-OF-WINDOW`.
- Reason for each red flag you dismissed: *(Will fill after memo review)*

## G6: Allowlist changes
Exact hosts only. For each host: what it provides and why a broader domain is not needed.

| Host added | Needed for (source, page) | Why nothing broader | Date |
|---|---|---|---|
| `ec.europa.eu` | Eurostat API for PM2.5 deaths (N6) | Specific API host limits exposure compared to allowing all of `*.europa.eu` | 2026-11-18 |
| `archive.ics.uci.edu` | UCI Air Quality dataset (N1) | Specific repository host limits exposure compared to allowing all of `*.uci.edu` | 2026-11-18 |

Hosts you chose **not** to add, and why:
`catalog.data.gov` — This is the host for the Chicago distractor link. I purposefully chose not to add it to the allowlist because its refusal is a deliberate finding meant to test the pipeline's domain guardrails.

## G5: Verdict calibration
- What you changed in `prompts/risk_assessor.md`, and the reasoning behind each rule: Added 7 explicit calibration rules. The reasoning focuses on practical feasibility: downgrading `FRS-STALE` for historical windows, strictly rejecting core needs with unmitigable blockers, allowing window re-assignments (using data for a different window than intended), and mandating imputation conditions when there are metadata contradictions (e.g., undocumented missing values).
- Verdicts that changed after you re-ran `--from-stage assess` (source: before → after, why):
  *(Run `python -m discovery_agent run --use-case UC1 --from-stage assess` to populate this!)*

## G7: One agent failure, fixed at its cause
- **Symptom**: The profiler wasted multiple turns and tokens retrying the Chicago dataset link (`catalog.data.gov`) after the domain guardrail correctly refused it.
- **Evidence**: The terminal output and trace for `link.data_open_air_chicago_hour_aggre_d4970b` showed the agent using 5 turns and 4 tool calls, continually trying to bypass the `DOMAIN_NOT_ALLOWLISTED` refusal.
- **Root cause**: The tool description for `inspect_dataset_link` did not instruct the LLM on how to handle domain guardrail refusals, leading it to treat the refusal as a fixable network error.
- **Fix**: Edited `discovery_agent/tools/links.py`. Added this instruction to the `inspect_dataset_link` tool description:
 "If the tool returns an error containing DOMAIN_NOT_ALLOWLISTED, do NOT retry the URL or try to bypass it. Accept the refusal as a definitive finding and stop profiling."
- **Re-run**: `python -m discovery_agent run --use-case UC1 --from-stage profile --stop-after profile --only link.data_open_air_chicago_hour_aggre_d4970b`
- **Before / after**: Before: 5 LLM calls, 4 tool calls. After: 2 LLM calls, 1 tool call. The agent stopped immediately on the first refusal.
- **Decision this failure could affect**: Wasting the run budget (tokens/API calls) on refused hosts could cause the orchestrator to exhaust the budget before profiling legitimate datasets, leading to false `ACC-UNREACHABLE` blockers for good sources.
- **Related source or test checked**: The Chicago distractor link (`link.data_open_air_chicago_hour_aggre_d4970b`).

## Other decisions
*UC2 Reuse Check (Step 2b): Reviewed 5 suggested sources; none accepted (all rejected for lack of fit/provenance or because needs were already met internally).*