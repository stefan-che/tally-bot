from colorama import Fore
from aiogram import types
from src.utils.access import getRole
from myTypes.roles import Role
from ..user.full_report import get_full_report as get_full_report_as_user
from ..admin.full_report import get_full_report as get_full_report_as_admin

async def full_report(msg: types.Message):
    await msg.answer("Preparing the report...")
    print(f"{Fore.LIGHTRED_EX}FULL_REPORT{Fore.BLACK}")
    if await getRole(msg.from_user.id) == Role.OWNER and msg.from_user.id == msg.chat.id:
        await get_full_report_as_admin(msg)
    else: 
        await get_full_report_as_user(msg)