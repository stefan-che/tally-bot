from sqlalchemy import select
from aiogram import types
from db import session_maker, Account
from src.keyboards.accounts_keyboard import get_accounts_inl_keyboard
from src.utils.telegram import answer
from src.utils.filter_acc_by_string import get_filter_accounts
from src.utils.sort_accounts import sort_accounts, normalize_sort
from ..utils.get_accounts_mes import get_accounts_message

NO_ACCOUNTS = "You have no accounts yet"
NO_MATCHING_ACCOUNTS = "No matching accounts"


async def build_accounts_view(session, msg: types.Message, chat_id: int, filter_str: str | None, sort_mode: str | None = None):
    """Text and keyboard of the "Get" list for a chat. -> (text, markup) or (error message, None).

    sort_mode=None → default (by amount). The choice is not stored: it comes from the button.
    """
    sort_mode = normalize_sort(sort_mode)

    query = select(Account).where(Account.user_id == chat_id)
    accounts = (await session.execute(query)).scalars().all()
    if not accounts:
        return NO_ACCOUNTS, None

    if filter_str:
        # dict.fromkeys drops duplicates when an account matches several filters
        accounts = list(dict.fromkeys(get_filter_accounts(accounts, [filter_str])))
        if not accounts:
            return NO_MATCHING_ACCOUNTS, None

    text = get_accounts_message(sort_accounts(accounts, sort_mode))
    markup = await get_accounts_inl_keyboard(msg, sort_mode=sort_mode, sort_filter=filter_str)
    return text, markup


# # GET
async def get_accounts(msg: types.Message):
    data = msg.text.strip().split()
    chat_id = msg.chat.id

    if len(data) > 2:
        return await answer(msg, "Check your input:\n /get [account filter]")

    filter_str = data[1] if len(data) == 2 else None
    async with session_maker() as session:
        text, markup = await build_accounts_view(session, msg, chat_id, filter_str)
    return await answer(msg, text, reply_markup=markup)
