__all__ = ["main_btns", "accounts_inline_btns", "commands"]

main_btns = {
    "full_report": "Full_report",
    "get": "Get",
    "history": "History",
    "help": "Help",
}

accounts_inline_btns = {
    "excel_full": "Generate statement",
    "sheets_excel_full": "Statement in Google Sheets",
    # "all_currency": "Generate full statement",
    # "sheets_all_currency": "Full statement in Google Sheets",
}

commands = {
    # $ ACCOUNT
    "get": ["get"],
    "get_all": ["get_all"],
    "add": ["add"],
    "delete": ["delete", "del"],
    "full_report": ["full_report", "excel"],
    "get_histories": ["history"],
    
    
    # $ USER
    "get_me": ["me", "get_me"],
    "get_users": ["users", "get_users"],
    "create_users": ["add_user", "create_user"],
    "create_admin": ["add_admin", "create_admin"],
    "update_user_role": ["update_role", "update_user_role"],
    "update_user_status": ["update_status", "update_user_status"],
    "delete_users": ["delete_user"],
    
    # $ GROUP
    "get_groups": ["groups", "get_groups"],
    "get_group": ["group"],
    "add_group": ["add_group"],
    "delete_group": ["delete_group"],
    "change_group_type": ["change_group_type"],
    
    # $ Other
    "help": ["help"],
    "currency": ["rate", "cur", "currency"],
    "update_balance": ["update_balance"],
    "migrate": ["migrate"]
}