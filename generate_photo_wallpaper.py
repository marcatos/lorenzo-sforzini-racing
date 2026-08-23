"""Composite photo GT panels + elegant mixed-case S.Marcato 42 wordmark."""

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
log = logging.getLogger("smarcato42")

PANEL_W, PANEL_H = 2560, 1440
WIDTH, HEIGHT = PANEL_W * 3, PANEL_H

ASSETS = Path(r"C:\Users\simot\.cursor\projects\c-Users-simot-Documents-Projects-fixminibeast\assets")
OUT_DIR = Path(__file__).resolve().parent
OUT = OUT_DIR / "smarcato42_racing_span_7680x1440.png"
WIN_FONTS = Path(r"C:\Windows\Fonts")

ICE = (248, 248, 250)
ICE_DIM = (200, 200, 208)
SHADOW = (0, 0, 0, 175)


def truetype(names: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in names:
        path = Path(name)
        if not path.is_file():
            path = WIN_FONTS / name
        try:
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    return ImageFont.load_default()


def fit_cover(src: Image.Image, tw: int, th: int) -> Image.Image:
    img = src.convert("RGB")
    sw, sh = img.size
    scale = max(tw / sw, th / sh)
    nw, nh = int(sw * scale), int(sh * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    return img.crop((left, top, left + tw, top + th))


def soften_grade(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Color(img).enhance(1.12)
    img = ImageEnhance.Contrast(img).enhance(1.05)
    img = ImageEnhance.Brightness(img).enhance(0.98)
    return img


def measure_tracked(text: str, font: ImageFont.ImageFont, tracking: float) -> tuple[int, int]:
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    total_w = 0
    max_h = 0
    for i, ch in enumerate(text):
        bbox = probe.textbbox((0, 0), ch, font=font)
        cw = bbox[2] - bbox[0]
        ch_h = bbox[3] - bbox[1]
        total_w += cw
        if i < len(text) - 1:
            total_w += int(tracking)
        max_h = max(max_h, ch_h)
    return total_w, max_h


def draw_tracked_text(
    base: Image.Image,
    text: str,
    center: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    tracking: float = 0,
    shadow_blur: int = 12,
) -> tuple[int, int, int, int]:
    """Draw centered text with letter-spacing on a shared baseline + soft shadow."""
    advances = [font.getlength(ch) for ch in text]
    ascent, descent = font.getmetrics()
    tw = int(sum(advances) + tracking * max(0, len(text) - 1))
    th = ascent + descent
    x0 = center[0] - tw // 2
    baseline = center[1] - th // 2 + ascent

    shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)

    x = float(x0)
    for i, ch in enumerate(text):
        sd.text((x + 2, baseline + 4), ch, font=font, fill=SHADOW, anchor="ls")
        od.text((x, baseline), ch, font=font, fill=(*fill, 255), anchor="ls")
        x += advances[i] + (tracking if i < len(text) - 1 else 0)

    shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
    base.alpha_composite(shadow)
    base.alpha_composite(overlay)
    return (x0, baseline - ascent, x0 + tw, baseline + descent)


def italicize(rgba: Image.Image, shear: float = 0.22) -> Image.Image:
    """Shear text layer for a subtle racing italic."""
    w, h = rgba.size
    # pad so shear doesn't clip
    pad = int(abs(shear) * h) + 8
    canvas = Image.new("RGBA", (w + pad * 2, h + 8), (0, 0, 0, 0))
    canvas.paste(rgba, (pad, 4))
    cw, ch = canvas.size
    # x' = x + shear * (h - y)
    return canvas.transform(
        (cw + int(abs(shear) * ch), ch),
        Image.Transform.AFFINE,
        (1, shear, -shear * ch if shear > 0 else 0, 0, 1, 0),
        resample=Image.Resampling.BICUBIC,
    )


def punch_black(logo: Image.Image, threshold: int = 35) -> Image.Image:
    logo = logo.convert("RGBA")
    pixels = list(logo.getdata())
    cleaned = []
    for r, g, b, a in pixels:
        if r < threshold and g < threshold and b < threshold:
            cleaned.append((0, 0, 0, 0))
        else:
            cleaned.append((r, g, b, a))
    logo.putdata(cleaned)
    return logo


def extract_42_racing(logo_path: Path) -> Image.Image:
    """Keep previous AI 42 + Racing; drop the old name block."""
    logo = punch_black(Image.open(logo_path))
    # Known bands on 1024 logo: name ~258-330, 42+Racing ~350-760
    crop = logo.crop((0, 340, logo.width, 780))
    # trim transparent margins
    bbox = crop.getbbox()
    if bbox:
        crop = crop.crop(bbox)
    return crop


def paste_with_shadow(base: Image.Image, layer: Image.Image, xy: tuple[int, int]) -> tuple[int, int, int, int]:
    x, y = xy
    alpha = layer.split()[-1]
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 160))
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    base.alpha_composite(shadow, (x + 3, y + 8))
    base.alpha_composite(layer, (x, y))
    return (x, y, x + layer.width, y + layer.height)


