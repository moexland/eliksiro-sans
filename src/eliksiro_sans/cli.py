"""Eliksiro Sans build pipeline. Run as: uv run eliksiro-sans COMMAND"""

import argparse
import logging
from collections.abc import Callable

from . import upstream

COMMANDS: dict[str, tuple[Callable[[], None], str]] = {
    "fetch": (
        upstream.fetch,
        "fetch the upstream sources into upstream/ and check their contents",
    ),
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
