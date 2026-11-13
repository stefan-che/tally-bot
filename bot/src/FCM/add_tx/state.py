from aiogram.fsm.state import StatesGroup, State

class States(StatesGroup):
    '''This is the Steps, that have to be done'''
    wait_for_action = State()
    set_value = State()

callback_data = "acc_add_amoun"

fields_to_change = {
    "amount": {
        "title": "Amount 💵",
        "question": "Enter the new amount",
        "error": "Something is wrong with your expression.",
    },
    "time": {
        "title": "Date and time 🕓",
        "question": "Enter the new date:\n*<dd mm yyyy> <hh mm>*",
        "error": "Something is wrong with the input...\nPlease check the format:\n\n*<dd mm yyyy> <hh mm>*",
    },
    "comment": {
        "title": "Comment 💬",
        "question": "Enter the new amount",
        "error": "Something is wrong with your expression.",
    },
}