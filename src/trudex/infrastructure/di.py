import logging
from collections.abc import AsyncIterable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dishka import AsyncContainer, Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from trudex.infrastructure.database.config import new_session_maker
from trudex.infrastructure.database.dao.group import GroupDAO
from trudex.infrastructure.database.dao.option import OptionDAO
from trudex.infrastructure.database.dao.question import QuestionDAO
from trudex.infrastructure.database.dao.test import TestDAO
from trudex.infrastructure.database.dao.test_attempt import TestAttemptDAO
from trudex.infrastructure.database.dao.user import UserDAO
from trudex.infrastructure.database.dao.user_answer import UserAnswerDAO
from trudex.infrastructure.database.repo.test import TestRepository
from trudex.infrastructure.database.repo.test_attempt import TestAttemptRepository
from trudex.infrastructure.database.repo.user import UserRepository
from trudex.infrastructure.scheduling.tasks import deactivate_expired_tests
from trudex.infrastructure.utils.config import Config


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    def get_session_maker(self, config: Config) -> async_sessionmaker[AsyncSession]:
        return new_session_maker(config.database.url)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_maker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with session_maker() as session:
            yield session
            await session.commit()

    @provide(scope=Scope.REQUEST)
    def get_user_dao(self, session: AsyncSession) -> UserDAO:
        return UserDAO(session)
    
    @provide(scope=Scope.REQUEST)
    def get_group_dao(self, session: AsyncSession) -> GroupDAO:
        return GroupDAO(session)
    
    @provide(scope=Scope.REQUEST)
    def get_test_dao(self, session: AsyncSession) -> TestDAO:
        return TestDAO(session)
    
    @provide(scope=Scope.REQUEST)
    def get_question_dao(self, session: AsyncSession) -> QuestionDAO:
        return QuestionDAO(session)
    
    @provide(scope=Scope.REQUEST)
    def get_option_dao(self, session: AsyncSession) -> OptionDAO:
        return OptionDAO(session)
    
    @provide(scope=Scope.REQUEST)
    def get_test_attempt_dao(self, session: AsyncSession) -> TestAttemptDAO:
        return TestAttemptDAO(session)
    
    @provide(scope=Scope.REQUEST)
    def get_user_answer_dao(self, session: AsyncSession) -> UserAnswerDAO:
        return UserAnswerDAO(session)
    
    @provide(scope=Scope.REQUEST)
    def get_user_repository(self, session: AsyncSession) -> UserRepository:
        return UserRepository(session)
    
    @provide(scope=Scope.REQUEST)
    def get_test_repository(self, session: AsyncSession) -> TestRepository:
        return TestRepository(session)
    
    @provide(scope=Scope.REQUEST)
    def get_test_attempt_repository(self, session: AsyncSession) -> TestAttemptRepository:
        return TestAttemptRepository(session)


class SchedulerProvider(Provider):
    @provide(scope = Scope.APP)
    def get_scheduler(self, container: AsyncContainer) -> AsyncIOScheduler:
        logging.getLogger('apscheduler').setLevel(logging.WARNING)
        scheduler = AsyncIOScheduler()
        
        scheduler.add_job(
            deactivate_expired_tests,
            'interval',
            minutes=5,
            args=[container],
            id='deactivate_expired_tests',
        )
        
        return scheduler
