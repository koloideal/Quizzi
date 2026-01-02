from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, Window, StartMode
from aiogram_dialog.widgets.kbd import Button, Column, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.creator_dialogs.states import CreatorTestsSG, CreatorMenuSG
from trudex.infrastructure.database.dao.test import TestDAO


@inject
async def get_tests_data(test_dao: FromDishka[TestDAO], **_kwargs):
    tests = await test_dao.get_all()
    
    return {
        "tests": [
            (t.title, t.id)
            for t in tests
        ],
        "count": len(tests),
    }


async def on_test_selected(_callback: CallbackQuery, _widget: Select, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_test_id"] = int(item_id)
    await _callback.answer("Тест выбран")


async def on_add_test_clicked(_callback: CallbackQuery, _button: Button, _manager: DialogManager):
    await _callback.answer("Добавление теста")


async def on_back_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(CreatorMenuSG.main, mode=StartMode.RESET_STACK)


tests_dialog = Dialog(
    Window(
        Format("<b>📝 Тесты</b>\n\nВсего: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="test_select",
                item_id_getter=lambda x: x[1],
                items="tests",
                on_click=on_test_selected,
            ),
            id="tests_scroll",
            width=1,
            height=7,
        ),
        Column(
            Button(Const("➕ Добавить тест"), id="add_test", on_click=on_add_test_clicked),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_clicked),
        ),
        state=CreatorTestsSG.tests_list,
        getter=get_tests_data,
    ),
)
