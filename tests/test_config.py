import os
import base64
from pathlib import Path

import pytest

from miltonmail import config

os.environ["MILTON_PASS"] = "mysecretpassphrase"


os.system("rm -rf /tmp/milton")


def test_config_path() -> None:
    """Test if the configuration path is correctly set."""
    assert config.CONFIG_PATH == Path.home() / ".config" / "milton"


def test_config_file_not_found() -> None:
    """Test if the config file raises FileNotFoundError when not present."""

    # Temporarily change location of config data to /tmp
    config.CONFIG_PATH = Path("/tmp/milton")
    pth = Path(config.CONFIG_PATH)

    # Ensure the directory exists
    pth.mkdir(parents=True, exist_ok=True)

    # Ensure get_config raises FileNotFoundError if no config exists
    with pytest.raises(FileNotFoundError):
        config.get_config()


def test_save_and_get_config() -> None:
    """Test saving and loading configuration."""

    # Temporarily change location of config data to /tmp
    config.CONFIG_PATH = Path("/tmp/milton")
    pth = Path(config.CONFIG_PATH)

    # Ensure the directory exists
    pth.mkdir(parents=True, exist_ok=True)

    # Define account data
    test_account = config.add_account(
        name="Test Account",
        server="imap.test.com",
        username="test_user",
        password="test_password",
        port=993,
    )

    # Create Config object and save it
    config_data = config.Config(accounts=[test_account])
    config.save_config(config_data)

    # Check if the config file is saved correctly
    assert (pth / "config.json").exists()

    # Retrieve the config and check if the data matches
    loaded_config = config.get_config()

    assert len(loaded_config.accounts) == 1
    loaded_account = loaded_config.accounts[0]

    assert loaded_account.name == "Test Account"
    assert loaded_account.server == "imap.test.com"
    assert loaded_account.username == "test_user"
    assert loaded_account.port == 993


def test_account_salt_generation() -> None:
    """Test if salt is generated correctly and saved."""

    # Generate an account and verify salt is created
    test_account = config.add_account(
        name="Salt Test",
        server="imap.test.com",
        username="test_user",
        password="test_password",
        port=993,
    )

    # Salt should be 16 bytes
    assert isinstance(test_account.salt, bytes)
    assert len(test_account.salt) == 16

    # Verify that the salt is correctly base64-encoded in the dict representation
    account_dict = test_account.to_dict()
    assert "salt" in account_dict

    # Base64-encoded salt should decode back to the original 16-byte salt
    decoded_salt = base64.b64decode(account_dict["salt"])
    assert decoded_salt == test_account.salt


def test_saving_loading_with_salt() -> None:
    """Test if saving and loading an account with a salt works properly."""

    # Temporarily change location of config data to /tmp
    config.CONFIG_PATH = Path("/tmp/milton")
    pth = Path(config.CONFIG_PATH)
    pth.mkdir(parents=True, exist_ok=True)

    # Create account with generated salt
    test_account = config.add_account(
        name="Salted Account",
        server="imap.test.com",
        username="test_user",
        password="test_password",
        port=993,
    )

    # Create Config object and save it
    config_data = config.Config(accounts=[test_account])
    config.save_config(config_data)

    # Load config and verify salt is correctly retrieved and used
    loaded_config = config.get_config()
    loaded_account = loaded_config.accounts[0]

    assert loaded_account.name == "Salted Account"
    assert loaded_account.salt == test_account.salt
