from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from trudex.domain.schemas import User as DomainUser
from trudex.infrastructure.database.dto.user import UserDTO
from trudex.infrastructure.database.models import User


class _UNSET:
    """Sentinel для различения None и "не передано"."""
    pass


UNSET = _UNSET()


class UserDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session
    
    async def get_by_id(self, user_id: int) -> DomainUser | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        model = result.scalar_one_or_none()
        return UserDTO(model).to_domain() if model else None
    
    async def get_all(self) -> list[DomainUser]:
        result = await self.session.execute(
            select(User).order_by(User.created_at.desc())
        )
        models = list(result.scalars().all())
        return [UserDTO(model).to_domain() for model in models]
    
    async def create(
        self,
        user_id: int,
        first_name: str,
        username: str | None = None,
        last_name: str | None = None,
        name: str | None = None,
        group: int | None = None,
        is_admin: bool = False,
    ) -> DomainUser:
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            name=name,
            group=group,
            is_admin=is_admin,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return UserDTO(user).to_domain()
    
    async def update(
        self,
        user_id: int,
        username: str | None | _UNSET = UNSET,
        first_name: str | _UNSET = UNSET,
        last_name: str | None | _UNSET = UNSET,
        name: str | None | _UNSET = UNSET,
        group: int | None | _UNSET = UNSET,
        is_admin: bool | _UNSET = UNSET,
        name_updated_at: datetime | None | _UNSET = UNSET,
        group_updated_at: datetime | None | _UNSET = UNSET,
    ) -> DomainUser | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        
        if not isinstance(username, _UNSET):
            user.username = username
        if not isinstance(first_name, _UNSET):
            user.first_name = first_name
        if not isinstance(last_name, _UNSET):
            user.last_name = last_name
        if not isinstance(name, _UNSET):
            user.name = name
        if not isinstance(group, _UNSET):
            user.group = group
        if not isinstance(is_admin, _UNSET):
            user.is_admin = is_admin
        if not isinstance(name_updated_at, _UNSET):
            user.name_updated_at = name_updated_at
        if not isinstance(group_updated_at, _UNSET):
            user.group_updated_at = group_updated_at
        
        await self.session.flush()
        await self.session.refresh(user)
        return UserDTO(user).to_domain()
    
    async def delete(self, user_id: int) -> bool:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        
        await self.session.delete(user)
        await self.session.flush()
        return True
    
    async def upsert(
        self,
        user_id: int,
        first_name: str,
        username: str | None = None,
        last_name: str | None = None,
        name: str | None | _UNSET = UNSET,
        group: int | None | _UNSET = UNSET,
        is_admin: bool | _UNSET = UNSET,
    ) -> DomainUser:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            if not isinstance(name, _UNSET):
                user.name = name
            if not isinstance(group, _UNSET):
                user.group = group
            if not isinstance(is_admin, _UNSET):
                user.is_admin = is_admin
            await self.session.flush()
            await self.session.refresh(user)
            return UserDTO(user).to_domain()
        
        return await self.create(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            name=name if not isinstance(name, _UNSET) else None,
            group=group if not isinstance(group, _UNSET) else None,
            is_admin=is_admin if not isinstance(is_admin, _UNSET) else False,
        )
