from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram import CONTAINER_NAME
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.admin_dialogs.states import AdminUsersSG, AdminMenuSG
from trudex.infrastructure.database.dao.user import UserDAO


@inject
async def get_users_data(user_dao: FromDishka[UserDAO], **_kwargs):
    users = await user_dao.get_all()
    
    return {
        "users": [
            (f"{u.first_name} (@{u.username or 'нет'})", u.id)
            for u in users
        ],
        "count": len(users),
    }


@inject
async def get_user_detail_data(dialog_manager: DialogManager, user_dao: FromDishka[UserDAO], **_kwargs):
    user_id = dialog_manager.dialog_data.get("selected_user_id")
    if not user_id:
        return {"user_info": "Пользователь не выбран"}
    
    user = await user_dao.get_by_id(user_id)
    if not user:
        return {"user_info": "Пользователь не найден"}
    
    username_str = f"@{user.username}" if user.username else "—"
    last_name_str = user.last_name or "—"
    group_str = str(user.group) if user.group else "—"
    admin_status = "✅ Да" if user.is_admin else "❌ Нет"
    
    user_info = (
        f"<b>👤 Информация о пользователе</b>\n\n"
        f"<b>ID:</b> <code>{user.id}</code>\n"
        f"<b>Имя:</b> {user.first_name}\n"
        f"<b>Фамилия:</b> {last_name_str}\n"
        f"<b>Username:</b> {username_str}\n"
        f"<b>Группа:</b> {group_str}\n"
        f"<b>Администратор:</b> {admin_status}"
    )
    
    return {"user_info": user_info}


async def on_user_selected(_callback: CallbackQuery, _widget: Select, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_user_id"] = int(item_id)
    await manager.switch_to(AdminUsersSG.user_detail)


async def on_input_mode(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(AdminUsersSG.users_input)


async def on_user_input(message: Message, _widget: MessageInput, manager: DialogManager):
    container = manager.middleware_data[CONTAINER_NAME]
    user_dao = await container.get(UserDAO)
    
    text = (message.text or "").strip()
    
    user = None
    if text.startswith("@"):
        username = text[1:]
        all_users = await user_dao.get_all()
        user = next((u for u in all_users if u.username == username), None)
    elif text.isdigit():
        user = await user_dao.get_by_id(int(text))
    
    if not user:
        await message.answer("❌ Пользователь не найден в базе данных.")
        return
    
    manager.dialog_data["selected_user_id"] = user.id
    await manager.switch_to(AdminUsersSG.user_detail)


async def on_back_to_main(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(AdminMenuSG.main, mode=StartMode.RESET_STACK)


users_dialog = Dialog(
    Window(
        Format("<b>👥 Пользователи</b>\n\nВсего: {count}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="user_select",
                item_id_getter=lambda x: x[1],
                items="users",
                on_click=on_user_selected,
            ),
            id="users_scroll",
            width=1,
            height=7,
        ),
        Column(
            Button(Const("✏️ Ввести ID/Username"), id="input_mode", on_click=on_input_mode),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_main),
        ),
        state=AdminUsersSG.users_list,
        getter=get_users_data,
    ),
    Window(
        Const("<b>Введите ID или @username пользователя:</b>"),
        MessageInput(on_user_input),
        SwitchTo(Const("◀️ Назад"), id="back_to_list", state=AdminUsersSG.users_list),
        state=AdminUsersSG.users_input,
    ),
    Window(
        Format("{user_info}"),
        SwitchTo(Const("◀️ Назад"), id="back_to_list", state=AdminUsersSG.users_list),
        state=AdminUsersSG.user_detail,
        getter=get_user_detail_data,
    ),
)
