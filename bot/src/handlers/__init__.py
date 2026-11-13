
from aiogram import Dispatcher
from .update_currency import update_currency_callback
from .reports.get_excel import get_excel_full
from .reports.get_excel_admin import get_excel_full_admin
from .reports.get_sheet import get_sheet_full
from .reports.get_sheet_admin import get_sheet_full_admin
from .cancel_tx import cancel_tx
from .update_histories import update_histories_callback
from .accounts_sort import accounts_sort_callback, is_accounts_sort_callback
from .accounts_all_page import accounts_all_page_callback, is_accounts_all_callback
from .groups_page import groups_page_callback, is_groups_callback
from .group_delete import group_delete_callback, is_gdel_callback

def split_and_check(data: str, index: int, value: str):
    split_data = data.split(".")
    if(len(split_data) > index):
        if(split_data[index] == value):
            return True
    return False

def register_handlers(dp: Dispatcher) -> None:
    # First: a "Get" filter may contain a dot, and the split(".") checks below would catch another button
    dp.callback_query.register(accounts_sort_callback, lambda c: is_accounts_sort_callback(c.data)) # "Get" sorting
    dp.callback_query.register(accounts_all_page_callback, lambda c: is_accounts_all_callback(c.data)) # "get_all": pages + sorting
    dp.callback_query.register(groups_page_callback, lambda c: is_groups_callback(c.data)) # /groups in a private chat: pages + filters
    dp.callback_query.register(group_delete_callback, lambda c: is_gdel_callback(c.data)) # /delete_group: confirmation

    dp.callback_query.register(update_currency_callback, lambda c: split_and_check(c.data, 1, "refresh_currency")) # rate

    # ADMIN
    dp.callback_query.register(get_excel_full_admin, lambda c: split_and_check(c.data, 1, "excel_full")) # full excel Report
    dp.callback_query.register(get_sheet_full_admin, lambda c: split_and_check(c.data, 1, "sheets_excel_full")) # full google sheet Report

    # USER
    dp.callback_query.register(get_excel_full, lambda c: split_and_check(c.data, 0, "excel_full")) # full excel Report
    dp.callback_query.register(get_sheet_full, lambda c: split_and_check(c.data, 0, "sheets_excel_full")) # full google sheet Report

    dp.callback_query.register(cancel_tx, lambda c:  split_and_check(c.data, 0, 'cancel-tx')) # cancel-tx

    dp.callback_query.register(update_histories_callback, lambda c:  split_and_check(c.data, 0, 'update_history')) # cancel-tx
