import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_dialog import setup_dialogs
from dishka import make_async_container
from dishka.integrations.aiogram import setup_dishka

from trudex.application.bot.admin_dialogs.main_menu import admin_menu_dialog
from trudex.application.bot.creator_dialogs.main_menu import creator_menu_dialog
from trudex.application.bot.handlers import router
from trudex.application.bot.middlewares.reject_not_admin import RejectNotAdminMiddleware
from trudex.application.bot.middlewares.reject_not_creator import RejectNotCreatorMiddleware
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
    dp.message.middleware(RejectNotAdminMiddleware())
    dp.message.middleware(RejectNotCreatorMiddleware())
    dp.include_router(router)
    
    dp.include_router(admin_menu_dialog)
    dp.include_router(creator_menu_dialog)
    
    container = make_async_container(DatabaseProvider())
    setup_dishka(container, dp, auto_inject=True)
    setup_dialogs(dp)
    
    logging.info("Бот запущен")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
