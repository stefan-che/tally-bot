from aiogram import types, Dispatcher
from aiogram.filters import Command
from functools import wraps
from src.app.app_state import AppState

def message_handler_decorator(commands=None, is_public=False):
    print(f"message_handler ::: commands = {commands}, is_public = {is_public}")
    def decorator(func):
        print(f"message_handler -> decorator ::: func = {func}")
        dp = AppState().dp

        # Register handler with the dispatcher
        dp.message.register(func, Command(commands=commands))

        # Store metadata about the handler
        app = AppState()
        app.add_command(commands, func, is_public=is_public)

        return func
    return decorator

def register_command(func, commands=None, is_public=False, lambda_func=None):
    app = AppState();

    app.add_command(commands, func, is_public=is_public)