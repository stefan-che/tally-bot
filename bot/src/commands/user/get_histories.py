from sqlalchemy import select, desc
from aiogram import types
from db import session_maker, Account
from db.query.history import get_all_histories_by_chat_id, get_all_histories_by_chat_id_currency
from src.commands.utils.get_histories_mes import get_histories_message
from src.keyboards.histories_next_page import get_histories_next_inl_keyboard
from src.utils.telegram import answer
from ..utils.get_accounts_mes import get_accounts_message

# # HISTORY
async def get_histories(msg: types.Message, chat_id, currency=None):
    async with session_maker() as session:
        pass
        if currency:
            histories = await get_all_histories_by_chat_id_currency(session, chat_id, currency, populate=["group"])
        else:
            histories = await get_all_histories_by_chat_id(session, chat_id, populate=["group"])

        text = get_histories_message(histories, 0);
        reply_markup = await get_histories_next_inl_keyboard(msg, histories, 0, chat_id, currency)


        await answer(msg, text, reply_markup);
