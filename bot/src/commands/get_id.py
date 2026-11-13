from aiogram import types
from sqlalchemy import insert, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import session_maker, User
from db.query.user import get_user_by_username

from app.utils import visualise
from src.utils.telegram import answer
from src.keyboards.mainMenu import get_main_keyboard
from src import answer


async def get_id(msg: types.Message):
    await answer(msg, f"USER ID: <code>{msg.from_user.id}</code>\nCHAT ID: <code>{msg.chat.id}</code>")