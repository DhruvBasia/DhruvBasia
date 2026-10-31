#!/usr/bin/env python3
"""Draw the ASCII card that types itself: an astronaut, or a photo portrait.

    python scripts/make_ascii_svg.py            # -> dhruv-ascii.svg
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, for previewing

No photo needed: without source-prepped.png the card is an astronaut bust
shaded from a few shapes, standard library only. Change ACCENT to recolour it.
Run prep_photo.py first and it becomes a portrait of that photo instead (that
path needs pillow + numpy).

Each row lives inside its own clip rect whose width animates 0 -> full, so the
row wipes in left-to-right with a block cursor riding the edge. Rows are
staggered top to bottom. It prints once and freezes -- no looping.

Two rules keep it looking like a picture and not like static:
  * ONE main colour. Per-character rainbow fills are what ruin most ASCII art;
    the astronaut only adds an accent and a gold visor rim, in solid regions.
  * A leading space in the ramp, so empty areas clear to nothing.
"""
import math
import os
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source-prepped.png"
OUT = ROOT / "dhruv-ascii.svg"

RAMP = " .`:-=+*cs#%@"   # bright (sparse) -> dark (dense)
#       ^ leading space clears the background to nothing

COLS = 88
FONT_SIZE = 7.0
CHAR_W = FONT_SIZE * 0.6      # monospace advance width
LINE_H = FONT_SIZE * 1.02     # tight leading so the grid reads as a solid image
PAD = 14

INK = "#f0f6fc"               # thin glyphs on a dark card need a bright ink
ACCENT = "#79c0ff"            # visor reflection, chest lights, typing cursor
CURSOR = ACCENT
BG = "#0d1117"
BORDER = "#30363d"

ROW_DUR = 0.42                # how long one row takes to wipe in
ROW_STAGGER = 0.028           # delay added per row
START = 0.2

STATIC = os.environ.get("STATIC") == "1"

# --- avatar ----------------------------------------------------------------
AVATAR_ROWS = 76
SUB = 3                       # samples per glyph each way, so edges stay smooth
PALETTE = {"C": ACCENT, "R": "#f2cc60"}   # ink keys; "." is plain INK

CX = COLS * CHAR_W / 2        # the figure is laid out around the centre line
HEAD_Y, HEAD_R = 206, 136
VISOR_Y, VISOR_A, VISOR_B = HEAD_Y - 8, 108, 88
GLOBE_X, GLOBE_Y, GLOBE_R = CX + 42, HEAD_Y + 196, 170    # reflected in the visor
GLINTS = [(CX - 46, VISOR_Y - 44), (CX + 28, VISOR_Y - 58), (CX + 66, VISOR_Y - 18),
          (CX - 74, VISOR_Y + 2), (CX + 2, VISOR_Y - 30), (CX - 20, VISOR_Y - 66)]


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def unit(x, y, z):
    n = math.sqrt(x * x + y * y + z * z)
    return x / n, y / n, z / n


LIGHT = unit(-0.52, -0.62, 0.58)


def box(x, y, cx, cy, hx, hy, r=0.0):
    """Signed distance to a rounded rectangle: negative inside."""
    dx, dy = abs(x - cx) - hx + r, abs(y - cy) - hy + r
    return math.hypot(max(dx, 0.0), max(dy, 0.0)) + min(max(dx, dy), 0.0) - r


def ball(dx, dy, r, floor, power):
    """Lambert tone at (dx, dy) on a sphere of radius r, or None outside it."""
    nx, ny = dx / r, dy / r
    q = 1 - nx * nx - ny * ny
    if q < 0:
        return None
    diff = max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + math.sqrt(q) * LIGHT[2])
    return floor + (1 - floor) * diff ** power


