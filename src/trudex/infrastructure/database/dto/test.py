from trudex.domain.schemas import Test as DomainTest
from trudex.infrastructure.database.models import Test as TestModel


class TestDTO:
    def __init__(self, model: TestModel) -> None:
        self.model: TestModel = model
    
    def to_domain(self) -> DomainTest:
        return DomainTest(
            id=self.model.id,
            title=self.model.title,
            description=self.model.description,
            for_group=self.model.for_group,
            password=self.model.password,
            expires_at=self.model.expires_at,
            is_active=self.model.is_active,
            created_at=self.model.created_at,
            updated_at=self.model.updated_at,
        )
