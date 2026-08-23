"""Build hybrid readability-first slideshow slides for L.Sforzini 44 screensaver."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

from brand_config import CARBON, HERO_ACCENT, ICE, ICE_DIM, SLUG
from brand_render import render_race_number, render_tagline, render_wordmark

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(f"{SLUG}.slideshow")

ROOT = Path(__file__).resolve().parent
SLIDE_DIR = ROOT / "slideshow"
ASSETS = Path(
    r"C:\Users\simot\.cursor\projects\c-Users-simot-Documents-Projects-fixminibeast\assets"
)

W, H = 1920, 1080


def fit_cover(src: Image.Image, tw: int, th: int) -> Image.Image:
    img = src.convert("RGB")
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def grade_photo(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Color(img).enhance(1.10)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    return ImageEnhance.Brightness(img).enhance(0.88)


def hybrid_bands(w: int, h: int) -> Image.Image:
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = overlay.load()
    top_h = int(h * 0.18)
    bot_h = int(h * 0.24)
    for y in range(h):
        if y < top_h:
            a = int(200 * (1.0 - (y / max(1, top_h - 1)) ** 1.6))
        elif y > h - bot_h:
            a = int(215 * (((y - (h - bot_h)) / max(1, bot_h - 1)) ** 0.75))
        else:
            a = 40
        if a <= 0:
            continue
        c = (*CARBON, a)
        for x in range(w):
            px[x, y] = c
    side = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(side)
    for i in range(60):
        a = int(70 * (1.0 - i / 59))
        sd.rectangle([i, 0, i, h], fill=(0, 0, 0, a))
        sd.rectangle([w - 1 - i, 0, w - 1 - i, h], fill=(0, 0, 0, a))
    return Image.alpha_composite(overlay, side).filter(ImageFilter.GaussianBlur(2))


def compose_hybrid(photo: Path) -> Image.Image:
    t0 = time.perf_counter()
    log.info("hybrid slide from %s", photo.name)
    bg = grade_photo(fit_cover(Image.open(photo), W, H)).convert("RGBA")
    bg = Image.alpha_composite(bg, hybrid_bands(W, H))

    word = render_wordmark(34)
    word.putalpha(word.split()[-1].point(lambda a: int(a * 0.76)))
    mark = render_race_number(68, HERO_ACCENT)
    mark.putalpha(mark.split()[-1].point(lambda a: int(a * 0.85)))
    tag = render_tagline(15, ICE_DIM, tracking=10)
    tag.putalpha(tag.split()[-1].point(lambda a: int(a * 0.57)))

    gap1, gap2 = 8, 6
    stack_w = max(word.width, mark.width, tag.width)
    stack_h = word.height + gap1 + mark.height + gap2 + tag.height
    brand = Image.new("RGBA", (stack_w, stack_h), (0, 0, 0, 0))
    y = 0
    for im, gap in ((word, gap1), (mark, gap2), (tag, 0)):
        brand.alpha_composite(im, ((stack_w - im.width) // 2, y))
        y += im.height + gap

    bx = (W - brand.width) // 2
    by = H - brand.height - 56
    hair = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(hair).line([(W // 2 - 50, by - 12), (W // 2 + 50, by - 12)], fill=(*ICE, 100), width=1)
    bg = Image.alpha_composite(bg, hair)
    shadow = Image.new("RGBA", brand.size, (0, 0, 0, 140))
    shadow.putalpha(brand.split()[-1])
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    bg.alpha_composite(shadow, (bx + 2, by + 3))
    bg.alpha_composite(brand, (bx, by))
    log.info("composed %s in %.0f ms", photo.name, (time.perf_counter() - t0) * 1000)
    return bg.convert("RGB")


def resolve_sources() -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []

    def pick(*candidates: Path) -> Path | None:
        return next((p for p in candidates if p.exists()), None)

    p = pick(ASSETS / "smarcato42_photo_center.png", ROOT / "smarcato42_photo_center.png")
    if p:
        pairs.append(("01_pit_hybrid", p))
    for idx, name in enumerate(("smarcato42_slide_a.png", "smarcato42_slide_b.png", "smarcato42_slide_c.png"), start=2):
        p = pick(ASSETS / name, ROOT / name)
        if p:
            pairs.append((f"{idx:02d}_{Path(name).stem}_hybrid", p))
    left = pick(ASSETS / "smarcato42_photo_left.png", ROOT / "smarcato42_photo_left.png")
    if left:
        pairs.append(("05_left_hybrid", left))
    right = pick(ASSETS / "smarcato42_photo_right.png", ROOT / "smarcato42_photo_right.png")
    if right:
        pairs.append(("06_right_hybrid", right))
    return pairs


def main() -> None:
    t0 = time.perf_counter()
    SLIDE_DIR.mkdir(parents=True, exist_ok=True)
    for old in list(SLIDE_DIR.glob("*.jpg")) + list(SLIDE_DIR.glob("*.png")):
        old.unlink()
    sources = resolve_sources()
    if not sources:
        raise FileNotFoundError("no photo sources for slideshow")
    for stem, path in sources:
        out = SLIDE_DIR / f"{stem}.jpg"
        compose_hybrid(path).save(out, "JPEG", quality=92, optimize=True)
        log.info("saved %s", out.name)
    log.info("slideshow ready in %.2fs | slides=%d", time.perf_counter() - t0, len(sources))


if __name__ == "__main__":
    main()
