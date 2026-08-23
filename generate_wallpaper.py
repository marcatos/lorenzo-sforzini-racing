"""Generate S.Marcato 42 Racing spanning wallpaper (7680x1440) — ice white on carbon black."""

from __future__ import annotations

import logging
import math
import random
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("smarcato42")

WIDTH, HEIGHT = 7680, 1440
PANEL = 2560
OUT = Path(__file__).resolve().parent / "smarcato42_racing_span_7680x1440.png"

BG = (8, 8, 10)
BG_MID = (18, 18, 22)
ACCENT = (245, 245, 248)  # ice white
ACCENT_DIM = (160, 160, 168)
ACCENT_FAINT = (70, 70, 78)
LINE = (230, 230, 235)


def font(path_candidates: list[str], size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for p in path_candidates:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def fonts() -> dict[str, ImageFont.ImageFont]:
    win = Path(r"C:\Windows\Fonts")
    agency = [
        str(win / "AGENCYB.TTF"),
        str(win / "AGENCYR.TTF"),
    ]
    bahn = [
        str(win / "bahnschrift.ttf"),
    ]
    segoe_black = [str(win / "seguibl.ttf")]
    return {
        "number": font(agency + segoe_black + bahn, 560),
        "name": font(agency + bahn, 120),
        "racing": font(bahn + agency, 42),
        "side": font(agency + bahn, 72),
        "micro": font(bahn + agency, 28),
    }


def draw_carbon_noise(img: Image.Image, strength: int = 12) -> None:
    rng = random.Random(42)
    px = img.load()
    w, h = img.size
    step = 3
    for y in range(0, h, step):
        for x in range(0, w, step):
            n = rng.randint(-strength, strength)
            r, g, b = px[x, y]
            px[x, y] = (
                max(0, min(255, r + n)),
                max(0, min(255, g + n)),
                max(0, min(255, b + n)),
            )


def vignette(img: Image.Image, intensity: float = 0.55) -> Image.Image:
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    # soft radial darkening toward edges
    for i in range(40):
        t = i / 39
        alpha = int(255 * (t**1.6) * intensity)
        inset_x = int(w * 0.02 * t)
        inset_y = int(h * 0.08 * t)
        md.ellipse(
            [inset_x, inset_y, w - inset_x, h - inset_y],
            fill=255 - alpha,
        )
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(img, dark, mask.filter(ImageFilter.GaussianBlur(80)))


def draw_speed_lines(draw: ImageDraw.ImageDraw, x0: int, x1: int) -> None:
    rng = random.Random(7)
    for i in range(18):
        y = 80 + i * 72 + rng.randint(-20, 20)
        length = rng.randint(400, 1400)
        x = rng.randint(x0 + 40, max(x0 + 60, x1 - length - 40))
        thick = 1 if i % 3 else 2
        alpha_col = ACCENT_FAINT if i % 2 else ACCENT_DIM
        # diagonal slash
        draw.line([(x, y), (x + length, y - 28)], fill=alpha_col, width=thick)


def draw_chevron_marks(draw: ImageDraw.ImageDraw, cx: int, cy: int, scale: float = 1.0) -> None:
    s = int(90 * scale)
    for i in range(5):
        ox = cx + i * int(55 * scale)
        fade = ACCENT if i < 2 else (ACCENT_DIM if i < 4 else ACCENT_FAINT)
        pts = [
            (ox, cy - s),
            (ox + int(38 * scale), cy),
            (ox, cy + s),
            (ox - int(14 * scale), cy + s),
            (ox + int(24 * scale), cy),
            (ox - int(14 * scale), cy - s),
        ]
        draw.polygon(pts, fill=fade)


def draw_arc_track(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    for width, col in ((18, ACCENT_FAINT), (3, ACCENT_DIM), (1, ACCENT)):
        bbox = [cx - r, cy - r, cx + r, cy + r]
        draw.arc(bbox, start=200, end=340, fill=col, width=width)


def text_center(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], fnt, fill) -> tuple[int, int, int, int]:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = xy[0] - tw // 2, xy[1] - th // 2
    draw.text((x, y), text, font=fnt, fill=fill)
    return (x, y, x + tw, y + th)


def main() -> None:
    t0 = time.perf_counter()
    log.info("start generating %sx%s wallpaper", WIDTH, HEIGHT)

    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(img)

    # horizontal gradient bands (subtle asphalt depth)
    log.info("painting base gradient")
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        # slight vertical gradient + center lift
        shade = int(BG[0] + (BG_MID[0] - BG[0]) * (0.35 + 0.45 * math.sin(math.pi * t)))
        draw.line([(0, y), (WIDTH, y)], fill=(shade, shade, shade + 2))

    # soft center glow behind logo
    glow = Image.new("RGB", (WIDTH, HEIGHT), BG)
    gd = ImageDraw.Draw(glow)
    for i in range(30, 0, -1):
        rad_x = 900 + i * 40
        rad_y = 320 + i * 18
        val = 8 + int(14 * (1 - i / 30))
        gd.ellipse(
            [WIDTH // 2 - rad_x, HEIGHT // 2 - rad_y, WIDTH // 2 + rad_x, HEIGHT // 2 + rad_y],
            fill=(val, val, val + 2),
        )
    img = Image.blend(img, glow, 0.55)
    draw = ImageDraw.Draw(img)

    log.info("drawing racing geometry")
    # LEFT panel atmosphere
    draw_arc_track(draw, PANEL // 2 - 200, HEIGHT // 2 + 80, 980)
    draw_arc_track(draw, PANEL // 2 - 200, HEIGHT // 2 + 80, 860)
    draw_speed_lines(draw, 0, PANEL)
    draw_chevron_marks(draw, 380, HEIGHT // 2, 1.15)

    # thin horizon rule across all panels
    draw.line([(120, HEIGHT // 2), (WIDTH - 120, HEIGHT // 2)], fill=ACCENT_FAINT, width=1)

    # RIGHT panel atmosphere (mirrored feel)
    draw_arc_track(draw, WIDTH - PANEL // 2 + 220, HEIGHT // 2 + 80, 980)
    draw_arc_track(draw, WIDTH - PANEL // 2 + 220, HEIGHT // 2 + 80, 860)
    draw_speed_lines(draw, PANEL * 2, WIDTH)
    # reverse chevrons on right
    for i in range(5):
        ox = WIDTH - 380 - i * 55
        cy = HEIGHT // 2
        s = 90
        fade = ACCENT if i < 2 else (ACCENT_DIM if i < 4 else ACCENT_FAINT)
        pts = [
            (ox, cy - s),
            (ox - 38, cy),
            (ox, cy + s),
            (ox + 14, cy + s),
            (ox - 24, cy),
            (ox + 14, cy - s),
        ]
        draw.polygon(pts, fill=fade)

    # panel separators — hairline white (subtle bezel awareness)
    for x in (PANEL, PANEL * 2):
        draw.line([(x, 60), (x, HEIGHT - 60)], fill=ACCENT_FAINT, width=1)

    f = fonts()
    cx = WIDTH // 2
    cy = HEIGHT // 2

    log.info("composing center logo S.MARCATO 42 RACING")

    # thin frame around logo zone
    frame_w, frame_h = 1180, 860
    fx0, fy0 = cx - frame_w // 2, cy - frame_h // 2 - 20
    for inset, col, w in (
        (0, ACCENT_FAINT, 1),
        (18, ACCENT_FAINT, 1),
    ):
        draw.rectangle(
            [fx0 + inset, fy0 + inset, fx0 + frame_w - inset, fy0 + frame_h - inset],
            outline=col,
            width=w,
        )
    # corner ticks
    tick = 36
    corners = [
        (fx0, fy0),
        (fx0 + frame_w, fy0),
        (fx0, fy0 + frame_h),
        (fx0 + frame_w, fy0 + frame_h),
    ]
    for x, y in corners:
        sx = 1 if x == fx0 else -1
        sy = 1 if y == fy0 else -1
        draw.line([(x, y), (x + sx * tick, y)], fill=ACCENT, width=2)
        draw.line([(x, y), (x, y + sy * tick)], fill=ACCENT, width=2)

    # name
    text_center(draw, "S.MARCATO", (cx, cy - 280), f["name"], ACCENT)

    # hairline under name
    draw.line([(cx - 220, cy - 210), (cx + 220, cy - 210)], fill=ACCENT, width=2)

    # huge number — measure real bounds so RACING never collides
    num_box = text_center(draw, "42", (cx, cy + 20), f["number"], ACCENT)

    # RACING wordmark — clear gap under the number
    racing_y = num_box[3] + 48
    text_center(draw, "RACING", (cx, racing_y), f["racing"], ACCENT_DIM)
    draw.line([(cx - 90, racing_y + 30), (cx + 90, racing_y + 30)], fill=ACCENT_FAINT, width=1)

    # micro labels on side panels
    text_center(draw, "GT", (PANEL // 2, 120), f["side"], ACCENT_DIM)
    text_center(draw, "ENDURANCE", (PANEL // 2, HEIGHT - 110), f["micro"], ACCENT_FAINT)
    text_center(draw, "SM", (WIDTH - PANEL // 2, 120), f["side"], ACCENT_DIM)
    text_center(draw, "PROTOTYPE", (WIDTH - PANEL // 2, HEIGHT - 110), f["micro"], ACCENT_FAINT)

    log.info("applying grain + vignette")
    draw_carbon_noise(img, strength=10)
    img = vignette(img, intensity=0.5)

    # re-draw center logo crisp on top of grain (cleaner brand mark)
    draw = ImageDraw.Draw(img)
    text_center(draw, "S.MARCATO", (cx, cy - 280), f["name"], ACCENT)
    draw.line([(cx - 220, cy - 210), (cx + 220, cy - 210)], fill=ACCENT, width=2)
    num_box = text_center(draw, "42", (cx, cy + 20), f["number"], ACCENT)
    racing_y = num_box[3] + 48
    text_center(draw, "RACING", (cx, racing_y), f["racing"], ACCENT_DIM)

    log.info("saving %s", OUT)
    img.save(OUT, "PNG", optimize=True)
    # also export per-panel crops for reference
    for i in range(3):
        crop = img.crop((i * PANEL, 0, (i + 1) * PANEL, HEIGHT))
        panel_path = OUT.parent / f"smarcato42_panel_{i + 1}_2560x1440.png"
        crop.save(panel_path, "PNG", optimize=True)
        log.info("saved panel %s -> %s", i + 1, panel_path.name)

    elapsed = time.perf_counter() - t0
    log.info("done in %.2fs | output=%s | size=%s bytes", elapsed, OUT, OUT.stat().st_size)


if __name__ == "__main__":
    main()
