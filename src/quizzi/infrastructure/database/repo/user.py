from typing import final

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from quizzi.domain.schemas import User
from quizzi.infrastructure.database.dao.user import UserDAO
from quizzi.infrastructure.database.dto.user import UserDTO
from quizzi.infrastructure.database.models import User as UserModel


@final
class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_dao = UserDAO(session)
    
    async def get_admins(self) -> list[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.is_admin == True)
        )
        models = list(result.scalars().all())
        return [UserDTO(model).to_domain() for model in models]
    
    async def get_users_by_group(self, group: int) -> list[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.group == group)
        )
        models = list(result.scalars().all())
        return [UserDTO(model).to_domain() for model in models]
    
    async def get_users_without_group(self) -> list[User]:
        result = await self.session.execute(
            select(UserModel).where(UserModel.group == None)
        )
        models = list(result.scalars().all())
        return [UserDTO(model).to_domain() for model in models]
    
    async def is_admin(self, user_id: int) -> bool:
        user = await self.user_dao.get_by_id(user_id)
        return user.is_admin if user else False
    
    async def has_group(self, user_id: int) -> bool:
        user = await self.user_dao.get_by_id(user_id)
        return user.group is not None if user else False
    
    async def count_users_by_group(self, group: int) -> int:
        result = await self.session.execute(
            select(func.count(UserModel.id))
            .where(UserModel.group == group)
        )
        count = result.scalar_one()
        return count
    
    async def count_admins(self) -> int:
        result = await self.session.execute(
            select(func.count(UserModel.id))
            .where(UserModel.is_admin == True)
        )
        count = result.scalar_one()
        return count
