from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.common import inline
from bot.services.store import Store
from bot.services.telegram import caption, navigate, target_id
from bot.services.validation import RuleError

router = Router(name="admin")


@router.message(Command("admin"))
async def admin(message: Message, store: Store) -> None:
    users, profiles, matches, reports = await store.stats(message.from_user.id)
    await message.answer(
        f"<b>🛡 Панель администратора</b>\n"
        f"Пользователи: {users}\nАктивные анкеты: {profiles}\n"
        f"Взаимные симпатии: {matches}\nОткрытые жалобы: {reports}\n\n"
        "/ban Telegram_ID — заблокировать\n/unban Telegram_ID — снять блокировку",
        reply_markup=inline((("⚠️ Жалобы", "admin:list:0"),)),
    )


@router.message(Command("ban", "unban"))
async def ban_command(message: Message, store: Store) -> None:
    store.require_admin(message.from_user.id)
    parts = (message.text or "").split()
    if len(parts) != 2:
        raise RuleError("Укажи Telegram ID после команды: /ban 123456789")
    banned = parts[0].split("@")[0] == "/ban"
    await store.ban_by_telegram(message.from_user.id, target_id(parts[1]), banned)
    await message.answer(
        "Пользователь заблокирован."
        if banned
        else "Блокировка снята. Анкета не активируется автоматически."
    )


@router.callback_query(F.data.startswith("admin:"))
async def admin_callback(callback: CallbackQuery, store: Store) -> None:
    store.require_admin(callback.from_user.id)
    parts = callback.data.split(":")
    if len(parts) != 3:
        raise RuleError("Недействительная кнопка администратора.")
    action, raw_id = parts[1:]
    if action == "list":
        page = 0 if raw_id == "0" else target_id(raw_id)
        reports = await store.report_page(callback.from_user.id, page)
        rows = [((f"Жалоба #{report.id}", f"admin:open:{report.id}"),) for report in reports]
        navigation = []
        if page:
            navigation.append(("← Назад", f"admin:list:{page - 1}"))
        if len(reports) == 5:
            navigation.append(("Далее →", f"admin:list:{page + 1}"))
        if navigation:
            rows.append(tuple(navigation))
        rows.append((("🏠 В меню", "home"),))
        await navigate(
            callback,
            f"<b>⚠️ Открытые жалобы</b>\nСтраница {page + 1}"
            if reports
            else "<b>Открытых жалоб нет</b>",
            inline(*rows),
        )
        return
    report_id = target_id(raw_id)
    if action == "open":
        report, profile = await store.report_detail(callback.from_user.id, report_id)
        keyboard = inline(
            (
                ("Заблокировать", f"admin:ban:{report_id}"),
                ("Снять блокировку", f"admin:unban:{report_id}"),
            ),
            (("Рассмотрено", f"admin:review:{report_id}"),),
            (("⚠️ Жалобы", "admin:list:0"),),
        )
        report_text = (
            f"<b>Жалоба #{report.id}</b>\nПричина: {escape(report.reason)}\n"
            f"Статус: {'открыта' if report.status == 'pending' else 'рассмотрена'}"
        )
        if profile:
            await navigate(
                callback,
                report_text + "\n\n" + caption(profile),
                keyboard,
                photo=profile.photo_file_id,
            )
        else:
            await navigate(
                callback,
                report_text + "\n\nТекущая анкета удалена, но запись модерации сохранена.",
                keyboard,
            )
    elif action in {"ban", "unban", "review"}:
        await store.admin_action(callback.from_user.id, report_id, action)
        await navigate(
            callback,
            "<b>Действие выполнено</b>\nСнятие блокировки не активирует анкету автоматически.",
            inline((("⚠️ Жалобы", "admin:list:0"),)),
        )
    else:
        raise RuleError("Недопустимое действие администратора.")
