"""Compiling Eliksiro Sans from the merged masters."""

import logging
import math
import os
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.ttLib import TTFont

from .fontinfo import FAMILY
from .paths import COMPILED, MERGED, OUT, ROOT

STEM = f"{FAMILY.replace(' ', '')}-VF"
FILENAME, WOFF2_FILENAME = f"{STEM}.otf", f"{STEM}.woff2"
# head.modified. Fixed, so that the same sources always give the same bytes.
MODIFIED = datetime(2026, 10, 27, tzinfo=UTC)
DOCUMENTS = ("OFL.txt", "FONTLOG.txt")

log = logging.getLogger(__name__)


def win_metrics(font: TTFont) -> tuple[int, int]:
    """usWinAscent and usWinDescent that clear every glyph at every weight."""
    # Outlines interpolate linearly between neighbouring masters, which sit at the
    # axis's minimum, default and maximum, so their extremes are at the masters.
    (axis,) = font["fvar"].axes
    y_min = y_max = 0.0
    for value in (axis.minValue, axis.defaultValue, axis.maxValue):
        glyphs = font.getGlyphSet(location={axis.axisTag: value})
        pen = BoundsPen(glyphs)
        for glyph in glyphs.values():
            glyph.draw(pen)
        assert pen.bounds is not None
        y_min, y_max = min(y_min, pen.bounds[1]), max(y_max, pen.bounds[3])
    return math.ceil(y_max), -math.floor(y_min)


def build(out_dir: Path = OUT) -> Path:
    """Compile the CFF2 variable font into out_dir, as OTF and WOFF2, next to its OFL
    and FONTLOG."""
    compiled = COMPILED / FILENAME
    log.info("compile with fontmake")
    subprocess.run(
        [sys.executable, "-m", "fontmake", "-m", str(MERGED / f"{FAMILY}.designspace")]
        + ["-o", "variable-cff2", "--optimize-cff", "1"]
        + ["--output-path", str(compiled), "--verbose", "WARNING"],
        check=True,
        env=os.environ | {"SOURCE_DATE_EPOCH": str(int(MODIFIED.timestamp()))},
    )

    log.info("set the win metrics from the glyph bounds")
    # Measured on a separate TTFont: drawing the glyphs would get CFF2 recompiled.
    ascent, descent = win_metrics(TTFont(compiled))
    font = TTFont(compiled, recalcBBoxes=False, recalcTimestamp=False)
    # fontTools sets the table's fields at run time, unknown to the type checker.
    vars(font["OS/2"]).update(usWinAscent=ascent, usWinDescent=descent)
    out_dir.mkdir(parents=True, exist_ok=True)
    font.save(out_dir / FILENAME)
    log.info("compress to WOFF2")
    font.flavor = "woff2"
    font.save(out_dir / WOFF2_FILENAME)
    for name in DOCUMENTS:
        shutil.copy(ROOT / name, out_dir)
    return out_dir / FILENAME
