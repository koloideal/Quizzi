from trudex.domain.schemas import Option as DomainOption
from trudex.infrastructure.database.models import Option as OptionModel


class OptionDTO:
    def __init__(self, model: OptionModel) -> None:
        self.model: OptionModel = model
    
    def to_domain(self) -> DomainOption:
        return DomainOption(
            id=self.model.id,
            question_id=self.model.question_id,
            text=self.model.text,
            is_correct=self.model.is_correct,
            explanation=self.model.explanation,
        )
