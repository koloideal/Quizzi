import logging

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import ErrorEvent, Message
from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.api.exceptions import OutdatedIntent, UnknownIntent
from dishka.integrations.aiogram import FromDishka

from quizzi.application.bot.admin_dialogs.states import AdminMenuSG
from quizzi.application.bot.creator_dialogs.states import CreatorMenuSG
from quizzi.application.bot.user_dialogs.states import UserDeeplinkSG, UserMenuSG, UserRegistrationSG
from quizzi.service.test import TestService
from quizzi.service.user import UserService

router = Router()
logger = logging.getLogger(__name__)


async def ensure_user_registered(
    user_service: UserService,
    message: Message,
    dialog_manager: DialogManager,
    pending_test_id: int | None = None,
) -> bool:
    assert message.from_user is not None
    
    result = await user_service.check_registration(message.from_user.id)
    
    start_data = {"user_id": message.from_user.id, "has_groups": result.has_groups}
    if pending_test_id:
        start_data["pending_test_id"] = pending_test_id
    
    if result.user is None:
        await user_service.create_user(
            user_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username,
            last_name=message.from_user.last_name,
        )
        await dialog_manager.start(
            UserRegistrationSG.input_name,
            mode=StartMode.RESET_STACK,
            data=start_data
        )
        return False
    
    if result.needs_name:
        await dialog_manager.start(
            UserRegistrationSG.input_name,
            mode=StartMode.RESET_STACK,
            data=start_data
        )
        return False
    
    if result.needs_group:
        await dialog_manager.start(
            UserRegistrationSG.select_group,
            mode=StartMode.RESET_STACK,
            data=start_data
        )
        return False
    
    await user_service.update_user_info(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        last_name=message.from_user.last_name,
    )
    return True


@router.message(CommandStart(deep_link=True))
async def start_with_deeplink(
    message: Message,
    command: CommandObject,
    dialog_manager: DialogManager,
    user_service: FromDishka[UserService],
    test_service: FromDishka[TestService],
) -> None:
    assert message.from_user is not None
    
    deeplink = command.args
    logger.info(
        "Deeplink start: user_id=%d, username=%s, deeplink=%s",
        message.from_user.id,
        message.from_user.username,
        deeplink,
    )
    
    if not deeplink:
        await start_handler(message, user_service, dialog_manager)
        return
    
    test_id = test_service.decode_test_hash(deeplink)
    if test_id is None:
        logger.warning("Invalid deeplink: user_id=%d, deeplink=%s", message.from_user.id, deeplink)
        await message.answer("❌ Неверная ссылка на тест")
        await start_handler(message, user_service, dialog_manager)
        return
    
    is_registered = await ensure_user_registered(
        user_service, message, dialog_manager, pending_test_id=test_id
    )
    
    if not is_registered:
        return
    
    validation = await test_service.validate_test(test_id, message.from_user.id)
    
    if not validation.is_valid:
        logger.info(
            "Test validation failed: user_id=%d, test_id=%d, error=%s",
            message.from_user.id,
            test_id,
            validation.error,
        )
        await dialog_manager.start(
            UserDeeplinkSG.test_preview,
            mode=StartMode.RESET_STACK,
            data={"test_id": test_id, "error": validation.error}
        )
        return
    
    logger.info("User starting test via deeplink: user_id=%d, test_id=%d", message.from_user.id, test_id)
    await dialog_manager.start(
        UserDeeplinkSG.test_preview,
        mode=StartMode.RESET_STACK,
        data={"test_id": test_id}
    )


@router.message(CommandStart())
async def start_handler(
    message: Message,
    dialog_manager: DialogManager,
    user_service: FromDishka[UserService],
) -> None:
    assert message.from_user is not None
    logger.info(
        "Start command: user_id=%d, username=%s",
        message.from_user.id,
        message.from_user.username,
    )
    
    is_registered = await ensure_user_registered(
        user_service, message, dialog_manager
    )
    
    if is_registered:
        await dialog_manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)


@router.message(Command("admin"))
async def admin_command(_message: Message, dialog_manager: DialogManager) -> None:
    assert _message.from_user is not None
    logger.info("Admin panel access: user_id=%d", _message.from_user.id)
    await dialog_manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


@router.message(Command("creator"))
async def creator_command(_message: Message, dialog_manager: DialogManager) -> None:
    assert _message.from_user is not None
    logger.info("Creator panel access: user_id=%d", _message.from_user.id)
    await dialog_manager.start(CreatorMenuSG.main, mode=StartMode.RESET_STACK)


@router.error()
async def dialog_error_handler(event: ErrorEvent, dialog_manager: DialogManager) -> None:
    if isinstance(event.exception, (UnknownIntent, OutdatedIntent)):
        logger.debug("Dialog intent error, resetting to main menu: %s", type(event.exception).__name__)
        await dialog_manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)
    else:
        logger.exception("Unhandled error in dialog: %s", event.exception)
