from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (Button, Column, Row, ScrollingGroup,
                                        Select)
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.admin_dialogs.states import (AdminGroupsSG,
                                                         AdminMenuSG)
from trudex.infrastructure.database.dao.group import GroupDAO


async def on_group_click(_callback: CallbackQuery, _widget, _manager: DialogManager, _item_id: str):
    await _callback.answer("ℹ️ Для удаления используйте кнопку 'Удалить группу'")


@inject
async def get_groups_data(dialog_manager: DialogManager, group_dao: FromDishka[GroupDAO], **_kwargs):
    groups = await group_dao.get_all()
    
    success_message = dialog_manager.dialog_data.pop("success_message", None)
    
    message_text = "<b>👥 Управление группами</b>\n\n"
    if success_message:
        message_text += f"{success_message}\n\n"
    message_text += f"📊 <b>Всего групп:</b> {len(groups)}\n\n<b>Список групп:</b>"
    
    return {
        "groups": [(str(g.id), str(g.number)) for g in groups],
        "groups_count": len(groups),
        "message_text": message_text,
    }


async def on_add_group(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(AdminGroupsSG.add_group_input_number)


async def on_delete_group(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(AdminGroupsSG.delete_groups_list)


async def on_back_to_menu(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


@inject
async def on_group_number_input(message: Message, _widget: MessageInput, manager: DialogManager, group_dao: FromDishka[GroupDAO]):
    if not message.text:
        await message.answer("❌ Номер группы не может быть пустым")
        return
    
    number_str = message.text.strip()
    
    if not number_str.isdigit():
        await message.answer("❌ Номер группы должен содержать только цифры")
        return
    
    number = int(number_str)
    
    if number < 1000 or number > 9999:
        await message.answer("❌ Номер группы должен быть четырехзначным (1000-9999)")
        return
    
    existing = await group_dao.get_by_number(number)
    if existing:
        await message.answer(f"❌ Группа с номером {number} уже существует")
        return
    
    try:
        await group_dao.create(number=number)
        manager.dialog_data["success_message"] = f"✅ Группа {number} создана"
    except Exception as e:
        await message.answer(f"❌ Ошибка создания группы: {e}")
        return
    
    await manager.switch_to(AdminGroupsSG.groups_list)


async def on_cancel_add(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(AdminGroupsSG.groups_list)


@inject
async def get_delete_groups_data(dialog_manager: DialogManager, group_dao: FromDishka[GroupDAO], **_kwargs):
    groups = await group_dao.get_all()
    
    return {
        "groups": [(str(g.id), f"{g.number}") for g in groups],
        "groups_count": len(groups),
    }


@inject
async def on_select_group_to_delete(_callback: CallbackQuery, _widget, manager: DialogManager, item_id: str, group_dao: FromDishka[GroupDAO]):
    group = await group_dao.get_by_id(int(item_id))
    if not group:
        await _callback.answer("❌ Группа не найдена", show_alert=True)
        return
    
    manager.dialog_data["delete_group_id"] = group.id
    manager.dialog_data["delete_group_number"] = group.number
    await manager.switch_to(AdminGroupsSG.delete_confirm)


async def get_delete_confirm_data(dialog_manager: DialogManager, **_kwargs):
    number = dialog_manager.dialog_data.get("delete_group_number", "")
    
    return {
        "group_info": str(number)
    }


@inject
async def on_confirm_delete(_callback: CallbackQuery, _button: Button, manager: DialogManager, group_dao: FromDishka[GroupDAO]):
    group_id = manager.dialog_data.get("delete_group_id")

    assert isinstance(group_id, int)
    
    await group_dao.delete(group_id)
    
    manager.dialog_data["success_message"] = "✅ Группа удалена"
    await manager.switch_to(AdminGroupsSG.groups_list)


async def on_cancel_delete(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(AdminGroupsSG.delete_groups_list)


groups_dialog = Dialog(
    Window(
        Format("{message_text}"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="groups",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_click,
            ),
            id="groups_scroll",
            width=2,
            height=7,
        ),
        Column(
            Button(Const("➕ Добавить группу"), id="add", on_click=on_add_group),
            Button(Const("🗑 Удалить группу"), id="delete", on_click=on_delete_group),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_menu),
        ),
        state=AdminGroupsSG.groups_list,
        getter=get_groups_data,
    ),
    Window(
        Const("<b>➕ Добавление группы</b>\n\n🔢 <b>Введите номер группы</b> (четырехзначное число 1000-9999):"),
        MessageInput(on_group_number_input),
        Button(Const("◀️ Отмена"), id="cancel", on_click=on_cancel_add),
        state=AdminGroupsSG.add_group_input_number,
    ),
    Window(
        Format("<b>🗑 Удаление группы</b>\n\n<b>Выберите группу для удаления:</b>\n\n📊 <b>Всего групп:</b> {groups_count}"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="delete_groups",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_select_group_to_delete,
            ),
            id="delete_groups_scroll",
            width=2,
            height=7,
        ),
        Button(Const("◀️ Назад"), id="back", on_click=on_cancel_add),
        state=AdminGroupsSG.delete_groups_list,
        getter=get_delete_groups_data,
    ),
    Window(
        Format("<b>⚠️ Подтверждение удаления</b>\n\n<b>Точно хотите удалить группу?</b>\n\n👥 {group_info}"),
        Row(
            Button(Const("✅ Да, удалить"), id="confirm", on_click=on_confirm_delete),
            Button(Const("❌ Отмена"), id="cancel", on_click=on_cancel_delete),
        ),
        state=AdminGroupsSG.delete_confirm,
        getter=get_delete_confirm_data,
    ),
)
