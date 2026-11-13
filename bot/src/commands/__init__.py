
from aiogram import Dispatcher
from aiogram.filters import Command
from src.app.app_state import AppState
# Commands
from ..common import commands, main_btns
from .start import start
from .router import register_router_commands
from .currency import get_course
from .help import get_help
from .get_id import get_id

def text_starts_with_arr_v(text, arr):
    if not text:  # photo/sticker/caption: m.text is None
        return False
    for v in arr:
        if text.lower().startswith(v.lower()):
            return True
    else:    
        return False

def register_commands():
    app = AppState()
    dp = app.dp
    app.add_command_listener(start, commands=['start'], is_public=True)
    app.add_command_listener(get_id, commands=['id'], is_public=True)


    app.add_command_listener(get_help, commands=['help'], is_public=False)
    dp.message.register(get_help, lambda m: text_starts_with_arr_v(m.text, [*commands['help'], main_btns['help']]))

    dp.message.register(get_course, Command(commands=commands['currency']))

    register_router_commands()
