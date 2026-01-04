import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram_dialog import setup_dialogs
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dishka import make_async_container
from dishka.integrations.aiogram import setup_dishka

from trudex.application.bot.admin_dialogs.broadcast import broadcast_dialog as admin_broadcast_dialog
from trudex.application.bot.admin_dialogs.create_test import admin_create_test_dialog
from trudex.application.bot.admin_dialogs.groups import groups_dialog as admin_groups_dialog
from trudex.application.bot.admin_dialogs.main_menu import admin_menu_dialog
from trudex.application.bot.admin_dialogs.templates import templates_dialog as admin_templates_dialog
from trudex.application.bot.admin_dialogs.tests import tests_dialog as admin_tests_dialog
from trudex.application.bot.admin_dialogs.users import users_dialog as admin_users_dialog
from trudex.application.bot.creator_dialogs.broadcast import broadcast_dialog as creator_broadcast_dialog
from trudex.application.bot.creator_dialogs.create_test import create_test_dialog
from trudex.application.bot.creator_dialogs.groups import groups_dialog as creator_groups_dialog
from trudex.application.bot.creator_dialogs.main_menu import creator_menu_dialog
from trudex.application.bot.creator_dialogs.templates import templates_dialog as creator_templates_dialog
from trudex.application.bot.creator_dialogs.tests import tests_dialog as creator_tests_dialog
from trudex.application.bot.creator_dialogs.users import users_dialog as creator_users_dialog
from trudex.application.bot.handlers import router
from trudex.application.bot.middlewares.reject_not_admin import RejectNotAdminMiddleware
from trudex.application.bot.middlewares.reject_not_creator import RejectNotCreatorMiddleware
from trudex.application.bot.user_dialogs.deeplink import deeplink_dialog
from trudex.application.bot.user_dialogs.main_menu import user_menu_dialog
from trudex.application.bot.user_dialogs.registration import registration_dialog
from trudex.application.bot.user_dialogs.take_test import take_test_dialog
from trudex.infrastructure.database.repo.user import UserRepository
from trudex.infrastructure.di import DatabaseProvider, SchedulerProvider
from trudex.infrastructure.utils.bot_commands import setup_bot_commands
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
    
    dp.include_routers(
        router,
        user_menu_dialog,
        take_test_dialog,
        registration_dialog,
        deeplink_dialog,
        admin_menu_dialog,
        admin_users_dialog,
        admin_tests_dialog,
        admin_groups_dialog,
        admin_broadcast_dialog,
        admin_templates_dialog,
        admin_create_test_dialog,
        creator_menu_dialog,
        creator_users_dialog,
        creator_tests_dialog,
        creator_groups_dialog,
        creator_broadcast_dialog,
        creator_templates_dialog,
        create_test_dialog,
    )
    
    router.message.middleware(RejectNotAdminMiddleware())
    router.message.middleware(RejectNotCreatorMiddleware())
    
    container = make_async_container(
        DatabaseProvider(),
        SchedulerProvider(),
        context={Bot: bot, Config: config}
    )
    setup_dialogs(dp)
    setup_dishka(container, dp, auto_inject=True)
    
    async with container() as request_container:
        user_repo = await request_container.get(UserRepository)
        await setup_bot_commands(bot, config, user_repo)
    
    scheduler = await container.get(AsyncIOScheduler)
    scheduler.start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    
    logging.info("Бот запущен")
    logging.info("Планировщик задач запущен")
    
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
