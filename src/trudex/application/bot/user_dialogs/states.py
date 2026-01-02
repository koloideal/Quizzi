from aiogram.fsm.state import State, StatesGroup


class UserMenuSG(StatesGroup):
    main = State()


class UserRegistrationSG(StatesGroup):
    select_group = State()
