"""Merging the IBM Plex Sans SC supplement into copies of Frex Sans GB's masters."""

import logging
from pathlib import Path

import glyphsLib
import ufoLib2
from fontTools.designspaceLib import DesignSpaceDocument

from .paths import FREX_DESIGNSPACE, FREX_MASTERS, MERGED, PLEX_GLYPHS
from .sources import load_glyphs, supplement_codepoints

MASTERS = ("Thin", "Regular", "Bold")

# Supplement code points whose characters Frex already has under another code point.
EQUIVALENTS = {
    0xF979: 0x51C9,  # 凉, compatibility ideograph
    0xFA0C: 0x5140,  # 兀, compatibility ideograph
    **{0xE790 + i: 0xFE13 + i for i in range(6)},  # GB 18030 private use: ︓︔︕︖︗︘
    0xE7C7: 0x1E3F,  # GB 18030 private use: ḿ
    0xE7C8: 0x01F9,  # GB 18030 private use: ǹ
}
# What add-ufo-vert-info.py gives every Frex glyph.
VERTICAL_ORIGIN, VERTICAL_ADVANCE = 880, 1000

log = logging.getLogger(__name__)


def supplement_glyphs(
    plex: ufoLib2.Font, codepoints: list[int]
) -> dict[str, list[int]]:
    """IBM glyph name -> the supplement code points it is imported with. Each code
    point goes to the first glyph that maps it, in the source's order."""
    first: dict[int, str] = {}
    for glyph in plex:
        assert glyph.name is not None
        for cp in glyph.unicodes:
            first.setdefault(cp, glyph.name)
    glyphs: dict[str, list[int]] = {}
    for cp in codepoints:
        if cp in first and cp not in EQUIVALENTS:
            glyphs.setdefault(first[cp], []).append(cp)
    return glyphs


def merge(out_dir: Path = MERGED) -> Path:
    """Write the merged masters and their designspace; return the designspace."""
    log.info("convert IBM's .glyphs source")
    plex_designspace = glyphsLib.to_designspace(load_glyphs(PLEX_GLYPHS), minimal=True)
    plex = {source.styleName: source.font for source in plex_designspace.sources}
    glyphs = supplement_glyphs(plex["Regular"], supplement_codepoints())

    out_dir.mkdir(parents=True, exist_ok=True)
    for master in MASTERS:
        log.info("merge into %s", master)
        font = ufoLib2.Font.open(FREX_MASTERS / f"{master}.ufo", lazy=False)
        by_codepoint: dict[int, str] = {}
        for glyph in font:
            assert glyph.name is not None
            by_codepoint.update(dict.fromkeys(glyph.unicodes, glyph.name))
        for cp, existing in EQUIVALENTS.items():
            font[by_codepoint[existing]].unicodes.append(cp)
        for name, codepoints in glyphs.items():
            if name in font:
                raise ValueError(f"{name} is in both Frex and IBM's source")
            glyph = plex[master][name].copy()
            glyph.unicodes = codepoints
            glyph.height = VERTICAL_ADVANCE
            glyph.lib["public.verticalOrigin"] = VERTICAL_ORIGIN
            font.layers.defaultLayer.insertGlyph(glyph, name, copy=False)
        font.glyphOrder = [*font.glyphOrder, *glyphs]
        font.save(out_dir / f"{master}.ufo", overwrite=True)

    designspace = DesignSpaceDocument.fromfile(FREX_DESIGNSPACE)
    for source in designspace.sources:
        assert source.filename is not None
        source.path = str(out_dir / Path(source.filename).name)
        source.filename = None
    path = out_dir / FREX_DESIGNSPACE.name
    designspace.write(path)
    return path
