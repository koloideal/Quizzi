from aiogram.fsm.state import State, StatesGroup


class UserMenuSG(StatesGroup):
    main = State()
    available_tests = State()
    edit_name = State()
    edit_group = State()


class UserRegistrationSG(StatesGroup):
    input_name = State()
    select_group = State()
