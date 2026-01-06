from quizzi.domain.schemas import TestAttempt as DomainTestAttempt
from quizzi.infrastructure.database.models import TestAttempt as TestAttemptModel


class TestAttemptDTO:
    def __init__(self, model: TestAttemptModel) -> None:
        self.model: TestAttemptModel = model
    
    def to_domain(self) -> DomainTestAttempt:
        return DomainTestAttempt(
            id=self.model.id,
            user_id=self.model.user_id,
            test_id=self.model.test_id,
            started_at=self.model.started_at,
            finished_at=self.model.finished_at,
            score=self.model.score,
            is_passed=self.model.is_passed,
        )
