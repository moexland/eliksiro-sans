"""Reading the inputs: the supplement code points, IBM's Glyphs sources and cmaps."""

from pathlib import Path
from typing import Any

import glyphsLib
from fontTools.ttLib import TTFont

from .paths import FREX_TTF, plex_static


def best_cmap(font: TTFont) -> dict[int, str]:
    cmap = font.getBestCmap()
    if cmap is None:
        raise ValueError(f"no Unicode cmap in {font.reader and font.reader.file}")
    return cmap


def supplement_codepoints() -> list[int]:
    """Code points IBM Plex Sans SC has and Frex Sans GB lacks."""
    plex = set(best_cmap(TTFont(plex_static("Regular"))))
    frex = set(best_cmap(TTFont(FREX_TTF)))
    return sorted(plex - frex)


def load_glyphs(path: Path) -> Any:
    """A glyphsLib GSFont (about 20 s and a few GiB for IBM's 210 MB source)."""
    with path.open(encoding="utf-8") as f:
        return glyphsLib.load(f)
