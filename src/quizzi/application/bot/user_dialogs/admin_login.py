from aiogram.types import Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from quizzi.application.bot.user_dialogs.states import UserAdminLoginSG
from quizzi.infrastructure.database.dao.user import UserDAO
from quizzi.infrastructure.utils.config import Config
from quizzi.infrastructure.utils.rate_limiter import PasswordRateLimiter


password_limiter = PasswordRateLimiter()


@inject
async def on_password_input(
    message: Message,
    _widget: MessageInput,
    manager: DialogManager,
    user_dao: FromDishka[UserDAO],
    config: FromDishka[Config],
):
    assert message.from_user is not None
    assert message.text is not None
    
    user_id = message.from_user.id
    
    allowed, wait_time = await password_limiter.check(user_id)
    
    if not allowed:
        minutes = int(wait_time // 60)
        seconds = int(wait_time % 60)
        await message.answer(
            f"❌ Слишком много попыток. Попробуйте через {minutes} мин {seconds} сек"
        )
        await manager.done()
        return
    
    password = message.text.strip()
    
    if password == config.bot.admin_password:
        await user_dao.update(user_id, is_admin=True)
        await message.answer("✅ Вы успешно получили права администратора")
        
        try:
            await message.bot.send_message(
                config.bot.creator_id,
                f"🔔 Новый администратор:\n"
                f"ID: {user_id}\n"
                f"Username: @{message.from_user.username or 'нет'}\n"
                f"Имя: {message.from_user.first_name}"
            )
        except Exception:
            pass
        
        await manager.done()
    else:
        await message.answer("❌ Неверный пароль")


async def on_cancel(_callback, _button, manager: DialogManager):
    await manager.done()


admin_login_dialog = Dialog(
    Window(
        Const("<b>🔐 Вход в панель администратора</b>\n\n🔑 Введите пароль администратора:"),
        MessageInput(on_password_input),
        Button(Const("❌ Отмена"), id="cancel", on_click=on_cancel),
        state=UserAdminLoginSG.password_input,
    ),
)
