from sqlalchemy import select, desc
from aiogram import types
from db import session_maker, Account, User
from db.query.user import find_or_create_user, EUserRole, get_user_by_id, create_user
from db.query.assigner import get_assigner_by_user_and_group_id, create_assigner
from db.query.group import get_group_by_tg_id, create_group, EGroupType

from src.commands.utils.get_histories_mes import get_histories_message
from src.keyboards.histories_next_page import get_histories_next_inl_keyboard
from src.utils.telegram import answer
from ..utils.get_accounts_mes import get_accounts_message

# 
async def add_user(msg: types.Message):
    data = msg.text.strip().split()
    
    new_user_id = None
    try:
        if data[1].isdigit():
            new_user_id = int(data[1])
        else:
            return await answer(msg, "Invalid input: [userId] must be a number.")
    except Exception:
        return await answer(msg, "Check your input\n/add_user [user_id]")
    
    chat_id = msg.chat.id;
    is_group = msg.chat.type == "group" or msg.chat.type == "supergroup"
    is_personal = msg.chat.type == "private"
    
    if not is_group and not is_personal:
        return await answer(msg, "This command is only available in private chats or groups")
    
    async with session_maker() as session:
        async with session.begin():
            
            user = await find_or_create_user(session, new_user_id, username=msg.from_user.username);
            
            # * Private chat: add the user to the system
            if is_personal: 
                new_user = await get_user_by_id(session, new_user_id);
                if not new_user:
                    new_user = create_user(session, new_user_id, username=msg.from_user.username);
                    return await answer(msg, "User added")
                return await answer(msg, f"User already exists: {new_user.username} with role {new_user.role}")
            
            # * Group chat: add the user to the group
            group = await get_group_by_tg_id(session, chat_id);
            if not group:
                if not EUserRole.is_admin(user.role):
                    return await answer(msg, "The group has not been initialized. Contact an administrator")
                else:
                    chat_type = EGroupType.get_group_type_from_msg(msg);
                    title = EGroupType.get_group_title_from_msg(msg);
                    group = create_group(session, chat_id, chat_type, title=title);
                    
            assigner = await get_assigner_by_user_and_group_id(session, user.id, group.id)
            if assigner:
                return await answer(msg, "The user is already in this group")
            assigner = create_assigner(session, user.id, group.id)
            if user.name:
                return await answer(msg, f"User {user.name} added to the group")
            return await answer(msg, f"New user added to the group")
            
            
                    
        
