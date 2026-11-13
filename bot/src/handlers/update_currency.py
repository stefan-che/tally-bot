from aiogram.types import CallbackQuery
from src.keyboards.currency_keyboard import get_currency_keyboard
from app.exchanges.binance import binance_currency
from app.exchanges.xe import xe_currency
from src.utils.currency import get_base_quote

async def update_currency_callback(callback_query: CallbackQuery):
    await callback_query.answer();
    res_data = callback_query.data.split('.')
    pair = res_data[2]
    count = int(res_data[3] or 1)

    base, quote = get_base_quote(pair);
    if not base:
        return await callback_query.answer("Pair can contain only 2 symbols");

    keyboard = await get_currency_keyboard('binance', pair, count);
    res, status = await binance_currency(base, quote, count)
    
    await callback_query.message.edit_text(
        f"{res}\n{res_data[1]}.com",
        reply_markup=keyboard,
    )
