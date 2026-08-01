#!/usr/bin/env python3
"""Turn source-prepped.png into a monochrome ASCII portrait that types itself.

    python scripts/make_ascii_svg.py            # -> dhruv-ascii.svg
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, for previewing

Each row lives inside its own clip rect whose width animates 0 -> full, so the
row wipes in left-to-right with a block cursor riding the edge. Rows are
staggered top to bottom. It prints once and freezes -- no looping.

Two rules keep it looking like a portrait and not like static:
  * ONE colour. Per-character rainbow fills are what ruin most ASCII portraits.
  * A leading space in the ramp, so bright areas clear to nothing.
"""
import os
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "dhruv-ascii.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#       ^ leading space clears the background to nothing

COLS = 100
FONT_SIZE = 7.0
CHAR_W = FONT_SIZE * 0.6      # monospace advance width
LINE_H = FONT_SIZE * 1.02     # tight leading so the grid reads as a solid image
PAD = 14

INK = "#c9d1d9"               # one colour, always
CURSOR = "#39d353"
BG = "#0d1117"
BORDER = "#30363d"

ROW_DUR = 0.42                # how long one row takes to wipe in
ROW_STAGGER = 0.028           # delay added per row
START = 0.2

STATIC = os.environ.get("STATIC") == "1"


def placeholder() -> Image.Image:
    """A stand-in bust so the README renders before you add a real photo."""
    h = w = 900
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy, r = w / 2, h * 0.36, h * 0.21
    head = ((xx - cx) / (r * 0.82)) ** 2 + ((yy - cy) / r) ** 2
    sx, sy = w / 2, h * 1.06
    body = ((xx - sx) / (w * 0.40)) ** 2 + ((yy - sy) / (h * 0.62)) ** 2
    mask = np.minimum(head, body)
    light = 0.42 + 0.5 * np.clip(
        1 - np.hypot((xx - cx * 0.78) / (w * 0.6), (yy - cy * 0.7) / (h * 0.6)), 0, 1
    )
    img = np.where(mask < 1.0, (1 - light) * 255, 255)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), mode="L")


def to_rows(img: Image.Image):
    # Characters are ~2x taller than wide, so squash vertically to compensate.
    rows = max(1, round(COLS * (img.height / img.width) * (CHAR_W / LINE_H)))
    small = np.asarray(
        img.convert("L").resize((COLS, rows), Image.LANCZOS), dtype=np.float32
    )
    # Stretch whatever range the image actually uses across the full ramp.
    lo, hi = np.percentile(small, 2), np.percentile(small, 98)
    norm = np.clip((small - lo) / max(hi - lo, 1e-6), 0, 1)
    idx = np.clip(((1 - norm) * (len(RAMP) - 1)).round().astype(int),
                  0, len(RAMP) - 1)
    return ["".join(RAMP[i] for i in row) for row in idx]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(rows):
    text_w = COLS * CHAR_W
    width = round(text_w + PAD * 2)
    height = round(len(rows) * LINE_H + PAD * 2)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="ASCII portrait">',
        f'<rect width="{width}" height="{height}" rx="10" fill="{BG}" '
        f'stroke="{BORDER}"/>',
    ]
    add = out.append

    # One clip rect per row, each animating its width open.
    add("<defs>")
    for i in range(len(rows)):
        y = PAD + i * LINE_H
        w0 = text_w if STATIC else 0
        add(f'<clipPath id="w{i}"><rect x="{PAD:.1f}" y="{y - LINE_H:.2f}" '
            f'width="{w0:.1f}" height="{LINE_H * 2:.2f}">')
        if not STATIC:
            add(f'<animate attributeName="width" from="0" to="{text_w:.1f}" '
                f'dur="{ROW_DUR}s" begin="{START + i * ROW_STAGGER:.2f}s" '
                f'fill="freeze"/>')
        add("</rect></clipPath>")
    add("</defs>")

    add(f'<g font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" '
        f'font-size="{FONT_SIZE}" fill="{INK}" xml:space="preserve">')
    for i, row in enumerate(rows):
        y = PAD + (i + 1) * LINE_H
        add(f'<text clip-path="url(#w{i})" x="{PAD:.1f}" y="{y:.2f}">'
            f'{esc(row)}</text>')
    add("</g>")

    # A block cursor that rides each wipe edge, then vanishes.
    if not STATIC:
        for i in range(len(rows)):
            begin = START + i * ROW_STAGGER
            y = PAD + i * LINE_H
            add(f'<rect y="{y + 1:.2f}" width="{CHAR_W:.2f}" '
                f'height="{LINE_H:.2f}" fill="{CURSOR}" opacity="0">'
                f'<animate attributeName="x" from="{PAD:.1f}" '
                f'to="{PAD + text_w:.1f}" dur="{ROW_DUR}s" '
                f'begin="{begin:.2f}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0.85" begin="{begin:.2f}s"/>'
                f'<set attributeName="opacity" to="0" '
                f'begin="{begin + ROW_DUR:.2f}s"/></rect>')

    add("</svg>")
    return "".join(out)


def main():
    if SRC.exists():
        img = Image.open(SRC)
        print(f"source: {SRC.name}")
    else:
        img = placeholder()
        print(f"! {SRC.name} not found -- rendering a PLACEHOLDER bust.")
        print("  run: python scripts/prep_photo.py your-photo.jpg")

    rows = to_rows(img)
    OUT.write_text(render(rows), encoding="utf-8")
    print(f"wrote {OUT.name} ({COLS}x{len(rows)} chars"
          f"{', static' if STATIC else ''})")


if __name__ == "__main__":
    main()
