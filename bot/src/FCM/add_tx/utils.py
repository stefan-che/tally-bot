from datetime import datetime


def get_tx_mes(account, amount: float, date: datetime, comment: str):
    return f'Account: *{account["currency"]}*\n' \
        f'Recorded: *{amount:,.{account["decimal"]}f}* \n' \
        f'Current balance: *{account["amount"] + amount}*\n' \
        f'Previous balance: *{account["amount"]}*\n\n' \
        f'Date and time: *{date.day}-{date.month}-{date.year} {str(date.hour).zfill(2)}:{str(date.minute).zfill(2)}*\n' \
        f'Comment: *{comment}*'


def parse_date_string(date_string):
    date_format = "%d %m %Y"
    if len(date_string) > 10:
        date_format += " %H %M"
    try:
        date = datetime.strptime(date_string, date_format)
        return date
    except ValueError:
        return None