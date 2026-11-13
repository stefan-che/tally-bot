from colorama import Fore
from constants import MAX_HISTORIES_PER_MES
from db import History
import math


def get_histories_message(histories, page=0, msg_header='<b><u>HISTORY</u></b>'):
    answer = [msg_header]
    min_show = int(page*MAX_HISTORIES_PER_MES)
    max_show = int(min((page+1)*MAX_HISTORIES_PER_MES, len(histories)))

    show_histories = histories[min_show: max_show]
    
    for his in show_histories:
        his: History

        amount_str = f'{his.count:,.{0}f}'.replace(",", "’")
        
        if his.count < 0:
            symbol = "🔴"
        elif his.count > 0:
            symbol = "🟢"
        else:
            symbol = "⚪️"

        if his.is_cancelled == False:
            pass
        elif his.is_cancelled == None:
            symbol = "❌" # If None then it's not cancelled, because this transaction is a cancelation of another transaction
        else:
            symbol = "🚫"
            
        formatted_amount = f' {symbol} {amount_str} {his.currency}'
        formatted_datetime = his.time.strftime('%Y-%m-%d %H:%M:%S')
        
        if his.message_id and ("group" in his.__dict__) and ("tg_id" in his.group.__dict__): # If message_id and group exists
            tg_id = his.group.tg_id
            if tg_id < 0:
                tg_id = str(tg_id)[4:] # cut first 4 symbols as usually it comes likr '-100123456' and we need only '123456' # P.S. if cut 2 it still work as it will be '00123456' and it's still valid
                
            message_link = f'<a href="https://t.me/c/{tg_id}/{his.message_id}" >MSG</a>'
            answer.append(f'<code>{formatted_amount}\n     {formatted_datetime}\n     by {his.username}</code> {message_link}')
        else:
            answer.append(f'<code>{formatted_amount}\n     {formatted_datetime}\n     by {his.username}</code>')
            
    return '\n\n'.join(answer)