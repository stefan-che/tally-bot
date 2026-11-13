from colorama import Fore
from aiogram import types
from app.utils import visualise
from db import session_maker, Account, History
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils import exception_with_line
from src import answer

async def delete_account(msg: types.Message):
    print("DELETE ACCOUNT", msg.text)
    # "Check if the input is valid
    if len(data := msg.text.strip().split()) != 2:
        await msg.answer("Check the message format\n/delete <account name>")

    user_id = msg.chat.id
    currency = data[1]
    print(f'{Fore.BLUE}Currency: {Fore.GREEN}{currency}')

    async with session_maker() as session:
        session: AsyncSession
        async with session.begin():
            try:
                account_query = delete(Account).where((Account.user_id == user_id) & (Account.currency == currency)).returning(Account)
                account = (await session.execute(account_query)).scalar()

                if not account:
                    return await answer(msg, f'You have no account <b>{currency}</b>')

                # No need to delete anything from the History table

            except IntegrityError as e:
                print("ERROR :::", e)
                visualise(e, "ERROR")
                if e.orig.sqlstate == "23505":
                    return await msg.answer("An account with this name already exists")
                else:
                    return exception_with_line();

    text = f"Account <b>{data[1]}</b> deleted"            
    await answer(msg, text);