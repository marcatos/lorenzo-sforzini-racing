"""L.Sforzini 44 Racing — Sticker Mule print pack (300 DPI, transparent PNG)."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from PIL import Image, ImageDraw

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from brand_config import BRAND_KIT, HERO_ACCENT, ICE, ICE_DIM, MARK_DIR, MARK_STEM, MONOGRAM_DIR, MONOGRAM_STEM, WORDMARK_STEM
from brand_render import horizontal_lockup, render_monogram, render_race_number, render_tagline, render_wordmark, stack_vertical, trim

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("stickermule")

ROOT = Path(__file__).resolve().parents[2]
BRAND = ROOT / "brand-identity"
OUT = Path(__file__).resolve().parent

DPI = 300
INCH = 3.0
PX = int(INCH * DPI)
PAD = int(0.12 * DPI)


def fit_in_box(img: Image.Image, max_side: int) -> Image.Image:
    ratio = min(max_side / img.width, max_side / img.height)
    return img.resize((max(1, int(img.width * ratio)), max(1, int(img.height * ratio))), Image.Resampling.LANCZOS)


def build_diecut_tight(mark: Image.Image, max_side: int = PX - PAD * 2) -> Image.Image:
    fitted = fit_in_box(trim(mark), max_side)
    canvas = Image.new("RGBA", (PX, PX), (0, 0, 0, 0))
    canvas.alpha_composite(fitted, ((PX - fitted.width) // 2, (PX - fitted.height) // 2))
    return canvas


def save_png(img: Image.Image, name: str) -> Path:
    path = OUT / name
    img.save(path, "PNG", optimize=True)
    log.info("saved %s", name)
    return path


def main() -> None:
    t0 = time.perf_counter()
    OUT.mkdir(parents=True, exist_ok=True)
    mark = render_race_number(280, HERO_ACCENT)
    monogram = render_monogram(220, ICE)
    word = render_wordmark(72, ICE)
    tag = render_tagline(28, ICE_DIM)
    mark_s = mark.resize((int(mark.width * 1.2), int(mark.height * 1.2)), Image.Resampling.LANCZOS)
    primary = stack_vertical([word, mark_s, tag], gaps=[24, 18], hairline=True)
    horizontal = horizontal_lockup(render_wordmark(56, ICE), fit_in_box(mark, 180), render_tagline(22, ICE_DIM), gap=28)

    outputs = [
        save_png(build_diecut_tight(mark), "sticker_diecut_44_3in.png"),
        save_png(build_diecut_tight(monogram), "sticker_diecut_monogram_3in.png"),
        save_png(build_diecut_tight(primary), "sticker_diecut_primary_3in.png"),
        save_png(build_diecut_tight(horizontal, PX - PAD), "sticker_diecut_horizontal_3in.png"),
        save_png(build_diecut_tight(mark, int(2 * DPI)), "sticker_diecut_44_2in.png"),
    ]

    (OUT / "README.md").write_text(
        f"""# Sticker Mule pack — {BRAND_KIT}

| File | Use |
|------|-----|
| `sticker_diecut_44_3in.png` | Die Cut ~3\" — Electric Blue 44 |
| `sticker_diecut_44_2in.png` | Die Cut ~2\" |
| `sticker_diecut_monogram_3in.png` | LS monogram |
| `sticker_diecut_primary_3in.png` | Stacked lockup |
| `sticker_diecut_horizontal_3in.png` | Horizontal lockup |

Generated in {time.perf_counter() - t0:.1f}s.
""",
        encoding="utf-8",
    )
    log.info("stickermule pack done: %d files in %.2fs", len(outputs), time.perf_counter() - t0)


if __name__ == "__main__":
    main()
