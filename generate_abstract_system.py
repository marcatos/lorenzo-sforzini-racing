"""Generate L.Sforzini 44 abstract graphic system (motors / carbon language).

Produces seamless tiles, overlays, SVG primitives, usage demo plates, and
merges guidelines into brand-tokens.json for shared brand-book use.
"""

from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("lsforzini44.abstract")

from brand_config import (
    BRAND_KIT,
    BRAND_SHORT,
    CARBON,
    CARBON_MID,
    HERO_ACCENT,
    HERO_ACCENT_HEX,
    HERO_ACCENT_KEY,
    ICE,
    ICE_DIM,
    MONOGRAM_DIR,
    RACE_NUMBER,
    SILVER,
    STRIPE_ANGLE_DEG,
    TYPE_SHEAR,
    WORDMARK_STEM,
)

ROOT = Path(__file__).resolve().parent
BRAND = ROOT / "brand-identity"
OUT = BRAND / "15-abstract-system"
TOKENS_PATH = BRAND / "brand-tokens.json"

BLACK = (0, 0, 0)

WEAVE_TILE = 1024


def ensure_dirs() -> dict[str, Path]:
    dirs = {
        "root": OUT,
        "weave": OUT / "01-carbon-weave",
        "stripes": OUT / "02-racing-stripes",
        "chevron": OUT / "03-speed-chevron",
        "hairline": OUT / "04-technical-hairlines",
        "accent": OUT / "05-accent-bars",
        "usage": OUT / "06-usage-examples",
        "sheets": OUT / "00-sheets",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def save_png(img: Image.Image, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)
    log.info("saved %s (%.0f KB)", path.relative_to(BRAND), path.stat().st_size / 1024)


def carbon_weave(size: int, period: int, bold: bool) -> Image.Image:
    """Seamless twill-like carbon weave (dark-on-dark, for overlays)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    px = img.load()
    # Base mid carbon
    for y in range(size):
        for x in range(size):
            # Twill: diagonal bands of raised/recessed fiber
            t = ((x + 2 * y) // (period // 2)) % 4
            if bold:
                if t in (0, 1):
                    a = 55
                    c = (28, 28, 34, a)
                else:
                    a = 28
                    c = (12, 12, 16, a)
            else:
                if t in (0, 1):
                    a = 32
                    c = (24, 24, 30, a)
                else:
                    a = 14
                    c = (10, 10, 14, a)
            # Micro fiber noise (deterministic)
            n = ((x * 17 + y * 31) ^ (x * y)) & 7
            a2 = max(0, min(255, c[3] + n - 3))
            px[x, y] = (c[0], c[1], c[2], a2)
    return img


def weave_preview(tile: Image.Image, bg: tuple[int, int, int] = CARBON) -> Image.Image:
    canvas = Image.new("RGBA", (tile.width, tile.height), (*bg, 255))
    canvas.alpha_composite(tile)
    return canvas.convert("RGB")


BRAND_SHEAR = TYPE_SHEAR  # matches Audiowide wordmark italic
# 0 = vertical ends (canvas-aligned parallelogram). Harmony with frame when inclined.
STRIPE_END_SHEAR = 0.0


def rotate_layer(src: Image.Image, angle: float, canvas_size: tuple[int, int]) -> Image.Image:
    """Paste rotated src centered on transparent canvas."""
    rotated = src.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    out = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    x = (canvas_size[0] - rotated.width) // 2
    y = (canvas_size[1] - rotated.height) // 2
    out.alpha_composite(rotated, (x, y))
    return out


def _stripe_parallelograms(
    width: int,
    height: int,
    band_w: int,
    count: int,
    gap: int,
    inset_ratio: float = 0.07,
    end_shear: float = STRIPE_END_SHEAR,
) -> list[list[tuple[float, float]]]:
    """Skew parallelograms: long edges at brand angle, ends sheared (not box cuts).

    End edges lean with a strong shear so terminals stay harmonious with the
    canvas instead of looking like rotated rectangles clipped by the frame.
    """
    angle = math.radians(STRIPE_ANGLE_DEG)
    cos_a = max(0.25, abs(math.cos(angle)))
    dy = band_w / cos_a
    gap_dy = gap / cos_a
    total = count * dy + max(0, count - 1) * gap_dy

    margin = max(0, int(width * inset_ratio))
    # Keep sheared bottom corners inside the frame
    end_dx = dy * end_shear
    x0 = float(margin)
    x1 = float(width - margin - max(0.0, end_dx))
    if x1 <= x0 + 8:
        x0, x1 = 0.0, float(width)
        end_dx = min(end_dx, width * 0.08)
        x1 = float(width) - abs(end_dx)

    span = x1 - x0
    run = span * math.tan(angle)
    y0 = height / 2 - total / 2 - run / 2

    polys: list[list[tuple[float, float]]] = []
    for i in range(count):
        yt = y0 + i * (dy + gap_dy)
        yb = yt + dy
        # TL → TR (long) → BR → BL (sheared ends, parallel)
        polys.append(
            [
                (x0, yt),
                (x1, yt + run),
                (x1 + end_dx, yb + run),
                (x0 + end_dx, yb),
            ]
        )
    return polys


def racing_stripe_band(
    width: int,
    height: int,
    band_w: int,
    color: tuple[int, int, int],
    alpha: int,
    count: int = 1,
    gap: int = 18,
    soft_ends: bool = False,
    inset_ratio: float = 0.08,
    end_shear: float = STRIPE_END_SHEAR,
) -> Image.Image:
    """Canvas-aligned parallelogram stripes (vertical ends), not rotated rectangles."""
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    for poly in _stripe_parallelograms(
        width, height, band_w, count, gap, inset_ratio=inset_ratio, end_shear=end_shear
    ):
        pts = [(int(round(x)), int(round(y))) for x, y in poly]
        d.polygon(pts, fill=(*color, alpha))
        # Crisp edge pass so vertical terminals read clearly
        d.line(pts + [pts[0]], fill=(*color, min(255, alpha + 40)), width=1)

    if soft_ends and width > 64:
        fade = max(12, int(width * max(inset_ratio, 0.04) * 0.5))
        if fade > 2:
            mask = Image.new("L", (width, height), 255)
            md = ImageDraw.Draw(mask)
            for i in range(fade):
                a = int(255 * (i / fade))
                md.line([(i, 0), (i, height)], fill=a)
                md.line([(width - 1 - i, 0), (width - 1 - i, height)], fill=a)
            r, g, b, a_ch = layer.split()
            a_ch = ImageChops.multiply(a_ch, mask)
            layer = Image.merge("RGBA", (r, g, b, a_ch))
    return layer


def make_stripe_tile(band_w: int, count: int, color: tuple[int, int, int], alpha: int) -> Image.Image:
    # Clear inset so vertical parallelogram ends are obvious on catalog tiles
    return racing_stripe_band(
        1400,
        1400,
        band_w,
        color,
        alpha,
        count=count,
        gap=max(12, band_w),
        soft_ends=False,
        inset_ratio=0.12,
        end_shear=0.0,
    )


def speed_chevron_row(
    width: int,
    height: int,
    tooth: int,
    stroke: int,
    color: tuple[int, int, int],
    alpha: int,
) -> Image.Image:
    """Chevron hash as sheared parallelograms (same language as stripes)."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = height // 2
    shear = 0.9  # chevron teeth: visible parallelogram skew
    angle = math.radians(STRIPE_ANGLE_DEG)
    # Advance along brand angle
    step = tooth + stroke * 3
    x = float(tooth)
    while x < width - tooth * 2:
        # Small parallelogram tooth
        tw = tooth * 0.85
        th = tooth * 0.55
        run = tw * math.tan(angle)
        end_dx = th * shear
        cx = x
        cy0 = cy - th / 2 - run / 2
        poly = [
            (cx, cy0),
            (cx + tw, cy0 + run),
            (cx + tw + end_dx, cy0 + run + th),
            (cx + end_dx, cy0 + th),
        ]
        d.polygon([(int(round(px)), int(round(py))) for px, py in poly], outline=(*color, alpha), width=stroke)
        x += step * math.cos(angle) + tooth * 0.35
    return img


def write_svg(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    log.info("saved %s", path.relative_to(BRAND))


def svg_chevron() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="512" height="128" viewBox="0 0 512 128" fill="none">
  <g fill="none" stroke="#F8F8FA" stroke-width="3" opacity="0.55">
    <!-- sheared parallelogram teeth -->
    <polygon points="40,40 100,28 112,70 52,82"/>
    <polygon points="120,40 180,28 192,70 132,82"/>
    <polygon points="200,40 260,28 272,70 212,82"/>
    <polygon points="280,40 340,28 352,70 292,82"/>
    <polygon points="360,40 420,28 432,70 372,82"/>
  </g>
  <text x="256" y="118" fill="#C8C8D0" font-family="Segoe UI" font-size="11" text-anchor="middle">chevron · shear {BRAND_SHEAR} · angle {STRIPE_ANGLE_DEG:.0f}°</text>
</svg>
"""


def svg_corner_brackets() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256" fill="none">
  <g stroke="#C8C8D0" stroke-width="2" opacity="0.7">
    <path d="M24 64 V24 H64"/>
    <path d="M192 24 H232 V64"/>
    <path d="M232 192 V232 H192"/>
    <path d="M64 232 H24 V192"/>
  </g>
</svg>
"""


def svg_hairline_grid() -> str:
    return """<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512" fill="none">
  <g stroke="#A8A8B0" stroke-width="1" opacity="0.28">
    <line x1="0" y1="128" x2="512" y2="128"/>
    <line x1="0" y1="256" x2="512" y2="256"/>
    <line x1="0" y1="384" x2="512" y2="384"/>
    <line x1="128" y1="0" x2="128" y2="512"/>
    <line x1="256" y1="0" x2="256" y2="512"/>
    <line x1="384" y1="0" x2="384" y2="512"/>
  </g>
  <g stroke="#F8F8FA" stroke-width="1" opacity="0.45">
    <line x1="240" y1="256" x2="272" y2="256"/>
    <line x1="256" y1="240" x2="256" y2="272"/>
  </g>
</svg>
"""


def technical_hairlines(size: tuple[int, int] = (1920, 1080)) -> Image.Image:
    w, h = size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Sparse horizontal ticks
    for y in (int(h * 0.18), int(h * 0.5), int(h * 0.82)):
        d.line([(80, y), (w - 80, y)], fill=(*SILVER, 55), width=1)
        for x in range(120, w - 120, 96):
            d.line([(x, y - 6), (x, y + 6)], fill=(*ICE_DIM, 70), width=1)
    # Corner brackets
    b = 48
    m = 40
    col = (*ICE_DIM, 160)
    for x0, y0, dx, dy in (
        (m, m, 1, 1),
        (w - m, m, -1, 1),
        (m, h - m, 1, -1),
        (w - m, h - m, -1, -1),
    ):
        d.line([(x0, y0 + dy * b), (x0, y0), (x0 + dx * b, y0)], fill=col, width=2)
    return img


def accent_bar_vertical(height: int = 1080, width: int = 8, color=HERO_ACCENT) -> Image.Image:
    img = Image.new("RGBA", (width + 40, height), (0, 0, 0, 0))
    ImageDraw.Draw(img).rectangle([20, 0, 20 + width, height], fill=(*color, 255))
    return img


def accent_stripe_oblique(size: tuple[int, int] = (1920, 1080)) -> Image.Image:
    return racing_stripe_band(size[0], size[1], 10, HERO_ACCENT, 200, count=1, gap=0)


def fit_logo(path: Path, max_h: int) -> Image.Image | None:
    if not path.exists():
        return None
    logo = Image.open(path).convert("RGBA")
    ratio = max_h / logo.height
    return logo.resize((max(1, int(logo.width * ratio)), max_h), Image.Resampling.LANCZOS)


def compose_usage_wallpaper(dirs: dict[str, Path], weave: Image.Image) -> Image.Image:
    w, h = 1920, 1080
    base = Image.new("RGBA", (w, h), (*CARBON, 255))
    # Tile weave
    for y in range(0, h, weave.height):
        for x in range(0, w, weave.width):
            base.alpha_composite(weave, (x, y))
    stripe = racing_stripe_band(w, h, 28, ICE, 40, count=2, gap=22)
    base.alpha_composite(stripe)
    base.alpha_composite(accent_stripe_oblique((w, h)))
    base.alpha_composite(technical_hairlines((w, h)))
    logo = fit_logo(BRAND / "01-primary-stacked" / "primary_stacked_on_carbon.png", 420)
    if logo is None:
        logo = fit_logo(BRAND / "01-primary-stacked" / "primary_stacked_master_2048_carbon.png", 420)
    if logo:
        # Punch dark plate behind? logo already on carbon in file — extract by using mono if available
        mono = fit_logo(BRAND / "01-primary-stacked" / "primary_stacked_mono_white.png", 380)
        mark = mono or logo
        lx = (w - mark.width) // 2
        ly = (h - mark.height) // 2
        base.alpha_composite(mark, (lx, ly))
    return base.convert("RGB")


def compose_usage_lower_third(dirs: dict[str, Path]) -> Image.Image:
    w, h = 1920, 1080
    base = Image.new("RGBA", (w, h), (*CARBON, 255))
    # Dark plate bottom
    plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rectangle([0, int(h * 0.72), w, h], fill=(*CARBON_MID, 230))
    base.alpha_composite(plate)
    chev = speed_chevron_row(900, 120, tooth=48, stroke=2, color=ICE, alpha=120)
    base.alpha_composite(chev, (80, int(h * 0.74)))
    accent = accent_bar_vertical(int(h * 0.22), 6)
    base.alpha_composite(accent, (40, int(h * 0.74)))
    word = fit_logo(BRAND / "04-wordmark" / f"{WORDMARK_STEM}_mono_white.png", 64)
    if word:
        base.alpha_composite(word, (100, int(h * 0.78)))
    tag = fit_logo(BRAND / "05-tag-racing" / "tag_racing_mono_white.png", 28)
    if tag is None:
        tag = fit_logo(BRAND / "05-tag-racing" / "tag_racing_on_carbon.png", 28)
    if tag:
        base.alpha_composite(tag, (100, int(h * 0.86)))
    return base.convert("RGB")


def compose_usage_story(dirs: dict[str, Path], weave_fine: Image.Image) -> Image.Image:
    w, h = 1080, 1920
    base = Image.new("RGBA", (w, h), (*CARBON, 255))
    for y in range(0, h, weave_fine.height):
        for x in range(0, w, weave_fine.width):
            base.alpha_composite(weave_fine, (x, y))
    stripe = racing_stripe_band(w, h, 18, SILVER, 35, count=3, gap=14)
    base.alpha_composite(stripe)
    # Soft bottom brand zone
    veil = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vd = ImageDraw.Draw(veil)
    for i, y in enumerate(range(int(h * 0.7), h)):
        a = int(160 * (i / max(1, h - int(h * 0.7))))
        vd.line([(0, y), (w, y)], fill=(*CARBON, a))
    base.alpha_composite(veil)
    mono = fit_logo(BRAND / MONOGRAM_DIR / f"monogram_ls44_mono_white.png", 280)
    if mono is None:
        mono = fit_logo(BRAND / MONOGRAM_DIR / f"monogram_ls44_on_carbon.png", 280)
    if mono:
        base.alpha_composite(mono, ((w - mono.width) // 2, int(h * 0.38)))
    return base.convert("RGB")


def compose_usage_poster(dirs: dict[str, Path], weave_bold: Image.Image) -> Image.Image:
    w, h = 1080, 1350
    base = Image.new("RGBA", (w, h), (*CARBON, 255))
    for y in range(0, h, weave_bold.height):
        for x in range(0, w, weave_bold.width):
            base.alpha_composite(weave_bold, (x, y))
    base.alpha_composite(racing_stripe_band(w, h, 40, ICE, 28, count=1))
    base.alpha_composite(racing_stripe_band(w, h, 8, HERO_ACCENT, 220, count=1))
    hl = technical_hairlines((w, h))
    base.alpha_composite(hl)
    logo = fit_logo(BRAND / "01-primary-stacked" / "primary_stacked_mono_white.png", 520)
    if logo:
        base.alpha_composite(logo, ((w - logo.width) // 2, (h - logo.height) // 2 - 40))
    return base.convert("RGB")


def guidelines_sheet(dirs: dict[str, Path], weave_fine: Image.Image) -> Image.Image:
    """Do / Don't visual sheet for brand book."""
    w, h = 2400, 1600
    img = Image.new("RGB", (w, h), (245, 245, 247))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, 90], fill=CARBON)
    d.text((48, 28), "15 · Abstract system — do / don't", fill=ICE)

    def panel(x: int, y: int, pw: int, ph: int, title: str, ok: bool, content: Image.Image) -> None:
        d.rectangle([x, y, x + pw, y + ph], fill=CARBON if ok else (30, 20, 20), outline=(60, 60, 70), width=2)
        thumb = content.resize((pw - 24, ph - 70), Image.Resampling.LANCZOS)
        img.paste(thumb, (x + 12, y + 12))
        label = "DO  ·  " + title if ok else "DON'T  ·  " + title
        color = (80, 180, 120) if ok else (225, 80, 70)
        d.text((x + 16, y + ph - 42), label, fill=color)

    # DO: subtle weave + logo
    do1 = Image.new("RGBA", (800, 500), (*CARBON, 255))
    for yy in range(0, 500, weave_fine.height):
        for xx in range(0, 800, weave_fine.width):
            do1.alpha_composite(weave_fine, (xx, yy))
    logo = fit_logo(BRAND / "01-primary-stacked" / "primary_stacked_mono_white.png", 220)
    if logo:
        do1.alpha_composite(logo, ((800 - logo.width) // 2, (500 - logo.height) // 2))
    panel(40, 120, 720, 520, "Weave soft + clearspace", True, do1.convert("RGB"))

    # DON'T: weave crushing logo
    dont1 = Image.new("RGBA", (800, 500), (*CARBON, 255))
    heavy = carbon_weave(256, period=16, bold=True)
    # Amplify alpha
    heavy = Image.blend(
        Image.new("RGBA", heavy.size, (0, 0, 0, 0)),
        heavy,
        1.0,
    )
    for yy in range(0, 500, 256):
        for xx in range(0, 800, 256):
            # Extra opaque overlay
            blot = Image.new("RGBA", (256, 256), (60, 60, 70, 160))
            dont1.alpha_composite(blot, (xx, yy))
            dont1.alpha_composite(heavy, (xx, yy))
    if logo:
        dont1.alpha_composite(logo, ((800 - logo.width) // 2, (500 - logo.height) // 2))
    panel(820, 120, 720, 520, "Weave too loud under logo", False, dont1.convert("RGB"))

    # DO: -18 stripe
    do2 = Image.new("RGBA", (800, 500), (*CARBON, 255))
    do2.alpha_composite(racing_stripe_band(800, 500, 20, ICE, 50, count=2, gap=16))
    if logo:
        do2.alpha_composite(logo, ((800 - logo.width) // 2, (500 - logo.height) // 2))
    panel(40, 680, 720, 520, f"Stripe angle {STRIPE_ANGLE_DEG:.0f}°", True, do2.convert("RGB"))

    # DON'T: wrong angle / rainbow
    dont2 = Image.new("RGBA", (800, 500), (*CARBON, 255))
    bad = racing_stripe_band(800, 500, 40, HERO_ACCENT, 200, count=1)
    # Force wrong angle by rotating extra
    bad = bad.rotate(35, expand=False, fillcolor=(0, 0, 0, 0))
    dont2.alpha_composite(bad)
    rainbow = racing_stripe_band(800, 500, 30, (0, 163, 224), 180, count=1)
    dont2.alpha_composite(rainbow)
    if logo:
        dont2.alpha_composite(logo, ((800 - logo.width) // 2, (500 - logo.height) // 2))
    panel(820, 680, 720, 520, "Wrong angle / multi-accent", False, dont2.convert("RGB"))

    # Third column tips
    d.rectangle([1600, 120, 2360, 1200], fill=(255, 255, 255), outline=(200, 200, 210))
    tips = [
        "Guidelines",
        "",
        "• Stripe −18° + vertical ends (parallelogram)",
        "• Weave opacity: fine 8–18% · bold 12–22%",
        "• Max 1 racing accent stripe per layout",
        "• Keep logo clearspace free of chevrons",
        "• Hairlines = structure, not decoration spam",
        "• Prefer carbon/ice/silver for structure",
        "• Rosso only as thin accent bar / CTA edge",
        "• Tile weave; never stretch non-uniformly",
        "• Abstract layers sit BEHIND logo stack",
        "• Stripe ends: sheared parallelogram, inset",
    ]
    y = 150
    for line in tips:
        d.text((1640, y), line, fill=(30, 30, 36) if line else (255, 255, 255))
        y += 42

    return img


def overview_sheet(
    dirs: dict[str, Path],
    samples: list[tuple[str, Image.Image]],
) -> Image.Image:
    w, h = 2400, 1400
    img = Image.new("RGB", (w, h), CARBON)
    d = ImageDraw.Draw(img)
    d.text((48, 36), "15 · Abstract system — motors / carbon", fill=ICE)
    cols = 3
    pad = 40
    cell_w = (w - pad * 4) // cols
    cell_h = 360
    for i, (title, sample) in enumerate(samples[:6]):
        col, row = i % cols, i // cols
        x = pad + col * (cell_w + pad)
        y = 100 + row * (cell_h + 80)
        thumb = sample.resize((cell_w, cell_h - 40), Image.Resampling.LANCZOS)
        img.paste(thumb.convert("RGB"), (x, y))
        d.text((x, y + cell_h - 28), title, fill=ICE_DIM)
    return img


def update_tokens() -> None:
    tokens: dict = {}
    if TOKENS_PATH.exists():
        tokens = json.loads(TOKENS_PATH.read_text(encoding="utf-8"))
    tokens["abstract_system"] = {
        "language": "motors / carbon",
        "stripe_angle_deg": STRIPE_ANGLE_DEG,
        "weave": {
            "tile_px": WEAVE_TILE,
            "fine_period_px": 28,
            "bold_period_px": 18,
            "opacity_fine_pct": [8, 18],
            "opacity_bold_pct": [12, 22],
        },
        "stripes": {
            "counts": [1, 2, 3],
            "shape": "sheared_parallelogram",
            "long_edge_angle_deg": STRIPE_ANGLE_DEG,
            "end_shear": 0.0,
            "end_edges": "vertical_canvas_aligned",
            "type_shear_ref": BRAND_SHEAR,
            "inset_ratio_default": 0.08,
            "soft_ends": False,
            "colors": ["ice", "silver", "electric_blue"],
            "max_racing_accent_per_layout": 1,
            "note": "Parallelogram with vertical ends — never rotated rectangles",
        },
        "chevron": {"scales": ["sm", "md", "lg"], "keep_out_of_logo_clearspace": True},
        "hairlines": {"use": "structure / framing", "opacity_pct": [15, 35]},
        "layer_order": [
            "carbon_base",
            "carbon_weave",
            "racing_stripes",
            "technical_hairlines",
            "accent_bar",
            "logo_lockup",
        ],
        "dont": [
            "stretch weave non-uniformly",
            "place dense pattern inside logo clearspace",
            "mix multiple racing accent colors in one abstract stack",
            "use stripe angles other than -18°",
            f"place chevrons over wordmark or {RACE_NUMBER} mark",
        ],
    }
    TOKENS_PATH.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    log.info("updated %s", TOKENS_PATH)


def main() -> None:
    t0 = time.perf_counter()
    dirs = ensure_dirs()
    log.info("start abstract system → %s", OUT)

    # --- Weave ---
    t = time.perf_counter()
    weave_fine = carbon_weave(WEAVE_TILE, period=28, bold=False)
    weave_bold = carbon_weave(WEAVE_TILE, period=18, bold=True)
    save_png(weave_fine, dirs["weave"] / "weave_fine_1024_transparent.png")
    save_png(weave_bold, dirs["weave"] / "weave_bold_1024_transparent.png")
    save_png(weave_preview(weave_fine), dirs["weave"] / "weave_fine_1024_on_carbon.png")
    save_png(weave_preview(weave_bold), dirs["weave"] / "weave_bold_1024_on_carbon.png")
    # Light ground variants (dark fibers)
    save_png(weave_preview(weave_fine, ICE), dirs["weave"] / "weave_fine_1024_on_ice.png")
    log.info("weave done in %.0f ms", (time.perf_counter() - t) * 1000)

    # --- Stripes ---
    t = time.perf_counter()
    stripe_specs = [
        ("stripe_single_ice", 36, 1, ICE, 70),
        ("stripe_double_ice", 22, 2, ICE, 60),
        ("stripe_triple_silver", 14, 3, SILVER, 55),
        ("stripe_single_electric_blue", 12, 1, HERO_ACCENT, 200),
    ]
    for name, bw, count, color, alpha in stripe_specs:
        tile = make_stripe_tile(bw, count, color, alpha)
        save_png(tile, dirs["stripes"] / f"{name}_1400.png")
        preview = Image.new("RGBA", (1400, 1400), (*CARBON, 255))
        preview.alpha_composite(tile)
        save_png(preview.convert("RGB"), dirs["stripes"] / f"{name}_on_carbon.png")
    write_svg(
        dirs["stripes"] / "stripe_angle_guide.svg",
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200" viewBox="0 0 400 200">
  <rect width="400" height="200" fill="#08080A"/>
  <!-- Sheared parallelogram: slanted run + italic end cuts (not rotated rect) -->
  <polygon points="40,50 360,20 360,55 40,85" fill="#F8F8FA" opacity="0.55"/>
  <polygon points="40,100 360,70 360,88 40,118" fill="{HERO_ACCENT_HEX}" opacity="0.85"/>
  <text x="200" y="175" fill="#C8C8D0" font-family="Segoe UI" font-size="12" text-anchor="middle">parallelogram · {STRIPE_ANGLE_DEG:.0f}° · vertical ends</text>
</svg>
""",
    )
    log.info("stripes done in %.0f ms", (time.perf_counter() - t) * 1000)

    # --- Chevron ---
    t = time.perf_counter()
    for label, tooth, stroke, size in (
        ("chevron_sm", 28, 2, (960, 240)),
        ("chevron_md", 48, 2, (1200, 280)),
        ("chevron_lg", 72, 3, (1600, 360)),
    ):
        ch = speed_chevron_row(size[0], size[1], tooth, stroke, ICE, 140)
        save_png(ch, dirs["chevron"] / f"{label}_transparent.png")
        prev = Image.new("RGBA", size, (*CARBON, 255))
        prev.alpha_composite(ch)
        save_png(prev.convert("RGB"), dirs["chevron"] / f"{label}_on_carbon.png")
    write_svg(dirs["chevron"] / "chevron_row.svg", svg_chevron())
    log.info("chevron done in %.0f ms", (time.perf_counter() - t) * 1000)

    # --- Hairlines ---
    t = time.perf_counter()
    hl = technical_hairlines((1920, 1080))
    save_png(hl, dirs["hairline"] / "hairlines_1920x1080_transparent.png")
    prev = Image.new("RGBA", (1920, 1080), (*CARBON, 255))
    prev.alpha_composite(hl)
    save_png(prev.convert("RGB"), dirs["hairline"] / "hairlines_on_carbon.png")
    write_svg(dirs["hairline"] / "corner_brackets.svg", svg_corner_brackets())
    write_svg(dirs["hairline"] / "grid_sparse.svg", svg_hairline_grid())
    log.info("hairlines done in %.0f ms", (time.perf_counter() - t) * 1000)

    # --- Accent bars ---
    t = time.perf_counter()
    save_png(accent_bar_vertical(), dirs["accent"] / "accent_bar_electric_blue_vertical.png")
    save_png(accent_stripe_oblique(), dirs["accent"] / "accent_stripe_electric_blue_oblique_1920x1080.png")
    for name, rgb in (
        ("papaya", (255, 135, 0)),
        ("signal_yellow", (245, 196, 0)),
        ("electric_blue", (0, 163, 224)),
        ("titanium", (138, 143, 152)),
    ):
        bar = accent_bar_vertical(1080, 8, rgb)
        save_png(bar, dirs["accent"] / f"accent_bar_{name}_vertical.png")
    log.info("accents done in %.0f ms", (time.perf_counter() - t) * 1000)

    # --- Usage examples ---
    t = time.perf_counter()
    usage_wall = compose_usage_wallpaper(dirs, weave_fine)
    usage_lt = compose_usage_lower_third(dirs)
    usage_story = compose_usage_story(dirs, weave_fine)
    usage_poster = compose_usage_poster(dirs, weave_bold)
    save_png(usage_wall, dirs["usage"] / "example_wallpaper_1920x1080.png")
    save_png(usage_lt, dirs["usage"] / "example_lower_third_1920x1080.png")
    save_png(usage_story, dirs["usage"] / "example_story_1080x1920.png")
    save_png(usage_poster, dirs["usage"] / "example_poster_1080x1350.png")
    log.info("usage examples done in %.0f ms", (time.perf_counter() - t) * 1000)

    # --- Sheets ---
    t = time.perf_counter()
    overview = overview_sheet(
        dirs,
        [
            ("Carbon weave fine", weave_preview(weave_fine)),
            ("Carbon weave bold", weave_preview(weave_bold)),
            ("Racing stripes", Image.open(dirs["stripes"] / "stripe_double_ice_on_carbon.png")),
            ("Speed chevron", Image.open(dirs["chevron"] / "chevron_md_on_carbon.png")),
            ("Technical hairlines", Image.open(dirs["hairline"] / "hairlines_on_carbon.png")),
            ("Usage wallpaper", usage_wall),
        ],
    )
    save_png(overview, dirs["sheets"] / "abstract_system_overview.png")
    save_png(guidelines_sheet(dirs, weave_fine), dirs["sheets"] / "abstract_do_dont.png")
    log.info("sheets done in %.0f ms", (time.perf_counter() - t) * 1000)

    update_tokens()

    # README for shared guidelines
    (OUT / "README.md").write_text(
        f"""# 15 · Abstract system (motors / carbon)

Shared graphic language for backgrounds and layouts with {BRAND_KIT}.

## Families
- `01-carbon-weave` — seamless tiles (fine / bold)
- `02-racing-stripes` — single / double / triple at **{STRIPE_ANGLE_DEG:.0f}°**
- `03-speed-chevron` — hash marks (sm / md / lg) + SVG
- `04-technical-hairlines` — ticks, brackets, sparse grid
- `05-accent-bars` — electric blue (and racing-color) edge accents
- `06-usage-examples` — wallpaper, lower-third, story, poster

## Layer order
carbon base → weave → stripes → hairlines → accent bar → logo

## Rules
See `brand-tokens.json` → `abstract_system` and sheets in `00-sheets/`.
""",
        encoding="utf-8",
    )

    n = len(list(OUT.rglob("*.*")))
    log.info("abstract system complete: %d files in %.2fs", n, time.perf_counter() - t0)


if __name__ == "__main__":
    main()
