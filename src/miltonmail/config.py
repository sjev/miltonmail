""" configuration stuff """

import os
import base64
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List

from miltonmail.crypto import decrypt_password, encrypt_password

# Path to the configuration file
DB_PATH = Path.home() / "miltonmail"


@dataclass
class Account:
    """Dataclass to hold account information, including encrypted password and salt."""

    name: str
    server: str
    username: str
    password: str  # Encrypted password (base64 encoded)
    salt: bytes  # Salt stored as bytes
    port: int = 993  # Default IMAP port

    def __post_init__(self) -> None:
        """Convert salt from base64 to bytes if necessary."""
        if isinstance(self.salt, str):
            self.salt = base64.b64decode(self.salt)

    def encrypt_password(self, plain_password: str) -> None:
        """Encrypt the plain password and store the encrypted password and salt."""
        encrypted_password, salt = encrypt_password(plain_password)
        self.password = encrypted_password.decode()  # Store as string for JSON
        self.salt = salt

    def decrypt_password(self) -> str:
        """Decrypt the password using the stored salt."""
        return decrypt_password(self.password.encode(), self.salt)

    def to_dict(self) -> dict:
        """Convert account object to a dictionary, encoding the salt as base64."""
        account_dict = asdict(self)
        account_dict["salt"] = base64.b64encode(self.salt).decode("utf-8")
        return account_dict


@dataclass
class Config:
    """Dataclass to hold all configuration data."""

    accounts: List[Account] = field(default_factory=list)

    @staticmethod
    def from_dict(config_dict: dict) -> "Config":
        """Converts a dictionary to a Config instance and decrypts passwords."""
        accounts = [Account(**account) for account in config_dict.get("accounts", [])]
        return Config(accounts=accounts)

    def get_account(self, name: str) -> Account:
        """Get an account by name."""
        for account in self.accounts:
            if account.name == name:
                return account
        raise ValueError(f"Account '{name}' not found.")

    def to_dict(self) -> dict:
        """Converts the Config instance back to a dictionary and encrypts passwords."""
        return {"accounts": [account.to_dict() for account in self.accounts]}


def get_config() -> Config:
    """Get the configuration from the configuration file."""
    with open(DB_PATH / "config.json", "r", encoding="utf8") as file:
        config_dict = json.load(file)
    return Config.from_dict(config_dict)


def save_config(config: Config) -> None:
    """Save the configuration to the configuration file."""
    DB_PATH.mkdir(parents=True, exist_ok=True)

    with open(DB_PATH / "config.json", "w", encoding="utf8") as file:
        json.dump(config.to_dict(), file, indent=4)


# Helper function to add an account
def add_account(
    name: str, server: str, username: str, password: str, port: int = 993
) -> Account:
    """Creates an Account with a generated salt and encrypts the password."""
    account = Account(
        name=name, server=server, username=username, password="", salt=b"", port=port
    )
    account.encrypt_password(password)  # Encrypt and store the password and salt
    return account


def get_current_account_name() -> str:
    """Get the name of the account to use."""
    account_name = os.getenv("MILTON_ACCOUNT")
    if account_name is None:
        raise ValueError("No account set. Set the MILTON_ACCOUNT environment variable.")
    return account_name


def get_current_account() -> Account:
    """Get the account to use."""
    account_name = get_current_account_name()
    config = get_config()
    return config.get_account(account_name)
