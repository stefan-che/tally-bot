from colorama import Fore
from aiogram import types
from db import EUserRole
from db.query.user import get_user_by_id_with_session
from ..user.get import get_accounts as get_accounts_as_user
from ..admin.get import get_accounts as get_accounts_as_admin

async def get_all_acc(msg: types.Message):
    user = await get_user_by_id_with_session(msg.from_user.id)
    

    if user and EUserRole.is_admin(user.role) and msg.from_user.id == msg.chat.id:
        await get_accounts_as_admin(msg) # Do only chat with bot, not in groups.
    else: 
        await msg.answer("You do not have permission to run this command.")