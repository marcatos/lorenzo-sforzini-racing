"""Twitch / Restream Video Player Banner (offline screen inside the player).

This is NOT a profile banner and NOT a channel-header lateral layout.
It fills the 16:9 player when the channel is offline — full hero composition.
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
log = logging.getLogger("twitch-player-banner")

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "brand-identity" / "14-youtube-twitch"
FONTS = ROOT / "fonts"
ASSETS = Path(
    r"C:\Users\simot\.cursor\projects\c-Users-simot-Documents-Projects-fixminibeast\assets"
)
WORKSPACE_ASSETS = Path(r"C:\Users\simot\Documents\Projects\fixminibeast\assets")

W, H = 1920, 1080
ICE = (248, 248, 250)
ICE_DIM = (190, 190, 200)
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
    out = [
        (0, 0, 0, 0) if r < thr and g < thr and b < thr else (r, g, b, a)
        for r, g, b, a in img.getdata()
    ]
    img.putdata(out)
    return img


def recolor(img: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
    img = img.convert("RGBA")
    r, g, b = rgb
    out = [(0, 0, 0, 0) if pa < 8 else (r, g, b, pa) for pr, pg, pb, pa in img.getdata()]
    img.putdata(out)
    return img


def extract_42(color=ROSSO) -> Image.Image:
    logo = punch_black(Image.open(ASSETS / "smarcato42_logo_clean.png"))
    crop = logo.crop((0, 350, logo.width, 690))
    bbox = crop.getbbox()
    if bbox:
        crop = crop.crop(bbox)
    return recolor(crop, color)


def tracked_text(
    text: str, size: int, color: tuple[int, int, int], tracking: int, font_name: str = "Candaral.ttf"
) -> Image.Image:
    f = font(font_name, size)
    advances = [f.getlength(c) for c in text]
    ascent, descent = f.getmetrics()
    tw = int(sum(advances) + tracking * max(0, len(text) - 1))
    layer = Image.new("RGBA", (tw + 40, ascent + descent + 40), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x = 20.0
    baseline = 20 + ascent
    for i, c in enumerate(text):
        ld.text((x, baseline), c, font=f, fill=(*color, 255), anchor="ls")
        x += advances[i] + tracking
    return layer.crop(layer.getbbox())


def make_monogram(size: int = 96) -> Image.Image:
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


def load_bg(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    sw, sh = img.size
    scale = max(W / sw, H / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - W) // 2, (nh - H) // 2
    # Bias crop slightly right — car/pit detail in hero zone
    left = min(max(0, left + int(nw * 0.04)), nw - W)
    img = img.crop((left, top, left + W, top + H))
    img = ImageEnhance.Brightness(img).enhance(0.32)
    img = ImageEnhance.Color(img).enhance(0.85)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    return img.convert("RGBA")


def stack_centered(*layers: Image.Image, gaps: list[int] | None = None) -> Image.Image:
    gaps = gaps or [12] * (len(layers) - 1)
    w = max(im.width for im in layers)
    h = sum(im.height for im in layers) + sum(gaps)
    block = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i, im in enumerate(layers):
        block.alpha_composite(im, ((w - im.width) // 2, y))
        y += im.height + (gaps[i] if i < len(gaps) else 0)
    return block


def build() -> Path:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    WORKSPACE_ASSETS.mkdir(parents=True, exist_ok=True)

    photo = next(
        (
            p
            for p in (
                ASSETS / "smarcato42_slide_c.png",
                ASSETS / "smarcato42_photo_right.png",
                ASSETS / "smarcato42_slide_a.png",
            )
            if p.exists()
        ),
        None,
    )
    if photo is None:
        raise FileNotFoundError("missing racing photo for video player banner")

    log.info("start video player banner 1920x1080 from %s", photo.name)
    bg = load_bg(photo)

    # Cinematic center plate — this asset IS the player contents
    veil = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    # Soft vignette rings
    for i, a in enumerate((110, 70, 40)):
        inset = 40 + i * 90
        vd.rounded_rectangle(
            [inset, inset, W - inset, H - inset],
            radius=28,
            fill=(0, 0, 0, a),
        )
    # Stronger mid band behind lockup
    vd.rounded_rectangle([360, 220, W - 360, H - 220], radius=20, fill=(0, 0, 0, 140))
    bg = Image.alpha_composite(bg, veil)

    # Red edge + thin top accent (race-stripe language)
    accent = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ad = ImageDraw.Draw(accent)
    ad.rectangle([0, 0, 8, H], fill=(*ROSSO, 255))
    ad.rectangle([0, 0, W, 4], fill=(*ROSSO, 220))
    ad.rectangle([0, H - 4, W, H], fill=(*ROSSO, 180))
    bg = Image.alpha_composite(bg, accent)

    # Hero lockup — designed as offline end-card, not side rails
    status = tracked_text("OFFLINE", 34, ROSSO, tracking=18, font_name="segoeuib.ttf")
    word = render_smarcato(72, ICE)
    mark = extract_42(ROSSO)
    mark_h = 320
    ratio = mark_h / mark.height
    mark = mark.resize(
        (max(1, int(mark.width * ratio)), mark_h), Image.Resampling.LANCZOS
    )
    tag = tracked_text("Racing", 28, ICE_DIM, tracking=14)
    sub = tracked_text("PROSSIMA SESSIONE", 22, ICE_DIM, tracking=10, font_name="segoeui.ttf")

    brand = stack_centered(status, word, mark, tag, sub, gaps=[22, 14, 10, 28])

    # Soft rosso glow behind 42 stack
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bx = (W - brand.width) // 2
    by = (H - brand.height) // 2 - 10
    ImageDraw.Draw(glow).ellipse(
        [bx - 40, by + 40, bx + brand.width + 40, by + brand.height - 20],
        fill=(225, 6, 0, 55),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(36))
    bg = Image.alpha_composite(bg, glow)
    bg.alpha_composite(brand, (bx, by))
    log.info("hero lockup at (%d,%d) size %dx%d", bx, by, brand.width, brand.height)

    # Corner monogram — secondary mark, doesn't compete with hero
    mono = make_monogram(70)
    mx, my = 36, H - mono.height - 36
    mplate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(mplate).rounded_rectangle(
        [mx - 12, my - 12, mx + mono.width + 12, my + mono.height + 12],
        radius=8,
        fill=(0, 0, 0, 150),
    )
    bg = Image.alpha_composite(bg, mplate)
    bg.alpha_composite(mono, (mx, my))

    final = bg.convert("RGB")
    name = "banner_twitch_video_player_1920x1080.png"
    png = OUT / name
    jpg = png.with_suffix(".jpg")
    final.save(png, "PNG", optimize=True)
    final.save(jpg, "JPEG", quality=93, optimize=True)

    # Workspace copy for quick preview / upload
    ws = WORKSPACE_ASSETS / name
    final.save(ws, "PNG", optimize=True)

    elapsed = (time.perf_counter() - t0) * 1000
    log.info(
        "saved %s (%.0f KB) + jpg + workspace copy in %.0f ms",
        png.name,
        png.stat().st_size / 1024,
        elapsed,
    )
    log.info("path: %s", png)
    return png


if __name__ == "__main__":
    build()
