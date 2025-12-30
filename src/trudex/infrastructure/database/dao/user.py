from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from trudex.infrastructure.database.models import User


class UserDAO:
    def __init__(self, session: AsyncSession) -> None:
        self.session: AsyncSession = session
    
    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> list[User]:
        result = await self.session.execute(select(User))
        return list(result.scalars().all())
    
    async def get_by_group(self, group: int) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.group == group)
        )
        return list(result.scalars().all())
    
    async def get_admins(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.is_admin == True)
        )
        return list(result.scalars().all())
    
    async def create(
        self,
        user_id: int,
        first_name: str,
        username: str | None = None,
        last_name: str | None = None,
        group: int | None = None,
        is_admin: bool = False,
    ) -> User:
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            group=group,
            is_admin=is_admin,
        )
        self.session.add(user)
        await self.session.flush()
        return user
    
    async def update(
        self,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        group: int | None = None,
        is_admin: bool | None = None,
    ) -> User | None:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        if username is not None:
            user.username = username
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if group is not None:
            user.group = group
        if is_admin is not None:
            user.is_admin = is_admin
        
        await self.session.flush()
        return user
    
    async def delete(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
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
        group: int | None = None,
        is_admin: bool = False,
    ) -> User:
        user = await self.get_by_id(user_id)
        if user:
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if group is not None:
                user.group = group
            if is_admin is not None:
                user.is_admin = is_admin
            await self.session.flush()
            return user
        
        return await self.create(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            group=group,
            is_admin=is_admin,
        )
