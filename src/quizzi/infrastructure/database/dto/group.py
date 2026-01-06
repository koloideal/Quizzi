from quizzi.domain.schemas import Group as DomainGroup
from quizzi.infrastructure.database.models import Group as GroupModel


class GroupDTO:
    def __init__(self, model: GroupModel) -> None:
        self.model: GroupModel = model
    
    def to_domain(self) -> DomainGroup:
        return DomainGroup(
            id=self.model.id,
            number=self.model.number,
            created_at=self.model.created_at,
            updated_at=self.model.updated_at,
        )
