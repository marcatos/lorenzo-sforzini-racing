"""Twitch banners with LATERAL branding — center kept clear for offline UI overlays."""

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
log = logging.getLogger("twitch-lateral")

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "brand-identity" / "14-youtube-twitch"
FONTS = ROOT / "fonts"
ASSETS = Path(
    r"C:\Users\simot\.cursor\projects\c-Users-simot-Documents-Projects-fixminibeast\assets"
)

CARBON = (8, 8, 10)
ICE = (248, 248, 250)
ICE_DIM = (210, 210, 218)
ROSSO = (225, 6, 0)


def font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in (FONTS / name, Path(r"C:\Windows\Fonts") / name):
        try:
            return ImageFont.truetype(str(p), size)
        except OSError:
            continue
    return ImageFont.load_default()


def italicize(rgba: Image.Image, shear: float = 0.32) -> Image.Image:
    w, h = rgba.size
    pad = int(abs(shear) * h) + 8
    c = Image.new("RGBA", (w + pad * 2, h + 8), (0, 0, 0, 0))
    c.paste(rgba, (pad, 4))
    cw, ch = c.size
    return c.transform(
        (cw + int(abs(shear) * ch), ch),
        Image.Transform.AFFINE,
        (1, shear, -shear * ch if shear > 0 else 0, 0, 1, 0),
        resample=Image.Resampling.BICUBIC,
    )


