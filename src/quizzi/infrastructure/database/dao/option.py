from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quizzi.domain.schemas import Option as DomainOption
from quizzi.infrastructure.database.dto.option import OptionDTO
from quizzi.infrastructure.database.models import Option


class OptionDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session
    
    async def get_by_id(self, option_id: int) -> DomainOption | None:
        result = await self.session.execute(
            select(Option).where(Option.id == option_id)
        )
        model = result.scalar_one_or_none()
        return OptionDTO(model).to_domain() if model else None
    
    async def get_all(self) -> list[DomainOption]:
        result = await self.session.execute(select(Option))
        models = list(result.scalars().all())
        return [OptionDTO(model).to_domain() for model in models]
    
    async def create(
        self,
        question_id: int,
        text: str,
        is_correct: bool = False,
        explanation: str | None = None,
    ) -> DomainOption:
        option = Option(
            question_id=question_id,
            text=text,
            is_correct=is_correct,
            explanation=explanation,
        )
        self.session.add(option)
        await self.session.flush()
        await self.session.refresh(option)
        return OptionDTO(option).to_domain()
    
    async def update(
        self,
        option_id: int,
        text: str | None = None,
        is_correct: bool | None = None,
        explanation: str | None = None,
    ) -> DomainOption | None:
        result = await self.session.execute(
            select(Option).where(Option.id == option_id)
        )
        option = result.scalar_one_or_none()
        if not option:
            return None
        
        if text is not None:
            option.text = text
        if is_correct is not None:
            option.is_correct = is_correct
        if explanation is not None:
            option.explanation = explanation
        
        await self.session.flush()
        await self.session.refresh(option)
        return OptionDTO(option).to_domain()
    
    async def delete(self, option_id: int) -> bool:
        result = await self.session.execute(
            select(Option).where(Option.id == option_id)
        )
        option = result.scalar_one_or_none()
        if not option:
            return False
        
        await self.session.delete(option)
        await self.session.flush()
        return True
