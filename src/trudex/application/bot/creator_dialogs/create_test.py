from datetime import date, datetime

from aiogram.types import CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (Button, Calendar, Cancel, Column, Row,
                                        ScrollingGroup, Select)
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.creator_dialogs.states import (CreateTestSG,
                                                           CreatorTestsSG)
from trudex.infrastructure.database.dao.group import GroupDAO
from trudex.infrastructure.database.dao.option import OptionDAO
from trudex.infrastructure.database.dao.question import QuestionDAO
from trudex.infrastructure.database.dao.test import TestDAO
from trudex.infrastructure.database.repo.test import TestRepository


async def on_title_input(message: Message, _widget: MessageInput, manager: DialogManager):
    if not message.text:
        await message.answer("❌ Название не может быть пустым")
        return
    
    title = message.text.strip()
    if not title:
        await message.answer("❌ Название не может быть пустым")
        return
    
    if len(title) > 255:
        await message.answer("❌ Название слишком длинное (максимум 255 символов)")
        return
    
    manager.dialog_data["title"] = title
    await manager.switch_to(CreateTestSG.input_description)


async def on_description_input(message: Message, _widget: MessageInput, manager: DialogManager):
    if not message.text:
        await message.answer("❌ Описание не может быть пустым")
        return
    
    description = message.text.strip()
    if not description:
        await message.answer("❌ Описание не может быть пустым")
        return
    
    if len(description) > 2000:
        await message.answer("❌ Описание слишком длинное (максимум 2000 символов)")
        return
    
    manager.dialog_data["description"] = description
    await manager.switch_to(CreateTestSG.input_password)


@inject
async def on_password_input(message: Message, _widget: MessageInput, manager: DialogManager, group_dao: FromDishka[GroupDAO]):
    if not message.text:
        await message.answer("❌ Пароль не может быть пустым")
        return
    
    password = message.text.strip()
    if not password:
        await message.answer("❌ Пароль не может быть пустым")
        return
    
    if len(password) > 255:
        await message.answer("❌ Пароль слишком длинный (максимум 255 символов)")
        return
    
    manager.dialog_data["password"] = password
    await manager.switch_to(CreateTestSG.input_attempts)


@inject
async def on_skip_password(_callback: CallbackQuery, _button: Button, manager: DialogManager, group_dao: FromDishka[GroupDAO]):
    manager.dialog_data["password"] = None
    await manager.switch_to(CreateTestSG.input_attempts)


async def on_attempts_input(message: Message, _widget: MessageInput, manager: DialogManager):
    if not message.text:
        await message.answer("❌ Количество попыток не может быть пустым")
        return
    
    attempts_str = message.text.strip()
    
    if not attempts_str.isdigit():
        await message.answer("❌ Количество попыток должно быть числом")
        return
    
    attempts = int(attempts_str)
    
    if attempts < 1:
        await message.answer("❌ Количество попыток должно быть больше 0")
        return
    
    if attempts > 100:
        await message.answer("❌ Количество попыток не может быть больше 100")
        return
    
    manager.dialog_data["attempts"] = attempts
    await manager.switch_to(CreateTestSG.input_expires_at)


