from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from quizzi.infrastructure.database.dao.user import UserDAO


@dataclass
class BroadcastStats:
    total: int
    success: int
    failed: int


class BroadcastService:
    def __init__(self, user_dao: UserDAO) -> None:
        self._user_dao = user_dao
    
    async def broadcast_message(
        self,
        bot: Bot,
        message_id: int,
        from_chat_id: int,
        group_numbers: list[int] | None = None,
    ) -> BroadcastStats:
        if group_numbers:
            users = await self._user_dao.get_by_groups(group_numbers)
        else:
            users = await self._user_dao.get_all()
        
        total = len(users)
        success = 0
        failed = 0
        
        for user in users:
            try:
                await bot.copy_message(
                    chat_id=user.id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                )
                success += 1
            except TelegramAPIError:
                failed += 1
        
        return BroadcastStats(total=total, success=success, failed=failed)
