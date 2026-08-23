"""Generate S.Marcato 42 Racing carbon-night livery for Toyota GR86 Trading Paints template.

Input: flattened template preview (or PSD composite) 2048x2048.
Output: paint TGA/PNG + specular hint + side-by-side preview.
"""

from __future__ import annotations

import logging
import math
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("smarcato42.livery")

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "brand-identity"
OUT = ROOT / "liveries" / "gr86-carbon-night"
TEMPLATE_PREVIEW = ROOT / "liveries" / "_tmp_gr86_template" / "preview_flat.jpg"
TEMPLATE_PSD = ROOT / "liveries" / "_tmp_gr86_template" / "Toyota GR86.psd"

CARBON = (8, 8, 10)
CARBON_MID = (18, 18, 22)
CARBON_HI = (32, 32, 38)
ICE = (248, 248, 250)
ICE_DIM = (200, 200, 208)
SILVER = (168, 168, 176)
ROSSO = (225, 6, 0)
STRIPE_ANGLE = -18.0
SIZE = 2048


def load_template() -> Image.Image:
    if TEMPLATE_PREVIEW.exists():
        log.info("template preview %s", TEMPLATE_PREVIEW)
        return Image.open(TEMPLATE_PREVIEW).convert("RGBA").resize((SIZE, SIZE), Image.Resampling.LANCZOS)
    if TEMPLATE_PSD.exists():
        log.info("template PSD composite %s", TEMPLATE_PSD)
        return Image.open(TEMPLATE_PSD).convert("RGBA")
    raise FileNotFoundError("GR86 template preview/PSD not found")


def is_body_blue(r: int, g: int, b: int, a: int = 255) -> bool:
    if a < 20:
        return False
    # Gazoo template blue body
    return b > 140 and b > r + 40 and b > g + 10 and r < 130 and g < 180


def is_sponsor_red_block(r: int, g: int, b: int) -> bool:
    return r > 160 and g < 90 and b < 90 and r > g + 60


def body_mask(src: Image.Image) -> Image.Image:
    """Alpha mask of paintable blue body (+ red door blocks to recolor)."""
    rgb = src.convert("RGB")
    data = rgb.getdata()
    out = bytearray(len(data))
    for i, (r, g, b) in enumerate(data):
        if (b > 140 and b > r + 40 and b > g + 10 and r < 130 and g < 180) or (
            r > 160 and g < 90 and b < 90 and r > g + 60
        ):
            out[i] = 255
    mask = Image.new("L", rgb.size)
    mask.putdata(out)
    mask = mask.filter(ImageFilter.MaxFilter(3))
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))
    return mask


def scrub_sponsors_on_body(paint: Image.Image, mask: Image.Image) -> None:
    """Darken leftover bright sponsor pixels inside body mask."""
    rgba = paint.convert("RGBA")
    pdata = list(rgba.getdata())
    mdata = list(mask.getdata())
    mid = (*CARBON_MID, 255)
    for i, ((r, g, b, a), m) in enumerate(zip(pdata, mdata)):
        if m < 128:
            continue
        bright = r > 170 or g > 170 or (b > 170 and r > 100)
        colorful = abs(r - g) > 40 or abs(g - b) > 40 or abs(r - b) > 40
        if bright and colorful:
            pdata[i] = (mid[0], mid[1], mid[2], a)
    rgba.putdata(pdata)
    paint.paste(rgba)


def restore_non_body(paint: Image.Image, orig: Image.Image, mask: Image.Image) -> None:
    rgba = paint.convert("RGBA")
    odata = list(orig.convert("RGBA").getdata())
    pdata = list(rgba.getdata())
    mdata = list(mask.getdata())
    for i, m in enumerate(mdata):
        if m < 40:
            pdata[i] = odata[i]
    rgba.putdata(pdata)
    paint.paste(rgba)


