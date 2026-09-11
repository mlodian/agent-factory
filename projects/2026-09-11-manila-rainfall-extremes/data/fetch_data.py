"""Download the Metro Manila daily-precipitation record from Open-Meteo.

Re-runnable, and careful about what "unchanged" means. Open-Meteo stamps every
response with `generationtime_ms`, so two downloads of the identical data differ
by a few bytes and therefore by file checksum. This script tracks both:

  SHA256          the exact bytes on disk — what the provenance gate verifies
  Content SHA256  a canonical hash of the (date, precipitation) arrays only,
                  which is stable across downloads

If a re-download carries the same content hash, the original file is left
untouched so its declared SHA256 keeps matching SOURCE.md. The file is replaced
only when the underlying data actually changed, and then it says so loudly.

Fails rather than writing a partial or fallback file — there is no sample-data
path here on purpose.

    python3 data/fetch_data.py
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude=14.6&longitude=120.98"
    "&start_date=1940-01-01&end_date=2025-12-31"
    "&daily=precipitation_sum&timezone=Asia%2FManila"
)

DATA_DIR = Path(__file__).resolve().parent
RAW_PATH = DATA_DIR / "raw" / "manila_precip_1940_2025.json"
SOURCE_MD = DATA_DIR / "SOURCE.md"

# The endpoint covers 1940-01-01..2025-12-31 inclusive. Anything materially
# short of that is a truncated response, not a valid answer.
MIN_EXPECTED_DAYS = 31_000


def user_agent() -> str:
    """Build the UA from FACTORY_CONTACT_EMAIL. Never embed a URL — some
    providers' firewalls reject any UA containing one."""
    email = os.environ.get("FACTORY_CONTACT_EMAIL", "").strip()
    return f"agent-factory/1.0 ({email})" if email else "agent-factory/1.0"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def content_sha256(payload: dict) -> str:
    """Hash only the measurements, canonically — stable across re-downloads.

    Excludes generationtime_ms and any other per-response server metadata, so
    this changes if and only if Open-Meteo's reanalysis values changed.
    """
    daily = payload["daily"]
    canonical = json.dumps(
        {"time": daily["time"], "precipitation_sum": daily["precipitation_sum"]},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def declared(field: str) -> str | None:
    """Read a `- <field>: <hex>` value out of SOURCE.md, if it exists yet."""
    if not SOURCE_MD.exists():
        return None
    pattern = rf"^- {re.escape(field)}:\s*([0-9a-f]{{64}})\s*$"
    match = re.search(pattern, SOURCE_MD.read_text(), re.MULTILINE)
    return match.group(1) if match else None


def validate(body: bytes) -> dict:
    """Confirm the body really is the Open-Meteo daily payload we asked for.

    A 200 response is not proof of success: APIs answer with HTML error pages and
    bot challenges under a 200, and a client that quietly saved one would poison
    everything downstream.
    """
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        head = body[:200].decode("utf-8", "replace")
        raise SystemExit(f"FATAL: response is not JSON ({exc}). First bytes: {head!r}")

    if not isinstance(payload, dict) or "daily" not in payload:
        raise SystemExit(f"FATAL: no 'daily' block in response. Keys: {list(payload)}")

    daily = payload["daily"]
    for key in ("time", "precipitation_sum"):
        if key not in daily:
            raise SystemExit(f"FATAL: 'daily' is missing {key!r}. Keys: {list(daily)}")

    days, precip = daily["time"], daily["precipitation_sum"]
    if len(days) != len(precip):
        raise SystemExit(f"FATAL: ragged arrays — {len(days)} dates, {len(precip)} values")
    if len(days) < MIN_EXPECTED_DAYS:
        raise SystemExit(
            f"FATAL: truncated response — {len(days)} days, expected >= {MIN_EXPECTED_DAYS}"
        )
    if all(v is None for v in precip):
        raise SystemExit("FATAL: every precipitation value is null")

    return payload


def describe(payload: dict) -> None:
    daily = payload["daily"]
    days, precip = daily["time"], daily["precipitation_sum"]
    present = [v for v in precip if v is not None]
    print(f"  records      : {len(days)} daily observations")
    print(f"  range        : {days[0]} .. {days[-1]}")
    print(f"  nulls        : {len(precip) - len(present)}")
    print(f"  max mm/day   : {max(present)}")
    print(f"  mean mm/day  : {sum(present) / len(present):.3f}")
    print(f"  elevation    : {payload.get('elevation')} m, tz {payload.get('timezone')}")


def download() -> bytes:
    request = urllib.request.Request(URL, headers={"User-Agent": user_agent()})
    started = time.time()
    try:
        # urlopen follows redirects for GET; we then check the FINAL response.
        with urllib.request.urlopen(request, timeout=180) as response:
            if not 200 <= response.status < 300:
                raise SystemExit(f"FATAL: HTTP {response.status} from {response.geturl()}")
            body = response.read()
            final_url = response.geturl()
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"FATAL: HTTP {exc.code} {exc.reason} for {URL}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"FATAL: could not reach Open-Meteo: {exc.reason}")

    print(f"  fetched      : {len(body)} bytes in {time.time() - started:.1f}s")
    print(f"  final url    : {final_url}")
    return body


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    force = "--force" in argv

    print(f"Source: {URL}")
    print(f"UA    : {user_agent()}")

    want_file = declared("SHA256")
    want_content = declared("Content SHA256")

    if not force and RAW_PATH.exists() and want_file and sha256_of(RAW_PATH) == want_file:
        print(f"\nCached  : {RAW_PATH.relative_to(DATA_DIR.parent)}")
        print(f"  SHA256       : {want_file} (matches SOURCE.md — skipping download)")
        payload = json.loads(RAW_PATH.read_bytes())
        print(f"  Content SHA256: {content_sha256(payload)}")
        describe(payload)
        return 0

    print("\nDownloading..." + (" (--force: ignoring the cached file)" if force else ""))
    body = download()
    payload = validate(body)
    fresh_content = content_sha256(payload)

    # Same measurements, different server timestamp: keep the bytes we already
    # declared, so the checksum in SOURCE.md stays true.
    if RAW_PATH.exists() and want_content and fresh_content == want_content:
        print(f"\nUnchanged: data/{RAW_PATH.relative_to(DATA_DIR)}")
        print(f"  Content SHA256: {fresh_content} (matches SOURCE.md)")
        print("  The response differs only in generationtime_ms; keeping the")
        print("  existing file so its declared SHA256 remains valid.")
        describe(payload)
        return 0

    if RAW_PATH.exists() and want_content:
        print(f"\n!! DATA CHANGED — content hash {fresh_content}")
        print(f"!! SOURCE.md declares  {want_content}")
        print("!! Open-Meteo revised this reanalysis series. Replacing the file;")
        print("!! update data/SOURCE.md and re-run verification before trusting results.")

    # Save the server's bytes verbatim — the raw file is provenance, not output.
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_bytes(body)

    print(f"\nSaved   : {RAW_PATH.relative_to(DATA_DIR.parent)}")
    print(f"  SHA256       : {sha256_of(RAW_PATH)}")
    print(f"  Content SHA256: {fresh_content}")
    describe(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
