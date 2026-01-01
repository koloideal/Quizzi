from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from dishka.integrations.aiogram import FromDishka

from trudex.application.bot.admin_dialogs.states import AdminMenuSG
from trudex.application.bot.creator_dialogs.states import CreatorMenuSG
from trudex.infrastructure.database.dao.user import UserDAO


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, user_dao: FromDishka[UserDAO]) -> None:
    assert message.from_user is not None
    
    await user_dao.upsert(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        last_name=message.from_user.last_name,
    )
    
    await message.answer("Привет! Я бот для тестирования по охране труда.")


@router.message(Command("admin"))
async def admin_command(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


@router.message(Command("creator"))
async def creator_command(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(CreatorMenuSG.main, mode=StartMode.RESET_STACK)
