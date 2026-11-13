from aiogram import Dispatcher, types
from aiogram.filters import StateFilter
from .state import States, callback_data
from .start import text_startswith_handler
from .waitForAction import cancel, cancelNo, cancelYes, confirm, edit, edit_back, set_value as set_value_action
from .set_value import set_value, set_value_return

def register_scene_acc_add_tx(dp: Dispatcher) -> None:
    # # Start
    dp.message.register(text_startswith_handler, lambda m: m.text and m.text.startswith('/'))

    # # Wait For Action
    dp.callback_query.register(confirm, lambda c: c.data == f'confirm.{callback_data}', StateFilter(States.wait_for_action))

    dp.callback_query.register(edit, lambda c: c.data == f'edit.{callback_data}', StateFilter(States.wait_for_action))
    dp.callback_query.register(edit_back, lambda c: c.data == f'back.{callback_data}', StateFilter(States.wait_for_action))
    dp.callback_query.register(set_value_action, lambda callBack: callBack.data.startswith('set.'), StateFilter(States.wait_for_action))

    dp.callback_query.register(cancel, lambda c: c.data == f'cancel.{callback_data}', StateFilter(States.wait_for_action))
    dp.callback_query.register(cancelNo, lambda c: c.data == f'cancel-no.{callback_data}', StateFilter(States.wait_for_action))
    dp.callback_query.register(cancelYes, lambda c: c.data == f'cancel-yes.{callback_data}', StateFilter(States.wait_for_action))

    # # SET VALUE
    dp.callback_query.register(set_value_return, lambda c: c.data == f'back.{callback_data}', StateFilter(States.set_value))
    dp.message.register(set_value, StateFilter(States.set_value))
