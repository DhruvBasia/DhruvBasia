#!/usr/bin/env python3
"""Render data/contributions.json as an animated 53x7 heatmap SVG.

All motion is CSS keyframes inside the SVG -- GitHub renders SVGs embedded via
<img> and plays their animations, but strips <script> and external CSS.
The reveal plays once on load and freezes (animation-fill-mode: forwards).
"""
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

# --- palette -----------------------------------------------------------------
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#7d8590"
TEXT_BRIGHT = "#c9d1d9"
ACCENT = "#39d353"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"

# --- geometry ----------------------------------------------------------------
CELL = 11
GAP = 3
STEP = CELL + GAP
PAD = 18
DAY_LABEL_W = 28
MONTH_H = 20
GRID_H = 7 * STEP - GAP
FOOTER_H = 44

GRID_X = PAD + DAY_LABEL_W
GRID_Y = PAD + MONTH_H

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def to_weeks(days):
    """Bucket the flat day list into columns, aligned so row 0 is Sunday."""
    weeks, col = [], [None] * 7
    for d in days:
        y, m, dd = (int(x) for x in d["date"].split("-"))
        dow = (date(y, m, dd).weekday() + 1) % 7  # Mon=0 -> Sun=0
        if col[dow] is not None:
            weeks.append(col)
            col = [None] * 7
        col[dow] = d
    if any(c is not None for c in col):
        weeks.append(col)
    return weeks


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def level_of(day, max_count):
    """Promote the very best days to the neon top of the ramp."""
    lvl = day["level"]
    if lvl >= 4 and max_count and day["count"] >= max_count:
        return 5
    return lvl


def render(data):
    days = data["days"]
    weeks = to_weeks(days)
    n_weeks = len(weeks)
    max_count = data.get("max_count", 0)

    width = GRID_X + n_weeks * STEP - GAP + PAD
    height = GRID_Y + GRID_H + FOOTER_H + PAD

    out = []
    add = out.append

    add(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{esc(data["total"])} GitHub contributions in the last year">'
    )

    # --- animation ----------------------------------------------------------
    add(
        "<style>"
        "@keyframes drop{from{opacity:0;transform:translateY(-9px) scale(.4)}"
        "to{opacity:1;transform:translateY(0) scale(1)}}"
        "@keyframes fade{from{opacity:0}to{opacity:1}}"
        ".c{opacity:0;animation:drop .5s cubic-bezier(.2,.9,.3,1.4) forwards}"
        ".f{opacity:0;animation:fade .6s ease-out forwards}"
        f"text{{font-family:{MONO}}}"
        "@media (prefers-reduced-motion:reduce){"
        ".c,.f{animation:none;opacity:1;transform:none}}"
        "</style>"
    )

    # --- panel --------------------------------------------------------------
    add(f'<rect width="{width}" height="{height}" rx="10" fill="{BG}" '
        f'stroke="{BORDER}"/>')

    # --- month labels -------------------------------------------------------
    seen = set()
    for wi, col in enumerate(weeks):
        first = next((c for c in col if c), None)
        if not first:
            continue
        mo = first["date"][5:7]
        if mo in seen:
            continue
        seen.add(mo)
        x = GRID_X + wi * STEP
        if x + 26 > width - PAD:
            continue
        delay = 0.15 + wi * 0.012
        add(f'<text class="f" style="animation-delay:{delay:.2f}s" x="{x}" '
            f'y="{PAD + 12}" font-size="10" fill="{TEXT}">'
            f'{MONTHS[int(mo) - 1]}</text>')

    # --- day-of-week labels -------------------------------------------------
    for row, label in DAY_LABELS.items():
        y = GRID_Y + row * STEP + CELL - 1
        add(f'<text class="f" style="animation-delay:{0.2 + row * 0.05:.2f}s" '
            f'x="{PAD}" y="{y}" font-size="9" fill="{TEXT}">{label}</text>')

    # --- the grid -----------------------------------------------------------
    add(f'<g transform="translate({GRID_X},{GRID_Y})">')
    for wi, col in enumerate(weeks):
        for row, day in enumerate(col):
            if day is None:
                continue
            x, y = wi * STEP, row * STEP
            fill = PALETTE[level_of(day, max_count)]
            delay = 0.25 + (wi * 0.011) + (row * 0.028)  # diagonal sweep
            add(
                f'<rect class="c" style="animation-delay:{delay:.2f}s;'
                f'transform-origin:{x + CELL / 2:.1f}px {y + CELL / 2:.1f}px" '
                f'x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{fill}">'
                f'<title>{day["count"]} on {day["date"]}</title></rect>'
            )
    add("</g>")

    # --- legend -------------------------------------------------------------
    fy = GRID_Y + GRID_H + 24
    legend_w = 6 * STEP + 58
    lx = width - PAD - legend_w
    tail = 0.25 + n_weeks * 0.011 + 0.3
    add(f'<g class="f" style="animation-delay:{tail:.2f}s">')
    add(f'<text x="{lx}" y="{fy + 9}" font-size="9" fill="{TEXT}">Less</text>')
    for i, colour in enumerate(PALETTE):
        add(f'<rect x="{lx + 30 + i * STEP}" y="{fy}" width="{CELL}" '
            f'height="{CELL}" rx="2.5" fill="{colour}"/>')
    add(f'<text x="{lx + 34 + 6 * STEP}" y="{fy + 9}" font-size="9" '
        f'fill="{TEXT}">More</text>')
    add("</g>")

    # --- stats footer -------------------------------------------------------
    add(f'<g class="f" style="animation-delay:{tail + 0.12:.2f}s">')
    add(f'<text x="{PAD}" y="{fy + 9}" font-size="11" fill="{TEXT_BRIGHT}">'
        f'<tspan fill="{ACCENT}" font-weight="600">{data["total"]:,}</tspan>'
        f' contributions in the last year</text>')
    add(f'<text x="{PAD}" y="{fy + 25}" font-size="9" fill="{TEXT}">'
        f'streak {data["current_streak"]}d · longest {data["longest_streak"]}d'
        f' · best {data["best_day"]["count"]} on {data["best_day"]["date"]}'
        f' · {data["active_days"]} active days</text>')
    add("</g>")

    add("</svg>")
    return "".join(out)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUT.write_text(render(data), encoding="utf-8")
    print(f"{OUT.name}: {data['total']} contributions, {len(data['days'])} days")


if __name__ == "__main__":
    main()
