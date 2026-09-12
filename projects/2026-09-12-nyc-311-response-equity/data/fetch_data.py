"""Download the 37 sampled daily slices of NYC 311 Service Requests (erm2-nwe9).

One request per sampled day (see `src/days.sampled_dates`), each scoped to a single
calendar day with `$where=created_date >= ... and created_date < ...` so the server
does the filtering, not this script. The endpoint answers with intermittent 503/500
responses under repeated querying, so every request retries with backoff before
giving up.

Re-runnable: if `data/raw/nyc311_sample_2025.csv` exists and its SHA256 matches the
value declared in `data/SOURCE.md`, the network is skipped entirely.

`closed_date` keeps being written to the live dataset (requests that were open at
first fetch may since have closed), so a byte-for-byte re-download is *expected* to
drift. Running with no flags trusts the committed extract and only re-verifies its
checksum. `--refresh` re-downloads all 37 slices and prints a DRIFT line — not a
failure — when the new bytes disagree with the ones already committed.

    python3 data/fetch_data.py            verify (or fetch, if nothing is cached yet)
    python3 data/fetch_data.py --refresh  re-download and report drift
"""

from __future__ import annotations

import csv
import hashlib
import io
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.days import sampled_dates  # noqa: E402

BASE_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.csv"
FIELDS = ["created_date", "closed_date", "complaint_type", "agency", "borough"]
EXPECTED_HEADER = FIELDS

DATA_DIR = Path(__file__).resolve().parent
RAW_PATH = DATA_DIR / "raw" / "nyc311_sample_2025.csv"
SOURCE_MD = DATA_DIR / "SOURCE.md"

MAX_ATTEMPTS = 6
BACKOFF_BASE_SECONDS = 2.0
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def user_agent() -> str:
    """Build the UA from FACTORY_CONTACT_EMAIL. Never embed a URL."""
    email = os.environ.get("FACTORY_CONTACT_EMAIL", "").strip()
    return f"agent-factory/1.0 ({email})" if email else "agent-factory/1.0"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def declared(field: str) -> str | None:
    if not SOURCE_MD.exists():
        return None
    pattern = rf"^-\s*{re.escape(field)}:\s*([0-9a-f]{{64}})\s*$"
    match = re.search(pattern, SOURCE_MD.read_text(), re.MULTILINE)
    return match.group(1) if match else None


def day_url(day) -> str:
    next_day = day.strftime("%Y-%m-%d")
    start = f"{day.isoformat()}T00:00:00"
    from datetime import timedelta

    end = f"{(day + timedelta(days=1)).isoformat()}T00:00:00"
    where = f"created_date >= '{start}' and created_date < '{end}'"
    params = {
        "$select": ",".join(FIELDS),
        "$where": where,
        "$limit": "100000",
        "$order": "created_date,complaint_type",
    }
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"{BASE_URL}?{query}"


def fetch_day(day) -> list[list[str]]:
    """Fetch one day's slice, retrying on 5xx/429 with exponential backoff.

    Returns the parsed CSV rows (header excluded). Raises SystemExit on a
    non-recoverable failure or a response that isn't the CSV we asked for.
    """
    url = day_url(day)
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        request = urllib.request.Request(url, headers={"User-Agent": user_agent()})
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                status = response.status
                body = response.read()
                final_url = response.geturl()
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = exc.read()
            final_url = url
            last_error = f"HTTP {status} {exc.reason}"
        except urllib.error.URLError as exc:
            last_error = f"could not reach the server: {exc.reason}"
            status = None
            body = b""
            final_url = url
        except (TimeoutError, ConnectionError) as exc:
            last_error = f"connection problem: {exc}"
            status = None
            body = b""
            final_url = url

        if status is not None and 200 <= status < 300:
            return validate_csv(body, day, final_url)

        if status in RETRYABLE_STATUSES or status is None:
            sleep_for = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            print(
                f"    attempt {attempt}/{MAX_ATTEMPTS} for {day}: "
                f"{last_error or f'HTTP {status}'} — retrying in {sleep_for:.0f}s"
            )
            if attempt < MAX_ATTEMPTS:
                time.sleep(sleep_for)
            continue

        raise SystemExit(f"FATAL: HTTP {status} for {day} (non-retryable): {url}")

    raise SystemExit(
        f"FATAL: gave up on {day} after {MAX_ATTEMPTS} attempts ({last_error})"
    )


