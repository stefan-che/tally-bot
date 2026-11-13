from colorama import Fore
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from db import session_maker
from src.commands.user.get import build_accounts_view
from src.utils.sort_accounts import parse_sort_callback, SORT_CALLBACK_PREFIX
from src.utils.telegram import edit_message


def is_accounts_sort_callback(data: str | None) -> bool:
    return bool(data) and data.startswith(SORT_CALLBACK_PREFIX)


async def accounts_sort_callback(callback_query: CallbackQuery):
    """Sort toggle button of "Get": redraws the same message in the chosen mode.
    Stores nothing — the mode comes in callback_data.

    The chat is taken from the message itself (not from callback_data), so forged data cannot open another chat's accounts.
    """
    mode, filter_str = parse_sort_callback(callback_query.data)
    message = callback_query.message
    chat_id = message.chat.id

    try:
        async with session_maker() as session:
            text, markup = await build_accounts_view(session, message, chat_id, filter_str, mode)

        if markup is None:  # accounts are gone / the filter no longer matches anything
            await edit_message(text, chat_id, message.message_id)
        else:
            await edit_message(text, chat_id, message.message_id, markup)
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            print(f"{Fore.RED}[accounts_sort_callback] {e}{Fore.BLACK}")
            await callback_query.answer("Could not refresh the list")
    except Exception as e:  # do not leave the button hanging and do not break processing
        print(f"{Fore.RED}[accounts_sort_callback] {e}{Fore.BLACK}")
        await callback_query.answer("Could not refresh the list")
