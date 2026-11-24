"""Licence and structured-metadata extraction from dataset landing pages."""

from __future__ import annotations

import json
import re

from .base import NotImplementedTool


def jsonld_datasets(html: str) -> list[dict]:
    """Return every schema.org Dataset object embedded as JSON-LD in a page.

    Many portals (Kaggle, Zenodo, data.gov, Hugging Face, Dataverse, CKAN sites) embed one.
    It is the most reliable machine-readable description of a dataset when it exists.
    """
    found = []
    for m in re.finditer(r"""(?is)<script[^>]*type=["']application/ld\+json["'][^>]*>(.*?)</script>""", html):
        try:
            data = json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for item in items:
            if isinstance(item, dict) and "Dataset" in str(item.get("@type", "")):
                found.append(item)
    return found


def summarise_jsonld_dataset(d: dict) -> dict:
    """Keep the fields that matter for discovery, clipped for the model."""

    def name_of(v):
        if isinstance(v, list):
            return [name_of(x) for x in v][:5]
        if isinstance(v, dict):
            return v.get("name") or v.get("url") or v.get("@id")
        return v

    def clip(v, n=600):
        v = re.sub(r"<[^>]+>", " ", str(v)) if v is not None else None
        return None if v is None else (" ".join(v.split())[:n])

    dist = d.get("distribution") or []
    dist = dist if isinstance(dist, list) else [dist]
    return {
        "name": d.get("name"),
        "description": clip(d.get("description")),
        "license": d.get("license"),
        "creator": name_of(d.get("creator")),
        "publisher": name_of(d.get("publisher")),
        "datePublished": d.get("datePublished"),
        "dateModified": d.get("dateModified"),
        "temporalCoverage": d.get("temporalCoverage"),
        "spatialCoverage": name_of(d.get("spatialCoverage")),
        "isAccessibleForFree": d.get("isAccessibleForFree"),
        "keywords": clip(d.get("keywords"), 300),
        "variableMeasured": name_of(d.get("variableMeasured")),
        "distribution": [
            {
                k: x.get(k)
                for k in ("contentUrl", "encodingFormat", "fileFormat", "contentSize", "requiresSubscription", "name")
                if isinstance(x, dict) and x.get(k) is not None
            }
            for x in dist[:10]
        ],
    }


# ---------------------------------------------------------------------------
# LEARNER TODO (G1): find the licence of ANY dataset from its landing page
# ---------------------------------------------------------------------------
# Without this, every dataset link ends up LIC-UNKNOWN (a blocker) and verdicts are wrong.
#
# Contract (tests/test_learner_gaps.py::test_g1_* checks it):
#   extract_licence(html: str, jsonld: list[dict] | None = None) -> dict with EXACTLY these keys
#     licence_name : normalised name, one of e.g. "CC BY 4.0", "CC BY-SA 4.0", "CC BY-NC 4.0", "CC BY-NC-SA 4.0",
#                    "CC BY-ND 4.0", "CC0 1.0", "ODbL 1.0", "OGL v3.0", "MIT", "Apache-2.0"; None if not found
#                    or if the page says the licence is unknown/unspecified
#     licence_url  : the licence URL you found, or None
#     snippet      : the text or JSON-LD value you read it from (<= 400 chars), or None
#     found_in     : "json-ld" | "link" | "text" | None
#
# Order of evidence: JSON-LD "license" (string URL, or {"name", "url"}) first; then links to
# creativecommons.org / opendatacommons.org / nationalarchives.gov.uk (OGL) / choosealicense.com;
# then sentences such as "licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) license".
# jsonld defaults to jsonld_datasets(html) when None. Never guess: return None values when unsure.
def extract_licence(html: str, jsonld: list[dict] | None = None) -> dict:
    if jsonld is None:
        jsonld = jsonld_datasets(html)

    out = {"licence_name": None, "licence_url": None, "snippet": None, "found_in": None}

    def norm(text):
        if not text:
            return None
        t = text.lower()
        if "unknown" in t:
            return None
        if "cc by-nc-sa" in t or "by-nc-sa/4.0" in t:
            return "CC BY-NC-SA 4.0"
        if "cc by-nc" in t or "by-nc/4.0" in t:
            return "CC BY-NC 4.0"
        if "cc by" in t or "by/4.0" in t:
            return "CC BY 4.0"
        if "cc0" in t:
            return "CC0 1.0"
        if "odbl" in t:
            return "ODbL 1.0"
        if "open government" in t or "ogl" in t:
            return "OGL v3.0"
        if "mit" in t:
            return "MIT"
        if "apache" in t:
            return "Apache-2.0"
        # Only fallback to raw text if it's very short (like a JSON-LD string), not a sentence
        if len(text.strip()) < 30 and " " not in text.strip()[:10]:
            return text.strip()
        return None

    # 1. Check JSON-LD first
    for d in jsonld:
        lic = d.get("license")
        if lic:
            snippet = str(lic)[:400]
            if "unknown" in snippet.lower():
                out["snippet"] = snippet
                out["found_in"] = "json-ld"
                return out

            if isinstance(lic, dict):
                name = norm(lic.get("name") or lic.get("url"))
                if name:
                    return {
                        "licence_name": name,
                        "licence_url": lic.get("url"),
                        "snippet": snippet,
                        "found_in": "json-ld",
                    }
            elif isinstance(lic, str):
                name = norm(lic)
                if name:
                    return {
                        "licence_name": name,
                        "licence_url": lic if "http" in lic else None,
                        "snippet": snippet,
                        "found_in": "json-ld",
                    }

    # 2. Check HTML Links
    import re

    for m in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I):
        url, text = m.groups()
        snippet = m.group(0)[:400]
        name = norm(text) or norm(url)
        if name and any(
            domain in url
            for domain in [
                "creativecommons.org",
                "opendatacommons.org",
                "nationalarchives.gov.uk",
                "choosealicense.com",
            ]
        ):
            return {"licence_name": name, "licence_url": url, "snippet": snippet, "found_in": "link"}

    # 3. Check raw HTML text sentences
    text_no_tags = re.sub(r"<[^>]+>", " ", html)
    for m in re.finditer(r"[^.]*licens[^.]*\.", text_no_tags, re.I):
        snippet = m.group(0).strip()[:400]
        name = norm(snippet)
        if name:
            return {"licence_name": name, "licence_url": None, "snippet": snippet, "found_in": "text"}

    return out
