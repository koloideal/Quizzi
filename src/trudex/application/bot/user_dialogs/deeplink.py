from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.user_dialogs.states import UserDeeplinkSG, UserMenuSG, UserTestSG
from trudex.infrastructure.database.dao.test import TestDAO
from trudex.infrastructure.database.models import QuestionType
from trudex.infrastructure.database.repo.test import TestRepository
from trudex.infrastructure.database.repo.test_attempt import TestAttemptRepository
from trudex.infrastructure.utils.rate_limiter import PasswordRateLimiter


@inject
async def get_deeplink_test_data(
    dialog_manager: DialogManager,
    test_dao: FromDishka[TestDAO],
    test_repo: FromDishka[TestRepository],
    **_kwargs,
):
    start_data = dialog_manager.start_data or {}
    assert isinstance(start_data, dict)
    test_id = start_data.get("test_id")
    error = start_data.get("error")
    
    if error:
        return {"test_info": error, "can_start": False}
    
    if not test_id:
        return {"test_info": "❌ Тест не найден", "can_start": False}
    
    test = await test_dao.get_by_id(test_id)
    
    if not test:
        return {"test_info": "❌ Тест не найден", "can_start": False}
    
    questions_count = await test_repo.count_questions_in_test(test_id)
    
    password_str = "🔒 Требуется пароль" if test.password else "🔓 Без пароля"
    attempts_str = f"🔄 Попыток: {test.attempts}" if test.attempts else "🔄 Попыток: ♾️"
    
    test_info = (
        f"<b>📝 {test.title}</b>\n\n"
        f"<blockquote>{test.description or '—'}</blockquote>\n\n"
        f"<b>Вопросов:</b> {questions_count}\n"
        f"{password_str}\n"
        f"{attempts_str}"
    )
    
    return {"test_info": test_info, "can_start": True, "has_password": bool(test.password)}


@inject
async def on_start_deeplink_test(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    test_dao: FromDishka[TestDAO],
    test_repo: FromDishka[TestRepository],
    attempt_repo: FromDishka[TestAttemptRepository],
    rate_limiter: FromDishka[PasswordRateLimiter],
):
    assert _callback.from_user is not None
    
    start_data = manager.start_data or {}
    assert isinstance(start_data, dict)
    test_id = start_data.get("test_id")
    user_id = _callback.from_user.id
    
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    test = await test_dao.get_by_id(test_id)
    if not test:
        await _callback.answer("❌ Тест не найден")
        return
    
    if test.attempts:
        attempts = await attempt_repo.get_user_test_attempts(user_id, test_id)
        finished_attempts = [a for a in attempts if a.finished_at]
        if len(finished_attempts) >= test.attempts:
            await _callback.answer("❌ Вы исчерпали все попытки")
            return
    
    active_attempt = await attempt_repo.get_active_attempt(user_id, test_id)
    if active_attempt:
        await attempt_repo.attempt_dao.delete(active_attempt.id)
    
    if test.password:
        allowed, wait_time = await rate_limiter.check(user_id)
        if not allowed:
            minutes = int(wait_time // 60) + 1
            await _callback.answer(f"⏳ Слишком много попыток. Подождите {minutes} мин.", show_alert=True)
            return
        await manager.switch_to(UserDeeplinkSG.password_input)
    else:
        await start_test_without_password(manager, test_repo, attempt_repo, test_id, user_id)


async def start_test_without_password(
    manager: DialogManager,
    test_repo: TestRepository,
    attempt_repo: TestAttemptRepository,
    test_id: int,
    user_id: int,
):
    _, questions = await test_repo.get_test_with_questions(test_id)
    
    if not questions:
        return
    
    attempt = await attempt_repo.attempt_dao.create(user_id=user_id, test_id=test_id)
    
    first_question, _ = await test_repo.get_question_with_options(questions[0].id)
    
    if first_question:
        if first_question.question_type == QuestionType.SINGLE:
            first_state = UserTestSG.question_single
        elif first_question.question_type == QuestionType.MULTIPLE:
            first_state = UserTestSG.question_multiple
        else:
            first_state = UserTestSG.question_input
    else:
        first_state = UserTestSG.question_single
    
    await manager.start(
        first_state,
        mode=StartMode.RESET_STACK,
        data={
            "test_id": test_id,
            "attempt_id": attempt.id,
            "questions": [q.id for q in questions],
            "current_question_index": 0,
            "user_answers": {},
        }
    )


@inject
async def on_deeplink_password_input(
    message: Message,
    _widget: MessageInput,
    manager: DialogManager,
    test_dao: FromDishka[TestDAO],
    test_repo: FromDishka[TestRepository],
    attempt_repo: FromDishka[TestAttemptRepository],
    rate_limiter: FromDishka[PasswordRateLimiter],
):
    assert message.from_user is not None
    
    start_data = manager.start_data or {}
    assert isinstance(start_data, dict)
    test_id = start_data.get("test_id")
    
    if not test_id:
        await message.answer("❌ Тест не найден")
        return
    
    test = await test_dao.get_by_id(test_id)
    
    if not test or not test.password:
        await message.answer("❌ Ошибка проверки пароля")
        return
    
    if message.text and message.text.strip() == test.password:
        await message.answer("✅ Пароль верный")
        await start_test_without_password(
            manager, test_repo, attempt_repo, test_id, message.from_user.id
        )
    else:
        allowed, wait_time = await rate_limiter.check(message.from_user.id)
        if not allowed:
            minutes = int(wait_time // 60) + 1
            await message.answer(f"❌ Неверный пароль\n⏳ Слишком много попыток. Подождите {minutes} мин.")
            await manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)
        else:
            await message.answer("❌ Неверный пароль")


async def on_back_to_menu(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)


deeplink_dialog = Dialog(
    Window(
        Format("{test_info}"),
        Button(
            Const("▶️ Пройти тест"),
            id="start_test",
            on_click=on_start_deeplink_test,
            when="can_start"
        ),
        Button(Const("◀️ В главное меню"), id="back", on_click=on_back_to_menu),
        state=UserDeeplinkSG.test_preview,
        getter=get_deeplink_test_data,
    ),
    Window(
        Const("<b>🔑 Введите пароль для доступа к тесту:</b>"),
        MessageInput(on_deeplink_password_input),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_menu),
        state=UserDeeplinkSG.password_input,
    ),
)
