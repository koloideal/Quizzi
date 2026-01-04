from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Multiselect, Radio
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.user_dialogs.states import UserMenuSG, UserTestSG
from trudex.domain.schemas import QuestionType
from trudex.infrastructure.database.dao.test import TestDAO
from trudex.infrastructure.database.dao.user_answer import UserAnswerDAO
from trudex.infrastructure.database.repo.test import TestRepository
from trudex.infrastructure.database.repo.test_attempt import TestAttemptRepository
from trudex.infrastructure.utils.rate_limiter import PasswordRateLimiter
from trudex.infrastructure.utils.timezone import now_msk_naive


async def get_state_for_question_type(question_type: str):
    if question_type == QuestionType.SINGLE:
        return UserTestSG.question_single
    elif question_type == QuestionType.MULTIPLE:
        return UserTestSG.question_multiple
    else:
        return UserTestSG.question_input


@inject
async def on_start_test(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    test_dao: FromDishka[TestDAO],
    test_repo: FromDishka[TestRepository],
    attempt_repo: FromDishka[TestAttemptRepository],
    rate_limiter: FromDishka[PasswordRateLimiter],
):
    assert _callback.from_user is not None
    test_id = manager.dialog_data.get("selected_test_id")
    user_id = _callback.from_user.id
    
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    test = await test_dao.get_by_id(test_id)
    if not test:
        await _callback.answer("❌ Тест не найден")
        return
    
    if not test.is_active:
        await _callback.answer("❌ Тест деактивирован")
        return
    
    if test.expires_at and test.expires_at < now_msk_naive():
        await _callback.answer("❌ Срок действия теста истек")
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
        # Проверяем rate limit перед показом экрана ввода пароля
        allowed, wait_time = await rate_limiter.check(user_id)
        if not allowed:
            minutes = int(wait_time // 60) + 1
            await _callback.answer(f"⏳ Слишком много попыток. Подождите {minutes} мин.", show_alert=True)
            return
        await manager.start(UserTestSG.password_input, mode=StartMode.NORMAL, data={"test_id": test_id})
    else:
        _, questions = await test_repo.get_test_with_questions(test_id)
        
        if not questions:
            await _callback.answer("❌ В тесте нет вопросов")
            return
        
        attempt = await attempt_repo.attempt_dao.create(user_id=user_id, test_id=test_id)
        
        first_question, _ = await test_repo.get_question_with_options(questions[0].id)
        first_state = await get_state_for_question_type(first_question.question_type if first_question else QuestionType.SINGLE)
        
        await manager.start(
            first_state,
            mode=StartMode.NORMAL,
            data={
                "test_id": test_id,
                "attempt_id": attempt.id,
                "questions": [q.id for q in questions],
                "current_question_index": 0,
                "user_answers": {},
            }
        )


@inject
async def on_password_input(
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
        await message.answer("✅ Пароль верный, начинаем тест")
        
        _, questions = await test_repo.get_test_with_questions(test_id)
        
        if not questions:
            await message.answer("❌ В тесте нет вопросов")
            return
        
        attempt = await attempt_repo.attempt_dao.create(user_id=message.from_user.id, test_id=test_id)
        
        first_question, _ = await test_repo.get_question_with_options(questions[0].id)
        first_state = await get_state_for_question_type(first_question.question_type if first_question else QuestionType.SINGLE)
        
        manager.dialog_data["attempt_id"] = attempt.id
        manager.dialog_data["questions"] = [q.id for q in questions]
        manager.dialog_data["current_question_index"] = 0
        manager.dialog_data["user_answers"] = {}
        
        await manager.switch_to(first_state)
    else:
        # Проверяем rate limit при неверном пароле
        allowed, wait_time = await rate_limiter.check(message.from_user.id)
        if not allowed:
            minutes = int(wait_time // 60) + 1
            await message.answer(f"❌ Неверный пароль\n⏳ Слишком много попыток. Подождите {minutes} мин.")
            await manager.done()
        else:
            await message.answer("❌ Неверный пароль")


@inject
async def on_cancel_test(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    attempt_repo: FromDishka[TestAttemptRepository],
):
    start_data = manager.start_data or {}
    assert isinstance(start_data, dict)
    attempt_id = manager.dialog_data.get("attempt_id") or start_data.get("attempt_id")
    
    if attempt_id:
        await attempt_repo.attempt_dao.delete(attempt_id)
    
    await _callback.answer("Тест отменен")
    await manager.start(UserMenuSG.available_tests, mode=StartMode.RESET_STACK)


@inject
async def get_question_data(
    dialog_manager: DialogManager,
    test_repo: FromDishka[TestRepository],
    **_kwargs,
):
    start_data = dialog_manager.start_data or {}
    assert isinstance(start_data, dict)
    
    current_index = dialog_manager.dialog_data.get("current_question_index")
    if current_index is None:
        current_index = start_data.get("current_question_index", 0)
    
    questions = dialog_manager.dialog_data.get("questions") or start_data.get("questions", [])
    
    if not questions or current_index >= len(questions):
        return {"question_text": "Ошибка", "options": []}
    
    question_id = questions[current_index]
    question, options = await test_repo.get_question_with_options(question_id)
    
    if not question:
        return {"question_text": "Ошибка", "options": []}
    
    progress = f"{current_index + 1}/{len(questions)}"
    
    return {
        "question_text": f"<b>📝 Вопрос {progress}</b>\n\n<blockquote>{question.text}</blockquote>",
        "options": [(opt.text, str(opt.id)) for opt in options],
    }


async def on_single_answer_selected(_callback: CallbackQuery, _widget, manager: DialogManager, item_id: str):
    start_data = manager.start_data or {}
    assert isinstance(start_data, dict)
    current_index = manager.dialog_data.get("current_question_index")
    if current_index is None:
        current_index = start_data.get("current_question_index", 0)
    questions = manager.dialog_data.get("questions") or start_data.get("questions", [])
    
    if not questions or current_index >= len(questions):
        return
    
    question_id = questions[current_index]
    user_answers = manager.dialog_data.get("user_answers", {})
    user_answers[str(question_id)] = {"type": "single", "answer": int(item_id)}
    manager.dialog_data["user_answers"] = user_answers


async def on_multiple_answer_changed(_event, widget, manager: DialogManager, _data: str):
    start_data = manager.start_data or {}
    assert isinstance(start_data, dict)
    current_index = manager.dialog_data.get("current_question_index")
    if current_index is None:
        current_index = start_data.get("current_question_index", 0)
    questions = manager.dialog_data.get("questions") or start_data.get("questions", [])
    
    if not questions or current_index >= len(questions):
        return
    
    question_id = questions[current_index]
    selected = widget.get_checked()
    
    user_answers = manager.dialog_data.get("user_answers", {})
    user_answers[str(question_id)] = {"type": "multiple", "answer": [int(x) for x in selected]}
    manager.dialog_data["user_answers"] = user_answers


@inject
async def on_text_answer_input(
    message: Message,
    _widget: MessageInput,
    manager: DialogManager,
    test_repo: FromDishka[TestRepository],
    attempt_repo: FromDishka[TestAttemptRepository],
    answer_dao: FromDishka[UserAnswerDAO],
    test_dao: FromDishka[TestDAO],
):
    start_data = manager.start_data or {}
    assert isinstance(start_data, dict)
    current_index = manager.dialog_data.get("current_question_index")
    if current_index is None:
        current_index = start_data.get("current_question_index", 0)
    questions = manager.dialog_data.get("questions") or start_data.get("questions", [])
    
    if not questions or current_index >= len(questions):
        return
    
    question_id = questions[current_index]
    text_answer = message.text.strip() if message.text else ""
    attempt_id = manager.dialog_data.get("attempt_id") or start_data.get("attempt_id")
    test_id = manager.dialog_data.get("test_id") or start_data.get("test_id")
    
    if not attempt_id:
        await message.answer("❌ Ошибка попытки")
        return
    
    question, options = await test_repo.get_question_with_options(question_id)
    if not question:
        await message.answer("❌ Вопрос не найден")
        return
    
    correct_options = [opt for opt in options if opt.is_correct]
    user_normalized = text_answer.lower().replace(" ", "")
    is_correct = any(opt.text.lower().replace(" ", "") == user_normalized for opt in correct_options)
    
    await answer_dao.create(
        attempt_id=attempt_id,
        question_id=question_id,
        text_answer=text_answer,
        is_correct=is_correct,
    )
    
    if current_index + 1 >= len(questions):
        test = await test_dao.get_by_id(test_id) if test_id else None
        are_results_viewable = test.are_results_viewable if test else False
        await finish_test(manager, attempt_repo, attempt_id, len(questions), are_results_viewable)
    else:
        next_index = current_index + 1
        manager.dialog_data["current_question_index"] = next_index
        
        next_question_id = questions[next_index]
        next_question, _ = await test_repo.get_question_with_options(next_question_id)
        next_state = await get_state_for_question_type(next_question.question_type if next_question else QuestionType.SINGLE)
        
        await manager.switch_to(next_state)


@inject
async def on_next_question(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    test_repo: FromDishka[TestRepository],
    attempt_repo: FromDishka[TestAttemptRepository],
    answer_dao: FromDishka[UserAnswerDAO],
    test_dao: FromDishka[TestDAO],
):
    start_data = manager.start_data or {}
    assert isinstance(start_data, dict)
    current_index = manager.dialog_data.get("current_question_index")
    if current_index is None:
        current_index = start_data.get("current_question_index", 0)
    questions = manager.dialog_data.get("questions") or start_data.get("questions", [])
    
    if not questions or current_index >= len(questions):
        await _callback.answer("❌ Ошибка")
        return
    
    question_id = questions[current_index]
    user_answers = manager.dialog_data.get("user_answers", {})
    
    if str(question_id) not in user_answers:
        await _callback.answer("❌ Выберите ответ")
        return
    
    answer_data = user_answers[str(question_id)]
    attempt_id = manager.dialog_data.get("attempt_id") or start_data.get("attempt_id")
    test_id = manager.dialog_data.get("test_id") or start_data.get("test_id")
    
    if not attempt_id:
        await _callback.answer("❌ Ошибка попытки")
        return
    
    question, options = await test_repo.get_question_with_options(question_id)
    
    if not question:
        await _callback.answer("❌ Вопрос не найден")
        return
    
    if answer_data["type"] == "single":
        selected_option_id = answer_data["answer"]
        correct_options = [opt for opt in options if opt.is_correct]
        is_correct = any(opt.id == selected_option_id for opt in correct_options)
        
        selected_text = next((opt.text for opt in options if opt.id == selected_option_id), "")
        
        await answer_dao.create(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            text_answer=selected_text,
            is_correct=is_correct,
        )
    
    elif answer_data["type"] == "multiple":
        selected_option_ids = set(answer_data["answer"])
        
        selected_texts = sorted([opt.text for opt in options if opt.id in selected_option_ids])
        correct_texts = sorted([opt.text for opt in options if opt.is_correct])
        is_correct = selected_texts == correct_texts
        
        await answer_dao.create(
            attempt_id=attempt_id,
            question_id=question_id,
            text_answer="|".join(selected_texts),
            is_correct=is_correct,
        )
    
    if current_index + 1 >= len(questions):
        test = await test_dao.get_by_id(test_id) if test_id else None
        are_results_viewable = test.are_results_viewable if test else False
        await finish_test(manager, attempt_repo, attempt_id, len(questions), are_results_viewable)
    else:
        next_index = current_index + 1
        manager.dialog_data["current_question_index"] = next_index
        
        next_question_id = questions[next_index]
        next_question, _ = await test_repo.get_question_with_options(next_question_id)
        next_state = await get_state_for_question_type(next_question.question_type if next_question else QuestionType.SINGLE)
        
        await manager.switch_to(next_state)


async def finish_test(
    manager: DialogManager,
    attempt_repo: TestAttemptRepository,
    attempt_id: int,
    total_questions: int,
    are_results_viewable: bool = False,
):
    correct_count = await attempt_repo.calculate_attempt_score(attempt_id)
    
    score = round((correct_count / total_questions * 100)) if total_questions > 0 else 0
    is_passed = score >= 50
    
    await attempt_repo.finish_attempt(attempt_id, score, is_passed)
    
    manager.dialog_data["score"] = score
    manager.dialog_data["correct_count"] = correct_count
    manager.dialog_data["total_questions"] = total_questions
    manager.dialog_data["is_passed"] = is_passed
    manager.dialog_data["are_results_viewable"] = are_results_viewable
    
    await manager.switch_to(UserTestSG.results)


async def get_results_data(dialog_manager: DialogManager, **_kwargs):
    score = dialog_manager.dialog_data.get("score", 0)
    correct_count = dialog_manager.dialog_data.get("correct_count", 0)
    total_questions = dialog_manager.dialog_data.get("total_questions", 0)
    is_passed = dialog_manager.dialog_data.get("is_passed", False)
    are_results_viewable = dialog_manager.dialog_data.get("are_results_viewable", False)
    
    if is_passed:
        status = "✅ <b>Тест пройден!</b>"
    else:
        status = "❌ <b>Тест не пройден</b>"
    
    results_text = (
        f"{status}\n\n"
        f"📊 <b>Результат:</b> {score}%\n"
        f"✏️ <b>Правильных ответов:</b> {correct_count} из {total_questions}"
    )
    
    return {"results_text": results_text, "are_results_viewable": are_results_viewable}


async def on_back_to_menu(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)


async def on_show_detailed_results(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(UserTestSG.detailed_results)


async def on_back_to_results(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(UserTestSG.results)


@inject
async def get_detailed_results_data(
    dialog_manager: DialogManager,
    attempt_repo: FromDishka[TestAttemptRepository],
    test_repo: FromDishka[TestRepository],
    **_kwargs,
):
    start_data = dialog_manager.start_data or {}
    assert isinstance(start_data, dict)
    attempt_id = dialog_manager.dialog_data.get("attempt_id") or start_data.get("attempt_id")
    
    if not attempt_id:
        return {"detailed_text": "Ошибка загрузки результатов"}
    
    answers = await attempt_repo.get_answers_for_attempt(attempt_id)
    
    lines = ["<b>📋 Подробные результаты</b>\n"]
    
    for i, answer in enumerate(answers, 1):
        question, options = await test_repo.get_question_with_options(answer.question_id)
        if not question:
            continue
        
        correct_options = [opt for opt in options if opt.is_correct]
        correct_texts = [opt.text for opt in correct_options]
        
        status = "✅" if answer.is_correct else "❌"
        
        user_answer = answer.text_answer or ""
        if "|" in user_answer:
            user_answer = ", ".join(user_answer.split("|"))
        
        lines.append(f"{status} <b>Вопрос {i}</b>")
        lines.append(f"<blockquote>{question.text}</blockquote>")
        lines.append(f"👤 <i>Ваш ответ:</i> {user_answer or '—'}")
        lines.append(f"✓ <i>Правильно:</i> {', '.join(correct_texts)}\n")
    
    return {"detailed_text": "\n".join(lines)}


take_test_dialog = Dialog(
    Window(
        Const("<b>🔑 Введите пароль для доступа к тесту:</b>"),
        MessageInput(on_password_input),
        Button(Const("❌ Отмена"), id="cancel", on_click=on_cancel_test),
        state=UserTestSG.password_input,
    ),
    Window(
        Format("{question_text}\n\n<i>Выберите один вариант ответа:</i>"),
        Column(
            Radio(
                Format("🔘 {item[0]}"),
                Format("⚪ {item[0]}"),
                id="single_answer",
                item_id_getter=lambda x: x[1],
                items="options",
                on_click=on_single_answer_selected,
            ),
        ),
        Button(Const("➡️ Далее"), id="next", on_click=on_next_question),
        state=UserTestSG.question_single,
        getter=get_question_data,
    ),
    Window(
        Format("{question_text}\n\n<i>Выберите несколько вариантов ответа:</i>"),
        Column(
            Multiselect(
                Format("✅ {item[0]}"),
                Format("⬜ {item[0]}"),
                id="multiple_answer",
                item_id_getter=lambda x: x[1],
                items="options",
                on_state_changed=on_multiple_answer_changed,
            ),
        ),
        Button(Const("➡️ Далее"), id="next", on_click=on_next_question),
        state=UserTestSG.question_multiple,
        getter=get_question_data,
    ),
    Window(
        Format("{question_text}\n\n<i>Введите ответ:</i>"),
        MessageInput(on_text_answer_input),
        state=UserTestSG.question_input,
        getter=get_question_data,
    ),
    Window(
        Format("{results_text}"),
        Column(
            Button(
                Const("📋 Подробные результаты"),
                id="detailed",
                on_click=on_show_detailed_results,
                when="are_results_viewable",
            ),
            Button(Const("◀️ В главное меню"), id="back", on_click=on_back_to_menu),
        ),
        state=UserTestSG.results,
        getter=get_results_data,
    ),
    Window(
        Format("{detailed_text}"),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_results),
        state=UserTestSG.detailed_results,
        getter=get_detailed_results_data,
    ),
)