def draw_hairline(base: Image.Image, y: int, cx: int, half: int) -> None:
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.line([(cx - half, y), (cx + half, y)], fill=(0, 0, 0, 130), width=5)
    glow = glow.filter(ImageFilter.GaussianBlur(3))
    line = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(line)
    ld.line([(cx - half, y), (cx + half, y)], fill=(*ICE, 180), width=1)
    base.alpha_composite(glow)
    base.alpha_composite(line)


def draw_wordmark(base: Image.Image, cx: int, cy: int) -> None:
    """Bold squared-rounded italic speed wordmark + previous 42/Racing."""
    font_dir = OUT_DIR / "fonts"
    f_name = truetype(
        [
            str(font_dir / "audiowide.ttf"),
            str(font_dir / "oxanium-800.ttf"),
            str(font_dir / "racing-sans-one.ttf"),
            str(font_dir / "exo2-900-italic.ttf"),
        ],
        112,
    )
    log.info("name font: %s", getattr(f_name, "path", "?"))

    # Render whole word on one baseline (fixes jagged/top-misaligned glyphs)
    text = "S.Marcato"
    tracking = 2
    stroke = 2
    ascent, descent = f_name.getmetrics()
    # advance widths for tracked layout
    advances = [f_name.getlength(ch) for ch in text]
    tw = int(sum(advances) + tracking * (len(text) - 1)) + stroke * 2
    th = ascent + descent + stroke * 2
    layer = Image.new("RGBA", (tw + 100, th + 100), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    baseline_y = 50 + ascent
    x = 50.0
    for i, ch in enumerate(text):
        ld.text(
            (x, baseline_y),
            ch,
            font=f_name,
            fill=(*ICE, 255),
            stroke_width=stroke,
            stroke_fill=(*ICE, 255),
            anchor="ls",  # left + baseline — same baseline for every glyph
        )
        x += advances[i] + (tracking if i < len(text) - 1 else 0)

    # crop to content then italicize hard for speed
    bbox = layer.getbbox()
    if bbox:
        layer = layer.crop(bbox)
    layer = italicize(layer, shear=0.36)

    # soft shadow
    alpha = layer.split()[-1]
    shadow = Image.new("RGBA", layer.size, (0, 0, 0, 170))
    shadow.putalpha(alpha)
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))

    lx = cx - layer.width // 2
    ly = cy - 255 - layer.height // 2
    base.alpha_composite(shadow, (lx + 3, ly + 8))
    base.alpha_composite(layer, (lx, ly))
    name_box = (lx, ly, lx + layer.width, ly + layer.height)

    draw_hairline(base, name_box[3] + 16, cx, 100)

    logo_path = ASSETS / "smarcato42_logo_clean.png"
    mark = extract_42_racing(logo_path)
    target_h = 430
    ratio = target_h / mark.height
    mark = mark.resize((max(1, int(mark.width * ratio)), target_h), Image.Resampling.LANCZOS)

    mx = cx - mark.width // 2
    my = name_box[3] + 34
    paste_with_shadow(base, mark, (mx, my))


def main() -> None:
    t0 = time.perf_counter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log.info("compositing photo spanning wallpaper %sx%s", WIDTH, HEIGHT)

    paths = [
        ASSETS / "smarcato42_photo_left.png",
        ASSETS / "smarcato42_photo_center.png",
        ASSETS / "smarcato42_photo_right.png",
    ]
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(p)

    panels = [soften_grade(fit_cover(Image.open(p), PANEL_W, PANEL_H)) for p in paths]
    span = Image.new("RGB", (WIDTH, HEIGHT))
    for i, panel in enumerate(panels):
        span.paste(panel, (i * PANEL_W, 0))
        log.info("placed panel %s", i + 1)

    vignette = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for i in range(50):
        a = int(45 * (i / 49) ** 1.4)
        vd.rectangle([i * 8, i * 4, WIDTH - i * 8, HEIGHT - i * 4], outline=(0, 0, 0, a))
    vignette = vignette.filter(ImageFilter.GaussianBlur(40))
    span_rgba = Image.alpha_composite(span.convert("RGBA"), vignette)

    cx, cy = WIDTH // 2, HEIGHT // 2 - 10
    log.info("drawing elegant mixed-case wordmark")
    draw_wordmark(span_rgba, cx, cy)

    final = span_rgba.convert("RGB")
    log.info("saving %s", OUT)
    final.save(OUT, "PNG", optimize=True)
    for i in range(3):
        crop = final.crop((i * PANEL_W, 0, (i + 1) * PANEL_W, HEIGHT))
        path = OUT_DIR / f"smarcato42_panel_{i + 1}_2560x1440.png"
        crop.save(path, "PNG", optimize=True)
        log.info("saved %s", path.name)

    elapsed = time.perf_counter() - t0
    log.info("done in %.2fs | %s bytes", elapsed, OUT.stat().st_size)


if __name__ == "__main__":
    main()
