from aiogram.fsm.state import State, StatesGroup


class SharedTemplatesSG(StatesGroup):
    main = State()
    export_list = State()
    spec = State()
    import_file = State()


class SharedTestsSG(StatesGroup):
    tests_list = State()
    test_detail = State()
    share_test = State()
    edit_menu = State()
    edit_password = State()
    edit_attempts = State()
    edit_time_limit = State()
    edit_group = State()
    edit_expires = State()
    statistics = State()
    attempt_detail = State()
    export_select_group = State()
    delete_confirm = State()


class SharedBroadcastSG(StatesGroup):
    select_groups = State()
    broadcast_input = State()
    broadcast_confirm = State()


class SharedGroupsSG(StatesGroup):
    groups_list = State()
    add_group_input_number = State()
    delete_groups_list = State()
    delete_confirm = State()


class SharedCreateTestSG(StatesGroup):
    input_title = State()
    input_description = State()
    input_password = State()
    input_attempts = State()
    input_time_limit = State()
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
