from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quizzi.domain.schemas import Question as DomainQuestion
from quizzi.domain.schemas import QuestionType
from quizzi.infrastructure.database.dto.question import QuestionDTO
from quizzi.infrastructure.database.models import Question


class QuestionDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session
    
    async def get_by_id(self, question_id: int) -> DomainQuestion | None:
        result = await self.session.execute(
            select(Question).where(Question.id == question_id)
        )
        model = result.scalar_one_or_none()
        return QuestionDTO(model).to_domain() if model else None
    
    async def get_all(self) -> list[DomainQuestion]:
        result = await self.session.execute(select(Question))
        models = list(result.scalars().all())
        return [QuestionDTO(model).to_domain() for model in models]
    
    async def create(
        self,
        test_id: int,
        text: str,
        position: int = 0,
        question_type: str | QuestionType = QuestionType.SINGLE,
        tg_file_id: str | None = None,
    ) -> DomainQuestion:
        if isinstance(question_type, str):
            question_type = QuestionType(question_type)
        question = Question(
            test_id=test_id,
            text=text,
            position=position,
            question_type=question_type,
            tg_file_id=tg_file_id,
        )
        self.session.add(question)
        await self.session.flush()
        await self.session.refresh(question)
        return QuestionDTO(question).to_domain()
    
    async def update(
        self,
        question_id: int,
        text: str | None = None,
        position: int | None = None,
        question_type: str | QuestionType | None = None,
        tg_file_id: str | None = None,
    ) -> DomainQuestion | None:
        result = await self.session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            return None
        
        if text is not None:
            question.text = text
        if position is not None:
            question.position = position
        if question_type is not None:
            if isinstance(question_type, str):
                question_type = QuestionType(question_type)
            question.question_type = question_type
        if tg_file_id is not None:
            question.tg_file_id = tg_file_id
        
        await self.session.flush()
        await self.session.refresh(question)
        return QuestionDTO(question).to_domain()
    
    async def delete(self, question_id: int) -> bool:
        result = await self.session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            return False
        
        await self.session.delete(question)
        await self.session.flush()
        return True
