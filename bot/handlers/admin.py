from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.keyboards.common import inline
from bot.services.store import Store
from bot.services.telegram import caption, target_id
from bot.services.validation import RuleError

router = Router(name="admin")


@router.message(Command("admin"))
async def admin(message: Message, store: Store) -> None:
    if message.from_user is None:
        raise RuleError("Не удалось определить отправителя команды.")
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
    if message.from_user is None:
        raise RuleError("Не удалось определить отправителя команды.")
    store.require_admin(message.from_user.id)
    if message.text is None:
        raise RuleError("Укажи Telegram ID после команды: /ban 123456789")
    parts = message.text.split()
    if len(parts) != 2:
        raise RuleError("Укажи Telegram ID после команды: /ban 123456789")
    banned = parts[0].split("@")[0] == "/ban"
    await store.ban_by_telegram(message.from_user.id, target_id(parts[1]), banned)
    await message.answer(
        "Пользователь заблокирован."
        if banned
        else "Блокировка снята. Анкета не активируется автоматически."
    )


@router.message(Command("premium_grant"))
async def premium_grant_command(message: Message, store: Store) -> None:
    if message.from_user is None:
        raise RuleError("Не удалось определить отправителя команды.")
    store.require_admin(message.from_user.id)
    if message.text is None:
        raise RuleError("Формат: /premium_grant TELEGRAM_ID PLAN_CODE")
    parts = message.text.split()
    if len(parts) != 3:
        raise RuleError(
            "Формат: /premium_grant TELEGRAM_ID PLAN_CODE\n"
            "План: premium_3d, premium_1m, premium_3m"
        )

    target_telegram_id = target_id(parts[1])
    plan_code = parts[2]

    if plan_code not in {"premium_3d", "premium_1m", "premium_3m"}:
        raise RuleError("План должен быть: premium_3d, premium_1m или premium_3m")

    event_id = f"admin_{message.from_user.id}_{target_telegram_id}_{message.message_id}"
    new_until = await store.grant_premium_by_telegram(
        message.from_user.id, target_telegram_id, plan_code, event_id
    )

    await message.answer(
        f"<b>Premium выдан</b>\n"
        f"Пользователь: <code>{target_telegram_id}</code>\n"
        f"План: {plan_code}\n"
        f"Действует до: {new_until.strftime('%d.%m.%Y %H:%M UTC')}"
    )


@router.message(Command("premium_status"))
async def premium_status_command(message: Message, store: Store) -> None:
    if message.from_user is None:
        raise RuleError("Не удалось определить отправителя команды.")
    store.require_admin(message.from_user.id)
    if message.text is None:
        raise RuleError("Формат: /premium_status TELEGRAM_ID")
    parts = message.text.split()
    if len(parts) != 2:
        raise RuleError("Формат: /premium_status TELEGRAM_ID")

    target_telegram_id = target_id(parts[1])
    status = await store.premium_status_info(target_telegram_id)

    await message.answer(
        f"<b>Premium статус</b>\n"
        f"Пользователь: <code>{target_telegram_id}</code>\n"
        f"Статус: {'Активен' if status['is_premium'] else 'Нет Premium'}\n"
        + (
            f"Действует до: {status['until'].strftime('%d.%m.%Y %H:%M UTC')}\n"
            f"Осталось дней: {status['days_left']}"
            if status["is_premium"] and status["until"]
            else ""
        )
    )


@router.message(Command("premium_revoke"))
async def premium_revoke_command(message: Message, store: Store) -> None:
    if message.from_user is None:
        raise RuleError("Не удалось определить отправителя команды.")
    store.require_admin(message.from_user.id)
    if message.text is None:
        raise RuleError("Формат: /premium_revoke TELEGRAM_ID")
    parts = message.text.split()
    if len(parts) != 2:
        raise RuleError("Формат: /premium_revoke TELEGRAM_ID")

    target_telegram_id = target_id(parts[1])
    await store.revoke_premium_by_telegram(message.from_user.id, target_telegram_id)

    await message.answer(
        f"<b>Premium отозван</b>\n" f"Пользователь: <code>{target_telegram_id}</code>"
    )


@router.callback_query(F.data.startswith("admin:"))
async def admin_callback(callback: CallbackQuery, store: Store) -> None:
    store.require_admin(callback.from_user.id)
    if callback.data is None:
        raise RuleError("Недействительная кнопка администратора.")
    if callback.message is None or not isinstance(callback.message, Message):
        raise RuleError("Сообщение администратора недоступно.")
    message = callback.message
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
        await message.answer(
            f"<b>⚠️ Открытые жалобы</b>\nСтраница {page + 1}"
            if reports
            else "<b>Открытых жалоб нет</b>",
            reply_markup=inline(*rows),
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
        await message.answer(
            f"<b>Жалоба #{report.id}</b>\nПричина: {escape(report.reason)}\n"
            f"Статус: {'открыта' if report.status == 'pending' else 'рассмотрена'}",
            reply_markup=keyboard,
        )
        if profile:
            await message.answer_photo(profile.photo_file_id, caption=caption(profile))
        else:
            await message.answer("Текущая анкета удалена, но запись модерации сохранена.")
    elif action in {"ban", "unban", "review"}:
        await store.admin_action(callback.from_user.id, report_id, action)
        await message.answer(
            "<b>Действие выполнено</b>\nСнятие блокировки не активирует анкету автоматически.",
            reply_markup=inline((("⚠️ Жалобы", "admin:list:0"),)),
        )
    else:
        raise RuleError("Недопустимое действие администратора.")
