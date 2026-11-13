from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from src.common import main_btns

async def get_main_keyboard(msg: Message):
    keyboard = ReplyKeyboardBuilder()

    btns = [main_btns[key] for key in main_btns.keys()];
    print("get_main_keyboard", btns);
    keyboard.add(*[KeyboardButton(text=main_btns[key]) for key in main_btns.keys()])
    keyboard.adjust(2)

    return keyboard.as_markup(resize_keyboard=True);
