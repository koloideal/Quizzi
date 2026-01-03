from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import ErrorEvent, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent
from dishka.integrations.aiogram import FromDishka

from trudex.application.bot.admin_dialogs.states import AdminMenuSG
from trudex.application.bot.creator_dialogs.states import CreatorMenuSG
from trudex.application.bot.user_dialogs.states import (UserMenuSG,
                                                        UserRegistrationSG)
from trudex.infrastructure.database.dao.group import GroupDAO
from trudex.infrastructure.database.dao.user import UserDAO

router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message,
    user_dao: FromDishka[UserDAO],
    group_dao: FromDishka[GroupDAO],
    dialog_manager: DialogManager
) -> None:
    assert message.from_user is not None
    
    existing_user = await user_dao.get_by_id(message.from_user.id)
    
    if existing_user is None:
        groups = await group_dao.get_all()
        
        if len(groups) > 0:
            await user_dao.create(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username,
                last_name=message.from_user.last_name,
            )
            await dialog_manager.start(
                UserRegistrationSG.input_name,
                mode=StartMode.RESET_STACK,
                data={"user_id": message.from_user.id}
            )
        else:
            await user_dao.create(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username,
                last_name=message.from_user.last_name,
            )
            await dialog_manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)
    else:
        groups = await group_dao.get_all()
        
        if len(groups) > 0 and (existing_user.name is None or existing_user.group is None):
            if existing_user.name is None:
                await dialog_manager.start(
                    UserRegistrationSG.input_name,
                    mode=StartMode.RESET_STACK,
                    data={"user_id": message.from_user.id}
                )
            else:
                await dialog_manager.start(
                    UserRegistrationSG.select_group,
                    mode=StartMode.RESET_STACK,
                    data={"user_id": message.from_user.id}
                )
        else:
            await user_dao.upsert(
                user_id=message.from_user.id,
                first_name=message.from_user.first_name,
                username=message.from_user.username,
                last_name=message.from_user.last_name,
            )
            await dialog_manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)


@router.message(Command("admin"))
async def admin_command(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


@router.message(Command("creator"))
async def creator_command(message: Message, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(CreatorMenuSG.main, mode=StartMode.RESET_STACK)


@router.error()
async def dialog_error_handler(event: ErrorEvent, dialog_manager: DialogManager) -> None:
    if isinstance(event.exception, (UnknownIntent, OutdatedIntent)):
        await dialog_manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)
