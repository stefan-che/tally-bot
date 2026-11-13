from db import Account
from html import escape

def get_accounts_message(accounts, msg_header='<code>Your funds:</code>\n'):
    answer = [msg_header]
    max_amount_length = max(len(f'{acc.amount:,.{0}f}') for acc in accounts)
    for acc in accounts:
        acc: Account
        amount_str = f'{acc.amount:,.{0}f}'.replace(",", "’")
        safe_currency = escape(acc.currency) # escape '<', '>', ...
        
        formatted_amount = f'{amount_str:>{max_amount_length}} {safe_currency}'
        answer.append(f'<code>  {formatted_amount}</code>')
    return '\n'.join(answer)