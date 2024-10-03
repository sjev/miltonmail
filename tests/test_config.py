from pathlib import Path
import miltonmail.config


def test_config_path() -> None:
    assert miltonmail.config.CONFIG_PATH == Path.home() / ".config" / "milton"
    # assert miltonmail.config.CONFIG_PATH.exists()
