from aiogram import types
from aiogram.enums import ParseMode
from db import session_maker, Account, EGroupType
from db.query.group import get_group_by_tg_id
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from app.utils import exception_with_line
from src import answer
from src.commands.utils.initialise_group import initialise_group

async def add_account(msg: types.Message):
    # "Check if the input is valid
    if len(data := msg.text.strip().split()) not in [2, 3]:
        await msg.answer("Check the message format\n/add <account name> [decimals]")

    group = await initialise_group(msg);
    
    try:
        decimal = min(int(data[2]), 8)
    except Exception:
        decimal = 2

    async with session_maker() as session:
        async with session.begin():
            try:
                account_name = data[1].lower()
                query = insert(Account).values(
                    group_id=group.id,
                    user_id=group.tg_id, currency=account_name,
                    name=account_name,
                    amount=0, decimal=decimal,
                )
                await session.execute(query)
            except IntegrityError as e:
                if e.orig.sqlstate == "23505":
                    return await msg.answer("An account with this name already exists")
                else:
                    return exception_with_line();

    text = f"Account *{data[1]}* created\nDecimals: {decimal}"            
    await answer(msg, text, parse_mode=ParseMode.MARKDOWN);