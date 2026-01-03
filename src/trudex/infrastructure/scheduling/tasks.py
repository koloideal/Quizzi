from dishka import AsyncContainer

from trudex.infrastructure.database.dao.test import TestDAO
from trudex.infrastructure.utils.timezone import now_msk


async def deactivate_expired_tests(container: AsyncContainer):
    async with container() as request_container:
        test_dao = await request_container.get(TestDAO)
        
        tests = await test_dao.get_all()
        
        for test in tests:
            if test.expires_at and test.expires_at < now_msk() and test.is_active:
                await test_dao.update(test.id, is_active=False)
