from aiogram.fsm.state import State, StatesGroup


class AdminMenuSG(StatesGroup):
    main = State()


class AdminUsersSG(StatesGroup):
    users_list = State()
    users_input = State()
    user_detail = State()
    user_stats = State()
    user_result_detail = State()
