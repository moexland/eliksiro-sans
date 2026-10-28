"""Checking the built font against the upstream fonts it comes from."""

import io
import logging
import sys
from typing import Any

from fontTools.designspaceLib import DesignSpaceDocument
from fontTools.misc.xmlWriter import XMLWriter
from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otBase import BaseTTXConverter
from fontTools.varLib import interpolatable

from .build import FILENAME
from .fixes import CONTOUR_ORDERS, START_POINTS
from .fontinfo import FAMILY, WEIGHTS
from .merge import EQUIVALENTS, MASTERS
from .paths import FREX_TTF, MERGED, OUT, plex_static
from .sources import best_cmap, supplement_codepoints

# How far outlines may stray, in font units of bounds and advance. From Frex's TrueType
# font, by the error of its quadratic curves; from IBM's static fonts, by what IBM's
# separate instance sources for them account for.
FREX_TOLERANCE = 1
IBM_TOLERANCE = 3
# Glyphs whose IBM static fonts and masters, which the supplement comes from, disagree
# by more than that at some weight: mostly ones IBM edited after building the fonts.
IBM_OUTLIERS = {
    "uni4491",
    "uni4C0C",
    "uni4D3B",
    "uni4D69",
    "uni4E2F",
    "uni84F1",
    "uni851D",
    "uni8520",
    "uni852F",
    "uni883F",
    "uni884B",
    "uni9FB0",
}
# Supplement code points without IBM's glyphs: U+22EF has a copy of Frex's U+2026.
FROM_FREX = {*EQUIVALENTS, 0x22EF}
# interpolatable's heuristic findings, listed for review rather than failed.
HEURISTIC = {"kink", "underweight", "overweight"}

log = logging.getLogger(__name__)


class Checks:
    def __init__(self) -> None:
        self.failed: list[str] = []

    def check(self, label: str, ok: bool, detail: str = "") -> None:
        print(
            f"{'ok' if ok else 'FAIL':5} {label}" + (f" ({detail})" if detail else "")
        )
        if not ok:
            self.failed.append(label)

    def note(self, text: str) -> None:
        print(f"{'note':5} {text}")


def difference(ours: Any, name: str, theirs: Any, their_name: str) -> float:
    """The largest difference between two glyphs' bounds and advances."""
    bounds = []
    for glyphs, n in ((ours, name), (theirs, their_name)):
        pen = BoundsPen(glyphs)
        glyphs[n].draw(pen)
        bounds.append(pen.bounds)
    a, b = bounds
    if a is None or b is None:
        apart = 0.0 if a == b else float("inf")
    else:
        apart = max(abs(p - q) for p, q in zip(a, b, strict=True))
    return max(apart, abs(ours[name].width - theirs[their_name].width))


def layout(font: TTFont, tag: str) -> tuple[list[tuple], list[tuple], list[str]]:
    """GSUB or GPOS: lookups as their flags and XML, Extension subtables unwrapped; the
    features' lookups; and the scripts as XML."""
    table = font[tag]
    assert isinstance(table, BaseTTXConverter)

    def xml(*objects: Any) -> str:
        out = io.StringIO()
        writer = XMLWriter(out)
        for obj in objects:
            obj.toXML(writer, font)
        return out.getvalue()

    lookups = [
        (
            lookup.LookupFlag,
            xml(*(getattr(st, "ExtSubTable", st) for st in lookup.SubTable)),
        )
        for lookup in table.table.LookupList.Lookup
    ]
    features = [
        (record.FeatureTag, record.Feature.LookupListIndex)
        for record in table.table.FeatureList.FeatureRecord
    ]
    scripts = [xml(record) for record in table.table.ScriptList.ScriptRecord]
    return lookups, features, scripts


def check_names(checks: Checks, font: TTFont) -> None:
    plex = sorted(
        {r.nameID for r in font["name"].names if "plex" in r.toUnicode().lower()}
    )
    checks.check(
        'no "Plex", a Reserved Font Name, in the name table', not plex, str(plex)
    )


