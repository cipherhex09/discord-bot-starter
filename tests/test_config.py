from pathlib import Path

import pytest

from bot.config import Config, ConfigError


def test_minimal():
    c = Config.from_env({"DISCORD_TOKEN": "abc"})
    assert c.token == "abc"
    assert c.dev_guild_ids == ()
    assert c.database_path == Path("data/bot.db")
    assert c.sync_commands is True


def test_full():
    c = Config.from_env(
        {
            "DISCORD_TOKEN": " abc ",
            "DEV_GUILD_IDS": "1, 2,",
            "OWNER_IDS": "42",
            "LOG_LEVEL": "debug",
            "LOG_DIR": "",
            "SYNC_COMMANDS": "false",
        }
    )
    assert c.token == "abc"
    assert c.dev_guild_ids == (1, 2)
    assert c.owner_ids == (42,)
    assert c.log_level == "DEBUG"
    assert c.log_dir is None
    assert c.sync_commands is False


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"DISCORD_TOKEN": ""},
        {"DISCORD_TOKEN": "x", "DEV_GUILD_IDS": "abc"},
        {"DISCORD_TOKEN": "x", "LOG_LEVEL": "loud"},
    ],
)
def test_errors(env):
    with pytest.raises(ConfigError):
        Config.from_env(env)
