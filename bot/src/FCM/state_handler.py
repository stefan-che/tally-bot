from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext # FSM
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import Command, StateFilter
import os


class ClientState(StatesGroup):
    '''This is the Steps, that have to be done'''
    name = State()
    editName = State()
    age = State()
    proffesion = State()


async def startClient(msg: types.Message, state: FSMContext) -> None:
    await msg.answer(f'{msg.from_user.username}, enter your name')
    await state.set_state(ClientState.name)

# Called when the user is entering their name
async def setName(msg: types.Message, state: FSMContext) -> None:
    user_msg = msg.text;
    await state.update_data(NAME=user_msg);

    s = await state.get_state()
    d = await state.get_data()
    print(s, d);

    await msg.answer(f'Thank you {user_msg}, how old are you?')
    await state.set_state(ClientState.age);

async def setAge(msg: types.Message, state: FSMContext) -> None:
    user_msg = msg.text;
    await state.update_data(AGE=user_msg);
    s = await state.get_state()
    d = await state.get_data()
    print(s, d);

    await msg.answer(f'Thank you, your age: {user_msg}')
    await state.set_state(ClientState.editName);

async def backToName(msg: types.Message, state: FSMContext) -> None:
    user_msg = msg.text;
    d = await state.get_data()

    # d is {'NAME': 'LK', 'AGE': 'ew', 'NEW_NAME': 'asd', 'attemps': 1}
    if 'attemps' in d:
        attemps = d['attemps'] + 1; # Error Here - AttributeError: 'dict' object has no attribute 'attemps'
    else:
        attemps = 1
        
    await state.update_data(NEW_NAME=user_msg, attemps=attemps);

    s = await state.get_state()
    print(s, d);

    await msg.answer(f'New name: {attemps} ::: {user_msg}, your name?')
    await state.set_state(ClientState.name);

async def exit(msg: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        # User is not in any state, ignoring
        return

    # Cancel state and inform user about it
    await state.clear()
    await msg.reply('Exited.')


def register_scene1(dp: Dispatcher) -> None:
    dp.message.register(startClient, Command(commands=['test']))

    dp.message.register(backToName, Command(commands=['exit']), StateFilter('*'))
    dp.message.register(setName, StateFilter(ClientState.name))
    dp.message.register(setAge, StateFilter(ClientState.age))
    dp.message.register(backToName, StateFilter(ClientState.editName))