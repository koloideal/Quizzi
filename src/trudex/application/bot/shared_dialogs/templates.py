import json

from aiogram import Bot
from aiogram.types import BufferedInputFile, CallbackQuery, ContentType, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.shared_dialogs.states import SharedTemplatesSG, SharedTestsSG
from trudex.domain.schemas import QuestionType
from trudex.domain.test_parser import ParsedTest, TestParser
from trudex.infrastructure.database.dao.option import OptionDAO
from trudex.infrastructure.database.dao.question import QuestionDAO
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
  "question_type": "single",
  "question": "Текст вопроса",
  "answers": [
    {"option": "Вариант 1", "is_correct": true},
    {"option": "Вариант 2", "is_correct": false}
  ]
}</code>

<b>Формат вопроса (input):</b>
<code>{
  "question_type": "input",
  "question": "Текст вопроса",
  "correct_answer": "правильный ответ"
}</code>

<b>⚠️ Важно:</b>
• Для <code>single</code> — ровно один <code>is_correct: true</code>
• Для <code>multiple</code> — один или более <code>is_correct: true</code>
• Минимум 2 варианта ответа для single/multiple"""


TEMPLATE_ULTIMATE = """// ═══════════════════════════════════════════════════════════════
// УЛЬТИМАТИВНЫЙ ШАБЛОН ТЕСТА
// ═══════════════════════════════════════════════════════════════
// 
// 📝 Название: Ультимативный пример теста
// 📄 Описание: Полная демонстрация всех возможностей формата
// 
// ⚙️ НАСТРОЙКИ:
//    • Пароль: test2024
//    • Попыток: 5
//    • Срок действия: 31 декабря 2026, 23:59
//    • Для группы: 2024 (или null для всех)
// 
// ❓ ВОПРОСЫ (всего 6):
//    1. [single]   - Один правильный ответ (3 варианта)
//    2. [single]   - Один правильный ответ (4 варианта)
//    3. [multiple] - Несколько правильных (4 варианта, 2 верных)
//    4. [multiple] - Несколько правильных (5 вариантов, 3 верных)
//    5. [input]    - Ввод текста (точный ответ)
//    6. [input]    - Ввод текста (регистр игнорируется)
// 
// 💡 ПОДСКАЗКИ:
//    • null означает "не задано" / "без ограничений"
//    • expires_at в формате ISO 8601: YYYY-MM-DDTHH:MM:SS
//    • for_group - номер группы или null для всех пользователей
// 
// ═══════════════════════════════════════════════════════════════

{
  "title": "Ультимативный пример теста",
  "description": "Полная демонстрация всех возможностей формата: разные типы вопросов, настройки доступа, ограничения по времени и группам",
  "password": "test2024",
  "attempts": 5,
  "expires_at": "2026-12-31T23:59:59",
  "for_group": 2024,
  "questions": [
    {
      "question_type": "single",
      "question": "Какой язык программирования чаще всего используется для создания Telegram ботов?",
      "answers": [
        {"option": "Python", "is_correct": true},
        {"option": "HTML", "is_correct": false},
        {"option": "CSS", "is_correct": false}
      ]
    },
    {
      "question_type": "single",
      "question": "Сколько байт в одном килобайте?",
      "answers": [
        {"option": "100", "is_correct": false},
        {"option": "1000", "is_correct": false},
        {"option": "1024", "is_correct": true},
        {"option": "2048", "is_correct": false}
      ]
    },
    {
      "question_type": "multiple",
      "question": "Выберите все языки программирования из списка:",
      "answers": [
        {"option": "Python", "is_correct": true},
        {"option": "JavaScript", "is_correct": true},
        {"option": "HTML", "is_correct": false},
        {"option": "CSS", "is_correct": false}
      ]
    },
    {
      "question_type": "multiple",
      "question": "Какие из перечисленных являются базами данных?",
      "answers": [
        {"option": "PostgreSQL", "is_correct": true},
        {"option": "MongoDB", "is_correct": true},
        {"option": "Redis", "is_correct": true},
        {"option": "React", "is_correct": false},
        {"option": "Docker", "is_correct": false}
      ]
    },
    {
      "question_type": "input",
      "question": "Как называется популярная библиотека для создания Telegram ботов на Python? (одно слово)",
      "correct_answer": "aiogram"
    },
    {
      "question_type": "input",
      "question": "Напишите название протокола для безопасной передачи данных в интернете (4 буквы, регистр не важен)",
      "correct_answer": "HTTPS"
    }
  ]
}
"""


async def on_export_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.switch_to(SharedTemplatesSG.export_list)


async def on_import_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.switch_to(SharedTemplatesSG.import_file)


async def on_spec_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.switch_to(SharedTemplatesSG.spec)


async def on_back_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.done()


async def on_back_to_templates(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.switch_to(SharedTemplatesSG.main)


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
    assert _callback.message is not None
    await _callback.answer("⏳ Экспортирую тест...")
    
    test_id = int(item_id)
    test, questions_with_options = await test_repo.get_full_test(test_id)
    
    if not test:
        await _callback.message.answer("❌ Тест не найден")
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
            "question_type": question.question_type.value,
            "question": question.text,
        }
        
        if question.question_type == QuestionType.INPUT:
            correct_options = [o for o in options if o.is_correct]
            if correct_options:
                question_data["correct_answer"] = correct_options[0].text
        else:
            question_data["answers"] = [
                {"option": o.text, "is_correct": o.is_correct}
                for o in options
            ]
        
        questions_list.append(question_data)
    
    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    
    # Build comment header
    created_str = test.created_at.strftime("%d.%m.%Y %H:%M") if test.created_at else "—"
    updated_str = test.updated_at.strftime("%d.%m.%Y %H:%M") if test.updated_at else "—"
    questions_count = len(questions_with_options)
    
    comment_header = f"""// ═══════════════════════════════════════════════════════════════
