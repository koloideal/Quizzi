from dataclasses import dataclass

from quizzi.domain.schemas import User
from quizzi.infrastructure.database.dao.group import GroupDAO
from quizzi.infrastructure.database.dao.user import UserDAO


@dataclass
class RegistrationResult:
    is_registered: bool
    needs_name: bool = False
    needs_group: bool = False
    has_groups: bool = False
    user: User | None = None


class UserService:
    def __init__(self, user_dao: UserDAO, group_dao: GroupDAO) -> None:
        self._user_dao = user_dao
        self._group_dao = group_dao
    
    async def check_registration(self, user_id: int) -> RegistrationResult:
        user = await self._user_dao.get_by_id(user_id)
        groups = await self._group_dao.get_all()
        has_groups = len(groups) > 0
        
        if user is None:
            return RegistrationResult(
                is_registered=False,
                needs_name=True,
                needs_group=has_groups,
                has_groups=has_groups,
            )
        
        needs_name = user.name is None
        needs_group = has_groups and user.group is None
        
        return RegistrationResult(
            is_registered=not needs_name and not needs_group,
            needs_name=needs_name,
            needs_group=needs_group,
            has_groups=has_groups,
            user=user,
        )
    
    async def create_user(
        self,
        user_id: int,
        first_name: str,
        username: str | None = None,
        last_name: str | None = None,
    ) -> User:
        return await self._user_dao.create(
            user_id=user_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
        )
    
    async def update_user_info(
        self,
        user_id: int,
        first_name: str,
        username: str | None = None,
        last_name: str | None = None,
    ) -> User | None:
        return await self._user_dao.upsert(
            user_id=user_id,
            first_name=first_name,
            username=username,
            last_name=last_name,
        )
    
    async def get_all_users(self) -> list[User]:
        return await self._user_dao.get_all()
