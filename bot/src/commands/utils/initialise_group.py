from aiogram import types
from db import EGroupType, session_maker, EGroupStatus
from db.query.group import get_group_by_tg_id, create_group


async def initialise_group(msg: types.Message):
    async with session_maker() as session:
        async with session.begin():
            group = await get_group_by_tg_id(session, msg.chat.id);
            if group:
                return await update_group_if_needed(msg, session, group);
            
            chat_type = EGroupType.get_group_type_from_msg(msg);
            
            if chat_type == EGroupType.PERSONAL:
                return await create_group(session, msg.chat.id, chat_type, msg.from_user.username);
            else:
                return await create_group(session, msg.chat.id, chat_type, msg.chat.title);
            

async def update_group_if_needed(msg: types.Message, session, group):
    chat_type = group.chat_type;
    changes = False;
    
    if chat_type == EGroupType.PERSONAL:
        if group.title != msg.from_user.username:
            group.title = msg.from_user.username
            changes = True;
    
    if chat_type == EGroupType.GROUP or chat_type == EGroupType.CHANNEL:
        print("[update_group_if_needed] chat_type", chat_type)
        title = msg.chat.title[:31];
        if group.title != title:
            group.title = title
            changes = True;
    
    if group.status == EGroupStatus.NEW:
        group.status = EGroupStatus.ACTIVE
        changes = True;
    
    if changes:
        await session.commit()
    
    return group