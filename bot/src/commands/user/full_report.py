import pathlib
from colorama import Fore
from aiogram.types import Message
from src.utils.telegram import send_document

from app.xlsx.full_history import create_full_group_history_excel

async def get_full_report(msg: Message):
    chat_id = msg.chat.id
    
    file = await create_full_group_history_excel(chat_id)
    if not file:
        return print(f'{Fore.RED}[get_full_report] FILE NAME NOT FOUND {Fore.BLACK}')
    print(f'{Fore.BLUE} FILE NAME: {Fore.GREEN} {file}')
    
    # `Send Document
    await send_document(chat_id, open(file, 'rb'))

    # Delete File
    pathlib.Path(file).unlink()