from colorama import Fore
from aiogram import types, Dispatcher, BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Awaitable, Any, Dict
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from db import session_maker, EGroupType, EUserRole, EUserStatus
from db.query.user import get_user_by_id_with_session, update_user
from db.query.group import get_group_by_tg_id
from src.app.app_state import AppState
from src.utils.optionalchain import optional_chain
from src import get_text_message, get_user_from_update, get_chat_from_update, answer, reply

from db.models.user import User  # Adjust the import according to your project structure

class GuardMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # The original update-guard body runs first (below). Its early
        # `return`s meant "allow -> continue to handler" in aiogram 2, and it
        # denies by raising (raise_unauthorized_exception). Extracting it into a
        # helper preserves that: normal completion falls through to the handler,
        # a raise propagates and stops processing.
        update = event
        await self._process_update(update, data)
        return await handler(event, data)

    async def _process_update(self, update: types.Update, data: dict):
        appState = AppState()

        textMessage = get_text_message(update);
        from_user = get_user_from_update(update);
        chat = get_chat_from_update(update);
        callbackQueryData = optional_chain(update, 'callback_query', 'data');
        message = update.message or optional_chain(update, 'callback_query', 'message');
        chat_type = EGroupType.get_group_type_from_msg(message);
        
        # * Group -> supergroup migration service messages: always let through, never
        #   answer "no access" (in the new supergroup the sender is GroupAnonymousBot).
        if update.message and (update.message.migrate_to_chat_id or update.message.migrate_from_chat_id):
            print(Fore.CYAN + f"[GUARD] Migration service message: {Fore.LIGHTGREEN_EX}'{update.message.migrate_from_chat_id or update.message.chat.id}' -> '{update.message.migrate_to_chat_id or update.message.chat.id}' {Fore.BLACK}");
            return;
        
        if not chat:
            print(Fore.LIGHTRED_EX + "[GUARD] Chat not found in the update")
            return;
        
        if not from_user:
            print(Fore.LIGHTRED_EX + "[GUARD] User not found in the update")
            await raise_unauthorized_exception(update, "User not found in the update, to identify the user.");
            return None;

        handler = None
        if textMessage: # If callback, need different handler
            handler = appState.get_handler_by_condition(textMessage);
        
        if handler and handler["is_public"]:
            print(Fore.GREEN + f"Public Handler: {Fore.LIGHTGREEN_EX}{handler}");
            return;
        
        # * Get User and Group
        user, group = None, None
        async with session_maker() as session:
            user = await get_user_by_id_with_session(from_user.id) # ! HERE IS THE ERROR
            group = await get_group_by_tg_id(session, chat.id, populateAssigners=True);
            print(Fore.BLUE + f"User: {Fore.LIGHTGREEN_EX}{user}");
            print(Fore.BLUE + f"Group: {Fore.LIGHTGREEN_EX}{group}");
        
        # * UnAuth users have access only to PUBLIC commands
        if not user:
            # Service events (someone joined/left) are not a command attempt:
            # stop processing silently instead of replying "no access" to the inviter.
            if is_member_service_message(update.message):
                print(Fore.LIGHTRED_EX + f"[Guard] Service message from unknown user {Fore.YELLOW}'{from_user.id}' skipped silently {Fore.BLACK}");
                raise Exception("User Unauthorized: service message from unknown user");
            if chat_type == EGroupType.GROUP:
                print(Fore.LIGHTRED_EX + f"[Guard] User is not found in the database {Fore.YELLOW}'{from_user.id}' {Fore.BLACK}");
                return await raise_unauthorized_exception(update, "You do not have access to edit the books in groups");
            else:
                return await raise_unauthorized_exception(update, "You do not have access to edit the books");
        
        if user.status == EUserStatus.NEW:
            print(Fore.LIGHTGREEN_EX + f"[Guard] User is not active {Fore.BLACK}");
            async with session_maker() as session:
                user = await update_user(session, user.id, status=EUserStatus.ACTIVE, username=from_user.username);
        
        # * SET DATA
        data["user"] = user
        
        # * GROUP ACCESS
        if chat_type == EGroupType.GROUP:
            have_group_access = await handle_group_access(update, group, user, handler);
            if have_group_access:
                return;
        else:
            have_private_access = await handle_private_access(update, user, handler);
            if have_private_access:
                print(Fore.LIGHTGREEN_EX + f"[Guard] User has private access {Fore.BLACK}");
                return;
        
        # * PRIVATE CHAT ACCESS
        if handler:
            print("handler::",handler)
            if not appState.is_user_has_private_access(user, handler):
                await raise_unauthorized_exception(update, "You do not have access to this command");
            
