from aiogram.types import CallbackQuery
from db.engine import session_maker
from db.query.history import get_all_histories_by_chat_id, get_all_histories_by_chat_id_currency
from src.commands.utils.get_histories_mes import get_histories_message
from src.keyboards.currency_keyboard import get_currency_keyboard
from app.exchanges.binance import binance_currency
from app.exchanges.xe import xe_currency
from src.keyboards.histories_next_page import get_histories_next_inl_keyboard
from src.utils.telegram import edit_message
from src.utils.currency import get_base_quote

async def update_histories_callback(callback_query: CallbackQuery):
    await callback_query.answer();
    res_data = callback_query.data.split('.')

    chat_id = int(res_data[1])
    page = int(res_data[2])
    currency = res_data[3]

    async with session_maker() as session:
        
        if currency == "all":
            histories = await get_all_histories_by_chat_id(session, chat_id)
        else:
            histories = await get_all_histories_by_chat_id_currency(session, chat_id, currency)

        text = get_histories_message(histories, page);
        reply_markup = await get_histories_next_inl_keyboard(callback_query, histories, page, chat_id, currency)

        await edit_message(text, callback_query.message.chat.id, callback_query.message.message_id, reply_markup)
