from aiogram import types
from ..user.add_tx import add_tx_to_account as add_tx_to_account_as_user
from src.commands.utils.initialise_group import initialise_group
from src.app.app_state import AppState
from db.query.user import get_user_by_id_with_session
from db.query.group import get_group_by_tg_id_with_session
from src.commands.utils.initialise_group import initialise_group
from db import EGroupType, session_maker, EUserRole, EUserStatus
from src import answer, reply

async def add_tx(msg: types.Message):
    chat_type = EGroupType.get_group_type_from_msg(msg)
    
    # /VALIDATION - Check if user is active
    user = await get_user_by_id_with_session(msg.from_user.id, populateGroup=True)
    if not user or user.status == EUserStatus.INACTIVE:
        return await reply(msg, "You are not allowed to add transactions in this bot");
    
    # /VALIDATION - Group
    # * GROUP - Check if user is in the group and group is initialised
    group = None
    if chat_type == EGroupType.GROUP:
        group = await get_group_by_tg_id_with_session(msg.chat.id, populateUsers=True)
        if not group:
            return await reply(msg, "The group is not active.\nContact an administrator to activate it");        
        
        super_admin =  EUserRole.is_super_admin(user.role);
        
        user_in_group = False;
        for assigner in user.assigners:
            if assigner.group_id == group.id:
                user_in_group = True;
                break;
        
        if not super_admin and not user_in_group:
            return await msg.answer("To add transactions in this group you must be a user of the group in the bot (not just a member of the Telegram chat).");
    
    
    # * PERSONAL - Initialise group
    elif chat_type == EGroupType.PERSONAL:
        group = await initialise_group(msg);
    
    else:
        return await reply(msg, "This chat is not supported");
    
    # $$ Add Transaction
    await add_tx_to_account_as_user(msg, user, group);