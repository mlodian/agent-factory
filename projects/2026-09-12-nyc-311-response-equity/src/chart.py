"""Render the headline borough comparison to a standalone SVG, string formatting only.

Two bars per borough — the raw 72h closure share and the same borough re-weighted onto
the citywide complaint mix — so a reversal in ranking between the two is visible without
reading a single number. The dashed line is the citywide rate both bars are measured
against. 95% cluster-bootstrap intervals are drawn as whiskers on top of each bar.
"""

from __future__ import annotations

INK = "#1b2733"
MUTED = "#6b7a8c"
RAW = "#c2570a"
STD = "#0b6fa4"
GRID = "#e6ebf0"

W, H = 760, 460
PAD_L, PAD_R, PAD_T, PAD_B = 60, 20, 70, 110
PLOT_W = W - PAD_L - PAD_R
PLOT_H = H - PAD_T - PAD_B
Y_MAX = 1.0


def _y(rate: float) -> float:
    return PAD_T + (1 - rate / Y_MAX) * PLOT_H


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_borough_bars(boroughs: list[dict], citywide_rate: float, subtitle: str) -> str:
    """`boroughs`: [{"name", "raw", "raw_lo", "raw_hi", "std", "std_lo", "std_hi"}, ...]."""
    n = len(boroughs)
    group_w = PLOT_W / n
    bar_w = group_w * 0.3
    gap = group_w * 0.08

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" '
        f'height="{H}" font-family="Helvetica,Arial,sans-serif" role="img" '
        f'aria-label="Raw versus mix-standardised 72-hour closure rate by borough, '
        f'citywide rate {citywide_rate * 100:.1f} percent">',
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
        f'<text x="{PAD_L}" y="26" font-size="17" font-weight="600" fill="{INK}">'
        f"Closed within 72 hours: raw vs. mix-standardised</text>",
        f'<text x="{PAD_L}" y="44" font-size="12" fill="{MUTED}">{_escape(subtitle)}</text>',
    ]

    for step in range(6):
        rate = step / 5
        y = _y(rate)
        parts.append(f'<line x1="{PAD_L}" y1="{y:.1f}" x2="{PAD_L + PLOT_W}" y2="{y:.1f}" '
                     f'stroke="{GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{PAD_L - 10}" y="{y + 4:.1f}" font-size="11" fill="{MUTED}" '
                     f'text-anchor="end">{rate * 100:.0f}%</text>')

    city_y = _y(citywide_rate)
    parts.append(f'<line x1="{PAD_L}" y1="{city_y:.1f}" x2="{PAD_L + PLOT_W}" y2="{city_y:.1f}" '
                 f'stroke="{INK}" stroke-width="1.5" stroke-dasharray="6 4"/>')
    parts.append(f'<text x="{PAD_L + PLOT_W - 2}" y="{city_y - 6:.1f}" font-size="11" '
                 f'font-weight="600" fill="{INK}" text-anchor="end">'
                 f"citywide {citywide_rate * 100:.1f}%</text>")

    for i, b in enumerate(boroughs):
        cx = PAD_L + group_w * i + group_w / 2
        for offset, key_prefix, color in ((-1, "raw", RAW), (1, "std", STD)):
            x = cx + offset * (bar_w / 2 + gap / 2)
            rate = b[key_prefix]
            lo, hi = b[f"{key_prefix}_lo"], b[f"{key_prefix}_hi"]
            y_top = _y(rate)
            bar_bottom = PAD_T + PLOT_H
            parts.append(f'<rect x="{x - bar_w / 2:.1f}" y="{y_top:.1f}" width="{bar_w:.1f}" '
                         f'height="{bar_bottom - y_top:.1f}" fill="{color}"/>')
            y_lo, y_hi = _y(hi), _y(lo)
            parts.append(f'<line x1="{x:.1f}" y1="{y_lo:.1f}" x2="{x:.1f}" y2="{y_hi:.1f}" '
                         f'stroke="{INK}" stroke-width="1.2"/>')
            for y_cap in (y_lo, y_hi):
                parts.append(f'<line x1="{x - 5:.1f}" y1="{y_cap:.1f}" x2="{x + 5:.1f}" '
                             f'y2="{y_cap:.1f}" stroke="{INK}" stroke-width="1.2"/>')
        parts.append(f'<text x="{cx:.1f}" y="{PAD_T + PLOT_H + 20}" font-size="12" fill="{INK}" '
                     f'text-anchor="middle">{_escape(b["name"].title())}</text>')

    legend_y = H - 34
    parts.append(f'<rect x="{PAD_L}" y="{legend_y - 10}" width="12" height="12" fill="{RAW}"/>')
    parts.append(f'<text x="{PAD_L + 18}" y="{legend_y}" font-size="11.5" fill="{INK}">'
                 f"raw (borough's own complaint mix)</text>")
    parts.append(f'<rect x="{PAD_L + 260}" y="{legend_y - 10}" width="12" height="12" fill="{STD}"/>')
    parts.append(f'<text x="{PAD_L + 278}" y="{legend_y}" font-size="11.5" fill="{INK}">'
                 f"standardised (citywide complaint mix)</text>")
    parts.append(f'<text x="{PAD_L}" y="{legend_y + 18}" font-size="10.5" fill="{MUTED}">'
                 f"whiskers: 95% cluster bootstrap interval, resampled over the 37 sampled days</text>")

    parts.append("</svg>")
    return "\n".join(parts) + "\n"
