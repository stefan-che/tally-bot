from html import escape
from sqlalchemy import select, desc
from aiogram import types
from db import session_maker, Account, EGroupType
from db.query.user import get_all_users, get_user_by_id
from db.query.user import find_or_create_user, EUserRole, create_user
from db.query.assigner import get_assigner_by_user_and_group_id, create_assigner, delete_assigners_by_user_id
from db.query.group import get_group_by_tg_id, create_group
from src.utils.telegram import answer
from app.utils import visualise
from src.commands.utils.initialise_group import initialise_group
from ..utils.get_accounts_mes import get_accounts_message
from ..utils.get_users_mes import get_users_message, get_assigners_message

async def get_me(msg: types.Message):
    async with session_maker() as session:
        user = await get_user_by_id(session, msg.from_user.id, popullateGroup=True);
        if not user:
            return await answer(msg, "You are not in the database")
        
        visualise(user.__dict__, "USER")
        
        text = f"<b>System role:</b> '{user.role}'"
        if user.assigners:
            text += f"\n\nYou are a member of <b>{len(user.assigners)}</b> {'groups' if len(user.assigners) != 1 else 'group' }:"
            for (i, assigner) in enumerate(user.assigners):
                role = EUserRole.get_message_role(assigner.role);
                text += f"\n <code>[{i+1}] [{role}]</code> <b>{escape(str(assigner.group.title))}</b>"
            
        await answer(msg, text)

# # USERS
async def get_users(msg: types.Message):
    data = msg.text.strip().split()
    chat_type = EGroupType.get_group_type_from_msg(msg);
    
    async with session_maker() as session:
        if chat_type == EGroupType.PERSONAL:
            users = await get_all_users(session)

            if not users:
                return await answer(msg, "No users")
            
            reply_msg = get_users_message(users)

            await answer(msg, reply_msg)
        else:
            group = await get_group_by_tg_id(session, msg.chat.id, populateUsers=True)
            if not group:
                return await answer(msg, "Group not found")
            reply_msg = get_assigners_message(group.assigners, f'<b>Users of this group:</b>')
            await answer(msg, reply_msg)
    

async def create_user_cmd(msg: types.Message, role = EUserRole.USER):
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
            
            # * Private chat: add the user to the system
            if is_personal: 
                new_user = await get_user_by_id(session, new_user_id);
                if not new_user:
                    new_user = await create_user(session, new_user_id, role=role);
                    return await answer(msg, "User added")
                return await answer(msg, f"User already exists: '{new_user.name}' with role '{new_user.role}'")
            
            # * Group chat: add the user to the group
            else: 
                group = await initialise_group(msg);
                user = await find_or_create_user(session, new_user_id);
                print(f'[CREATE_USER]\nUSER: {user}\nGROUP: {group}')
                if not group:
                    if not EUserRole.is_admin(user.role):
                        return await answer(msg, "The group has not been initialized. Contact an administrator")
                    else:
                        chat_type = EGroupType.get_group_type_from_msg(msg);
                        title = EGroupType.get_group_title_from_msg(msg);
                        group = await create_group(session, chat_id, chat_type, title=title);
                        
                assigner = await get_assigner_by_user_and_group_id(session, user.id, group.id)
                if assigner:
                    if role != assigner.role and role != EUserRole.USER:
                        assigner.role = role
                        await session.commit()
                        return await answer(msg, f"Role of user {user.name} updated to '{role}'")
                    return await answer(msg, f"User {user.name} is already in this group")
                assigner = await create_assigner(session, user.id, group.id, role=role)
                if user.name:
                    return await answer(msg, f"User {user.name} added to the group")
                return await answer(msg, f"New user added to the group")

async def update_user_role(msg: types.Message):
    data = msg.text.strip().split()
    if len(data) == 3:
        role = EUserRole.get_valid_role(data[2])
        if not role:
            return await answer(msg, f"Role '{data[2]}' not found")
        
        try:
            user_id = int(data[1])
        except Exception:
            return await answer(msg, "Invalid input: user_id must be a number.")
        
        
        
        async with session_maker() as session:
            async with session.begin():
                user = await get_user_by_id(session, user_id)
                if not user:
                    return await answer(msg, f"User {user_id} not found")

                user.role = role
                await session.commit()

                await answer(msg, f"Role of user {user.id} {user.name} updated to '{role}'")
    else:
        await answer(msg, "Check your input:\n /update_role [user_id] [role]")


async def delete_user(msg: types.Message):
    data = msg.text.strip().split()
    chat_type = EGroupType.get_group_type_from_msg(msg);
    if len(data) == 2:
        try:
            user_id = int(data[1])
        except Exception:
            return await answer(msg, "Invalid input: user_id must be a number.")
        
        user = None;
        async with session_maker() as session:
            async with session.begin():
                if chat_type == EGroupType.PERSONAL:
                    user = await get_user_by_id(session, user_id)
                    if not user:
                        return await answer(msg, f"User not found")
                    
                    await delete_assigners_by_user_id(session, user.id)

                    await session.delete(user)
                    await answer(msg, f"User {user.id} {user.name} deleted")
                if chat_type == EGroupType.GROUP:
                    group = await get_group_by_tg_id(session, msg.chat.id)
                    assigner = await get_assigner_by_user_and_group_id(session, user_id, group.id)
                    if not assigner:
                        return await answer(msg, f"User {user_id} not found in the group")
                    await session.delete(assigner)
                    await answer(msg, f"User {user_id} removed from the group")

    else:
        await answer(msg, "Check your input:\n /delete_user [user_id]")



async def delete_user_accounts(msg: types.Message):
    data = msg.text.strip().split()
    if len(data) == 2:
        try:
            user_id = int(data[1])
        except Exception:
            return await answer(msg, "Invalid input: user_id must be a number.")
        

        async with session_maker() as session:
            async with session.begin():
                query = select(Account).where(Account.user_id == user_id)
                accounts = (await session.execute(query)).scalars().all()

                if not accounts:
                    return await answer(msg, f"User {user_id} has no accounts")

                for account in accounts:
                    await session.delete(account)

                await answer(msg, f"All accounts of user {user_id} deleted")
    else:
        await answer(msg, "Check your input:\n /delete_user <user_id>")
