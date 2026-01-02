from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.user_dialogs.states import (UserMenuSG,
                                                        UserRegistrationSG)
from trudex.infrastructure.database.dao.group import GroupDAO
from trudex.infrastructure.database.dao.user import UserDAO


@inject
async def get_groups_for_registration(dialog_manager: DialogManager, group_dao: FromDishka[GroupDAO], **_kwargs):
    groups = await group_dao.get_all()
    
    return {
        "groups": [(str(g.number), str(g.number)) for g in groups],
    }


@inject
async def on_group_selected(_callback: CallbackQuery, _widget, manager: DialogManager, item_id: str, user_dao: FromDishka[UserDAO]):
    user_id = manager.start_data.get("user_id")
    
    await user_dao.update(user_id=user_id, group=int(item_id))
    
    await _callback.answer("✅ Группа выбрана! Вы можете изменить её через 24 часа", show_alert=True)
    await manager.start(UserMenuSG.main, mode=StartMode.RESET_STACK)


registration_dialog = Dialog(
    Window(
        Const(
            "<b>👋 Добро пожаловать!</b>\n\n"
            "🎓 <b>Выберите вашу группу:</b>\n\n"
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
