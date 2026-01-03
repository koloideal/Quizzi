import json

from aiogram.types import BufferedInputFile, CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.admin_dialogs.states import AdminMenuSG, AdminTemplatesSG
from trudex.infrastructure.database.dao.test import TestDAO
from trudex.infrastructure.database.repo.test import TestRepository


TEMPLATES_INFO = (
    "<b>📦 Шаблоны тестов</b>\n\n"
    "Шаблоны позволяют экспортировать и импортировать тесты в формате JSON.\n\n"
    "🔹 <b>Экспорт</b> — сохраните тест как файл для резервной копии или передачи\n"
    "🔹 <b>Импорт</b> — загрузите тест из файла\n"
    "🔹 <b>Спецификация</b> — описание формата JSON для создания тестов вручную"
)

SPEC_INFO = """<b>📋 Спецификация формата JSON</b>

<b>Структура файла:</b>
<code>{
  "title": "Название теста",
  "description": "Описание теста",
  "password": null,
  "attempts": null,
  "expires_at": null,
  "for_group": null,
  "questions": [...]
}</code>

<b>Поля теста:</b>
• <code>title</code> — название (обязательно, до 255 символов)
• <code>description</code> — описание (до 2000 символов)
• <code>password</code> — пароль для доступа или <code>null</code>
• <code>attempts</code> — лимит попыток (1-100) или <code>null</code>
• <code>expires_at</code> — срок действия в ISO формате или <code>null</code>
• <code>for_group</code> — номер группы или <code>null</code> для всех

<b>Типы вопросов:</b>
• <code>single</code> — один правильный ответ
• <code>multiple</code> — несколько правильных ответов
• <code>input</code> — ввод текста (регистр и пробелы игнорируются)

<b>Формат вопроса (single/multiple):</b>
<code>{
  "text": "Текст вопроса",
  "question_type": "single",
  "options": [
    {"text": "Вариант 1", "is_correct": true},
    {"text": "Вариант 2", "is_correct": false}
  ]
}</code>

<b>Формат вопроса (input):</b>
<code>{
  "text": "Текст вопроса",
  "question_type": "input",
  "correct_answer": "правильный ответ"
}</code>

<b>⚠️ Важно:</b>
• Для <code>single</code> — ровно один <code>is_correct: true</code>
• Для <code>multiple</code> — один или более <code>is_correct: true</code>
• Минимум 2 варианта ответа для single/multiple"""

TEMPLATE_SINGLE = {
    "title": "Пример теста с одиночным выбором",
    "description": "Демонстрация формата single вопросов",
    "password": None,
    "attempts": None,
    "expires_at": None,
    "for_group": None,
    "questions": [
        {
            "text": "Какой язык программирования используется для разработки Telegram ботов?",
            "question_type": "single",
            "options": [
                {"text": "Python", "is_correct": True},
                {"text": "HTML", "is_correct": False},
                {"text": "CSS", "is_correct": False},
            ],
        },
    ],
}

TEMPLATE_MULTIPLE = {
    "title": "Пример теста с множественным выбором",
    "description": "Демонстрация формата multiple вопросов",
    "password": None,
    "attempts": None,
    "expires_at": None,
    "for_group": None,
    "questions": [
        {
            "text": "Выберите языки программирования:",
            "question_type": "multiple",
            "options": [
                {"text": "Python", "is_correct": True},
                {"text": "JavaScript", "is_correct": True},
                {"text": "HTML", "is_correct": False},
                {"text": "CSS", "is_correct": False},
            ],
        },
    ],
}

TEMPLATE_INPUT = {
    "title": "Пример теста с вводом текста",
    "description": "Демонстрация формата input вопросов",
    "password": None,
    "attempts": None,
    "expires_at": None,
    "for_group": None,
    "questions": [
        {
            "text": "Как называется библиотека для создания Telegram ботов на Python?",
            "question_type": "input",
            "correct_answer": "aiogram",
        },
    ],
}

TEMPLATE_FULL = {
    "title": "Полный пример теста",
    "description": "Тест со всеми типами вопросов и настройками",
    "password": "secret123",
    "attempts": 3,
    "expires_at": "2026-12-31T23:59:59",
    "for_group": 1234,
    "questions": [
        {
            "text": "Выберите правильный ответ:",
            "question_type": "single",
            "options": [
                {"text": "Вариант A", "is_correct": False},
                {"text": "Вариант B", "is_correct": True},
                {"text": "Вариант C", "is_correct": False},
            ],
        },
        {
            "text": "Выберите все правильные ответы:",
            "question_type": "multiple",
            "options": [
                {"text": "Ответ 1", "is_correct": True},
                {"text": "Ответ 2", "is_correct": True},
                {"text": "Ответ 3", "is_correct": False},
            ],
        },
        {
            "text": "Введите ответ:",
            "question_type": "input",
            "correct_answer": "ответ",
        },
    ],
}


