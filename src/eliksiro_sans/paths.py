"""File locations in the repository."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UPSTREAM = ROOT / "upstream"

FREX_CLONE = UPSTREAM / "frex-sans"

PLEX_CLONE = UPSTREAM / "plex"
PLEX_OTF = PLEX_CLONE / "packages/plex-sans-sc/fonts/complete/otf/unhinted"
PLEX_SOURCES = UPSTREAM / "plex-sc-sources" / "sources"
