"""Group -> supergroup migration tests on SQLite: cd bot && pytest tests/test_group_migration.py"""
import asyncio, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("BOT_TOKEN", "1:a")

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import UUID

@compiles(UUID, "sqlite")
def _uuid_sqlite(t, compiler, **kw):  # models use the uppercase UUID type (Postgres-only DDL)
    return "CHAR(32)"
from db import BaseModel, Group, Account, Assigner, History
import src.utils.group_migration as GM

engine = None
S = lambda: AsyncSession(engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def _sqlite_engine(monkeypatch):
    # A fresh engine per test (see test_group_delete.py), and session_maker is patched
    # only for the duration of the test.
    global engine
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    monkeypatch.setattr(GM, "session_maker", S)
    try:
        yield
    finally:
        await engine.dispose()


async def reset():
    async with engine.begin() as c:
        await c.run_sync(BaseModel.metadata.drop_all)
        await c.run_sync(BaseModel.metadata.create_all)


async def add(*objs):
    async with S() as s:
        s.add_all(objs); await s.commit()
    return objs


async def q(model, *where):
    async with S() as s:
        return (await s.execute(select(model).where(*where))).scalars().all()


async def test_move_in_place():
    await reset()
    g, = await add(Group(tg_id=-5, title="A"))
    await add(Account(group_id=g.id, user_id=-5, name="usdt", currency="USDT", amount=10),
              Assigner(user_id=1, group_id=g.id, role="ADMIN"),
              History(group_id=g.id, currency="USDT", count=10, comment="x"))
    r = await GM.migrate_group_tg_id(-5, -1005)
    assert r.status == "moved" and r.accounts_moved == 1, r
    [g2] = await q(Group)
    assert g2.id == g.id and g2.tg_id == -1005            # same row, new chat id
    assert (await q(Account))[0].user_id == -1005
    assert (await q(Assigner))[0].group_id == g.id        # admins untouched
    r2 = await GM.migrate_group_tg_id(-5, -1005)          # second service message
    assert r2.status == "already" and r2.ok


async def test_merge_into_existing_new_row():
    await reset()
    old, new = await add(Group(tg_id=-7, title="Old"), Group(tg_id=-1007, title=None))
    await add(Account(group_id=old.id, user_id=-7, name="usdt", currency="USDT", amount=5),
              Account(group_id=old.id, user_id=-7, name="rub", currency="RUB", amount=1),
              Account(group_id=new.id, user_id=-1007, name="rub", currency="RUB", amount=2),
              Assigner(user_id=1, group_id=old.id, role="ADMIN"),
              Assigner(user_id=2, group_id=old.id, role="USER"),
              Assigner(user_id=2, group_id=new.id, role="USER"),
              Assigner(user_id=3, group_id=old.id, role="SUPER_ADMIN"),
              Assigner(user_id=3, group_id=new.id, role="USER"),
              History(group_id=old.id, currency="USDT", count=5, comment="a"),
              History(group_id=old.id, currency="RUB", count=1, comment="b"))
    r = await GM.migrate_group_tg_id(-7, -1007)
    assert r.status == "merged" and r.accounts_moved == 1 and r.conflicts == ["RUB"], r
    usdt = (await q(Account, Account.currency == "USDT"))[0]
    assert usdt.group_id == new.id and usdt.user_id == -1007
    old_rub = (await q(Account, Account.group_id == old.id))
    assert [a.currency for a in old_rub] == ["RUB"]                    # conflict left, money not summed
    assert {h.currency for h in await q(History, History.group_id == new.id)} == {"USDT"}
    na = {a.user_id: a.role for a in await q(Assigner, Assigner.group_id == new.id)}
    assert na == {1: "ADMIN", 2: "USER", 3: "SUPER_ADMIN"}, na          # moved, no dups, higher role kept
    o, n = (await q(Group, Group.tg_id == -7))[0], (await q(Group, Group.tg_id == -1007))[0]
    assert o.status == "Inactive" and n.status == "Active" and n.title == "Old"


async def test_dry_run_and_concurrency():
    await reset()
    await add(Group(tg_id=-9, title="C"))
    r = await GM.migrate_group_tg_id(-9, -1009, dry_run=True)
    assert r.status == "moved" and (await q(Group))[0].tg_id == -9      # nothing written
    rs = await asyncio.gather(*[GM.migrate_group_tg_id(-9, -1009) for _ in range(5)])
    assert sorted(x.status for x in rs) == ["already"] * 4 + ["moved"], rs
    assert (await GM.migrate_group_tg_id(-1, -1001)).status == "not_found"
