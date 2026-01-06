from datetime import datetime
from typing import NotRequired, TypedDict, Unpack

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from quizzi.domain.schemas import Test as DomainTest
from quizzi.infrastructure.database.dto.test import TestDTO
from quizzi.infrastructure.database.models import Test


class _UNSET:
    """Sentinel для различения None и "не передано"."""
    pass


UNSET = _UNSET()


class TestUpdateFields(TypedDict, total=False):
    title: str
    description: str | None
    for_group: int | None
    password: str | None
    expires_at: datetime | None
    attempts: int | None
    time_limit: int | None
    is_active: bool
    are_results_viewable: bool


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
            select(Test).order_by(Test.created_at.desc())
        )
        models = list(result.scalars().all())
        return [TestDTO(model).to_domain() for model in models]
    
    async def get_expired_active_tests(self, now: datetime) -> list[DomainTest]:
        result = await self.session.execute(
            select(Test)
            .where(Test.is_active == True)
            .where(Test.expires_at.isnot(None))
            .where(Test.expires_at < now)
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
        attempts: int | None = None,
        time_limit: int | None = None,
        is_active: bool = True,
        are_results_viewable: bool = False,
    ) -> DomainTest:
        test = Test(
            title=title,
            description=description,
            for_group=for_group,
            password=password,
            expires_at=expires_at,
            attempts=attempts,
            time_limit=time_limit,
            is_active=is_active,
            are_results_viewable=are_results_viewable,
        )
        self.session.add(test)
        await self.session.flush()
        await self.session.refresh(test)
        return TestDTO(test).to_domain()
    
    async def update(
        self,
        test_id: int,
        title: str | _UNSET = UNSET,
        description: str | None | _UNSET = UNSET,
        for_group: int | None | _UNSET = UNSET,
        password: str | None | _UNSET = UNSET,
        expires_at: datetime | None | _UNSET = UNSET,
        attempts: int | None | _UNSET = UNSET,
        time_limit: int | None | _UNSET = UNSET,
        is_active: bool | _UNSET = UNSET,
        are_results_viewable: bool | _UNSET = UNSET,
    ) -> DomainTest | None:
        result = await self.session.execute(
            select(Test).where(Test.id == test_id)
        )
        test = result.scalar_one_or_none()
        if not test:
            return None
        
        if not isinstance(title, _UNSET):
            test.title = title
        if not isinstance(description, _UNSET):
            test.description = description
        if not isinstance(for_group, _UNSET):
            test.for_group = for_group
        if not isinstance(password, _UNSET):
            test.password = password
        if not isinstance(expires_at, _UNSET):
            test.expires_at = expires_at
        if not isinstance(attempts, _UNSET):
            test.attempts = attempts
        if not isinstance(time_limit, _UNSET):
            test.time_limit = time_limit
        if not isinstance(is_active, _UNSET):
            test.is_active = is_active
        if not isinstance(are_results_viewable, _UNSET):
            test.are_results_viewable = are_results_viewable
        
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
