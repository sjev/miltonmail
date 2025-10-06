# MiltonMail

A command-line tool for managing your email accounts and automating the download of email attachments.

## Features

*   Connect to your email accounts using IMAP.
*   Add and manage multiple email accounts.
*   List folders in your email account.
*   Download only the attachments from your emails, not the entire message.
*   Securely store your account passwords using encryption.

## Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/miltonmail.git
    ```
2.  Install the dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

### Configuration File

MiltonMail stores its configuration in `~/miltonmail/config.json`. This file contains your account information, including your IMAP server, username, and encrypted password.

You can add accounts to this file using the `add-account` command.

### Environment Variables

MiltonMail uses the following environment variables:

*   `MILTON_PASS`: Your passphrase for encrypting and decrypting your account passwords.
*   `MILTON_ACCOUNT`: The name of the account you want to use.

## Usage

### `info`

Displays configuration information, including the path to the configuration file and the current account.

```bash
python -m miltonmail.cli info
```

### `add-account`

Interactively adds a new email account to your configuration.

```bash
python -m miltonmail.cli add-account
```

### `show accounts`

Lists all the accounts in your configuration.

```bash
python -m miltonmail.cli show accounts
```

### `show folders`

Lists all the folders in the current account.

```bash
python -m miltonmail.cli show folders
```

### `get attachments`

Downloads attachments from a specified folder in the current account. This command only downloads the attachments, not the email messages themselves.

```bash
python -m miltonmail.cli get attachments <folder>
```

You can also specify a cutoff date to only download attachments from emails received after that date:

```bash
python -m miltonmail.cli get attachments <folder> --cutoff-date YYYYMMDD
```

## Development


1. develop and test in devcontainer (VSCode)
2. use `invoke` for local devops actions

## Tooling

* Automation: `invoke` - run `invoke -l` to list available commands. (uses `tasks.py`)
* Verisoning : `setuptools_scm`
* Linting and formatting : `ruff`
* Typechecking: `mypy`
