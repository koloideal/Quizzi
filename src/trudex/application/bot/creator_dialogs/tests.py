from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import (Button, Column, Row, ScrollingGroup,
                                        Select)
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.creator_dialogs.states import (CreateTestSG,
                                                           CreatorMenuSG,
                                                           CreatorTestsSG)
from trudex.infrastructure.database.dao.test import TestDAO
from trudex.infrastructure.database.repo.test import TestRepository


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
    await manager.switch_to(CreatorTestsSG.test_detail)


@inject
async def get_test_detail(test_dao: FromDishka[TestDAO], test_repo: FromDishka[TestRepository], dialog_manager: DialogManager, **_kwargs):
    test_id = dialog_manager.dialog_data.get("selected_test_id")
    
    if not test_id:
        return {
            "test_info": "Тест не найден",
            "is_active": False,
            "button_text": "◀️ Назад",
        }
    
    test = await test_dao.get_by_id(test_id)
    questions_count = await test_repo.count_questions_in_test(test_id)
    
    if not test:
        return {
            "test_info": "Тест не найден",
            "is_active": False,
            "button_text": "◀️ Назад",
        }
    
    status = "🟢 Активен" if test.is_active else "🔴 Деактивирован"
    password_str = f"🔒 {test.password}" if test.password else "🔓 Без пароля"
    expires_str = test.expires_at.strftime("%d.%m.%Y %H:%M") if test.expires_at else "♾️ Без срока"
    group_str = f"🎓 Группа {test.for_group}" if test.for_group else "👥 Для всех"
    
    test_info = (
        f"<b>📝 Информация о тесте</b>\n\n"
        f"<b>Название:</b> {test.title}\n"
        f"<b>Описание:</b> {test.description or '—'}\n\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Вопросов:</b> {questions_count}\n"
        f"{password_str}\n"
        f"{expires_str}\n"
        f"{group_str}\n\n"
        f"<b>Создан:</b> {test.created_at.strftime('%d.%m.%Y %H:%M') if test.created_at else '—'}"
    )
    
    button_text = "🔴 Деактивировать" if test.is_active else "🟢 Активировать"
    
    return {
        "test_info": test_info,
        "is_active": test.is_active,
        "button_text": button_text,
    }


@inject
async def on_toggle_active(_callback: CallbackQuery, _button: Button, manager: DialogManager, test_dao: FromDishka[TestDAO]):
    test_id = manager.dialog_data.get("selected_test_id")
    if not test_id:
        await _callback.answer("❌ Тест не найден")
        return
    
    test = await test_dao.get_by_id(test_id)
    
    if test:
        await test_dao.update(test_id, is_active=not test.is_active)
        action = "деактивирован" if test.is_active else "активирован"
        await _callback.answer(f"✅ Тест {action}")
        await manager.switch_to(CreatorTestsSG.test_detail)


async def on_back_to_list(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(CreatorTestsSG.tests_list)


async def on_add_test_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(CreateTestSG.input_title, mode=StartMode.RESET_STACK)


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
    Window(
        Format("{test_info}"),
        Row(
            Button(
                Format("{button_text}"),
                id="toggle_active",
                on_click=on_toggle_active
            ),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_list),
        ),
        state=CreatorTestsSG.test_detail,
        getter=get_test_detail,
    ),
)
