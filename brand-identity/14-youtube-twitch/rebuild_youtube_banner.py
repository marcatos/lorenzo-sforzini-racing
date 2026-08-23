"""YouTube banner 2560x1440 with ALL branding inside the 1546x423 safe area."""

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
log = logging.getLogger("yt-banner")

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "brand-identity" / "14-youtube-twitch"
FONTS = ROOT / "fonts"
ASSETS = Path(
    r"C:\Users\simot\.cursor\projects\c-Users-simot-Documents-Projects-fixminibeast\assets"
)

W, H = 2560, 1440
SAFE_W, SAFE_H = 1546, 423
SAFE_X = (W - SAFE_W) // 2
SAFE_Y = (H - SAFE_H) // 2

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


def render_smarcato(size: int = 72, color=ICE, shear: float = 0.34) -> Image.Image:
    f = font("audiowide.ttf", size)
    text = "S.Marcato"
    tracking = max(1, size // 55)
    stroke = max(1, size // 60)
    ascent, descent = f.getmetrics()
    advances = [f.getlength(ch) for ch in text]
    tw = int(sum(advances) + tracking * (len(text) - 1)) + stroke * 2
    layer = Image.new("RGBA", (tw + 100, ascent + descent + 100), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    baseline = 50 + ascent
    x = 50.0
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


def tracked_racing(size: int = 28, color=ICE_DIM, tracking: int = 12) -> Image.Image:
    f = font("Candaral.ttf", size)
    text = "Racing"
    advances = [f.getlength(c) for c in text]
    ascent, descent = f.getmetrics()
    tw = int(sum(advances) + tracking * (len(text) - 1))
    layer = Image.new("RGBA", (tw + 40, ascent + descent + 40), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x = 20.0
    baseline = 20 + ascent
    for i, c in enumerate(text):
        ld.text((x, baseline), c, font=f, fill=(*color, 255), anchor="ls")
        x += advances[i] + tracking
    return layer.crop(layer.getbbox())


def load_bg(path: Path, tw: int, th: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    img = img.crop((left, top, left + tw, top + th))
    img = ImageEnhance.Brightness(img).enhance(0.40)
    img = ImageEnhance.Color(img).enhance(0.85)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    return img.convert("RGBA")


def main() -> None:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)

    # Clean photos WITHOUT burned-in logo
    photo_candidates = [
        ASSETS / "smarcato42_photo_center.png",
        ASSETS / "smarcato42_slide_a.png",
        ASSETS / "smarcato42_slide_c.png",
        ASSETS / "smarcato42_photo_left.png",
    ]
    photo = next((p for p in photo_candidates if p.exists()), None)
    if photo is None:
        raise FileNotFoundError("No clean racing photo found for banner background")
    log.info("background photo (no logo): %s", photo.name)

    bg = load_bg(photo, W, H)

    # Dim outside safe zone — keeps focus for mobile crop
    dim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dim)
    dd.rectangle([0, 0, SAFE_X - 1, H], fill=(0, 0, 0, 120))
    dd.rectangle([SAFE_X + SAFE_W, 0, W, H], fill=(0, 0, 0, 120))
    dd.rectangle([SAFE_X, 0, SAFE_X + SAFE_W, SAFE_Y - 1], fill=(0, 0, 0, 80))
    dd.rectangle([SAFE_X, SAFE_Y + SAFE_H, SAFE_X + SAFE_W, H], fill=(0, 0, 0, 100))
    bg = Image.alpha_composite(bg, dim)

    # Readable plate strictly inside safe area
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    inset = 36
    pd.rounded_rectangle(
        [
            SAFE_X + inset,
            SAFE_Y + inset,
            SAFE_X + SAFE_W - inset,
            SAFE_Y + SAFE_H - inset,
        ],
        radius=12,
        fill=(0, 0, 0, 165),
    )
    bg = Image.alpha_composite(bg, plate)

    # Compact lockup — must fit inside safe with margin
    word = render_smarcato(62, ICE)
    mark = extract_42(ROSSO)
    target_mark_h = 190
    ratio = target_mark_h / mark.height
    mark = mark.resize(
        (max(1, int(mark.width * ratio)), target_mark_h), Image.Resampling.LANCZOS
    )
    tag = tracked_racing(24, ICE_DIM, 10)

    gap = 26
    right_w = max(mark.width, tag.width)
    right_h = mark.height + 8 + tag.height
    block_w = word.width + gap + 3 + gap + right_w
    block_h = max(word.height, right_h)

    max_block_w = SAFE_W - 140
    max_block_h = SAFE_H - 100
    scale = min(1.0, max_block_w / block_w, max_block_h / block_h)
    if scale < 1.0:
        word = word.resize(
            (max(1, int(word.width * scale)), max(1, int(word.height * scale))),
            Image.Resampling.LANCZOS,
        )
        mark = mark.resize(
            (max(1, int(mark.width * scale)), max(1, int(mark.height * scale))),
            Image.Resampling.LANCZOS,
        )
        tag = tag.resize(
            (max(1, int(tag.width * scale)), max(1, int(tag.height * scale))),
            Image.Resampling.LANCZOS,
        )
        gap = max(14, int(gap * scale))
        right_w = max(mark.width, tag.width)
        right_h = mark.height + max(6, int(8 * scale)) + tag.height
        block_w = word.width + gap + 3 + gap + right_w
        block_h = max(word.height, right_h)

    block = Image.new("RGBA", (block_w + 4, block_h + 4), (0, 0, 0, 0))
    by = (block_h - word.height) // 2
    block.alpha_composite(word, (0, by))
    bd = ImageDraw.Draw(block)
    rx = word.width + gap
    bd.line([(rx, 2), (rx, block_h - 2)], fill=(*ROSSO, 245), width=3)
    rx2 = rx + gap
    ry = (block_h - right_h) // 2
    block.alpha_composite(mark, (rx2 + (right_w - mark.width) // 2, ry))
    block.alpha_composite(
        tag,
        (
            rx2 + (right_w - tag.width) // 2,
            ry + mark.height + max(6, int(8 * scale)),
        ),
    )

    cx = SAFE_X + SAFE_W // 2
    cy = SAFE_Y + SAFE_H // 2
    bx = cx - block.width // 2
    by = cy - block.height // 2

    assert bx >= SAFE_X + 20
    assert by >= SAFE_Y + 20
    assert bx + block.width <= SAFE_X + SAFE_W - 20
    assert by + block.height <= SAFE_Y + SAFE_H - 20
    log.info(
        "lockup %dx%d centered in safe area at (%d,%d)",
        block.width,
        block.height,
        bx,
        by,
    )

    # Soft glow under lockup (inside safe)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse(
        [bx - 40, by - 20, bx + block.width + 40, by + block.height + 20],
        fill=(225, 6, 0, 35),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    bg = Image.alpha_composite(bg, glow)
    bg.alpha_composite(block, (bx, by))

    # Corner ticks of safe area (decorative, still in margin)
    ticks = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(ticks)
    tick = 26
    for x0, y0, sx, sy in (
        (SAFE_X + 18, SAFE_Y + 18, 1, 1),
        (SAFE_X + SAFE_W - 18, SAFE_Y + 18, -1, 1),
        (SAFE_X + 18, SAFE_Y + SAFE_H - 18, 1, -1),
        (SAFE_X + SAFE_W - 18, SAFE_Y + SAFE_H - 18, -1, -1),
    ):
        td.line([(x0, y0), (x0 + sx * tick, y0)], fill=(*ROSSO, 140), width=2)
        td.line([(x0, y0), (x0, y0 + sy * tick)], fill=(*ROSSO, 140), width=2)
    bg = Image.alpha_composite(bg, ticks)

    final = bg.convert("RGB")
    out = OUT / "banner_youtube_2560x1440.png"
    final.save(out, "PNG", optimize=True)
    final.save(OUT / "banner_youtube_2560x1440.jpg", "JPEG", quality=92, optimize=True)

    # Device previews
    previews = OUT / "youtube_device_previews"
    previews.mkdir(exist_ok=True)
    crops = {
        "preview_tv_full.png": (0, 0, W, H),
        "preview_desktop.png": (SAFE_X - 200, SAFE_Y - 80, SAFE_W + 400, SAFE_H + 160),
        "preview_tablet.png": (SAFE_X - 80, SAFE_Y - 20, SAFE_W + 160, SAFE_H + 40),
        "preview_mobile_safe.png": (SAFE_X, SAFE_Y, SAFE_W, SAFE_H),
    }
    for name, (x, y, w, h) in crops.items():
        x = max(0, x)
        y = max(0, y)
        w = min(w, W - x)
        h = min(h, H - y)
        final.crop((x, y, x + w, y + h)).save(previews / name, "PNG", optimize=True)
        log.info("preview %s", name)

    # Guide
    guide = final.copy()
    gdi = ImageDraw.Draw(guide)
    gdi.rectangle(
        [SAFE_X, SAFE_Y, SAFE_X + SAFE_W - 1, SAFE_Y + SAFE_H - 1],
        outline=ROSSO,
        width=4,
    )
    fl = font("segoeui.ttf", 28)
    gdi.rectangle([SAFE_X, SAFE_Y - 42, SAFE_X + 640, SAFE_Y - 2], fill=(0, 0, 0))
    gdi.text(
        (SAFE_X + 12, SAFE_Y - 38),
        "SAFE AREA 1546x423 — visible on phone / tablet / desktop / TV",
        font=fl,
        fill=ROSSO,
    )
    guide.save(OUT / "banner_youtube_2560x1440_safearea_guide.png", "PNG", optimize=True)

    log.info("done in %.2fs | %s", time.perf_counter() - t0, out)


if __name__ == "__main__":
    main()
