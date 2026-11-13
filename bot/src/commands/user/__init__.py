from aiogram import Dispatcher
from aiogram.filters import Command

from src.common import commands, main_btns
from .get import get_accounts
from .add_acc import add_account
from .add_tx import add_tx_to_account
from .delete_acc import delete_account

@DeprecationWarning
def register_user_commands(dp: Dispatcher) -> None:
    dp.message.register(get_accounts, Command(commands=commands['get']))
    dp.message.register(get_accounts, lambda m: m.text and m.text.lower() in [*commands['get'], main_btns['get'].lower()])

    dp.message.register(add_account, Command(commands=commands['add']))
    dp.message.register(add_account, lambda m: m.text and m.text.lower().split(" ")[0] in commands['add'])

    dp.message.register(delete_account, Command(commands=commands['delete']))
    dp.message.register(delete_account, lambda m: m.text and m.text.lower().split(" ")[0] in commands['delete'])

    # # Add TX to Account / Cance Tx
    dp.message.register(add_tx_to_account, lambda m: m.text and m.text.startswith('/'))
    