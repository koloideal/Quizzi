from collections.abc import Awaitable
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from dishka import AsyncContainer

from trudex.infrastructure.utils.config import Config


class RejectNotCreatorMiddleware(BaseMiddleware):
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
        creator_commands = ["/creator"]
        
        if event.text and event.text.strip() in creator_commands:
            config: Config = await container.get(Config)
            
            if user_id == config.bot.creator_id:
                return await handler(event, data)
            
            await event.answer("У вас нет доступа к панели создателя.")
            return
        
        return await handler(event, data)
