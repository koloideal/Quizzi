from typing import Any, Callable
from collections.abc import Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from dishka import AsyncContainer

from trudex.infrastructure.database.repo import UserRepository


class RejectNotAdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        assert event.from_user is not None
        
        container: AsyncContainer = data["dishka_container"]
        user_id = event.from_user.id
        admin_commands = ["/admin"]
        if event.text:
            if event.text.strip() in admin_commands:
                users_dao: UserRepository = await container.get(UserRepository)
                admins = await users_dao.get_admins()
                if user_id in [admin.id for admin in admins]:
                    return await handler(event, data)
                else:
                    pass
            else:
                return await handler(event, data)
        else:
            return await handler(event, data)
