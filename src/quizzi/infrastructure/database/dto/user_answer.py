from quizzi.domain.schemas import UserAnswer as DomainUserAnswer
from quizzi.infrastructure.database.models import UserAnswer as UserAnswerModel


class UserAnswerDTO:
    def __init__(self, model: UserAnswerModel) -> None:
        self.model: UserAnswerModel = model
    
    def to_domain(self) -> DomainUserAnswer:
        return DomainUserAnswer(
            id=self.model.id,
            attempt_id=self.model.attempt_id,
            question_id=self.model.question_id,
            selected_option_id=self.model.selected_option_id,
            text_answer=self.model.text_answer,
            is_correct=self.model.is_correct,
        )
