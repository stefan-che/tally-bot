import numexpr as ne
import locale
import os
from colorama import Fore
from datetime import datetime
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message, InlineKeyboardMarkup, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext  # FSM

from app.utils import exception_with_line
from app.utils.validate_num import validate_num
from db import session_maker, Account, History, EUserRole
from db.query.group import get_group_by_tg_id
from db.query.user import get_user_by_id
from src import answer, edit_message
from src.keyboards import btn
from src.utils.telegram import send_message

async def send_balanse_changed_message(msg: Message, oldBalance, newBalance, accountName):

    owner_id = os.getenv("OWNER_ID")
    user_id = msg.from_user.id
    chat_id = msg.chat.id
    isChat = user_id != chat_id;



    if isChat:
        # Bot in group
        name = msg.chat.title;
        pass
    else:
        # Private Chat
        name = msg.chat.username;
        pass
    text = f'''Balanced was changed 
        from <b>{oldBalance}</b> to <b>{newBalance}</b>
        {"CHAT" if isChat else "USER"}: <b>{name}</b>
        Account: <b>{accountName}</b>
    '''
    await send_message(owner_id, text)
    pass


async def update_balance(msg: Message):
    data = msg.text.strip().split(" ")
    chat_id = msg.chat.id
    if len(data) == 2:
        print(msg)
        async with session_maker() as session:
            async with session.begin():
                session: AsyncSession
                accName = data[1]

                print(chat_id, accName)
                
                group = await get_group_by_tg_id(session, chat_id)
                
                # `` Find Account.
                query = select(Account).where(
                    Account.group_id == group.id,
                    Account.currency == accName.lower()
                )
                account = (await session.execute(query)).scalars().one_or_none()
                if not account:
                    return await answer(msg, f'you have no account: {accName}')
                

                # ``Find histories
                query = select(History.count).where(
                    History.account_id == account.id,
                )

                # ``Calculate total balance
                counts = (await session.execute(query)).scalars().all()
                total_balance = 0
                for count in counts:
                    total_balance += count; # 
                
                
                previos_balance = account.amount;
                account.amount = total_balance;
                await session.commit();

                if(previos_balance == total_balance):
                    return await answer(msg, f"Account <b>{accName}</b> is up to date...")

                await answer(msg, f"Balance of account '{accName}' updated.\nNew balance: {total_balance}\nOld balance: {previos_balance}")
                await send_balanse_changed_message(msg, previos_balance, total_balance, accName);
                return print(f"{Fore.LIGHTRED_EX}[update_balance]{Fore.LIGHTCYAN_EX} {total_balance} {Fore.BLACK}")
    elif len(data) == 3:
        session: AsyncSession
        accName = data[1]
        total_balance = data[2]

        async with session_maker() as session:
            async with session.begin():
                
                user = await get_user_by_id(session, msg.from_user.id)
                if user.role != EUserRole.SUPER_ADMIN:
                    return await answer(msg, "Extra parameters are available to the super admin only")
                
                group = await get_group_by_tg_id(session, chat_id)
                
                # `` Find Account.
                query = select(Account).where(
                    Account.group_id == group.id,
                    Account.currency == accName.lower()
                )
                account = (await session.execute(query)).scalars().one_or_none()
                if not account:
                    return await answer(msg, f'you have no account: {accName}')
                

                previos_balance = account.amount;
                account.amount = float(total_balance);

                await session.commit()
        

                if(previos_balance == total_balance):
                    return await answer(msg, f"Account <b>{accName}</b> is up to date...")

                await answer(msg, f"Balance of account {accName} updated.\nNew balance: {total_balance}")
                await send_balanse_changed_message(msg, previos_balance, total_balance, accName);
                return print(Fore.LIGHTCYAN_EX, total_balance)
    else:
        return await msg.answer(
            "Check your input:\n"
            "`/update_balance account-name`",
            parse_mode=ParseMode.MARKDOWN,
        )
