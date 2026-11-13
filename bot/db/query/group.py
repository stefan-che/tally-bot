from sqlalchemy.sql import select, func
from sqlalchemy import desc
from sqlalchemy.orm import selectinload
from db import session_maker

from ..models.group import Group, EGroupStatus, EGroupType
from ..models.user import User
from ..models.assigner import Assigner


async def create_group(session, tg_id, chat_type=EGroupType.GROUP, title=None, status=EGroupStatus.ACTIVE):
    title = title[:31] if title else None # Limit title to 32 characters
    new_group = Group(tg_id=tg_id, title=title, chat_type=chat_type, status=status)
    session.add(new_group)
    await session.commit()
    return new_group

async def update_group(session, group_id, tg_id=None, title=None, chat_type=None, status=None):
    group = await get_group_by_id(session, group_id)
    title = title[:31] if title else None # Limit title to 32 characters
    
    if tg_id != group.tg_id:
        group.tg_id = tg_id
    if title != group.title:
        group.title = title
    if chat_type != group.chat_type:
        group.chat_type = chat_type
    if status != group.status:
        group.status = status
    await session.commit()
    return group

async def get_all_groups(session, populateAssigners=False, populateAccounts=False, populateUsers=False):
    query = select(Group)
    query = populate_query(query, populateAssigners, populateAccounts, populateUsers)
        
    res = await session.execute(query)
    return res.scalars().all()

def populate_query(query, populateAssigners=False, populateAccounts=False, populateUsers=False):
    if populateAssigners or populateUsers:
        if populateUsers:
            query = query.options(selectinload(Group.assigners).selectinload(Assigner.user))
        else:
            query = query.options(selectinload(Group.assigners))
    if populateAccounts:
        query = query.options(selectinload(Group.accounts))
    
    return query

async def get_group_by_id(session, group_id):
    query = select(Group).where(Group.id == group_id)
    res = await session.execute(query)
    return res.scalars().first()

async def get_group_by_tg_id(session, tg_id, populateUsers=False, populateAccounts=False, populateAssigners=False):
    query = select(Group).where(Group.tg_id == tg_id)
    query = populate_query(query, populateAssigners, populateAccounts, populateUsers)
    res = await session.execute(query)
    return res.scalars().first()

async def get_group_by_tg_id_with_session(tg_id, populateUsers=False, populateAccounts=False, populateAssigners=False):
    async with session_maker() as session:
        return await get_group_by_tg_id(session, tg_id, populateUsers, populateAccounts, populateAssigners)

async def get_groups_paginated(session, page: int = 1, per_page: int = 20, tg_id: int = None):
    offset = (page - 1) * per_page
    filters = []
    if tg_id is not None:
        filters.append(Group.tg_id == tg_id)
    count_query = select(func.count()).select_from(Group)
    if filters:
        count_query = count_query.where(*filters)
    total = (await session.execute(count_query)).scalar()
    query = select(Group).order_by(desc(Group.tg_id)).offset(offset).limit(per_page)
    if filters:
        query = query.where(*filters)
    groups = (await session.execute(query)).scalars().all()
    return groups, total

# * Get group with users
async def get_group_with_assigners(session, group_id):
    query = select(Group).where(Group.id == group_id).options(selectinload(Group.assigners))
    res = await session.execute(query)
    return res.scalars().first()


# * /groups in a private chat: filters + page + counters in SQL (no lazy load → no MissingGreenlet)
def _groups_filters(search=None, status=None, chat_type=None, has_accounts=None, has_users=None):
    """search — title substring (case-insensitive) or tg_id; status/chat_type — EGroupStatus/EGroupType values.
    has_accounts/has_users: True — has some, False — has none, None — no filter."""
    from sqlalchemy import or_, cast, String, exists
    from ..models.account import Account

    filters = []
    if search:
        filters.append(or_(
            Group.title.icontains(search, autoescape=True),
            cast(Group.tg_id, String).contains(search, autoescape=True),
        ))
    if status:
        filters.append(Group.status == status)
    if chat_type:
        filters.append(Group.chat_type == chat_type)
    if has_accounts is not None:
        cond = exists().where(Account.group_id == Group.id)
        filters.append(cond if has_accounts else ~cond)
    if has_users is not None:
        cond = exists().where(Assigner.group_id == Group.id)
        filters.append(cond if has_users else ~cond)
    return filters


