"""Generate racing-color logo variants for L.Sforzini 44 brand kit."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

from PIL import Image, ImageDraw

from brand_config import (
    BRAND_KIT,
    BRAND_SHORT,
    CARBON,
    HERO_ACCENT,
    HERO_ACCENT_KEY,
    ICE,
    ICE_DIM,
    MARK_DIR,
    MARK_STEM,
    MONOGRAM_DIR,
    MONOGRAM_STEM,
    RACING_COLORS,
    WHITE,
    WORDMARK_STEM,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("racing-colors")

ROOT = Path(__file__).resolve().parent / "brand-identity"
OUT = ROOT / "13-racing-colors"

MASTERS = {
    "primary": ROOT / "01-primary-stacked" / "primary_stacked_transparent.png",
    "horizontal": ROOT / "02-horizontal" / "horizontal_transparent.png",
    "mark44": ROOT / MARK_DIR / f"{MARK_STEM}_transparent.png",
    "wordmark": ROOT / "04-wordmark" / f"{WORDMARK_STEM}_transparent.png",
    "tag_racing": ROOT / "05-tag-racing" / "tag_racing_transparent.png",
    "monogram": ROOT / MONOGRAM_DIR / f"{MONOGRAM_STEM}_transparent.png",
}


def recolor(img: Image.Image, rgb: tuple[int, int, int]) -> Image.Image:
    img = img.convert("RGBA")
    r, g, b = rgb
    out = []
    for pr, pg, pb, pa in img.getdata():
        if pa < 8:
            out.append((0, 0, 0, 0))
        else:
            out.append((r, g, b, pa))
    img.putdata(out)
    return img


def fit_on(mark: Image.Image, size: tuple[int, int], bg: tuple[int, int, int], scale: float = 0.72) -> Image.Image:
    tw, th = size
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


def palette_sheet(path: Path) -> None:
    canvas = Image.new("RGB", (1800, 720), CARBON)
    d = ImageDraw.Draw(canvas)
    try:
        from PIL import ImageFont

        title = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 42)
        label = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 24)
        small = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 18)
    except OSError:
        title = label = small = ImageFont.load_default()
    d.text((64, 48), f"{BRAND_SHORT} 44 — Racing Color System", font=title, fill=(248, 248, 250))
    x, y = 64, 140
    for key, meta in RACING_COLORS.items():
        d.rounded_rectangle([x, y, x + 260, y + 200], radius=14, fill=meta["rgb"])
        lum = 0.2126 * meta["rgb"][0] + 0.7152 * meta["rgb"][1] + 0.0722 * meta["rgb"][2]
        tcol = (8, 8, 10) if lum > 140 else (248, 248, 250)
        d.text((x + 18, y + 140), meta["hex"], font=label, fill=tcol)
        d.text((x, y + 220), meta["name"], font=label, fill=(248, 248, 250))
        d.text((x, y + 252), meta["use"], font=small, fill=(168, 168, 176))
        x += 286
    canvas.save(path, "PNG", optimize=True)


def main() -> None:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    log.info("generating racing color variants → %s", OUT)

    palette_sheet(OUT / "racing_color_system.png")

    for color_key, meta in RACING_COLORS.items():
        cdir = OUT / color_key
        cdir.mkdir(parents=True, exist_ok=True)
        rgb = meta["rgb"]
        log.info("colorway %s %s", color_key, meta["hex"])

        for stem, master in MASTERS.items():
            if not master.exists():
                log.warning("missing master %s", master)
                continue
            base = Image.open(master)
            colored = recolor(base, rgb)
            colored.save(cdir / f"{stem}_{color_key}_transparent.png")
            fit_on(colored, (2048, 2048), CARBON, 0.7 if stem != "horizontal" else 0.78).convert("RGB").save(
                cdir / f"{stem}_{color_key}_on_carbon.png"
            )
            fit_on(colored, (2048, 2048), WHITE, 0.7 if stem != "horizontal" else 0.78).convert("RGB").save(
                cdir / f"{stem}_{color_key}_on_white.png"
            )

        h = Image.open(MASTERS["horizontal"])
        hcol = recolor(h, rgb)
        fit_on(hcol, (2400, 900), CARBON, 0.72).convert("RGB").save(cdir / f"banner_{color_key}_carbon.png")
        fit_on(hcol, (2400, 900), WHITE, 0.72).convert("RGB").save(cdir / f"banner_{color_key}_white.png")

        word = recolor(Image.open(MASTERS["wordmark"]), ICE)
        mark = recolor(Image.open(MASTERS["mark44"]), rgb)
        tag = recolor(Image.open(MASTERS["tag_racing"]), ICE_DIM)
        gap = 36
        mark = mark.resize((int(mark.width * 1.35), int(mark.height * 1.35)), Image.Resampling.LANCZOS)
        max_w = max(p.width for p in (word, mark, tag))
        total_h = word.height + mark.height + tag.height + gap * 2
        stack = Image.new("RGBA", (max_w + 80, total_h + 80), (0, 0, 0, 0))
        y = 40
        for i, part in enumerate((word, mark, tag)):
            x = 40 + (max_w - part.width) // 2
            stack.alpha_composite(part, (x, y))
            y += part.height + (gap if i < 2 else 0)
        fit_on(stack, (2048, 2048), CARBON, 0.72).convert("RGB").save(
            cdir / f"primary_ice_plus_{color_key}_on_carbon.png"
        )

    tokens_path = ROOT / "brand-tokens.json"
    tokens = {}
    if tokens_path.exists():
        tokens = json.loads(tokens_path.read_text(encoding="utf-8"))
    tokens["racing_colors"] = {k: {"hex": v["hex"], "name": v["name"], "use": v["use"]} for k, v in RACING_COLORS.items()}
    tokens["hero_accent"] = {
        "key": HERO_ACCENT_KEY,
        "hex": RACING_COLORS[HERO_ACCENT_KEY]["hex"],
        "name": RACING_COLORS[HERO_ACCENT_KEY]["name"],
    }
    tokens_path.write_text(json.dumps(tokens, indent=2), encoding="utf-8")

    n = len(list(OUT.rglob("*.png")))
    log.info("done in %.2fs | %d png in %s", time.perf_counter() - t0, n, OUT)


if __name__ == "__main__":
    main()
