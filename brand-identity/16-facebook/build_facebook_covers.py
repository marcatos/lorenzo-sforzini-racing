"""Facebook Page cover photos — layout dedicated to FB safe zones (not resized banners).

Specs (2026):
  Upload: 1640×624 (2×) + 851×315 JPG under 100 KB
  Safe zone: center ~640×312 @1× — keep brand here
  Avoid: bottom-left (profile pic ~168px), bottom-right (Page CTA)
"""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("facebook-cover")

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FONTS = ROOT / "fonts"
HORIZONTAL = ROOT / "brand-identity" / "02-horizontal"
ASSETS = Path(
    r"C:\Users\simot\.cursor\projects\c-Users-simot-Documents-Projects-fixminibeast\assets"
)
# 2× upload (displays ~820×312 desktop)
W, H = 1640, 624
W1, H1 = 820, 312

CARBON = (8, 8, 10)
ICE = (248, 248, 250)
ICE_DIM = (200, 200, 210)
ROSSO = (225, 6, 0)

# Safe zones @2× (derived from FB layout guides)
SAFE = (180, 0, W - 180, H)  # center band survives mobile side-crop
PROFILE_AVOID = (0, int(H * 0.42), int(W * 0.28), H)  # bottom-left avatar overlap
CTA_AVOID = (int(W * 0.72), int(H * 0.55), W, H)  # bottom-right Page CTA


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


