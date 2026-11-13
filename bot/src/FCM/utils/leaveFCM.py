from aiogram.fsm.context import FSMContext

async def leave_fsm(state: FSMContext):
    await state.clear()