from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from trudex.domain.schemas import User as DomainUser
from trudex.infrastructure.database.dto.user import UserDTO
from trudex.infrastructure.database.models import User


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
        result = await self.session.execute(select(User))
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
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        name: str | None = None,
        group: int | None = None,
        is_admin: bool | None = None,
        name_updated_at: datetime | None = None,
        group_updated_at: datetime | None = None,
    ) -> DomainUser | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        
        if username is not None:
            user.username = username
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if name is not None:
            user.name = name
        if group is not None:
            user.group = group
        if is_admin is not None:
            user.is_admin = is_admin
        if name_updated_at is not None:
            user.name_updated_at = name_updated_at
        if group_updated_at is not None:
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
        name: str | None = None,
        group: int | None = None,
        is_admin: bool | None = None,
    ) -> DomainUser:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if name is not None:
                user.name = name
            if group is not None:
                user.group = group
            if is_admin is not None:
                user.is_admin = is_admin
            await self.session.flush()
            await self.session.refresh(user)
            return UserDTO(user).to_domain()
        
        return await self.create(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            name=name,
            group=group,
            is_admin=is_admin or False,
        )
