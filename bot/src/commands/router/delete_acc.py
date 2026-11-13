from aiogram import types
from src.utils.access import getRole
from myTypes.roles import Role
from ..user.delete_acc import delete_account as delete_account_as_user

async def delete_acc(msg: types.Message):
    await delete_account_as_user(msg)