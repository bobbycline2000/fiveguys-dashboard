"""Generate PWA icons for the Five Guys / Estep dashboard app.

Renders 3 PNG icons:
  - icon-192.png   (Android home screen)
  - icon-512.png   (Android splash + maskable)
  - apple-touch-icon.png (180x180 — iOS home screen)

Five Guys red (#C8102E) background, white "FG" wordmark, simple and
recognizable at a glance.

Run: python scripts/build_pwa_icons.py
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
ICONS_DIR = REPO / "icons"
ICONS_DIR.mkdir(exist_ok=True)

RED   = (200, 16, 46, 255)   # #C8102E Five Guys red
WHITE = (255, 255, 255, 255)
GOLD  = (217, 169, 59, 255)  # #D9A93B accent


def _font(px: int) -> ImageFont.FreeTypeFont:
    """Try a few common bold fonts; fall back to default."""
    for name in (
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/HelveticaNeueBd.ttf",
        "C:/Windows/Fonts/segoeuib.ttf",
        "Arial Bold.ttf", "Arial.ttf",
    ):
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def build(path: Path, size: int, *, maskable: bool = False) -> None:
    img = Image.new("RGBA", (size, size), RED)
    draw = ImageDraw.Draw(img)

    # Maskable icons need a "safe zone" — 80% of canvas. Non-maskable can
    # fill edge-to-edge with a small inner card.
    safe = int(size * (0.80 if maskable else 0.92))
    pad = (size - safe) // 2

    # Rounded inner card (slightly darker red for depth, only on non-maskable)
    if not maskable:
        draw.rounded_rectangle(
            (pad, pad, size - pad, size - pad),
            radius=int(size * 0.18),
            fill=RED,
            outline=GOLD,
            width=max(2, size // 80),
        )

    # Wordmark "FG"
    txt = "FG"
    font_px = int(safe * 0.65)
    font = _font(font_px)
    bbox = draw.textbbox((0, 0), txt, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1] - int(size * 0.02)
    # Shadow for depth
    draw.text((tx + max(2, size // 120), ty + max(2, size // 120)), txt,
              font=font, fill=(120, 8, 24, 200))
    draw.text((tx, ty), txt, font=font, fill=WHITE)

    # Small "2065" pill at the bottom (only at larger sizes)
    if size >= 192:
        tag = "2065"
        tag_font_px = max(14, int(size * 0.08))
        tag_font = _font(tag_font_px)
        tbox = draw.textbbox((0, 0), tag, font=tag_font)
        ttw = tbox[2] - tbox[0]
        tth = tbox[3] - tbox[1]
        tag_pad_x = int(size * 0.04)
        tag_pad_y = int(size * 0.012)
        tag_x = (size - ttw) // 2 - tbox[0]
        tag_y = size - int(size * 0.18) - tth
        draw.rounded_rectangle(
            (tag_x - tag_pad_x, tag_y - tag_pad_y,
             tag_x + ttw + tag_pad_x, tag_y + tth + tag_pad_y),
            radius=int(size * 0.05),
            fill=GOLD,
        )
        draw.text((tag_x, tag_y), tag, font=tag_font, fill=(20, 20, 20, 255))

    img.save(path, "PNG", optimize=True)
    print(f"wrote {path.name} ({size}x{size})")


def main() -> None:
    build(ICONS_DIR / "icon-192.png", 192)
    build(ICONS_DIR / "icon-512.png", 512)
    build(ICONS_DIR / "icon-512-maskable.png", 512, maskable=True)
    build(ICONS_DIR / "apple-touch-icon.png", 180)
    build(ICONS_DIR / "favicon-32.png", 32)


if __name__ == "__main__":
    main()
