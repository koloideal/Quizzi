import asyncio
import logging
from dataclasses import dataclass

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
)

from trudex.infrastructure.database.dao.user import UserDAO

logger = logging.getLogger(__name__)


@dataclass
class BroadcastStats:
    success: int
    failed: int
    total: int


async def broadcast_message(bot: Bot, message_id: int, chat_id: int, user_dao: UserDAO) -> BroadcastStats:
    users = await user_dao.get_all()
    success = 0
    failed = 0
    
    logger.info("Starting broadcast: message_id=%d, total_users=%d", message_id, len(users))
    
    for user in users:
        try:
            await bot.copy_message(chat_id=user.id, from_chat_id=chat_id, message_id=message_id)
            success += 1
        except TelegramRetryAfter as e:
            logger.warning("Rate limited, waiting %d seconds", e.retry_after)
            await asyncio.sleep(e.retry_after)
            # Retry after waiting
            try:
                await bot.copy_message(chat_id=user.id, from_chat_id=chat_id, message_id=message_id)
                success += 1
            except TelegramAPIError:
                failed += 1
        except TelegramForbiddenError:
            logger.debug("Broadcast failed (forbidden): user_id=%d", user.id)
            failed += 1
        except TelegramBadRequest as e:
            logger.debug("Broadcast failed (bad request): user_id=%d, error=%s", user.id, e)
            failed += 1
        except TelegramNetworkError as e:
            logger.warning("Network error during broadcast: user_id=%d, error=%s", user.id, e)
            failed += 1
        except TelegramAPIError as e:
            logger.warning("Telegram API error during broadcast: user_id=%d, error=%s", user.id, e)
            failed += 1
        
        await asyncio.sleep(0.05)
    
    logger.info("Broadcast completed: success=%d, failed=%d, total=%d", success, failed, len(users))
    return BroadcastStats(success=success, failed=failed, total=len(users))
