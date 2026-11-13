from aiogram import Dispatcher, types

from db import EUserRole
from src.common import commands, main_btns
from .get import get_acc
from .get_all import get_all_acc
from .get_histories import get_histories
from .full_report import full_report
from .add_acc import add_account
from .update_balance import update_balance
from ..admin.user_command import get_users, delete_user, create_user_cmd, update_user_role, get_me
from ..admin.group_command import add_group, get_groups, delete_group, change_group_type, get_group
from . import update_balance
from src.app.register_commands import register_command
from src.app.app_state import AppState
from src import get_text_message, get_text_from_message

from .add_tx import add_tx
from .delete_acc import delete_acc
from .migrate_groups import migrate_groups

def starts_with_in_arr(text: str, arr) -> bool:
    for v in arr:
        if text.startswith(v):
            return True
    else:
        return False

def register_router_commands() -> None:
    app = AppState()

    # * DP, add type
    dp: Dispatcher = app.dp 

    # *** USER
    app.add_command_listener(get_me, commands['get_me']) # me
    app.add_command_listener(get_users, commands['get_users'], roles=[EUserRole.ADMIN])
    # aiogram 3 does not await coroutines returned by sync callables (e.g. lambda) — wrappers must be async
    async def create_user_handler(m: types.Message):
        return await create_user_cmd(m)

    async def create_admin_handler(m: types.Message):
        return await create_user_cmd(m, EUserRole.ADMIN)

    app.add_command_listener(create_user_handler, commands=commands['create_users'], roles=[EUserRole.ADMIN], group_roles=[EUserRole.ADMIN])
    app.add_command_listener(create_admin_handler, commands=commands['create_admin'], roles=[EUserRole.ADMIN], group_roles=[EUserRole.ADMIN], private_roles=[EUserRole.SUPER_ADMIN])
    app.add_command_listener(delete_user, commands=commands['delete_users'], roles=[EUserRole.SUPER_ADMIN], group_roles=[EUserRole.ADMIN])
    app.add_command_listener(update_user_role, commands=commands['update_user_role'], roles=[EUserRole.SUPER_ADMIN])

    # *** GROUP
    app.add_command_listener(get_groups, commands=commands['get_groups'], roles=[EUserRole.ADMIN])
    app.add_command_listener(get_group, commands=commands['get_group'])
    app.add_command_listener(add_group, commands=commands['add_group'], roles=[EUserRole.ADMIN])
    app.add_command_listener(delete_group, commands=commands['delete_group'], roles=[EUserRole.SUPER_ADMIN])
    app.add_command_listener(change_group_type, commands=commands['change_group_type'], roles=[EUserRole.SUPER_ADMIN])
    
    # *** Get
    app.add_command_listener(get_all_acc, commands=commands['get_all'], roles=[EUserRole.ADMIN])
    app.add_hear_listener(get_all_acc, commands=commands['get_all'], roles=[EUserRole.ADMIN])
    app.add_command_listener(get_acc, commands=commands['get'])
    app.add_hear_listener(get_acc, commands=commands['get'])

    app.add_command_listener(get_histories, commands=commands['get_histories'], roles=[EUserRole.ADMIN])
    app.add_hear_listener(get_histories, commands=commands['get_histories'], roles=[EUserRole.ADMIN])

    # *** Add
    app.add_command_listener(add_account, commands=commands['add'], roles=[EUserRole.ADMIN], private_roles=[EUserRole.USER])
    app.add_hear_listener(add_account, commands['add'], roles=[EUserRole.ADMIN], private_roles=[EUserRole.USER])
    
    # *** Delete
    app.add_command_listener(delete_acc, commands=commands['delete'], roles=[EUserRole.SUPER_ADMIN], group_roles=[EUserRole.ADMIN], private_roles=[EUserRole.USER, EUserRole.ADMIN])
    app.add_hear_listener(delete_acc, commands['delete'], group_roles=[EUserRole.ADMIN], private_roles=[EUserRole.USER])

    # *** Full Excel statement
    app.add_command_listener(full_report, commands['full_report'])
    app.add_hear_listener(full_report, [*commands['full_report'], main_btns['full_report']])
    
    # *** MIGRATE
    app.add_command_listener(migrate_groups, commands=commands['migrate'], roles=[EUserRole.SUPER_ADMIN]) # MIGRATE
    app.add_hear_listener(migrate_groups, commands=commands['migrate'], roles=[EUserRole.SUPER_ADMIN]) # MIGRATE
    dp.message.register(migrate_groups, lambda m: m.migrate_to_chat_id is not None)
    dp.message.register(migrate_groups, lambda m: m.migrate_from_chat_id is not None)
    
    app.add_command_listener(update_balance, commands['update_balance'], roles=[EUserRole.SUPER_ADMIN], group_roles=[EUserRole.ADMIN], private_roles=[EUserRole.USER, EUserRole.ADMIN])
    app.add_hear_listener(update_balance, commands['update_balance'], roles=[EUserRole.SUPER_ADMIN], group_roles=[EUserRole.ADMIN], private_roles=[EUserRole.USER, EUserRole.ADMIN])

    # *** Add TX
    dp.message.register(add_tx, lambda m: m.text and m.text.startswith('/'))
    dp.message.register(
        add_tx,
        lambda message: message.caption and message.caption.startswith('/'),
        # Use a lambda function to filter messages based on the custom condition
    )
    
    
    


