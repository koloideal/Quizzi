from typing import TYPE_CHECKING

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Multiselect, Row, ScrollingGroup
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from quizzi.application.bot.shared_dialogs.states import SharedBroadcastSG
from quizzi.infrastructure.database.dao.group import GroupDAO
from quizzi.service.broadcast import BroadcastService

from aiogram_dialog.widgets.kbd.select import ManagedMultiselect


@inject
async def get_groups_data(group_dao: FromDishka[GroupDAO], **_kwargs):
    groups = await group_dao.get_all()
    return {
        "groups": [(str(g.id), str(g.number)) for g in groups],
        "has_groups": len(groups) > 0,
    }


async def on_group_selected(
    _callback: CallbackQuery,
    _widget,
    manager: DialogManager,
    _item_id: str,
):
    pass


@inject
async def on_send_to_selected(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    group_dao: FromDishka[GroupDAO],
):
    multiselect: ManagedMultiselect[str] = manager.find("groups_multiselect")  # type: ignore[assignment]
    selected_ids = multiselect.get_checked()
    
    if not selected_ids:
        await _callback.answer("❌ Выберите хотя бы одну группу", show_alert=True)
        return
    
    groups = await group_dao.get_all()
    id_to_number = {str(g.id): g.number for g in groups}
    selected_numbers = [id_to_number[gid] for gid in selected_ids if gid in id_to_number]
    
    manager.dialog_data["selected_group_numbers"] = selected_numbers
    manager.dialog_data["broadcast_to_all"] = False
    await manager.switch_to(SharedBroadcastSG.broadcast_input)


async def on_send_to_all(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    manager.dialog_data["selected_group_numbers"] = None
    manager.dialog_data["broadcast_to_all"] = True
    await manager.switch_to(SharedBroadcastSG.broadcast_input)


async def on_broadcast_input(message: Message, _widget: MessageInput, manager: DialogManager):
    manager.dialog_data["broadcast_message_id"] = message.message_id
    manager.dialog_data["broadcast_chat_id"] = message.chat.id
    await manager.switch_to(SharedBroadcastSG.broadcast_confirm)


async def get_confirm_data(dialog_manager: DialogManager, **_kwargs):
    broadcast_to_all = dialog_manager.dialog_data.get("broadcast_to_all", False)
    selected_numbers = dialog_manager.dialog_data.get("selected_group_numbers", [])
    
    if broadcast_to_all:
        target_text = "всем пользователям"
    else:
        groups_str = ", ".join(str(n) for n in selected_numbers)
        target_text = f"группам: {groups_str}"
    
    return {"target_text": target_text}


@inject
async def on_broadcast_confirm(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    broadcast_service: FromDishka[BroadcastService],
):
    message_id = manager.dialog_data.get("broadcast_message_id")
    chat_id = manager.dialog_data.get("broadcast_chat_id")
    
    if not message_id or not chat_id or not _callback.message:
        await _callback.answer("Ошибка: сообщение не найдено")
        return
    
    await _callback.message.answer("⏳ Рассылка началась...")
    
    bot = _callback.bot
    if not bot:
        await _callback.answer("Ошибка: бот не найден")
        return
    
    group_numbers = manager.dialog_data.get("selected_group_numbers")
    stats = await broadcast_service.broadcast_message(bot, message_id, chat_id, group_numbers)
    
    stats_text = (
        f"✅ <b>Рассылка завершена</b>\n\n"
        f"Всего пользователей: {stats.total}\n"
        f"Успешно отправлено: {stats.success}\n"
        f"Не удалось отправить: {stats.failed}"
    )
    
    await _callback.message.answer(stats_text)
    await manager.done()


async def on_broadcast_cancel(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await _callback.answer("Рассылка отменена")
    await manager.done()


async def on_back_to_groups(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(SharedBroadcastSG.select_groups)


async def on_back_to_main(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.done()


shared_broadcast_dialog = Dialog(
    Window(
        Const("<b>📢 Рассылка</b>\n\n<b>Выберите группы для рассылки:</b>"),
        ScrollingGroup(
            Multiselect(
                Format("✅ {item[1]}"),
                Format("⬜ {item[1]}"),
                id="groups_multiselect",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_selected,
            ),
            id="groups_scroll",
            width=2,
            height=5,
            when="has_groups",
        ),
        Column(
            Button(Const("📤 Отправить выбранным"), id="send_selected", on_click=on_send_to_selected, when="has_groups"),
            Button(Const("📢 Отправить всем"), id="send_all", on_click=on_send_to_all),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_main),
        ),
        state=SharedBroadcastSG.select_groups,
        getter=get_groups_data,
    ),
    Window(
        Const("<b>📢 Рассылка</b>\n\nОтправьте сообщение, которое хотите разослать:"),
        MessageInput(on_broadcast_input),
        Button(Const("◀️ Назад"), id="back", on_click=on_back_to_groups),
        state=SharedBroadcastSG.broadcast_input,
    ),
    Window(
        Format("<b>⚠️ Подтверждение рассылки</b>\n\nВы уверены, что хотите отправить это сообщение {target_text}?"),
        Row(
            Button(Const("✅ Да"), id="broadcast_confirm", on_click=on_broadcast_confirm),
            Button(Const("❌ Нет"), id="broadcast_cancel", on_click=on_broadcast_cancel),
        ),
        state=SharedBroadcastSG.broadcast_confirm,
        getter=get_confirm_data,
    ),
)
