"""Deterministic red-flag rules, run on every catalog record before the Risk Assessor agent.

Why rules and an agent? Rules are cheap, repeatable and testable, and they catch what can be
read from structured fields. The agent adds judgement flags (conflicts, consent gaps,
representativeness, ...) and may dismiss a rule flag only with a written reason, and the
orchestrator enforces that.

Each rule: (record, candidate, use_case, settings) -> list of {"code", "evidence"}.
"""

from __future__ import annotations

import re
from datetime import date

Flag = dict

GRAIN_ORDER = ["minute", "15min", "30min", "hourly", "daily", "weekly", "monthly", "quarterly", "annual"]
INACTIVE_STATUSES = {"deprecated", "archived", "frozen", "retired", "decommissioned", "superseded"}


def _flag(code: str, evidence: str) -> Flag:
    return {"code": code, "evidence": evidence}


def _d(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Provided rules (read these as worked examples)
# ---------------------------------------------------------------------------
def rule_licence(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    if record["kind"] == "internal":
        return []
    lic = record.get("licence") or {}
    name = (lic.get("name") or "").strip()
    flags = []
    if not name or name.lower() in {"unknown", "none", "null", "not found", "n/a"}:
        flags.append(_flag("LIC-UNKNOWN", f"No licence established. Evidence field: {lic.get('evidence')!r}"))
    elif re.search(r"\bNC\b|non[- ]?commercial", name, re.I):
        flags.append(_flag("LIC-NONCOMMERCIAL", f"Licence {name!r} restricts commercial use"))
    elif re.search(r"\bBY\b|attribution|OGL|open government", name, re.I):
        flags.append(_flag("LIC-ATTRIBUTION", f"Licence {name!r} requires attribution"))
    if lic.get("mixed_sources"):
        flags.append(_flag("LIC-MIXED", "Record states that parts come from upstream providers with different terms"))
    return flags


def rule_agreement(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    status = ((record.get("licence") or {}).get("agreement_status") or "").lower()
    if record["kind"] == "vendor_feed" and status not in {"active", "signed"}:
        return [_flag("LIC-AGREEMENT-NOT-ACTIVE", f"Vendor feed with agreement_status={status or 'unknown'!r}")]
    return []


def rule_access(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    acc = record.get("access") or {}
    flags = []
    if acc.get("auth_required") or (acc.get("classification") or "").lower() == "restricted":
        flags.append(
            _flag(
                "ACC-RESTRICTED",
                f"auth_required={acc.get('auth_required')}, "
                f"classification={acc.get('classification')}, process={acc.get('request_process')!r}",
            )
        )
    if (acc.get("method") or "").lower() in {"manual_export", "manual", "spreadsheet", "email"}:
        flags.append(_flag("ACC-MANUAL", f"Access method {acc.get('method')!r}"))
    if acc.get("reachable") is False:
        flags.append(_flag("ACC-UNREACHABLE", "Record states the source could not be reached or restored"))
    return flags


def rule_payload(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    size = (record.get("access") or {}).get("approx_size_bytes")
    limit = settings["rules"]["large_payload_bytes"]
    if isinstance(size, int) and size > limit:
        return [_flag("OPS-LARGE-PAYLOAD", f"approx_size_bytes={size:,} > {limit:,}")]
    return []


def rule_pii(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    pii_fields = [f["name"] for f in (record.get("schema") or {}).get("fields", []) if f.get("pii") is True]
    declared = (record.get("declared_metadata") or {}).get("contains_pii")
    if pii_fields or declared is True:
        return [_flag("GOV-PII", f"PII fields: {pii_fields or 'declared contains_pii=true'}")]
    return []


def rule_owner(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    if record["kind"] == "internal" and not ((record.get("ownership") or {}).get("owner") or "").strip():
        return [_flag("GOV-OWNER-UNKNOWN", "Internal source with no recorded owner")]
    return []


def rule_status(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    status = (record.get("status") or "").lower()
    if status in INACTIVE_STATUSES:
        return [_flag("GOV-DEPRECATED", f"status={status!r}")]
    return []


# ---------------------------------------------------------------------------
# LEARNER TODO (G4): three rules. tests/test_learner_gaps.py::test_g4_* checks them.
# ---------------------------------------------------------------------------
def rule_temporal_coverage(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    flags = []
    t = record.get("temporal", {})
    if t.get("grain") == "static":
        return []
    start = _d(t.get("start"))
    if not start:
        return []
    end = _d(t.get("end"))

    as_of = _d(uc.get("as_of", date.today().isoformat()))
    effective_end = end if end else as_of

    all_zeros = True
    any_partial = False
    evidence_parts = []

    for w_id in candidate.get("target_windows", []):
        w = next((x for x in uc.get("windows", []) if x["id"] == w_id), None)
        if not w:
            continue
        w_start = _d(w["start"])
        w_end = _d(w["end"])

        i_start = max(start, w_start)
        i_end = min(effective_end, w_end)

        if i_start <= i_end:
            overlap = (i_end - i_start).days + 1
            w_total = (w_end - w_start).days + 1
            frac = overlap / w_total if w_total > 0 else 0
            if frac > 0:
                all_zeros = False
            if 0 < frac < settings["rules"]["partial_window_threshold"]:
                any_partial = True
        else:
            frac = 0

        evidence_parts.append(f"{w_id}: {start} to {effective_end}")

    if all_zeros and evidence_parts:
        flags.append(_flag("COV-OUT-OF-WINDOW", "; ".join(evidence_parts)))
    elif any_partial and evidence_parts:
        flags.append(_flag("COV-PARTIAL-WINDOW", "; ".join(evidence_parts)))

    if end and as_of:
        years_stale = (as_of - end).days / 365.25
        if years_stale > settings["rules"]["stale_after_years"]:
            flags.append(
                _flag(
                    "FRS-STALE",
                    f"Data ends {end}, which is >{settings['rules']['stale_after_years']} years before {as_of}",
                )
            )

    return flags


def rule_grain(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    rg = record.get("temporal", {}).get("grain")
    if rg not in GRAIN_ORDER:
        return []

    for n_id in candidate.get("need_ids", []):
        need = next((n for n in uc.get("needs", []) if n["id"] == n_id), None)
        if not need:
            continue
        mg = need.get("min_grain")
        if mg in GRAIN_ORDER:
            if GRAIN_ORDER.index(rg) > GRAIN_ORDER.index(mg):
                return [_flag("COV-GRAIN-MISMATCH", f"Record grain {rg} is coarser than need {n_id} min_grain {mg}")]
    return []


def rule_metadata_contradiction(record: dict, candidate: dict, uc: dict, settings: dict) -> list[Flag]:
    dm = record.get("declared_metadata", {})
    hmv = dm.get("has_missing_values")
    if str(hmv).lower() not in ("no", "false"):
        return []

    text = " ".join(record.get("documentation_excerpts", []) + record.get("quality_notes", []))

    # Strip negated phrases first so they aren't falsely flagged
    stripped = re.sub(r"(?i)no\s+missing\s+values?", "", text)

    if re.search(r"(?i)missing\s+values?|absence\s+of\s+value|-200|\?|NaN", stripped):
        return [
            _flag("DQ-METADATA-CONTRADICTION", f"declared has_missing_values={hmv} but found contradiction: {text}")
        ]

    return []


RULES = [
    rule_licence,
    rule_agreement,
    rule_access,
    rule_payload,
    rule_pii,
    rule_owner,
    rule_status,
    rule_temporal_coverage,
    rule_grain,
    rule_metadata_contradiction,
]


def evaluate(record: dict, candidate: dict, uc: dict, settings: dict) -> tuple[list[Flag], list[str]]:
    """Run every rule. Returns (flags, warnings). A rule that is not implemented yet is skipped with a warning."""
    flags: list[Flag] = []
    warnings: list[str] = []
    for rule in RULES:
        try:
            for f in rule(record, candidate, uc, settings):
                flags.append({**f, "raised_by": f"rule:{rule.__name__}"})
        except NotImplementedError as exc:
            warnings.append(f"{rule.__name__} skipped: {exc}")
    seen, unique = set(), []
    for f in flags:
        if f["code"] not in seen:
            seen.add(f["code"])
            unique.append(f)
    return unique, warnings
