import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from dishka import AsyncContainer
from sqlalchemy.exc import SQLAlchemyError

from quizzi.infrastructure.database.dao.test import TestDAO
from quizzi.infrastructure.database.dao.user_answer import UserAnswerDAO
from quizzi.infrastructure.database.repo.test import TestRepository
from quizzi.infrastructure.database.repo.test_attempt import TestAttemptRepository
from quizzi.infrastructure.utils.timezone import now_msk_naive

logger = logging.getLogger(__name__)


async def deactivate_expired_tests(container: AsyncContainer) -> None:
    async with container() as request_container:
        test_dao = await request_container.get(TestDAO)
        
        expired_tests = await test_dao.get_expired_active_tests(now_msk_naive())
        
        for test in expired_tests:
            await test_dao.update(test.id, is_active=False)
            logger.info("Деактивирован истёкший тест: id=%d, title=%s", test.id, test.title)


async def finish_expired_test_attempts(container: AsyncContainer, bot: Bot) -> None:
    async with container() as request_container:
        attempt_repo = await request_container.get(TestAttemptRepository)
        test_repo = await request_container.get(TestRepository)
        answer_dao = await request_container.get(UserAnswerDAO)
        
        now = now_msk_naive()
        expired_attempts = await attempt_repo.get_expired_active_attempts(now)
        
        for attempt, _ in expired_attempts:
            try:
                test, questions_with_options = await test_repo.get_full_test(attempt.test_id)
                if not test:
                    continue
                
                question_ids = [q.id for q, _ in questions_with_options]
                
                answered_question_ids = set()
                answers = await attempt_repo.get_answers_for_attempt(attempt.id)
                for answer in answers:
                    answered_question_ids.add(answer.question_id)
                
                for question_id in question_ids:
                    if question_id not in answered_question_ids:
                        await answer_dao.create(
                            attempt_id=attempt.id,
                            question_id=question_id,
                            text_answer=None,
                            is_correct=False,
                        )
                
                correct_count = await attempt_repo.calculate_attempt_score(attempt.id)
                total_questions = len(question_ids)
                score = round((correct_count / total_questions * 100)) if total_questions > 0 else 0
                is_passed = score >= 50
                
                await attempt_repo.finish_attempt(attempt.id, score, is_passed)
                
                status = "пройден ✅" if is_passed else "не пройден ❌"
                
                try:
                    await bot.send_message(
                        attempt.user_id,
                        f"⏰ <b>Время на прохождение теста истекло!</b>\n\n"
                        f"📝 <b>Тест:</b> {test.title}\n"
                        f"📊 <b>Результат:</b> {score}%\n"
                        f"🏆 <b>Статус:</b> {status}\n\n"
                        f"<i>Неотвеченные вопросы засчитаны как неправильные.</i>"
                    )
                except TelegramAPIError as e:
                    logger.warning("Не удалось отправить уведомление пользователю %d: %s", attempt.user_id, e)
                
                logger.info(
                    "Завершена просроченная попытка: attempt_id=%d, user_id=%d, test_id=%d, score=%d%%",
                    attempt.id, attempt.user_id, attempt.test_id, score
                )
                
            except SQLAlchemyError as e:
                logger.error("Ошибка при завершении попытки %d: %s", attempt.id, e)


async def send_time_warning_notifications(container: AsyncContainer, bot: Bot) -> None:
    async with container() as request_container:
        attempt_repo = await request_container.get(TestAttemptRepository)
        test_repo = await request_container.get(TestRepository)
        
        now = now_msk_naive()
        attempts_needing_warning = await attempt_repo.get_attempts_needing_warning(now)
        
        for attempt, time_limit, questions_count in attempts_needing_warning:
            try:
                answers = await attempt_repo.get_answers_for_attempt(attempt.id)
                
                if answers:
                    avg_time_per_question = time_limit / questions_count
                    time_since_start = (now - attempt.started_at).total_seconds()
                    expected_answers = int(time_since_start / avg_time_per_question)
                    
                    if len(answers) >= expected_answers:
                        continue
                
                test, _ = await test_repo.get_full_test(attempt.test_id)
                if not test:
                    continue
                
                elapsed = (now - attempt.started_at).total_seconds()
                remaining_seconds = int(time_limit - elapsed)
                remaining_minutes = remaining_seconds // 60
                remaining_secs = remaining_seconds % 60
                
                if remaining_minutes > 0:
                    time_str = f"{remaining_minutes} мин {remaining_secs} сек"
                else:
                    time_str = f"{remaining_secs} сек"
                
                try:
                    await bot.send_message(
                        attempt.user_id,
                        f"⚠️ <b>Внимание! Время заканчивается!</b>\n\n"
                        f"📝 <b>Тест:</b> {test.title}\n"
                        f"⏱️ <b>Осталось:</b> {time_str}\n\n"
                        f"<i>Поторопитесь с ответами!</i>"
                    )
                except TelegramAPIError as e:
                    logger.warning("Не удалось отправить предупреждение пользователю %d: %s", attempt.user_id, e)
                
                await attempt_repo.mark_warning_sent(attempt.id, now)
                
                logger.info(
                    "Отправлено предупреждение о времени: attempt_id=%d, user_id=%d, remaining=%ds",
                    attempt.id, attempt.user_id, remaining_seconds
                )
                
            except SQLAlchemyError as e:
                logger.error("Ошибка при отправке предупреждения для попытки %d: %s", attempt.id, e)
