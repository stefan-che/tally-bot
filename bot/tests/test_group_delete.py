"""Group deletion with confirmation: cd bot && pytest tests/test_group_delete.py

Pure functions (callback_data, texts) + bulk delete on SQLite (FKs are not enforced there, so we check
that deletion is explicit and does not touch another group).
"""
import os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("BOT_TOKEN", "1:a")

import pytest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import UUID

@compiles(UUID, "sqlite")
def _uuid_sqlite(t, compiler, **kw):  # models use the uppercase UUID type (Postgres-only DDL)
    return "CHAR(32)"
from db import BaseModel, Group, Account, Assigner, History, AccountWallet, BlockchainHistory
from db.query.group import get_group_delete_stats, delete_group_with_data, lock_group_by_tg_id
import src.utils.group_delete as GD

engine = None


@pytest.fixture(autouse=True)
async def _sqlite_engine():
    # A fresh engine per test: the aiosqlite connection is bound to the test's event loop,
    # and a shared module-level engine across loops hung the full pytest run.
    global engine
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    try:
        yield
    finally:
        await engine.dispose()


S = lambda: AsyncSession(engine, expire_on_commit=False)


# ---------- pure functions ----------

def test_callback_roundtrip():
    for action in (GD.CONFIRM, GD.CANCEL):
        for tg_id in (-1001234567890, -5, 42):
            data = GD.build_gdel_callback(action, tg_id)
            assert len(data.encode("utf-8")) <= 64
            assert GD.is_gdel_callback(data) and GD.parse_gdel_callback(data) == (action, tg_id)
    assert GD.build_gdel_callback("y", -100) == "gdel:y:-100"


def test_callback_garbage():
    for bad in (None, "", "gdel:", "gdel:x:1", "gdel:y:", "gdel:y:abc", "gdel:y:1:2", "grp:aaa:1", "gdel:y"):
        assert GD.parse_gdel_callback(bad) is None, bad
    assert not GD.is_gdel_callback("grp:aaaana:1") and not GD.is_gdel_callback(None)


def test_fmt_balance():
    assert GD.fmt_balance(1234567.5) == "1’234’567.5"
    assert GD.fmt_balance(10, 2) == "10"
    assert GD.fmt_balance(-0.125, 3) == "-0.125"
    assert GD.fmt_balance(None) == "0"
    assert GD.fmt_balance(1.5, None) == "1.5" and GD.fmt_balance(1.5, 0) == "2"


def test_summary_text():
    text = GD.build_delete_summary("<b>x</b> & y", -100, 3, [("USDT", 10.5, 2), ("<RUB>", -2, 2)], 7)
    assert "&lt;b&gt;x&lt;/b&gt; &amp; y" in text and "<b>x</b>" not in text      # html escaped
    assert "&lt;RUB&gt;" in text and "<code>-100</code>" in text
    assert "<b>Users:</b> 3" in text and "<b>Accounts:</b> 2" in text and "<b>Operations in history:</b> 7" in text
    assert "USDT: <code>10.5</code>" in text
    assert "permanently deletes" in text and "cannot be undone" in text
    many = [(f"C{i}", i, 2) for i in range(20)]
    text = GD.build_delete_summary(None, 1, 0, many, 0)
    assert "untitled" in text and text.count("  • ") == GD.ACCOUNTS_LIST_LIMIT and "and 5 more" in text
    assert GD.build_delete_result(2, 5, 1) == "Group deleted. Removed: 2 accounts, 5 operations, 1 users."


# ---------- bulk delete on SQLite ----------

async def reset():
    async with engine.begin() as c:
        await c.run_sync(BaseModel.metadata.drop_all)
        await c.run_sync(BaseModel.metadata.create_all)


async def add(*objs):
    async with S() as s:
        s.add_all(objs); await s.commit()
    return objs


async def count(model, *where):
    async with S() as s:
        return (await s.execute(select(func.count()).select_from(model).where(*where))).scalar()


async def seed(tg_id, title):
    g, = await add(Group(tg_id=tg_id, title=title))
    a1, a2 = await add(Account(group_id=g.id, user_id=tg_id, name="usdt", currency="USDT", amount=10),
                       Account(group_id=g.id, user_id=tg_id, name="rub", currency="RUB", amount=-3.5))
    w, = await add(AccountWallet(account_id=a1.id, wallet_address=f"T{tg_id}", network="tron"))
    await add(Assigner(user_id=1, group_id=g.id, role="ADMIN"),
              Assigner(user_id=2, group_id=g.id, role="USER"),
              History(group_id=g.id, account_id=a1.id, currency="USDT", count=10, comment="x"),
              History(group_id=g.id, currency="RUB", count=1, comment="by group only"),
              History(group_id=None, account_id=a2.id, currency="RUB", count=2, comment="by account only"),
              BlockchainHistory(group_id=g.id, account_id=a1.id, wallet_id=w.id, currency="USDT", count=1,
                                comment="bc", txid=f"tx{tg_id}a"),
              BlockchainHistory(group_id=None, account_id=None, wallet_id=w.id, currency="USDT", count=1,
                                comment="bc wallet only", txid=f"tx{tg_id}b"))
    return g


async def test_bulk_delete_isolated():
    await reset()
    a = await seed(-1, "A")
    b = await seed(-2, "B")
    await add(History(group_id=None, account_id=None, currency="X", count=1, comment="orphan"))

    async with S() as s:
        users, accounts, ops = await get_group_delete_stats(s, a.id)
    assert users == 2 and ops == 3 and sorted(accounts) == [("RUB", -3.5, 2), ("USDT", 10.0, 2)], (users, accounts, ops)

    async with S() as s:
        async with s.begin():
            g = await lock_group_by_tg_id(s, -1)
            result = await delete_group_with_data(s, g.id)
    assert result == {"accounts": 2, "operations": 3, "users": 2}, result

    # A — everything deleted
    assert await count(Group, Group.id == a.id) == 0
    assert await count(Account, Account.group_id == a.id) == 0
    assert await count(Assigner, Assigner.group_id == a.id) == 0
    assert await count(History, History.group_id == a.id) == 0
    assert await count(History, History.comment == "by account only", History.currency == "RUB") == 1  # this one belongs to B
    # B — untouched
    assert await count(Group, Group.id == b.id) == 1
    assert await count(Account, Account.group_id == b.id) == 2
    assert await count(Assigner, Assigner.group_id == b.id) == 2
    assert await count(History) == 3 + 1                    # 3 operations of B + orphan
    assert await count(AccountWallet) == 1 and await count(BlockchainHistory) == 2
    async with S() as s:
        assert (await get_group_delete_stats(s, b.id))[2] == 3

    # repeated confirmation — the group is already gone
    async with S() as s:
        async with s.begin():
            assert await lock_group_by_tg_id(s, -1) is None
            assert await delete_group_with_data(s, a.id) is None
