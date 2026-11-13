from aiogram import types
from sqlalchemy import insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import session_maker, User, EUserStatus, EGroupType
from db.query.user import get_user_by_id, get_user_by_username

from app.utils import visualise
from src.utils.telegram import answer
from src.keyboards.mainMenu import get_main_keyboard
from src import answer


async def start(msg: types.Message):
    keyboard = await get_main_keyboard(msg)
    user_id = msg.from_user.id
    chat_type = EGroupType.get_group_type_from_msg(msg)

    async with session_maker() as session:
        session: AsyncSession
        async with session.begin():
            # `Find User by user.id

            user = await get_user_by_id(session, user_id)
            if not user:
                user = await get_user_by_username(session, msg.from_user.username.lower())
            
            if not user:
                if chat_type == EGroupType.GROUP:
                    return await answer(msg, f"{msg.from_user.username}, you do not have access to edit the books in groups")
                else:
                    return await answer(msg, f"{msg.from_user.username}, you do not have access to edit the books")
            
            if user.status == EUserStatus.NEW:
                print(f"USER: {user} - CHANGING STATUS TO ACTIVE")
                user.status = EUserStatus.ACTIVE;

            if user.name != msg.from_user.username and msg.from_user.username:
                user.name = msg.from_user.username.lower()
                
            await session.commit()

            visualise(user.__dict__, "USER")

    # `Greating message.
    await answer(msg, f'{msg.from_user.username}, welcome', reply_markup=keyboard)