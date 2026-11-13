import pathlib
from colorama import Fore
from aiogram import types
from src.utils.telegram import send_document
from app.xlsx.full_history import create_full_group_history_excel


async def get_excel_full(callback_query: types.CallbackQuery):
    print(f"{Fore.BLUE}callback.data:: {Fore.GREEN}", callback_query.data)
    data_split = callback_query.data.split(".")
    chat_id = callback_query.message.chat.id

    if len(data_split) == 2:
        chat_id = int(data_split[1])
    
    print(f"{Fore.BLUE}CHAT ID::: {Fore.LIGHTGREEN_EX}", chat_id)
    file = await create_full_group_history_excel(chat_id)
    if not file:
        return print(f'{Fore.RED}[get_excel_full] FILE NAME NOT FOUND {Fore.BLACK}')
    print(f'{Fore.BLUE} FILE NAME: {Fore.GREEN} {file}')
    
    # `Send Document
    await send_document(chat_id, open(file, 'rb'))

    # Delete File
    pathlib.Path(file).unlink()