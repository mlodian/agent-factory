#!/usr/bin/env python3
"""Provenance gate for one factory project.

Runs in CI after the agent finishes, and decides whether the project's data and
claims hold up. The agent's own account of its work is not consulted.

    python3 scripts/check_provenance.py <slug> [--offline]

Checks, grouped:
  contract     required files exist; no {{placeholders}} left in the docs
  provenance   SOURCE.md names a registered, non-denied source; checksums match;
               the cited URL is live
  fabrication  no synthetic-data generators outside tests/
  claims       every number on every slide traces to VERIFY.md or the chart
               script's FIGURES.md; project.json's status agrees with VERIFY.md

Exit 0 only if nothing FAILs. Writes the report to .provenance-report.md so the
workflow can attach it to the pull request.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
# SEC EDGAR requires a contact email in the User-Agent and rejects one containing a URL.
_CONTACT = os.environ.get("FACTORY_CONTACT_EMAIL", "")
USER_AGENT = f"agent-factory/1.0 ({_CONTACT})" if _CONTACT else "agent-factory/1.0"
RAW_SIZE_LIMIT = 10 * 1024 * 1024

REQUIRED_FILES = [
    "SPEC.md",
    "README.md",
    "ARCHITECTURE.md",
    "DEMO.md",
    "VERIFY.md",
    "verify.sh",
    "project.json",
    "deck/deck.md",
    "deck/STORY.md",
]
DATA_FILES = ["data/SOURCE.md", "data/fetch_data.py"]
PLACEHOLDER_DOCS = ["README.md", "ARCHITECTURE.md", "DEMO.md", "deck/deck.md"]

# Calls that manufacture values rather than read them. A line can opt out with
# `# provenance: allow <reason>`; the reason is printed in the report so the
# reviewer sees every exception.
SYNTHETIC_PATTERNS = [
    (re.compile(r"\bnp\.random\.(?!seed\b|permutation\b|shuffle\b)\w+"), "numpy random generator"),
    (re.compile(r"\bnumpy\.random\.(?!seed\b|permutation\b|shuffle\b)\w+"), "numpy random generator"),
    (re.compile(r"\bdefault_rng\s*\("), "numpy Generator"),
    (re.compile(r"\b[Ff]aker\b"), "Faker"),
    (re.compile(r"\bmake_(classification|regression|blobs|moons|circles|friedman\d)\s*\("), "sklearn synthetic dataset"),
    (re.compile(r"\brandom\.(gauss|uniform|normalvariate|randint|lognormvariate|triangular|betavariate)\s*\("), "stdlib random value"),
    (re.compile(r"\btorch\.(randn|rand|randint)\s*\("), "torch random tensor"),
]
ALLOW_MARKER = re.compile(r"#\s*provenance:\s*allow\s+(\S.*)$")

NUMBER = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?%?")


@dataclass
class Report:
    slug: str
    lines: list[tuple[str, str, str]] = field(default_factory=list)

    def ok(self, group: str, msg: str) -> None:
        self.lines.append(("PASS", group, msg))

    def warn(self, group: str, msg: str) -> None:
        self.lines.append(("WARN", group, msg))

    def fail(self, group: str, msg: str) -> None:
        self.lines.append(("FAIL", group, msg))

    @property
    def failed(self) -> bool:
        return any(level == "FAIL" for level, _, _ in self.lines)

    def render(self) -> str:
        icon = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌"}
        verdict = "FAILED" if self.failed else "PASSED"
        out = [f"## Provenance check: {verdict}", "", f"Project: `{self.slug}`", ""]
        for level, group, msg in self.lines:
            out.append(f"- {icon[level]} **{group}** — {msg}")
        return "\n".join(out) + "\n"


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_source_md(text: str) -> tuple[dict[str, str], list[tuple[str, str]]]:
    """Return the first value of each `- Key: value` field, plus (file, sha256) pairs.

    A SOURCE.md may list several files; each `File:` line is paired with the
    next `SHA256:` line.
    """
    fields: dict[str, str] = {}
    pairs: list[tuple[str, str]] = []
    pending_file: str | None = None
    for raw in text.splitlines():
        m = re.match(r"^\s*-\s*([A-Za-z0-9 ]+?)\s*:\s*(.+?)\s*$", raw)
        if not m:
            continue
        key, value = m.group(1).strip().lower(), m.group(2).split("#")[0].strip()
        fields.setdefault(key, value)
        if key == "file":
            pending_file = value
        elif key == "sha256" and pending_file is not None:
            pairs.append((pending_file, value.lower()))
            pending_file = None
    return fields, pairs


HTML_SNIFF = re.compile(rb"^\s*(<!doctype\s+html|<html|<head)", re.I)


def content_problem(path: Path) -> str | None:
    """Why this file isn't plausibly the data it claims to be, or None if it is.

    A matching checksum only proves the file hasn't changed since the agent saved
    it — not that it was ever data. The usual failure is a download that saved an
    error, redirect, or bot-challenge page under a .json name.
    """
    size = path.stat().st_size
    if size == 0:
        return "file is empty"
    suffix = path.suffix.lower()
    head = path.open("rb").read(1024)
    if suffix not in {".html", ".htm"} and HTML_SNIFF.search(head):
        title = re.search(rb"<title>([^<]{0,80})", head, re.I)
        hint = f" (title: {title.group(1).decode(errors='replace').strip()!r})" if title else ""
        return f"is an HTML page, not data — likely an error, redirect, or bot challenge{hint}"
    if suffix in {".json", ".geojson"}:
        import json
        try:
            json.loads(path.read_bytes())
        except ValueError as exc:
            return f"is not valid JSON ({exc.__class__.__name__}: {str(exc)[:60]})"
    if suffix in {".csv", ".tsv"}:
        with path.open("rb") as fh:
            lines = sum(1 for _, line in zip(range(3), fh) if line.strip())
        if lines < 2:
            return "has a header but no data rows"
    return None


def url_is_live(url: str, attempts: int = 3) -> tuple[bool, str]:
    last = ""
    for i in range(attempts):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return 200 <= resp.status < 300, f"HTTP {resp.status}"
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code < 500 and exc.code != 429:
                return False, last
        except (urllib.error.URLError, TimeoutError) as exc:
            last = f"{type(exc).__name__}: {exc}"
        time.sleep(2 ** i)
    return False, last


def numbers_in(text: str) -> set[str]:
    return {n.replace(",", "") for n in NUMBER.findall(text)}


def deck_visible_text(deck: str) -> str:
    """What an audience actually reads on the slides.

    Drops front matter, speaker notes and directives, code, image references, HTML
    tags and style blocks, URLs, and ISO dates, so a link to projects/2026-09-11-…
    or a CSS value isn't mistaken for a claim.
    """
    text = re.sub(r"\A---\s*\n.*?\n---\s*\n", "", deck, flags=re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\b(?:https?://|www\.)\S+|\b[\w.-]+\.(?:com|org|io|gov|dev)(?:/\S*)?", " ", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}(?:T[\d:.]+Z?)?", " ", text)
    # Identifiers, not claims: "API 2.0", "CC BY 4.0", "CVSS v3.1", "Python 3.12", "ISO 8601".
    return re.sub(r"(?i)\b(?:api|v|version|cc[ -]by(?:-[a-z]{2})*|cc0|cvss(?:\s*v)?|python|http|iso|utf|rfc|tls)"
                  r"[\s-]*\d+(?:\.\d+)*\b", " ", text)


def exempt(number: str) -> bool:
    """Years and small counts ("3 reasons", "1 in N") are context, not measurements."""
    bare = number.rstrip("%")
    if number.endswith("%") or "." in bare:
        return False
    value = int(bare)
    return 0 <= value <= 12 or 1900 <= value <= 2100


def check_contract(project: Path, needs_data: bool, report: Report) -> None:
    missing = [f for f in REQUIRED_FILES + (DATA_FILES if needs_data else []) if not (project / f).exists()]
    if missing:
        report.fail("contract", "missing required files: " + ", ".join(missing))
    else:
        report.ok("contract", "all required files present")

    leftovers = []
    for name in PLACEHOLDER_DOCS:
        path = project / name
        if path.exists() and re.search(r"\{\{[^}]+\}\}", path.read_text(encoding="utf-8")):
            leftovers.append(name)
    if leftovers:
        report.fail("contract", "unfilled {{placeholders}} in: " + ", ".join(leftovers))
    else:
        report.ok("contract", "no template placeholders left")


def check_provenance(project: Path, registry: dict, offline: bool, report: Report) -> None:
    source_md = project / "data" / "SOURCE.md"
    if not source_md.exists():
        return  # already reported by the contract check

    fields, pairs = parse_source_md(source_md.read_text(encoding="utf-8"))
    known = {s["id"]: s for s in registry.get("sources", [])}
    denied = {d["id"] for d in registry.get("denied", [])}

    reg_id = fields.get("registry", "")
    if reg_id in denied:
        report.fail("provenance", f"source `{reg_id}` is on the registry's denied list")
    elif reg_id not in known:
        report.fail("provenance", f"registry id `{reg_id or '(blank)'}` is not in sources/registry.yml")
    else:
        report.ok("provenance", f"source `{reg_id}` is registered ({known[reg_id]['licence']})")

    raw_dir = project / "data" / "raw"
    raw_files = sorted(p for p in raw_dir.rglob("*") if p.is_file()) if raw_dir.exists() else []
    declared = {Path(f).as_posix() for f, _ in pairs}

    if not pairs:
        report.fail("provenance", "SOURCE.md declares no `File:` / `SHA256:` pair")
    for rel, expected in pairs:
        path = project / "data" / rel
        if not path.exists():
            report.fail("provenance", f"declared file `{rel}` does not exist — run data/fetch_data.py")
            continue
        problem = content_problem(path)
        if problem:
            report.fail("provenance", f"`{rel}` {problem}")
        actual = sha256(path)
        if actual != expected:
            report.fail("provenance", f"`{rel}` SHA256 mismatch (declared {expected[:12]}…, actual {actual[:12]}…)")
        elif not problem:
            report.ok("provenance", f"`{rel}` checksum matches and content parses as data")
        if path.stat().st_size > RAW_SIZE_LIMIT:
            report.warn("provenance", f"`{rel}` is over 10 MB — the workflow will drop it from the commit; fetch_data.py recreates it")

    for path in raw_files:
        rel = path.relative_to(project / "data").as_posix()
        if rel not in declared:
            report.fail("provenance", f"`{rel}` is in data/ but not declared in SOURCE.md — undeclared data")

    url = fields.get("url", "").split()[0] if fields.get("url") else ""
    if not url.startswith("http"):
        report.fail("provenance", "SOURCE.md has no usable `URL:`")
    elif offline:
        report.warn("provenance", "URL liveness skipped (--offline)")
    else:
        live, detail = url_is_live(url)
        if live:
            report.ok("provenance", f"cited URL is live ({detail})")
        else:
            report.fail("provenance", f"cited URL is not reachable ({detail}): {url}")


def check_fabrication(project: Path, report: Report) -> None:
    hits, exceptions = [], []
    for path in sorted(project.rglob("*.py")):
        rel = path.relative_to(project)
        if rel.parts[0] in {"tests", ".venv", "venv"}:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for pattern, label in SYNTHETIC_PATTERNS:
                if pattern.search(line):
                    allowed = ALLOW_MARKER.search(line)
                    where = f"`{rel}:{lineno}` ({label})"
                    if allowed:
                        exceptions.append(f"{where} — reason given: “{allowed.group(1).strip()}”")
                    else:
                        hits.append(where)
    if hits:
        report.fail("fabrication", "synthetic-data generators outside tests/: " + "; ".join(hits))
    else:
        report.ok("fabrication", "no synthetic-data generators outside tests/")
    for exc in exceptions:
        report.warn("fabrication", "allowed by annotation, reviewer should confirm: " + exc)


def check_claims(project: Path, report: Report, verify_log: Path | None = None) -> None:
    verify_path, deck_path = project / "VERIFY.md", project / "deck" / "deck.md"
    if not (verify_path.exists() and deck_path.exists()):
        return

    verify = verify_path.read_text(encoding="utf-8")
    m = re.search(r"STATUS:\s*(PASSED|FAILED)", verify)
    verify_status = m.group(1).lower() if m else None
    if verify_status is None:
        report.fail("claims", "VERIFY.md has no `STATUS: PASSED|FAILED` line")

    pj = project / "project.json"
    if pj.exists() and verify_status:
        import json
        declared = str(json.loads(pj.read_text(encoding="utf-8")).get("status", "")).lower()
        if declared != verify_status:
            report.fail("claims", f"project.json says `{declared}` but VERIFY.md says `{verify_status}`")
        else:
            report.ok("claims", f"project.json status agrees with VERIFY.md ({verify_status})")

    # Every number on every slide must trace to one of three places:
    #   measured  — what verify.sh actually printed. In CI that's the log the workflow
    #               captured from its own independent run (--verify-log), NOT VERIFY.md,
    #               whose prose an agent writes and could launder a number into.
    #   derived   — deck/charts/FIGURES.md, written by the committed chart script,
    #               which the workflow regenerates before this gate runs.
    #   cited     — data/CONTEXT.md bullets that carry a source URL: outside facts
    #               (e.g. a historical gauge record), visibly marked as not measured.
    if verify_log is not None:
        measured, basis = verify_log.read_text(encoding="utf-8", errors="replace"), "the workflow's own verify.sh log"
    else:
        measured, basis = verify, "VERIFY.md"
        report.warn("claims", "checked against VERIFY.md prose — pass --verify-log for the independent check CI runs")
    allowed = numbers_in(measured)
    figures = project / "deck" / "charts" / "FIGURES.md"
    if figures.exists():
        allowed |= numbers_in(figures.read_text(encoding="utf-8"))
    context = project / "data" / "CONTEXT.md"
    cited = 0
    if context.exists():
        for line in context.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith(("-", "*")):
                if re.search(r"https?://\S+", line):
                    allowed |= numbers_in(re.sub(r"https?://\S+", " ", line))
                    cited += 1
                elif numbers_in(line):
                    report.fail("claims", f"data/CONTEXT.md line has a number but no source URL: {line.strip()[:80]}")
    shown = numbers_in(deck_visible_text(deck_path.read_text(encoding="utf-8")))
    unsupported = sorted(n for n in shown - allowed if not exempt(n))
    if not shown:
        report.warn("claims", "the deck contains no numbers — confirm that's deliberate")
    elif unsupported:
        report.fail("claims", f"numbers on slides not found in {basis}, FIGURES.md, or cited CONTEXT.md: " + ", ".join(unsupported))
    else:
        report.ok("claims", f"all {len(shown)} distinct numbers on the slides trace to {basis}, FIGURES.md"
                  + (f", or {cited} cited context line(s)" if cited else ""))
    if cited:
        report.warn("claims", f"{cited} outside fact(s) cited in data/CONTEXT.md — reviewer should confirm each source")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("slug")
    parser.add_argument("--offline", action="store_true", help="skip the URL liveness check")
    parser.add_argument("--verify-log", type=Path,
                        help="output captured from the workflow's own verify.sh run; slide numbers "
                             "are checked against this instead of agent-written VERIFY.md")
    parser.add_argument("--data-only", action="store_true",
                        help="provenance + fabrication only; for mid-pipeline use before docs exist")
    args = parser.parse_args()

    project = ROOT / "projects" / args.slug
    report = Report(args.slug)
    if not project.is_dir():
        report.fail("contract", f"projects/{args.slug} does not exist")
    else:
        registry = load_yaml(ROOT / "sources" / "registry.yml")
        needs_data = (project / "data").exists() or not _declares_no_source(project)
        if not args.data_only:
            check_contract(project, needs_data, report)
        if needs_data:
            check_provenance(project, registry, args.offline, report)
        else:
            report.ok("provenance", "project declares `source: none` — no dataset to check")
        check_fabrication(project, report)
        if not args.data_only:
            check_claims(project, report, args.verify_log)

    text = report.render()
    print(text)
    (ROOT / ".provenance-report.md").write_text(text, encoding="utf-8")
    return 1 if report.failed else 0


def _declares_no_source(project: Path) -> bool:
    import json
    pj = project / "project.json"
    if not pj.exists():
        return False
    source = json.loads(pj.read_text(encoding="utf-8")).get("source")
    return source in (None, "none") or (isinstance(source, dict) and source.get("registry_id") in (None, "none"))


if __name__ == "__main__":
    sys.exit(main())
