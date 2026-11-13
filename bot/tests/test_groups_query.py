"""SQL for /groups (has/has-not filters, sorting, NULLs last) on SQLite: cd bot && pytest tests/test_groups_query.py"""
import datetime, os, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("BOT_TOKEN", "1:a")

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import UUID

@compiles(UUID, "sqlite")
def _uuid_sqlite(t, compiler, **kw):  # models use the uppercase UUID type (Postgres-only DDL)
    return "CHAR(32)"
from db import BaseModel, Group, Account, Assigner
from db.query.group import get_groups_page, count_groups_filtered

engine = None


@pytest.fixture(autouse=True)
async def _sqlite_engine():
    # A fresh engine per test (see test_group_delete.py).
    global engine
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    try:
        yield
    finally:
        await engine.dispose()


S = lambda: AsyncSession(engine, expire_on_commit=False)
D = datetime.datetime


async def seed():
    async with engine.begin() as c:
        await c.run_sync(BaseModel.metadata.drop_all)
        await c.run_sync(BaseModel.metadata.create_all)
    async with S() as s:
        # B: 2 users, 1 account, old;  A: 0/2, new;  C: 1/0, no date;  D: 0/0, no date
        b, a, c, d = (Group(tg_id=-2, title="B", created_at=D(2024, 1, 1)), Group(tg_id=-1, title="A", created_at=D(2025, 1, 1)),
                      Group(tg_id=-3, title="C"), Group(tg_id=-4, title="D"))
        s.add_all([b, a, c, d]); await s.flush()
        c.created_at = d.created_at = None  # the ORM default sets now; old groups have NULL
        s.add_all([Assigner(user_id=1, group_id=b.id, role="USER"), Assigner(user_id=2, group_id=b.id, role="USER"),
                   Assigner(user_id=1, group_id=c.id, role="USER"),
                   Account(group_id=b.id, user_id=-2, name="u", currency="USDT", amount=1),
                   Account(group_id=a.id, user_id=-1, name="u", currency="USDT", amount=1),
                   Account(group_id=a.id, user_id=-1, name="r", currency="RUB", amount=1)])
        await s.commit()


async def titles(**kw):
    async with S() as s:
        return [g.title for g, _, _ in await get_groups_page(s, 0, 10, **kw)]


async def test_sort_and_filters():
    await seed()
    assert await titles() == ["A", "B", "C", "D"]
    assert await titles(descending=True) == ["D", "C", "B", "A"]
    assert await titles(sort="users", descending=True) == ["B", "C", "D", "A"]   # 2,1,0,0 — tie broken by tg_id (-4 < -1)
    assert await titles(sort="users") == ["D", "A", "C", "B"]
    assert await titles(sort="accounts", descending=True) == ["A", "B", "D", "C"]
    assert await titles(sort="created") == ["B", "A", "D", "C"]                   # NULLs last
    assert await titles(sort="created", descending=True) == ["A", "B", "D", "C"]  # also when descending
    assert await titles(has_accounts=True) == ["A", "B"] and await titles(has_accounts=False) == ["C", "D"]
    assert await titles(has_users=True) == ["B", "C"] and await titles(has_users=False) == ["A", "D"]
    assert await titles(has_accounts=False, has_users=True) == ["C"]
    async with S() as s:
        assert await count_groups_filtered(s, has_users=False) == 2 and await count_groups_filtered(s) == 4
        rows = await get_groups_page(s, 0, 10, sort="users", descending=True)
        assert [(u, a) for _, u, a in rows] == [(2, 1), (1, 0), (0, 0), (0, 2)]
    async with S() as s:  # a new group without an explicit date gets one (ORM default)
        g = Group(tg_id=-9, title="N"); s.add(g); await s.commit()
        assert g.created_at is not None
