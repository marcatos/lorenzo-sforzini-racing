"""Shared raster rendering helpers for Lorenzo Sforzini brand kit."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from brand_config import (
    BRAND_SHORT,
    FONTS,
    HERO_ACCENT,
    ICE,
    ICE_DIM,
    MONOGRAM_LETTERS,
    RACE_NUMBER,
    TAGLINE,
    TYPE_SHEAR,
    WIN_FONTS,
)


def font(path_names: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in path_names:
        p = Path(name)
        if not p.is_file():
            p = FONTS / name
        if not p.is_file():
            p = WIN_FONTS / name
        try:
            return ImageFont.truetype(str(p), size)
        except OSError:
            continue
    return ImageFont.load_default()


def italicize(rgba: Image.Image, shear: float = TYPE_SHEAR) -> Image.Image:
    w, h = rgba.size
    pad = int(abs(shear) * h) + 8
    canvas = Image.new("RGBA", (w + pad * 2, h + 8), (0, 0, 0, 0))
    canvas.paste(rgba, (pad, 4))
    cw, ch = canvas.size
    return canvas.transform(
        (cw + int(abs(shear) * ch), ch),
        Image.Transform.AFFINE,
        (1, shear, -shear * ch if shear > 0 else 0, 0, 1, 0),
        resample=Image.Resampling.BICUBIC,
    )


def trim(img: Image.Image, pad: int = 0) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    cropped = img.crop(bbox)
    if pad <= 0:
        return cropped
    out = Image.new("RGBA", (cropped.width + pad * 2, cropped.height + pad * 2), (0, 0, 0, 0))
    out.paste(cropped, (pad, pad), cropped)
    return out


def recolor_opaque(img: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
    img = img.convert("RGBA")
    r, g, b = rgb
    pixels = []
    for pr, pg, pb, pa in img.getdata():
        if pa < 8:
            pixels.append((0, 0, 0, 0))
        else:
            pixels.append((r, g, b, pa))
    img.putdata(pixels)
    return img


def render_tracked_text(
    text: str,
    size: int,
    color: tuple[int, int, int],
    font_names: list[str],
    tracking_ratio: float = 0.02,
    stroke_ratio: float = 0.018,
    shear: float = TYPE_SHEAR,
) -> Image.Image:
    f = font(font_names, size)
    tracking = max(1, int(size * tracking_ratio))
    stroke = max(1, int(size * stroke_ratio))
    ascent, descent = f.getmetrics()
    advances = [f.getlength(ch) for ch in text]
    tw = int(sum(advances) + tracking * (len(text) - 1)) + stroke * 2
    th = ascent + descent + stroke * 2
    layer = Image.new("RGBA", (tw + 120, th + 120), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    baseline = 60 + ascent
    x = 60.0
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
    return italicize(trim(layer), shear=shear)


def render_wordmark(size: int = 180, color: tuple[int, int, int] = ICE) -> Image.Image:
    return render_tracked_text(BRAND_SHORT, size, color, ["audiowide.ttf"])


def render_race_number(
    size: int = 280,
    color: tuple[int, int, int] = HERO_ACCENT,
    shear: float = 0.32,
) -> Image.Image:
    """Hero race number — bold italic Audiowide."""
    f = font(["audiowide.ttf"], size)
    stroke = max(2, size // 40)
    ascent, descent = f.getmetrics()
    tw = int(f.getlength(RACE_NUMBER)) + stroke * 2
    th = ascent + descent + stroke * 2
    layer = Image.new("RGBA", (tw + 80, th + 80), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.text(
        (40, 40 + ascent),
        RACE_NUMBER,
        font=f,
        fill=(*color, 255),
        stroke_width=stroke,
        stroke_fill=(*color, 255),
        anchor="ls",
    )
    return italicize(trim(layer), shear=shear)


def render_tagline(size: int = 48, color: tuple[int, int, int] = ICE_DIM, tracking: int = 18) -> Image.Image:
    f = font(["Candaral.ttf", "segoeuil.ttf", "calibril.ttf"], size)
    text = TAGLINE
    advances = [f.getlength(ch) for ch in text]
    ascent, descent = f.getmetrics()
    tw = int(sum(advances) + tracking * (len(text) - 1))
    layer = Image.new("RGBA", (tw + 40, ascent + descent + 40), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    x = 20.0
    baseline = 20 + ascent
    for i, ch in enumerate(text):
        ld.text((x, baseline), ch, font=f, fill=(*color, 255), anchor="ls")
        x += advances[i] + tracking
    return trim(layer)


def render_monogram(size: int = 320, color: tuple[int, int, int] = ICE) -> Image.Image:
    """LS monogram with small 44 badge."""
    f = font(["audiowide.ttf"], size)
    layer = Image.new("RGBA", (size * 3, size * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    letters = MONOGRAM_LETTERS
    ld.text((size // 2, size // 3), letters[0], font=f, fill=(*color, 255), anchor="mm")
    f2 = font(["audiowide.ttf"], int(size * 0.92))
    ld.text((size // 2 + size // 8, size), letters[1], font=f2, fill=(*color, 255), anchor="mm")
    f3 = font(["audiowide.ttf"], int(size * 0.22))
    ld.text(
        (size // 2 + size // 2, int(size * 1.35)),
        RACE_NUMBER,
        font=f3,
        fill=(*HERO_ACCENT, 255),
        anchor="mm",
    )
    return italicize(trim(layer), shear=0.28)


def stack_vertical(
    parts: list[Image.Image],
    gaps: list[int],
    hairline: bool = False,
    hairline_color: tuple[int, int, int] = ICE,
) -> Image.Image:
    widths = [p.width for p in parts]
    max_w = max(widths)
    total_h = sum(p.height for p in parts) + sum(gaps)
    if hairline:
        total_h += 20
    canvas = Image.new("RGBA", (max_w + 40, total_h + 40), (0, 0, 0, 0))
    y = 20
    for i, part in enumerate(parts):
        x = 20 + (max_w - part.width) // 2
        canvas.alpha_composite(part, (x, y))
        y += part.height
        if i < len(gaps):
            if hairline and i == 0:
                y += gaps[i] // 2
                ld = ImageDraw.Draw(canvas)
                cx = canvas.width // 2
                ld.line([(cx - 80, y), (cx + 80, y)], fill=(*hairline_color, 200), width=2)
                y += gaps[i] - gaps[i] // 2 + 4
            else:
                y += gaps[i]
    return trim(canvas, pad=8)


def horizontal_lockup(name: Image.Image, mark: Image.Image, racing: Image.Image, gap: int = 48) -> Image.Image:
    right = stack_vertical([mark, racing], gaps=[18], hairline=False)
    h = max(name.height, right.height)
    w = name.width + gap + 2 + gap + right.width
    canvas = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    ny = 20 + (h - name.height) // 2
    canvas.alpha_composite(name, (20, ny))
    ld = ImageDraw.Draw(canvas)
    rx = 20 + name.width + gap
    ld.line([(rx, 20), (rx, 20 + h)], fill=(*ICE_DIM, 180), width=2)
    ry = 20 + (h - right.height) // 2
    canvas.alpha_composite(right, (rx + gap, ry))
    return trim(canvas, pad=8)