// ЭКСПОРТ ТЕСТА: {test.title}
// ═══════════════════════════════════════════════════════════════
// 
// ❓ Вопросов: {questions_count}
// 📅 Создан: {created_str}
// 🔄 Обновлён: {updated_str}
// 
// ═══════════════════════════════════════════════════════════════

"""
    
    full_content = comment_header + json_str
    
    safe_title = "".join(c if c.isalnum() or c in "-_" else "_" for c in test.title)[:50]
    filename = f"{safe_title}.json"
    
    await _callback.message.answer_document(
        document=BufferedInputFile(full_content.encode("utf-8"), filename=filename),
        caption=f"📤 <b>Экспорт теста:</b> {test.title}",
    )


async def send_template(callback: CallbackQuery, template_str: str, name: str, title: str) -> None:
    filename = f"template_{name}.json"
    
    assert callback.message is not None
    await callback.message.answer_document(
        document=BufferedInputFile(template_str.encode("utf-8"), filename=filename),
        caption=f"📄 <b>Шаблон:</b> {title}",
    )


async def on_template_ultimate(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await send_template(_callback, TEMPLATE_ULTIMATE, "ultimate", "Ультимативный пример теста")


async def create_test_from_parsed(
    parsed: ParsedTest,
    test_dao: TestDAO,
    question_dao: QuestionDAO,
    option_dao: OptionDAO,
) -> int:
    test = await test_dao.create(
        title=parsed.title,
        description=parsed.description,
        password=parsed.password,
        attempts=parsed.attempts,
        expires_at=parsed.expires_at,
        for_group=parsed.for_group,
        is_active=False,
    )
    
    for position, q in enumerate(parsed.questions):
        question = await question_dao.create(
            test_id=test.id,
            text=q.text,
            position=position,
            question_type=q.question_type,
        )
        
        for opt in q.options:
            await option_dao.create(
                question_id=question.id,
                text=opt.text,
                is_correct=opt.is_correct,
            )
    
    return test.id


@inject
async def on_import_file(
    message: Message,
    _widget: MessageInput,
    manager: DialogManager,
    bot_inst: FromDishka[Bot],
    test_dao: FromDishka[TestDAO],
    question_dao: FromDishka[QuestionDAO],
    option_dao: FromDishka[OptionDAO],
) -> None:
    if not message.document:
        await message.answer("❌ Отправьте JSON файл")
        return
    
    if message.document.file_size and message.document.file_size > 1024 * 1024:
        await message.answer("❌ Файл слишком большой (максимум 1 МБ)")
        return
    
    progress_msg = await message.answer("⏳ Импортирую тест...")
    
    file = await bot_inst.get_file(message.document.file_id)
    if not file.file_path:
        await progress_msg.edit_text("❌ Не удалось загрузить файл")
        return
    
    file_bytes = await bot_inst.download_file(file.file_path)
    if not file_bytes:
        await progress_msg.edit_text("❌ Не удалось загрузить файл")
        return
    
    try:
        json_str = file_bytes.read().decode("utf-8")
    except UnicodeDecodeError:
        await progress_msg.edit_text("❌ Файл должен быть в кодировке UTF-8")
        return
    
    parser = TestParser()
    result = parser.parse(json_str)
    
    if isinstance(result, list):
        if not result:
            await progress_msg.edit_text("❌ Неизвестная ошибка валидации")
            return
        error_lines = ["❌ <b>Ошибки валидации:</b>\n"]
        for err in result[:10]:
            path_str = f" (<code>{err.path}</code>)" if err.path else ""
            error_lines.append(f"• {err.message}{path_str}")
        if len(result) > 10:
            error_lines.append(f"\n... и ещё {len(result) - 10} ошибок")
        await progress_msg.edit_text("\n".join(error_lines))
        return
    
    await create_test_from_parsed(result, test_dao, question_dao, option_dao)
    
    await progress_msg.edit_text(
        f"✅ <b>Тест импортирован!</b>\n\n"
        f"📝 <b>Название:</b> {result.title}\n"
        f"❓ <b>Вопросов:</b> {len(result.questions)}\n\n"
        f"Тест создан в деактивированном состоянии."
    )
    
    await manager.start(SharedTestsSG.tests_list, mode=StartMode.RESET_STACK)


shared_templates_dialog = Dialog(
    Window(
        Const(TEMPLATES_INFO),
        Row(
            Button(Const("📤 Экспорт"), id="export", on_click=on_export_clicked),
            Button(Const("📥 Импорт"), id="import", on_click=on_import_clicked),
        ),
        Button(Const("📋 Спецификация"), id="spec", on_click=on_spec_clicked),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_clicked),
        state=SharedTemplatesSG.main,
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
        state=SharedTemplatesSG.export_list,
        getter=get_tests_for_export,
    ),
    Window(
        Const(SPEC_INFO),
        Button(Const("📦 Ультимативный шаблон"), id="tpl_ultimate", on_click=on_template_ultimate),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_templates),
        state=SharedTemplatesSG.spec,
    ),
    Window(
        Const("<b>📥 Импорт теста</b>\n\nОтправьте JSON файл с тестом.\n\n<i>Формат файла описан в разделе «Спецификация»</i>"),
        MessageInput(on_import_file, content_types=[ContentType.DOCUMENT]),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_templates),
        state=SharedTemplatesSG.import_file,
    ),
)