def carbon_fill(size: int = SIZE) -> Image.Image:
    """Subtle carbon weave fill."""
    img = Image.new("RGB", (size, size), CARBON)
    px = img.load()
    period = 14
    for y in range(size):
        for x in range(size):
            t = ((x + 2 * y) // (period // 2)) % 4
            n = ((x * 17 + y * 31) ^ (x * y)) & 7
            if t in (0, 1):
                c = CARBON_HI
                a = 18 + n
            else:
                c = CARBON_MID
                a = 8 + (n // 2)
            # blend toward carbon
            r = int(CARBON[0] + (c[0] - CARBON[0]) * a / 40)
            g = int(CARBON[1] + (c[1] - CARBON[1]) * a / 40)
            b = int(CARBON[2] + (c[2] - CARBON[2]) * a / 40)
            px[x, y] = (r, g, b)
    return img


def stripe_parallelograms(
    width: int,
    height: int,
    band_w: int,
    count: int,
    gap: int,
    cy: float,
    x0: float,
    x1: float,
    color: tuple[int, int, int],
    alpha: int,
) -> Image.Image:
    angle = math.radians(STRIPE_ANGLE)
    cos_a = max(0.25, abs(math.cos(angle)))
    dy = band_w / cos_a
    gap_dy = gap / cos_a
    total = count * dy + max(0, count - 1) * gap_dy
    span = x1 - x0
    run = span * math.tan(angle)
    y0 = cy - total / 2 - run / 2
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(count):
        yt = y0 + i * (dy + gap_dy)
        yb = yt + dy
        poly = [
            (x0, yt),
            (x1, yt + run),
            (x1, yb + run),
            (x0, yb),
        ]
        d.polygon([(int(p[0]), int(p[1])) for p in poly], fill=(*color, alpha))
    return layer


def load_logo(rel: str, max_h: int) -> Image.Image | None:
    p = BRAND / rel
    if not p.exists():
        log.warning("missing logo %s", p)
        return None
    im = Image.open(p).convert("RGBA")
    # punch near-black to alpha for on_* composites that include bg
    if "mono_white" in rel or "transparent" in rel:
        pass
    else:
        # keep as-is
        pass
    ratio = max_h / im.height
    return im.resize((max(1, int(im.width * ratio)), max_h), Image.Resampling.LANCZOS)


def recolor_logo(im: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
    im = im.convert("RGBA")
    r, g, b = rgb
    out = []
    for pr, pg, pb, pa in im.getdata():
        if pa < 8:
            out.append((0, 0, 0, 0))
        else:
            out.append((r, g, b, pa))
    im.putdata(out)
    return im


def paste_center(base: Image.Image, logo: Image.Image, cx: int, cy: int, opacity: float = 1.0) -> None:
    if opacity < 1:
        a = logo.split()[-1].point(lambda v: int(v * opacity))
        logo = logo.copy()
        logo.putalpha(a)
    x = int(cx - logo.width / 2)
    y = int(cy - logo.height / 2)
    base.alpha_composite(logo, (x, y))


def build_livery() -> tuple[Image.Image, Image.Image]:
    t0 = time.perf_counter()
    tpl = load_template()
    log.info("building body mask…")
    mask = body_mask(tpl)
    mask_path = OUT / "debug_body_mask.png"
    mask.save(mask_path)
    log.info("mask saved %s (%.0f ms)", mask_path.name, (time.perf_counter() - t0) * 1000)

    # Start from template, replace body with carbon
    carbon = carbon_fill(SIZE).convert("RGBA")
    paint = tpl.copy()
    paint.paste(carbon, (0, 0), mask)
    scrub_sponsors_on_body(paint, mask)

    # Brand accents — UV placements tuned to GR86 Trading Paints sheet
    # Hood (large left-center panel)
    hood = load_logo("01-primary-stacked/primary_stacked_mono_white.png", 280)
    if hood:
        paste_center(paint, hood, 420, 480, 0.95)
    mark_hood = load_logo("03-mark-42/mark_42_mono_white.png", 160)
    if mark_hood:
        mark_hood = recolor_logo(mark_hood, ROSSO)
        paste_center(paint, mark_hood, 420, 620, 0.98)

    # Roof — ice double stripe + small monogram
    roof_stripes = stripe_parallelograms(
        SIZE, SIZE, 18, 2, 14, cy=520, x0=980, x1=1450, color=ICE_DIM, alpha=90
    )
    paint.alpha_composite(roof_stripes)
    mono = load_logo("06-monogram-sm/monogram_sm42_mono_white.png", 70)
    if mono:
        paste_center(paint, mono, 1220, 700, 0.85)

    # Side skirts / rocker — long parallelogram stripes (top & bottom strips)
    # Bottom strip ≈ driver side silhouette band
    for cy, x0, x1 in (
        (1750, 80, 1980),   # lower side band
        (120, 80, 1600),    # upper side band
    ):
        side = stripe_parallelograms(SIZE, SIZE, 22, 2, 16, cy=cy, x0=x0, x1=x1, color=SILVER, alpha=70)
        paint.alpha_composite(side)
        accent = stripe_parallelograms(SIZE, SIZE, 6, 1, 0, cy=cy, x0=x0, x1=x1, color=ROSSO, alpha=210)
        paint.alpha_composite(accent)

    # Door number zones (approx where red blocks were) — 42 rosso + S.Marcato
    word = load_logo("04-wordmark/wordmark_smarcato_mono_white.png", 48)
    mark_door = load_logo("03-mark-42/mark_42_mono_white.png", 110)
    if mark_door:
        mark_door = recolor_logo(mark_door, ROSSO)
    for cx, cy in ((720, 1680), (1280, 200), (720, 200), (1280, 1680)):
        if mark_door:
            paste_center(paint, mark_door, cx, cy, 0.95)
        if word:
            paste_center(paint, word, cx, cy + 70, 0.9)

    # Front bumper / nose — small monogram
    if mono:
        paste_center(paint, mono.resize((50, 50), Image.Resampling.LANCZOS), 80, 900, 0.8)

    # Keep non-body template details (wires, glass, mandatory)
    restore_non_body(paint, tpl, mask)

    # Specular hint map: brighter on ice stripes / logos, dark carbon
    spec = Image.new("RGB", (SIZE, SIZE), (30, 30, 32))
    # rough: use value of paint
    gray = paint.convert("L")
    spec = Image.merge("RGB", (gray, gray, gray))
    spec = ImageEnhance.Contrast(spec).enhance(1.4)
    spec = ImageEnhance.Brightness(spec).enhance(0.55)

    log.info("livery composed in %.2fs", time.perf_counter() - t0)
    return paint.convert("RGBA"), spec


def save_tga(img: Image.Image, path: Path) -> None:
    """iRacing-friendly 32-bit TGA (bottom-up)."""
    rgba = img.convert("RGBA")
    # Pillow TGA save
    rgba.save(path, format="TGA")
    log.info("saved %s (%.0f KB)", path.name, path.stat().st_size / 1024)


def main() -> None:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    log.info("start GR86 carbon-night livery → %s", OUT)

    paint, spec = build_livery()

    png = OUT / "gr86_smarcato42_carbon_night.png"
    tga = OUT / "gr86_smarcato42_carbon_night.tga"
    spec_png = OUT / "gr86_smarcato42_carbon_night_spec.png"
    paint.save(png, "PNG", optimize=True)
    save_tga(paint, tga)
    spec.save(spec_png, "PNG", optimize=True)

    # Side-by-side preview
    tpl = load_template().convert("RGB").resize((640, 640))
    prev = paint.convert("RGB").resize((640, 640))
    sheet = Image.new("RGB", (1320, 700), CARBON)
    sheet.paste(tpl, (20, 40))
    sheet.paste(prev, (680, 40))
    d = ImageDraw.Draw(sheet)
    d.text((20, 10), "Template", fill=ICE_DIM)
    d.text((680, 10), "S.Marcato 42 · carbon night", fill=ICE)
    sheet.save(OUT / "preview_compare.jpg", quality=92)

    readme = OUT / "README.md"
    readme.write_text(
        f"""# GR86 · S.Marcato 42 Racing — Carbon Night

Trading Paints livrea for **Toyota GR86** template `160_template_GR86`.

## Design
- Base: carbon weave night
- Accents: ice / silver parallelogram stripes (−18°, vertical ends)
- Hero: **42** rosso corsa + S.Marcato wordmark
- Monogram on roof / nose

## Files
| File | Use |
|------|-----|
| `gr86_smarcato42_carbon_night.tga` | Main paint (2048×2048) — import into template / Trading Paints |
| `gr86_smarcato42_carbon_night.png` | Same paint as PNG |
| `gr86_smarcato42_carbon_night_spec.png` | Rough specular hint (optional) |
| `preview_compare.jpg` | Template vs livrea |

## How to apply
1. Open `Toyota GR86.psd` in Photoshop (from Trading Paints template zip).
2. Turn off guide layers listed as *Turn Off Before Exporting TGA*.
3. Place `gr86_smarcato42_carbon_night.tga` above **Base Paint** (or replace Base Paint).
4. Keep **Car_Mandatory** / **Mask** / wire guides as required by the template.
5. Export TGA per Trading Paints instructions and upload.

Or upload the TGA directly in Trading Paints custom paint tools if the car supports flat texture upload.

## Regenerate
```powershell
cd C:\\Users\\simot\\Documents\\Projects\\smarcato42-racing
python liveries/generate_gr86_carbon_night.py
```
""",
        encoding="utf-8",
    )

    log.info(
        "done in %.2fs | paint=%s",
        time.perf_counter() - t0,
        png.name,
    )


if __name__ == "__main__":
    main()
