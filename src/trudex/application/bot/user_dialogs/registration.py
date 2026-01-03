from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.user_dialogs.states import (
    UserDeeplinkSG,
    UserMenuSG,
    UserRegistrationSG,
)
from trudex.infrastructure.database.dao.group import GroupDAO
from trudex.infrastructure.database.dao.user import UserDAO


@inject
async def on_name_input(
    message: Message,
    _widget: MessageInput,
    manager: DialogManager,
    user_dao: FromDishka[UserDAO],
):
    assert message.from_user is not None
    if not message.text:
        await message.answer("❌ Имя и фамилия не могут быть пустыми")
        return
    
    name = message.text.strip()
    if not name:
        await message.answer("❌ Имя и фамилия не могут быть пустыми")
        return
    
    if len(name) > 128:
        await message.answer("❌ Имя и фамилия слишком длинные (максимум 128 символов)")
        return
    
    start_data = manager.start_data or {}
    assert isinstance(start_data, dict)
    user_id = start_data.get("user_id")
    if user_id:
        await user_dao.update(user_id=user_id, name=name)
    
    manager.dialog_data["name"] = name
    await manager.switch_to(UserRegistrationSG.select_group)


@inject
async def get_groups_for_registration(group_dao: FromDishka[GroupDAO], **_kwargs):
    groups = await group_dao.get_all()
    
    return {
        "groups": [(str(g.number), str(g.number)) for g in groups],
    }


@inject
async def on_group_selected(
    _callback: CallbackQuery,
    _widget,
    manager: DialogManager,
    item_id: str,
    user_dao: FromDishka[UserDAO],
):
    assert _callback.from_user is not None
    start_data = manager.start_data or {}
    assert isinstance(start_data, dict)
    user_id = start_data.get("user_id")
    pending_test_id = start_data.get("pending_test_id")
    
    if user_id:
        await user_dao.update(user_id=user_id, group=int(item_id))
    
    if pending_test_id:
        await manager.start(
            UserDeeplinkSG.test_preview,
            mode=StartMode.RESET_STACK,
            data={"test_id": pending_test_id}
        )
    else:
        await manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)


registration_dialog = Dialog(
    Window(
        Const(
            "<b>👋 Добро пожаловать!</b>\n\n"
            "✏️ <b>Введите ваше имя и фамилию:</b>\n\n"
            "⚠️ <b>Внимание:</b> Изменить данные можно будет только через 24 часа!"
        ),
        MessageInput(on_name_input),
        state=UserRegistrationSG.input_name,
    ),
    Window(
        Const(
            "<b>🎓 Выберите вашу группу:</b>\n\n"
            "⚠️ <b>Внимание:</b> Изменить группу можно будет только через 24 часа!"
        ),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="groups",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_selected,
            ),
            id="groups_scroll",
            width=2,
            height=7,
        ),
        state=UserRegistrationSG.select_group,
        getter=get_groups_for_registration,
    ),
)