def validate_csv(body: bytes, day, final_url: str) -> list[list[str]]:
    """Confirm the body really is the CSV slice asked for, not an HTML error page
    or a bot-challenge page served under a 200."""
    text = body.decode("utf-8-sig", errors="replace")
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error as exc:
        raise SystemExit(f"FATAL: {day} did not parse as CSV ({exc}): {final_url}")

    if not rows:
        raise SystemExit(f"FATAL: {day} returned an empty body: {final_url}")

    header, data_rows = rows[0], rows[1:]
    if header != EXPECTED_HEADER:
        head = text[:200]
        raise SystemExit(
            f"FATAL: {day} has header {header!r}, expected {EXPECTED_HEADER!r}. "
            f"First bytes: {head!r}"
        )
    for row in data_rows:
        if len(row) != len(EXPECTED_HEADER):
            raise SystemExit(f"FATAL: {day} has a ragged row: {row!r}")
    return data_rows


def download_all() -> tuple[list[str], int]:
    """Fetch all 37 sampled days, return (combined CSV lines, row count)."""
    days = sampled_dates()
    writer_buffer = io.StringIO()
    writer = csv.writer(writer_buffer, lineterminator="\n")
    writer.writerow(EXPECTED_HEADER)
    total_rows = 0
    for i, day in enumerate(days, start=1):
        print(f"  [{i:>2}/{len(days)}] {day.isoformat()} ... ", end="", flush=True)
        started = time.time()
        rows = fetch_day(day)
        writer.writerows(rows)
        total_rows += len(rows)
        print(f"{len(rows):>6,} rows in {time.time() - started:.1f}s")
    return writer_buffer.getvalue(), total_rows


def describe(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as fh:
        n = sum(1 for _ in csv.reader(fh)) - 1
    print(f"  records      : {n:,} rows x {len(EXPECTED_HEADER)} columns")
    return n


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    refresh = "--refresh" in argv

    print(f"Source: {BASE_URL}")
    print(f"UA    : {user_agent()}")
    print(f"Days  : {len(sampled_dates())} sampled (stride 10, day-of-year 1..361)")

    want = declared("SHA256")

    if RAW_PATH.exists() and not refresh:
        actual = sha256_of(RAW_PATH)
        print(f"\nCached  : {RAW_PATH.relative_to(DATA_DIR.parent)}")
        if want is None:
            print(f"  SHA256       : {actual} (no value recorded yet in SOURCE.md)")
            describe(RAW_PATH)
            return 0
        if actual == want:
            print(f"  SHA256       : {actual} (matches SOURCE.md — skipping download)")
            describe(RAW_PATH)
            return 0
        print(f"  SHA256       : {actual}")
        print(f"  SOURCE.md    : {want}")
        print("FATAL: the committed extract does not match its declared checksum.")
        print("       Re-run with --refresh if this drift is expected, otherwise")
        print("       the file on disk has been altered or corrupted.")
        return 1

    print("\nDownloading 37 daily slices" + (" (--refresh)" if refresh else "") + "...")
    combined, total_rows = download_all()

    body = combined.encode("utf-8")
    fresh_hash = hashlib.sha256(body).hexdigest()

    if refresh and RAW_PATH.exists() and want and fresh_hash != want:
        print(f"\nDRIFT: new SHA256 {fresh_hash}")
        print(f"       committed SHA256 {want}")
        print("       Expected: closed_date keeps being written to the live dataset.")
        print("       Update data/SOURCE.md with the new hash if you want to adopt it.")

    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    RAW_PATH.write_bytes(body)

    print(f"\nSaved   : {RAW_PATH.relative_to(DATA_DIR.parent)}")
    print(f"  SHA256       : {fresh_hash}")
    print(f"  records      : {total_rows:,} rows x {len(EXPECTED_HEADER)} columns")
    return 0


if __name__ == "__main__":
    sys.exit(main())
