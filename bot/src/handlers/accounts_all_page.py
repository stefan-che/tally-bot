from colorama import Fore
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from db import session_maker, EUserRole
from db.query.user import get_user_by_id_with_session
from src.commands.admin.get import build_all_accounts_view, NO_PREVIEW
from src.utils.accounts_pages import parse_all_callback, ALL_CALLBACK_PREFIX
from src.utils.telegram import edit_message


def is_accounts_all_callback(data: str | None) -> bool:
    return bool(data) and data.startswith(ALL_CALLBACK_PREFIX)


async def accounts_all_page_callback(callback_query: CallbackQuery):
    """"get_all": paging, sort toggle and view toggle (flat / by group) — edits the same message.

    The list contains the accounts of ALL clients, so rights (admin or super admin) are checked again here
    (the guard may be off and callback_data can be forged): admin/super admin, private chat with the bot only.
    """
    message = callback_query.message
    if message is None:
        return await callback_query.answer()
    chat_id = message.chat.id

    try:
        user = await get_user_by_id_with_session(callback_query.from_user.id)
        if not (user and user.role and EUserRole.is_admin(user.role) and callback_query.from_user.id == chat_id):  # same as router/get_all.py
            return await callback_query.answer("Not enough rights", show_alert=True)

        mode, page, filter_str, view = parse_all_callback(callback_query.data)
        async with session_maker() as session:
            text, markup = await build_all_accounts_view(session, filter_str, mode, page, view)
        await edit_message(text, chat_id, message.message_id, markup, link_preview_options=NO_PREVIEW)
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            print(f"{Fore.RED}[accounts_all_page_callback] {e}{Fore.BLACK}")
            await callback_query.answer("Could not refresh the list")
    except Exception as e:  # do not leave the button hanging
        print(f"{Fore.RED}[accounts_all_page_callback] {e}{Fore.BLACK}")
        await callback_query.answer("Could not refresh the list")
