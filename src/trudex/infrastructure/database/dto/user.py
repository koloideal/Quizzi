from trudex.domain.schemas import User as DomainUser
from trudex.infrastructure.database.models import User as UserModel


class UserDTO:
    def __init__(self, model: UserModel) -> None:
        self.model: UserModel = model
    
    def to_domain(self) -> DomainUser:
        return DomainUser(
            id=self.model.id,
            username=self.model.username,
            first_name=self.model.first_name,
            last_name=self.model.last_name,
            group=self.model.group,
            is_admin=self.model.is_admin,
            created_at=self.model.created_at,
            updated_at=self.model.updated_at,
        )
