import asyncio
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from trudex.infrastructure.database.dao.user import UserDAO


@dataclass
class BroadcastStats:
    success: int
    failed: int
    total: int


async def broadcast_message(bot: Bot, message_id: int, chat_id: int, user_dao: UserDAO) -> BroadcastStats:
    users = await user_dao.get_all()
    success = 0
    failed = 0
    
    for user in users:
        try:
            await bot.copy_message(chat_id=user.id, from_chat_id=chat_id, message_id=message_id)
            success += 1
        except TelegramForbiddenError:
            failed += 1
        except TelegramBadRequest:
            failed += 1
        except Exception:
            failed += 1
        
        await asyncio.sleep(0.1)
    
    return BroadcastStats(success=success, failed=failed, total=len(users))
