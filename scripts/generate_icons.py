#!/usr/bin/env python3
"""Generate Kotline PNG/ICO icons.

Primary path: downscale assets/branding/app_icon_master.png (a high-res render
of the logo) into the icon sizes, cropping to the artwork and applying a
transparent rounded-rectangle mask.

Fallback path: if no master image is present, draw a simple mark programmatically
so the build never breaks.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "branding"
MASTER = OUT / "app_icon_master.png"
SIZES = [16, 32, 48, 64, 128, 256]

BG = "#2a3142"
PLAN = "#c8d0dc"
ACCENT = "#4a90d9"


def _autocrop_to_artwork(img: Image.Image, tol: int = 24) -> Image.Image:
    """Crop a near-uniform border off the artwork and center it on a square.

    The generated master sits on a (near-)white background that is not perfectly
    uniform, so a tolerance is applied before computing the bounding box. The
    cropped artwork is then padded onto a transparent square canvas so later
    resizing never distorts or runs off the image edge.
    """
    from PIL import ImageChops

    rgb = img.convert("RGB")
    bg_img = Image.new("RGB", rgb.size, rgb.getpixel((0, 0)))
    diff = ImageChops.difference(rgb, bg_img).convert("L")
    mask = diff.point(lambda p: 255 if p > tol else 0)
    bbox = mask.getbbox()
    if not bbox:
        return img.convert("RGBA")

    art = img.convert("RGBA").crop(bbox)
    side = max(art.width, art.height)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(art, ((side - art.width) // 2, (side - art.height) // 2))
    return canvas


def _rounded_mask(size: int, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def _from_master(size: int, art: Image.Image) -> Image.Image:
    resized = art.resize((size, size), Image.LANCZOS).convert("RGBA")
    mask = _rounded_mask(size, radius=max(2, size // 5))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(resized, (0, 0), mask)
    return out


def _draw_fallback(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    r = max(2, size // 5)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=r, fill=BG)
    # stacked level datums forming a left stem
    stem_x = size * 0.30
    line_w = max(1, int(size / 22))
    for frac in (0.30, 0.48, 0.66, 0.82):
        y = size * frac
        draw.line((stem_x, y, size * 0.66, y), fill=PLAN, width=line_w)
        dr = max(1, size // 24)
        draw.ellipse((stem_x - dr, y - dr, stem_x + dr, y + dr), fill=ACCENT)
    draw.line((stem_x, size * 0.82, stem_x, size * 0.30), fill=PLAN, width=line_w)
    # diagonal section cut
    draw.line(
        (size * 0.30, size * 0.82, size * 0.74, size * 0.20),
        fill=ACCENT,
        width=max(2, int(size / 14)),
    )
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    art = None
    if MASTER.exists():
        try:
            art = _autocrop_to_artwork(Image.open(MASTER))
            print(f"using master {MASTER}")
        except OSError as exc:
            print(f"master unreadable ({exc}); using fallback")
            art = None
    else:
        print("no master image; using programmatic fallback")

    images = []
    for size in SIZES:
        img = _from_master(size, art) if art is not None else _draw_fallback(size)
        path = OUT / f"app_icon_{size}.png"
        img.save(path)
        images.append(img)
        print(f"wrote {path}")

    ico_path = OUT / "app_icon.ico"
    images[-1].save(ico_path, format="ICO", sizes=[(s, s) for s in SIZES])
    print(f"wrote {ico_path}")


if __name__ == "__main__":
    main()
