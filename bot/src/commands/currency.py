from aiogram.types import Message, CallbackQuery
from colorama import Fore
from src.keyboards.currency_keyboard import get_currency_keyboard
from src import answer
from app.exchanges.binance import binance_currency
from app.exchanges.xe import xe_currency
from src.utils.currency import get_base_quote


async def get_course(message: Message):
    msg = message.text.split()
    if len(msg) == 3:
        _, pair, count = msg
        count = int(count)
    elif len(msg) == 2:
        _, pair = msg
        count = 1
    else:
        await message.answer("Invalid request")
        return
    
    base, quote = get_base_quote(pair);
    if not base:
        return await answer(msg, "Pair can contain only 2 symbols");

    #$$ Binance
    res, status = await binance_currency(base, quote, count)
    print(f'{Fore.BLUE}{res}{Fore.BLACK}', status)
    if status:
        keyboard = await get_currency_keyboard('binance', pair, count);
        return await message.answer(f"{res}\nbinance.com", reply_markup=keyboard)
    
    # 'Don't get success response
    await message.answer("I don't have this currency\n" \
                          "To add it, contact an administrator with the pair")
    