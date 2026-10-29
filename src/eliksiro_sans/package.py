"""Packaging Eliksiro Sans for npm: the font in WOFF2 slices for the web, with a CSS
entry, so that browsers download only the slices a page uses."""

import json
import logging
import re
import shutil
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.unicodedata import script

from .build import DOCUMENTS, FILENAME, STEM
from .fontinfo import FAMILY
from .paths import GOOGLE_SLICES, NPM, OUT, ROOT
from .sources import best_cmap

NAME = "@moexland/eliksiro-sans"
CSS = "eliksiro-sans.css"
# npm's patch version, for releases that change the packaging but not the font.
PATCH = 1
# GPOS features such as kern and chws work only within a file, so these blocks,
# Latin, punctuation and full-width forms, all go in the first slice.
FIRST_BLOCKS = [(0x20, 0xFF), (0x2000, 0x206F), (0x3000, 0x303F), (0xFF00, 0xFFEF)]
# Code points per slice beyond Google's slices, about the size of Google's own bins.
BIN = 140
SUBSET_OPTIONS = {
    "layout_features": ["*"],
    "name_IDs": ["*"],
    "name_languages": ["*"],
    "flavor": "woff2",
    # Only the slice's code points, not their mirrored forms, such as U+2265 for
    # U+2264: those have their own slices.
    "bidi_closure": False,
}

log = logging.getLogger(__name__)


def google_slices() -> list[list[int]]:
    """Google Fonts' slices, most frequent first."""
    blocks = GOOGLE_SLICES.read_text().split("subsets {")[1:]
    # The file lists them least frequent first.
    return [
        [int(cp) for cp in re.findall(r"codepoints: (\d+)", block)]
        for block in reversed(blocks)
    ]


def bins(codepoints: list[int]) -> list[list[int]]:
    """Split evenly into slices of about BIN code points."""
    size = len(codepoints)
    n = -(-size // BIN)
    return [codepoints[i * size // n : (i + 1) * size // n] for i in range(n)]


def slices(codepoints: set[int]) -> list[list[int]]:
    """The font's code points in slices, most frequent first: Google's slices, without
    the code points the font lacks, then the rest in code point order, ideographs apart.
    """
    google = google_slices()
    first = set(google[0]) | {
        cp for cp in codepoints for lo, hi in FIRST_BLOCKS if lo <= cp <= hi
    }
    result, taken = [], set()
    for codes in [first, *google[1:]]:
        rest = sorted((set(codes) & codepoints) - taken)
        if rest:
            result.append(rest)
            taken.update(rest)
    left = sorted(codepoints - taken)
    ideographs = [cp for cp in left if script(chr(cp)) == "Hani"]
    others = [cp for cp in left if script(chr(cp)) != "Hani"]
    return result + bins(others) + bins(ideographs)


def unicode_range(codepoints: list[int]) -> str:
    runs: list[list[int]] = []
    for cp in sorted(codepoints):
        if runs and runs[-1][1] == cp - 1:
            runs[-1][1] = cp
        else:
            runs.append([cp, cp])
    return ", ".join(f"U+{a:X}" if a == b else f"U+{a:X}-{b:X}" for a, b in runs)


def slice_path(index: int) -> str:
    return f"woff2/{STEM}-{index:03}.woff2"


def write_slice(font_path: Path, codepoints: list[int], dest: Path) -> None:
    options = subset.Options(**SUBSET_OPTIONS)
    font = subset.load_font(font_path, options, dontLoadGlyphNames=True)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=codepoints)
    subsetter.subset(font)
    subset.save_font(font, dest, options)


def version(font: TTFont) -> str:
    """npm's version for the font's: Version 0.100 is 0.100.0."""
    name = font["name"].getDebugName(5) or ""
    match = re.fullmatch(r"Version (\d+)\.(\d{3})", name)
    assert match, name
    major, minor = map(int, match.groups())
    return f"{major}.{minor}.{PATCH}"


def package_json(font: TTFont) -> dict:
    return {
        "name": NAME,
        "version": version(font),
        "description": "Frex Sans GB with IBM Plex Sans SC supplements, sliced for the web",
        "license": "OFL-1.1",
        "repository": {
            "type": "git",
            "url": "git+https://github.com/moexland/eliksiro-sans.git",
        },
        # For CSS @import of the bare package name, as by Tailwind CSS.
        "style": f"./{CSS}",
        "exports": {
            ".": {"style": f"./{CSS}", "default": f"./{CSS}"},
            "./otf": f"./{FILENAME}",
            # For users' own @font-face rules, such as one for U+00B7 alone.
            "./woff2/*": "./woff2/*",
            "./package.json": "./package.json",
        },
        "files": [CSS, "woff2/", FILENAME, *DOCUMENTS],
        "sideEffects": ["*.css"],
        "publishConfig": {"access": "public"},
    }


def package(out_dir: Path = NPM) -> Path:
    """Write the npm package into out_dir."""
    font_path = OUT / FILENAME
    font = TTFont(font_path)
    (axis,) = font["fvar"].axes
    parts = slices(set(best_cmap(font)))
    log.info("%d slices", len(parts))

    shutil.rmtree(out_dir, ignore_errors=True)
    (out_dir / "woff2").mkdir(parents=True)
    paths = [out_dir / slice_path(index) for index in range(len(parts))]
    with ProcessPoolExecutor() as pool:
        list(pool.map(write_slice, repeat(font_path), parts, paths))
    faces = []
    for index, codepoints in enumerate(parts):
        faces.append(
            "@font-face {\n"
            f'  font-family: "{FAMILY}";\n'
            "  font-style: normal;\n"
            f"  font-weight: {axis.minValue:g} {axis.maxValue:g};\n"
            "  font-display: swap;\n"
            f'  src: url("./{slice_path(index)}") format("woff2");\n'
            f"  unicode-range: {unicode_range(codepoints)};\n"
            "}\n"
        )
    (out_dir / CSS).write_text("\n".join(faces))

    content = json.dumps(package_json(font), indent=2, ensure_ascii=False)
    (out_dir / "package.json").write_text(content + "\n")
    shutil.copy(ROOT / "npm" / "README.md", out_dir)
    for name in (FILENAME, *DOCUMENTS):
        shutil.copy(OUT / name, out_dir)
    return out_dir
