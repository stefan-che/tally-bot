from colorama import Fore
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from db import session_maker, EUserRole
from db.query.user import get_user_by_id_with_session
from src.commands.admin.get import NO_PREVIEW
from src.commands.admin.group_command import build_groups_view
from src.utils.groups_pages import parse_groups_callback, is_groups_callback
from src.utils.telegram import edit_message

__all__ = ["groups_page_callback", "is_groups_callback"]


async def groups_page_callback(callback_query: CallbackQuery):
    """/groups in a private chat: paging and filters — edits the same message.

    Rights (admin or super admin, private chat with the bot only) are checked again here:
    the guard does not check roles for buttons in private chats, and callback_data can be forged.
    """
    message = callback_query.message
    if message is None:
        return await callback_query.answer()
    chat_id = message.chat.id

    try:
        user = await get_user_by_id_with_session(callback_query.from_user.id)
        if not (user and user.role and EUserRole.is_admin(user.role) and callback_query.from_user.id == chat_id):
            return await callback_query.answer("Not enough rights", show_alert=True)

        page, status, chat_type, accounts, search, users, sort, direction = parse_groups_callback(callback_query.data)
        async with session_maker() as session:
            text, markup = await build_groups_view(session, page, status, chat_type, accounts, search,
                                                   users, sort, direction)
        await edit_message(text, chat_id, message.message_id, markup, link_preview_options=NO_PREVIEW)
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            print(f"{Fore.RED}[groups_page_callback] {e}{Fore.BLACK}")
            await callback_query.answer("Could not refresh the list")
    except Exception as e:  # do not leave the button hanging
        print(f"{Fore.RED}[groups_page_callback] {e}{Fore.BLACK}")
        await callback_query.answer("Could not refresh the list")
