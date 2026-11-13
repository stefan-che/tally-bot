from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from constants import MAX_HISTORIES_PER_MES
from src.common import accounts_inline_btns
from .create_btn import btn
import math


async def get_histories_next_inl_keyboard(msg: Message, histories, page, chat_id, currency):

    pages = math.ceil(len(histories) / MAX_HISTORIES_PER_MES) - 1

    if not currency:
        currency = "all"

    prev_btn = InlineKeyboardButton(text="⬅️Back", callback_data= f'update_history.{chat_id}.{int(page-1)}.{currency}')
    next_btn = InlineKeyboardButton(text="➡️Next", callback_data= f'update_history.{chat_id}.{int(page+1)}.{currency}')

    btns = []
    if page != 0: btns.append(prev_btn)
    if page < pages: btns.append(next_btn)
    kb = InlineKeyboardBuilder()
    kb.add(*btns)
    kb.adjust(2)
    return kb.as_markup()
