"""Install S.Marcato 42 Chrome theme permanently on a profile (Default = marcato.simone@gmail.com)."""

from __future__ import annotations

import hashlib
import json
import logging
import shutil
import subprocess
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("smarcato42.chrome.apply")

THEME_DIR = Path(__file__).resolve().parent
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
USER_DATA = Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "User Data"
# marcato.simone@gmail.com → Default (from Local State info_cache)
PROFILE_DIR = "Default"
ROSSO = (225, 6, 0)


def extension_id_from_path(path: Path) -> str:
    abs_path = str(path.resolve())
    digest = hashlib.sha256(abs_path.encode("utf-16le")).hexdigest()[:32]
    return digest.translate(str.maketrans("0123456789abcdef", "abcdefghijklmnop"))


def sk_color(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    u = (0xFF << 24) | (r << 16) | (g << 8) | b
    return u - 0x100000000 if u >= 0x80000000 else u


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
        return
    log.info("closing Chrome")
    subprocess.run(["taskkill", "/IM", "chrome.exe", "/F"], capture_output=True)
    for _ in range(50):
        if not chrome_running():
            break
        time.sleep(0.2)
    time.sleep(0.8)


def chrome_install_time() -> str:
    # Chrome stores install_time as microseconds since Windows FILETIME epoch
    # Approx: now as Chrome-compatible decimal string
    # FILETIME epoch: 1601-01-01; Unix epoch offset 11644473600 seconds
    now = time.time()
    ft = int((now + 11644473600) * 10_000_000)
    return str(ft)


def apply(profile_dir: str = PROFILE_DIR) -> str:
    prefs_path = USER_DATA / profile_dir / "Preferences"
    if not prefs_path.exists():
        raise FileNotFoundError(prefs_path)

    manifest_path = THEME_DIR / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    ext_id = extension_id_from_path(THEME_DIR)
    theme_path = str(THEME_DIR.resolve())
    log.info("profile=%s theme_id=%s path=%s", profile_dir, ext_id, theme_path)

    prefs = json.loads(prefs_path.read_text(encoding="utf-8"))
    backup = prefs_path.with_suffix(".bak-smarcato42-theme")
    shutil.copy2(prefs_path, backup)
    log.info("backup=%s", backup)

    settings = prefs.setdefault("extensions", {}).setdefault("settings", {})
    settings[ext_id] = {
        "active_permissions": {
            "api": [],
            "explicit_host": [],
            "manifest_permissions": [],
            "scriptable_host": [],
        },
        "commands": {},
        "content_settings": [],
        "creation_flags": 1,
        "from_webstore": False,
        "granted_permissions": {
            "api": [],
            "explicit_host": [],
            "manifest_permissions": [],
            "scriptable_host": [],
        },
        "install_time": chrome_install_time(),
        "location": 4,  # UNPACKED
        "manifest": manifest,
        "path": theme_path,
        "was_installed_by_default": False,
        "was_installed_by_oem": False,
        "withholding_permissions": False,
    }

    # Activate this theme (not the generic color picker id)
    prefs["extensions"]["theme"] = {"id": ext_id, "use_system": False}

    # Keep dark + rosso seed as fallback if theme images fail to load
    rosso_sk = sk_color(ROSSO)
    browser_theme = prefs.setdefault("browser", {}).setdefault("theme", {})
    browser_theme["color_scheme"] = 2
    browser_theme["color_variant"] = 1
    browser_theme["user_color"] = rosso_sk
    prefs.setdefault("theme", {})
    prefs["theme"]["color_scheme2"] = 2
    prefs["theme"]["color_variant2"] = 1
    prefs["theme"]["user_color2"] = rosso_sk

    prefs.setdefault("extensions", {}).setdefault("ui", {})["developer_mode"] = True

    # Disable "follow OS" / system theme fighting the brand theme
    if "browser" in prefs and "theme" in prefs["browser"]:
        prefs["browser"]["theme"].pop("follows_system_colors", None)

    prefs_path.write_text(
        json.dumps(prefs, separators=(",", ":"), ensure_ascii=False),
        encoding="utf-8",
    )
    log.info("wrote Preferences theme id=%s", ext_id)
    return ext_id


def main() -> None:
    t0 = time.perf_counter()
    stop_chrome()
    ext_id = apply(PROFILE_DIR)

    if CHROME.exists():
        subprocess.Popen(
            [
                str(CHROME),
                f"--profile-directory={PROFILE_DIR}",
                f"--load-extension={THEME_DIR.resolve()}",
                "chrome://settings/manageProfile",
                "chrome://extensions/?id=" + ext_id,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        log.info("launched Chrome profile=%s — check Appearance / theme", PROFILE_DIR)

    log.info("done in %.2fs | id=%s", time.perf_counter() - t0, ext_id)


if __name__ == "__main__":
    main()
