from aiogram.types import InlineKeyboardButton, KeyboardButton

def btn(text, callback_data=None, url=None):
    if not callback_data:
        return KeyboardButton(text=text, url=url)
    else:
        return InlineKeyboardButton(text=text, callback_data=callback_data, url=url);