async def handle_group_access(update, group, user, handler):
    if group:
        callbackQueryData = optional_chain(update, 'callback_query', 'data');
        if callbackQueryData:
            if user.role and EUserRole.is_super_admin(user.role):  # as for commands: a super admin has access in any group
                return True;
            for assigner in group.assigners:
                if assigner.user_id == user.id:
                    return True;
            else:
                return await raise_unauthorized_exception(update, "You are not a user of this group");
        
        (has_access, errorOrSuccessMessage) = await is_assigner_has_access(handler, group, user);
        if not has_access:
            print(f"{Fore.BLUE}[Guard] {Fore.LIGHTRED_EX}User doesn't have group access {Fore.BLACK}");
            await raise_unauthorized_exception(update, errorOrSuccessMessage);
            return;
        elif errorOrSuccessMessage == "SKIP":
            return 
        else:
            print(f"{Fore.BLUE}[Guard] {Fore.LIGHTGREEN_EX}User has group access {Fore.BLACK}: {errorOrSuccessMessage}");
            return has_access;
        
async def handle_private_access(update, user, handler):
    appState = AppState()
    # IF GROUP NOT FOUND
    # check if user has access by roles
    # If no roles set, then give access to the user.
    if handler:
        if appState.is_user_has_private_access(user, handler):
            return (True, "User has access by roles")
        else:
            await raise_unauthorized_exception(update, "Access to this command in a private chat is restricted.");
            return False;
    else:
        return True;

async def is_assigner_has_access(handler, group, user):
    appState = AppState()
    
    if EUserRole.is_super_admin(user.role):
        return (True, "User is Super Admin")

    # System role rules, if any.
    if handler and handler["roles"]:
        if appState.is_user_has_access(user, handler):
            return (True, "User has access by roles")
    
    # Group role rules, if any.
    if handler and handler["group_roles"]:
        for assigner in group.assigners:
            if assigner.user_id == user.id:
                if EUserRole.has_roles_access(assigner.role, handler["group_roles"]):
                    return (True, "The user has access to this group")
                else:
                    print(Fore.LIGHTRED_EX + f"[Guard] User doesn't have group access by roles [{handler['group_roles']}] {Fore.BLACK}");
                    return (False, "This command is not available to you")
        else:
            print(Fore.LIGHTRED_EX + f"[Guard] User not found in group, restricted Access roles [{handler['group_roles']}] {Fore.BLACK}");
            return (False, f"You are not a user of this group. This command also requires the role: {', '.join(handler['group_roles'])}")
    
    # * If No restrictions for roles and group roles, then give access to the user. (suppose to be restricted)
    if handler:
        if not handler["roles"]:
            return (True, "No access rules, open to everyone")
        else:
            # Here group_roles are not set and the user is not in handler["roles"],
            # so the user must be a member of the group.
            for assigner in group.assigners:
                if assigner.user_id == user.id:
                    return (True, "The user has access to this group")
            else: 
                return (False, f"This command requires group membership OR one of the system roles: {', '.join(handler['roles'])}")
    else:
        return (True, "No access rules, open to everyone")



def is_member_service_message(message) -> bool:
    return bool(message and (message.new_chat_members or message.left_chat_member))


async def raise_unauthorized_exception(update: types.Update, message: str = "You are not registered."):
    print(Fore.LIGHTRED_EX + f"[Guard] User not found in the database {Fore.BLACK}");
    answer = optional_chain(update, 'message', 'answer') or optional_chain(update, 'callback_query', 'message', 'answer');
    reply = optional_chain(update, 'message', 'reply') or optional_chain(update, 'callback_query', 'message', 'reply');
    if answer:
        from_user = get_user_from_update(update);
        chat = get_chat_from_update(update);

        if (from_user.id != chat.id):
            message = f"<b>{from_user.username}</b>, {message}"

        await reply(message, parse_mode="HTML");
    raise Exception(f"User Unauthorized: '{message}'")