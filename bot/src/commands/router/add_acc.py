from aiogram import types
from src.utils.access import getRole
from myTypes.roles import Role
from ..user.add_acc import add_account as add_account_as_user

async def add_account(msg: types.Message):
    await add_account_as_user(msg)