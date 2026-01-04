from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.admin_dialogs.states import AdminUsersSG
from trudex.infrastructure.database.dao.user import UserDAO


@inject
async def get_users_data(user_dao: FromDishka[UserDAO], **_kwargs):
    users = await user_dao.get_all()
    users_sorted = sorted(users, key=lambda u: u.created_at or u.id, reverse=True)
    
    return {
        "users": [
            (f"{'👑 ' if u.is_admin else ''}{u.name or u.first_name} (@{u.username or 'нет'})", u.id)
            for u in users_sorted
        ],
        "count": len(users_sorted),
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
    name_str = user.name or "—"
    group_str = str(user.group) if user.group else "—"
    admin_status = "✅ Да" if user.is_admin else "❌ Нет"
    
    user_info = (
        f"<b>👤 Информация о пользователе</b>\n\n"
        f"<b>ID:</b> <code>{user.id}</code>\n"
        f"<b>Ник:</b> {user.first_name}\n"
        f"<b>Имя и фамилия:</b> {name_str}\n"
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


@inject
async def on_user_input(message: Message, _widget: MessageInput, manager: DialogManager, user_dao: FromDishka[UserDAO]):
    text = (message.text or "").strip()
    
    user = None
    if text.startswith("@"):
        username = text[1:]
        user = await user_dao.get_by_username(username)
    elif text.isdigit():
        user = await user_dao.get_by_id(int(text))
    
    if not user:
        await message.answer("❌ Пользователь не найден в базе данных.")
        return
    
    manager.dialog_data["selected_user_id"] = user.id
    await manager.switch_to(AdminUsersSG.user_detail)


async def on_back_to_main(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.done()


admin_users_dialog = Dialog(
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
