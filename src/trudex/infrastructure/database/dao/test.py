from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from trudex.domain.schemas import Test as DomainTest
from trudex.infrastructure.database.dto.test import TestDTO
from trudex.infrastructure.database.models import Test


class TestDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session
    
    async def get_by_id(self, test_id: int) -> DomainTest | None:
        result = await self.session.execute(
            select(Test).where(Test.id == test_id)
        )
        model = result.scalar_one_or_none()
        return TestDTO(model).to_domain() if model else None
    
    async def get_all(self) -> list[DomainTest]:
        result = await self.session.execute(
            select(Test).order_by(Test.id)
        )
        models = list(result.scalars().all())
        return [TestDTO(model).to_domain() for model in models]
    
    async def create(
        self,
        title: str,
        description: str | None = None,
        for_group: int | None = None,
        password: str | None = None,
        expires_at: datetime | None = None,
        is_active: bool = True,
    ) -> DomainTest:
        test = Test(
            title=title,
            description=description,
            for_group=for_group,
            password=password,
            expires_at=expires_at,
            is_active=is_active,
        )
        self.session.add(test)
        await self.session.flush()
        await self.session.refresh(test)
        return TestDTO(test).to_domain()
    
    async def update(
        self,
        test_id: int,
        title: str | None = None,
        description: str | None = None,
        for_group: int | None = None,
        password: str | None = None,
        expires_at: datetime | None = None,
        is_active: bool | None = None,
    ) -> DomainTest | None:
        result = await self.session.execute(
            select(Test).where(Test.id == test_id)
        )
        test = result.scalar_one_or_none()
        if not test:
            return None
        
        if title is not None:
            test.title = title
        if description is not None:
            test.description = description
        if for_group is not None:
            test.for_group = for_group
        if password is not None:
            test.password = password
        if expires_at is not None:
            test.expires_at = expires_at
        if is_active is not None:
            test.is_active = is_active
        
        await self.session.flush()
        await self.session.refresh(test)
        return TestDTO(test).to_domain()
    
    async def delete(self, test_id: int) -> bool:
        result = await self.session.execute(
            select(Test).where(Test.id == test_id)
        )
        test = result.scalar_one_or_none()
        if not test:
            return False
        
        await self.session.delete(test)
        await self.session.flush()
        return True
