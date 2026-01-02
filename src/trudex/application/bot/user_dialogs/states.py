from aiogram.fsm.state import State, StatesGroup


class UserMenuSG(StatesGroup):
    main = State()


class UserRegistrationSG(StatesGroup):
    input_name = State()
    select_group = State()
