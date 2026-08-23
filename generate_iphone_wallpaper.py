"""Generate L.Sforzini 44 hybrid wallpapers for iPhone 15 family.

Layout: carbon band at top (clock/notifications), photo mid, soft brand footer.
Preserves lock-screen readability — no brand marks in Dynamic Island / clock zone.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
from brand_config import BRAND_SHORT, CARBON, HERO_ACCENT, ICE, ICE_DIM, RACE_NUMBER, SLUG, TAGLINE
from brand_render import render_race_number, render_tagline, render_wordmark

log = logging.getLogger("lsforzini44.iphone")

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "iphone"
ASSETS = Path(
    r"C:\Users\simot\.cursor\projects\c-Users-simot-Documents-Projects-fixminibeast\assets"
)

SIZES = (
    (f"{SLUG}_iphone15_1179x2556", 1179, 2556),
    (f"{SLUG}_iphone15plus_1290x2796", 1290, 2796),
)


def fit_cover(src: Image.Image, tw: int, th: int) -> Image.Image:
    img = src.convert("RGB")
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    # Slight upward bias keeps horizon/lights in mid band under the clock veil
    top = max(0, min((nh - th) // 2 - th // 20, nh - th))
    return img.crop((left, top, left + tw, top + th))


def grade_photo(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Color(img).enhance(1.10)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    # Keep mid-frame photo readable; carbon bands handle clock contrast
    img = ImageEnhance.Brightness(img).enhance(0.94)
    return img


def resolve_photo() -> Path:
    # Prefer wider pit scenes that still read after portrait cover-crop
    candidates = (
        ASSETS / "smarcato42_slide_c.png",
        ASSETS / "smarcato42_slide_a.png",
        ASSETS / "smarcato42_photo_center.png",
        ROOT / "smarcato42_photo_center.png",
        ASSETS / "smarcato42_photo_left.png",
    )
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("no racing photo found for iPhone wallpaper")


def render_wordmark_footer(size: int, alpha: int = 220) -> Image.Image:
    mark = render_wordmark(size, ICE)
    alpha_ch = mark.split()[-1].point(lambda a: int(a * alpha / 255))
    mark.putalpha(alpha_ch)
    return mark


def extract_race_mark(target_h: int) -> Image.Image:
    mark = render_race_number(max(72, target_h), HERO_ACCENT)
    ratio = target_h / mark.height
    return mark.resize((max(1, int(mark.width * ratio)), target_h), Image.Resampling.LANCZOS)


def render_tag(size: int, alpha: int = 170) -> Image.Image:
    tag = render_tagline(size, ICE_DIM)
    alpha_ch = tag.split()[-1].point(lambda a: int(a * alpha / 255))
    tag.putalpha(alpha_ch)
    return tag


def vertical_band_gradient(
    w: int, h: int, top_frac: float, bottom_frac: float
) -> Image.Image:
    """Carbon fade from top and bottom; mid stays transparent for photo."""
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    top_h = int(h * top_frac)
    bot_h = int(h * bottom_frac)
    for y in range(h):
        if y < top_h:
            # Strong solid near top, fade to transparent
            t = y / max(1, top_h - 1)
            # Stay opaque through clock zone, then open to photo
            ease = t ** 2.4
            a = int(235 * (1.0 - ease))
        elif y > h - bot_h:
            # Fade in toward bottom for soft brand plate
            t = (y - (h - bot_h)) / max(1, bot_h - 1)
            ease = t ** 0.9
            a = int(210 * ease)
        else:
            # Very light mid veil — keep GT photo visible
            a = 18
        if a <= 0:
            continue
        c = (*CARBON, a)
        for x in range(w):
            px[x, y] = c
    return overlay.filter(ImageFilter.GaussianBlur(1))


def compose(w: int, h: int, photo_path: Path) -> Image.Image:
    t_step = time.perf_counter()
    log.info("compose %dx%d from %s", w, h, photo_path.name)

    bg = grade_photo(fit_cover(Image.open(photo_path), w, h)).convert("RGBA")
    log.info("photo fitted in %.0f ms", (time.perf_counter() - t_step) * 1000)

    t_step = time.perf_counter()
    bands = vertical_band_gradient(w, h, top_frac=0.28, bottom_frac=0.22)
    bg = Image.alpha_composite(bg, bands)
    # Extra solid top plate so iOS white clock stays crisp
    clock_plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clock_plate)
    clock_h = int(h * 0.14)
    for i in range(clock_h):
        a = int(200 * (1.0 - (i / max(1, clock_h - 1)) ** 2.6))
        cd.line([(0, i), (w, i)], fill=(*CARBON, a))
    bg = Image.alpha_composite(bg, clock_plate)
    log.info("carbon bands applied in %.0f ms", (time.perf_counter() - t_step) * 1000)

    # Soft brand footer — stays above home indicator (~bottom 6%)
    t_step = time.perf_counter()
    scale = w / 1179
    word = render_wordmark_footer(max(28, int(42 * scale)), alpha=210)
    mark = extract_race_mark(max(72, int(110 * scale)))
    # Soften 42 slightly so it does not overpower lock widgets
    mark_soft = Image.new("RGBA", mark.size, (0, 0, 0, 0))
    mark_soft.alpha_composite(mark)
    mark_soft.putalpha(mark_soft.split()[-1].point(lambda a: int(a * 0.88)))
    tag = render_tag(max(14, int(18 * scale)), alpha=160)

    gap1, gap2 = int(10 * scale), int(8 * scale)
    stack_w = max(word.width, mark_soft.width, tag.width)
    stack_h = word.height + gap1 + mark_soft.height + gap2 + tag.height
    brand = Image.new("RGBA", (stack_w, stack_h), (0, 0, 0, 0))
    y = 0
    for im, gap in ((word, gap1), (mark_soft, gap2), (tag, 0)):
        brand.alpha_composite(im, ((stack_w - im.width) // 2, y))
        y += im.height + gap

    # Hairline above brand
    hair = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hair)
    cx = w // 2
    by = int(h * 0.825) - brand.height // 2
    by = min(by, h - brand.height - int(h * 0.07))
    line_y = by - int(14 * scale)
    hd.line([(cx - int(48 * scale), line_y), (cx + int(48 * scale), line_y)], fill=(*ICE, 110), width=1)
    bg = Image.alpha_composite(bg, hair)

    shadow = Image.new("RGBA", brand.size, (0, 0, 0, 0))
    sa = brand.split()[-1]
    shadow_layer = Image.new("RGBA", brand.size, (0, 0, 0, 160))
    shadow_layer.putalpha(sa)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(max(6, int(10 * scale))))
    bx = (w - brand.width) // 2
    bg.alpha_composite(shadow_layer, (bx + 2, by + 4))
    bg.alpha_composite(brand, (bx, by))
    log.info(
        "brand footer at (%d,%d) %dx%d in %.0f ms",
        bx,
        by,
        brand.width,
        brand.height,
        (time.perf_counter() - t_step) * 1000,
    )

    return bg.convert("RGB")


def main() -> None:
    t0 = time.perf_counter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    photo = resolve_photo()
    log.info("start iPhone hybrid wallpapers | photo=%s | out=%s", photo, OUT_DIR)

    written: list[Path] = []
    for stem, w, h in SIZES:
        t_size = time.perf_counter()
        img = compose(w, h, photo)
        out = OUT_DIR / f"{stem}.png"
        img.save(out, "PNG", optimize=True)
        written.append(out)
        log.info(
            "saved %s (%.0f KB) in %.0f ms",
            out.name,
            out.stat().st_size / 1024,
            (time.perf_counter() - t_size) * 1000,
        )

    elapsed = time.perf_counter() - t0
    log.info(
        "done in %.2fs | %d files | total=%.1f MB",
        elapsed,
        len(written),
        sum(p.stat().st_size for p in written) / (1024 * 1024),
    )


if __name__ == "__main__":
    main()
