"""Asset generator — produces AI-style abstract art placeholders.

Each product gets a unique, seeded piece of generative art (soft gradient
field + translucent orbs + flowing sine ribbons + a gold hairline) in a
light academic palette, so the store looks designed rather than mocked.
Runs offline with Pillow only. Re-run any time:  python scripts_gen_assets.py
"""
from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

# warm academic palette — light but lively
IVORY = (255, 253, 249)
PAPER = (248, 242, 231)
MAROON = (139, 51, 85)          # richer IISc maroon
MAROON_DEEP = (102, 32, 62)
GOLD = (201, 155, 47)
GOLD_PALE = (240, 223, 174)
SAGE = (149, 168, 124)
SLATE = (117, 138, 171)
BLUSH = (222, 154, 167)
TERRA = (204, 132, 92)

# per-category tint so shelves read as families
CATEGORY_TINTS = {
    "Apparel": BLUSH,
    "Drinkware": SLATE,
    "Stationery": SAGE,
    "Accessories": GOLD_PALE,
    "Memorabilia": (205, 170, 150),
}

PRODUCTS = [
    ("tshirt", "Apparel"), ("hoodie", "Apparel"), ("cap", "Apparel"),
    ("mug", "Drinkware"), ("bottle", "Drinkware"), ("flask", "Drinkware"),
    ("notebook", "Stationery"), ("penset", "Stationery"),
    ("sleeve", "Accessories"), ("backpack", "Accessories"),
    ("badge", "Memorabilia"), ("stickers", "Memorabilia"),
]


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _lerp(a, b, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _vertical_gradient(size, top, bottom) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=_lerp(top, bottom, y / h))
    return img


