import os
from enum import Enum
from pathlib import Path

from amrita_core.config import CookieConfig

CWD = Path( os.getcwd()) / ".amrita"
CONFIG_DIR = CWD / "config"
CONFIG_PATH = CONFIG_DIR / "config.toml"

DATA_DIR = CWD / "data"
PRESETS_DIR = DATA_DIR / "presets"
MEMORY_SESSIONS_DIR = DATA_DIR / "memory"

COOKIE_CONFIG = CookieConfig(enable_cookie=False)


class ColorsEnum(str, Enum):
    bg_primary = "#1a1a1a"
    bg_secondary = "#504f4f"
    bg_tertiary = "#3d3d3d"
    text_primary = "#ffffff"
    text_secondary = "#b0b0b0"
    accent_primary = "#10a37f"
    accent_hover = "#1d9d73"
    input_bg = "#40414f"
    input_border = "#565869"
    divider = "#404040"


class FontSizesEnum(int, Enum):
    heading = 24
    title = 18
    body = 14
    small = 12


MODELS = [
    "GPT-4",
    "GPT-4 Turbo",
    "GPT-3.5-Turbo",
    "Claude-3-Opus",
    "Claude-3-Sonnet",
    "Deepseek-V3",
    "Qwen-Plus",
]


SIDEBAR_WIDTH = 250
MAIN_PADDING = 15
