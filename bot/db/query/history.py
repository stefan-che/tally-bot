from sqlalchemy import select, desc, func
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from db.query.group import get_group_by_tg_id
from .. import Account, History

async def get_all_histories(session: AsyncSession):
    query = select(History).order_by(desc(History.time))
    res = await session.execute(query)

    return res.scalars().all()

async def get_all_histories_by_chat_id(session: AsyncSession, chat_id, populate=[]):
    group = await get_group_by_tg_id(session, chat_id)
    query = select(History).where(
        History.group_id == group.id
    ).order_by(desc(History.time))
    
    # Add population of related entities based on the `populate` parameter
    for relation in populate:
        if relation == "user":
            query = query.options(joinedload(History.user))
        elif relation == "account":
            query = query.options(joinedload(History.account))
        elif relation == "group":
            query = query.options(joinedload(History.group))
    
    res = await session.execute(query)

    return res.scalars().all()

async def get_all_histories_by_chat_id_currency(session: AsyncSession, chat_id, currency, populate=[]):
    group = await get_group_by_tg_id(session, chat_id)
    query = select(History).where(
        History.group_id == group.id, History.currency == currency
    ).order_by(desc(History.time))
    
    # Add population of related entities based on the `populate` parameter
    for relation in populate:
        if relation == "user":
            query = query.options(joinedload(History.user))
        elif relation == "account":
            query = query.options(joinedload(History.account))
        elif relation == "group":
            query = query.options(joinedload(History.group))

    res = await session.execute(query)

    return res.scalars().all()


async def get_all_histories_by_group_id(session: AsyncSession, group_id):
    query = select(History).where(
        History.group_id == group_id
    ).order_by(desc(History.time))

    res = await session.execute(query)

    return res.scalars().all()


async def get_last_message_ids(session: AsyncSession, group_ids) -> dict:
    """{group_id: message_id of the last operation} — for the "open chat" link (t.me/c/<id>/<msg>).
    Only for the groups on the current "get_all" page (a few dozen ids at most)."""
    group_ids = [g for g in group_ids if g is not None]
    if not group_ids:
        return {}
    query = (
        select(History.group_id, func.max(History.message_id))
        .where(History.group_id.in_(group_ids), History.message_id.isnot(None))
        .group_by(History.group_id)
    )
    return {gid: mid for gid, mid in (await session.execute(query)).all() if mid}
