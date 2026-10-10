#!/usr/bin/env python3
"""Draw the ASCII card that types itself: pixel Iron Man, or a photo portrait.

    python scripts/make_ascii_svg.py            # -> dhruv-ascii.svg
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, for previewing

No photo needed: without source-prepped.png the card is a chibi Iron Man
sprite, each pixel printed as a small block of glyphs, standard library only.
Run prep_photo.py first and it becomes a portrait of that photo instead (that
path needs pillow + numpy).

Each row lives inside its own clip rect whose width animates 0 -> full, so the
row wipes in left-to-right with a block cursor riding the edge. Rows are
staggered top to bottom. It prints once and freezes -- no looping.

Two rules keep a portrait looking like a picture and not like static:
  * ONE colour. Per-character rainbow fills are what ruin most ASCII art.
  * A leading space in the ramp, so empty areas clear to nothing.
The sprite is the exception on colour: flat pixel-art inks, one per region.
"""
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
# One letter per pixel: K outline, R red, Y gold, W white, . empty.
SPRITE = """
......KKKKK......
....KKRRRRRKK....
...KRRRRRRRRRK...
..KRRYYRRRYYRRK..
..KRYYYYRYYYYRK..
.KRRYYYYYYYYYRRK.
.KRYYYYYYYYYYYRK.
.KRYKKKKYKKKKYRK.
.KRYWWWKYKWWWYRK.
.KRYYYYYYYYYYYRK.
.KRRYYYYYYYYYRRK.
..KRYYKKKKKYYRK..
..KRRYYYYYYYRRK..
...KKRRRRRRRKK...
....KKKKKKKKK....
..KKRRRRRRRRRKK..
.KYYRKRWWWRKRYYK.
KRRYRKRRWRRKRYRRK
KRRKKRRRRRRRKKRRK
.KK.KRRYYYRRK.KK.
....KRRRKRRRK....
...KYYRK.KRYYK...
...KRRRK.KRRRK...
..KRRRRK.KRRRRK..
..KKKKKK.KKKKKK..
""".split()

PIXEL_W, PIXEL_H = 5, 3       # glyphs per pixel: 21 x 21.4 px, as good as square
GLYPH = {"K": "#", "R": "%", "Y": "#", "W": "@", ".": " "}
PALETTE = {"K": "#484f58", "R": "#f85149", "Y": "#e3b341", "W": "#f0f6fc"}


def avatar_rows():
    """The sprite blown up to the glyph grid: (rows of glyphs, rows of ink keys)."""
    left = (COLS - len(SPRITE[0]) * PIXEL_W) // 2
    rows, inks = [], []
    for line in SPRITE:
        keys = ("." * left + "".join(k * PIXEL_W for k in line)).ljust(COLS, ".")
        rows += ["".join(GLYPH[k] for k in keys)] * PIXEL_H
        inks += [keys] * PIXEL_H
    return rows, inks


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
        f'font-size="{FONT_SIZE}" fill="{INK}" xml:space="preserve">')
    for i, row in enumerate(rows):
        ink = row.strip()
        if not ink:
            continue
        # Pin every row to the grid. The fallback fonts differ in advance width,
        # and an unpinned row drifts out of column wherever CHAR_W is a guess.
        lead = len(row) - len(row.lstrip())
        x = PAD + lead * CHAR_W
        y = PAD + (i + 1) * LINE_H
        body = esc(ink) if inks is None else spans(ink, inks[i][lead:])
        add(f'<text clip-path="url(#w{i})" x="{x:.1f}" y="{y:.2f}" '
            f'textLength="{len(ink) * CHAR_W:.1f}" lengthAdjust="spacing">'
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
        print(f"no {SRC.name} -- drawing pixel Iron Man")

    OUT.write_text(render(rows, inks), encoding="utf-8")
    print(f"wrote {OUT.name} ({COLS}x{len(rows)} chars"
          f"{', static' if STATIC else ''})")


if __name__ == "__main__":
    main()
