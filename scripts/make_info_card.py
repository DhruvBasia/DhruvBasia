#!/usr/bin/env python3
"""Hand-author a neofetch-style info card SVG that prints line by line.

    python scripts/make_info_card.py            # -> info-card.svg
    STATIC=1 python scripts/make_info_card.py   # frozen frame, for previewing

>>> EDIT THE CONFIG BLOCK BELOW. That's the whole point of this file. <<<

Keep GitHub *stats* out of here -- the contribution graph already covers those.
This card is for the story the numbers can't tell.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

# ============================ CONFIG =========================================
USER = "dhruv"
HOST = "github"

ROWS = [
    ("Now",       "AI & Data Science student · Delhi, IN"),
    ("Focus",     "machine learning · NLP · computer vision"),
    ("Stack",     "Python · JavaScript · React · Node"),
    ("Tools",     "PyTorch · scikit-learn · OpenCV · pandas"),
    ("Exploring", "cloud + AI deployment, micro-Doppler radar"),
    ("Building",  "green-commute-tracker · cognitive-load-analysis"),
    ("Prev",      "J.P. Morgan SWE virtual program"),
    ("Fun fact",  "talks to AI models more than humans"),
    ("Reach",     "discord: D.hruvv"),
]
# =============================================================================

BG = "#0d1117"
BORDER = "#30363d"
KEY = "#39d353"
VAL = "#c9d1d9"
DIM = "#7d8590"
ACCENT = "#58a6ff"
PALETTE = ["#f85149", "#d29922", "#39d353", "#58a6ff", "#bc8cff", "#39c5cf"]

FS = 12.5
CHAR_W = FS * 0.6
PAD = 20
LINE_H = 25
KEY_W = 96          # column where values start
WIDTH = 520

STAGGER = 0.09
START = 0.35


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def anim(delay):
    """CSS animation-delay, or nothing at all in static mode."""
    return "" if STATIC else f' style="animation-delay:{delay:.2f}s"'


def cls():
    return "" if STATIC else ' class="ln"'


def render():
    title = f"{USER}@{HOST}"
    rule = "─" * max(len(title), 22)

    y = PAD + 22
    body = []
    add = body.append
    d = START

    # --- header ------------------------------------------------------------
    add(f'<text{cls()}{anim(d)} x="{PAD}" y="{y}">'
        f'<tspan fill="{KEY}" font-weight="700">{esc(USER)}</tspan>'
        f'<tspan fill="{DIM}">@</tspan>'
        f'<tspan fill="{ACCENT}" font-weight="700">{esc(HOST)}</tspan></text>')
    d += STAGGER
    y += 16
    add(f'<text{cls()}{anim(d)} x="{PAD}" y="{y}" fill="{DIM}">{rule}</text>')
    d += STAGGER
    y += 14

    # --- key/value rows -----------------------------------------------------
    for key, val in ROWS:
        y += LINE_H
        add(f'<text{cls()}{anim(d)} x="{PAD}" y="{y}" fill="{KEY}" '
            f'font-weight="600">{esc(key)}</text>')
        add(f'<text{cls()}{anim(d)} x="{PAD + KEY_W}" y="{y}" '
            f'fill="{VAL}">{esc(val)}</text>')
        d += STAGGER

    # --- neofetch colour strip ---------------------------------------------
    y += LINE_H + 2
    sw, gap = 22, 6
    for i, colour in enumerate(PALETTE):
        add(f'<rect{cls()}{anim(d + i * 0.04)} x="{PAD + i * (sw + gap)}" '
            f'y="{y - 11}" width="{sw}" height="11" rx="2" fill="{colour}"/>')
    d += STAGGER

    height = round(y + PAD)

    head = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" '
        f'aria-label="Profile info card">'
        "<style>"
        "@keyframes ln{from{opacity:0;transform:translateX(-10px)}"
        "to{opacity:1;transform:translateX(0)}}"
        ".ln{opacity:0;animation:ln .45s ease-out forwards}"
        "text{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;"
        f"font-size:{FS}px}}"
        "@media (prefers-reduced-motion:reduce){"
        ".ln{animation:none;opacity:1;transform:none}}"
        "</style>"
        f'<rect width="{WIDTH}" height="{height}" rx="10" fill="{BG}" '
        f'stroke="{BORDER}"/>'
    )
    return head + "".join(body) + "</svg>"


def main():
    OUT.write_text(render(), encoding="utf-8")
    print(f"wrote {OUT.name} ({len(ROWS)} rows"
          f"{', static' if STATIC else ''})")


if __name__ == "__main__":
    main()
