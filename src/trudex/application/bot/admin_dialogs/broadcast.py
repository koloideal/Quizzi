from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.text import Const
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.admin_dialogs.states import (AdminBroadcastSG,
                                                         AdminMenuSG)
from trudex.infrastructure.database.dao.user import UserDAO
from trudex.infrastructure.utils.broadcast import broadcast_message


async def on_broadcast_input(message: Message, _widget: MessageInput, manager: DialogManager):
    manager.dialog_data["broadcast_message_id"] = message.message_id
    manager.dialog_data["broadcast_chat_id"] = message.chat.id
    await manager.switch_to(AdminBroadcastSG.broadcast_confirm)


@inject
async def on_broadcast_confirm(_callback: CallbackQuery, _button: Button, manager: DialogManager, user_dao: FromDishka[UserDAO]):
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
    
    stats = await broadcast_message(bot, message_id, chat_id, user_dao)
    
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


async def on_back_to_main(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


broadcast_dialog = Dialog(
    Window(
        Const("<b>📢 Рассылка</b>\n\nОтправьте сообщение, которое хотите разослать всем пользователям:"),
        MessageInput(on_broadcast_input),
        Button(Const("◀️ Отмена"), id="back", on_click=on_back_to_main),
        state=AdminBroadcastSG.broadcast_input,
    ),
    Window(
        Const("<b>⚠️ Подтверждение рассылки</b>\n\nВы уверены, что хотите отправить это сообщение всем пользователям?"),
        Row(
            Button(Const("✅ Да"), id="broadcast_confirm", on_click=on_broadcast_confirm),
            Button(Const("❌ Нет"), id="broadcast_cancel", on_click=on_broadcast_cancel),
        ),
        state=AdminBroadcastSG.broadcast_confirm,
    ),
)
