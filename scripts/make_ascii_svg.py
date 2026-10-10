#!/usr/bin/env python3
"""Draw the ASCII card that types itself: Iron Man, or a photo portrait.

    python scripts/make_ascii_svg.py            # -> dhruv-ascii.svg
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, for previewing

No photo needed: without source-prepped.png the card is an Iron Man bust drawn
from a handful of shapes, standard library only. Run prep_photo.py first and
it becomes a portrait of that photo instead (that path needs pillow + numpy).

Each row lives inside its own clip rect whose width animates 0 -> full, so the
row wipes in left-to-right with a block cursor riding the edge. Rows are
staggered top to bottom. It prints once and freezes -- no looping.

Two rules keep it looking like a picture and not like static:
  * ONE colour. Per-character rainbow fills are what ruin most ASCII art.
  * A leading space in the ramp, so empty areas clear to nothing.
"""
import math
import os
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

INK = "#c9d1d9"               # one colour, always
CURSOR = "#39d353"
BG = "#0d1117"
BORDER = "#30363d"

ROW_DUR = 0.42                # how long one row takes to wipe in
ROW_STAGGER = 0.028           # delay added per row
START = 0.2

STATIC = os.environ.get("STATIC") == "1"

# --- avatar ----------------------------------------------------------------
AVATAR_ROWS = 76
CX = COLS * CHAR_W / 2        # the helmet is laid out around the centre line
SUB_X, SUB_Y = 2, 3           # samples averaged per glyph, so edges stay smooth


def mirror(half):
    """Close a half outline, as (distance from centre line, y), into a polygon."""
    return ([(CX + dx, y) for dx, y in half]
            + [(CX - dx, y) for dx, y in reversed(half) if dx])


HELMET = mirror([(0, 22), (52, 26), (92, 46), (114, 84), (122, 130), (122, 178),
                 (116, 222), (104, 262), (78, 302), (46, 326), (0, 332)])
FACEPLATE = mirror([(0, 74), (60, 72), (86, 98), (93, 150), (88, 196), (64, 216),
                    (58, 262), (44, 300), (0, 306)])
CHEST = mirror([(0, 358), (50, 354), (96, 368), (150, 394), (176, 430),
                (180, 560), (0, 560)])
EYE = [(13, 171.4), (13, 163), (72, 152), (79, 158), (75, 171.4)]  # x from centre


def box(x, y, cx, cy, hx, hy, r=0.0):
    """Signed distance to a rounded rectangle: negative inside."""
    dx, dy = abs(x - cx) - hx + r, abs(y - cy) - hy + r
    return math.hypot(max(dx, 0.0), max(dy, 0.0)) + min(max(dx, dy), 0.0) - r


def poly(x, y, pts):
    """Signed distance to a polygon: negative inside."""
    d2, inside = math.inf, False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        ex, ey = x1 - x0, y1 - y0
        t = clamp(((x - x0) * ex + (y - y0) * ey) / (ex * ex + ey * ey))
        d2 = min(d2, (x - x0 - ex * t) ** 2 + (y - y0 - ey * t) ** 2)
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * ex / ey:
            inside = not inside
    return -math.sqrt(d2) if inside else math.sqrt(d2)


def paint(v, d, fill, rim=None, t=6.0):
    """Lay a shape over v: `rim` within t px of its edge, `fill` inside."""
    if d >= 0:
        return v
    if rim is not None and d > -t:
        return rim
    return fill


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def ironman(x, y):
    """Ink density, 0 (blank) to 1 (solid), at pixel (x, y) of the text area."""
    ax = abs(x - CX)
    lit = (CX - x) / 185 + (270 - y) / 270      # light falls from the top left
    v = 0.0
    if y > 320:
        # neck
        if box(x, y, CX, 346, 40, 22) < 0:
            v = 0.2
        # chest and shoulders
        v = paint(v, poly(x, y, CHEST), clamp(0.36 + 0.06 * lit, 0.2, 0.5), 0.86)
        # arc reactor: glow on the chest, then housing, ring and core
        r = math.hypot(x - CX, y - 462)
        if v:
            v = max(v, 0.75 * math.exp(-(max(r - 30, 0.0) / 18) ** 2))
        for radius, ink in ((30, 0.0), (25, 0.9), (18, 0.0), (13, 1.0)):
            if r < radius:
                v = ink
    if y < 340:
        # helmet shell
        v = paint(v, poly(x, y, HELMET), clamp(0.32 + 0.10 * lit, 0.2, 0.5), 0.88)
        # faceplate, with a dark seam just inside its edge
        v = paint(v, poly(x, y, FACEPLATE),
                  clamp(0.60 + 0.12 * lit, 0.5, 0.78), 0.0, 4.5)
        # eyes: bright slits in dark sockets
        if 135 < y < 195:
            e = poly(ax, y, EYE)
            if e < 6:
                v = 0.0
            if e < 0:
                v = 1.0
        # mouth slit
        if box(x, y, CX, 260.6, 30, 3.6) < 0:
            v = 0.0
    return v


def avatar_rows():
    rows = []
    for r in range(AVATAR_ROWS):
        line = []
        for c in range(COLS):
            acc = sum(
                ironman((c + (i + 0.5) / SUB_X) * CHAR_W,
                      (r + (j + 0.5) / SUB_Y) * LINE_H)
                for j in range(SUB_Y) for i in range(SUB_X)
            )
            v = clamp(acc / (SUB_X * SUB_Y))
            line.append(RAMP[round(v * (len(RAMP) - 1))])
        rows.append("".join(line))
    return rows


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


def render(rows):
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
        f'font-size="{FONT_SIZE}" fill="{INK}" xml:space="preserve">')
    for i, row in enumerate(rows):
        ink = row.strip()
        if not ink:
            continue
        # Pin every row to the grid. The fallback fonts differ in advance width,
        # and an unpinned row drifts out of column wherever CHAR_W is a guess.
        x = PAD + (len(row) - len(row.lstrip())) * CHAR_W
        y = PAD + (i + 1) * LINE_H
        add(f'<text clip-path="url(#w{i})" x="{x:.1f}" y="{y:.2f}" '
            f'textLength="{len(ink) * CHAR_W:.1f}" lengthAdjust="spacing">'
            f'{esc(ink)}</text>')
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
        rows = photo_rows()
        print(f"source: {SRC.name}")
    else:
        rows = avatar_rows()
        print(f"no {SRC.name} -- drawing Iron Man")

    OUT.write_text(render(rows), encoding="utf-8")
    print(f"wrote {OUT.name} ({COLS}x{len(rows)} chars"
          f"{', static' if STATIC else ''})")


if __name__ == "__main__":
    main()
