from typing import final
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from trudex.domain.schemas import Option, Question, Test
from trudex.infrastructure.database.dao.option import OptionDAO
from trudex.infrastructure.database.dao.question import QuestionDAO
from trudex.infrastructure.database.dao.test import TestDAO
from trudex.infrastructure.database.dto.option import OptionDTO
from trudex.infrastructure.database.dto.question import QuestionDTO
from trudex.infrastructure.database.dto.test import TestDTO
from trudex.infrastructure.database.models import (
    Option as OptionModel,
    Question as QuestionModel,
    Test as TestModel,
)


@final
class TestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.test_dao = TestDAO(session)
        self.question_dao = QuestionDAO(session)
        self.option_dao = OptionDAO(session)
    
    async def get_active_tests(self) -> list[Test]:
        result = await self.session.execute(
            select(TestModel).where(TestModel.is_active == True)
        )
        models = list(result.scalars().all())
        return [TestDTO(model).to_domain() for model in models]
    
    async def get_tests_by_group(self, group: int) -> list[Test]:
        result = await self.session.execute(
            select(TestModel).where(TestModel.for_group == group)
        )
        models = list(result.scalars().all())
        return [TestDTO(model).to_domain() for model in models]
    
    async def get_active_tests_by_group(self, group: int) -> list[Test]:
        result = await self.session.execute(
            select(TestModel)
            .where(TestModel.for_group == group)
            .where(TestModel.is_active == True)
        )
        models = list(result.scalars().all())
        return [TestDTO(model).to_domain() for model in models]
    
    async def get_test_with_questions(self, test_id: int) -> tuple[Test | None, list[Question]]:
        test = await self.test_dao.get_by_id(test_id)
        if not test:
            return None, []
        
        result = await self.session.execute(
            select(TestModel)
            .where(TestModel.id == test_id)
            .options(selectinload(TestModel.questions))
        )
        test_model = result.scalar_one_or_none()
        if not test_model:
            return test, []
        
        questions = [QuestionDTO(q).to_domain() for q in sorted(test_model.questions, key=lambda x: x.position)]
        return test, questions
    
    async def get_question_with_options(self, question_id: int) -> tuple[Question | None, list[Option]]:
        question = await self.question_dao.get_by_id(question_id)
        if not question:
            return None, []
        
        result = await self.session.execute(
            select(QuestionModel)
            .where(QuestionModel.id == question_id)
            .options(selectinload(QuestionModel.options))
        )
        question_model = result.scalar_one_or_none()
        if not question_model:
            return question, []
        
        options = [OptionDTO(o).to_domain() for o in question_model.options]
        return question, options
    
    async def get_correct_options_for_question(self, question_id: int) -> list[Option]:
        result = await self.session.execute(
            select(OptionModel)
            .where(OptionModel.question_id == question_id)
            .where(OptionModel.is_correct == True)
        )
        models = list(result.scalars().all())
        return [OptionDTO(model).to_domain() for model in models]
    
    async def get_full_test(self, test_id: int) -> tuple[Test | None, list[tuple[Question, list[Option]]]]:
        test = await self.test_dao.get_by_id(test_id)
        if not test:
            return None, []
        
        result = await self.session.execute(
            select(TestModel)
            .where(TestModel.id == test_id)
            .options(
                selectinload(TestModel.questions).selectinload(QuestionModel.options)
            )
        )
        test_model = result.scalar_one_or_none()
        if not test_model:
            return test, []
        
        questions_with_options: list[tuple[Question, list[Option]]] = []
        for question_model in sorted(test_model.questions, key=lambda x: x.position):
            question = QuestionDTO(question_model).to_domain()
            options = [OptionDTO(o).to_domain() for o in question_model.options]
            questions_with_options.append((question, options))
        
        return test, questions_with_options
    
    async def count_questions_in_test(self, test_id: int) -> int:
        result = await self.session.execute(
            select(func.count(QuestionModel.id))
            .where(QuestionModel.test_id == test_id)
        )
        count = result.scalar_one()
        return count
    
    async def duplicate_test(self, test_id: int, new_title: str) -> Test | None:
        test, questions_with_options = await self.get_full_test(test_id)
        if not test:
            return None
        
        new_test = await self.test_dao.create(
            title=new_title,
            description=test.description,
            for_group=test.for_group,
            is_active=False,
        )
        
        for question, options in questions_with_options:
            new_question = await self.question_dao.create(
                test_id=new_test.id,
                text=question.text,
                position=question.position,
                question_type=question.question_type,
                tg_file_id=question.tg_file_id,
            )
            
            for option in options:
                _ = await self.option_dao.create(
                        question_id=new_question.id,
                        text=option.text,
                        is_correct=option.is_correct,
                        explanation=option.explanation,
                    )
        
        return new_test
