#!/usr/bin/env python3
"""Re-verify that every source in sources/registry.yml is still live.

    python3 scripts/check_sources.py

Hits each source's `example` endpoint (or its base_url when there's no example)
and prints one line per source. Exits non-zero if any source is down, so it can
run as a weekly workflow and open an issue when the registry goes stale.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
# SEC EDGAR requires a contact email in the User-Agent and rejects one that
# contains a URL. OpenAlex and Crossref use the same email for their polite pool.
CONTACT = os.environ.get("FACTORY_CONTACT_EMAIL", "")
USER_AGENT = f"agent-factory/1.0 ({CONTACT})" if CONTACT else "agent-factory/1.0"


def probe_url(source: dict) -> str:
    base = source["base_url"].rstrip("/")
    example = str(source.get("example", "")).split("|")[0].strip()
    if example.startswith(("/", "?")):
        return base + example
    return base


def probe(url: str) -> tuple[bool, str]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return 200 <= resp.status < 300, str(resp.status)
    except urllib.error.HTTPError as exc:
        return False, str(exc.code)
    except (urllib.error.URLError, TimeoutError) as exc:
        return False, type(exc).__name__


def main() -> int:
    registry = yaml.safe_load((ROOT / "sources" / "registry.yml").read_text(encoding="utf-8"))
    if not CONTACT:
        print("note: FACTORY_CONTACT_EMAIL is unset — SEC's access policy and the OpenAlex/Crossref\n"
              "      polite pools ask for a contact email; requests still work without one.\n")
    down = []
    for source in registry["sources"]:
        if source.get("unattended") is False:
            print(f"-  {source['id']:<22} {'skipped':<14} marked unattended: false (manual use only)")
            continue
        url = probe_url(source)
        url = url.replace("YOU@example.com", CONTACT) if CONTACT else url.replace("&mailto=YOU@example.com", "")
        ok, detail = probe(url)
        print(f"{'✓' if ok else '✗'}  {source['id']:<22} {detail:<14} {url[:90]}")
        if not ok:
            down.append(source["id"])
    print(f"\n{len(registry['sources']) - len(down)}/{len(registry['sources'])} sources live")
    if down:
        print("down: " + ", ".join(down))
    return 1 if down else 0


if __name__ == "__main__":
    sys.exit(main())