async def on_skip_attempts(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    manager.dialog_data["attempts"] = None
    await manager.switch_to(CreateTestSG.input_expires_at)


async def on_date_selected(_callback, _widget, manager: DialogManager, selected_date: date):
    manager.dialog_data["expires_at"] = datetime.combine(selected_date, datetime.min.time())
    await manager.switch_to(CreateTestSG.input_for_group)


async def on_skip_expires(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    manager.dialog_data["expires_at"] = None
    await manager.switch_to(CreateTestSG.input_for_group)


@inject
async def get_groups_for_test(dialog_manager: DialogManager, group_dao: FromDishka[GroupDAO], **_kwargs):
    groups = await group_dao.get_all()
    
    return {
        "groups": [(str(g.number), str(g.number)) for g in groups],
    }


async def on_group_selected(_callback: CallbackQuery, _widget, manager: DialogManager, item_id: str):
    manager.dialog_data["for_group"] = int(item_id)
    await manager.switch_to(CreateTestSG.confirm_test_info)


async def on_skip_group(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    manager.dialog_data["for_group"] = None
    await manager.switch_to(CreateTestSG.confirm_test_info)


async def get_test_info(dialog_manager: DialogManager, **_kwargs):
    title = dialog_manager.dialog_data.get("title", "—")
    description = dialog_manager.dialog_data.get("description", "—")
    password = dialog_manager.dialog_data.get("password")
    attempts = dialog_manager.dialog_data.get("attempts")
    expires_at = dialog_manager.dialog_data.get("expires_at")
    for_group = dialog_manager.dialog_data.get("for_group")
    
    password_str = f"🔒 {password}" if password else "Без пароля"
    attempts_str = f"🔄 {attempts}" if attempts else "♾️ Без ограничений"
    expires_str = expires_at.strftime("%d.%m.%Y") if expires_at else "Без срока"
    group_str = str(for_group) if for_group else "Для всех"
    
    return {
        "info": (
            f"<b>📝 Информация о тесте</b>\n\n"
            f"<b>Название:</b> {title}\n"
            f"<b>Описание:</b> {description}\n"
            f"<b>Пароль:</b> {password_str}\n"
            f"<b>Попыток:</b> {attempts_str}\n"
            f"<b>Истекает:</b> {expires_str}\n"
            f"<b>Для группы:</b> {group_str}"
        )
    }


@inject
async def on_confirm_test(_callback: CallbackQuery, _button: Button, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    title = manager.dialog_data.get("title")
    assert isinstance(title, str)
    description = manager.dialog_data.get("description")
    password = manager.dialog_data.get("password")
    attempts = manager.dialog_data.get("attempts")
    expires_at = manager.dialog_data.get("expires_at")
    for_group = manager.dialog_data.get("for_group")
    
    test = await test_dao.create(
        title=title,
        description=description,
        password=password,
        attempts=attempts,
        expires_at=expires_at,
        for_group=for_group,
    )
    
    manager.dialog_data["test_id"] = test.id
    manager.dialog_data["questions"] = []
    await manager.switch_to(CreateTestSG.add_question)


async def on_add_question(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    manager.dialog_data["current_question"] = {}
    await manager.switch_to(CreateTestSG.input_question_text)


async def on_question_input(message: Message, _widget: MessageInput, manager: DialogManager):
    current_question = manager.dialog_data.get("current_question", {})
    
    if message.content_type == ContentType.PHOTO:
        photo = message.photo[-1] if message.photo else None
        if photo:
            text = (message.caption or "").strip()
            if not text:
                await message.answer("❌ Изображение должно содержать подпись с текстом вопроса")
                return
            if len(text) > 2000:
                await message.answer("❌ Текст вопроса слишком длинный (максимум 2000 символов)")
                return
            current_question["tg_file_id"] = photo.file_id
            current_question["text"] = text
    elif message.content_type == ContentType.TEXT and message.text:
        text = message.text.strip()
        if not text:
            await message.answer("❌ Текст вопроса не может быть пустым")
            return
        if len(text) > 2000:
            await message.answer("❌ Текст вопроса слишком длинный (максимум 2000 символов)")
            return
        current_question["text"] = text
        current_question["tg_file_id"] = None
    else:
        await message.answer("❌ Отправьте текст или фото с подписью")
        return
    
    manager.dialog_data["current_question"] = current_question
    await manager.switch_to(CreateTestSG.select_question_type)


async def get_question_type_data(**_kwargs):
    return {
        "question_types": [
            ("single", "📌 Один правильный ответ"),
            ("multiple", "� Несколько правильных ответов"),
            ("input", "✏️ Ввод текста"),
        ]
    }


async def on_question_type_selected(_callback: CallbackQuery, _widget, manager: DialogManager, item_id: str):
    current_question = manager.dialog_data.get("current_question", {})
    current_question["question_type"] = item_id
    manager.dialog_data["current_question"] = current_question
    
    if item_id == "input":
        await manager.switch_to(CreateTestSG.input_correct_answer)
    else:
        manager.dialog_data["current_options"] = []
        await manager.switch_to(CreateTestSG.input_options)


async def on_correct_answer_input(message: Message, _widget: MessageInput, manager: DialogManager):
    if not message.text:
        await message.answer("❌ Правильный ответ не может быть пустым")
        return
    
    answer = message.text.strip()
    if not answer:
        await message.answer("❌ Правильный ответ не может быть пустым")
        return
    
    if len(answer) > 255:
        await message.answer("❌ Ответ слишком длинный (максимум 255 символов)")
        return
    
    current_question = manager.dialog_data.get("current_question", {})
    current_question["correct_answer"] = answer
    manager.dialog_data["current_question"] = current_question
    await manager.switch_to(CreateTestSG.confirm_question)


async def on_option_input(message: Message, _widget: MessageInput, manager: DialogManager):
    if not message.text:
        await message.answer("❌ Вариант ответа не может быть пустым")
        return
    
    option_text = message.text.strip()
    if not option_text:
        await message.answer("❌ Вариант ответа не может быть пустым")
        return
    
    if len(option_text) > 255:
        await message.answer("❌ Вариант ответа слишком длинный (максимум 255 символов)")
        return
    
    current_options = manager.dialog_data.get("current_options", [])
    
    if len(current_options) >= 10:
        await message.answer("❌ Максимум 10 вариантов ответа")
        return
    
    current_options.append({"text": option_text, "is_correct": False})
    manager.dialog_data["current_options"] = current_options
    
    await message.answer(f"✅ Вариант {len(current_options)} добавлен")


async def on_finish_options(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    current_options = manager.dialog_data.get("current_options", [])
    if len(current_options) < 2:
        await _callback.answer("❌ Добавьте минимум 2 варианта ответа", show_alert=True)
        return
    
    await manager.switch_to(CreateTestSG.mark_correct_options)


async def get_options_data(dialog_manager: DialogManager, **_kwargs):
    current_options = dialog_manager.dialog_data.get("current_options", [])
    formatted_options = []
    for i, opt in enumerate(current_options):
        marker = "✅" if opt["is_correct"] else "❌"
        formatted_options.append((str(i), f"{marker} {opt['text']}"))
    return {
        "options": formatted_options,
        "options_count": len(current_options),
    }


async def on_option_toggle(_callback: CallbackQuery, _widget, manager: DialogManager, item_id: str):
    current_options = manager.dialog_data.get("current_options", [])
    current_question = manager.dialog_data.get("current_question", {})
    question_type = current_question.get("question_type", "single")
    
    option_idx = int(item_id)
    
    if question_type == "single":
        for opt in current_options:
            opt["is_correct"] = False
        current_options[option_idx]["is_correct"] = True
    else:
        current_options[option_idx]["is_correct"] = not current_options[option_idx]["is_correct"]
    
    manager.dialog_data["current_options"] = current_options
    await _callback.answer()


async def on_confirm_correct(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    current_options = manager.dialog_data.get("current_options", [])
    
    if not any(opt["is_correct"] for opt in current_options):
        await _callback.answer("❌ Отметьте хотя бы один правильный ответ", show_alert=True)
        return
    
    await manager.switch_to(CreateTestSG.confirm_question)


async def get_question_preview(dialog_manager: DialogManager, **_kwargs):
    current_question = dialog_manager.dialog_data.get("current_question", {})
    current_options = dialog_manager.dialog_data.get("current_options", [])
    
    text = current_question.get("text", "")
    question_type = current_question.get("question_type", "single")
    has_image = current_question.get("tg_file_id") is not None
    
    type_names = {
        "single": "📌 Один правильный ответ",
        "multiple": "📋 Несколько правильных ответов",
        "input": "✏️ Ввод текста",
    }
    
    preview = f"<b>📝 Предпросмотр вопроса</b>\n\n"
    preview += f"<b>Текст:</b> {text}\n"
    preview += f"<b>Тип:</b> {type_names[question_type]}\n"
    preview += f"<b>Изображение:</b> {'✅ Да' if has_image else '❌ Нет'}\n\n"
    
    if question_type == "input":
        correct_answer = current_question.get("correct_answer", "")
        preview += f"<b>Правильный ответ:</b> <code>{correct_answer}</code>"
    else:
        preview += "<b>Варианты ответов:</b>\n"
        for i, opt in enumerate(current_options, 1):
            marker = "✅" if opt["is_correct"] else "❌"
            preview += f"{i}. {marker} {opt['text']}\n"
    
    return {"preview": preview}


@inject
async def on_save_question(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    question_dao: FromDishka[QuestionDAO],
    option_dao: FromDishka[OptionDAO],
    test_repo: FromDishka[TestRepository],
):
    test_id = manager.dialog_data.get("test_id")
    assert isinstance(test_id, int)
    current_question = manager.dialog_data.get("current_question", {})
    current_options = manager.dialog_data.get("current_options", [])
    
    questions_count = await test_repo.count_questions_in_test(test_id)
    
    question = await question_dao.create(
        test_id=test_id,
        text=current_question.get("text", ""),
        position=questions_count,
        question_type=current_question.get("question_type", "single"),
        tg_file_id=current_question.get("tg_file_id"),
    )
    
    if current_question.get("question_type") == "input":
        await option_dao.create(
            question_id=question.id,
            text=current_question.get("correct_answer", ""),
            is_correct=True,
        )
    else:
        for opt in current_options:
            await option_dao.create(
                question_id=question.id,
                text=opt["text"],
                is_correct=opt["is_correct"],
            )
    
    questions = manager.dialog_data.get("questions", [])
    questions.append(question.id)
    manager.dialog_data["questions"] = questions
    
    manager.dialog_data.pop("current_question", None)
    manager.dialog_data.pop("current_options", None)
    
    await _callback.answer("✅ Вопрос добавлен")
    await manager.switch_to(CreateTestSG.add_question)


async def on_cancel_question(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    manager.dialog_data.pop("current_question", None)
    manager.dialog_data.pop("current_options", None)
    await manager.switch_to(CreateTestSG.add_question)


async def get_questions_count(dialog_manager: DialogManager, **_kwargs):
    questions = dialog_manager.dialog_data.get("questions", [])
    return {"questions_count": len(questions)}


async def on_finish_test(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    questions = manager.dialog_data.get("questions", [])
    
    if len(questions) == 0:
        await _callback.answer("❌ Добавьте хотя бы один вопрос", show_alert=True)
        return
    
    await _callback.answer("✅ Тест создан")
    await manager.start(CreatorTestsSG.tests_list, mode=StartMode.RESET_STACK)


async def on_cancel(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(CreatorTestsSG.tests_list, mode=StartMode.RESET_STACK)


create_test_dialog = Dialog(
    Window(
        Const("<b>📝 Создание теста</b>\n\n💬 <b>Введите название теста:</b>\n<i>(максимум 255 символов)</i>"),
        MessageInput(on_title_input),
        Cancel(Const("◀️ Отмена")),
        state=CreateTestSG.input_title,
    ),
    Window(
        Const("<b>📝 Создание теста</b>\n\n📄 <b>Введите описание теста:</b>\n<i>(максимум 2000 символов)</i>"),
        MessageInput(on_description_input),
        state=CreateTestSG.input_description,
    ),
    Window(
        Const("<b>🔒 Пароль</b>\n\n🔑 <b>Введите пароль для доступа к тесту</b> или пропустите этот шаг:\n<i>(максимум 255 символов)</i>"),
        MessageInput(on_password_input),
        Button(Const("⏭️ Без пароля"), id="skip_password", on_click=on_skip_password),
        state=CreateTestSG.input_password,
    ),
    Window(
        Const("<b>🔄 Количество попыток</b>\n\n🔢 <b>Введите количество попыток</b> (1-100) или пропустите для неограниченного количества:"),
        MessageInput(on_attempts_input),
        Button(Const("⏭️ Без ограничений"), id="skip_attempts", on_click=on_skip_attempts),
        state=CreateTestSG.input_attempts,
    ),
    Window(
        Const("<b>📅 Срок действия</b>\n\n🗓 <b>Выберите дату истечения теста</b> или пропустите:"),
        Calendar(id="calendar", on_click=on_date_selected),
        Button(Const("⏭️ Без срока"), id="skip_expires", on_click=on_skip_expires),
        state=CreateTestSG.input_expires_at,
    ),
    Window(
        Const("<b>👥 Группа</b>\n\n🎓 <b>Выберите группу</b> или пропустите для всех:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="groups",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_selected,
            ),
            id="groups_scroll",
            width=2,
            height=7,
        ),
        Button(Const("⏭️ Для всех"), id="skip_group", on_click=on_skip_group),
        state=CreateTestSG.input_for_group,
        getter=get_groups_for_test,
    ),
    Window(
        Format("{info}\n\n<b>✅ Подтвердите создание теста:</b>"),
        Row(
            Button(Const("✅ Создать"), id="confirm", on_click=on_confirm_test),
            Button(Const("❌ Отмена"), id="cancel", on_click=on_cancel),
        ),
        state=CreateTestSG.confirm_test_info,
        getter=get_test_info,
    ),
    Window(
        Format("<b>➕ Добавление вопросов</b>\n\n📊 <b>Вопросов добавлено:</b> {questions_count}\n\n💡 Добавьте вопросы к тесту:"),
        Column(
            Button(Const("➕ Добавить вопрос"), id="add_question", on_click=on_add_question),
            Button(Const("✅ Завершить создание"), id="finish", on_click=on_finish_test),
        ),
        state=CreateTestSG.add_question,
        getter=get_questions_count,
    ),
    Window(
        Const("<b>❓ Текст вопроса</b>\n\n📝 <b>Отправьте текст вопроса</b> или 📷 <b>фото с подписью:</b>\n<i>(максимум 2000 символов)</i>"),
        MessageInput(on_question_input, content_types=[ContentType.TEXT, ContentType.PHOTO]),
        Button(Const("◀️ Назад"), id="back", on_click=on_cancel_question),
        state=CreateTestSG.input_question_text,
    ),
    Window(
        Const("<b>📋 Тип вопроса</b>\n\n🎯 <b>Выберите тип вопроса:</b>"),
        Column(Select(
            Format("{item[1]}"),
            id="question_type",
            item_id_getter=lambda x: x[0],
            items="question_types",
            on_click=on_question_type_selected,
        )),
        Button(Const("◀️ Назад"), id="back", on_click=on_cancel_question),
        state=CreateTestSG.select_question_type,
        getter=get_question_type_data,
    ),
    Window(
        Const("<b>✏️ Правильный ответ</b>\n\n💬 <b>Введите правильный ответ</b> (для проверки будет использоваться точное совпадение):\n<i>(максимум 255 символов)</i>"),
        MessageInput(on_correct_answer_input),
        Button(Const("◀️ Назад"), id="back", on_click=on_cancel_question),
        state=CreateTestSG.input_correct_answer,
    ),
    Window(
        Format("<b>📝 Варианты ответов</b>\n\n📊 <b>Добавлено вариантов:</b> {options_count}/10\n\n💬 <b>Введите вариант ответа:</b>\n<i>(максимум 255 символов)</i>"),
        MessageInput(on_option_input),
        Button(Const("✅ Завершить добавление вариантов"), id="finish_options", on_click=on_finish_options),
        Button(Const("◀️ Назад"), id="back", on_click=on_cancel_question),
        state=CreateTestSG.input_options,
        getter=get_options_data,
    ),
    Window(
        Const("<b>✅ Правильные ответы</b>\n\n<b>Отметьте правильные варианты ответов:</b>"),
        Column(Select(
            Format("{item[1]}"),
            id="options",
            item_id_getter=lambda x: x[0],
            items="options",
            on_click=on_option_toggle,
        )),
        Button(Const("✅ Подтвердить выбор"), id="confirm", on_click=on_confirm_correct),
        Button(Const("◀️ Назад"), id="back", on_click=on_cancel_question),
        state=CreateTestSG.mark_correct_options,
        getter=get_options_data,
    ),
    Window(
        Format("{preview}\n\n<b>💾 Сохранить вопрос?</b>"),
        Row(
            Button(Const("✅ Сохранить"), id="save", on_click=on_save_question),
            Button(Const("❌ Отмена"), id="cancel", on_click=on_cancel_question),
        ),
        state=CreateTestSG.confirm_question,
        getter=get_question_preview,
    ),
)
