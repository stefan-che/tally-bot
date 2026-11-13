"""Group -> supergroup migration (Telegram changes chat_id).

The group identity in our DB is Group.id (UUID); tg_id is just the current chat id.
So a migration either:
  * re-points the existing Group row to the new tg_id (no new row -> assigners,
    accounts and histories stay attached automatically), or
  * if a row for the new tg_id already exists (someone created it after the
    migration), merges the old row into it.

Idempotent and serialized: Telegram delivers two service messages per migration
(migrate_to_chat_id in the old chat, migrate_from_chat_id in the new one), and a
shared folder link migrates dozens of groups at once. Both paths may call this;
the second call is a no-op.
"""
import asyncio
from dataclasses import dataclass, field

from colorama import Fore
from sqlalchemy import select, update

from db import session_maker, Account, Group, EGroupStatus
from db.models.assigner import Assigner
from db.models.history import History

_locks: dict[int, asyncio.Lock] = {}

ROLE_RANK = {"USER": 0, "ADMIN": 1, "SUPER_ADMIN": 2}


@dataclass
class MigrationResult:
    old_id: int
    new_id: int
    status: str = "noop"  # moved | merged | already | not_found | error
    accounts_moved: int = 0
    assigners_moved: int = 0
    # currencies present in both groups: left on the old (inactive) group, needs a human
    conflicts: list = field(default_factory=list)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status in ("moved", "merged", "already")

    def summary(self) -> str:
        s = f"{self.old_id} -> {self.new_id}: {self.status}"
        if self.status in ("moved", "merged"):
            s += f" (accounts: {self.accounts_moved}, users: {self.assigners_moved})"
        if self.conflicts:
            s += f" ⚠️ currencies present in both groups, not merged: {', '.join(self.conflicts)}"
        if self.error:
            s += f" ❌ {self.error}"
        return s


def _rank(role) -> int:
    return ROLE_RANK.get(getattr(role, "value", role), 0)


def _lock_for(old_id: int) -> asyncio.Lock:
    lock = _locks.get(old_id)
    if lock is None:
        lock = _locks[old_id] = asyncio.Lock()
    return lock


async def migrate_group_tg_id(old_id: int, new_id: int, dry_run: bool = False) -> MigrationResult:
    res = MigrationResult(int(old_id), int(new_id))
    if res.old_id == res.new_id:
        res.status = "already"
        return res

    async with _lock_for(res.old_id):
        try:
            async with session_maker() as session:
                try:
                    await _migrate(session, res)
                    if dry_run:
                        await session.rollback()
                    else:
                        await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        except Exception as e:  # noqa: BLE001 - reported to caller
            res.status, res.error = "error", f"{type(e).__name__}: {e}"
            print(f"{Fore.RED}[group_migration] {res.summary()}{Fore.BLACK}")
            return res

    print(f"{Fore.LIGHTGREEN_EX}[group_migration] {res.summary()}{'(dry-run)' if dry_run else ''}{Fore.BLACK}")
    return res


async def _get_for_update(session, tg_id):
    q = select(Group).where(Group.tg_id == tg_id).with_for_update()
    return (await session.execute(q)).scalars().first()


async def _migrate(session, res: MigrationResult):
    old = await _get_for_update(session, res.old_id)
    new = await _get_for_update(session, res.new_id)

    if not old:
        res.status = "already" if new else "not_found"
        return

    # --- Simple case: just re-point the row ---------------------------------
    if not new:
        old.tg_id = res.new_id
        old.status = EGroupStatus.ACTIVE
        r = await session.execute(
            update(Account).where(Account.group_id == old.id).values(user_id=res.new_id)
        )
        res.accounts_moved = r.rowcount or 0
        res.status = "moved"
        return

    # --- Merge old row into the existing new row ----------------------------
    new_accounts = (await session.execute(select(Account).where(Account.group_id == new.id))).scalars().all()
    new_currencies = {a.currency for a in new_accounts}
    old_accounts = (await session.execute(select(Account).where(Account.group_id == old.id))).scalars().all()

    moved_currencies = []
    for acc in old_accounts:
        if acc.currency in new_currencies:
            # Money in both groups for the same currency: never auto-sum, leave for a human.
            res.conflicts.append(acc.currency)
            continue
        acc.group_id = new.id
        acc.user_id = res.new_id  # Account.user_id holds the chat id (legacy field)
        moved_currencies.append(acc.currency)
    res.accounts_moved = len(moved_currencies)

    # Histories follow their accounts; conflicting currencies stay with the old group.
    hist_q = update(History).where(History.group_id == old.id)
    if res.conflicts:
        hist_q = hist_q.where(History.currency.notin_(res.conflicts))
    await session.execute(hist_q.values(group_id=new.id))

    new_assigners = (await session.execute(select(Assigner).where(Assigner.group_id == new.id))).scalars().all()
    by_user = {a.user_id: a for a in new_assigners}
    old_assigners = (await session.execute(select(Assigner).where(Assigner.group_id == old.id))).scalars().all()
    for a in old_assigners:
        existing = by_user.get(a.user_id)
        if existing is None:
            a.group_id = new.id
            res.assigners_moved += 1
        elif _rank(a.role) > _rank(existing.role):
            existing.role = a.role  # keep the higher role

    if not new.title and old.title:
        new.title = old.title
    new.status = EGroupStatus.ACTIVE
    old.status = EGroupStatus.INACTIVE
    res.status = "merged"
