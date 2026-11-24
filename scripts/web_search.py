#!/usr/bin/env python3
"""Search the web via the gateway's /v1/chat/completions endpoint.

Usage: python scripts/web_search.py "<query>"

Environment variables:
    ANTHROPIC_BASE_URL      (required)  Gateway base URL
    ANTHROPIC_AUTH_TOKEN    (required)  Bearer token
    WEB_SEARCH_MODEL        (optional)  Model id; default gemini-3.8-flash
"""

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    if not base_url:
        print("Missing environment variable: ANTHROPIC_BASE_URL", file=sys.stderr)
        return 1

    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "").strip()
    if not token:
        print("Missing environment variable: ANTHROPIC_AUTH_TOKEN", file=sys.stderr)
        return 1

    model = os.environ.get("WEB_SEARCH_MODEL", "gemini-3.8-flash").strip()

    if len(sys.argv) < 2 or not sys.argv[1].strip():
        print("Usage: python scripts/web_search.py \"<query>\"", file=sys.stderr)
        return 1

    query = sys.argv[1].strip()

    body = {
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "web_search_options": {},
    }

    req = urllib.request.Request(
        url=f"{base_url}/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            response = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"HTTP error {exc.code}: {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc.reason}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Invalid JSON response: {exc}", file=sys.stderr)
        return 1

    choices = response.get("choices", [])
    if not choices:
        print("No choices in response", file=sys.stderr)
        return 1

    message = choices[0].get("message", {})
    content = message.get("content", "") or ""
    print(content)

    # Collect citations from the response
    citations = []
    for choice in choices:
        msg = choice.get("message", {})
        citation_objs = msg.get("citations", [])
        for c in citation_objs:
            url = c.get("url") or c.get("link") or c.get("uri") or ""
            if url:
                citations.append(url)

    # Also check top-level citations
    top_citations = response.get("citations", [])
    for c in top_citations:
        url = c.get("url") or c.get("link") or c.get("uri") or ""
        if url and url not in citations:
            citations.append(url)

    if citations:
        print()
        for c in citations:
            print(c)

    return 0


if __name__ == "__main__":
    sys.exit(main())