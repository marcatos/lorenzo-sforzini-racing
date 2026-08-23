"""Build S.Marcato 42 Racing Chrome theme and apply to the default profile."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("smarcato42.chrome")

ROOT = Path(__file__).resolve().parents[1]
THEME_DIR = ROOT / "chrome-theme"
IMG_DIR = THEME_DIR / "images"
FONTS = ROOT / "fonts"
FAVICON = ROOT / "brand-identity" / "08-favicon" / "favicon_128.png"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
USER_DATA = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
PREFS = USER_DATA / "Default" / "Preferences"

CARBON = (8, 8, 10)
CARBON_MID = (18, 18, 22)
ICE = (248, 248, 250)
ICE_DIM = (200, 200, 208)
ROSSO = (225, 6, 0)


def sk_color(rgb: tuple[int, int, int]) -> int:
    """Chrome Preferences store SkColor as signed 32-bit ARGB."""
    r, g, b = rgb
    u = (0xFF << 24) | (r << 16) | (g << 8) | b
    return u - 0x100000000 if u >= 0x80000000 else u


def make_solid(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    Image.new("RGB", size, color).save(path, "PNG")


def make_frame(path: Path) -> None:
    w, h = 1920, 80
    img = Image.new("RGB", (w, h), CARBON)
    d = ImageDraw.Draw(img)
    d.rectangle([0, h - 3, w, h], fill=ROSSO)
    img.save(path, "PNG")


def make_toolbar(path: Path) -> None:
    w, h = 1920, 120
    img = Image.new("RGB", (w, h), CARBON_MID)
    d = ImageDraw.Draw(img)
    d.line([(0, h - 1), (w, h - 1)], fill=(40, 40, 48), width=1)
    img.save(path, "PNG")


def make_ntp(path: Path) -> None:
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), CARBON)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    # Soft vignette + bottom brand plate
    for y in range(h):
        if y > int(h * 0.62):
            t = (y - int(h * 0.62)) / (h * 0.38)
            a = int(90 * t)
            od.line([(0, y), (w, y)], fill=(*CARBON_MID, a))
    # Subtle rosso hairline
    od.rectangle([0, 0, 6, h], fill=(*ROSSO, 255))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGBA")

    # Wordmark
    font_path = FONTS / "audiowide.ttf"
    try:
        f_name = ImageFont.truetype(str(font_path), 54)
        f_tag = ImageFont.truetype(str(FONTS / "audiowide.ttf"), 18)
    except OSError:
        f_name = ImageFont.load_default()
        f_tag = f_name

    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cx, cy = w // 2, int(h * 0.72)
    ld.text((cx, cy), "S.Marcato", font=f_name, fill=(*ICE, 220), anchor="mm")
    ld.text((cx, cy + 48), "42", font=f_name, fill=(*ROSSO, 235), anchor="mm")
    ld.text((cx, cy + 92), "RACING", font=f_tag, fill=(*ICE_DIM, 160), anchor="mm")
    # Soften text
    shadow = layer.filter(ImageFilter.GaussianBlur(8))
    img = Image.alpha_composite(img, shadow)
    img = Image.alpha_composite(img, layer)

    if FAVICON.exists():
        icon = Image.open(FAVICON).convert("RGBA").resize((96, 96), Image.Resampling.LANCZOS)
        img.alpha_composite(icon, (cx - 48, int(h * 0.48)))

    img.convert("RGB").save(path, "PNG", optimize=True)


def write_manifest() -> None:
    manifest = {
        "manifest_version": 2,
        "name": "S.Marcato 42 Racing",
        "version": "1.0.0",
        "description": "Carbon / ice / rosso corsa theme for S.Marcato 42 Racing",
        "theme": {
            "images": {
                "theme_frame": "images/frame.png",
                "theme_toolbar": "images/toolbar.png",
                "theme_ntp_background": "images/ntp.png",
                "theme_tab_background": "images/tab.png",
            },
            "colors": {
                "frame": list(CARBON),
                "frame_inactive": list(CARBON_MID),
                "toolbar": list(CARBON_MID),
                "tab_text": list(ICE),
                "tab_background_text": list(ICE_DIM),
                "bookmark_text": list(ICE),
                "ntp_background": list(CARBON),
                "ntp_text": list(ICE),
                "ntp_link": list(ROSSO),
                "ntp_section": list(CARBON_MID),
                "button_background": list(CARBON_MID),
                "omnibox_background": list(CARBON),
                "omnibox_text": list(ICE),
            },
            "tints": {
                "buttons": [0.0, 0.6, 0.55],
                "frame": [-1.0, -1.0, -1.0],
                "background_tab": [-1.0, 0.3, 0.35],
            },
            "properties": {
                "ntp_background_alignment": "bottom",
                "ntp_background_repeat": "no-repeat",
                "ntp_logo_alternate": 1,
            },
        },
    }
    (THEME_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )


def chrome_running() -> bool:
    try:
        out = subprocess.check_output(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/NH"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return "chrome.exe" in out.lower()
    except Exception:
        return False


def stop_chrome() -> None:
    if not chrome_running():
        log.info("Chrome not running")
        return
    log.info("closing Chrome to write theme prefs")
    subprocess.run(["taskkill", "/IM", "chrome.exe", "/F"], capture_output=True)
    for _ in range(40):
        if not chrome_running():
            break
        time.sleep(0.25)
    time.sleep(0.5)


def apply_user_color_theme() -> None:
    """Immediate brand tint via Chrome's built-in 'pick a color' theme (rosso seed + dark)."""
    if not PREFS.exists():
        raise FileNotFoundError(PREFS)
    raw = PREFS.read_text(encoding="utf-8")
    prefs = json.loads(raw)

    rosso_sk = sk_color(ROSSO)
    browser = prefs.setdefault("browser", {})
    theme = browser.setdefault("theme", {})
    # 2 = dark scheme in recent Chromium
    theme["color_scheme"] = 2
    theme["color_variant"] = 1
    theme["user_color"] = rosso_sk

    # Mirror keys used by current Chrome builds
    prefs.setdefault("theme", {})
    prefs["theme"]["color_scheme2"] = 2
    prefs["theme"]["color_variant2"] = 1
    prefs["theme"]["user_color2"] = rosso_sk

    ext = prefs.setdefault("extensions", {})
    ext_theme = ext.setdefault("theme", {})
    # Keep color theme active until full package is loaded
    if ext_theme.get("id") not in (None, "", "user_color_theme_id"):
        log.info("existing theme id=%s (will keep until unpacked theme loaded)", ext_theme.get("id"))
    else:
        ext_theme["id"] = "user_color_theme_id"

    # Enable developer mode so unpacked theme can be loaded
    ui = ext.setdefault("ui", {})
    ui["developer_mode"] = True

    backup = PREFS.with_suffix(".bak-smarcato42")
    shutil.copy2(PREFS, backup)
    PREFS.write_text(json.dumps(prefs, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    log.info("wrote Chrome prefs (backup=%s) user_color=%s", backup.name, rosso_sk)


def write_readme() -> None:
    text = """# S.Marcato 42 Racing — Chrome theme

## Applied automatically
`build_and_apply.py` sets Chrome's dark + Rosso Corsa color theme on the Default profile.

## Full theme package (frame / toolbar / new-tab)
1. Open `chrome://extensions`
2. Enable **Developer mode**
3. **Load unpacked** → select this folder:
   `{theme}`
4. The theme activates immediately.

Or run:
```
"{chrome}" --load-extension="{theme}"
```
(session-only unless also loaded via Extensions UI)

Colors: carbon #08080A · carbon mid #121216 · ice #F8F8FA · rosso #E10600
""".format(
        theme=THEME_DIR, chrome=CHROME
    )
    (THEME_DIR / "README.md").write_text(text, encoding="utf-8")


def main() -> None:
    t0 = time.perf_counter()
    log.info("start Chrome theme build | out=%s", THEME_DIR)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    make_frame(IMG_DIR / "frame.png")
    make_toolbar(IMG_DIR / "toolbar.png")
    make_solid(IMG_DIR / "tab.png", (64, 64), CARBON_MID)
    make_ntp(IMG_DIR / "ntp.png")
    if FAVICON.exists():
        shutil.copy2(FAVICON, THEME_DIR / "icon128.png")
    write_manifest()
    write_readme()
    log.info("theme assets ready")

    stop_chrome()
    apply_user_color_theme()

    if CHROME.exists():
        # Open extensions page so full theme can be loaded in one click if needed
        subprocess.Popen(
            [
                str(CHROME),
                f"--load-extension={THEME_DIR}",
                "chrome://extensions",
                "chrome://settings/manageProfile",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log.info("launched Chrome with theme extension + settings")
    else:
        log.warning("chrome.exe not found at %s", CHROME)

    log.info("done in %.2fs", time.perf_counter() - t0)


if __name__ == "__main__":
    main()
