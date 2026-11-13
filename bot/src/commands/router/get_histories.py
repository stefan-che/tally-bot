from colorama import Fore
from aiogram import types
from src.utils.access import getRole
from myTypes.roles import Role
from db import session_maker, EGroupType, EUserRole, EUserStatus
from ..user.get import get_accounts as get_accounts_as_user
from ..user.get_histories import get_histories as get_histories_as_user
from ..admin.get_histories import get_histories as get_histories_as_admin

async def get_histories(msg: types.Message):

    data = msg.text.split(" ")
    currency = None
    if len(data) == 2:
        currency = data[1]
        
    chat_type = EGroupType.get_group_type_from_msg(msg);

    if chat_type == EGroupType.PERSONAL:
        print(f"GET HISTORIES: PERSONAL")
        await get_histories_as_admin(msg, msg.chat.id, currency) # Do only chat with bot, not in groups.
    else: 
        print(f"GET HISTORIES: CHAT")
        await get_histories_as_user(msg, msg.chat.id, currency) # Do only chat with bot, not in groups.
