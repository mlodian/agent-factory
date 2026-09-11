#!/usr/bin/env python3
"""Validate a project's visual identity palette. Computed, not eyeballed.

    python3 scripts/check_palette.py projects/<slug>/deck/identity.json

Checks:
  contrast    WCAG 2.x ratios against the background:
                ink, muted            >= 4.5  (body and small text)
                accent, context,
                every categorical     >= 3.0  (large text and chart marks, WCAG 1.4.11)
  separation  every pair of chart colors (categorical + accent vs context):
                normal vision         OKLab ΔE×100 >= 15
                protan/deutan/tritan  >= 8 (FAIL below 6; WARN 6–8, allowed only with labels)

Exit 1 on any FAIL. Standard library only.
"""

from __future__ import annotations

import itertools
import json
import re
import sys
from pathlib import Path

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")

# Machado, Oliveira & Fernandes (2009), severity 1.0, applied in linear RGB.
CVD = {
    "protan": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deutan": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritan": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


def to_linear(hex_color: str) -> tuple[float, float, float]:
    out = []
    for i in (1, 3, 5):
        c = int(hex_color[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)  # type: ignore[return-value]


def luminance(hex_color: str) -> float:
    r, g, b = to_linear(hex_color)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def oklab(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    r, g, b = rgb
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = (max(v, 0.0) ** (1 / 3) for v in (l, m, s))
    return (0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
            1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
            0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_)


def simulate(rgb: tuple[float, float, float], kind: str) -> tuple[float, float, float]:
    matrix = CVD[kind]
    return tuple(min(max(sum(matrix[i][j] * rgb[j] for j in range(3)), 0.0), 1.0) for i in range(3))  # type: ignore[return-value]


def delta_e(a: str, b: str, kind: str | None = None) -> float:
    ra, rb = to_linear(a), to_linear(b)
    if kind:
        ra, rb = simulate(ra, kind), simulate(rb, kind)
    la, lb = oklab(ra), oklab(rb)
    return 100 * sum((x - y) ** 2 for x, y in zip(la, lb)) ** 0.5


def check(identity: dict) -> list[tuple[str, str, str]]:
    """Return (level, check, message) rows. level is PASS, WARN, or FAIL."""
    rows: list[tuple[str, str, str]] = []
    colors = identity.get("colors", {})
    required = ["background", "ink", "muted", "accent", "context", "categorical"]
    missing = [k for k in required if k not in colors]
    if missing:
        return [("FAIL", "schema", "colors missing: " + ", ".join(missing))]

    flat = {k: v for k, v in colors.items() if isinstance(v, str)}
    flat.update({f"categorical[{i}]": v for i, v in enumerate(colors["categorical"])})
    bad = [f"{k}={v}" for k, v in flat.items() if not HEX.match(v)]
    if bad:
        return [("FAIL", "schema", "not #rrggbb: " + ", ".join(bad))]
    if not 1 <= len(colors["categorical"]) <= 6:
        rows.append(("FAIL", "schema", f"categorical must have 1–6 colors, has {len(colors['categorical'])}"))

    bg = colors["background"]
    targets = [("ink", 4.5), ("muted", 4.5), ("accent", 3.0), ("context", 3.0)]
    targets += [(f"categorical[{i}]", 3.0) for i in range(len(colors["categorical"]))]
    for name, need in targets:
        ratio = contrast(flat[name], bg)
        level = "PASS" if ratio >= need else "FAIL"
        rows.append((level, "contrast", f"{name} {flat[name]} on background {bg}: {ratio:.2f}:1 (needs {need})"))
    if "surface" in flat:
        ratio = contrast(flat["ink"], flat["surface"])
        rows.append(("PASS" if ratio >= 4.5 else "FAIL", "contrast",
                     f"ink on surface {flat['surface']}: {ratio:.2f}:1 (needs 4.5)"))

    marks = [(f"categorical[{i}]", c) for i, c in enumerate(colors["categorical"])]
    pairs = list(itertools.combinations(marks, 2))
    pairs.append((("accent", colors["accent"]), ("context", colors["context"])))
    for (na, a), (nb, b) in pairs:
        if a.lower() == b.lower():
            continue  # accent is usually categorical[0] on purpose
        normal = delta_e(a, b)
        worst_kind, worst = min(((k, delta_e(a, b, k)) for k in CVD), key=lambda t: t[1])
        if normal < 15:
            rows.append(("FAIL", "separation", f"{na} vs {nb}: ΔE {normal:.1f} under normal vision (needs 15)"))
        elif worst < 6:
            rows.append(("FAIL", "separation", f"{na} vs {nb}: ΔE {worst:.1f} under {worst_kind} simulation (needs 8)"))
        elif worst < 8:
            rows.append(("WARN", "separation", f"{na} vs {nb}: ΔE {worst:.1f} under {worst_kind} — allowed only with direct labels"))
        else:
            rows.append(("PASS", "separation", f"{na} vs {nb}: ΔE {normal:.1f} normal, {worst:.1f} worst ({worst_kind})"))
    return rows


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    identity = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    rows = check(identity)
    for level, name, msg in rows:
        print(f"{ {'PASS': '✓', 'WARN': '!', 'FAIL': '✗'}[level] } {level:<4} {name:<10} {msg}")
    failed = any(level == "FAIL" for level, _, _ in rows)
    print(f"\npalette {'FAILED' if failed else 'passed'}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
