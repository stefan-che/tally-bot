from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from db import session_maker, EUserStatus, EUserRole, Assigner
from sqlalchemy.ext.asyncio import AsyncSession
from .. import User


def populate_user(query, populateAssigners=False, populateGroup=False):
    if populateGroup or populateAssigners:
        if populateGroup:
            query = query.options(selectinload(User.assigners).selectinload(Assigner.group))
        else:
            query = query.options(selectinload(User.assigners))
    return query

async def get_all_users(session: AsyncSession):
    user_accounts_query = select(User)
    res = await session.execute(user_accounts_query)

    return res.scalars().all()

async def find_or_create_user(session: AsyncSession, user_id, username=None, status=None, role=None) -> User:
    user = await get_user_by_id(session, user_id)
    if not user:
        user = await create_user(session, user_id, username, status, role)
    return user

async def create_user(session: AsyncSession, user_id, username=None, status=EUserStatus.NEW, role=EUserRole.USER) -> User:
    user = User(id=user_id, status=status, role=role, name=username)
    session.add(user)
    return user


async def update_user(session: AsyncSession, user_id, status=None, role=None, username=None) -> User:
    query = select(User).where(User.id == user_id)
    res = await session.execute(query)
    user = res.scalars().first()
    if status:
        user.status = status
    if role:
        user.role = role
    if username:
        user.name = username.lower()
    
    await session.commit()
    return user

async def get_user_by_id(session: AsyncSession, user_id, populateAssigners=False, popullateGroup=False) -> User:
    query = select(User).where(User.id == user_id)
    query = populate_user(query, populateAssigners, popullateGroup)
    res = await session.execute(query)

    return res.scalars().first()

async def get_user_by_id_with_session(user_id, populateAssigners=False, populateGroup=False) -> User:
    async with session_maker() as session:
        async with session.begin():
            return await get_user_by_id(session, user_id, populateAssigners=populateAssigners, popullateGroup=populateGroup)

async def get_user_by_username(session: AsyncSession, username: str, return_option="all") -> User:
    user_accounts_query = select(User).where(User.name == username.lower())
    res = await session.execute(user_accounts_query)

    return res.scalars().first()
