"""Build Windows lock screen (2560x1440) — center clear for clock/date UI."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from brand_config import CARBON, HERO_ACCENT, ICE_DIM, SLUG
from brand_render import render_monogram, render_race_number, render_tagline, render_wordmark

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lock-screen")

ROOT = Path(__file__).resolve().parent
ASSETS = Path(
    r"C:\Users\simot\.cursor\projects\c-Users-simot-Documents-Projects-fixminibeast\assets"
)
OUT_PNG = ROOT / f"{SLUG}_lock_screen_2560x1440.png"
OUT_JPG = ROOT / f"{SLUG}_lock_screen_2560x1440.jpg"

W, H = 2560, 1440


def load_bg(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    sw, sh = img.size
    scale = max(W / sw, H / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - W) // 2, (nh - H) // 2
    img = img.crop((left, top, left + W, top + H))
    img = ImageEnhance.Brightness(img).enhance(0.38)
    img = ImageEnhance.Color(img).enhance(0.88)
    img = ImageEnhance.Contrast(img).enhance(1.12)
    return img.convert("RGBA")


def build() -> Path:
    t0 = time.perf_counter()
    photo = next(
        (p for p in (ASSETS / "smarcato42_slide_c.png", ASSETS / "smarcato42_photo_center.png", ASSETS / "smarcato42_slide_a.png") if p.exists()),
        None,
    )
    if photo is None:
        raise FileNotFoundError("missing racing photo")

    log.info("start lock screen %dx%d from %s", W, H, photo.name)
    bg = load_bg(photo)

    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    vd.ellipse([int(W * 0.22), int(H * 0.08), int(W * 0.78), int(H * 0.62)], fill=(0, 0, 0, 90))
    vd.rectangle([0, int(H * 0.62), W, H], fill=(0, 0, 0, 120))
    veil = veil.filter(ImageFilter.GaussianBlur(40))
    bg = Image.alpha_composite(bg, veil)

    bar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rectangle([0, 0, 8, H], fill=(*HERO_ACCENT, 255))
    bg = Image.alpha_composite(bg, bar)

    word = render_wordmark(64)
    mark = render_race_number(220, HERO_ACCENT)
    tag = render_tagline(26, ICE_DIM, tracking=12)

    stack_w = max(word.width, mark.width, tag.width)
    gap1, gap2 = 12, 10
    stack_h = word.height + gap1 + mark.height + gap2 + tag.height
    brand = Image.new("RGBA", (stack_w, stack_h), (0, 0, 0, 0))
    y = 0
    for im, g in ((word, gap1), (mark, gap2), (tag, 0)):
        brand.alpha_composite(im, ((stack_w - im.width) // 2, y))
        y += im.height + g

    bx = (W - brand.width) // 2
    by = min(int(H * 0.70) - brand.height // 2, H - brand.height - 80)

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        [bx - 30, by, bx + brand.width + 30, by + brand.height],
        fill=(*HERO_ACCENT, 40),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    bg = Image.alpha_composite(bg, glow)
    bg.alpha_composite(brand, (bx, by))

    mono = render_monogram(78)
    mx, my = 28, H - mono.height - 28
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle(
        [mx - 10, my - 10, mx + mono.width + 10, my + mono.height + 10],
        radius=8,
        fill=(*CARBON, 140),
    )
    bg = Image.alpha_composite(bg, plate)
    bg.alpha_composite(mono, (mx, my))

    final = bg.convert("RGB")
    final.save(OUT_PNG, "PNG", optimize=True)
    final.save(OUT_JPG, "JPEG", quality=94, optimize=True)
    log.info("saved %s in %.0f ms", OUT_PNG.name, (time.perf_counter() - t0) * 1000)
    return OUT_JPG


if __name__ == "__main__":
    build()
