from dataclasses import dataclass
from datetime import datetime

from quizzi.domain.schemas import QuestionType
from quizzi.infrastructure.database.dao.test import TestDAO
from quizzi.infrastructure.database.dao.user_answer import UserAnswerDAO
from quizzi.infrastructure.database.repo.test import TestRepository
from quizzi.infrastructure.database.repo.test_attempt import TestAttemptRepository
from quizzi.infrastructure.utils.timezone import now_utc_naive


@dataclass
class AttemptStartResult:
    success: bool
    attempt_id: int | None = None
    questions: list[int] | None = None
    started_at: datetime | None = None
    error: str = ""


@dataclass
class AnswerResult:
    success: bool
    is_correct: bool = False
    error: str = ""


@dataclass
class TestResult:
    score: int
    correct_count: int
    total_questions: int
    is_passed: bool


class TestAttemptService:
    def __init__(
        self,
        test_dao: TestDAO,
        test_repo: TestRepository,
        attempt_repo: TestAttemptRepository,
        answer_dao: UserAnswerDAO,
    ) -> None:
        self._test_dao = test_dao
        self._test_repo = test_repo
        self._attempt_repo = attempt_repo
        self._answer_dao = answer_dao
    
    async def start_attempt(self, user_id: int, test_id: int) -> AttemptStartResult:
        active_attempt = await self._attempt_repo.get_active_attempt(user_id, test_id)
        if active_attempt:
            await self._attempt_repo.attempt_dao.delete(active_attempt.id)
        
        _, questions = await self._test_repo.get_test_with_questions(test_id)
        if not questions:
            return AttemptStartResult(success=False, error="❌ В тесте нет вопросов")
        
        attempt = await self._attempt_repo.attempt_dao.create(user_id=user_id, test_id=test_id)
        started_at = now_utc_naive()
        
        return AttemptStartResult(
            success=True,
            attempt_id=attempt.id,
            questions=[q.id for q in questions],
            started_at=started_at,
        )
    
    async def cancel_attempt(self, attempt_id: int) -> bool:
        return await self._attempt_repo.attempt_dao.delete(attempt_id)
    
    async def save_single_answer(
        self,
        attempt_id: int,
        question_id: int,
        selected_option_id: int,
    ) -> AnswerResult:
        question, options = await self._test_repo.get_question_with_options(question_id)
        if not question:
            return AnswerResult(success=False, error="❌ Вопрос не найден")
        
        correct_options = [opt for opt in options if opt.is_correct]
        is_correct = any(opt.id == selected_option_id for opt in correct_options)
        selected_text = next((opt.text for opt in options if opt.id == selected_option_id), "")
        
        await self._answer_dao.create(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            text_answer=selected_text,
            is_correct=is_correct,
        )
        
        return AnswerResult(success=True, is_correct=is_correct)
    
    async def save_multiple_answer(
        self,
        attempt_id: int,
        question_id: int,
        selected_option_ids: list[int],
    ) -> AnswerResult:
        question, options = await self._test_repo.get_question_with_options(question_id)
        if not question:
            return AnswerResult(success=False, error="❌ Вопрос не найден")
        
        selected_texts = sorted([opt.text for opt in options if opt.id in selected_option_ids])
        correct_texts = sorted([opt.text for opt in options if opt.is_correct])
        is_correct = selected_texts == correct_texts
        
        await self._answer_dao.create(
            attempt_id=attempt_id,
            question_id=question_id,
            text_answer="|".join(selected_texts),
            is_correct=is_correct,
        )
        
        return AnswerResult(success=True, is_correct=is_correct)
    
    async def save_text_answer(
        self,
        attempt_id: int,
        question_id: int,
        text_answer: str,
    ) -> AnswerResult:
        question, options = await self._test_repo.get_question_with_options(question_id)
        if not question:
            return AnswerResult(success=False, error="❌ Вопрос не найден")
        
        correct_options = [opt for opt in options if opt.is_correct]
        user_normalized = text_answer.lower().replace(" ", "")
        is_correct = any(opt.text.lower().replace(" ", "") == user_normalized for opt in correct_options)
        
        await self._answer_dao.create(
            attempt_id=attempt_id,
            question_id=question_id,
            text_answer=text_answer,
            is_correct=is_correct,
        )
        
        return AnswerResult(success=True, is_correct=is_correct)
    
    async def finish_attempt(self, attempt_id: int, total_questions: int) -> TestResult:
        correct_count = await self._attempt_repo.calculate_attempt_score(attempt_id)
        score = round((correct_count / total_questions * 100)) if total_questions > 0 else 0
        is_passed = score >= 50
        
        await self._attempt_repo.finish_attempt(attempt_id, score, is_passed)
        
        return TestResult(
            score=score,
            correct_count=correct_count,
            total_questions=total_questions,
            is_passed=is_passed,
        )
    
    async def finish_by_timeout(
        self,
        attempt_id: int,
        questions: list[int],
        user_answers: dict,
    ) -> TestResult:
        answered_question_ids = set()
        answers = await self._attempt_repo.get_answers_for_attempt(attempt_id)
        for answer in answers:
            answered_question_ids.add(answer.question_id)
        
        for question_id in questions:
            if question_id in answered_question_ids:
                continue
            
            answer_data = user_answers.get(str(question_id))
            
            if answer_data:
                question, options = await self._test_repo.get_question_with_options(question_id)
                if not question:
                    continue
                
                if answer_data["type"] == "single":
                    await self.save_single_answer(attempt_id, question_id, answer_data["answer"])
                elif answer_data["type"] == "multiple":
                    await self.save_multiple_answer(attempt_id, question_id, answer_data["answer"])
            else:
                await self._answer_dao.create(
                    attempt_id=attempt_id,
                    question_id=question_id,
                    text_answer=None,
                    is_correct=False,
                )
        
        return await self.finish_attempt(attempt_id, len(questions))
    
    async def get_question_state(self, question_type: str):
        from quizzi.application.bot.user_dialogs.states import UserTestSG
        
        if question_type == QuestionType.SINGLE:
            return UserTestSG.question_single
        elif question_type == QuestionType.MULTIPLE:
            return UserTestSG.question_multiple
        else:
            return UserTestSG.question_input
    
    async def get_next_question_state(self, question_id: int):
        question, _ = await self._test_repo.get_question_with_options(question_id)
        question_type = question.question_type if question else QuestionType.SINGLE
        return await self.get_question_state(question_type)
