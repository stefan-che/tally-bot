from colorama import Fore
from datetime import datetime
from sqlalchemy import select, insert, update
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery
from db import session_maker, History, Account
from db.query.user import get_user_by_id_with_session
from src.utils.telegram import edit_message, reply

async def cancel_tx(callback: CallbackQuery):
    data = callback.data.split(".");
    user = callback.from_user;
    history_id = data[1]
    tx_user_id = int(data[2]);
    
    if user.id != tx_user_id:
        tx_user = await get_user_by_id_with_session(tx_user_id);
        return await reply(callback.message, f"<b>{user.username}</b>, you cannot cancel a transaction made by @{tx_user.name}")
    
    print(f'{Fore.CYAN} History Id', history_id)

    try:
        async with session_maker() as session:
            session: AsyncSession
            async with session.begin():
                query = select(History).where(History.id == history_id)
                history = (await session.execute(query)).scalar_one()
                
                if history.is_cancelled:
                    return await reply(callback.message, "The transaction is already cancelled")
                
                history.is_cancelled = True

                query = select(Account).where(Account.id == history.account_id)
                account = (await session.execute(query)).scalar_one()

                await session.execute(
                    update(Account)
                    .where(Account.id == account.id)
                    .values(amount=Account.amount - history.count)
                )

                insert_cancel_his = insert(History).values(
                    user_id=history.user_id,
                    account_id=history.account_id,
                    currency=history.currency,
                    count=history.count * -1,
                    comment=f'[Cancelled]{history.comment}',
                    time=datetime.now(),
                    username=history.username,
                    group_id=history.group_id,
                    is_cancelled=None,
                    message_id=history.message_id, # Points to the original transaction
                )

                await session.execute(insert_cancel_his)

            chat_id = callback.message.chat.id
            message_text = callback.message.text
            message_id = callback.message.message_id

            await edit_message(message_text + "\n\n Cancelled 🚫", chat_id, message_id, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(Fore.RED, e)
        await session.rollback()
        return await reply(callback.message, f"Something went wrong\nError: {e}")

