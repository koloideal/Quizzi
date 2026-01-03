import json

from aiogram.types import BufferedInputFile, CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.creator_dialogs.states import CreatorMenuSG, CreatorTemplatesSG
from trudex.infrastructure.database.dao.test import TestDAO
from trudex.infrastructure.database.repo.test import TestRepository


TEMPLATES_INFO = (
    "<b>📦 Шаблоны тестов</b>\n\n"
    "Шаблоны позволяют экспортировать и импортировать тесты в формате JSON.\n\n"
    "🔹 <b>Экспорт</b> — сохраните тест как файл для резервной копии или передачи\n"
    "🔹 <b>Импорт</b> — загрузите тест из файла\n"
    "🔹 <b>Спецификация</b> — описание формата JSON для создания тестов вручную"
)


async def on_export_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.switch_to(CreatorTemplatesSG.export_list)


async def on_import_clicked(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await _callback.answer("🚧 В разработке", show_alert=True)


async def on_spec_clicked(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await _callback.answer("🚧 В разработке", show_alert=True)


async def on_back_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(CreatorMenuSG.main, mode=StartMode.RESET_STACK)


async def on_back_to_templates(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.switch_to(CreatorTemplatesSG.main)


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
    
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in test.title)[:50]
    filename = f"{safe_title}.json"
    
    assert _callback.message is not None
    await _callback.message.answer_document(
        document=BufferedInputFile(json_str.encode("utf-8"), filename=filename),
        caption=f"📤 <b>Экспорт теста:</b> {test.title}",
    )


templates_dialog = Dialog(
    Window(
        Const(TEMPLATES_INFO),
        Row(
            Button(Const("📤 Экспорт"), id="export", on_click=on_export_clicked),
            Button(Const("📥 Импорт"), id="import", on_click=on_import_clicked),
        ),
        Button(Const("📋 Спецификация"), id="spec", on_click=on_spec_clicked),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_clicked),
        state=CreatorTemplatesSG.main,
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
        state=CreatorTemplatesSG.export_list,
        getter=get_tests_for_export,
    ),
)
