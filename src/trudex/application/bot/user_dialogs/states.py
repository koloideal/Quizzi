from aiogram.fsm.state import State, StatesGroup


class UserMenuSG(StatesGroup):
    main = State()
    available_tests = State()
    test_detail = State()
    edit_name = State()
    edit_group = State()
    my_results = State()
    result_detail = State()


class UserTestSG(StatesGroup):
    password_input = State()
    question_single = State()
    question_multiple = State()
    question_input = State()
    results = State()
    detailed_results = State()


class UserRegistrationSG(StatesGroup):
    input_name = State()
    select_group = State()
