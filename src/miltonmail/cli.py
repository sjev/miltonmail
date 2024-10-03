#!/usr/bin/env python3
"""
miltonmail CLI
"""

import click
from miltonmail import __version__


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    pass


if __name__ == "__main__":
    cli()
