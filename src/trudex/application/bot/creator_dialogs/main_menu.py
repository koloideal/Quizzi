from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Const

from trudex.application.bot.creator_dialogs.states import CreatorMenuSG, CreatorUsersSG
from trudex.application.bot.shared_dialogs.states import (
    SharedBroadcastSG,
    SharedGroupsSG,
    SharedTemplatesSG,
    SharedTestsSG,
)


async def on_tests_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(SharedTestsSG.tests_list)


async def on_users_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(CreatorUsersSG.users_list)


async def on_groups_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(SharedGroupsSG.groups_list)


async def on_broadcast_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(SharedBroadcastSG.broadcast_input)


async def on_templates_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(SharedTemplatesSG.main)


creator_menu_dialog = Dialog(
    Window(
        Const("👑 <b>Панель создателя</b>\n\nВыберите раздел:"),
        Column(
            Button(Const("📝 Тесты"), id="tests", on_click=on_tests_clicked),
            Button(Const("👥 Пользователи"), id="users", on_click=on_users_clicked),
            Button(Const("🎓 Группы"), id="groups", on_click=on_groups_clicked),
            Button(Const("📢 Рассылка"), id="broadcast", on_click=on_broadcast_clicked),
            Button(Const("📦 Шаблоны тестов"), id="templates", on_click=on_templates_clicked),
        ),
        state=CreatorMenuSG.main,
    ),
)
