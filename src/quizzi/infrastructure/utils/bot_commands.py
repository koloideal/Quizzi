from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat

from quizzi.infrastructure.database.repo.user import UserRepository
from quizzi.infrastructure.utils.config import Config


async def setup_bot_commands(bot: Bot, config: Config, user_repo: UserRepository) -> None:
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Главное меню"),
        ],
        scope=BotCommandScopeAllPrivateChats(),
    )
    
    admins = await user_repo.get_admins()
    for admin in admins:
        await bot.set_my_commands(
            commands=[
                BotCommand(command="start", description="Главное меню"),
                BotCommand(command="admin", description="Админ-панель"),
            ],
            scope=BotCommandScopeChat(chat_id=admin.id),
        )
    
    await bot.set_my_commands(
        commands=[
            BotCommand(command="start", description="Главное меню"),
            BotCommand(command="creator", description="Панель создателя"),
        ],
        scope=BotCommandScopeChat(chat_id=config.bot.creator_id),
    )
