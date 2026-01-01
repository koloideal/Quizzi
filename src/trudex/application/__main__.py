import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from dishka import make_async_container
from dishka.integrations.aiogram import setup_dishka

from trudex.application.bot.handlers import router
from trudex.infrastructure.di import DatabaseProvider
from trudex.infrastructure.utils.config import Config


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    config = Config.from_toml("config.toml")
    
    bot = Bot(
        token=config.bot.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    dp.include_router(router)
    
    container = make_async_container(DatabaseProvider())
    setup_dishka(container, dp)
    
    logging.info("Бот запущен")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
