import asyncio

from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (Button, Column, Row, ScrollingGroup,
                                        Select, SwitchTo)
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from trudex.application.bot.creator_dialogs.states import (CreatorMenuSG,
                                                           CreatorUsersSG)
from trudex.infrastructure.database.dao.user import UserDAO
from trudex.infrastructure.database.repo.user import UserRepository
from trudex.infrastructure.utils.bot_commands import setup_bot_commands
from trudex.infrastructure.utils.config import Config


@inject
async def get_users_data(user_dao: FromDishka[UserDAO], **_kwargs):
    users = await user_dao.get_all()
    users_sorted = sorted(users, key=lambda u: u.created_at, reverse=True)
    
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
        return {"user_info": "Пользователь не выбран", "is_admin": True, "show_make_admin": False}
    
    user = await user_dao.get_by_id(user_id)
    if not user:
        return {"user_info": "Пользователь не найден", "is_admin": True, "show_make_admin": False}
    
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
    
    return {
        "user_info": user_info,
        "is_admin": user.is_admin,
        "show_make_admin": not user.is_admin,
        "show_remove_admin": user.is_admin,
    }


@inject
async def get_confirm_data(dialog_manager: DialogManager, user_dao: FromDishka[UserDAO], **_kwargs):
    user_id = dialog_manager.dialog_data.get("selected_user_id")
    if not user_id:
        return {"user_info": "Пользователь не выбран"}
    
    user = await user_dao.get_by_id(user_id)
    if not user:
        return {"user_info": "Пользователь не найден"}
    
    username_str = f"@{user.username}" if user.username else "—"
    name_str = user.name or f"{user.first_name} {user.last_name or ''}".strip()
    return {
        "user_info": f"<b>{name_str}</b>\n{username_str}\nID: <code>{user.id}</code>"
    }


async def on_user_selected(_callback: CallbackQuery, _widget: Select, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_user_id"] = int(item_id)
    await manager.switch_to(CreatorUsersSG.user_detail)


async def on_input_mode(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(CreatorUsersSG.users_input)


@inject
async def on_user_input(message: Message, _widget: MessageInput, manager: DialogManager, user_dao: FromDishka[UserDAO]):
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
    await manager.switch_to(CreatorUsersSG.user_detail)


async def on_make_admin_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(CreatorUsersSG.make_admin_confirm)


async def on_remove_admin_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(CreatorUsersSG.remove_admin_confirm)


@inject
async def on_confirm_yes(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    user_dao: FromDishka[UserDAO],
    user_repo: FromDishka[UserRepository],
    bot: FromDishka[Bot],
    config: FromDishka[Config],
):
    user_id = manager.dialog_data.get("selected_user_id")
    if not user_id:
        await _callback.answer("Ошибка: пользователь не выбран")
        return
    
    await user_dao.update(user_id=user_id, is_admin=True)
    asyncio.create_task(setup_bot_commands(bot, config, user_repo))
    await _callback.answer("✅ Пользователь назначен администратором")
    await manager.switch_to(CreatorUsersSG.user_detail)


@inject
async def on_remove_admin_confirm_yes(
    _callback: CallbackQuery,
    _button: Button,
    manager: DialogManager,
    user_dao: FromDishka[UserDAO],
    user_repo: FromDishka[UserRepository],
    bot: FromDishka[Bot],
    config: FromDishka[Config],
):
    user_id = manager.dialog_data.get("selected_user_id")
    if not user_id:
        await _callback.answer("Ошибка: пользователь не выбран")
        return
    
    await user_dao.update(user_id=user_id, is_admin=False)
    asyncio.create_task(setup_bot_commands(bot, config, user_repo))
    await _callback.answer("✅ Пользователь снят с должности администратора")
    await manager.switch_to(CreatorUsersSG.user_detail)


async def on_confirm_no(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await _callback.answer("Отменено")
    await manager.switch_to(CreatorUsersSG.user_detail)


async def on_back_to_main(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.start(CreatorMenuSG.main, mode=StartMode.RESET_STACK)


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
        state=CreatorUsersSG.users_list,
        getter=get_users_data,
    ),
    Window(
        Const("<b>Введите ID или @username пользователя:</b>"),
        MessageInput(on_user_input),
        SwitchTo(Const("◀️ Назад"), id="back_to_list", state=CreatorUsersSG.users_list),
        state=CreatorUsersSG.users_input,
    ),
    Window(
        Format("{user_info}"),
        Column(
            Button(Const("👑 Сделать администратором"), id="make_admin", on_click=on_make_admin_clicked, when="show_make_admin"),
            Button(Const("🚫 Снять администратора"), id="remove_admin", on_click=on_remove_admin_clicked, when="show_remove_admin"),
            SwitchTo(Const("◀️ Назад"), id="back_to_list", state=CreatorUsersSG.users_list),
        ),
        state=CreatorUsersSG.user_detail,
        getter=get_user_detail_data,
    ),
    Window(
        Const("<b>⚠️ Подтверждение</b>\n\nВы уверены, что хотите назначить этого пользователя администратором?\n\n"),
        Format("{user_info}"),
        Row(
            Button(Const("✅ Да"), id="confirm_yes", on_click=on_confirm_yes),
            Button(Const("❌ Нет"), id="confirm_no", on_click=on_confirm_no),
        ),
        state=CreatorUsersSG.make_admin_confirm,
        getter=get_confirm_data,
    ),
    Window(
        Const("<b>⚠️ Подтверждение</b>\n\nВы уверены, что хотите снять этого пользователя с должности администратора?\n\n"),
        Format("{user_info}"),
        Row(
            Button(Const("✅ Да"), id="confirm_yes", on_click=on_remove_admin_confirm_yes),
            Button(Const("❌ Нет"), id="confirm_no", on_click=on_confirm_no),
        ),
        state=CreatorUsersSG.remove_admin_confirm,
        getter=get_confirm_data,
    ),
)
