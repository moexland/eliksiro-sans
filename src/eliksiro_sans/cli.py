"""Eliksiro Sans build pipeline. Run as: uv run eliksiro-sans COMMAND"""

import argparse
import logging
from collections.abc import Callable

from . import build, merge, upstream, verify

COMMANDS: dict[str, tuple[Callable[[], object], str]] = {
    "fetch": (
        upstream.fetch,
        "fetch the upstream sources into upstream/ and check their contents",
    ),
    "merge": (
        merge.merge,
        "write Eliksiro Sans's masters: Frex's, with the IBM Plex Sans SC supplement",
    ),
    "build": (build.build, "compile the variable font into out/"),
    "verify": (verify.verify, "check the built font against the upstream fonts"),
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="eliksiro-sans", description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    for name, (_, description) in COMMANDS.items():
        commands.add_parser(name, help=description, description=description)
    args = parser.parse_args(argv)

    # This package's messages only: fontTools logs a lot at INFO.
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%H:%M:%S"))
    package = logging.getLogger("eliksiro_sans")
    package.addHandler(handler)
    package.setLevel(logging.INFO)

    run, _ = COMMANDS[args.command]
    run()
