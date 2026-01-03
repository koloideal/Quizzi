from datetime import datetime
from typing import final

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from trudex.domain.schemas import TestAttempt, UserAnswer
from trudex.infrastructure.database.dao.test_attempt import TestAttemptDAO
from trudex.infrastructure.database.dao.user_answer import UserAnswerDAO
from trudex.infrastructure.database.dto.test_attempt import TestAttemptDTO
from trudex.infrastructure.database.dto.user_answer import UserAnswerDTO
from trudex.infrastructure.database.models import \
    TestAttempt as TestAttemptModel
from trudex.infrastructure.database.models import UserAnswer as UserAnswerModel


@final
class TestAttemptRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.attempt_dao = TestAttemptDAO(session)
        self.answer_dao = UserAnswerDAO(session)
    
    async def get_user_attempts(self, user_id: int) -> list[TestAttempt]:
        result = await self.session.execute(
            select(TestAttemptModel)
            .where(TestAttemptModel.user_id == user_id)
            .order_by(TestAttemptModel.started_at.desc())
        )
        models = list(result.scalars().all())
        return [TestAttemptDTO(model).to_domain() for model in models]
    
    async def get_test_attempts(self, test_id: int) -> list[TestAttempt]:
        result = await self.session.execute(
            select(TestAttemptModel)
            .where(TestAttemptModel.test_id == test_id)
            .order_by(TestAttemptModel.started_at.desc())
        )
        models = list(result.scalars().all())
        return [TestAttemptDTO(model).to_domain() for model in models]
    
    async def get_user_test_attempts(self, user_id: int, test_id: int) -> list[TestAttempt]:
        result = await self.session.execute(
            select(TestAttemptModel)
            .where(TestAttemptModel.user_id == user_id)
            .where(TestAttemptModel.test_id == test_id)
            .order_by(TestAttemptModel.started_at.desc())
        )
        models = list(result.scalars().all())
        return [TestAttemptDTO(model).to_domain() for model in models]
    
    async def get_active_attempt(self, user_id: int, test_id: int) -> TestAttempt | None:
        result = await self.session.execute(
            select(TestAttemptModel)
            .where(TestAttemptModel.user_id == user_id)
            .where(TestAttemptModel.test_id == test_id)
            .where(TestAttemptModel.finished_at == None)
            .order_by(TestAttemptModel.started_at.desc())
        )
        model = result.scalar_one_or_none()
        return TestAttemptDTO(model).to_domain() if model else None
    
    async def get_attempt_with_answers(self, attempt_id: int) -> tuple[TestAttempt | None, list[UserAnswer]]:
        attempt = await self.attempt_dao.get_by_id(attempt_id)
        if not attempt:
            return None, []
        
        result = await self.session.execute(
            select(TestAttemptModel)
            .where(TestAttemptModel.id == attempt_id)
            .options(selectinload(TestAttemptModel.answers))
        )
        attempt_model = result.scalar_one_or_none()
        if not attempt_model:
            return attempt, []
        
        answers = [UserAnswerDTO(answer).to_domain() for answer in attempt_model.answers]
        return attempt, answers
    
    async def get_answers_for_attempt(self, attempt_id: int) -> list[UserAnswer]:
        result = await self.session.execute(
            select(UserAnswerModel)
            .where(UserAnswerModel.attempt_id == attempt_id)
        )
        models = list(result.scalars().all())
        return [UserAnswerDTO(model).to_domain() for model in models]
    
    async def count_user_attempts(self, user_id: int, test_id: int | None = None) -> int:
        query = select(func.count(TestAttemptModel.id)).where(TestAttemptModel.user_id == user_id)
        if test_id is not None:
            query = query.where(TestAttemptModel.test_id == test_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        return count
    
    async def count_passed_attempts(self, user_id: int, test_id: int | None = None) -> int:
        query = (
            select(func.count(TestAttemptModel.id))
            .where(TestAttemptModel.user_id == user_id)
            .where(TestAttemptModel.is_passed == True)
        )
        if test_id is not None:
            query = query.where(TestAttemptModel.test_id == test_id)
        
        result = await self.session.execute(query)
        count = result.scalar_one()
        return count
    
    async def get_best_attempt(self, user_id: int, test_id: int) -> TestAttempt | None:
        result = await self.session.execute(
            select(TestAttemptModel)
            .where(TestAttemptModel.user_id == user_id)
            .where(TestAttemptModel.test_id == test_id)
            .where(TestAttemptModel.finished_at != None)
            .order_by(TestAttemptModel.score.desc(), TestAttemptModel.started_at.asc())
        )
        model = result.scalar_one_or_none()
        return TestAttemptDTO(model).to_domain() if model else None
    
    async def get_latest_attempt(self, user_id: int, test_id: int) -> TestAttempt | None:
        result = await self.session.execute(
            select(TestAttemptModel)
            .where(TestAttemptModel.user_id == user_id)
            .where(TestAttemptModel.test_id == test_id)
            .order_by(TestAttemptModel.started_at.desc())
        )
        model = result.scalar_one_or_none()
        return TestAttemptDTO(model).to_domain() if model else None
    
    async def finish_attempt(self, attempt_id: int, score: int, is_passed: bool) -> TestAttempt | None:
        return await self.attempt_dao.update(
            attempt_id=attempt_id,
            finished_at=datetime.utcnow(),
            score=score,
            is_passed=is_passed
        )
    
    async def calculate_attempt_score(self, attempt_id: int) -> int:
        result = await self.session.execute(
            select(func.count(UserAnswerModel.id))
            .where(UserAnswerModel.attempt_id == attempt_id)
            .where(UserAnswerModel.is_correct == True)
        )
        count = result.scalar_one()
        return count
    
    async def get_incorrect_answers(self, attempt_id: int) -> list[UserAnswer]:
        result = await self.session.execute(
            select(UserAnswerModel)
            .where(UserAnswerModel.attempt_id == attempt_id)
            .where(UserAnswerModel.is_correct == False)
        )
        models = list(result.scalars().all())
        return [UserAnswerDTO(model).to_domain() for model in models]
    
    async def get_question_statistics(self, question_id: int) -> dict[str, int]:
        total_result = await self.session.execute(
            select(func.count(UserAnswerModel.id))
            .where(UserAnswerModel.question_id == question_id)
        )
        total = total_result.scalar_one()
        
        correct_result = await self.session.execute(
            select(func.count(UserAnswerModel.id))
            .where(UserAnswerModel.question_id == question_id)
            .where(UserAnswerModel.is_correct == True)
        )
        correct = correct_result.scalar_one()
        
        return {
            "total_answers": total,
            "correct_answers": correct,
            "incorrect_answers": total - correct,
        }
    
    async def get_most_difficult_questions(self, test_id: int, limit: int = 10) -> list[tuple[int, float]]:
        from trudex.infrastructure.database.models import \
            Question as QuestionModel
        
        result = await self.session.execute(
            select(
                UserAnswerModel.question_id,
                func.count(UserAnswerModel.id).label("total"),
                func.sum(func.cast(UserAnswerModel.is_correct, func.Integer)).label("correct")
            )
            .join(QuestionModel, UserAnswerModel.question_id == QuestionModel.id)
            .where(QuestionModel.test_id == test_id)
            .group_by(UserAnswerModel.question_id)
            .having(func.count(UserAnswerModel.id) > 0)
            .order_by((func.sum(func.cast(UserAnswerModel.is_correct, func.Integer)) / func.count(UserAnswerModel.id)).asc())
            .limit(limit)
        )
        
        rows = result.all()
        return [(row.question_id, row.correct / row.total if row.total > 0 else 0.0) for row in rows]

    async def get_user_stats(self, user_id: int) -> dict:
        result = await self.session.execute(
            select(
                func.count(TestAttemptModel.id).label("total_attempts"),
                func.avg(TestAttemptModel.score).label("avg_score"),
            ).where(
                TestAttemptModel.user_id == user_id,
                TestAttemptModel.finished_at.isnot(None)
            )
        )
        row = result.one()
        return {
            "total_attempts": row.total_attempts or 0,
            "avg_score": round(row.avg_score, 1) if row.avg_score else 0,
        }
