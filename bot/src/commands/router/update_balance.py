from colorama import Fore
from aiogram import types
from src.utils.access import getRole
from myTypes.roles import Role
from ..user.update_balance import update_balance as update_balance_as_user
from ..admin.get import get_accounts as get_accounts_as_admin

async def update_balance(msg: types.Message):
    if await getRole(msg.from_user.id) == Role.OWNER and msg.from_user.id == msg.chat.id:
        await update_balance_as_user(msg) # Do only chat with bot, not in groups.
    else: 
        await update_balance_as_user(msg)