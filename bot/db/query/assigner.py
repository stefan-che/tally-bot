from sqlalchemy.sql.expression import select, delete
from sqlalchemy.orm import joinedload, selectinload
from ..models.assigner import Assigner
from db import EUserRole

# * get Group Assigner
async def get_assigner_by_user_and_group_id(session, user_id, group_id):
    query = select(Assigner).where(Assigner.user_id == user_id, Assigner.group_id == group_id)
    res = await session.execute(query)
    return res.scalars().first()

async def create_assigner(session, user_id, group_id, role=EUserRole.USER):
    new_assigner = Assigner(user_id=user_id, group_id=group_id, role=role)
    session.add(new_assigner)
    await session.commit()
    return new_assigner

async def delete_assigner_by_user_and_group_id(session, user_id, group_id):
    query = select(Assigner).where(Assigner.user_id == user_id, Assigner.group_id == group_id)
    res = await session.execute(query)
    assigner = res.scalars().first()
    await session.delete(assigner)
    await session.commit()

async def delete_assigners_by_user_id(session, user_id):
    # Delete all assigners for the user first
    await session.execute(
        delete(Assigner).where(Assigner.user_id == user_id)
    )

async def get_assigners_by_group_id(session, group_id, populateUser=False):
    query = select(Assigner).where(Assigner.group_id == group_id)
    if populateUser:
        query = query.options(selectinload(Assigner.user))
    res = await session.execute(query)
    return res.scalars().all()

async def get_assigners_by_user_id(session, user_id):
    query = select(Assigner).where(Assigner.user_id == user_id)
    res = await session.execute(query)
    return res.scalars().all()