def check_frex(checks: Checks, font: TTFont, frex: TTFont) -> None:
    cmap, frex_cmap = best_cmap(font), best_cmap(frex)
    expected = set(frex_cmap) | set(supplement_codepoints()) | set(EQUIVALENTS)
    checks.check(
        "code points: Frex's, the supplement and the equivalents",
        set(cmap) == expected,
        f"{len(cmap)}",
    )
    moved = [f"U+{cp:04X}" for cp in frex_cmap if cmap.get(cp) != frex_cmap[cp]]
    checks.check(
        "Frex's code points keep their glyphs, but U+2022", moved == ["U+2022"]
    )

    for tag in ("GSUB", "GPOS"):
        same = layout(font, tag) == layout(frex, tag)
        checks.check(f"{tag} lookups, features and scripts as in Frex", same)

    # The fixes change Frex's outlines between the masters only.
    fixed = {name for name, _ in (*START_POINTS, *CONTOUR_ORDERS)}
    masters = {WEIGHTS[m] for m in MASTERS}
    for style, weight in WEIGHTS.items():
        ours = font.getGlyphSet(location={"wght": weight})
        theirs = frex.getGlyphSet(location={"wght": weight})
        names = [n for n in frex.getGlyphOrder() if weight in masters or n not in fixed]
        off = [n for n in names if difference(ours, n, theirs, n) > FREX_TOLERANCE]
        checks.check(
            f"Frex's glyphs at {style}, within {FREX_TOLERANCE} unit of Frex's font",
            not off,
            f"{len(names)} glyphs" + (f"; off: {off[:10]}" if off else ""),
        )


def check_ibm(checks: Checks, font: TTFont) -> None:
    cmap = best_cmap(font)
    codepoints = [cp for cp in supplement_codepoints() if cp not in FROM_FREX]
    for style, weight in WEIGHTS.items():
        static = TTFont(plex_static(style))
        static_cmap = best_cmap(static)
        ours, theirs = font.getGlyphSet(location={"wght": weight}), static.getGlyphSet()
        off, close = [], 0
        for cp in codepoints:
            d = difference(ours, cmap[cp], theirs, static_cmap[cp])
            close += d <= 1
            if d > IBM_TOLERANCE and cmap[cp] not in IBM_OUTLIERS:
                off.append(cmap[cp])
        checks.check(
            f"supplement at {style}, within {IBM_TOLERANCE} units of IBM's static font",
            not off,
            f"{close} of {len(codepoints)} within 1 unit"
            + (f"; off: {off[:10]}" if off else ""),
        )


def check_interpolation(checks: Checks) -> None:
    path = MERGED / f"{FAMILY}.designspace"
    unexported = set(DesignSpaceDocument.fromfile(path).lib["public.skipExportGlyphs"])
    problems = interpolatable.main([str(path), "--quiet"]) or {}
    errors, findings = [], []
    for name, items in sorted(problems.items()):
        for p in items:
            if p["type"] == "missing" and name in unexported:
                continue
            masters = f"{p.get('master_1')}-{p.get('master_2')}"
            entry = f"{name} {p['type']} contour {p.get('contour')} {masters}"
            (findings if p["type"] in HEURISTIC else errors).append(entry)
    checks.check(
        "interpolatable on the merged masters, all glyphs: no errors",
        not errors,
        "; ".join(errors[:10]),
    )
    for entry in findings:
        checks.note(f"interpolatable heuristic: {entry}")


def verify() -> None:
    """Exit with an error if any check fails."""
    font, frex = TTFont(OUT / FILENAME), TTFont(FREX_TTF)
    checks = Checks()
    check_names(checks, font)
    log.info("against Frex Sans GB")
    check_frex(checks, font, frex)
    log.info("against IBM Plex Sans SC's static fonts")
    check_ibm(checks, font)
    log.info("interpolatable")
    check_interpolation(checks)
    if checks.failed:
        sys.exit(f"{len(checks.failed)} check(s) failed")
