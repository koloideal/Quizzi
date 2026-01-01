from aiogram.fsm.state import State, StatesGroup


class AdminMenuSG(StatesGroup):
    main = State()
    users_list = State()
    users_input = State()
    user_detail = State()
    broadcast_input = State()
    broadcast_confirm = State()
