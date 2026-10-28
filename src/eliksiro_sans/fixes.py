"""Fixes to the merged masters: contours that interpolate wrongly, and the glyphs of
U+2022 and U+22EF."""

from fontTools.misc.roundTools import otRound
from fontTools.misc.transform import Scale
from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.roundingPen import RoundingPointPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from ufoLib2.objects import Component, Font, Glyph

from .paths import plex_sans_static

# Start points to move, (glyph, master) -> {contour: r}: the contour's points become
# points[r:] + points[:r]. For IBM's glyphs, in the point order glyphsLib converts to.
START_POINTS = {
    ("uni6961", "Bold"): {1: 3, 3: 3, 4: 3},  # 楡, IBM
    ("uni6B1D", "Thin"): {15: 3, 19: 1},  # 欝, IBM
    ("uni9476", "Thin"): {19: 4},  # 鑶, IBM
    ("uni7296", "Thin"): {3: 3},  # 犖, Frex
}
# Contours to reorder, (glyph, master) -> the old contour indices in their new order.
CONTOUR_ORDERS = {
    ("uni2504", "Bold"): [1, 2, 3, 0, 4, 5],  # ┄, Frex
}
# Frex's Latin, which is IBM Plex Sans SC's, is IBM Plex Sans enlarged by this much:
# heights exactly, widths a little less in heavier weights.
LATIN_SCALE = 1.05


def bullet(master: str, template: Glyph) -> Glyph:
    """U+2022 from IBM Plex Sans, enlarged like Frex's Latin, with the template's
    vertical metrics."""
    source = TTFont(plex_sans_static(master)).getGlyphSet()["bullet"]
    glyph = Glyph(
        "uni2022",
        width=otRound(source.width * LATIN_SCALE),
        height=template.height,
        unicodes=[0x2022],
    )
    glyph.lib["public.verticalOrigin"] = template.lib["public.verticalOrigin"]
    pen = SegmentToPointPen(RoundingPointPen(glyph.getPointPen()))
    source.draw(TransformPen(pen, Scale(LATIN_SCALE)))
    return glyph


def midline_ellipsis(ellipsis: Glyph) -> Glyph:
    """U+22EF as a copy of U+2026's centred ellipsis. Not the same glyph: in Latin text,
    locl swaps that one for the baseline ellipsis."""
    assert ellipsis.name is not None
    glyph = Glyph(
        "uni22EF",
        width=ellipsis.width,
        height=ellipsis.height,
        unicodes=[0x22EF],
        components=[Component(ellipsis.name)],
    )
    glyph.lib["public.verticalOrigin"] = ellipsis.lib["public.verticalOrigin"]
    return glyph


def apply(font: Font, master: str) -> None:
    for (name, m), shifts in START_POINTS.items():
        if m == master:
            for index, r in shifts.items():
                contour = font[name].contours[index]
                contour.points = contour.points[r:] + contour.points[:r]
    for (name, m), order in CONTOUR_ORDERS.items():
        if m == master:
            glyph = font[name]
            glyph.contours = [glyph.contours[i] for i in order]

    # U+2022 was on Frex's Latin middle dot.
    middle_dot = font["uni00B7.latn"]
    middle_dot.unicodes.remove(0x2022)
    names = []
    for glyph in bullet(master, middle_dot), midline_ellipsis(font["uni2026"]):
        assert glyph.name is not None
        font.layers.defaultLayer.insertGlyph(glyph, overwrite=False, copy=False)
        names.append(glyph.name)
    font.glyphOrder = [*font.glyphOrder, *names]
