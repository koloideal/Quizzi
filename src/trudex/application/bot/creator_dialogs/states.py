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


class CreatorGroupsSG(StatesGroup):
    groups_list = State()
    add_group_input_number = State()
    delete_groups_list = State()
    delete_confirm = State()


class CreateTestSG(StatesGroup):
    input_title = State()
    input_description = State()
    input_password = State()
    input_expires_at = State()
    input_for_group = State()
    confirm_test_info = State()
    add_question = State()
    input_question_text = State()
    select_question_type = State()
    input_correct_answer = State()
    input_options = State()
    mark_correct_options = State()
    confirm_question = State()
    test_created = State()