def render_smarcato(size: int, color=ICE, shear: float = 0.34) -> Image.Image:
    f = font("audiowide.ttf", size)
    text = "S.Marcato"
    tracking = max(1, size // 55)
    stroke = max(1, size // 60)
    ascent, descent = f.getmetrics()
    advances = [f.getlength(ch) for ch in text]
    tw = int(sum(advances) + tracking * (len(text) - 1)) + stroke * 2
    layer = Image.new("RGBA", (tw + 80, ascent + descent + 80), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    baseline = 40 + ascent
    x = 40.0
    for i, ch in enumerate(text):
        ld.text(
            (x, baseline),
            ch,
            font=f,
            fill=(*color, 255),
            stroke_width=stroke,
            stroke_fill=(*color, 255),
            anchor="ls",
        )
        x += advances[i] + (tracking if i < len(text) - 1 else 0)
    return italicize(layer.crop(layer.getbbox()), shear)


def punch_black(img: Image.Image, thr: int = 35) -> Image.Image:
    img = img.convert("RGBA")
    out = []
    for r, g, b, a in img.getdata():
        out.append((0, 0, 0, 0) if r < thr and g < thr and b < thr else (r, g, b, a))
    img.putdata(out)
    return img


def recolor(img: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
    img = img.convert("RGBA")
    r, g, b = rgb
    out = []
    for pr, pg, pb, pa in img.getdata():
        out.append((0, 0, 0, 0) if pa < 8 else (r, g, b, pa))
    img.putdata(out)
    return img


def extract_42(color=ROSSO) -> Image.Image:
    logo = punch_black(Image.open(ASSETS / "smarcato42_logo_clean.png"))
    crop = logo.crop((0, 350, logo.width, 690))
    bbox = crop.getbbox()
    if bbox:
        crop = crop.crop(bbox)
    return recolor(crop, color)


def tracked_racing(size: int, color=ICE_DIM, tracking: int = 10) -> Image.Image:
    f = font("Candaral.ttf", size)
    text = "Racing"
    advances = [f.getlength(c) for c in text]
    ascent, descent = f.getmetrics()
    tw = int(sum(advances) + tracking * (len(text) - 1))
    layer = Image.new("RGBA", (tw + 30, ascent + descent + 30), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x = 15.0
    baseline = 15 + ascent
    for i, c in enumerate(text):
        ld.text((x, baseline), c, font=f, fill=(*color, 255), anchor="ls")
        x += advances[i] + tracking
    return layer.crop(layer.getbbox())


def make_monogram(size: int = 120) -> Image.Image:
    f = font("audiowide.ttf", size)
    layer = Image.new("RGBA", (size * 3, size * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text((size // 2, size // 3), "S", font=f, fill=(*ICE, 255), anchor="mm")
    f2 = font("audiowide.ttf", int(size * 0.92))
    ld.text((size // 2 + size // 8, size), "M", font=f2, fill=(*ICE, 255), anchor="mm")
    f3 = font("audiowide.ttf", int(size * 0.26))
    ld.text(
        (size // 2 + size // 2, int(size * 1.38)),
        "42",
        font=f3,
        fill=(*ROSSO, 255),
        anchor="mm",
    )
    return italicize(layer.crop(layer.getbbox()), 0.28)


def load_bg(path: Path, tw: int, th: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    img = img.crop((left, top, left + tw, top + th))
    img = ImageEnhance.Brightness(img).enhance(0.36)
    img = ImageEnhance.Color(img).enhance(0.9)
    img = ImageEnhance.Contrast(img).enhance(1.1)
    return img.convert("RGBA")


def stack_brand(word: Image.Image, mark: Image.Image, tag: Image.Image, gap: int = 10) -> Image.Image:
    """Vertical stack for side panels: name / 42 / Racing."""
    w = max(word.width, mark.width, tag.width)
    h = word.height + gap + mark.height + max(6, gap // 2) + tag.height
    block = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    block.alpha_composite(word, ((w - word.width) // 2, y))
    y += word.height + gap
    block.alpha_composite(mark, ((w - mark.width) // 2, y))
    y += mark.height + max(6, gap // 2)
    block.alpha_composite(tag, ((w - tag.width) // 2, y))
    return block


def build_banner(tw: int, th: int, name: str, offline_layout: bool) -> None:
    """
    offline_layout=True  → wide channel/offline view: brand on FAR RIGHT (+ small left), center empty
    offline_layout=False → profile 1200x480: brand on RIGHT content rail, left clear for avatar
    """
    photo = next(
        (
            p
            for p in (
                ASSETS / "smarcato42_slide_c.png",
                ASSETS / "smarcato42_slide_a.png",
                ASSETS / "smarcato42_photo_right.png",
                ASSETS / "smarcato42_photo_center.png",
            )
            if p.exists()
        ),
        None,
    )
    if photo is None:
        raise FileNotFoundError("missing racing photo")

    bg = load_bg(photo, tw, th)

    # Center UI occlusion zone — keep visually quieter
    if offline_layout:
        # Offline panels + player cover ~center-left through most of the right half.
        # Safe brand strip is only the far-right ~14–16%.
        ui_x0 = int(tw * 0.14)
        ui_x1 = int(tw * 0.84)
        dim = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dim)
        dd.rectangle([ui_x0, int(th * 0.10), ui_x1, int(th * 0.94)], fill=(0, 0, 0, 100))
        bg = Image.alpha_composite(bg, dim)
        left_rail = (int(tw * 0.012), int(th * 0.22), int(tw * 0.12), int(th * 0.78))
        right_rail = (int(tw * 0.845), int(th * 0.16), int(tw * 0.988), int(th * 0.84))
    else:
        # Profile banner: avatar bottom-left; put brand on right third
        dim = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        dd = ImageDraw.Draw(dim)
        for x in range(tw):
            t = x / (tw - 1)
            # darken left/center slightly; keep right for brand
            a = int(110 * (1 - max(0, (t - 0.45) / 0.55)) ** 1.1) if t < 0.72 else 20
            dd.line([(x, 0), (x, th)], fill=(0, 0, 0, max(0, min(160, a))))
        bg = Image.alpha_composite(bg, dim)
        left_rail = (16, 40, 180, th - 160)  # small monogram only (above avatar)
        right_rail = (int(tw * 0.68), 48, tw - 24, th - 48)

    # Red edge accent
    bar = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rectangle([0, 0, max(5, tw // 200), th], fill=(*ROSSO, 255))
    bg = Image.alpha_composite(bg, bar)

    # --- RIGHT brand (primary visible zone on Twitch offline) ---
    rx0, ry0, rx1, ry1 = right_rail
    rw, rh = rx1 - rx0, ry1 - ry0

    # Compact lockup: stays inside the thin far-right strip beside the player.
    gap = max(6, th // 64)
    if offline_layout:
        word = render_smarcato(max(28, min(40, rw // 7)), ICE)
        tag = tracked_racing(max(13, th // 42), ICE_DIM, 7)
        if word.width > rw - 6:
            s = (rw - 6) / word.width
            word = word.resize(
                (max(1, int(word.width * s)), max(1, int(word.height * s))),
                Image.Resampling.LANCZOS,
            )
        if tag.width > rw - 6:
            s = (rw - 6) / tag.width
            tag = tag.resize(
                (max(1, int(tag.width * s)), max(1, int(tag.height * s))),
                Image.Resampling.LANCZOS,
            )
        mark = extract_42(ROSSO)
        # Cap 42 so stack uses ~70% of rail height (was filling almost all of it)
        mark_h = min(
            int(rh * 0.48),
            max(64, rh - word.height - tag.height - gap * 2 - 16),
        )
        ratio = min(mark_h / mark.height, (rw - 10) / mark.width)
        mark = mark.resize(
            (max(1, int(mark.width * ratio)), max(1, int(mark.height * ratio))),
            Image.Resampling.LANCZOS,
        )
    else:
        word = render_smarcato(max(30, th // 15), ICE)
        mark = extract_42(ROSSO)
        tag = tracked_racing(max(14, th // 34), ICE_DIM, 7)
        mark_h = min(int(rh * 0.42), int(th * 0.32))
        ratio = min(mark_h / mark.height, (rw - 10) / mark.width)
        mark = mark.resize(
            (max(1, int(mark.width * ratio)), max(1, int(mark.height * ratio))),
            Image.Resampling.LANCZOS,
        )

    brand = stack_brand(word, mark, tag, gap=gap)

    # Fit brand into right rail, then leave a little air
    scale = min(rw / brand.width, rh / brand.height, 1.0) * (0.88 if offline_layout else 0.92)
    if scale < 0.99:
        brand = brand.resize(
            (max(1, int(brand.width * scale)), max(1, int(brand.height * scale))),
            Image.Resampling.LANCZOS,
        )

    # Plate behind right brand — hug the RIGHT edge (not centered in rail)
    plate = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pad = 12
    bx = rx1 - brand.width - 6
    by = ry0 + (rh - brand.height) // 2
    pd.rounded_rectangle(
        [bx - pad, by - pad, bx + brand.width + pad, by + brand.height + pad],
        radius=10,
        fill=(0, 0, 0, 160),
    )
    bg = Image.alpha_composite(bg, plate)

    glow = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        [bx - 20, by - 10, bx + brand.width + 20, by + brand.height + 10],
        fill=(225, 6, 0, 45),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    bg = Image.alpha_composite(bg, glow)
    bg.alpha_composite(brand, (bx, by))
    log.info("%s right brand at (%d,%d) size %dx%d", name, bx, by, brand.width, brand.height)

    # --- LEFT small monogram (secondary, stays in thin visible strip) ---
    lx0, ly0, lx1, ly1 = left_rail
    lw, lh = lx1 - lx0, ly1 - ly0
    mono = make_monogram(max(70, th // 6))
    mscale = min((lw - 12) / mono.width, (lh - 12) / mono.height, 1.0)
    mono = mono.resize(
        (max(1, int(mono.width * mscale)), max(1, int(mono.height * mscale))),
        Image.Resampling.LANCZOS,
    )
    mx = lx0 + (lw - mono.width) // 2
    my = ly0 + (lh - mono.height) // 2
    # For profile banner, keep mono higher so avatar doesn't cover it
    if not offline_layout:
        my = min(my, th - 200 - mono.height)

    lplate = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ImageDraw.Draw(lplate).rounded_rectangle(
        [mx - 10, my - 10, mx + mono.width + 10, my + mono.height + 10],
        radius=8,
        fill=(0, 0, 0, 140),
    )
    bg = Image.alpha_composite(bg, lplate)
    bg.alpha_composite(mono, (mx, my))
    log.info("%s left monogram at (%d,%d)", name, mx, my)

    final = bg.convert("RGB")
    png = OUT / name
    final.save(png, "PNG", optimize=True)
    final.save(png.with_suffix(".jpg"), "JPEG", quality=93, optimize=True)

    # Layout guide
    guide = final.copy()
    g = ImageDraw.Draw(guide)
    g.rectangle([rx0, ry0, rx1, ry1], outline=(0, 220, 120), width=3)
    g.rectangle([lx0, ly0, lx1, ly1], outline=(0, 180, 255), width=2)
    if offline_layout:
        g.rectangle(
            [int(tw * 0.14), int(th * 0.10), int(tw * 0.84), int(th * 0.94)],
            outline=(225, 6, 0),
            width=3,
        )
        fl = font("segoeui.ttf", 22)
        g.rectangle([12, 12, 620, 78], fill=(0, 0, 0))
        g.text((18, 16), "RED = Twitch offline UI (keep empty)", font=fl, fill=ROSSO)
        g.text((18, 42), "GREEN = primary brand (RIGHT)  |  BLUE = mono LEFT", font=fl, fill=ICE)
    else:
        g.rectangle([0, th - 180, 210, th], outline=(225, 6, 0), width=3)
        fl = font("segoeui.ttf", 18)
        g.rectangle([8, 8, 520, 54], fill=(0, 0, 0))
        g.text((12, 12), "RED = avatar zone", font=fl, fill=ROSSO)
        g.text((12, 32), "GREEN = brand RIGHT (visible)", font=fl, fill=(0, 220, 120))

    guide_name = name.replace(".png", "_layout_guide.png")
    guide.save(OUT / guide_name, "PNG", optimize=True)
    log.info("saved %s (%.0f KB)", png.name, png.stat().st_size / 1024)


def main() -> None:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)

    # Profile banner (channel header)
    build_banner(1200, 480, "banner_twitch_1200x480.png", offline_layout=False)

    # Offline / channel page background (what you're seeing under the boxes)
    build_banner(1920, 1080, "banner_twitch_offline_1920x1080.png", offline_layout=True)

    # Also a wider 1920x480 strip variant for some layouts
    build_banner(1920, 480, "banner_twitch_1920x480.png", offline_layout=True)

    log.info("done in %.2fs → %s", time.perf_counter() - t0, OUT)


if __name__ == "__main__":
    main()
