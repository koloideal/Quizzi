from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quizzi.domain.schemas import TestAttempt as DomainTestAttempt
from quizzi.infrastructure.database.dto.test_attempt import TestAttemptDTO
from quizzi.infrastructure.database.models import TestAttempt


class TestAttemptDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session
    
    async def get_by_id(self, attempt_id: int) -> DomainTestAttempt | None:
        result = await self.session.execute(
            select(TestAttempt).where(TestAttempt.id == attempt_id)
        )
        model = result.scalar_one_or_none()
        return TestAttemptDTO(model).to_domain() if model else None
    
    async def get_all(self) -> list[DomainTestAttempt]:
        result = await self.session.execute(select(TestAttempt))
        models = list(result.scalars().all())
        return [TestAttemptDTO(model).to_domain() for model in models]
    
    async def create(
        self,
        user_id: int,
        test_id: int,
        score: int = 0,
        is_passed: bool = False,
    ) -> DomainTestAttempt:
        attempt = TestAttempt(
            user_id=user_id,
            test_id=test_id,
            started_at=datetime.utcnow(),
            score=score,
            is_passed=is_passed,
        )
        self.session.add(attempt)
        await self.session.flush()
        await self.session.refresh(attempt)
        return TestAttemptDTO(attempt).to_domain()
    
    async def update(
        self,
        attempt_id: int,
        finished_at: datetime | None = None,
        warning_sent_at: datetime | None = None,
        score: int | None = None,
        is_passed: bool | None = None,
    ) -> DomainTestAttempt | None:
        result = await self.session.execute(
            select(TestAttempt).where(TestAttempt.id == attempt_id)
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            return None
        
        if finished_at is not None:
            attempt.finished_at = finished_at
        if warning_sent_at is not None:
            attempt.warning_sent_at = warning_sent_at
        if score is not None:
            attempt.score = score
        if is_passed is not None:
            attempt.is_passed = is_passed
        
        await self.session.flush()
        await self.session.refresh(attempt)
        return TestAttemptDTO(attempt).to_domain()
    
    async def delete(self, attempt_id: int) -> bool:
        result = await self.session.execute(
            select(TestAttempt).where(TestAttempt.id == attempt_id)
        )
        attempt = result.scalar_one_or_none()
        if not attempt:
            return False
        
        await self.session.delete(attempt)
        await self.session.flush()
        return True
    
    async def get_by_user_id(self, user_id: int) -> list[DomainTestAttempt]:
        result = await self.session.execute(
            select(TestAttempt).where(TestAttempt.user_id == user_id)
        )
        models = list(result.scalars().all())
        return [TestAttemptDTO(model).to_domain() for model in models]
