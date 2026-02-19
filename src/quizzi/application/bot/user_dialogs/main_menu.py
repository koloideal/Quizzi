import asyncio
import functools
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Row, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from quizzi.application.bot.user_dialogs.states import UserMenuSG
from quizzi.application.bot.user_dialogs.take_test import on_start_test
from quizzi.infrastructure.database.dao.group import GroupDAO
from quizzi.infrastructure.database.dao.user import UserDAO
from quizzi.infrastructure.database.repo.test import TestRepository
from quizzi.infrastructure.database.repo.test_attempt import TestAttemptRepository
from quizzi.infrastructure.utils.config import Config
from quizzi.infrastructure.utils.qr_generator import generate_qr_bytes
from quizzi.infrastructure.utils.test_id_to_hash import encode_id
from quizzi.infrastructure.utils.timezone import now_utc, now_utc_naive, to_msk


def can_edit_field(updated_at: datetime | None) -> bool:
    if updated_at is None:
        return True
    updated_at_msk = to_msk(updated_at)
    assert updated_at_msk is not None
    now_msk = to_msk(now_utc())
    assert now_msk is not None
    return now_msk - updated_at_msk >= timedelta(hours=24)


def get_remaining_time(updated_at: datetime) -> str:
    updated_at_msk = to_msk(updated_at)
    assert updated_at_msk is not None
    now_msk = to_msk(now_utc())
    assert now_msk is not None
    remaining = timedelta(hours=24) - (now_msk - updated_at_msk)
    hours = int(remaining.total_seconds() // 3600)
    minutes = int((remaining.total_seconds() % 3600) // 60)
    return f"{hours}ч {minutes}м"


@inject
async def get_user_data(
    dialog_manager: DialogManager,
    user_dao: FromDishka[UserDAO],
    attempt_repo: FromDishka[TestAttemptRepository],
    **_kwargs,
):
    assert dialog_manager.event.from_user is not None
    user_id = dialog_manager.event.from_user.id
    user = await user_dao.get_by_id(user_id)
    stats = await attempt_repo.get_user_stats(user_id)
    
    if not user:
        return {"user_info": "❌ Пользователь не найден"}
    
    name = user.name or user.first_name
    group_str = f"🎓 Группа {user.group}" if user.group else "👤 Группа не указана"
    
    if stats["total_attempts"] > 0:
        accuracy_str = f"📊 Средняя точность: <b>{stats['avg_score']}%</b>"
        tests_str = f"📝 Пройдено тестов: <b>{stats['total_attempts']}</b>"
    else:
        accuracy_str = "📊 Средняя точность: <b>—</b>"
        tests_str = "📝 Пройдено тестов: <b>0</b>"
    
    user_info = (
        f"<b>👋 Привет, {name}!</b>\n\n"
        f"<blockquote>{group_str}</blockquote>\n\n"
        f"{tests_str}\n"
        f"{accuracy_str}"
    )
    
    return {"user_info": user_info}


@inject
async def on_edit_name_clicked(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    user_dao: FromDishka[UserDAO],
):
    assert _callback.from_user is not None
    user = await user_dao.get_by_id(_callback.from_user.id)
    
    if not user:
        await _callback.answer("❌ Пользователь не найден")
        return
    
    if not can_edit_field(user.name_updated_at):
        assert user.name_updated_at is not None
        remaining = get_remaining_time(user.name_updated_at)
        await _callback.answer(f"⏳ Изменить можно через {remaining}")
        return
    
    await manager.switch_to(UserMenuSG.edit_name)


@inject
async def on_edit_group_clicked(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    user_dao: FromDishka[UserDAO],
):
    assert _callback.from_user is not None
    user = await user_dao.get_by_id(_callback.from_user.id)
    
    if not user:
        await _callback.answer("❌ Пользователь не найден")
        return
    
    if not can_edit_field(user.group_updated_at):
        assert user.group_updated_at is not None
        remaining = get_remaining_time(user.group_updated_at)
        await _callback.answer(f"⏳ Изменить можно через {remaining}")
        return
    
    await manager.switch_to(UserMenuSG.edit_group)


async def on_tests_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(UserMenuSG.available_tests)


async def on_results_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(UserMenuSG.my_results)


async def on_back_to_main(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(UserMenuSG.main)


@inject
async def on_name_input(
    message: Message,
    _widget: MessageInput,
    manager: DialogManager,
    user_dao: FromDishka[UserDAO],
):
    assert message.from_user is not None
    if not message.text or len(message.text.strip()) < 2:
        await message.answer("❌ Имя должно содержать минимум 2 символа")
        return
    
    name = message.text.strip()[:128]
    result = await user_dao.update(
        user_id=message.from_user.id,
        name=name,
        name_updated_at=now_utc_naive(),
    )
    if result:
        await message.answer("✅ Имя обновлено")
    else:
        await message.answer("❌ Не удалось обновить имя")
    await manager.switch_to(UserMenuSG.main)


@inject
async def get_groups_data(group_dao: FromDishka[GroupDAO], **_kwargs):
    groups = await group_dao.get_all()
    return {"groups": [(str(g.number), str(g.number)) for g in groups]}


@inject
async def on_group_selected(
    _callback: CallbackQuery,
    _widget,
    manager: DialogManager,
    item_id: str,
    user_dao: FromDishka[UserDAO],
):
    assert _callback.from_user is not None
    result = await user_dao.update(
        user_id=_callback.from_user.id,
        group=int(item_id),
        group_updated_at=now_utc_naive(),
    )
    if result:
        await _callback.answer("✅ Группа обновлена")
    else:
        await _callback.answer("❌ Не удалось обновить группу")
    await manager.switch_to(UserMenuSG.main)


@inject
async def get_available_tests(
    dialog_manager: DialogManager,
    user_dao: FromDishka[UserDAO],
    test_repo: FromDishka[TestRepository],
    **_kwargs,
):
    assert dialog_manager.event.from_user is not None
    user_id = dialog_manager.event.from_user.id
    user = await user_dao.get_by_id(user_id)
    
    if not user:
        return {"tests": [], "count": 0}
    
    tests = await test_repo.get_available_tests_for_user(user_id, user.group)
    
    return {
        "tests": [(f"📝 {t.title}", t.id) for t in tests],
        "count": len(tests),
    }


async def on_test_selected(_callback: CallbackQuery, _widget: Select, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_test_id"] = int(item_id)
    await manager.switch_to(UserMenuSG.test_detail)


async def on_back_to_tests(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(UserMenuSG.available_tests)


@inject
async def on_share_test(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    config: FromDishka[Config],
    bot_inst: FromDishka[Bot],
):
    test_id = manager.dialog_data.get("selected_test_id")
    
    if not test_id:
        await _callback.answer("Ошибка: тест не найден")
        return
    
    test_hash = encode_id(
        test_id,
        config.security.encode_key,
        config.security.encoded_string_length,
    )
    
    bot_info = await bot_inst.get_me()
    bot_username = bot_info.username or "your_bot"
    share_link = f"https://t.me/{bot_username}?start={test_hash}"
    
    loop = asyncio.get_running_loop()
    qr_bytes = await loop.run_in_executor(
        None,
        functools.partial(generate_qr_bytes, share_link),
    )

    assert _callback.message is not None

    await _callback.message.answer_photo(
        photo=BufferedInputFile(qr_bytes, filename="qr.png"),
        caption=f"<b>🔗 Поделиться тестом</b>\n\n📎 <b>Ссылка на тест:</b>\n<code>{share_link}</code>\n\n💡 Отправьте эту ссылку или QR-код пользователям для прохождения теста",
    )


@inject
async def get_test_detail(
    dialog_manager: DialogManager,
    test_repo: FromDishka[TestRepository],
    attempt_repo: FromDishka[TestAttemptRepository],
    **_kwargs,
):
    assert dialog_manager.event.from_user is not None
    test_id = dialog_manager.dialog_data.get("selected_test_id")
    user_id = dialog_manager.event.from_user.id
    
    if not test_id:
        return {"test_info": "❌ Тест не найден"}
    
    test, questions = await test_repo.get_test_with_questions(test_id)
    
    if not test:
        return {"test_info": "❌ Тест не найден"}
    
    attempts = await attempt_repo.get_user_test_attempts(user_id, test_id)
    finished_attempts = [a for a in attempts if a.finished_at]
    
    password_str = "🔒 Требуется пароль" if test.password else "🔓 Без пароля"
    attempts_str = f"🔄 Попыток: {len(finished_attempts)}/{test.attempts}" if test.attempts else f"🔄 Попыток: {len(finished_attempts)}/♾️"
    time_limit_str = f"⏱️ Время: {test.time_limit // 60} мин" if test.time_limit else "⏱️ Без лимита"
    
    expires_at_msk = to_msk(test.expires_at)
    expires_str = f"📅 До {expires_at_msk.strftime('%d.%m.%Y %H:%M')}" if expires_at_msk else "📅 Без срока"
    group_str = f"🎓 Для группы {test.for_group}" if test.for_group else "👥 Для всех"
    
    test_info = (
        f"<b>📝 {test.title}</b>\n\n"
        f"<blockquote>{test.description or '—'}</blockquote>\n\n"
        f"<b>Вопросов:</b> {len(questions)}\n"
        f"{password_str}\n"
        f"{attempts_str}\n"
        f"{time_limit_str}\n"
        f"{expires_str}\n"
        f"{group_str}"
    )
    
    return {"test_info": test_info}


@inject
async def get_my_results(
    dialog_manager: DialogManager,
    attempt_repo: FromDishka[TestAttemptRepository],
    **_kwargs,
):
    assert dialog_manager.event.from_user is not None
    user_id = dialog_manager.event.from_user.id
    attempts_with_tests = await attempt_repo.get_finished_attempts_with_tests(user_id)
    
    results = []
    for attempt, test_title in attempts_with_tests:
        status = "✅" if attempt.is_passed else "❌"
        finished_at_msk = to_msk(attempt.finished_at)
        date_str = finished_at_msk.strftime("%d.%m.%Y") if finished_at_msk else ""
        results.append((f"{status} {test_title} — {attempt.score}% ({date_str})", attempt.id))
    
    return {
        "results": results,
        "count": len(results),
    }


async def on_result_selected(_callback: CallbackQuery, _widget: Select, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_attempt_id"] = int(item_id)
    await manager.switch_to(UserMenuSG.result_detail)


async def on_back_to_results(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(UserMenuSG.my_results)


@inject
async def get_result_detail(
    dialog_manager: DialogManager,
    attempt_repo: FromDishka[TestAttemptRepository],
    test_repo: FromDishka[TestRepository],
    **_kwargs
):
    attempt_id = dialog_manager.dialog_data.get("selected_attempt_id")
    
    if not attempt_id:
        return {"result_info": "❌ Результат не найден"}
    
    attempt, answers = await attempt_repo.get_attempt_with_answers(attempt_id)
    
    if not attempt:
        return {"result_info": "❌ Результат не найден"}
    
    test, _ = await test_repo.get_test_with_questions(attempt.test_id)
    test_title = test.title if test else "Неизвестный тест"
    are_results_viewable = test.are_results_viewable if test else False
    
    status = "✅ Пройден" if attempt.is_passed else "❌ Не пройден"
    finished_at_msk = to_msk(attempt.finished_at)
    date_str = finished_at_msk.strftime("%d.%m.%Y %H:%M") if finished_at_msk else "—"
    
    correct_count = sum(1 for a in answers if a.is_correct)
    total_count = len(answers)
    
    lines = [
        f"<b>📝 {test_title}</b>\n",
        f"📊 <b>Результат:</b> {attempt.score}%",
        f"✏️ <b>Правильных ответов:</b> {correct_count} из {total_count}",
        f"📅 <b>Дата:</b> {date_str}",
        f"🏆 <b>Статус:</b> {status}",
    ]
    
    if are_results_viewable:
        lines.append("\n<b>📋 Ответы:</b>\n")
        
        for i, answer in enumerate(answers, 1):
            question, options = await test_repo.get_question_with_options(answer.question_id)
            if not question:
                continue
            
            correct_options = [opt for opt in options if opt.is_correct]
            correct_texts = [opt.text for opt in correct_options]
            
            status_icon = "✅" if answer.is_correct else "❌"
            
            user_answer = answer.text_answer or ""
            if "|" in user_answer:
                user_answer = ", ".join(user_answer.split("|"))
            
            lines.append(f"{status_icon} <b>Вопрос {i}</b>")
            lines.append(f"<blockquote>{question.text}</blockquote>")
            lines.append(f"👤 <i>Ваш ответ:</i> {user_answer or '—'}")
            lines.append(f"✓ <i>Правильно:</i> {', '.join(correct_texts)}\n")
    else:
        lines.append("\n<i>🔒 Подробные результаты скрыты</i>")
    
    return {"result_info": "\n".join(lines)}


user_menu_dialog = Dialog(
    Window(
        Format("{user_info}"),
        Column(
            Button(Const("📝 Доступные тесты"), id="tests", on_click=on_tests_clicked),
            Button(Const("📊 Мои результаты"), id="results", on_click=on_results_clicked),
        ),
        Row(
            Button(Const("✏️ Имя"), id="edit_name", on_click=on_edit_name_clicked),
            Button(Const("🎓 Группа"), id="edit_group", on_click=on_edit_group_clicked),
        ),
        state=UserMenuSG.main,
        getter=get_user_data,
    ),
    Window(
        Format("<b>📝 Доступные тесты</b>\n\nВсего: {count}"),
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
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_main),
        state=UserMenuSG.available_tests,
        getter=get_available_tests,
    ),
    Window(
        Format("{test_info}"),
        Column(
            Button(Const("▶️ Пройти тест"), id="start_test", on_click=on_start_test),
            Button(Const("🔗 Поделиться"), id="share", on_click=on_share_test),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_tests),
        ),
        state=UserMenuSG.test_detail,
        getter=get_test_detail,
    ),
    Window(
        Const("<b>✏️ Изменение имени</b>\n\nВведите имя и фамилию:"),
        MessageInput(on_name_input),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_main),
        state=UserMenuSG.edit_name,
    ),
    Window(
        Const("<b>🎓 Изменение группы</b>\n\nВыберите группу:"),
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
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_main),
        state=UserMenuSG.edit_group,
        getter=get_groups_data,
    ),
    Window(
        Format("<b>📊 Мои результаты</b>\n\nВсего: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="result_select",
                item_id_getter=lambda x: x[1],
                items="results",
                on_click=on_result_selected,
            ),
            id="results_scroll",
            width=1,
            height=7,
        ),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_main),
        state=UserMenuSG.my_results,
        getter=get_my_results,
    ),
    Window(
        Format("{result_info}"),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_results),
        state=UserMenuSG.result_detail,
        getter=get_result_detail,
    ),
)
