from quizzi.domain.schemas import Test as DomainTest
from quizzi.infrastructure.database.models import Test as TestModel


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
            attempts=self.model.attempts,
            is_active=self.model.is_active,
            are_results_viewable=self.model.are_results_viewable,
            created_at=self.model.created_at,
            updated_at=self.model.updated_at,
        )
