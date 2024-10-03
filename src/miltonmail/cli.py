#!/usr/bin/env python3
"""
miltonmail CLI
"""
import os

import click
import coloredlogs
from click import echo

from miltonmail import __version__, config, core, crypto

LOGLEVEL: str = os.environ.get("LOGLEVEL", "INFO").upper()
LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

coloredlogs.install(level=LOGLEVEL, fmt=LOG_FORMAT)

# check if passphrase is set
try:
    crypto.get_passphrase()
except ValueError:
    click.echo("Passphrase not found in environment. Set MILTON_PASS to use the CLI.")
    exit(1)


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """Main entry point for Milton CLI."""


@cli.command()
def info() -> None:
    """display configration information"""
    echo(f"Configuration path: {config.DB_PATH}")

    try:
        current_account = config.get_current_account_name()
        echo(f"Current account: {current_account}")
    except ValueError as e:
        echo(str(e))


@cli.command()
def add_account() -> None:
    """Add a new account interactively."""
    # Load current config
    try:
        current_config = config.get_config()
    except FileNotFoundError:
        current_config = config.Config(accounts=[])

    # Collect account details interactively
    name = click.prompt("Account name", type=str)
    server = click.prompt("IMAP server", type=str)
    username = click.prompt("Username", type=str)
    password = click.prompt("Password", hide_input=True)
    port = click.prompt("IMAP Port", type=int, default=993)

    # Add the account to the configuration
    new_account = config.add_account(
        name=name, server=server, username=username, password=password, port=port
    )
    current_config.accounts.append(new_account)

    # Save updated config
    config.save_config(current_config)

    click.echo(f"Account '{name}' added successfully!")


@cli.group()
def show() -> None:
    """show info, see subcommands"""


@show.command("accounts")
def list_accounts() -> None:
    """List all existing accounts."""
    try:
        current_config = config.get_config()
        if not current_config.accounts:
            click.echo("No accounts found.")
            return

        click.echo("Existing accounts:")
        for account in current_config.accounts:
            click.echo(
                f"- {account.name} (Server: {account.server}, Username: {account.username})"
            )

    except FileNotFoundError:
        click.echo("No configuration file found. No accounts have been added yet.")


@show.command("folders")
def show_folders() -> None:
    """List all folders for the current account"""
    acc = config.get_current_account()

    conn = core.login_to_imap(
        acc.server, acc.username, acc.decrypt_password(), acc.port
    )
    folders = core.list_folders(conn)
    for folder in folders:
        click.echo(folder)


@cli.group("get")
def get_items() -> None:
    """get items, see subcommands"""


@get_items.command("attachments")
@click.argument("folder")
def get_attachments(folder: str) -> None:
    """Download attachments from imap folder to current DB_PATH/<account_name>/attachments"""

    acc = config.get_current_account()

    dest = config.DB_PATH / acc.name / "attachments"
    dest.mkdir(parents=True, exist_ok=True)

    conn = core.login_to_imap(
        acc.server, acc.username, acc.decrypt_password(), acc.port
    )
    core.download_attachments_from_folder(conn, folder, output_dir=dest)


if __name__ == "__main__":
    cli()
