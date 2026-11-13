from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from src.common import accounts_inline_btns
from src.utils.sort_accounts import toggle_label, toggle_target, build_sort_callback
from .create_btn import btn


async def get_accounts_inl_keyboard(
    msg: Message,
    callback_prefix: str = "",
    callback_postfix: str = "",
    sort_mode: str | None = None,
    sort_filter: str | None = None,
):
    """If sort_mode is set, the first row is the sort toggle button (only for "Get" in the own chat)."""

    btns = [InlineKeyboardButton(text=accounts_inline_btns[key], callback_data= callback_prefix + key + callback_postfix) for key in accounts_inline_btns.keys()]
    sort_data = build_sort_callback(toggle_target(sort_mode), sort_filter) if sort_mode is not None else None
    if sort_data:
        btns.insert(0, InlineKeyboardButton(text=toggle_label(sort_mode), callback_data=sort_data))
    kb = InlineKeyboardBuilder()
    kb.add(*btns)
    kb.adjust(1)
    return kb.as_markup()
