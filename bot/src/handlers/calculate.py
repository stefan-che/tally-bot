import numexpr as ne
from colorama import Fore
from aiogram import types
from app.utils.validate_num import validate_num
from app.utils import exception_with_line
from src.utils.telegram import answer

async def calculate(message: types.Message):
    try:
        v_n = validate_num(message.text)
        print(Fore.GREEN,v_n, Fore.BLACK)
        result = ne.evaluate(v_n)
        await answer(message, f'{message.text} = <b>{str(result)}</b>')
    except Exception:
        exception_with_line()
#         ...