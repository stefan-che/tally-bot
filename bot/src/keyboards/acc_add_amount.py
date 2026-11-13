from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from .cancel_keyboard import cancel_btn


async def get_acc_add_inl_keyboard(callback_data = "acc_add_amount"):
    confirmBtn = InlineKeyboardButton(text=f'Confirm 🟢', callback_data=f'confirm.{callback_data}')
    editBtn = InlineKeyboardButton(text=f'Edit ✏️', callback_data=f'edit.{callback_data}')
    cancelBtn = await cancel_btn(callback_data);
    kb = InlineKeyboardBuilder()
    kb.add(confirmBtn, editBtn, cancelBtn)
    kb.adjust(1)
    return kb.as_markup()
