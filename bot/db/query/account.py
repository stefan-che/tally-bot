from typing import Optional
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from .. import Account

async def get_all_accounts(session: AsyncSession):
    user_accounts_query = select(Account).order_by(desc(Account.amount))
    res = await session.execute(user_accounts_query)

    return res.scalars().all()

async def get_all_accounts_with_groups(session: AsyncSession):
    """All accounts plus their groups in one extra query (no lazy loading in async)."""
    query = select(Account).options(selectinload(Account.group)).order_by(desc(Account.amount))
    return (await session.execute(query)).scalars().all()


async def get_accounts_by_user_id(session: AsyncSession, user_id):
    user_accounts_query = select(Account).where(
        Account.user_id == user_id
    ).order_by(desc(Account.amount))
    res = await session.execute(user_accounts_query)

    return res.scalars().all()


async def get_account_by_user_id_currency(session: AsyncSession, user_id, currency):
    user_accounts_query = select(Account).where(
        Account.user_id == user_id, Account.currency == currency
    )
    res = await session.execute(user_accounts_query)
    return res.scalars().first()


async def get_account_by_chat_id_and_user_id(session: AsyncSession, chat_id, acc_name):
    query = select(Account).where(
                    # TODO - change to Account.group_id == chat_id
                    Account.user_id == chat_id, # user_id field deprecated for chat_id
                    Account.currency == acc_name.lower()
                )
    return (await session.execute(query)).scalars().one_or_none()


async def get_accounts_paginated(
    session: AsyncSession,
    page: int = 1,
    per_page: int = 20,
    user_id=None,
    group_id=None,
):
    offset = (page - 1) * per_page

    count_q = select(func.count()).select_from(Account)
    data_q = select(Account)

    if user_id is not None:
        count_q = count_q.where(Account.user_id == user_id)
        data_q = data_q.where(Account.user_id == user_id)
    if group_id is not None:
        count_q = count_q.where(Account.group_id == group_id)
        data_q = data_q.where(Account.group_id == group_id)

    total = (await session.execute(count_q)).scalar()
    accounts = (
        await session.execute(
            data_q.order_by(desc(Account.amount))
            .offset(offset)
            .limit(per_page)
            .options(selectinload(Account.wallets))
        )
    ).scalars().all()
    return accounts, total


async def get_account_by_id(session: AsyncSession, account_id: UUID) -> Optional[Account]:
    result = await session.execute(
        select(Account).where(Account.id == account_id).options(selectinload(Account.wallets))
    )
    return result.scalars().one_or_none()