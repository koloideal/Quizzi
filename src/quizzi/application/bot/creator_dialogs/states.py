from aiogram.fsm.state import State, StatesGroup


class CreatorMenuSG(StatesGroup):
    main = State()


class CreatorUsersSG(StatesGroup):
    users_list = State()
    users_input = State()
    user_detail = State()
    user_stats = State()
    user_result_detail = State()
    make_admin_confirm = State()
    remove_admin_confirm = State()
