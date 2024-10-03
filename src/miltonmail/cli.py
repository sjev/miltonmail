#!/usr/bin/env python3
"""
miltonmail CLI
"""

import click
from miltonmail import __version__, config, crypto

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


@cli.group()
def account() -> None:
    """Manage accounts."""


@account.command()
def add() -> None:
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


@account.command("list")
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


if __name__ == "__main__":
    cli()