async def on_export_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminTemplatesSG.export_list)


async def on_import_clicked(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await _callback.answer("🚧 В разработке", show_alert=True)


async def on_spec_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminTemplatesSG.spec)


async def on_back_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


async def on_back_to_templates(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.switch_to(AdminTemplatesSG.main)


@inject
async def get_tests_for_export(test_dao: FromDishka[TestDAO], **_kwargs):
    tests = await test_dao.get_all()
    return {
        "tests": [(f"📝 {t.title}", t.id) for t in tests],
        "count": len(tests),
    }


@inject
async def on_test_selected_for_export(
    _callback: CallbackQuery,
    _widget: Select,  # type: ignore[type-arg]
    _manager: DialogManager,
    item_id: str,
    test_repo: FromDishka[TestRepository],
) -> None:
    test_id = int(item_id)
    test, questions_with_options = await test_repo.get_full_test(test_id)
    
    if not test:
        await _callback.answer("❌ Тест не найден")
        return
    
    export_data: dict = {
        "title": test.title,
        "description": test.description,
        "password": test.password,
        "attempts": test.attempts,
        "expires_at": test.expires_at.isoformat() if test.expires_at else None,
        "for_group": test.for_group,
        "questions": [],
    }
    
    questions_list: list = export_data["questions"]
    
    for question, options in questions_with_options:
        question_data: dict = {
            "text": question.text,
            "question_type": question.question_type,
        }
        
        if question.question_type == "input":
            correct_options = [o for o in options if o.is_correct]
            if correct_options:
                question_data["correct_answer"] = correct_options[0].text
        else:
            question_data["options"] = [
                {"text": o.text, "is_correct": o.is_correct}
                for o in options
            ]
        
        questions_list.append(question_data)
    
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in test.title)[:50]
    filename = f"{safe_title}.json"
    
    assert _callback.message is not None
    await _callback.message.answer_document(
        document=BufferedInputFile(json_str.encode("utf-8"), filename=filename),
        caption=f"📤 <b>Экспорт теста:</b> {test.title}",
    )


async def send_template(callback: CallbackQuery, template: dict, name: str) -> None:
    json_str = json.dumps(template, ensure_ascii=False, indent=2)
    filename = f"template_{name}.json"
    
    assert callback.message is not None
    await callback.message.answer_document(
        document=BufferedInputFile(json_str.encode("utf-8"), filename=filename),
        caption=f"📄 <b>Шаблон:</b> {template['title']}",
    )


async def on_template_single(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await send_template(_callback, TEMPLATE_SINGLE, "single")


async def on_template_multiple(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await send_template(_callback, TEMPLATE_MULTIPLE, "multiple")


async def on_template_input(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await send_template(_callback, TEMPLATE_INPUT, "input")


async def on_template_full(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await send_template(_callback, TEMPLATE_FULL, "full")


templates_dialog = Dialog(
    Window(
        Const(TEMPLATES_INFO),
        Row(
            Button(Const("📤 Экспорт"), id="export", on_click=on_export_clicked),
            Button(Const("📥 Импорт"), id="import", on_click=on_import_clicked),
        ),
        Button(Const("📋 Спецификация"), id="spec", on_click=on_spec_clicked),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_clicked),
        state=AdminTemplatesSG.main,
    ),
    Window(
        Format("<b>📤 Экспорт теста</b>\n\nВыберите тест для экспорта:\n\nВсего: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="test_select",
                item_id_getter=lambda x: x[1],
                items="tests",
                on_click=on_test_selected_for_export,  # type: ignore[arg-type]
            ),
            id="tests_scroll",
            width=1,
            height=7,
        ),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_templates),
        state=AdminTemplatesSG.export_list,
        getter=get_tests_for_export,
    ),
    Window(
        Const(SPEC_INFO),
        Row(
            Button(Const("📌 Single"), id="tpl_single", on_click=on_template_single),
            Button(Const("📋 Multiple"), id="tpl_multiple", on_click=on_template_multiple),
        ),
        Row(
            Button(Const("✏️ Input"), id="tpl_input", on_click=on_template_input),
            Button(Const("📦 Полный"), id="tpl_full", on_click=on_template_full),
        ),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_templates),
        state=AdminTemplatesSG.spec,
    ),
)
