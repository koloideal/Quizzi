from aiogram.fsm.state import State, StatesGroup


class CreatorMenuSG(StatesGroup):
    main = State()


class CreatorUsersSG(StatesGroup):
    users_list = State()
    users_input = State()
    user_detail = State()
    make_admin_confirm = State()


class CreatorTestsSG(StatesGroup):
    tests_list = State()


class CreatorBroadcastSG(StatesGroup):
    broadcast_input = State()
    broadcast_confirm = State()
