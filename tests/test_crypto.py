import os
import pytest

from miltonmail import crypto

PASS = "mysecretpassphrase"


def test_phrase() -> None:

    # unset the passphrase
    os.environ["MILTON_PASS"] = ""

    with pytest.raises(ValueError):
        crypto.get_passphrase()

    # set the passphrase
    os.environ["MILTON_PASS"] = PASS

    assert crypto.get_passphrase() == PASS


def test_encrypt_decrypt() -> None:
    os.environ["MILTON_PASS"] = PASS

    password = "mysecretpassword"
    encrypted_password, salt = crypto.encrypt_password(password)

    assert password != encrypted_password
    assert password == crypto.decrypt_password(encrypted_password, salt)
