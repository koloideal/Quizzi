from aiogram.fsm.state import State, StatesGroup


class AdminMenuSG(StatesGroup):
    main = State()


class AdminUsersSG(StatesGroup):
    users_list = State()
    users_input = State()
    user_detail = State()


class AdminTestsSG(StatesGroup):
    tests_list = State()


class AdminBroadcastSG(StatesGroup):
    broadcast_input = State()
    broadcast_confirm = State()


class AdminGroupsSG(StatesGroup):
    groups_list = State()
    add_group_input_number = State()
    delete_groups_list = State()
    delete_confirm = State()
