from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Const

from trudex.application.bot.admin_dialogs.states import (AdminBroadcastSG,
                                                         AdminGroupsSG,
                                                         AdminMenuSG,
                                                         AdminTemplatesSG,
                                                         AdminTestsSG,
                                                         AdminUsersSG)


async def on_tests_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(AdminTestsSG.tests_list, mode=StartMode.RESET_STACK)


async def on_users_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(AdminUsersSG.users_list, mode=StartMode.RESET_STACK)


async def on_groups_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(AdminGroupsSG.groups_list, mode=StartMode.RESET_STACK)


async def on_broadcast_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(AdminBroadcastSG.broadcast_input, mode=StartMode.RESET_STACK)


async def on_templates_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager) -> None:
    await manager.start(AdminTemplatesSG.main, mode=StartMode.RESET_STACK)


admin_menu_dialog = Dialog(
    Window(
        Const("🔧 <b>Админ-панель</b>\n\nВыберите раздел:"),
        Column(
            Button(Const("📝 Тесты"), id="tests", on_click=on_tests_clicked),
            Button(Const("👥 Пользователи"), id="users", on_click=on_users_clicked),
            Button(Const("🎓 Группы"), id="groups", on_click=on_groups_clicked),
            Button(Const("📢 Рассылка"), id="broadcast", on_click=on_broadcast_clicked),
            Button(Const("📦 Шаблоны тестов"), id="templates", on_click=on_templates_clicked),
        ),
        state=AdminMenuSG.main,
    ),
)
