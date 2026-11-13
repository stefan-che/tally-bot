import os
from colorama import Fore
from aiogram import types
from aiogram.enums import ParseMode
from app.google import google_enabled
from app.google.drive.lookup_or_create import lookup_or_create_folder
from app.google.sheets.full_history import write_google_sheets_full_user_history
from db import session_maker, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.telegram import send_message
from dotenv import load_dotenv
load_dotenv()


async def get_sheet_full(callback_query: types.CallbackQuery):
    if not google_enabled():
        await callback_query.answer()
        return await send_message(callback_query.message.chat.id, "Google export is not configured (GOOGLE_CREDENTIAL_PATH)")
    root_folder_name = os.getenv("ROOT_FOLDER_NAME")

    # Initialise user_id and username
    user_id = callback_query.message.chat.id
    username = callback_query.message.chat.username
    if not username:
        username = callback_query.message.chat.full_name
        chatname = username
    
    # 
    split_data = callback_query.data.split(".")
    if len(split_data) == 2: 
        # "This Request come from admin Panel data = excel_report.{user_id}
        user_id = int(split_data[1])
        # ``Find the user by user.id
        async with session_maker() as session:
            session: AsyncSession
            user = await session.get(User, user_id)
            
            if not user:
                return await send_message(callback_query.message.chat.id, f"No user with ID {user_id} in the database")
            
            username = user.name

    
    folder_id = lookup_or_create_folder(root_folder_name, grant_write_permission=True)
    user_folder_id = lookup_or_create_folder(f'{username}::{user_id}', folder_id)

    url, status = await write_google_sheets_full_user_history(user_id, username, user_folder_id);
    if not status:
        return await send_message(callback_query.message.chat.id, url);

    print(f"{Fore.BLUE}URL:: {Fore.GREEN}", url)
    print(Fore.BLACK)

    await callback_query.answer("Spreadsheet created...")
    await callback_query.message.answer(f"📚 [Spreadsheets folder](https://drive.google.com/drive/u/0/folders/{user_folder_id})\n"  \
                                        f"📗 [Current statement]({url})",
                                        parse_mode=ParseMode.MARKDOWN)
