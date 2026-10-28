"""Fetching the upstream sources into upstream/."""

import hashlib
import logging
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from .paths import (
    FREX_CLONE,
    GOOGLE_SLICES,
    PLEX_CLONE,
    PLEX_OTF,
    PLEX_SANS_OTF,
    PLEX_SOURCES,
    UPSTREAM,
)

FREX_REPO = "https://github.com/maoken-fonts/frex-sans.git"
FREX_COMMIT = "2ce4353c796c3ed8c3f05e9334b653345130bd03"  # tag v1.100
PLEX_REPO = "https://github.com/IBM/plex.git"
PLEX_COMMIT = "222657a016f31e6d913ede88520de7dec84dc81b"  # tag @ibm/plex-sans-sc@1.1.0
PLEX_SOURCES_URL = (
    "https://github.com/IBM/plex/releases/download/"
    "%40ibm%2Fplex-sans-sc%401.1.0/sources.zip"
)
PLEX_SOURCES_SHA256 = "136363a1fa695df192fe05a6b6527ae61dbae8ccc311920e5fe96cb4f73a0ea7"
PLEX_SOURCES_ZIP = UPSTREAM / "plex-sc-sources.zip"
# Google Fonts' Simplified Chinese web slices: the npm package's start from them.
GOOGLE_SLICES_URL = (
    "https://raw.githubusercontent.com/googlefonts/nam-files/"
    "80f8e537a43ff6754810666709740dc18de8a17f/slices/simplified-chinese_default.txt"
)
GOOGLE_SLICES_SHA256 = (
    "cd022036048744a478b2d261131a90400bacbb9098b83efd0360f1e44122c2c1"
)

log = logging.getLogger(__name__)


def _git(*args: str | Path) -> str:
    result = subprocess.run(
        ["git", "-c", "advice.detachedHead=false", *map(str, args)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def clone(url: str, commit: str, dest: Path, sparse: tuple[Path, ...] = ()) -> None:
    """With sparse, only those directories are checked out and their files downloaded."""
    if not dest.exists():
        partial = ["--filter=blob:none", "--no-checkout"] if sparse else []
        _git("clone", "--depth", "1", "--revision", commit, *partial, url, dest)
    if sparse:
        # Also on an existing clone, which may predate a directory in the list.
        _git("-C", dest, "sparse-checkout", "set", *(p.as_posix() for p in sparse))
        _git("-C", dest, "checkout")
    head = _git("-C", dest, "rev-parse", "HEAD")
    if head != commit:
        sys.exit(f"{dest} is at {head}, expected {commit}; remove it to fetch again")


def download(url: str, dest: Path, attempts: int = 3) -> None:
    if dest.exists():
        return
    part = dest.with_name(dest.name + ".part")
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url) as response, part.open("wb") as f:
                shutil.copyfileobj(response, f, 1 << 20)
            break
        except OSError as e:
            if attempt == attempts:
                raise
            log.warning("retrying %s after: %s", dest.name, e)
    part.replace(dest)


def check_sha256(path: Path, expected: str) -> None:
    with path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    if digest != expected:
        sys.exit(f"{path.name} has SHA-256 {digest}, expected {expected}")


def fetch_plex_sources() -> None:
    download(PLEX_SOURCES_URL, PLEX_SOURCES_ZIP)
    check_sha256(PLEX_SOURCES_ZIP, PLEX_SOURCES_SHA256)
    medium = "sources/instances/postscript/IBM Plex Sans SC-Medium.glyphs"
    with zipfile.ZipFile(PLEX_SOURCES_ZIP) as z:
        for name in z.namelist():
            if name.startswith("sources/masters/") or name == medium:
                # ZipFile.extract drops ".." and leading "/" from member names.
                z.extract(name, PLEX_SOURCES.parent)


def fetch() -> None:
    UPSTREAM.mkdir(exist_ok=True)
    log.info("Frex Sans")
    clone(FREX_REPO, FREX_COMMIT, FREX_CLONE)
    log.info("IBM Plex Sans SC and IBM Plex Sans static fonts")
    sparse = tuple(path.relative_to(PLEX_CLONE) for path in (PLEX_OTF, PLEX_SANS_OTF))
    clone(PLEX_REPO, PLEX_COMMIT, PLEX_CLONE, sparse)
    log.info("IBM Plex Sans SC sources")
    fetch_plex_sources()
    log.info("Google Fonts' Simplified Chinese slices")
    download(GOOGLE_SLICES_URL, GOOGLE_SLICES)
    check_sha256(GOOGLE_SLICES, GOOGLE_SLICES_SHA256)
