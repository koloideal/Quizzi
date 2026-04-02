from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, ScrollingGroup, Select, SwitchTo
from aiogram_dialog.widgets.text import Const, Format
from dishka import FromDishka
from dishka.integrations.aiogram_dialog import inject

from quizzi.application.bot.admin_dialogs.states import AdminUsersSG
from quizzi.infrastructure.database.dao.group import GroupDAO
from quizzi.infrastructure.database.dao.user import UserDAO
from quizzi.infrastructure.database.repo.test import TestRepository
from quizzi.infrastructure.database.repo.test_attempt import TestAttemptRepository
from quizzi.infrastructure.utils.timezone import to_msk


@inject
async def get_users_data(dialog_manager: DialogManager, user_dao: FromDishka[UserDAO], group_dao: FromDishka[GroupDAO], **_kwargs):
    filter_group = dialog_manager.dialog_data.get("filter_group")
    
    if filter_group:
        users = await user_dao.get_by_groups([filter_group])
    else:
        users = await user_dao.get_all()
    
    users_sorted = sorted(users, key=lambda u: u.created_at or u.id, reverse=True)
    
    groups = await group_dao.get_all()
    has_groups = len(groups) > 0
    
    filter_text = f" (группа {filter_group})" if filter_group else ""
    
    return {
        "users": [
            (f"{'👑 ' if u.is_admin else ''}{u.name or u.first_name} (@{u.username or 'нет'})", u.id)
            for u in users_sorted
        ],
        "count": len(users_sorted),
        "has_groups": has_groups,
        "filter_text": filter_text,
    }


@inject
async def get_groups_filter_data(group_dao: FromDishka[GroupDAO], **_kwargs):
    groups = await group_dao.get_all()
    return {
        "groups": [(str(g.id), str(g.number)) for g in groups],
    }


