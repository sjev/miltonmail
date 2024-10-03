import os
import pytest

from miltonmail import crypto


def test_phrase() -> None:
    with pytest.raises(ValueError):
        crypto.get_passphrase()

    # set the passphrase
    os.environ["MILTON_PASS"] = "mysecretpassphrase"

    assert crypto.get_passphrase() == "mysecretpassphrase"