def astronaut(x, y):
    """(ink density 0..1, ink key) at pixel (x, y) of the text area."""
    v, k = 0.0, "."
    # suit
    d = box(x, y, CX, 568, 168, 212, 110)
    if d < 0:
        nx = clamp((x - CX - 18) / 168, -1, 1)
        ny = clamp((y - 470) / 190, -1, 1)
        nz = math.sqrt(max(0.05, 1 - 0.8 * nx * nx - 0.5 * ny * ny))
        diff = max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])
        v = 0.2 + 0.8 * diff
        v -= 0.14 * max(0.0, math.sin((x - CX) * 0.11 + y * 0.035)) ** 6   # folds
        if d > -3.5:
            v = 0.92
    # chest unit
    d = box(x, y, CX, 470, 70, 40, 8)
    if d < 0:
        v, k = (0.86, ".") if d > -3.5 else (0.08, ".")
        for i, bx in enumerate((-40, -14, 12, 38)):
            if box(x, y, CX + bx, 460, 8, 7) < 0:
                v, k = (1.0, "C") if i != 2 else (0.5, "C")
        if box(x, y, CX, 488, 46, 3.6) < 0:
            v, k = 0.6, "."
    # collar
    e = ((x - CX) / 104) ** 2 + ((y - 338) / 30) ** 2
    if e < 1:
        v, k = (0.2 if e < 0.55 else 0.86), "."
    # ear pods
    for side in (-1, 1):
        d = box(x, y, CX + side * 142, HEAD_Y + 6, 14, 42, 9)
        if d < 0:
            v = 0.76 + side * -0.3
            if d > -3:
                v = 0.9
    # helmet
    tone = ball(x - CX, y - HEAD_Y, HEAD_R, 0.05, 1.1)
    if tone is not None:
        v, k = 0.2 + 0.8 * tone, "."
        # visor: gold rim, dark glass, a globe, a few stars and a glare arc
        q = abs((x - CX) / VISOR_A) ** 2.7 + abs((y - VISOR_Y) / VISOR_B) ** 2.7
        if q < 1:
            if q > 0.84:
                return 0.97, "R"
            v, k = 0.015, "."
            d = math.hypot(x - GLOBE_X, y - GLOBE_Y)
            if d < GLOBE_R:
                return 0.22 + 0.72 * math.exp(-(GLOBE_R - d) / 16), "C"
            for gx, gy in GLINTS:
                if math.hypot(x - gx, y - gy) < 2.6:
                    return 0.95, "."
            arc = math.hypot(x - CX - 26, y - VISOR_Y - 34)
            if 104 < arc < 113 and x < CX - 18 and y < VISOR_Y - 2:
                return 0.82, "."
    return v, k


def avatar_rows():
    """The figure sampled onto the glyph grid: (rows of glyphs, rows of ink keys)."""
    rows, inks = [], []
    for r in range(AVATAR_ROWS):
        line, keys = [], []
        for c in range(COLS):
            total, votes = 0.0, {}
            for j in range(SUB):
                y = (r + (j + 0.5) / SUB) * LINE_H
                for i in range(SUB):
                    v, k = astronaut((c + (i + 0.5) / SUB) * CHAR_W, y)
                    total += v
                    votes[k] = votes.get(k, 0.0) + v + 1e-4
            ch = RAMP[round(clamp(total / SUB ** 2) * (len(RAMP) - 1))]
            line.append(ch)
            keys.append(max(votes, key=votes.get) if ch != " " else ".")
        rows.append(line)
        inks.append(keys)

    # Stars, only where a glyph and all its neighbours are empty.
    rng = random.Random(3)
    for _ in range(120):
        r, c = rng.randrange(1, AVATAR_ROWS - 1), rng.randrange(1, COLS - 1)
        near = [rows[r + j][c + i] for j in (-1, 0, 1) for i in (-1, 0, 1)]
        if all(ch == " " for ch in near):
            rows[r][c] = rng.choice("...``:+*")
            inks[r][c] = "."
    return ["".join(r) for r in rows], ["".join(k) for k in inks]


# --- photo portrait --------------------------------------------------------
def photo_rows():
    import numpy as np            # heavy deps: only the photo path pays for them
    from PIL import Image

    img = Image.open(SRC)
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


def spans(text, keys):
    """Give each run of same-ink glyphs its own fill."""
    out, start = [], 0
    for end in range(1, len(text) + 1):
        if end == len(text) or keys[end] != keys[start]:
            run, fill = esc(text[start:end]), PALETTE.get(keys[start])
            out.append(f'<tspan fill="{fill}">{run}</tspan>' if fill else run)
            start = end
    return "".join(out)


def render(rows, inks=None):
    text_w = COLS * CHAR_W
    width = round(text_w + PAD * 2)
    height = round(len(rows) * LINE_H + PAD * 2)

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="ASCII avatar">',
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
        f'font-size="{FONT_SIZE}" fill="{INK}">')
    for i, row in enumerate(rows):
        ink = row.strip()
        if not ink:
            continue
        # Pin every row to the grid. The fallback fonts differ in advance width,
        # and an unpinned row drifts out of column wherever CHAR_W is a guess.
        # xml:space must sit on the <text> itself: browsers ignore it on a <g>,
        # which collapses inner gaps and lets textLength smear the whole row.
        lead = len(row) - len(row.lstrip())
        x = PAD + lead * CHAR_W
        y = PAD + (i + 1) * LINE_H
        body = esc(ink) if inks is None else spans(ink, inks[i][lead:])
        add(f'<text clip-path="url(#w{i})" x="{x:.1f}" y="{y:.2f}" '
            f'textLength="{len(ink) * CHAR_W:.1f}" lengthAdjust="spacing" '
            f'xml:space="preserve">'
            f'{body}</text>')
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
        rows, inks = photo_rows(), None
        print(f"source: {SRC.name}")
    else:
        rows, inks = avatar_rows()
        print(f"no {SRC.name} -- drawing the astronaut")

    OUT.write_text(render(rows, inks), encoding="utf-8")
    print(f"wrote {OUT.name} ({COLS}x{len(rows)} chars"
          f"{', static' if STATIC else ''})")


if __name__ == "__main__":
    main()
