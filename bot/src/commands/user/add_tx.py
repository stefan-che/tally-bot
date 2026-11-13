import numexpr as ne
import locale
from colorama import Fore
from datetime import datetime
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext  # FSM

from app.utils import exception_with_line
from app.utils.validate_num import validate_num
from db import session_maker, Account, History
from db.query.account import get_account_by_chat_id_and_user_id
from db.query.user import get_user_by_id
from db.query.group import get_group_by_tg_id
from src import answer, edit_message
from src.keyboards import btn

def format_number_with_separators(number):
    # Format the number with thousands separators and remove trailing zeros
    parts = f"{number:.2f}".split(".")
    integer_part = "{:,}".format(int(parts[0])).replace(",", "’")
    formatted_number = f"{integer_part}.{parts[1]}".rstrip('0').rstrip('.')
    return formatted_number

async def add_tx_to_account(msg: Message, user, group):
    print(f"{Fore.LIGHTRED_EX}[ADD_TX]{Fore.BLACK}")

    if msg.text:
        data = msg.text.strip().split(" ", 2)
    elif msg.caption:
        data = msg.caption.strip().split(" ", 2)
    else:
        await answer(msg, "[DEV] Could not read the text.")
        raise Exception("Empty Text or Caption...")
    
    print("[ACCOUNT, SUM]:", data)
    if len(data) > 1:
        async with session_maker() as session:
            async with session.begin():
                session: AsyncSession
                accName = data[0][1:]
                
                account = await get_account_by_chat_id_and_user_id(session, group.tg_id, accName);
                if not account:
                    return await answer(msg, f'you have no account: {accName}')

                try:
                    text_to_calc = ""
                    comment = ""    
                    if '\n' in data[1]:
                        text_to_calc = data[1].split("\n")[0]
                        comment: str = "\n".join(data[1].split("\n")[1:])
                        
                    else:
                        text_to_calc = data[1]
                        
                    str_input = validate_num(text_to_calc.strip())
                    amount = round(ne.evaluate(str_input).tolist(),
                                   ndigits=account.decimal)
                    time = datetime.now()
                    if len(data) == 3:
                            comment += f' {data[2]}'
                    else:
                        pass
                
                    comment = f'({text_to_calc}) ' + comment

                    # PRINT IN CONSOLE THE OUTPUT OF USER
                    print(f'\n{Fore.LIGHTRED_EX}[ADD TX]')
                    print(f'   {Fore.BLUE}USER:\t{Fore.GREEN}{msg.from_user.username} \t {Fore.LIGHTBLACK_EX}IS CHAT: {Fore.LIGHTYELLOW_EX}{msg.from_user.id != msg.chat.id}')
                    print(f'   {Fore.BLUE}AMOUNT:\t{Fore.GREEN}{amount} \t ')
                    print(f'   {Fore.BLUE}CURRENCY:\t{Fore.GREEN}{account.currency} \t ')
                    print(f'   {Fore.BLUE}COMMENT:\t{Fore.LIGHTGREEN_EX}{comment} \t ')
                    print(f'   {Fore.BLUE}MESSAGE_ID:\t{Fore.GREEN}{msg.message_id} \t')
                    print(f'{Fore.BLACK}===================================')
                        
                    history = History(
                        user_id=user.id,
                        account_id=account.id,
                        currency=account.currency,
                        count=amount,
                        comment=comment,
                        time=time,
                        username=msg.from_user.username,
                        group_id=group.id,
                        message_id=msg.message_id
                    )

                    await session.execute(
                        update(Account)
                        .where(Account.id == account.id)
                        .values(amount=Account.amount + amount)
                    )

                    session.add(history)
                    await session.flush()

                    history_id = history.id
                    new_balance = account.amount
                    tx_currency = account.currency

                except Exception as e:
                    print(Fore.RED, e)
                    exception_with_line()
                    await session.rollback()
                    return await msg.answer(f"Something went wrong, most likely in '{data[1]}'\nError: {e}")

            cancel_btn = btn("Cancel this change", f'cancel-tx.{history_id}.{user.id}')
            kb = InlineKeyboardBuilder()
            kb.add(cancel_btn)
            kb.adjust(1)
            keyboard = kb.as_markup()

            formatted_amount = format_number_with_separators(amount)
            formatted_account_amount = format_number_with_separators(new_balance)

            tx_mes = f'Recorded: {"+" if amount > 0 else ""}{formatted_amount}\n' \
                    f'Balance: {formatted_account_amount} {tx_currency}\n'

            await answer(msg, tx_mes, parse_mode=ParseMode.HTML, reply_markup=keyboard)

    else:
        return await msg.answer(
            "Check your input:\n"
            "`/account-name number (formula)`",
            parse_mode=ParseMode.MARKDOWN,
        )