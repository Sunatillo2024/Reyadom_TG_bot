from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from bot.i18n import tr
from bot.keyboards.common import inline
from bot.services.store import Store
from bot.services.telegram import caption, target_id
from bot.services.validation import RuleError

router = Router(name="admin")


@router.message(Command("admin"))
async def admin(message: Message, store: Store) -> None:
    if message.from_user is None:
        raise RuleError(tr("err_no_sender"))
    users, profiles, matches, reports = await store.stats(message.from_user.id)
    await message.answer(
        tr(
            "admin_panel",
            users=users,
            profiles=profiles,
            matches=matches,
            reports=reports,
        ),
        reply_markup=inline(((tr("admin_reports_button"), "admin:list:0"),)),
    )


@router.message(Command("ban", "unban"))
async def ban_command(message: Message, store: Store) -> None:
    if message.from_user is None:
        raise RuleError(tr("err_no_sender"))
    store.require_admin(message.from_user.id)
    if message.text is None:
        raise RuleError(tr("err_ban_usage"))
    parts = message.text.split()
    if len(parts) != 2:
        raise RuleError(tr("err_ban_usage"))
    banned = parts[0].split("@")[0] == "/ban"
    await store.ban_by_telegram(message.from_user.id, target_id(parts[1]), banned)
    await message.answer(tr("admin_banned") if banned else tr("admin_unbanned"))


@router.message(Command("premium_grant"))
async def premium_grant_command(message: Message, store: Store) -> None:
    if message.from_user is None:
        raise RuleError(tr("err_no_sender"))
    store.require_admin(message.from_user.id)
    if message.text is None:
        raise RuleError(tr("err_grant_usage"))
    parts = message.text.split()
    if len(parts) != 3:
        raise RuleError(tr("err_grant_plan_usage"))

    target_telegram_id = target_id(parts[1])
    plan_code = parts[2]

    if plan_code not in {"premium_3d", "premium_1m", "premium_3m"}:
        raise RuleError(tr("err_plan_invalid"))

    event_id = f"admin_{message.from_user.id}_{target_telegram_id}_{message.message_id}"
    new_until = await store.grant_premium_by_telegram(
        message.from_user.id, target_telegram_id, plan_code, event_id
    )

    await message.answer(
        tr(
            "admin_granted",
            telegram_id=target_telegram_id,
            plan=plan_code,
            until=new_until.strftime("%d.%m.%Y %H:%M UTC"),
        )
    )


@router.message(Command("premium_status"))
async def premium_status_command(message: Message, store: Store) -> None:
    if message.from_user is None:
        raise RuleError(tr("err_no_sender"))
    store.require_admin(message.from_user.id)
    if message.text is None:
        raise RuleError(tr("err_status_usage"))
    parts = message.text.split()
    if len(parts) != 2:
        raise RuleError(tr("err_status_usage"))

    target_telegram_id = target_id(parts[1])
    status = await store.premium_status_info(target_telegram_id)

    status_text = tr("admin_status_active") if status["is_premium"] else tr("admin_status_none")
    details = ""
    if status["is_premium"] and status["until"]:
        details = tr(
            "admin_status_until",
            until=status["until"].strftime("%d.%m.%Y %H:%M UTC"),
            days=status["days_left"],
        )
    await message.answer(
        tr(
            "admin_status",
            telegram_id=target_telegram_id,
            status=status_text,
            details=details,
        )
    )


@router.message(Command("premium_revoke"))
async def premium_revoke_command(message: Message, store: Store) -> None:
    if message.from_user is None:
        raise RuleError(tr("err_no_sender"))
    store.require_admin(message.from_user.id)
    if message.text is None:
        raise RuleError(tr("err_revoke_usage"))
    parts = message.text.split()
    if len(parts) != 2:
        raise RuleError(tr("err_revoke_usage"))

    target_telegram_id = target_id(parts[1])
    await store.revoke_premium_by_telegram(message.from_user.id, target_telegram_id)

    await message.answer(tr("admin_revoked", telegram_id=target_telegram_id))


@router.callback_query(F.data.startswith("admin:"))
async def admin_callback(callback: CallbackQuery, store: Store) -> None:
    store.require_admin(callback.from_user.id)
    if callback.data is None:
        raise RuleError(tr("err_admin_button"))
    if callback.message is None or not isinstance(callback.message, Message):
        raise RuleError(tr("err_admin_message"))
    message = callback.message
    parts = callback.data.split(":")
    if len(parts) != 3:
        raise RuleError(tr("err_admin_button"))
    action, raw_id = parts[1:]
    if action == "list":
        page = 0 if raw_id == "0" else target_id(raw_id)
        reports = await store.report_page(callback.from_user.id, page)
        rows = [
            ((tr("admin_report_row", report_id=report.id), f"admin:open:{report.id}"),)
            for report in reports
        ]
        navigation = []
        if page:
            navigation.append((tr("matches_prev"), f"admin:list:{page - 1}"))
        if len(reports) == 5:
            navigation.append((tr("matches_next"), f"admin:list:{page + 1}"))
        if navigation:
            rows.append(tuple(navigation))
        rows.append(((tr("back_menu"), "home"),))
        await message.answer(
            tr("admin_reports_page", page=page + 1)
            if reports
            else tr("admin_no_reports"),
            reply_markup=inline(*rows),
        )
        return
    report_id = target_id(raw_id)
    if action == "open":
        report, profile = await store.report_detail(callback.from_user.id, report_id)
        keyboard = inline(
            (
                (tr("admin_block_button"), f"admin:ban:{report_id}"),
                (tr("admin_unblock_button"), f"admin:unban:{report_id}"),
            ),
            ((tr("admin_reviewed_button"), f"admin:review:{report_id}"),),
            ((tr("admin_reports_button"), "admin:list:0"),),
        )
        await message.answer(
            tr(
                "admin_report_detail",
                report_id=report.id,
                reason=escape(report.reason),
                status=(
                    tr("admin_report_open")
                    if report.status == "pending"
                    else tr("admin_report_closed")
                ),
            ),
            reply_markup=keyboard,
        )
        if profile:
            await message.answer_photo(profile.photo_file_id, caption=caption(profile))
        else:
            await message.answer(tr("admin_profile_deleted"))
    elif action in {"ban", "unban", "review"}:
        await store.admin_action(callback.from_user.id, report_id, action)
        await message.answer(
            tr("admin_action_done"),
            reply_markup=inline(((tr("admin_reports_button"), "admin:list:0"),)),
        )
    else:
        raise RuleError(tr("err_admin_action"))