async def on_filter_group_click(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(AdminUsersSG.filter_by_group)


@inject
async def on_group_filter_selected(_callback: CallbackQuery, _widget, manager: DialogManager, item_id: str, group_dao: FromDishka[GroupDAO]):
    groups = await group_dao.get_all()
    group = next((g for g in groups if str(g.id) == item_id), None)
    if group:
        manager.dialog_data["filter_group"] = group.number
    await manager.switch_to(AdminUsersSG.users_list)


async def on_clear_filter(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    manager.dialog_data.pop("filter_group", None)
    await manager.switch_to(AdminUsersSG.users_list)


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


async def on_user_stats_clicked(_callback: CallbackQuery, _button: Button, manager: DialogManager):
    await manager.switch_to(AdminUsersSG.user_stats)


@inject
async def get_user_stats_data(
    dialog_manager: DialogManager,
    user_dao: FromDishka[UserDAO],
    attempt_repo: FromDishka[TestAttemptRepository],
    **_kwargs,
):
    user_id = dialog_manager.dialog_data.get("selected_user_id")
    if not user_id:
        return {"stats_info": "Пользователь не выбран", "results": [], "count": 0}
    
    user = await user_dao.get_by_id(user_id)
    if not user:
        return {"stats_info": "Пользователь не найден", "results": [], "count": 0}
    
    stats = await attempt_repo.get_user_stats(user_id)
    attempts_with_tests = await attempt_repo.get_finished_attempts_with_tests(user_id)
    
    name = user.name or user.first_name
    
    if stats["total_attempts"] > 0:
        accuracy_str = f"📊 Средняя точность: <b>{stats['avg_score']}%</b>"
        tests_str = f"📝 Пройдено тестов: <b>{stats['total_attempts']}</b>"
    else:
        accuracy_str = "📊 Средняя точность: <b>—</b>"
        tests_str = "📝 Пройдено тестов: <b>0</b>"
    
    stats_info = (
        f"<b>📊 Статистика: {name}</b>\n\n"
        f"{tests_str}\n"
        f"{accuracy_str}"
    )
    
    results = []
    for attempt, test_title in attempts_with_tests:
        status = "✅" if attempt.is_passed else "❌"
        finished_at_msk = to_msk(attempt.finished_at)
        date_str = finished_at_msk.strftime("%d.%m.%Y") if finished_at_msk else ""
        results.append((f"{status} {test_title} — {attempt.score}% ({date_str})", attempt.id))
    
    return {
        "stats_info": stats_info,
        "results": results,
        "count": len(results),
    }


async def on_result_selected(_callback: CallbackQuery, _widget: Select, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_attempt_id"] = int(item_id)
    await manager.switch_to(AdminUsersSG.user_result_detail)


@inject
async def get_user_result_detail(
    dialog_manager: DialogManager,
    attempt_repo: FromDishka[TestAttemptRepository],
    test_repo: FromDishka[TestRepository],
    **_kwargs
):
    attempt_id = dialog_manager.dialog_data.get("selected_attempt_id")
    
    if not attempt_id:
        return {"result_info": "❌ Результат не найден"}
    
    attempt, answers = await attempt_repo.get_attempt_with_answers(attempt_id)
    
    if not attempt:
        return {"result_info": "❌ Результат не найден"}
    
    test, _ = await test_repo.get_test_with_questions(attempt.test_id)
    test_title = test.title if test else "Неизвестный тест"
    
    status = "✅ Пройден" if attempt.is_passed else "❌ Не пройден"
    finished_at_msk = to_msk(attempt.finished_at)
    date_str = finished_at_msk.strftime("%d.%m.%Y %H:%M") if finished_at_msk else "—"
    
    correct_count = sum(1 for a in answers if a.is_correct)
    total_count = len(answers)
    
    lines = [
        f"<b>📝 {test_title}</b>\n",
        f"📊 <b>Результат:</b> {attempt.score}%",
        f"✏️ <b>Правильных ответов:</b> {correct_count} из {total_count}",
        f"📅 <b>Дата:</b> {date_str}",
        f"🏆 <b>Статус:</b> {status}",
        "\n<b>📋 Ответы:</b>\n",
    ]
    
    question_ids = [answer.question_id for answer in answers]
    questions_map = await test_repo.get_questions_with_options_by_ids(question_ids)
    
    for i, answer in enumerate(answers, 1):
        question_data = questions_map.get(answer.question_id)
        if not question_data:
            continue
        
        question, options = question_data
        correct_options = [opt for opt in options if opt.is_correct]
        correct_texts = [opt.text for opt in correct_options]
        
        status_icon = "✅" if answer.is_correct else "❌"
        
        user_answer = answer.text_answer or ""
        if "|" in user_answer:
            user_answer = ", ".join(user_answer.split("|"))
        
        lines.append(f"{status_icon} <b>Вопрос {i}</b>")
        lines.append(f"<blockquote>{question.text}</blockquote>")
        lines.append(f"👤 <i>Ответ:</i> {user_answer or '—'}")
        lines.append(f"✓ <i>Правильно:</i> {', '.join(correct_texts)}\n")
    
    return {"result_info": "\n".join(lines)}


admin_users_dialog = Dialog(
    Window(
        Format("<b>👥 Пользователи</b>{filter_text}\n\nВсего: {count}"),
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
            Button(Const("🔍 Фильтр по группе"), id="filter_group", on_click=on_filter_group_click, when="has_groups"),
            Button(Const("✏️ Ввести ID/Username"), id="input_mode", on_click=on_input_mode),
            Button(Const("◀️ Назад"), id="back", on_click=on_back_to_main),
        ),
        state=AdminUsersSG.users_list,
        getter=get_users_data,
    ),
    Window(
        Const("<b>🔍 Фильтр по группе</b>\n\nВыберите группу:"),
        ScrollingGroup(
            Select(
                Format("{item[1]}"),
                id="group_filter_select",
                item_id_getter=lambda x: x[0],
                items="groups",
                on_click=on_group_filter_selected,
            ),
            id="groups_filter_scroll",
            width=2,
            height=5,
        ),
        Column(
            Button(Const("🗑 Сбросить фильтр"), id="clear_filter", on_click=on_clear_filter),
            SwitchTo(Const("◀️ Назад"), id="back_to_list", state=AdminUsersSG.users_list),
        ),
        state=AdminUsersSG.filter_by_group,
        getter=get_groups_filter_data,
    ),
    Window(
        Const("<b>Введите ID или @username пользователя:</b>"),
        MessageInput(on_user_input),
        SwitchTo(Const("◀️ Назад"), id="back_to_list", state=AdminUsersSG.users_list),
        state=AdminUsersSG.users_input,
    ),
    Window(
        Format("{user_info}"),
        Column(
            Button(Const("📊 Статистика"), id="stats", on_click=on_user_stats_clicked),
            SwitchTo(Const("◀️ Назад"), id="back_to_list", state=AdminUsersSG.users_list),
        ),
        state=AdminUsersSG.user_detail,
        getter=get_user_detail_data,
    ),
    Window(
        Format("{stats_info}"),
        ScrollingGroup(
            Select(
                Format("{item[0]}"),
                id="result_select",
                item_id_getter=lambda x: x[1],
                items="results",
                on_click=on_result_selected,
            ),
            id="results_scroll",
            width=1,
            height=5,
        ),
        SwitchTo(Const("◀️ Назад"), id="back_to_detail", state=AdminUsersSG.user_detail),
        state=AdminUsersSG.user_stats,
        getter=get_user_stats_data,
    ),
    Window(
        Format("{result_info}"),
        SwitchTo(Const("◀️ Назад"), id="back_to_stats", state=AdminUsersSG.user_stats),
        state=AdminUsersSG.user_result_detail,
        getter=get_user_result_detail,
    ),
)
