"""Settings come from environment variables (or a .env file in development).

Everything is read and checked once at startup so a typo fails loudly before
the bot connects, not hours later inside a command.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(RuntimeError):
    pass


def _int_list(raw: str, name: str) -> tuple[int, ...]:
    out = []
    for part in raw.replace(" ", "").split(","):
        if not part:
            continue
        if not part.isdigit():
            raise ConfigError(f"{name} must be a comma separated list of ids, got {part!r}")
        out.append(int(part))
    return tuple(out)


@dataclass(frozen=True)
class Config:
    token: str
    # Slash commands sync to these guilds instantly. Leave empty in production
    # to sync globally (which can take up to an hour to show up everywhere).
    dev_guild_ids: tuple[int, ...] = ()
    owner_ids: tuple[int, ...] = ()
    database_path: Path = Path("data/bot.db")
    log_level: str = "INFO"
    log_dir: Path | None = Path("logs")
    sync_commands: bool = True
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> Config:
        if env is None:
            try:
                from dotenv import load_dotenv
            except ImportError:
                pass
            else:
                load_dotenv()
            env = dict(os.environ)

        token = env.get("DISCORD_TOKEN", "").strip()
        if not token:
            raise ConfigError("DISCORD_TOKEN is not set. Copy .env.example to .env and fill it in.")

        level = env.get("LOG_LEVEL", "INFO").upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
            raise ConfigError(f"LOG_LEVEL must be DEBUG, INFO, WARNING or ERROR, got {level!r}")

        log_dir = env.get("LOG_DIR", "logs").strip()
        return cls(
            token=token,
            dev_guild_ids=_int_list(env.get("DEV_GUILD_IDS", ""), "DEV_GUILD_IDS"),
            owner_ids=_int_list(env.get("OWNER_IDS", ""), "OWNER_IDS"),
            database_path=Path(env.get("DATABASE_PATH", "data/bot.db")),
            log_level=level,
            log_dir=Path(log_dir) if log_dir else None,
            sync_commands=env.get("SYNC_COMMANDS", "true").lower() not in {"0", "false", "no"},
        )
