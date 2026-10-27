"""Eliksiro Sans's names, version and line metrics, and its designspace."""

from pathlib import Path

from fontTools.designspaceLib import (
    AxisLabelDescriptor,
    DesignSpaceDocument,
    InstanceDescriptor,
)
from ufoLib2.objects import Info

from .paths import FREX_DESIGNSPACE

FAMILY = "Eliksiro Sans"
VERSION = (0, 100)
CREATED = "2026/10/27 00:00:00"
# Ours, then the upstream ones as in their fonts. No "Plex": a Reserved Font Name.
COPYRIGHT = (
    "Copyright 2026 The Eliksiro Sans Project Authors"
    " (https://github.com/moexland/eliksiro-sans)."
    " Copyright 2025 The Frex Sans Project Authors"
    " (https://gitee.com/NightFurySL2001/flex-sc)."
    " Copyright 2018 IBM Corp. All rights reserved."
)
ASCENDER, DESCENDER, LINE_GAP = 880, -120, 500
WEIGHTS = {
    "Thin": 100,
    "ExtraLight": 200,
    "Light": 300,
    "Regular": 400,
    "Text": 450,
    "Medium": 500,
    "SemiBold": 600,
    "Bold": 700,
}
REGULAR, BOLD = WEIGHTS["Regular"], WEIGHTS["Bold"]

# Frex's, which ufo2ft derives anew from the family and style names and the version.
DERIVED = (
    "styleMapFamilyName",
    "styleMapStyleName",
    "openTypeNamePreferredFamilyName",
    "openTypeNamePreferredSubfamilyName",
    "openTypeNameVersion",
    "postscriptFontName",
    "postscriptFullName",
)
# Frex's credits and vendor ID, which are not Eliksiro Sans's.
DROPPED = (
    "openTypeNameDesigner",
    "openTypeNameManufacturer",
    "openTypeNameManufacturerURL",
    "openTypeOS2VendorID",
)


def apply(info: Info) -> None:
    """Turn a Frex master's font info into Eliksiro Sans's. The win metrics are left
    to the build, which sets them from the compiled glyphs."""
    info.familyName = FAMILY
    info.copyright = COPYRIGHT
    info.versionMajor, info.versionMinor = VERSION
    info.openTypeHeadCreated = CREATED
    for key in (*DERIVED, *DROPPED):
        setattr(info, key, None)
    info.openTypeHheaAscender = info.openTypeOS2TypoAscender = ASCENDER
    info.openTypeHheaDescender = info.openTypeOS2TypoDescender = DESCENDER
    info.openTypeHheaLineGap = info.openTypeOS2TypoLineGap = LINE_GAP


def designspace(masters: Path) -> DesignSpaceDocument:
    """Frex's designspace, for the masters in the given directory, with Eliksiro Sans's
    names, named instances and STAT labels."""
    doc = DesignSpaceDocument.fromfile(FREX_DESIGNSPACE)
    del doc.lib["public.fontInfo"]
    for source in doc.sources:
        assert source.filename is not None
        source.path = str(masters / Path(source.filename).name)
        source.filename = None
        source.familyName = FAMILY
        source.localisedFamilyName = {}
    (axis,) = doc.axes
    axis.axisLabels = [
        AxisLabelDescriptor(
            name=name,
            userValue=value,
            elidable=value == REGULAR,
            linkedUserValue=BOLD if value == REGULAR else None,
        )
        for name, value in WEIGHTS.items()
    ]
    doc.instances = [
        InstanceDescriptor(
            familyName=FAMILY,
            styleName=name,
            postScriptFontName=f"{FAMILY.replace(' ', '')}-{name}",
            userLocation={axis.name: value},
        )
        for name, value in WEIGHTS.items()
    ]
    return doc
