"""Twitch profile banner 1200x480 — avatar-safe layout for all devices."""

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
log = logging.getLogger("twitch-banner")

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "brand-identity" / "14-youtube-twitch"
FONTS = ROOT / "fonts"
ASSETS = Path(
    r"C:\Users\simot\.cursor\projects\c-Users-simot-Documents-Projects-fixminibeast\assets"
)

# Official Twitch profile banner
W, H = 1200, 480

# Profile picture sits bottom-left and covers part of the banner.
# Keep critical branding OUT of this zone.
AVATAR_ZONE = (0, H - 200, 220, H)  # x0,y0,x1,y1 approximate overlap

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


def render_smarcato(size: int = 52, color=ICE, shear: float = 0.34) -> Image.Image:
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


def tracked_racing(size: int = 22, color=ICE_DIM, tracking: int = 10) -> Image.Image:
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


def load_bg(path: Path, tw: int, th: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - tw) // 2, (nh - th) // 2
    img = img.crop((left, top, left + tw, top + th))
    img = ImageEnhance.Brightness(img).enhance(0.38)
    img = ImageEnhance.Color(img).enhance(0.9)
    img = ImageEnhance.Contrast(img).enhance(1.08)
    return img.convert("RGBA")


def main() -> None:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)

    photo_candidates = [
        ASSETS / "smarcato42_slide_c.png",
        ASSETS / "smarcato42_slide_a.png",
        ASSETS / "smarcato42_photo_center.png",
        ASSETS / "smarcato42_photo_right.png",
    ]
    photo = next((p for p in photo_candidates if p.exists()), None)
    if photo is None:
        raise FileNotFoundError("No clean racing photo for Twitch banner")
    log.info("bg=%s", photo.name)

    bg = load_bg(photo, W, H)

    # Left-to-right gradient: darker on left (avatar zone) so profile pic pops,
    # keep atmosphere on right.
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grad)
    for x in range(W):
        # stronger dark on left third
        t = x / (W - 1)
        a = int(150 * (1 - min(1.0, t * 1.6)) ** 1.2)
        gd.line([(x, 0), (x, H)], fill=(0, 0, 0, a))
    # bottom band darkening
    for y in range(H - 120, H):
        a = int(90 * ((y - (H - 120)) / 120))
        gd.line([(0, y), (W, y)], fill=(0, 0, 0, a))
    bg = Image.alpha_composite(bg, grad)

    # Red accent bar on left edge (Twitch brand energy, thin)
    bar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rectangle([0, 0, 6, H], fill=(*ROSSO, 255))
    bg = Image.alpha_composite(bg, bar)

    # Content safe rect: avoid avatar overlap + margins
    # Usable content area roughly x=240..1160, y=40..400
    content_x0, content_y0 = 260, 48
    content_x1, content_y1 = W - 40, H - 56
    content_w = content_x1 - content_x0
    content_h = content_y1 - content_y0

    # Readable plate in content zone (not over avatar)
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rounded_rectangle(
        [content_x0 - 16, content_y0 - 8, content_x1, content_y1 + 8],
        radius=10,
        fill=(0, 0, 0, 145),
    )
    bg = Image.alpha_composite(bg, plate)

    # Lockup: horizontal S.Marcato | 42 / Racing — sized for 1200x480
    word = render_smarcato(48, ICE)
    mark = extract_42(ROSSO)
    target_mark_h = 150
    ratio = target_mark_h / mark.height
    mark = mark.resize(
        (max(1, int(mark.width * ratio)), target_mark_h), Image.Resampling.LANCZOS
    )
    tag = tracked_racing(20, ICE_DIM, 9)

    gap = 22
    right_w = max(mark.width, tag.width)
    right_h = mark.height + 6 + tag.height
    block_w = word.width + gap + 3 + gap + right_w
    block_h = max(word.height, right_h)

    max_w = content_w - 24
    max_h = content_h - 16
    scale = min(1.0, max_w / block_w, max_h / block_h)
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
        gap = max(12, int(gap * scale))
        right_w = max(mark.width, tag.width)
        right_h = mark.height + max(4, int(6 * scale)) + tag.height
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
        (rx2 + (right_w - tag.width) // 2, ry + mark.height + max(4, int(6 * scale))),
    )

    # Place lockup in center of CONTENT zone (shifted right of avatar)
    cx = content_x0 + content_w // 2
    cy = content_y0 + content_h // 2
    bx = cx - block.width // 2
    by = cy - block.height // 2
    # clamp inside content
    bx = max(content_x0, min(bx, content_x1 - block.width))
    by = max(content_y0, min(by, content_y1 - block.height))

    log.info(
        "lockup %dx%d at (%d,%d) | content zone %d..%d x %d..%d | avatar-safe left=%d",
        block.width,
        block.height,
        bx,
        by,
        content_x0,
        content_x1,
        content_y0,
        content_y1,
        AVATAR_ZONE[2],
    )

    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse(
        [bx - 30, by - 16, bx + block.width + 30, by + block.height + 16],
        fill=(225, 6, 0, 40),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(22))
    bg = Image.alpha_composite(bg, glow)
    bg.alpha_composite(block, (bx, by))

    final = bg.convert("RGB")

    # Main deliverable
    out_png = OUT / "banner_twitch_1200x480.png"
    out_jpg = OUT / "banner_twitch_1200x480.jpg"
    final.save(out_png, "PNG", optimize=True)
    final.save(out_jpg, "JPEG", quality=93, optimize=True)

    # Guide showing avatar zone + content zone
    guide = final.copy()
    g = ImageDraw.Draw(guide)
    g.rectangle(AVATAR_ZONE, outline=(225, 6, 0), width=3)
    g.rectangle(
        [content_x0, content_y0, content_x1, content_y1],
        outline=(0, 200, 120),
        width=2,
    )
    fl = font("segoeui.ttf", 18)
    g.rectangle([8, 8, 420, 54], fill=(0, 0, 0))
    g.text((14, 12), "RED = avatar overlap zone (keep clear)", font=fl, fill=ROSSO)
    g.text((14, 32), "GREEN = content safe zone", font=fl, fill=(0, 200, 120))
    guide.save(OUT / "banner_twitch_1200x480_layout_guide.png", "PNG", optimize=True)

    # Mock: avatar circle on banner (how it looks on Twitch)
    mock = final.copy().convert("RGBA")
    avatar_path = OUT / "profile_twitch_800.png"
    if avatar_path.exists():
        av = Image.open(avatar_path).convert("RGBA").resize((140, 140), Image.Resampling.LANCZOS)
        mask = Image.new("L", (140, 140), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, 139, 139], fill=255)
        av.putalpha(mask)
        # Twitch places avatar near bottom-left of banner
        mock.alpha_composite(av, (36, H - 140 - 28))
        # white ring
        ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ring).ellipse(
            [34, H - 140 - 30, 34 + 144, H - 140 - 30 + 144],
            outline=(255, 255, 255, 220),
            width=3,
        )
        mock = Image.alpha_composite(mock, ring)
    mock.convert("RGB").save(OUT / "banner_twitch_1200x480_with_avatar_mock.png", "PNG", optimize=True)

    log.info(
        "done in %.2fs | %s (%.0f KB) | %s (%.0f KB)",
        time.perf_counter() - t0,
        out_png.name,
        out_png.stat().st_size / 1024,
        out_jpg.name,
        out_jpg.stat().st_size / 1024,
    )


if __name__ == "__main__":
    main()
