import os
from colorama import Fore
from aiogram import types
from aiogram.enums import ParseMode
from app.google import google_enabled
from app.google.drive.lookup_or_create import lookup_or_create_folder
from app.google.sheets.full_history import write_google_sheets_full_admin_history
from dotenv import load_dotenv
from src.utils.telegram import send_message
load_dotenv()


async def get_sheet_full_admin(callback_query: types.CallbackQuery):
    if not google_enabled():
        await callback_query.answer()
        return await send_message(callback_query.message.chat.id, "Google export is not configured (GOOGLE_CREDENTIAL_PATH)")
    root_folder_name = os.getenv("ROOT_FOLDER_NAME")
    admin_folder = "Admin"
    username = callback_query.from_user.username
    
    print(f"{Fore.BLUE}callback.data:: {Fore.GREEN}",  callback_query.from_user)
    
    folder_id = lookup_or_create_folder(root_folder_name, grant_write_permission=True)
    
    user_folder_id = lookup_or_create_folder(admin_folder, folder_id)

    url, status = await write_google_sheets_full_admin_history(user_folder_id);
    if not status:
        return await send_message(callback_query.message.chat.id, url);

    print(f"{Fore.BLUE}URL:: {Fore.GREEN}", url)
    print(Fore.BLACK)

    await callback_query.answer("Spreadsheet created...")
    await callback_query.message.answer(f"📚 [Spreadsheets folder](https://drive.google.com/drive/u/0/folders/{user_folder_id})\n"  \
                                        f"📗 [Current statement]({url})",
                                        parse_mode=ParseMode.MARKDOWN)
