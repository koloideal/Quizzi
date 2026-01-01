from aiogram.fsm.state import State, StatesGroup


class CreatorMenuSG(StatesGroup):
    main = State()
    users_list = State()
    users_input = State()
    user_detail = State()
    make_admin_confirm = State()
    broadcast_input = State()
    broadcast_confirm = State()
