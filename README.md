# discord-bot-starter

A discord.py template for bots you plan to keep running. It covers the parts every real bot needs and most tutorials skip: config that fails early, a database with migrations, errors users can understand, logs that do not fill the disk, clean shutdowns, Docker, tests and CI.

It ships with one complete feature, `/remind`, so you can see each pattern used for real before you delete it and build your own.

```console
$ python -m bot
22:45:36 INFO    bot.db: applying database migration 1
22:45:36 INFO    bot.db: applying database migration 2
22:45:36 INFO    bot.client: loaded bot.cogs.general
22:45:36 INFO    bot.client: loaded bot.cogs.owner
22:45:36 INFO    bot.client: loaded bot.cogs.reminders
22:45:37 INFO    bot.client: synced 3 commands to dev guild 123456789012345678
22:45:38 INFO    bot.client: ready as Starter#4821 (987654321098765432) in 1 servers
```

## What you get

| | |
|---|---|
| **Slash commands** | `/ping`, `/about`, and `/remind me`, `/remind list`, `/remind cancel` with autocomplete |
| **Cogs** | Every file in `bot/cogs/` loads on start. Copy `_template.py` to add one |
| **Command sync** | Instant sync to your test servers during development, global sync in production, or manual with `@Bot sync` |
| **Owner tools** | `@Bot sync` and `@Bot reload [cog]` to update without restarting. Hidden from everyone else |
| **Errors** | Cooldowns, missing permissions and bad input get a plain reply. Real bugs are logged with a short id that the user sees, so bug reports point at the exact traceback |
| **Database** | SQLite through aiosqlite with WAL mode and numbered migrations |
| **Background tasks** | Reminders are stored in the database and delivered by a loop, so a restart never loses one. A failing reminder never blocks the rest |
| **Config** | Environment variables or `.env`, checked at startup with clear messages |
| **Logging** | Console plus a rotating file capped at 30 MB |
| **Shutdown** | SIGTERM and Ctrl+C close the gateway and database cleanly |
| **Intents** | Default intents only. Nothing privileged is requested, so no portal toggles to forget |
| **Deploy** | Dockerfile (non-root, data volume) and docker-compose |
| **Quality** | 30 pytest tests that load every cog without connecting to Discord, ruff, and GitHub Actions on Python 3.10 to 3.13 |

## Quick start

1. Create an application at the [Discord developer portal](https://discord.com/developers/applications). Under **Bot**, reset and copy the token.
2. Under **OAuth2 > URL Generator**, tick `bot` and `applications.commands`, then the permissions your bot needs (for this template, **Send Messages** is enough). Open the generated URL to invite the bot to a test server.
3. Clone and configure:

```sh
git clone https://github.com/cipherhex09/discord-bot-starter my-bot
cd my-bot
cp .env.example .env
```

Put your token in `.env`. Add your test server id to `DEV_GUILD_IDS` so new commands show up instantly (turn on Developer Mode in Discord, then right click the server and pick **Copy Server ID**).

4. Run it:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m bot
```

Python 3.10 or newer is required.

### With Docker

```sh
docker compose up -d --build
docker compose logs -f
```

The database lives in `./data` on the host, so rebuilding the container keeps it.

## Configuration

| Variable | Required | What it does |
|---|---|---|
| `DISCORD_TOKEN` | yes | The bot token |
| `DEV_GUILD_IDS` | no | Comma separated server ids. Commands sync to these instantly instead of globally |
| `OWNER_IDS` | no | Comma separated user ids for owner commands. Defaults to the application owner |
| `DATABASE_PATH` | no | SQLite file, default `data/bot.db` |
| `LOG_LEVEL` | no | `DEBUG`, `INFO`, `WARNING` or `ERROR`. Default `INFO` |
| `LOG_DIR` | no | Folder for `bot.log`, default `logs`. Empty means console only |
| `SYNC_COMMANDS` | no | `false` to skip syncing on start and use `@Bot sync` instead |

Global commands can take up to an hour to appear in every server, and Discord rate limits syncing. That is why development syncs to specific servers. Remove `DEV_GUILD_IDS` when you deploy for real.

## Project layout

```
bot/
  __main__.py      entry point: config, logging, signals, start
  client.py        Bot class: loads cogs, syncs commands, owns the database
  config.py        environment parsing and validation
  db.py            SQLite connection and migrations
  errors.py        app command error handler and UserError
  log.py           console and rotating file logging
  cogs/
    general.py     /ping and /about
    reminders.py   /remind, a full example feature
    owner.py       @Bot sync and @Bot reload
    _template.py   copy this to start a new cog (not loaded)
  utils/
    duration.py    parses "1h30m", "2 days" and so on
tests/
```

## Adding a feature

Copy the template and rename the class:

```sh
cp bot/cogs/_template.py bot/cogs/polls.py
```

A few rules the template follows that save a lot of debugging:

- Discord waits 3 seconds for a reply. If a command does anything slow, call `await interaction.response.defer()` first and answer with `interaction.followup.send()`.
- To show the user an error, `raise UserError("message")`. The handler replies for you and nothing gets logged as a bug.
- Add tables by appending to `MIGRATIONS` in `bot/db.py`. Never edit a migration that has already run somewhere.
- Use `@app_commands.checks.cooldown()` on anything that writes to the database or calls an outside API.

After changing command names or options, run `@Bot reload` then `@Bot sync`, or just restart.

## Tests

```sh
pip install -e ".[dev]"
pytest
ruff check . && ruff format --check .
```

The tests start the bot's setup without logging in, so they check that every cog imports, every command registers, migrations apply once, and the reminder loop delivers and cleans up correctly.

## License

MIT
