import asyncio
import functools
import json
from datetime import date, datetime, time

from aiogram import Bot
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Calendar, Column, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from quizzi.application.bot.shared_dialogs.states import SharedCreateTestSG, SharedTestsSG
from quizzi.domain.schemas import QuestionType
from quizzi.infrastructure.database.dao.group import GroupDAO
from quizzi.infrastructure.database.dao.test import TestDAO
from quizzi.infrastructure.database.repo.test import TestRepository
from quizzi.infrastructure.database.repo.test_attempt import TestAttemptRepository
from quizzi.infrastructure.utils.config import Config
from quizzi.infrastructure.utils.qr_generator import generate_qr_bytes
from quizzi.infrastructure.utils.test_id_to_hash import encode_id
from quizzi.infrastructure.utils.timezone import to_msk


@inject
async def get_tests_data(test_dao: FromDishka[TestDAO], **_kwargs):
    tests = await test_dao.get_all()
    
    return {
        "tests": [
            (f"{'🟢' if t.is_active else '🔴'} {t.title}", t.id)
            for t in tests
        ],
        "count": len(tests),
    }


async def on_test_selected(_callback: CallbackQuery, _widget: Select, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_test_id"] = int(item_id)
    await manager.switch_to(SharedTestsSG.test_detail)


@inject
async def get_test_detail(test_dao: FromDishka[TestDAO], test_repo: FromDishka[TestRepository], dialog_manager: DialogManager, **_kwargs):
    test_id = dialog_manager.dialog_data.get("selected_test_id")
    
    if not test_id:
        return {
            "test_info": "Тест не найден",
            "is_active": False,
            "button_text": "◀️ Назад",
            "results_button_text": "👁 Показать результаты",
        }
    
    test = await test_dao.get_by_id(test_id)
    questions_count = await test_repo.count_questions_in_test(test_id)
    
    if not test:
        return {
            "test_info": "Тест не найден",
            "is_active": False,
            "button_text": "◀️ Назад",
            "results_button_text": "👁 Показать результаты",
        }
    
    status = "🟢 Активен" if test.is_active else "🔴 Деактивирован"
    password_str = f"🔒 {test.password}" if test.password else "🔓 Без пароля"
    attempts_str = f"🔄 {test.attempts}" if test.attempts else "♾️ Без ограничений"
    expires_str = f"📅 {to_msk(test.expires_at).strftime('%d.%m.%Y %H:%M')}" if test.expires_at else "📅 Без срока"
    group_str = f"🎓 Группа {test.for_group}" if test.for_group else "👥 Для всех"
    results_str = "👁 Результаты видны" if test.are_results_viewable else "🔒 Результаты скрыты"
    
    test_info = (
        f"<b>📝 Информация о тесте</b>\n\n"
        f"<b>Название:</b>\n<blockquote>{test.title}</blockquote>\n"
        f"<b>Описание:</b>\n<blockquote>{test.description or '—'}</blockquote>\n\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Вопросов:</b> {questions_count}\n"
        f"<b>Пароль:</b> {password_str}\n"
        f"<b>Попытки:</b> {attempts_str}\n"
        f"<b>Срок:</b> {expires_str}\n"
        f"<b>Группа:</b> {group_str}\n"
        f"<b>Видимость:</b> {results_str}\n\n"
        f"<b>Создан:</b> {to_msk(test.created_at).strftime('%d.%m.%Y %H:%M') if test.created_at else '—'}"
    )
    
    button_text = "🔴 Деактивировать" if test.is_active else "🟢 Активировать"
    results_button_text = "🔒 Скрыть результаты" if test.are_results_viewable else "👁 Показать результаты"
    
    return {
        "test_info": test_info,
        "is_active": test.is_active,
        "button_text": button_text,
        "results_button_text": results_button_text,
    }


@inject
async def on_toggle_active(_callback: CallbackQuery, _button: Button, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    test = await test_dao.get_by_id(test_id)
    
    if test:
        await test_dao.update(test_id, is_active=not test.is_active)
        action = "деактивирован" if test.is_active else "активирован"
        await _callback.answer(f"✅ Тест {action}")
        await manager.switch_to(SharedTestsSG.test_detail)


@inject
async def on_toggle_results_viewable(_callback: CallbackQuery, _button: Button, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    test = await test_dao.get_by_id(test_id)
    
    if test:
        await test_dao.update(test_id, are_results_viewable=not test.are_results_viewable)
        action = "скрыты" if test.are_results_viewable else "видны"
        await _callback.answer(f"✅ Результаты теперь {action}")
        await manager.switch_to(SharedTestsSG.test_detail)


async def on_back_to_list(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.tests_list)


async def on_statistics(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.statistics)


@inject
async def get_statistics_data(
    dialog_manager: DialogManager,
    attempt_repo: FromDishka[TestAttemptRepository],
    **_kwargs
):
    test_id = dialog_manager.dialog_data.get("selected_test_id")
    
    if not test_id:
        return {"attempts": [], "count": 0}
    
    attempts_with_users = await attempt_repo.get_test_attempts_with_users(test_id)
    
    results = []
    for attempt, user_name in attempts_with_users:
        status = "✅" if attempt.is_passed else "❌"
        finished_at_msk = to_msk(attempt.finished_at)
        date_str = finished_at_msk.strftime("%d.%m.%Y %H:%M") if finished_at_msk else ""
        results.append((f"{status} {user_name} — {attempt.score}% ({date_str})", attempt.id))
    
    return {
        "attempts": results,
        "count": len(results),
    }


async def on_attempt_selected(_callback: CallbackQuery, _widget: Select, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_attempt_id"] = int(item_id)
    await manager.switch_to(SharedTestsSG.attempt_detail)


async def on_back_to_statistics(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.statistics)


@inject
async def get_attempt_detail(
    dialog_manager: DialogManager,
    attempt_repo: FromDishka[TestAttemptRepository],
    test_repo: FromDishka[TestRepository],
    **_kwargs
):
    attempt_id = dialog_manager.dialog_data.get("selected_attempt_id")
    
    if not attempt_id:
        return {"attempt_info": "❌ Результат не найден"}
    
    attempt, answers = await attempt_repo.get_attempt_with_answers(attempt_id)
    
    if not attempt:
        return {"attempt_info": "❌ Результат не найден"}
    
    status = "✅ Пройден" if attempt.is_passed else "❌ Не пройден"
    finished_at_msk = to_msk(attempt.finished_at)
    date_str = finished_at_msk.strftime("%d.%m.%Y %H:%M") if finished_at_msk else "—"
    
    lines = [
        "<b>📊 Результат прохождения</b>\n",
        f"📈 <b>Результат:</b> {attempt.score}%",
        f"📅 <b>Дата:</b> {date_str}",
        f"🏆 <b>Статус:</b> {status}\n",
        "<b>📋 Ответы:</b>\n",
    ]
    
    question_ids = [answer.question_id for answer in answers]
    questions_map = await test_repo.get_questions_with_options_by_ids(question_ids)
    
    for i, answer in enumerate(answers, 1):
        question_data = questions_map.get(answer.question_id)
        if not question_data:
            continue
        
        question, options = question_data
        correct_options = [opt for opt in options if opt.is_correct]
        correct_texts = [opt.text for opt in correct_options]
        
        status_icon = "✅" if answer.is_correct else "❌"
        
        user_answer = answer.text_answer or ""
        if "|" in user_answer:
            user_answer = ", ".join(user_answer.split("|"))
        
        lines.append(f"{status_icon} <b>Вопрос {i}</b>")
        lines.append(f"<blockquote>{question.text}</blockquote>")
        lines.append(f"👤 <i>Ответ:</i> {user_answer or '—'}")
        lines.append(f"✓ <i>Правильно:</i> {', '.join(correct_texts)}\n")
    
    return {"attempt_info": "\n".join(lines)}


@inject
async def on_export_test(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    test_repo: FromDishka[TestRepository],
) -> None:
    test_id = manager.dialog_data.get("selected_test_id")
    
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    assert _callback.message is not None
    await _callback.answer("⏳ Экспортирую тест...")
    
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


@inject
async def on_share_test(_callback: CallbackQuery, _button: Button, manager: DialogManager, config: FromDishka[Config], bot_inst: FromDishka[Bot]):
    test_id = manager.dialog_data.get("selected_test_id")
    
    if not test_id:
        return {
            "share_link": "Ошибка: тест не найден"
        }
    
    test_hash = encode_id(
        test_id, 
        config.security.encode_key,
        config.security.encoded_string_length
    )
    
    bot_info = await bot_inst.get_me()
    bot_username = bot_info.username or "your_bot"
    share_link = f"https://t.me/{bot_username}?start={test_hash}"
    
    loop = asyncio.get_running_loop()
    qr_bytes = await loop.run_in_executor(
        None,
        functools.partial(generate_qr_bytes, share_link)
    )

    assert _callback.message is not None

    await _callback.message.answer_photo(
        photo=BufferedInputFile(qr_bytes, filename="qr.png"),
        caption=f"<b>🔗 Поделиться тестом</b>\n\n📎 <b>Ссылка на тест:</b>\n<code>{share_link}</code>\n\n💡 Отправьте эту ссылку или QR-код пользователям для прохождения теста"
    )


async def on_edit_menu(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.edit_menu)


async def on_back_to_detail(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.test_detail)


async def on_back_to_edit_menu(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.edit_menu)


async def on_edit_password(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.edit_password)


async def on_edit_attempts(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.edit_attempts)


async def on_edit_group(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.edit_group)


async def on_edit_expires(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedTestsSG.edit_expires)


@inject
async def on_password_input(message: Message, _widget: MessageInput, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await message.answer("❌ Тест не найден")
        return
    
    if not message.text:
        await message.answer("❌ Пароль не может быть пустым")
        return
    
    password = message.text.strip()
    if len(password) > 255:
        await message.answer("❌ Пароль слишком длинный (максимум 255 символов)")
        return
    
    await test_dao.update(test_id, password=password)
    await message.answer("✅ Пароль обновлен")
    await manager.switch_to(SharedTestsSG.test_detail)


@inject
async def on_remove_password(_callback: CallbackQuery, _button: Button, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    await test_dao.update(test_id, password=None)
    await _callback.answer("✅ Пароль удален")
    await manager.switch_to(SharedTestsSG.test_detail)


@inject
async def on_attempts_input_edit(message: Message, _widget: MessageInput, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await message.answer("❌ Тест не найден")
        return
    
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
    
    await test_dao.update(test_id, attempts=attempts)
    await message.answer("✅ Количество попыток обновлено")
    await manager.switch_to(SharedTestsSG.test_detail)


@inject
async def on_remove_attempts(_callback: CallbackQuery, _button: Button, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    await test_dao.update(test_id, attempts=None)
    await _callback.answer("✅ Ограничение попыток удалено")
    await manager.switch_to(SharedTestsSG.test_detail)


@inject
async def get_groups_for_edit(dialog_manager: DialogManager, group_dao: FromDishka[GroupDAO], **_kwargs):
    groups = await group_dao.get_all()
    
    return {
        "groups": [(str(g.number), str(g.number)) for g in groups],
    }


@inject
async def on_group_selected_for_test(_callback: CallbackQuery, _widget, manager: DialogManager, item_id: str, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    await test_dao.update(test_id, for_group=int(item_id))
    await _callback.answer("✅ Группа обновлена")
    await manager.switch_to(SharedTestsSG.test_detail)


@inject
async def on_remove_group(_callback: CallbackQuery, _button: Button, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    await test_dao.update(test_id, for_group=None)
    await _callback.answer("✅ Тест теперь доступен для всех групп")
    await manager.switch_to(SharedTestsSG.test_detail)


@inject
async def on_date_selected_for_test(_callback, _widget, manager: DialogManager, selected_date: date, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    expires_at = datetime.combine(selected_date, time.min)
    await test_dao.update(test_id, expires_at=expires_at)
    await _callback.answer("✅ Срок действия обновлен")
    await manager.switch_to(SharedTestsSG.test_detail)


@inject
async def on_remove_expires(_callback: CallbackQuery, _button: Button, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    await test_dao.update(test_id, expires_at=None)
    await _callback.answer("✅ Срок действия удален")
    await manager.switch_to(SharedTestsSG.test_detail)


async def on_add_test_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(SharedCreateTestSG.input_title, mode=StartMode.RESET_STACK)


async def on_back_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.done()


shared_tests_dialog = Dialog(
    Window(
        Format("<b>📝 Тесты</b>\n\nВсего: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="test_select",
                item_id_getter=lambda x: x[1],
                items="tests",
                on_click=on_test_selected,
            ),
            id="tests_scroll",
            width=1,
            height=7,
        ),
        Column(
            Button(Const("➕ Добавить тест"), id="add_test", on_click=on_add_test_clicked),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_clicked),
        ),
        state=SharedTestsSG.tests_list,
        getter=get_tests_data,
    ),
    Window(
        Format("{test_info}"),
        Column(
            Button(
                Format("{button_text}"),
                id="toggle_active",
                on_click=on_toggle_active
            ),
            Button(
                Format("{results_button_text}"),
                id="toggle_results",
                on_click=on_toggle_results_viewable
            ),
            Button(Const("📊 Статистика"), id="statistics", on_click=on_statistics),
            Button(Const("🔗 Поделиться"), id="share", on_click=on_share_test),
            Button(Const("📤 Экспорт"), id="export", on_click=on_export_test),
            Button(Const("✏️ Изменить"), id="edit_menu", on_click=on_edit_menu),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_list),
        ),
        state=SharedTestsSG.test_detail,
        getter=get_test_detail,
    ),
    Window(
        Const("<b>✏️ Изменить тест</b>\n\nВыберите, что хотите изменить:"),
        Column(
            Button(Const("🔑 Пароль"), id="edit_password", on_click=on_edit_password),
            Button(Const("🔄 Попытки"), id="edit_attempts", on_click=on_edit_attempts),
            Button(Const("👥 Группа"), id="edit_group", on_click=on_edit_group),
            Button(Const("📅 Срок действия"), id="edit_expires", on_click=on_edit_expires),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_detail),
        ),
        state=SharedTestsSG.edit_menu,
    ),
    Window(
        Const("<b>🔑 Изменение пароля</b>\n\n💬 <b>Введите новый пароль</b> или удалите текущий:\n<i>(максимум 255 символов)</i>"),
        MessageInput(on_password_input),
        Column(
            Button(Const("🗑 Удалить пароль"), id="remove_password", on_click=on_remove_password),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_edit_menu),
        ),
        state=SharedTestsSG.edit_password,
    ),
    Window(
        Const("<b>🔄 Изменение количества попыток</b>\n\n🔢 <b>Введите новое количество попыток</b> (1-100) или удалите ограничение:"),
        MessageInput(on_attempts_input_edit),
        Column(
            Button(Const("🗑 Без ограничений"), id="remove_attempts", on_click=on_remove_attempts),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_edit_menu),
        ),
        state=SharedTestsSG.edit_attempts,
    ),
    Window(
        Const("<b>👥 Изменение группы</b>\n\n🎓 <b>Выберите группу</b> или удалите привязку:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="groups",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_selected_for_test,
            ),
            id="groups_scroll",
            width=2,
            height=7,
        ),
        Column(
            Button(Const("🗑 Для всех групп"), id="remove_group", on_click=on_remove_group),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_edit_menu),
        ),
        state=SharedTestsSG.edit_group,
        getter=get_groups_for_edit,
    ),
    Window(
        Const("<b>📅 Изменение срока действия</b>\n\n🗓 <b>Выберите новую дату</b> или удалите срок:"),
        Calendar(id="calendar", on_click=on_date_selected_for_test),
        Column(
            Button(Const("🗑 Удалить срок"), id="remove_expires", on_click=on_remove_expires),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_edit_menu),
        ),
        state=SharedTestsSG.edit_expires,
    ),
    Window(
        Format("<b>📊 Статистика теста</b>\n\nПрошли тест: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="attempt_select",
                item_id_getter=lambda x: x[1],
                items="attempts",
                on_click=on_attempt_selected,
            ),
            id="attempts_scroll",
            width=1,
            height=7,
        ),
        Column(
            Button(Const("🔄 Обновить"), id="refresh", on_click=on_statistics),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_detail),
        ),
        state=SharedTestsSG.statistics,
        getter=get_statistics_data,
    ),
    Window(
        Format("{attempt_info}"),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_statistics),
        state=SharedTestsSG.attempt_detail,
        getter=get_attempt_detail,
    ),
)
