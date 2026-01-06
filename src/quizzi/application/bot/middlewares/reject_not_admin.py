from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from dishka import AsyncContainer

from quizzi.infrastructure.database.repo import UserRepository
from quizzi.infrastructure.utils.config import Config


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
        
        if event.text and event.text.strip() in admin_commands:
            config: Config = await container.get(Config)
            
            if user_id == config.bot.creator_id:
                return await handler(event, data)
            
            users_repo: UserRepository = await container.get(UserRepository)
            is_admin = await users_repo.is_admin(user_id)
            
            if is_admin:
                return await handler(event, data)
            
            return
        
        return await handler(event, data)