def render_smarcato(size: int, color=ICE) -> Image.Image:
    f = font("audiowide.ttf", size)
    text = "S.Marcato"
    tracking = max(1, size // 55)
    stroke = max(1, size // 70)
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
    return italicize(layer.crop(layer.getbbox()), 0.34)


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
    out = [(0, 0, 0, 0) if pa < 8 else (r, g, b, pa) for _, _, _, pa in img.getdata()]
    img.putdata(out)
    return img


def extract_42(color=ROSSO) -> Image.Image:
    logo = punch_black(Image.open(ASSETS / "smarcato42_logo_clean.png"))
    crop = logo.crop((0, 350, logo.width, 690))
    bbox = crop.getbbox()
    if bbox:
        crop = crop.crop(bbox)
    return recolor(crop, color)


def tracked(text: str, size: int, color: tuple[int, int, int], tracking: int) -> Image.Image:
    f = font("Candaral.ttf", size)
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


def load_photo_bg(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGB")
    sw, sh = img.size
    scale = max(W / sw, H / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = min(max(0, (nw - W) // 2 + int(nw * 0.06)), nw - W)
    top = (nh - H) // 2
    img = img.crop((left, top, left + W, top + H))
    img = ImageEnhance.Brightness(img).enhance(0.34)
    img = ImageEnhance.Color(img).enhance(0.88)
    img = ImageEnhance.Contrast(img).enhance(1.12)
    return img.convert("RGBA")


def carbon_bg() -> Image.Image:
    bg = Image.new("RGBA", (W, H), (*CARBON, 255))
    noise = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(noise)
    for x in range(0, W, 4):
        a = 8 + (x % 7)
        nd.line([(x, 0), (x, H)], fill=(255, 255, 255, a))
    noise = noise.filter(ImageFilter.GaussianBlur(1))
    return Image.alpha_composite(bg, noise)


def add_race_stripe(canvas: Image.Image) -> Image.Image:
    bar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rectangle([0, 0, 10, H], fill=(*ROSSO, 255))
    return Image.alpha_composite(canvas, bar)


def horizontal_lockup(target_h: int, red_42: bool = True) -> Image.Image:
    """Wide row: S.Marcato | divider | 42+Racing — fits FB cover height."""
    name_h = int(target_h * 0.52)
    word = render_smarcato(name_h, ICE)
    mark = extract_42(ROSSO if red_42 else ICE)
    mark_h = int(target_h * 0.88)
    ratio = mark_h / mark.height
    mark = mark.resize(
        (max(1, int(mark.width * ratio)), mark_h), Image.Resampling.LANCZOS
    )
    tag = tracked("Racing", max(14, int(target_h * 0.14)), ICE_DIM, 10)

    mark_col_h = mark.height + 8 + tag.height
    mark_col = Image.new("RGBA", (max(mark.width, tag.width), mark_col_h), (0, 0, 0, 0))
    mark_col.alpha_composite(mark, ((mark_col.width - mark.width) // 2, 0))
    mark_col.alpha_composite(tag, ((mark_col.width - tag.width) // 2, mark.height + 8))

    gap = max(28, target_h // 6)
    div_w = 3
    total_w = word.width + gap + div_w + gap + mark_col.width
    total_h = max(word.height, mark_col_h)
    row = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))

    y_word = (total_h - word.height) // 2
    y_col = (total_h - mark_col_h) // 2
    x = 0
    row.alpha_composite(word, (x, y_word))
    x += word.width + gap
    ImageDraw.Draw(row).rectangle([x, y_col + 8, x + div_w, y_col + mark_col_h - 8], fill=(*ROSSO, 200))
    x += div_w + gap
    row.alpha_composite(mark_col, (x, y_col))
    return row


def recolor_horizontal_asset(red_42: bool = True) -> Image.Image:
    """Use pre-built horizontal transparent lockup; recolor 42 to racing red."""
    src = Image.open(HORIZONTAL / "horizontal_transparent.png").convert("RGBA")
    if not red_42:
        return src
    px = src.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if a < 20:
                continue
            # Right half ≈ 42 mark (white bold glyphs)
            if x > src.width * 0.42 and r > 200 and g > 200 and b > 200:
                px[x, y] = (*ROSSO, a)
    return src


def place_lockup(
    canvas: Image.Image, lockup: Image.Image, shift_x: int = 60
) -> tuple[Image.Image, int, int, int, int]:
    """Center in safe zone, nudge right to clear profile overlap."""
    sx0, sy0, sx1, sy1 = SAFE
    sw, sh = sx1 - sx0, sy1 - sy0
    scale = min(sw * 0.68 / lockup.width, sh * 0.72 / lockup.height, 1.0)
    if scale < 0.99:
        lockup = lockup.resize(
            (max(1, int(lockup.width * scale)), max(1, int(lockup.height * scale))),
            Image.Resampling.LANCZOS,
        )
    # Bias right so S.Marcato clears bottom-left profile photo overlap
    bx = sx0 + (sw - lockup.width) // 2 + 140
    by = sy0 + (sh - lockup.height) // 2 - int(H * 0.04)
    bx = min(max(sx0, bx), sx1 - lockup.width)
    by = min(max(sy0, by), sy1 - lockup.height)

    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pad = 16
    pd.rounded_rectangle(
        [bx - pad, by - pad, bx + lockup.width + pad, by + lockup.height + pad],
        radius=8,
        fill=(0, 0, 0, 120),
    )
    out = Image.alpha_composite(canvas, plate)
    out.alpha_composite(lockup, (bx, by))
    return out, bx, by, lockup.width, lockup.height


def save_jpeg_under_kb(img: Image.Image, path: Path, max_kb: int = 98) -> None:
    rgb = img.convert("RGB")
    for q in range(92, 70, -3):
        buf = io.BytesIO()
        rgb.save(buf, "JPEG", quality=q, optimize=True, subsampling=0)
        if buf.tell() / 1024 <= max_kb:
            path.write_bytes(buf.getvalue())
            log.info("jpg %s quality=%d size=%.0f KB", path.name, q, buf.tell() / 1024)
            return
    rgb.save(path, "JPEG", quality=70, optimize=True)
    log.info("jpg %s fallback quality=70 size=%.0f KB", path.name, path.stat().st_size / 1024)


def build_variant(name: str, bg: Image.Image, lockup: Image.Image, guide: bool) -> None:
    canvas = add_race_stripe(bg.copy())
    canvas, bx, by, lw, lh = place_lockup(canvas, lockup.copy())
    log.info("%s lockup at (%d,%d) size %dx%d", name, bx, by, lw, lh)

    rgb = canvas.convert("RGB")
    png = OUT / f"{name}_1640x624.png"
    rgb.save(png, "PNG", optimize=True)

    jpg = OUT / f"{name}_851x315.jpg"
    small = rgb.resize((W1, H1), Image.Resampling.LANCZOS)
    save_jpeg_under_kb(small, jpg)

    if guide:
        g = rgb.copy()
        gd = ImageDraw.Draw(g)
        gd.rectangle(list(SAFE), outline=(0, 220, 120), width=3)
        gd.rectangle(list(PROFILE_AVOID), outline=(225, 6, 0), width=2)
        gd.rectangle(list(CTA_AVOID), outline=(255, 180, 0), width=2)
        gd.rectangle([bx, by, bx + lw, by + lh], outline=(255, 255, 255), width=2)
        fl = font("segoeui.ttf", 22)
        gd.rectangle([12, 8, 780, 72], fill=(0, 0, 0))
        gd.text((16, 10), "GREEN=safe  RED=profile pic  ORANGE=Page CTA", font=fl, fill=ICE)
        g.save(OUT / f"{name}_layout_guide.png", "PNG", optimize=True)


def main() -> None:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)

    photo = next(
        (
            p
            for p in (
                ASSETS / "smarcato42_slide_c.png",
                ASSETS / "smarcato42_photo_center.png",
                ASSETS / "smarcato42_slide_a.png",
            )
            if p.exists()
        ),
        None,
    )
    if photo is None:
        raise FileNotFoundError("missing racing photo")

    lockup_h = int(H * 0.46)
    lockup_red = horizontal_lockup(lockup_h, red_42=True)
    lockup_mono = recolor_horizontal_asset(red_42=True)

    # Scale mono asset to similar height
    ms = lockup_h / lockup_mono.height
    lockup_mono = lockup_mono.resize(
        (max(1, int(lockup_mono.width * ms)), lockup_h), Image.Resampling.LANCZOS
    )

    log.info("building Facebook covers %dx%d", W, H)

    build_variant("cover_facebook_page_photo", load_photo_bg(photo), lockup_red, guide=True)
    build_variant("cover_facebook_page_carbon", carbon_bg(), lockup_red, guide=False)

    # Photo + existing horizontal lockup (cleaner typographic match)
    build_variant("cover_facebook_page_horizontal", load_photo_bg(photo), lockup_mono, guide=False)

    log.info("done in %.2fs → %s", time.perf_counter() - t0, OUT)


if __name__ == "__main__":
    main()
