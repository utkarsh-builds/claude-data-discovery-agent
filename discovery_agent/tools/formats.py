"""Summarisers for self-describing metadata formats the supplementary URLs use.

The tool wrappers (fetch + call) are provided. The pure functions that do the
summarising are LEARNER TODOs (G3). The data-package summary is not graded in this version. They are pure so you can test them offline
against tests/fixtures/ without network or LLM.
"""

from __future__ import annotations

from .base import NotImplementedTool, ToolContext, tool

LARGE_RESOURCE_BYTES = 100_000_000


# ---------------------------------------------------------------------------
# Not graded in this version (former G2). Left as a stub: no graded link uses a data package.
# ---------------------------------------------------------------------------
# Spec: https://specs.frictionlessdata.io/data-package/
# Return a dict with EXACTLY these keys (tests/test_learner_gaps.py checks them):
#   title, version, profile          : str | None, copied from the package
#   declared_licences                : the package's "licenses" list, or None if absent/empty
#   temporal                         : {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} from package["temporal"], or None
#   resources                        : [{"name", "path", "format", "bytes", "field_count"}] one per resource
#   total_bytes                      : sum of resource bytes (missing bytes count as 0)
#   largest_resource_bytes           : max resource bytes
#   matching_fields                  : fields whose name starts with any prefix in field_filter (all resources,
#                                      de-duplicated by name, max 60): [{"resource", "name", "unit", "source"}]
#                                      where "source" is field["source"]["name"] if present. [] if field_filter is None.
#   upstream_sources                 : sorted distinct field["source"]["name"] values across ALL fields
#   warnings                         : list containing (when they apply)
#                                        "NO_PACKAGE_LICENCE"         no package-level licence declared
#                                        "LARGE_RESOURCE"             any resource > LARGE_RESOURCE_BYTES
#                                        "MULTIPLE_UPSTREAM_SOURCES"  more than one upstream source
def datapackage_summary(package: dict, field_filter: list[str] | None = None) -> dict:
    raise NotImplementedTool("datapackage_summary is not implemented in this version (former G2).")


# ---------------------------------------------------------------------------
# LEARNER TODO (G3): JSON-stat 2.0 dataset -> summary
# ---------------------------------------------------------------------------
# Spec: https://json-stat.org/full/   (Eurostat's dissemination API returns this format)
# Return a dict with EXACTLY these keys:
#   label, updated, source           : copied from the dataset
#   dimensions                       : [{"id", "size", "labels"}] in the order of dataset["id"];
#                                      labels = first 10 "code: label" strings for that dimension
#   time                             : {"first", "last", "values"} for the "time" dimension (codes, sorted), or None
#   geo_codes                        : list of codes in the "geo" dimension, in index order ([] if no geo dimension)
#   expected_cells                   : product of dataset["size"]
#   value_count                      : number of non-null values (dataset["value"] can be a dict OR a list)
#   missing_cells                    : expected_cells - value_count
#   status_counts                    : {status_code: count} from dataset.get("status") (dict or list), {} if absent
#   warnings                         : list containing (when they apply)
#                                        "MISSING_CELLS"       missing_cells > 0
#                                        "NON_ISO_GEO_CODES"   any geo code that is not ISO 3166-1 alpha-2,
#                                                              including Eurostat's "UK" (ISO: GB) and "EL" (ISO: GR)
#                                                              and aggregates such as "EU27_2020"
# Hint: dimension categories look like
#   dataset["dimension"]["geo"]["category"] = {"index": {"UK": 0, "FR": 1}, "label": {"UK": "United Kingdom", ...}}
#   "index" can also be a list of codes.
def jsonstat_summary(dataset: dict) -> dict:
    dim_ids = dataset.get("id", [])
    sizes = dataset.get("size", [])

    expected = 1
    for s in sizes:
        expected *= s
    if not sizes:
        expected = 0

    dims = []
    for i, dim_id in enumerate(dim_ids):
        cat = dataset.get("dimension", {}).get(dim_id, {}).get("category", {})
        labels_dict = cat.get("label", {})
        labels = [f"{k}: {v}" for k, v in list(labels_dict.items())[:10]]
        dims.append({"id": dim_id, "size": sizes[i] if i < len(sizes) else 0, "labels": labels})

    time_dim = dataset.get("dimension", {}).get("time", {}).get("category", {}).get("index", [])
    time_vals = sorted(list(time_dim.keys()) if isinstance(time_dim, dict) else time_dim)
    time_obj = {"first": time_vals[0], "last": time_vals[-1], "values": time_vals} if time_vals else None

    geo_dim = dataset.get("dimension", {}).get("geo", {}).get("category", {}).get("index", [])
    geo_codes = list(geo_dim.keys()) if isinstance(geo_dim, dict) else geo_dim

    val_data = dataset.get("value", [])
    if isinstance(val_data, dict):
        v_count = len(val_data)
    else:
        v_count = sum(1 for v in val_data if v is not None)

    missing = expected - v_count

    from collections import Counter

    status_data = dataset.get("status", {})
    if isinstance(status_data, list):
        s_counts = dict(Counter(s for s in status_data if s))
    else:
        s_counts = dict(Counter(status_data.values()))

    warnings = []
    if missing > 0:
        warnings.append("MISSING_CELLS")
    for gc in geo_codes:
        if len(str(gc)) > 2 or gc in ("UK", "EL"):
            warnings.append("NON_ISO_GEO_CODES")
            break

    return {
        "label": dataset.get("label"),
        "updated": dataset.get("updated"),
        "source": dataset.get("source"),
        "dimensions": dims,
        "time": time_obj,
        "geo_codes": geo_codes,
        "expected_cells": expected,
        "value_count": v_count,
        "missing_cells": missing,
        "status_counts": s_counts,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Tool wrappers (provided)
# ---------------------------------------------------------------------------
@tool(
    "summarize_datapackage",
    "Summarise a Frictionless Data Package descriptor (datapackage.json): licence declarations, temporal coverage, "
    "resource sizes, matching fields and their upstream sources. Reads only the descriptor, never the data files.",
    {
        "url": {"type": "string"},
        "field_filter": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Field-name prefixes to list, e.g. ['AB_', 'CD_load']",
        },
    },
    ["url"],
)
def summarize_datapackage(ctx: ToolContext, args: dict) -> dict:
    package, res = ctx.http.get_json(args["url"], max_bytes=5_000_000, agent=ctx.agent)
    return {
        "url": args["url"],
        "last_modified_header": res.headers.get("last-modified"),
        **datapackage_summary(package, args.get("field_filter")),
    }


@tool(
    "summarize_jsonstat",
    "Summarise a JSON-stat 2.0 dataset (for example from the Eurostat dissemination API): dimensions, time coverage, "
    "geo codes, missing cells and status flags.",
    {"url": {"type": "string"}},
    ["url"],
)
def summarize_jsonstat(ctx: ToolContext, args: dict) -> dict:
    dataset, _ = ctx.http.get_json(args["url"], max_bytes=5_000_000, agent=ctx.agent)
    return {"url": args["url"], **jsonstat_summary(dataset)}
