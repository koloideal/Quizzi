from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from trudex.domain.schemas import Group as DomainGroup
from trudex.infrastructure.database.dto.group import GroupDTO
from trudex.infrastructure.database.models import Group


class GroupDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session
    
    async def get_by_id(self, group_id: int) -> DomainGroup | None:
        result = await self.session.execute(
            select(Group).where(Group.id == group_id)
        )
        model = result.scalar_one_or_none()
        return GroupDTO(model).to_domain() if model else None
    
    async def get_by_number(self, number: int) -> DomainGroup | None:
        result = await self.session.execute(
            select(Group).where(Group.number == number)
        )
        model = result.scalar_one_or_none()
        return GroupDTO(model).to_domain() if model else None
    
    async def get_all(self) -> list[DomainGroup]:
        result = await self.session.execute(select(Group))
        models = list(result.scalars().all())
        return [GroupDTO(model).to_domain() for model in models]
    
    async def create(
        self,
        number: int,
    ) -> DomainGroup:
        group = Group(
            number=number,
        )
        self.session.add(group)
        await self.session.flush()
        await self.session.refresh(group)
        return GroupDTO(group).to_domain()
    
    async def update(
        self,
        group_id: int,
        number: int | None = None
    ) -> DomainGroup | None:
        result = await self.session.execute(
            select(Group).where(Group.id == group_id)
        )
        group = result.scalar_one_or_none()
        if not group:
            return None
        
        if number is not None:
            group.number = number
        
        await self.session.flush()
        await self.session.refresh(group)
        return GroupDTO(group).to_domain()
    
    async def delete(self, group_id: int) -> bool:
        result = await self.session.execute(
            select(Group).where(Group.id == group_id)
        )
        group = result.scalar_one_or_none()
        if not group:
            return False
        
        await self.session.delete(group)
        await self.session.flush()
        return True
