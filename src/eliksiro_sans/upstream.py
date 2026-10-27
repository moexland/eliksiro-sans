"""Fetching the upstream sources into upstream/."""

import hashlib
import logging
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from .paths import FREX_CLONE, PLEX_CLONE, PLEX_OTF, PLEX_SOURCES, UPSTREAM

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

log = logging.getLogger(__name__)


def _git(*args: str | Path) -> str:
    result = subprocess.run(
        ["git", "-c", "advice.detachedHead=false", *map(str, args)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def clone(url: str, commit: str, dest: Path, sparse: Path | None = None) -> None:
    """With sparse, only that directory is checked out and its files downloaded."""
    if not dest.exists():
        partial = ["--filter=blob:none", "--no-checkout"] if sparse else []
        _git("clone", "--depth", "1", "--revision", commit, *partial, url, dest)
        if sparse:
            _git("-C", dest, "sparse-checkout", "set", sparse.as_posix())
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


def fetch_plex_sources() -> None:
    download(PLEX_SOURCES_URL, PLEX_SOURCES_ZIP)
    with PLEX_SOURCES_ZIP.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    if digest != PLEX_SOURCES_SHA256:
        sys.exit(
            f"{PLEX_SOURCES_ZIP.name} has SHA-256 {digest}, expected {PLEX_SOURCES_SHA256}"
        )
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
    log.info("IBM Plex Sans SC static fonts")
    clone(PLEX_REPO, PLEX_COMMIT, PLEX_CLONE, sparse=PLEX_OTF.relative_to(PLEX_CLONE))
    log.info("IBM Plex Sans SC sources")
    fetch_plex_sources()