def _orbs(draw: ImageDraw.ImageDraw, size, rng, colors, count=5) -> None:
    """Large translucent circles drifting through the frame."""
    w, h = size
    for _ in range(count):
        r = rng.randint(int(w * 0.18), int(w * 0.42))
        x = rng.randint(-r // 2, w - r // 2)
        y = rng.randint(-r // 2, h - r // 2)
        color = rng.choice(colors)
        alpha = rng.randint(50, 105)
        draw.ellipse([x, y, x + r, y + r], fill=color + (alpha,))


def _ribbons(draw: ImageDraw.ImageDraw, size, rng, colors, count=3) -> None:
    """Flowing sine ribbons — the 'generative' signature of each piece."""
    w, h = size
    for _ in range(count):
        color = rng.choice(colors)
        alpha = rng.randint(100, 160)
        amp = rng.uniform(h * 0.04, h * 0.12)
        freq = rng.uniform(1.1, 2.6)
        phase = rng.uniform(0, math.tau)
        base_y = rng.uniform(h * 0.25, h * 0.8)
        thickness = rng.randint(8, 20)
        points = [
            (x, base_y + amp * math.sin(freq * math.tau * x / w + phase))
            for x in range(0, w + 8, 8)
        ]
        draw.line(points, fill=color + (alpha,), width=thickness, joint="curve")


def abstract_art(size, seed: str, tint, label: str | None = None) -> Image.Image:
    """Compose one seeded abstract piece."""
    rng = random.Random(seed)
    w, h = size

    base = _vertical_gradient(size, IVORY, _lerp(PAPER, tint, 0.62))

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    palette = [MAROON, GOLD, tint, MAROON_DEEP, TERRA]
    _orbs(d, size, rng, palette, count=rng.randint(4, 6))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=w // 24))

    sharp = Image.new("RGBA", size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(sharp)
    _ribbons(d2, size, rng, [MAROON, GOLD, MAROON_DEEP], count=rng.randint(2, 4))
    sharp = sharp.filter(ImageFilter.GaussianBlur(radius=1))

    art = base.convert("RGBA")
    art.alpha_composite(overlay)
    art.alpha_composite(sharp)

    d3 = ImageDraw.Draw(art)
    # gold hairline footer — ties every piece to the brand
    d3.rectangle([int(w * 0.30), h - 14, int(w * 0.70), h - 10], fill=GOLD + (255,))
    if label:
        d3.text((w // 2, h - 44), label, font=_font(26),
                fill=MAROON_DEEP + (220,), anchor="mm")
    return art.convert("RGB")


def logo() -> None:
    img = Image.new("RGBA", (240, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse([10, 10, 230, 230], fill=IVORY + (255,))
    d.ellipse([10, 10, 230, 230], outline=MAROON + (255,), width=6)
    d.ellipse([24, 24, 216, 216], outline=GOLD + (255,), width=3)
    d.text((120, 104), "IISc", font=_font(76), fill=MAROON + (255,), anchor="mm")
    d.text((120, 164), "ALUMNI", font=_font(20), fill=GOLD + (255,), anchor="mm")
    img.save(os.path.join(ASSETS, "logo.png"))


BANNERS = [
    ("banner_1", GOLD_PALE, "IISc Alumni Store",
     "Crafted for the Institute community."),
    ("banner_2", BLUSH, "Convocation 2026 Collection",
     "Limited-edition tees, pen sets and keepsakes."),
    ("banner_3", SAGE, "Free shipping above \u20b9999",
     "Applied automatically at checkout, across India."),
    ("banner_4", SLATE, "Every purchase gives back",
     "Surplus funds scholarships and heritage restoration."),
]


def banners() -> None:
    size = (1600, 440)
    for name, tint, title, subtitle in BANNERS:
        art = abstract_art(size, seed=f"iisc-{name}-2026", tint=tint)
        d = ImageDraw.Draw(art)
        d.text((80, 140), title, font=_font(78), fill=MAROON_DEEP)
        d.text((84, 250), subtitle, font=_font(30), fill=MAROON)
        d.rectangle([84, 320, 324, 326], fill=GOLD)
        art.save(os.path.join(ASSETS, f"{name}.jpg"), quality=90)




def campus() -> None:
    """Stylised IISc Main Building placeholder — swap with a real campus photo."""
    w, h = 900, 620
    img = _vertical_gradient((w, h), (250, 244, 228), (255, 252, 245))
    d = ImageDraw.Draw(img, "RGBA")

    # sun
    d.ellipse([w - 300, 60, w - 140, 220], fill=GOLD + (70,))
    d.ellipse([w - 272, 88, w - 168, 192], fill=GOLD + (110,))

    ground = h - 120
    B = MAROON_DEEP + (255,)

    def arch_windows(x0, x1, y0, y1, n):
        step = (x1 - x0) / n
        for i in range(n):
            wx0 = x0 + i * step + step * 0.25
            wx1 = x0 + i * step + step * 0.75
            d.rectangle([wx0, y0 + (y1 - y0) * 0.28, wx1, y1], fill=(250, 244, 228, 255))
            d.pieslice([wx0, y0, wx1, y0 + (y1 - y0) * 0.56], 180, 360,
                       fill=(250, 244, 228, 255))

    # side wings
    d.rectangle([80, ground - 150, 380, ground], fill=B)
    d.rectangle([w - 380, ground - 150, w - 80, ground], fill=B)
    arch_windows(100, 360, ground - 120, ground - 30, 4)
    arch_windows(w - 360, w - 100, ground - 120, ground - 30, 4)

    # central tower (Main Building silhouette)
    cx = w // 2
    d.rectangle([cx - 90, ground - 320, cx + 90, ground], fill=B)
    d.rectangle([cx - 60, ground - 150, cx + 60, ground], fill=(250, 244, 228, 255))
    d.pieslice([cx - 60, ground - 260, cx + 60, ground - 40], 180, 360,
               fill=(250, 244, 228, 255))
    # tiered roof + spire
    d.polygon([(cx - 100, ground - 320), (cx + 100, ground - 320), (cx + 70, ground - 360),
               (cx - 70, ground - 360)], fill=B)
    d.polygon([(cx - 45, ground - 360), (cx + 45, ground - 360), (cx, ground - 440)], fill=B)
    d.line([cx, ground - 440, cx, ground - 480], fill=GOLD + (255,), width=5)
    d.ellipse([cx - 6, ground - 492, cx + 6, ground - 480], fill=GOLD + (255,))

    # banyan trees
    for tx in (150, 260, w - 260, w - 150):
        d.rectangle([tx - 6, ground - 60, tx + 6, ground], fill=(90, 66, 46, 255))
        for dx, dy, r in ((-38, -95, 46), (30, -105, 52), (-4, -140, 44)):
            d.ellipse([tx + dx - r, ground + dy - r, tx + dx + r, ground + dy + r],
                      fill=(110, 130, 92, 235))

    # lawn + path
    d.rectangle([0, ground, w, h], fill=(196, 205, 168, 255))
    d.polygon([(cx - 34, ground), (cx + 34, ground), (cx + 110, h), (cx - 110, h)],
              fill=(236, 226, 200, 255))
    d.rectangle([0, ground - 2, w, ground + 2], fill=GOLD + (255,))

    d.text((cx, h - 46), "Indian Institute of Science  .  Bengaluru",
           font=_font(26), fill=MAROON_DEEP + (255,), anchor="mm")
    img.save(os.path.join(ASSETS, "campus.jpg"), quality=88)


if __name__ == "__main__":
    os.makedirs(os.path.join(ASSETS, "products"), exist_ok=True)
    logo()
    banners()
    campus()
    for key, category in PRODUCTS:
        art = abstract_art((640, 640), seed=f"iisc-{key}", tint=CATEGORY_TINTS[category])
        art.save(os.path.join(ASSETS, "products", f"{key}.png"))
    print("abstract assets generated")