async def count_groups_filtered(session, search=None, status=None, chat_type=None, has_accounts=None,
                                has_users=None) -> int:
    filters = _groups_filters(search, status, chat_type, has_accounts, has_users)
    return (await session.execute(select(func.count()).select_from(Group).where(*filters))).scalar() or 0


async def get_groups_page(session, offset: int = 0, limit: int = 10, search=None, status=None,
                          chat_type=None, has_accounts=None, has_users=None, sort="name", descending=False):
    """-> [(group, users_count, accounts_count), ...] — one page.

    sort: name | users | accounts | created; NULLs last in either direction, ties broken by tg_id.
    """
    from ..models.account import Account

    filters = _groups_filters(search, status, chat_type, has_accounts, has_users)
    users_count = (select(func.count(Assigner.id)).where(Assigner.group_id == Group.id)
                   .correlate(Group).scalar_subquery())
    accounts_count = (select(func.count(Account.id)).where(Account.group_id == Group.id)
                      .correlate(Group).scalar_subquery())
    key = {"users": users_count, "accounts": accounts_count, "created": Group.created_at}.get(sort, Group.title)
    query = (
        select(Group, users_count, accounts_count)
        .where(*filters)
        .order_by((key.desc() if descending else key.asc()).nulls_last(), Group.tg_id)
        .offset(offset).limit(limit)
    )
    rows = (await session.execute(query)).all()
    return [(g, u or 0, a or 0) for g, u, a in rows]


def _group_history_filter(group_id):
    """Group operations: by group_id or by its accounts (old records may have an empty group_id)."""
    from sqlalchemy import or_
    from ..models.account import Account
    from ..models.history import History

    account_ids = select(Account.id).where(Account.group_id == group_id)
    return or_(History.group_id == group_id, History.account_id.in_(account_ids))


async def get_group_delete_stats(session, group_id):
    """-> (users_count, [(currency, amount, decimal), ...], operations_count) — for the delete confirmation."""
    from ..models.account import Account
    from ..models.history import History

    users = (await session.execute(
        select(func.count(Assigner.id)).where(Assigner.group_id == group_id))).scalar() or 0
    accounts = (await session.execute(
        select(Account.currency, Account.amount, Account.decimal)
        .where(Account.group_id == group_id).order_by(Account.currency))).all()
    operations = (await session.execute(
        select(func.count(History.id)).where(_group_history_filter(group_id)))).scalar() or 0
    return users, [tuple(a) for a in accounts], operations


async def delete_group_with_data(session, group_id) -> dict | None:
    """Delete the group and everything it owns: history, blockchain history, wallets, accounts, assignments. Bulk delete, no ORM cascades.

    The caller manages the transaction. -> {"accounts", "operations", "users"}, or None if the group is already gone.
    """
    from sqlalchemy import delete, or_
    from ..models.account import Account
    from ..models.account_wallet import AccountWallet
    from ..models.blockchain_history import BlockchainHistory
    from ..models.history import History

    account_ids = select(Account.id).where(Account.group_id == group_id)
    wallet_ids = select(AccountWallet.id).where(AccountWallet.account_id.in_(account_ids))
    opts = dict(execution_options={"synchronize_session": False})

    operations = (await session.execute(
        delete(History).where(_group_history_filter(group_id)), **opts)).rowcount
    await session.execute(delete(BlockchainHistory).where(or_(
        BlockchainHistory.group_id == group_id,
        BlockchainHistory.account_id.in_(account_ids),
        BlockchainHistory.wallet_id.in_(wallet_ids),
    )), **opts)
    await session.execute(delete(AccountWallet).where(AccountWallet.account_id.in_(account_ids)), **opts)
    accounts = (await session.execute(delete(Account).where(Account.group_id == group_id), **opts)).rowcount
    users = (await session.execute(delete(Assigner).where(Assigner.group_id == group_id), **opts)).rowcount
    deleted = (await session.execute(delete(Group).where(Group.id == group_id), **opts)).rowcount
    if not deleted:
        return None
    return {"accounts": accounts, "operations": operations, "users": users}


async def lock_group_by_tg_id(session, tg_id) -> Group | None:
    """SELECT ... FOR UPDATE: two concurrent "Yes, delete" clicks do not delete twice (SQLite has no locking)."""
    return (await session.execute(select(Group).where(Group.tg_id == tg_id).with_for_update())).scalars().first()
