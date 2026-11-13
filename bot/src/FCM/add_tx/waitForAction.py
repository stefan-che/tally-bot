from colorama import Fore
from aiogram.types import CallbackQuery
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext  # FSM
from aiogram.fsm.state import State
from sqlalchemy import update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from db import session_maker, Account, History
from app.utils import visualise, exception_with_line
from src import send_message, edit_reply_markup, edit_message, delete_message
from src.keyboards import cancel_confirm_keyboard, get_acc_add_inl_keyboard, btn
from src.FCM.utils import leave_fsm

from .state import callback_data, fields_to_change, States


# cancel.acc_add_amount
async def cancel(call_back: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        message_id = data["message_id"]
        chat_id = call_back.message.chat.id
        if call_back.message.message_id != message_id:
            visualise(
                [f"Clicked on another btn callback{call_back.message.message_id} state {message_id}"])

        cancel_confirm_kbrd = await cancel_confirm_keyboard(callback_data)
        await edit_reply_markup(cancel_confirm_kbrd, chat_id, message_id)

    except Exception as e:
        print("ERROR:"+Fore.RED, e)
        exception_with_line()


async def cancelNo(call_back: CallbackQuery, state: FSMContext):
    keyboard = await get_acc_add_inl_keyboard(callback_data)
    await edit_reply_markup(keyboard, call_back.message.chat.id, call_back.message.message_id)


async def cancelYes(call_back: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data['message_id']

    await delete_message(call_back.message.chat.id, message_id)
    await leave_fsm(state)
    data = await state.get_data()
    print("DATA:", data)


async def confirm(call_back: CallbackQuery, state: FSMContext):
    try:
        data = await state.get_data()
        message_id = data['message_id']

        if (call_back.message.message_id != message_id):
            print(Fore.RED, "Another Message")
            return

        visualise(data, "DATA for Confirm::")
        async with session_maker() as session:
            async with session.begin():
                session: AsyncSession
                account = data['account']
                amount = data['amount']
                time = data['time']
                comment = data['comment']

                visualise(account, "ACCOUNT to update")

                await session.execute(
                    update(Account).where(Account.id == account['id']).values(
                        amount=account['amount'] + amount)
                )
                user_id = call_back.message.chat.id

                visualise(call_back.message);
                print('User_id', user_id);
                await session.execute(
                    insert(History).values(
                        user_id=account['user_id'],
                        account_id=account['id'],
                        currency=account['currency'],
                        count=amount,
                        comment=comment,
                        time=time,
                        username=call_back.message.from_user.username,
                    ),
                )

        await leave_fsm(state);

        await send_message(call_back.message.chat.id, "Transaction saved 👍")

        await state.update_data(current_step="cencel")
        visualise(data)
    except Exception as e:
        print("ERROR:", e)
        exception_with_line()

# # # Open Edit Menu
async def edit(call_back: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    message_id = data['message_id']
    btns = []
    back_btn = btn("Back ↩️", f'back.{callback_data}')
    for key in fields_to_change.keys():
        editBtn = btn(fields_to_change[key]['title'], f'set.{key}.{callback_data}')
        btns.append(editBtn);
    
    kb = InlineKeyboardBuilder()
    kb.add(*btns, back_btn)
    kb.adjust(2)
    keyboard = kb.as_markup()

    await edit_reply_markup(keyboard, call_back.message.chat.id, message_id);

# # # Back to Main Menu
async def edit_back(call_back: CallbackQuery, state: FSMContext):
    keyboard = await get_acc_add_inl_keyboard(callback_data)
    await edit_reply_markup(keyboard, call_back.message.chat.id, call_back.message.message_id)


# # # Edit Value - Asq Question, wait for response, validate input and save in state.
async def set_value(call_back: CallbackQuery, state: FSMContext):
    key = call_back.data.split(".")[1] # set.{key}.{callback_data}

    question = fields_to_change[key]['question'];
    back_btn = btn("Back ↩️", f'back.{callback_data}')
    kb = InlineKeyboardBuilder()
    kb.add(back_btn)
    kb.adjust(1)
    keyboard = kb.as_markup()

    # `Sending Question with backBtn.
    msg = await send_message(call_back.message.chat.id, question, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

    await state.update_data(current_step=key, question_id=msg.message_id)
    await state.set_state(States.set_value)
