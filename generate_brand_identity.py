"""Generate complete Lorenzo Sforzini (L.Sforzini 44) brand identity kit."""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

from PIL import Image, ImageDraw

from brand_config import (
    BLACK,
    BRAND_DIR,
    BRAND_KIT,
    BRAND_SHORT,
    CARBON,
    HERO_ACCENT,
    HERO_ACCENT_HEX,
    HERO_ACCENT_KEY,
    HERO_ACCENT_NAME,
    ICE,
    ICE_DIM,
    MARK_DIR,
    MARK_STEM,
    MONOGRAM_DIR,
    MONOGRAM_STEM,
    PALETTE,
    RACE_NUMBER,
    SILVER,
    WHITE,
    WORDMARK_STEM,
)
from brand_render import (
    font,
    horizontal_lockup,
    recolor_opaque,
    render_monogram,
    render_race_number,
    render_tagline,
    render_wordmark,
    stack_vertical,
    trim,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("brandkit")

BRAND = BRAND_DIR


def fit_on_canvas(
    mark: Image.Image,
    size: tuple[int, int],
    bg: tuple[int, int, int] | None,
    scale: float = 0.72,
) -> Image.Image:
    tw, th = size
    if bg is None:
        canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    else:
        canvas = Image.new("RGBA", (tw, th), (*bg, 255))
    ratio = min((tw * scale) / mark.width, (th * scale) / mark.height)
    resized = mark.resize(
        (max(1, int(mark.width * ratio)), max(1, int(mark.height * ratio))),
        Image.Resampling.LANCZOS,
    )
    x = (tw - resized.width) // 2
    y = (th - resized.height) // 2
    canvas.alpha_composite(resized, (x, y))
    return canvas


def save_variants(mark: Image.Image, folder: Path, stem: str, sizes: list[int] | None = None) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    master = trim(mark, pad=16)
    master.save(folder / f"{stem}_transparent.png")
    for label, bg, fg in (
        ("on_carbon", CARBON, None),
        ("on_white", WHITE, BLACK),
        ("on_ice", ICE, BLACK),
    ):
        colored = master if fg is None else recolor_opaque(master, fg)
        canvas = fit_on_canvas(colored, (2048, 2048), bg, scale=0.7)
        canvas.convert("RGB").save(folder / f"{stem}_{label}.png", "PNG", optimize=True)
    recolor_opaque(master, WHITE).save(folder / f"{stem}_mono_white.png")
    recolor_opaque(master, BLACK).save(folder / f"{stem}_mono_black.png")
    if sizes:
        for s in sizes:
            fitted = fit_on_canvas(master, (s, s), None, scale=0.78)
            fitted.save(folder / f"{stem}_{s}.png")


def clearspace_sheet(mark: Image.Image, out: Path) -> None:
    mark = trim(mark)
    unit = max(24, mark.height // 8)
    pad = unit
    w, h = mark.width + pad * 2, mark.height + pad * 2
    canvas = Image.new("RGBA", (w + 120, h + 160), (*CARBON, 255))
    box = Image.new("RGBA", (w, h), (40, 40, 48, 255))
    bd = ImageDraw.Draw(box)
    bd.rectangle([0, 0, w - 1, h - 1], outline=(*ICE_DIM, 255), width=2)
    for x0, y0 in ((0, 0), (w - unit, 0), (0, h - unit), (w - unit, h - unit)):
        bd.rectangle([x0, y0, x0 + unit - 1, y0 + unit - 1], outline=(*SILVER, 180), width=1)
        bd.line([(x0 + 4, y0 + unit // 2), (x0 + unit - 4, y0 + unit // 2)], fill=(*SILVER, 200), width=1)
    canvas.alpha_composite(box, (60, 80))
    canvas.alpha_composite(mark, (60 + pad, 80 + pad))
    ImageDraw.Draw(canvas).text((60, 24), "CLEAR SPACE = height/8", fill=ICE_DIM)
    canvas.convert("RGB").save(out, "PNG", optimize=True)


def color_palette_sheet(out: Path) -> None:
    canvas = Image.new("RGB", (1600, 900), CARBON)
    d = ImageDraw.Draw(canvas)
    title_f = font(["audiowide.ttf"], 48)
    label_f = font(["Candaral.ttf", "segoeuil.ttf"], 28)
    d.text((80, 60), f"{BRAND_SHORT} {RACE_NUMBER} — Color System", font=title_f, fill=ICE)
    swatches = [
        ("Carbon", "carbon", "Primary background"),
        ("Carbon Mid", "carbon_mid", "Panels / surfaces"),
        ("Ice White", "ice", "Primary logo"),
        ("Ice Dim", "ice_dim", "Secondary type"),
        ("Silver", "silver", "Rules / meta"),
        ("Electric Blue", "electric_blue", "Hero accent / number"),
        ("Black", "black", "Print mono"),
        ("White", "white", "Light grounds"),
    ]
    x, y = 80, 180
    for i, (name, key, use) in enumerate(swatches):
        hex_v, rgb = PALETTE[key]
        d.rounded_rectangle([x, y, x + 200, y + 200], radius=12, fill=rgb, outline=ICE_DIM, width=1)
        label_col = ICE if sum(rgb) < 400 else CARBON
        d.text((x + 16, y + 150), hex_v, font=label_f, fill=label_col)
        d.text((x, y + 220), name, font=label_f, fill=ICE)
        d.text((x, y + 255), use, font=font(["Candaral.ttf", "segoeuil.ttf"], 22), fill=ICE_DIM)
        x += 220
        if i == 3:
            x, y = 80, 520
    canvas.save(out, "PNG", optimize=True)


def typography_sheet(out: Path) -> None:
    canvas = Image.new("RGB", (1600, 1000), CARBON)
    d = ImageDraw.Draw(canvas)
    d.text((80, 50), "Typography", font=font(["audiowide.ttf"], 52), fill=ICE)
    rows = [
        ("Display / Name", "Audiowide Italic (shear)", BRAND_SHORT),
        ("Hero Number", "Audiowide italic racing", RACE_NUMBER),
        ("Tagline", "Candara Light / tracked", "Racing"),
        ("UI / Body", "Segoe UI / system sans", "Endurance · Prototype · GT"),
    ]
    y = 160
    for title, meta, sample in rows:
        d.text((80, y), title, font=font(["Candaral.ttf"], 26), fill=SILVER)
        d.text((80, y + 36), meta, font=font(["Candaral.ttf"], 22), fill=ICE_DIM)
        if sample == BRAND_SHORT:
            mark = render_wordmark(72)
            canvas.paste(Image.new("RGB", mark.size, CARBON), (80, y + 80))
            tmp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            tmp.alpha_composite(mark, (80, y + 80))
            canvas = Image.alpha_composite(canvas.convert("RGBA"), tmp).convert("RGB")
            d = ImageDraw.Draw(canvas)
            y += 220
        elif sample == RACE_NUMBER:
            mark = render_race_number(120, HERO_ACCENT)
            tmp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            tmp.alpha_composite(mark, (80, y + 70))
            canvas = Image.alpha_composite(canvas.convert("RGBA"), tmp).convert("RGB")
            d = ImageDraw.Draw(canvas)
            y += 260
        else:
            d.text((80, y + 70), sample, font=font(["Candaral.ttf"], 44), fill=ICE)
            y += 160
    canvas.save(out, "PNG", optimize=True)


def write_guidelines_html(
    primary_rel: str,
    horizontal_rel: str,
    mark_rel: str,
    mono_rel: str,
) -> None:
    path = BRAND / "index.html"
    if path.exists() and 'id="top-nav"' in path.read_text(encoding="utf-8"):
        text = path.read_text(encoding="utf-8")
        replacements = [
            (r'src="01-primary-stacked/[^"]+"', f'src="{primary_rel}"'),
            (r'src="02-horizontal/[^"]+"', f'src="{horizontal_rel}"'),
            (r'src="03-mark-44/[^"]+"', f'src="{mark_rel}"'),
            (r'src="06-monogram-ls/[^"]+"', f'src="{mono_rel}"'),
        ]
        for pattern, repl in replacements:
            text = re.sub(pattern, repl, text, count=1)
        path.write_text(text, encoding="utf-8")
        log.info("guidelines html nav preserved + image refs refreshed")
        return
    log.warning("index.html nav not found — skipping html refresh")


def main() -> None:
    t0 = time.perf_counter()
    BRAND.mkdir(parents=True, exist_ok=True)
    log.info("building brand identity kit → %s", BRAND)

    name_ice = render_wordmark(160, ICE)
    mark_num = render_race_number(280, HERO_ACCENT)
    mark_ice = render_race_number(280, ICE)
    racing = render_tagline(42, ICE_DIM)

    target_h = 420
    ratio = target_h / mark_num.height
    mark_s = mark_num.resize((int(mark_num.width * ratio), target_h), Image.Resampling.LANCZOS)
    racing_s = racing.resize(
        (
            int(racing.width * (mark_s.width / max(1, racing.width)) * 0.92),
            int(racing.height * (mark_s.width / max(1, racing.width)) * 0.92),
        ),
        Image.Resampling.LANCZOS,
    )

    primary = stack_vertical([name_ice, mark_s, racing_s], gaps=[28, 22], hairline=True, hairline_color=ICE)
    log.info("primary stacked ready")

    name_h = render_wordmark(96, ICE)
    mark_h = mark_num.resize((int(mark_num.width * 0.55), int(mark_num.height * 0.55)), Image.Resampling.LANCZOS)
    racing_h = racing.resize((int(racing.width * 0.7), int(racing.height * 0.7)), Image.Resampling.LANCZOS)
    horizontal = horizontal_lockup(name_h, mark_h, racing_h, gap=40)
    log.info("horizontal lockup ready")

    monogram = render_monogram(280, ICE)
    log.info("monogram ready")

    save_variants(primary, BRAND / "01-primary-stacked", "primary_stacked", sizes=[512, 1024])
    fit_on_canvas(primary, (2400, 2400), CARBON, 0.75).convert("RGB").save(
        BRAND / "01-primary-stacked" / "primary_stacked_master_2048_carbon.png"
    )

    save_variants(horizontal, BRAND / "02-horizontal", "horizontal")
    for bg, tag, fg_mark in ((CARBON, "carbon", horizontal), (WHITE, "white", recolor_opaque(horizontal, BLACK))):
        banner = fit_on_canvas(fg_mark, (2400, 900), bg, scale=0.7)
        banner.convert("RGB").save(BRAND / "02-horizontal" / f"horizontal_banner_{tag}.png")

    save_variants(mark_num, BRAND / MARK_DIR, MARK_STEM, sizes=[64, 128, 256, 512])
    save_variants(mark_ice, BRAND / MARK_DIR, f"{MARK_STEM}_ice", sizes=[])
    save_variants(name_ice, BRAND / "04-wordmark", WORDMARK_STEM, sizes=[256, 512])
    save_variants(racing, BRAND / "05-tag-racing", "tag_racing", sizes=[256])
    save_variants(monogram, BRAND / MONOGRAM_DIR, MONOGRAM_STEM, sizes=[64, 128, 256, 512, 1024])

    social = BRAND / "07-social"
    social.mkdir(parents=True, exist_ok=True)
    fit_on_canvas(monogram, (1024, 1024), CARBON, 0.7).convert("RGB").save(social / "avatar_1024_carbon.png")
    fit_on_canvas(recolor_opaque(monogram, BLACK), (1024, 1024), ICE, 0.7).convert("RGB").save(social / "avatar_1024_ice.png")
    sq = fit_on_canvas(monogram, (1024, 1024), CARBON, 0.62)
    mask = Image.new("L", (1024, 1024), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, 1023, 1023], fill=255)
    circ = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    circ.paste(sq, (0, 0))
    circ.putalpha(mask)
    circ.save(social / "avatar_circle_1024.png")
    fit_on_canvas(primary, (1080, 1920), CARBON, 0.55).convert("RGB").save(social / "story_1080x1920.png")
    fit_on_canvas(horizontal, (1500, 500), CARBON, 0.75).convert("RGB").save(social / "cover_1500x500.png")
    fit_on_canvas(horizontal, (1920, 1080), CARBON, 0.55).convert("RGB").save(social / "youtube_1920x1080.png")
    fit_on_canvas(primary, (1200, 630), CARBON, 0.7).convert("RGB").save(social / "og_1200x630.png")
    log.info("social assets saved")

    fav = BRAND / "08-favicon"
    fav.mkdir(parents=True, exist_ok=True)
    for s in (16, 32, 48, 64, 128, 180, 192, 256, 512):
        fit_on_canvas(monogram, (s, s), CARBON, 0.78).convert("RGB").save(fav / f"favicon_{s}.png")
    fit_on_canvas(monogram, (180, 180), CARBON, 0.72).convert("RGB").save(fav / "apple-touch-icon.png")

    app = BRAND / "09-app-icons"
    app.mkdir(parents=True, exist_ok=True)
    for s in (1024, 512, 256):
        fit_on_canvas(monogram, (s, s), CARBON, 0.68).convert("RGB").save(app / f"app_icon_{s}.png")
        icon = fit_on_canvas(monogram, (s, s), CARBON, 0.68)
        mask = Image.new("L", (s, s), 0)
        rad = s // 4
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=rad, fill=255)
        rounded = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        rounded.paste(icon, (0, 0))
        rounded.putalpha(mask)
        rounded.save(app / f"app_icon_rounded_{s}.png")

    cs = BRAND / "10-clearspace"
    cs.mkdir(parents=True, exist_ok=True)
    clearspace_sheet(primary, cs / "clearspace_primary.png")
    clearspace_sheet(monogram, cs / "clearspace_monogram.png")

    (BRAND / "11-palette").mkdir(parents=True, exist_ok=True)
    (BRAND / "12-typography").mkdir(parents=True, exist_ok=True)
    color_palette_sheet(BRAND / "11-palette" / "color_system.png")
    typography_sheet(BRAND / "12-typography" / "type_system.png")

    tokens = {
        "brand": BRAND_KIT,
        "driver": "Lorenzo Sforzini",
        "wordmark": BRAND_SHORT,
        "race_number": RACE_NUMBER,
        "hero_accent": {
            "key": HERO_ACCENT_KEY,
            "hex": HERO_ACCENT_HEX,
            "name": HERO_ACCENT_NAME,
        },
        "colors": {k: v[0] for k, v in PALETTE.items()},
        "typography": {
            "display_name": "Audiowide + italic shear 0.36",
            "hero_number": f"Audiowide italic {RACE_NUMBER}",
            "tagline": "Candara Light tracked — Racing",
            "ui": "Segoe UI / system sans",
        },
        "clearspace": "1/8 of logo height",
        "minimum_sizes_px": {"stacked_height": 120, "mark_44": 32, "favicon": 16},
    }
    (BRAND / "brand-tokens.json").write_text(json.dumps(tokens, indent=2), encoding="utf-8")

    write_guidelines_html(
        primary_rel="01-primary-stacked/primary_stacked_on_carbon.png",
        horizontal_rel="02-horizontal/horizontal_on_carbon.png",
        mark_rel=f"{MARK_DIR}/{MARK_STEM}_on_carbon.png",
        mono_rel=f"{MONOGRAM_DIR}/{MONOGRAM_STEM}_on_carbon.png",
    )

    files = sorted(p for p in BRAND.rglob("*") if p.is_file())
    elapsed = time.perf_counter() - t0
    log.info("brand kit complete: %d files in %.2fs → %s", len(files), elapsed, BRAND)


if __name__ == "__main__":
    main()
