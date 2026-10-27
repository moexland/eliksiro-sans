"""File locations in the repository."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "upstream"
WORK = ROOT / "work"
MERGED = WORK / "merged"

FREX_CLONE = UPSTREAM / "frex-sans"
FREX_SOURCES = FREX_CLONE / "sources" / "FrexSansGBVF"
FREX_DESIGNSPACE = FREX_SOURCES / "Frex Sans GB.designspace"
FREX_MASTERS = FREX_SOURCES / "masters"
FREX_TTF = FREX_CLONE / "fonts" / "variable" / "Frex Sans GB[wght].ttf"  # official

PLEX_CLONE = UPSTREAM / "plex"
PLEX_OTF = PLEX_CLONE / "packages/plex-sans-sc/fonts/complete/otf/unhinted"
PLEX_SOURCES = UPSTREAM / "plex-sc-sources" / "sources"
PLEX_GLYPHS = PLEX_SOURCES / "masters" / "IBM Plex Sans SC.glyphs"


def plex_static(style: str) -> Path:
    return PLEX_OTF / f"IBMPlexSansSC-{style}.otf"
