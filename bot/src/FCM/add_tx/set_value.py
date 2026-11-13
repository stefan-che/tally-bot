from colorama import Fore
import numexpr as ne
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext  # FSM

from app.utils import visualise, exception_with_line, validate_num
from src import edit_message, delete_message
from src.keyboards import btn, get_acc_add_inl_keyboard

from .state import callback_data, fields_to_change, States
from .utils import get_tx_mes, parse_date_string


# cancel.acc_add_amount
async def set_value(msg: Message, state: FSMContext):
    data = await state.get_data();
    visualise(data, "set_value state_data :::")

    text = msg.text
    current_step = data["current_step"]
    message_id = data["message_id"]
    question_id = data["question_id"]
    account = data["account"]
    amount = data["amount"]
    time = data["time"]
    comment = data["comment"]

    try:
        if current_step == "amount":
            print("set_value text", text)
            validate_input = validate_num.validate_num(text)
            print(Fore.GREEN,validate_input, Fore.BLACK)
            amount = ne.evaluate(validate_input)
        elif current_step == "time":
            date, time = parse_date_string(text)
            print("time")
        elif current_step == "comment":
                print("Comment")
        else:
            raise f"Unknown Step {current_step}"

        await state.update_data(amount=amount, time=time, comment=comment)
        await state.set_state(States.wait_for_action)

        tx_msg = get_tx_mes(account, amount, time, comment)
        keyboard = await get_acc_add_inl_keyboard(callback_data)
        await edit_message(tx_msg, msg.chat.id, message_id, reply_markup=keyboard)
    except Exception as e:
        print(Fore.RED+"ERROR:", e)
        exception_with_line()

        error_msg = fields_to_change[current_step]['error']
        back_btn = btn("Back ↩️", f'back.{callback_data}')
        kb = InlineKeyboardBuilder()
        kb.add(back_btn)
        kb.adjust(1)
        keyboard = kb.as_markup()
        newMsg = await msg.answer(error_msg, reply_markup=keyboard)
        await state.update_data(question_id=newMsg.message_id)
    finally:
        await delete_message(msg.chat.id, msg.message_id);
        await delete_message(msg.chat.id, question_id);


async def set_value_return(call_back: CallbackQuery, state: FSMContext):
    data = await state.get_data();
    question_id = data["question_id"]
    await delete_message(call_back.message.chat.id, question_id);
    await state.set_state(States.wait_for_action);