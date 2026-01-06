from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quizzi.domain.schemas import UserAnswer as DomainUserAnswer
from quizzi.infrastructure.database.dto.user_answer import UserAnswerDTO
from quizzi.infrastructure.database.models import UserAnswer


class UserAnswerDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session
    
    async def get_by_id(self, answer_id: int) -> DomainUserAnswer | None:
        result = await self.session.execute(
            select(UserAnswer).where(UserAnswer.id == answer_id)
        )
        model = result.scalar_one_or_none()
        return UserAnswerDTO(model).to_domain() if model else None
    
    async def get_all(self) -> list[DomainUserAnswer]:
        result = await self.session.execute(select(UserAnswer))
        models = list(result.scalars().all())
        return [UserAnswerDTO(model).to_domain() for model in models]
    
    async def create(
        self,
        attempt_id: int,
        question_id: int,
        selected_option_id: int | None = None,
        text_answer: str | None = None,
        is_correct: bool = False,
    ) -> DomainUserAnswer:
        answer = UserAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_id=selected_option_id,
            text_answer=text_answer,
            is_correct=is_correct,
        )
        self.session.add(answer)
        await self.session.flush()
        await self.session.refresh(answer)
        return UserAnswerDTO(answer).to_domain()
    
    async def update(
        self,
        answer_id: int,
        selected_option_id: int | None = None,
        text_answer: str | None = None,
        is_correct: bool | None = None,
    ) -> DomainUserAnswer | None:
        result = await self.session.execute(
            select(UserAnswer).where(UserAnswer.id == answer_id)
        )
        answer = result.scalar_one_or_none()
        if not answer:
            return None
        
        if selected_option_id is not None:
            answer.selected_option_id = selected_option_id
        if text_answer is not None:
            answer.text_answer = text_answer
        if is_correct is not None:
            answer.is_correct = is_correct
        
        await self.session.flush()
        await self.session.refresh(answer)
        return UserAnswerDTO(answer).to_domain()
    
    async def delete(self, answer_id: int) -> bool:
        result = await self.session.execute(
            select(UserAnswer).where(UserAnswer.id == answer_id)
        )
        answer = result.scalar_one_or_none()
        if not answer:
            return False
        
        await self.session.delete(answer)
        await self.session.flush()
        return True
