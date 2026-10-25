from bot.db import MIGRATIONS, Database


async def test_migrations_run_once(tmp_path):
    db = Database(tmp_path / "bot.db")
    await db.connect()
    cur = await db.conn.execute("PRAGMA user_version")
    assert (await cur.fetchone())[0] == len(MIGRATIONS)
    assert await db.migrate() == 0
    await db.close()

    # Reopening an existing database must not re-run anything.
    db = Database(tmp_path / "bot.db")
    await db.connect()
    assert await db.migrate() == 0
    await db.close()


async def test_settings(tmp_path):
    db = Database(tmp_path / "bot.db")
    await db.connect()
    assert await db.get_setting(1, "prefix", "!") == "!"
    await db.set_setting(1, "prefix", "?")
    await db.set_setting(1, "prefix", "$")
    assert await db.get_setting(1, "prefix") == "$"
    assert await db.get_setting(2, "prefix") is None
    await db.close()
