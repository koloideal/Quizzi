from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Button, Column
from aiogram_dialog.widgets.text import Const

from trudex.application.bot.user_dialogs.states import UserMenuSG


async def on_tests_clicked(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await _callback.answer("Доступные тесты")


async def on_results_clicked(_callback: CallbackQuery, _button: Button, _manager: DialogManager) -> None:
    await _callback.answer("Мои результаты")


user_menu_dialog = Dialog(
    Window(
        Const("📚 <b>Главное меню</b>\n\nВыберите раздел:"),
        Column(
            Button(Const("📝 Доступные тесты"), id="tests", on_click=on_tests_clicked),
            Button(Const("📊 Мои результаты"), id="results", on_click=on_results_clicked),
        ),
        state=UserMenuSG.main,
    ),
)
