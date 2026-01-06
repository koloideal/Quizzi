from quizzi.domain.schemas import Question as DomainQuestion
from quizzi.infrastructure.database.models import Question as QuestionModel


class QuestionDTO:
    def __init__(self, model: QuestionModel) -> None:
        self.model: QuestionModel = model
    
    def to_domain(self) -> DomainQuestion:
        return DomainQuestion(
            id=self.model.id,
            test_id=self.model.test_id,
            text=self.model.text,
            position=self.model.position,
            question_type=self.model.question_type,
            tg_file_id=self.model.tg_file_id,
        )
