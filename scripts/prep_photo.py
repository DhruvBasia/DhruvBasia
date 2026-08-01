#!/usr/bin/env python3
"""Prep a photo so it converts to *readable* ASCII instead of a dark blob.

    python scripts/prep_photo.py source-photo.jpg

Three things matter, in this order:
  1. Cut the background out (rembg) so only the subject prints.
  2. Boost *local* contrast (CLAHE) -- a flatly-lit face has no highlights or
     shadows for the glyph ramp to grab onto, and comes out as mush.
  3. Composite onto pure white, so the background maps to the blank end of
     the ramp (white -> space) and disappears.

rembg and opencv are optional; the script degrades gracefully without them,
it just won't look as good. Run it once per photo -- the daily GitHub Action
never touches this file.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "source-prepped.png"
MAX_SIDE = 1400
PAD = 0.04  # fraction of the subject bbox to keep as breathing room


def cut_background(img: Image.Image) -> Image.Image:
    """RGBA with the background alpha'd out. Falls back to the original."""
    try:
        from rembg import remove
    except ImportError:
        print("  ! rembg not installed -- keeping background "
              "(pip install rembg for a much cleaner portrait)")
        return img.convert("RGBA")
    print("  · removing background")
    return remove(img).convert("RGBA")


def local_contrast(gray: np.ndarray) -> np.ndarray:
    """CLAHE if OpenCV is around, otherwise a global autocontrast."""
    try:
        import cv2
    except ImportError:
        print("  ! opencv not installed -- global autocontrast only")
        return np.asarray(
            ImageOps.autocontrast(Image.fromarray(gray), cutoff=2), dtype=np.uint8
        )
    print("  · CLAHE local contrast")
    clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
    return clahe.apply(gray)


def crop_to_subject(rgba: Image.Image) -> Image.Image:
    bbox = rgba.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    if not bbox:
        return rgba
    x0, y0, x1, y1 = bbox
    px, py = int((x1 - x0) * PAD), int((y1 - y0) * PAD)
    return rgba.crop(
        (max(0, x0 - px), max(0, y0 - py),
         min(rgba.width, x1 + px), min(rgba.height, y1 + py))
    )


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python scripts/prep_photo.py <photo.jpg>")
    src = Path(sys.argv[1])
    if not src.exists():
        sys.exit(f"no such file: {src}")

    img = Image.open(src).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    print(f"loaded {src.name} ({img.width}x{img.height})")

    rgba = crop_to_subject(cut_background(img))

    # Composite onto white BEFORE grayscaling, so cut-out areas read as blank.
    white = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(white, rgba).convert("L")

    boosted = local_contrast(np.asarray(flat, dtype=np.uint8))

    # Gentle S-curve: push darks darker and lights lighter so the ramp spreads.
    x = boosted.astype(np.float32) / 255.0
    curved = np.clip((x - 0.5) * 1.18 + 0.5, 0, 1)
    final = Image.fromarray((curved * 255).astype(np.uint8), mode="L")

    final.save(OUT)
    print(f"wrote {OUT.name} ({final.width}x{final.height})")
    print("next: python scripts/make_ascii_svg.py")


if __name__ == "__main__":
    main()
