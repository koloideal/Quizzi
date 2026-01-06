import logging

from dishka import AsyncContainer

from quizzi.infrastructure.database.dao.test import TestDAO
from quizzi.infrastructure.utils.timezone import now_msk_naive

logger = logging.getLogger(__name__)


async def deactivate_expired_tests(container: AsyncContainer) -> None:
    async with container() as request_container:
        test_dao = await request_container.get(TestDAO)
        
        expired_tests = await test_dao.get_expired_active_tests(now_msk_naive())
        
        for test in expired_tests:
            await test_dao.update(test.id, is_active=False)
            logger.info("Деактивирован истёкший тест: id=%d, title=%s", test.id, test.title)
