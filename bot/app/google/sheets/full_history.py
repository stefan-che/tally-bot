from datetime import datetime
from colorama import Fore
from db import session_maker, History
from sqlalchemy import select
from app.google import sheet_service, drive_service
from uuid import uuid4
from collections import defaultdict

from .utils import excel_create, excel_batch_update
from app.google.drive.utils import grant_permission_to_all, add_parent_folder

async def write_google_sheets_full_admin_history(folderId=None):
    try: 
        async with session_maker() as session:
            query = select(History).order_by(History.time)
            histories = (await session.execute(query)).scalars().all()
            if not histories:
                return ("There are no transactions yet.", False)

            name = f'Full statement as of {datetime.now()}'
            sheetName = "Statement"
            
            url = google_sheet_create_full_history(name, sheetName, folderId, histories)

            if url: 
                return url, True
            else:
                return "Something went wrong", False
    except Exception as e:
        print(f'{Fore.RED}ERROR: [write_google_sheets_full_history]\n', e)
        return f"Something went wrong\n Error: {e}", False
    
async def write_google_sheets_full_user_history(user_id: int, username, folderId=None):
    try: 
        async with session_maker() as session:
            query = select(History).where(History.user_id == user_id).order_by(History.time)
            histories = (await session.execute(query)).scalars().all()
            if not histories:
                return ("There are no transactions yet.", False)

            name = f'{username}: Full statement {datetime.now()}'
            sheetName = "Statement"
            
            url = google_sheet_create_full_history(name, sheetName, folderId, histories)

            if url: 
                return url, True
            else:
                return "Something went wrong", False
    except Exception as e:
        print(f'{Fore.RED}ERROR: [write_google_sheets_full_history]\n', e)
        return f"Something went wrong\n Error: {e}", False


def google_sheet_create_full_history(name, sheetName, folderId, histories):
    header_row = ['Date', 'User', 'Account', 'Amount', 'Balance', 'Comment']

    spreadSheetId = excel_create(name, sheetName=sheetName, columns=6)

    if folderId:
        print(Fore.BLUE,spreadSheetId, Fore.BLACK)
        add_parent_folder(spreadSheetId, folderId);

    rows_to_append = []
    count = 0
    for history in histories:
        count += history.count
        rows_to_append.append([
            history.time.strftime("%Y-%m-%d %H:%M:%S"),
            history.username,
            history.currency,
            history.count,
            count,
            history.comment,
        ])
    
    # REVERSE THE TABLE
    rows_to_append = rows_to_append[::-1]
    size = len(rows_to_append) + 1

    # Insert table to the begining
    rows_to_append.insert(0, header_row)
    
    excel_batch_update(spreadSheetId, sheetName, rows_to_append, rangeEnd=f"F{size}")

    grant_permission_to_all(spreadSheetId)

    return rf"https://docs.google.com/spreadsheets/d/{spreadSheetId}"