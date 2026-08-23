"""Lorenzo Sforzini Racing — shared brand tokens for all generators."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
BRAND_DIR = ROOT / "brand-identity"
FONTS = ROOT / "fonts"
WIN_FONTS = Path(r"C:\Windows\Fonts")

# Identity
BRAND_FULL = "Lorenzo Sforzini"
BRAND_SHORT = "L.Sforzini"
BRAND_KIT = "L.Sforzini 44 Racing"
RACE_NUMBER = "44"
TAGLINE = "Racing"
MONOGRAM_LETTERS = "LS"

# Slug / file stems
SLUG = "lsforzini44"
WORDMARK_STEM = "wordmark_lsforzini"
MARK_STEM = "mark_44"
MONOGRAM_STEM = "monogram_ls44"
MARK_DIR = "03-mark-44"
MONOGRAM_DIR = "06-monogram-ls"

# Core palette
CARBON = (8, 8, 10)
CARBON_MID = (18, 18, 22)
ICE = (248, 248, 250)
ICE_DIM = (200, 200, 208)
SILVER = (168, 168, 176)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Hero accent — Electric Blue (replaces Rosso Corsa)
HERO_ACCENT = (0, 163, 224)
HERO_ACCENT_HEX = "#00A3E0"
HERO_ACCENT_KEY = "electric_blue"
HERO_ACCENT_NAME = "Electric Blue"

PALETTE = {
    "carbon": ("#08080A", CARBON),
    "carbon_mid": ("#121216", CARBON_MID),
    "ice": ("#F8F8FA", ICE),
    "ice_dim": ("#C8C8D0", ICE_DIM),
    "silver": ("#A8A8B0", SILVER),
    "black": ("#000000", BLACK),
    "white": ("#FFFFFF", WHITE),
    "electric_blue": (HERO_ACCENT_HEX, HERO_ACCENT),
}

RACING_COLORS = {
    "electric_blue": {
        "hex": "#00A3E0",
        "rgb": (0, 163, 224),
        "name": "Electric Blue",
        "use": "Hero accent / number / CTA",
    },
    "rosso_corsa": {
        "hex": "#E10600",
        "rgb": (225, 6, 0),
        "name": "Rosso Corsa",
        "use": "Alternate motorsport accent",
    },
    "papaya": {
        "hex": "#FF8700",
        "rgb": (255, 135, 0),
        "name": "Papaya",
        "use": "Energy / endurance night",
    },
    "signal_yellow": {
        "hex": "#F5C400",
        "rgb": (245, 196, 0),
        "name": "Signal Yellow",
        "use": "High-vis / safety stripe",
    },
    "racing_green": {
        "hex": "#004225",
        "rgb": (0, 66, 37),
        "name": "Racing Green",
        "use": "Heritage / classic GT",
    },
    "titanium": {
        "hex": "#8A8F98",
        "rgb": (138, 143, 152),
        "name": "Titanium",
        "use": "Secondary metal / carbon trim",
    },
}

TYPE_SHEAR = 0.36
STRIPE_ANGLE_DEG = -18.0
