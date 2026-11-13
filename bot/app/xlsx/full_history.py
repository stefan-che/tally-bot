from typing import Union
from datetime import datetime
from colorama import Fore
from collections import defaultdict

from sqlalchemy import select
import xlsxwriter

from db import History, Account, session_maker
from db.query.group import get_group_by_tg_id
from app.google.service import get_goole_service

async def create_full_group_history_excel(chat_id: int) -> Union[bool, str]:

    async with session_maker() as session:
        group = await get_group_by_tg_id(session, chat_id);
        if not group:
            print(f'{Fore.RED} [create_full_group_history_excel] Group not found {Fore.BLACK}')
            return False
        
        query = select(History).where(History.group_id == group.id).order_by(History.time)
        histories = (await session.execute(query)).scalars().all()
        if not histories[::-1]:
            print(f'{Fore.RED} [create_full_group_history_excel] Histories not found {Fore.BLACK}')
            return False
        
        name = f'Full statement as of {datetime.now()}.xlsx'
        create_excel_histories(name, histories);

    return name


async def create_full_admin_history_excel() -> Union[bool, str]:
    query = select(History).order_by(History.time)
    async with session_maker() as session:
        histories = (await session.execute(query)).scalars().all()
        if not histories[::-1]:
            return False
        
        name = f'Full statement for all accounts as of {datetime.now()}.xlsx'
        create_excel_histories(name, histories);

    return name


def create_excel_histories(name: str, histories):
    columns = ['Date', 'User', 'Account', 'Amount', 'Balance', 'Comment']
    

    with xlsxwriter.Workbook(name) as workbook:
        # ''STYLES
        font_family = "Arial"
        header_format = workbook.add_format({'bg_color': "#444444", "font_color": "white", "bold": True, 'font_name': font_family})
        first_row =workbook.add_format({"bg_color": "#fCfCfC", 'font_name': font_family})
        second_row =workbook.add_format({"bg_color": "#f0f0f0", 'font_name': font_family})
        
        # `Create Sheet
        worksheet = workbook.add_worksheet()

        for i, col_name in enumerate(columns):
            worksheet.write(0, i, col_name, header_format)

        # `Calculate all balance left on each row.
        count_by_currency = defaultdict(int)
        
        size = len(histories)
        for i, history in enumerate(histories, 1):
            row_format = first_row
            if i % 2 == 1:
                row_format = second_row

            position = size - i + 1
            count_by_currency[history.currency] += history.count
            worksheet.write(position, 0, history.time.strftime("%d-%m-%Y %H:%M:%S"), row_format)
            worksheet.write(position, 1, history.username, row_format)
            worksheet.write(position, 2, history.currency, row_format)
            worksheet.write(position, 3, history.count, row_format)
            worksheet.write(position, 4, count_by_currency[history.currency], row_format)
            worksheet.write(position, 5, history.comment, row_format)

        worksheet.set_column_pixels(0, 0, 140)
        worksheet.set_column_pixels(1, 1, 100)
        worksheet.set_column_pixels(2, 4, 80)
        worksheet.set_column_pixels(5, 5, 200)