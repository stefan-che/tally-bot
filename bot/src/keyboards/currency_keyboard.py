from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def get_currency_keyboard(ex:str, pair:str, count:int):
    inline_btn_1 = InlineKeyboardButton(
            text='Refresh rate ♻️',
            callback_data=f'refresh_currency.{ex}.{pair}.{count}'
        )
    kb = InlineKeyboardBuilder()
    kb.add(inline_btn_1)
    kb.adjust(2)
    return kb.as_markup()
