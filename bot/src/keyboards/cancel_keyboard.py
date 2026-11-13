from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def cancel_confirm_keyboard(callback_data:str):
    question = InlineKeyboardButton(
            text='Are you sure you want to cancel? 🤷‍♂️',
            callback_data=f'cancel-question.{callback_data}'
        )
    btn_yes = InlineKeyboardButton(
            text='Yes 🙆‍♂️',
            callback_data=f'cancel-yes.{callback_data}'
        )
    btn_no = InlineKeyboardButton(
            text='No 🙅‍♂️',
            callback_data=f'cancel-no.{callback_data}'
        )
    kb = InlineKeyboardBuilder()
    kb.row(question)
    kb.row(btn_yes, btn_no)
    return kb.as_markup()

async def cancel_btn(callback_data):
    return InlineKeyboardButton(
            text='Cancel 🚫',
            callback_data=f'cancel.{callback_data}'
        )
