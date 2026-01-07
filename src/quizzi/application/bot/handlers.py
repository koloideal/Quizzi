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
from quizzi.infrastructure.database.dao.group import GroupDAO
from quizzi.infrastructure.database.dao.test import TestDAO
from quizzi.infrastructure.database.dao.user import UserDAO
from quizzi.infrastructure.utils.config import Config
from quizzi.infrastructure.utils.test_id_to_hash import decode_id
from quizzi.infrastructure.utils.timezone import now_msk_naive

router = Router()
logger = logging.getLogger(__name__)


async def ensure_user_registered(
    user_dao: UserDAO,
    group_dao: GroupDAO,
    message: Message,
    dialog_manager: DialogManager,
    pending_test_id: int | None = None,
) -> bool:
    assert message.from_user is not None
    
    existing_user = await user_dao.get_by_id(message.from_user.id)
    groups = await group_dao.get_all()
    has_groups = len(groups) > 0
    
    start_data = {"user_id": message.from_user.id, "has_groups": has_groups}
    if pending_test_id:
        start_data["pending_test_id"] = pending_test_id
    
    if existing_user is None:
        await user_dao.create(
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
    
    needs_name = existing_user.name is None
    needs_group = has_groups and existing_user.group is None
    
    if needs_name:
        await dialog_manager.start(
            UserRegistrationSG.input_name,
            mode=StartMode.RESET_STACK,
            data=start_data
        )
        return False
    
    if needs_group:
        await dialog_manager.start(
            UserRegistrationSG.select_group,
            mode=StartMode.RESET_STACK,
            data=start_data
        )
        return False
    
    await user_dao.upsert(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        last_name=message.from_user.last_name,
    )
    return True


async def validate_deeplink_test(
    test_dao: TestDAO,
    user_dao: UserDAO,
    test_id: int,
    user_id: int,
) -> tuple[bool, str]:
    test = await test_dao.get_by_id(test_id)
    
    if not test:
        return False, "❌ Тест не найден"
    
    if not test.is_active:
        return False, "❌ Тест деактивирован"
    
    if test.expires_at and test.expires_at < now_msk_naive():
        return False, "❌ Срок действия теста истек"
    
    user = await user_dao.get_by_id(user_id)
    if test.for_group and user and user.group != test.for_group:
        return False, f"❌ Тест доступен только для группы {test.for_group}"
    
    return True, ""


@router.message(CommandStart(deep_link=True))
async def start_with_deeplink(
    message: Message,
    command: CommandObject,
    dialog_manager: DialogManager,
    user_dao: FromDishka[UserDAO],
    group_dao: FromDishka[GroupDAO],
    test_dao: FromDishka[TestDAO],
    config: FromDishka[Config],
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
        await start_handler(message, user_dao, group_dao, dialog_manager)
        return
    
    try:
        test_id = decode_id(deeplink, config.security.encode_key)
    except (ValueError, IndexError):
        logger.warning("Invalid deeplink: user_id=%d, deeplink=%s", message.from_user.id, deeplink)
        await message.answer("❌ Неверная ссылка на тест")
        await start_handler(message, user_dao, group_dao, dialog_manager)
        return
    
    is_registered = await ensure_user_registered(
        user_dao, group_dao, message, dialog_manager, pending_test_id=test_id
    )
    
    if not is_registered:
        return
    
    is_valid, error = await validate_deeplink_test(
        test_dao, user_dao, test_id, message.from_user.id
    )
    
    if not is_valid:
        logger.info(
            "Test validation failed: user_id=%d, test_id=%d, error=%s",
            message.from_user.id,
            test_id,
            error,
        )
        await dialog_manager.start(
            UserDeeplinkSG.test_preview,
            mode=StartMode.RESET_STACK,
            data={"test_id": test_id, "error": error}
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
    user_dao: FromDishka[UserDAO],
    group_dao: FromDishka[GroupDAO],
) -> None:
    assert message.from_user is not None
    logger.info(
        "Start command: user_id=%d, username=%s",
        message.from_user.id,
        message.from_user.username,
    )
    
    is_registered = await ensure_user_registered(
        user_dao, group_dao, message, dialog_manager
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
