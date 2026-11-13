import numexpr as ne
from colorama import Fore
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext  # FSM

from app.utils import exception_with_line
from app.utils.validate_num import validate_num
from db import session_maker, Account
from src import answer
from src.keyboards.acc_add_amount import get_acc_add_inl_keyboard
from .state import States, callback_data
from .utils import get_tx_mes


async def text_startswith_handler(msg: Message, state: FSMContext):
    if len(data := msg.text.strip().split(" ", 1)) > 1:
        async with session_maker() as session:
            async with session.begin():
                session: AsyncSession
                user_id = msg.from_user.id
                accName = data[0][1:]

                # ``Find account
                query = select(Account).where(
                    Account.user_id == user_id,
                    Account.currency == accName.lower()
                )
                account = (await session.execute(query)).scalars().one_or_none()
                if not account:
                    return await answer(msg, f'you have no account: {accName}')

                try:
                    str_input = validate_num(data[1])
                    amount = round(ne.evaluate(str_input).tolist(),
                                ndigits=account.decimal)
                    time = datetime.now()
                    accountObj = {
                        "id": account.id,
                        "amount": account.amount,
                        "currency": account.currency,
                        "decimal": account.decimal,
                        "user_id": account.user_id,
                    }

                    await state.update_data(account=accountObj, amount=amount, time=time, comment="...")


                    keyboard = await get_acc_add_inl_keyboard(callback_data)
                    tx_mes = get_tx_mes(accountObj, amount, time, "...")
                    newMes = await answer(msg, tx_mes, 
                                parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
                    
                    await state.update_data(message_id=newMes.message_id)
                    
                    print("Wait for Any Action")
                    await state.set_state(States.wait_for_action)

                except Exception as e:
                    print(Fore.RED, e)
                    exception_with_line()
                    return await msg.answer(f"Something went wrong, most likely in {data[1]}\n Error: {e}")
    else:
        return await msg.answer(
            "Check your input:\n"
            "`/account-name number (formula)`",
            parse_mode=ParseMode.MARKDOWN,
        )
