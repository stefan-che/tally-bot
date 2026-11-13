import pathlib
from colorama import Fore
from aiogram import types
from src.utils.telegram import send_document
from app.xlsx.full_history import create_full_admin_history_excel


async def get_excel_full_admin(callback_query: types.CallbackQuery):
    print(f"{Fore.BLUE}callback.data:: {Fore.GREEN}", callback_query.data)
    chat_id = callback_query.message.chat.id
    
    file = await create_full_admin_history_excel()
    if not file:
        # Should never be there...
        return print(f'{Fore.RED}[get_excel_full_admin] FILE NAME NOT FOUND {Fore.BLACK}')
    print(f'{Fore.BLUE} FILE NAME: {Fore.GREEN} {file}')
    
    # `Send Document
    await send_document(chat_id, open(file, 'rb'))

    # Delete File
    pathlib.Path(file).unlink()