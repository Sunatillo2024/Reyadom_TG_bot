from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import and_, case, delete, exists, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from bot.db.database import Database
from bot.db.models import (
    Block,
    BoostHistory,
    Match,
    PremiumGrant,
    Profile,
    ProfilePhoto,
    Reaction,
    Report,
    User,
    utcnow,
)
from bot.services.premium import (
    BOOST_COOLDOWN_HOURS,
    BOOST_DURATION_MINUTES,
    FREE_DAILY_LIKES,
    FREE_PHOTO_LIMIT,
    PREMIUM_PHOTO_LIMIT,
    calculate_premium_end,
    daily_limit_start,
    has_premium,
    photo_limit,
    premium_status,
)
from bot.services.validation import (
    RuleError,
    age_range,
    age_value,
    clean_text,
    coordinates,
    normalize_city,
)


@dataclass(frozen=True)
class Decision:
    created: bool
    match_id: int | None = None
    recipient_telegram_id: int | None = None


@dataclass(frozen=True)
class UserSyncResult:
    user: User
    welcome_trial_granted: bool


@dataclass(frozen=True)
class TrialNotification:
    user_id: int
    telegram_id: int
    kind: str
    trial_started_at: datetime
    trial_ends_at: datetime


def pair_clause(left: Any, right: Any, actor: Any, target: Any):
    return or_(and_(left == actor, right == target), and_(left == target, right == actor))


class Store:
    def __init__(
        self,
        db: Database,
        admin_ids: list[int],
        *,
        stars_sales_enabled: bool = True,
        welcome_trial_enabled: bool = True,
        welcome_trial_days: int = 7,
    ) -> None:
        if welcome_trial_days < 1:
            raise ValueError("welcome_trial_days must be positive")
        self.db = db
        self.admin_ids = frozenset(admin_ids)
        self.stars_sales_enabled = stars_sales_enabled
        self.welcome_trial_enabled = welcome_trial_enabled
        self.welcome_trial_days = welcome_trial_days

    async def sync_user(
        self, telegram_id: int, username: str | None, *, now: datetime | None = None
    ) -> User:
        return (await self.sync_user_with_status(telegram_id, username, now=now)).user

    async def sync_user_with_status(
        self, telegram_id: int, username: str | None, *, now: datetime | None = None
    ) -> UserSyncResult:
        """Create or refresh a user, atomically consuming the one-time trial eligibility."""
        registered_at = now or datetime.now(UTC)
        trial_started_at = registered_at if self.welcome_trial_enabled else None
        trial_ends_at = (
            registered_at + timedelta(days=self.welcome_trial_days)
            if self.welcome_trial_enabled
            else None
        )
        async with self.db.sessions.begin() as session:
            created_user_id = await session.scalar(
                insert(User)
                .values(
                    telegram_id=telegram_id,
                    username=username,
                    created_at=registered_at,
                    trial_started_at=trial_started_at,
                    trial_ends_at=trial_ends_at,
                    # Registration consumes eligibility even while the feature is disabled.
                    trial_used=True,
                )
                .on_conflict_do_nothing(index_elements=[User.telegram_id])
                .returning(User.id)
            )
            trial_granted = created_user_id is not None and self.welcome_trial_enabled
            user = await session.scalar(
                select(User).where(User.telegram_id == telegram_id).with_for_update()
            )
            if user is None:
                raise RuleError("Пользователь не найден.")
            user.username = username
            # Rows must never retain eligibility after their first server-side registration.
            if not user.trial_used:
                user.trial_used = True
            if not username:
                profile = await session.get(Profile, user.id)
                if profile:
                    profile.is_active = False
            return UserSyncResult(user=user, welcome_trial_granted=trial_granted)

    async def claim_trial_notifications(
        self,
        *,
        now: datetime | None = None,
        user_id: int | None = None,
        limit: int = 100,
    ) -> list[TrialNotification]:
        """Atomically claim due trial notices so concurrent workers cannot duplicate them."""
        if limit < 1:
            return []
        claimed_at = now or datetime.now(UTC)
        reminder_cutoff = claimed_at + timedelta(hours=24)
        due = or_(
            User.trial_welcome_sent_at.is_(None),
            and_(
                User.trial_reminder_sent_at.is_(None),
                User.trial_ends_at > claimed_at,
                User.trial_ends_at <= reminder_cutoff,
            ),
            and_(
                User.trial_expired_sent_at.is_(None),
                User.trial_ends_at <= claimed_at,
            ),
        )
        async with self.db.sessions.begin() as session:
            query = (
                select(User)
                .where(User.trial_started_at.is_not(None), User.trial_ends_at.is_not(None), due)
                .order_by(User.trial_ends_at, User.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            if user_id is not None:
                query = query.where(User.id == user_id)
            users = list(await session.scalars(query))
            notifications: list[TrialNotification] = []
            for user in users:
                assert user.trial_started_at is not None
                assert user.trial_ends_at is not None
                paid_covers_trial = bool(
                    user.premium_until and user.premium_until > user.trial_ends_at
                )
                if user.trial_welcome_sent_at is None:
                    user.trial_welcome_sent_at = claimed_at
                    notifications.append(
                        TrialNotification(
                            user.id,
                            user.telegram_id,
                            "welcome",
                            user.trial_started_at,
                            user.trial_ends_at,
                        )
                    )
                if (
                    user.trial_reminder_sent_at is None
                    and claimed_at < user.trial_ends_at <= reminder_cutoff
                ):
                    user.trial_reminder_sent_at = claimed_at
                    if not paid_covers_trial:
                        notifications.append(
                            TrialNotification(
                                user.id,
                                user.telegram_id,
                                "reminder",
                                user.trial_started_at,
                                user.trial_ends_at,
                            )
                        )
                if user.trial_expired_sent_at is None and user.trial_ends_at <= claimed_at:
                    user.trial_expired_sent_at = claimed_at
                    if not paid_covers_trial:
                        notifications.append(
                            TrialNotification(
                                user.id,
                                user.telegram_id,
                                "expired",
                                user.trial_started_at,
                                user.trial_ends_at,
                            )
                        )
            return notifications

    async def hide_telegram(self, telegram_id: int) -> None:
        async with self.db.sessions.begin() as session:
            user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
            if user and (profile := await session.get(Profile, user.id)):
                profile.is_active = False

    async def _actor(self, session: AsyncSession, actor: int, active: bool = False) -> User:
        user = await session.get(User, actor)
        if not user or user.is_banned:
            raise RuleError("Доступ ограничен. Доступны /help, /privacy и /delete.")
        if active:
            profile = await session.get(Profile, actor)
            if not profile or not profile.is_active or not user.username:
                raise RuleError("Сначала создай анкету или снова сделай её видимой.")
        return user

    async def profile(self, actor: int) -> Profile | None:
        async with self.db.sessions() as session:
            return await session.get(Profile, actor)

    async def save_profile(self, actor: int, draft: dict[str, Any]) -> bool:
        """Atomically create a profile; return False when the same save was already applied."""
        async with self.db.sessions.begin() as session:
            # Serialize saves per user so duplicate Telegram updates cannot both insert a profile.
            user = await session.scalar(select(User).where(User.id == actor).with_for_update())
            if not user or user.is_banned:
                raise RuleError("Доступ ограничен. Доступны /help, /privacy и /delete.")
            if not user.username:
                raise RuleError("Добавь имя пользователя в настройках Telegram.")
            if await session.get(Profile, actor):
                return False

            try:
                if "latitude" in draft or "longitude" in draft:
                    latitude, longitude = coordinates(
                        draft.get("latitude"), draft.get("longitude")
                    )
                    city = "Геолокация"
                else:
                    latitude, longitude = None, None
                    city = clean_text(draft["city"], 2, 60)
                values = {
                    "name": clean_text(draft["name"], 2, 40),
                    "age": age_value(draft["age"]),
                    "gender": draft["gender"],
                    "seeking": draft["seeking"],
                    "city": city,
                    "bio": clean_text(draft["bio"], 0, 300),
                    "photo_file_id": draft["photo_file_id"],
                    "latitude": latitude,
                    "longitude": longitude,
                }
            except KeyError as exc:
                raise RuleError("Данные анкеты устарели. Начни заново с /start.") from exc
            if values["gender"] not in {"male", "female"} or values["seeking"] not in {
                "male",
                "female",
                "any",
            }:
                raise RuleError("Выбери пол с помощью кнопки.")
            if not values["photo_file_id"] or not isinstance(draft.get("consent_at"), datetime):
                raise RuleError("Нужны фото и твоё согласие. Начни заново с /start.")
            values["city_normalized"] = normalize_city(values["city"])

            # Old releases could leave gallery rows behind after deleting a profile.
            await session.execute(delete(ProfilePhoto).where(ProfilePhoto.user_id == actor))
            session.add(Profile(user_id=actor, consent_at=draft["consent_at"], **values))
            session.add(
                ProfilePhoto(
                    user_id=actor,
                    file_id=values["photo_file_id"],
                    is_primary=True,
                    position=0,
                    created_at=draft["consent_at"],
                )
            )
            await session.flush()
            return True

    async def edit_profile(self, actor: int, field: str, value: Any) -> None:
        if field in {"name", "city", "bio"}:
            limits = {"name": (2, 40), "city": (2, 60), "bio": (0, 300)}
            value = clean_text(value, *limits[field])
        elif field == "age":
            value = age_value(value)
        elif field == "gender" and value in {"male", "female"}:
            pass
        elif field == "seeking" and value in {"male", "female", "any"}:
            pass
        elif field == "photo_file_id" and isinstance(value, str) and value:
            pass
        else:
            raise RuleError("Недопустимое поле или значение.")
        async with self.db.sessions.begin() as session:
            await self._actor(session, actor)
            profile = await session.get(Profile, actor)
            if not profile:
                raise RuleError("Анкета не найдена. Отправь /start.")
            setattr(profile, field, value)
            if field == "city":
                profile.city_normalized = normalize_city(value)

    async def edit_location(self, actor: int, latitude: float, longitude: float) -> None:
        latitude, longitude = coordinates(latitude, longitude)
        async with self.db.sessions.begin() as session:
            await self._actor(session, actor)
            profile = await session.get(Profile, actor)
            if not profile:
                raise RuleError("Анкета не найдена. Отправь /start.")
            profile.latitude, profile.longitude = latitude, longitude
            profile.city, profile.city_normalized = "Геолокация", "геолокация"

    async def settings(self, actor: int, minimum: int, maximum: int, own_city: bool) -> None:
        minimum, maximum = age_range(minimum, maximum)
        async with self.db.sessions.begin() as session:
            await self._actor(session, actor)
            profile = await session.get(Profile, actor)
            if not profile:
                raise RuleError("Сначала создай анкету: /start")
            profile.min_age, profile.max_age = minimum, maximum
            profile.own_city_only = own_city

    async def set_active(self, actor: int, active: bool) -> None:
        async with self.db.sessions.begin() as session:
            user = await self._actor(session, actor)
            profile = await session.get(Profile, actor)
            if not profile or (active and not user.username):
                raise RuleError("Нужны анкета и имя пользователя Telegram.")
            profile.is_active = active

    async def delete_profile(self, actor: int) -> None:
        # Deliberately available to banned users. Moderation records survive.
        async with self.db.sessions.begin() as session:
            await session.execute(
                delete(Reaction).where(
                    or_(Reaction.from_user_id == actor, Reaction.to_user_id == actor)
                )
            )
            await session.execute(
                delete(Match).where(or_(Match.user_low_id == actor, Match.user_high_id == actor))
            )
            await session.execute(delete(ProfilePhoto).where(ProfilePhoto.user_id == actor))
            await session.execute(delete(BoostHistory).where(BoostHistory.user_id == actor))
            await session.execute(delete(Profile).where(Profile.user_id == actor))
            user = await session.get(User, actor)
            if user:
                user.username = None

    def _candidates(self, actor: int, *, decisions: bool = True, incoming: bool = False):
        own = aliased(Profile)
        owner = aliased(User)
        has_locations = and_(
            own.latitude.is_not(None),
            own.longitude.is_not(None),
            Profile.latitude.is_not(None),
            Profile.longitude.is_not(None),
        )
        own_latitude = func.radians(own.latitude)
        own_longitude = func.radians(own.longitude)
        candidate_latitude = func.radians(Profile.latitude)
        candidate_longitude = func.radians(Profile.longitude)
        haversine = func.power(func.sin((candidate_latitude - own_latitude) / 2), 2) + (
            func.cos(own_latitude)
            * func.cos(candidate_latitude)
            * func.power(func.sin((candidate_longitude - own_longitude) / 2), 2)
        )
        distance = case(
            (
                has_locations,
                6_371.0088
                * 2
                * func.asin(func.least(1.0, func.sqrt(haversine))),
            ),
            else_=None,
        ).label("distance_km")

        # Boost priority: profiles with active boost have priority=1, others priority=0
        now = func.now()
        has_boost = exists().where(
            BoostHistory.user_id == Profile.user_id,
            BoostHistory.started_at <= now,
            BoostHistory.ends_at > now,
        )
        boost_priority = case((has_boost, 1), else_=0).label("boost_priority")

        query = (
            select(Profile, distance, boost_priority)
            .join(User, User.id == Profile.user_id)
            .join(own, own.user_id == actor)
            .join(owner, owner.id == actor)
            .where(
                Profile.user_id != actor,
                Profile.is_active.is_(True),
                own.is_active.is_(True),
                User.is_banned.is_(False),
                owner.is_banned.is_(False),
                User.username.is_not(None),
                owner.username.is_not(None),
                Profile.age.between(own.min_age, own.max_age),
                own.age.between(Profile.min_age, Profile.max_age),
                or_(own.seeking == "any", own.seeking == Profile.gender),
                or_(Profile.seeking == "any", Profile.seeking == own.gender),
                or_(
                    has_locations,
                    and_(
                        own.latitude.is_(None),
                        Profile.latitude.is_(None),
                        or_(
                            and_(own.own_city_only.is_(False), Profile.own_city_only.is_(False)),
                            own.city_normalized == Profile.city_normalized,
                        ),
                    ),
                ),
                ~exists().where(
                    pair_clause(Block.blocker_id, Block.blocked_id, actor, Profile.user_id)
                ),
            )
        )

        # Apply premium radius filter if set
        query = query.where(
            or_(
                own.premium_radius_km.is_(None),
                ~has_locations,
                distance <= own.premium_radius_km,
            )
        )

        if decisions:
            query = query.where(
                ~exists().where(
                    Reaction.from_user_id == actor, Reaction.to_user_id == Profile.user_id
                ),
                ~exists().where(
                    Reaction.from_user_id == Profile.user_id,
                    Reaction.to_user_id == actor,
                    Reaction.kind == "pass",
                ),
                ~exists().where(
                    pair_clause(Match.user_low_id, Match.user_high_id, actor, Profile.user_id)
                ),
            )
        if incoming:
            query = query.where(
                exists().where(
                    Reaction.from_user_id == Profile.user_id,
                    Reaction.to_user_id == actor,
                    Reaction.kind == "like",
                )
            )
        # Sort by: boost (descending), distance (nulls last), then user_id
        return query.order_by(boost_priority.desc(), distance.is_(None), distance, Profile.user_id)

    async def next_profile(self, actor: int, incoming: bool = False) -> Profile | None:
        async with self.db.sessions() as session:
            await self._actor(session, actor, active=True)
            result = await session.execute(self._candidates(actor, incoming=incoming).limit(1))
            row = result.first()
            if not row:
                return None
            profile, distance, boost_priority = row
            profile.distance_km = round(float(distance), 1) if distance is not None else None
            return profile

    async def can_send_like(
        self, user: User, likes_today: int, now: datetime | None = None
    ) -> tuple[bool, str]:
        """Check if user can send a like considering Premium status and daily limit."""
        if has_premium(user, now):
            return True, ""

        if likes_today >= FREE_DAILY_LIKES:
            from bot.services.premium import daily_limit_reset_at

            reset_at = daily_limit_reset_at(now)
            return (
                False,
                f"Лимит {FREE_DAILY_LIKES} лайков исчерпан.\n"
                f"Следующее обновление: {reset_at.strftime('%H:%M')} UTC.\n\n"
                "💎 Premium снимает лимит лайков.",
            )
        return True, ""

    async def decide(self, actor: int, target: int, kind: str) -> Decision:
        if kind not in {"like", "pass"} or actor == target:
            raise RuleError("Недопустимая реакция.")
        async with self.db.sessions.begin() as session:
            low, high = sorted((actor, target))
            await session.execute(select(func.pg_advisory_xact_lock(low, high)))
            user = await self._actor(session, actor, active=True)

            # Check like limit before creating reaction
            if kind == "like":
                # Count likes within this transaction to avoid nested sessions
                from bot.services.premium import daily_limit_start

                now = utcnow()
                start_of_day = daily_limit_start(now)
                likes_today = await session.scalar(
                    select(func.count())
                    .select_from(Reaction)
                    .where(
                        Reaction.from_user_id == actor,
                        Reaction.kind == "like",
                        Reaction.created_at >= start_of_day,
                    )
                )
                can_like, error_msg = await self.can_send_like(user, likes_today or 0, now)
                if not can_like:
                    raise RuleError(error_msg)

            previous = await session.scalar(
                select(Reaction.id).where(
                    Reaction.from_user_id == actor, Reaction.to_user_id == target
                )
            )
            if previous is not None:
                return Decision(False)
            eligible = await session.scalar(
                self._candidates(actor).where(Profile.user_id == target)
            )
            if not eligible:
                raise RuleError("Эта анкета сейчас недоступна или не соответствует твоим фильтрам.")
            reaction_id = await session.scalar(
                insert(Reaction)
                .values(from_user_id=actor, to_user_id=target, kind=kind)
                .on_conflict_do_nothing(
                    index_elements=[Reaction.from_user_id, Reaction.to_user_id]
                )
                .returning(Reaction.id)
            )
            if reaction_id is None:
                return Decision(False)
            other = await session.get(User, target)
            if other is None:
                raise RuleError("Пользователь не найден.")
            reverse = await session.scalar(
                select(Reaction).where(
                    Reaction.from_user_id == target,
                    Reaction.to_user_id == actor,
                    Reaction.kind == "like",
                )
            )
            match_id = None
            if kind == "like" and reverse:
                match_id = await session.scalar(
                    insert(Match)
                    .values(user_low_id=low, user_high_id=high)
                    .on_conflict_do_nothing(
                        index_elements=[Match.user_low_id, Match.user_high_id]
                    )
                    .returning(Match.id)
                )
            return Decision(True, match_id, other.telegram_id)

    async def _match_target(self, session: AsyncSession, actor: int, match_id: int) -> User:
        await self._actor(session, actor)
        match = await session.get(Match, match_id)
        if not match or actor not in (match.user_low_id, match.user_high_id):
            raise RuleError("Взаимная симпатия не найдена или недоступна тебе.")
        target = match.user_high_id if actor == match.user_low_id else match.user_low_id
        user = await session.get(User, target)
        blocked = await session.scalar(
            select(Block.id).where(pair_clause(Block.blocker_id, Block.blocked_id, actor, target))
        )
        if (
            not user
            or user.is_banned
            or blocked
            or not await session.get(Profile, actor)
            or not await session.get(Profile, target)
        ):
            raise RuleError("Эта взаимная симпатия сейчас недоступна.")
        return user

    async def match_target(self, actor: int, match_id: int) -> User:
        async with self.db.sessions() as session:
            return await self._match_target(session, actor, match_id)

    async def match_page(self, actor: int, page: int) -> list[tuple[Match, Profile]]:
        if not 0 <= page <= 1_000_000:
            raise RuleError("Недопустимая страница.")
        async with self.db.sessions() as session:
            await self._actor(session, actor)
            if not await session.get(Profile, actor):
                return []
            query = (
                select(Match, Profile)
                .join(
                    Profile,
                    or_(
                        and_(Match.user_low_id == actor, Profile.user_id == Match.user_high_id),
                        and_(Match.user_high_id == actor, Profile.user_id == Match.user_low_id),
                    ),
                )
                .join(User, User.id == Profile.user_id)
                .where(
                    User.is_banned.is_(False),
                    ~exists().where(
                        pair_clause(Block.blocker_id, Block.blocked_id, actor, Profile.user_id)
                    ),
                )
                .order_by(Match.id.desc())
                .offset(page * 5)
                .limit(5)
            )
            return [(match, profile) for match, profile in (await session.execute(query)).all()]

    async def _moderation_target(self, session: AsyncSession, actor: int, target: int) -> None:
        await self._actor(session, actor)
        if actor == target or not await session.get(Profile, actor):
            raise RuleError("Недопустимая анкета.")
        if not await session.get(Profile, target):
            raise RuleError("Анкета удалена.")
        known = await session.scalar(
            select(Reaction.id).where(
                pair_clause(Reaction.from_user_id, Reaction.to_user_id, actor, target)
            )
        )
        matched = await session.scalar(
            select(Match.id).where(
                pair_clause(Match.user_low_id, Match.user_high_id, actor, target)
            )
        )
        blocked = await session.scalar(
            select(Block.id).where(Block.blocker_id == actor, Block.blocked_id == target)
        )
        eligible = await session.scalar(self._candidates(actor).where(Profile.user_id == target))
        if not (known or matched or blocked or eligible):
            raise RuleError("Действие с этой анкетой недоступно.")

    async def validate_target(self, actor: int, target: int) -> None:
        async with self.db.sessions() as session:
            await self._moderation_target(session, actor, target)

    async def _block(self, session: AsyncSession, actor: int, target: int) -> None:
        await session.execute(
            insert(Block)
            .values(blocker_id=actor, blocked_id=target)
            .on_conflict_do_nothing(index_elements=[Block.blocker_id, Block.blocked_id])
        )

    async def block(self, actor: int, target: int) -> None:
        async with self.db.sessions.begin() as session:
            await self._moderation_target(session, actor, target)
            await self._block(session, actor, target)

    async def report(self, actor: int, target: int, reason: str) -> None:
        if not 1 <= len(reason) <= 320:
            raise RuleError("Комментарий к жалобе слишком длинный или пустой.")
        async with self.db.sessions.begin() as session:
            low, high = sorted((actor, target))
            await session.execute(select(func.pg_advisory_xact_lock(low, high)))
            await self._moderation_target(session, actor, target)
            await session.execute(
                insert(Report)
                .values(reporter_id=actor, reported_user_id=target, reason=reason)
                .on_conflict_do_nothing(
                    index_elements=[Report.reporter_id, Report.reported_user_id],
                    index_where=text("status = 'pending'"),
                )
            )
            await self._block(session, actor, target)

    def require_admin(self, telegram_id: int) -> None:
        if telegram_id not in self.admin_ids:
            raise RuleError("Этот раздел доступен только администратору.")

    async def stats(self, telegram_id: int) -> tuple[int, int, int, int]:
        self.require_admin(telegram_id)
        async with self.db.sessions() as session:
            users = (await session.scalar(select(func.count()).select_from(User))) or 0
            profiles = await session.scalar(
                select(func.count())
                .select_from(Profile)
                .join(User, User.id == Profile.user_id)
                .where(Profile.is_active.is_(True), User.is_banned.is_(False))
            )
            profiles = profiles or 0
            matches = (await session.scalar(select(func.count()).select_from(Match))) or 0
            reports = await session.scalar(
                select(func.count()).select_from(Report).where(Report.status == "pending")
            )
            reports = reports or 0
            return users, profiles, matches, reports

    async def report_page(self, telegram_id: int, page: int) -> list[Report]:
        self.require_admin(telegram_id)
        if not 0 <= page <= 1_000_000:
            raise RuleError("Недопустимая страница.")
        async with self.db.sessions() as session:
            return list(
                await session.scalars(
                    select(Report)
                    .where(Report.status == "pending")
                    .order_by(Report.id)
                    .offset(page * 5)
                    .limit(5)
                )
            )

    async def report_detail(
        self, telegram_id: int, report_id: int
    ) -> tuple[Report, Profile | None]:
        self.require_admin(telegram_id)
        async with self.db.sessions() as session:
            report = await session.get(Report, report_id)
            if not report:
                raise RuleError("Жалоба не найдена.")
            return report, await session.get(Profile, report.reported_user_id)

    async def admin_action(self, telegram_id: int, report_id: int, action: str) -> None:
        self.require_admin(telegram_id)
        async with self.db.sessions.begin() as session:
            report = await session.get(Report, report_id)
            if not report or action not in {"ban", "unban", "review"}:
                raise RuleError("Недопустимое действие или жалоба.")
            if action == "review":
                admin = await session.scalar(select(User).where(User.telegram_id == telegram_id))
                if not admin:
                    raise RuleError("Сначала отправь /start.")
                report.status, report.reviewed_by = "reviewed", admin.id
            else:
                user = await session.get(User, report.reported_user_id)
                if user is None:
                    raise RuleError("Пользователь не найден.")
                user.is_banned = action == "ban"
                if action == "ban" and (profile := await session.get(Profile, user.id)):
                    profile.is_active = False

    async def ban_by_telegram(
        self, telegram_id: int, target_telegram_id: int, banned: bool
    ) -> None:
        self.require_admin(telegram_id)
        async with self.db.sessions.begin() as session:
            user = await session.scalar(select(User).where(User.telegram_id == target_telegram_id))
            if not user:
                raise RuleError("Пользователь не найден.")
            user.is_banned = banned
            if banned and (profile := await session.get(Profile, user.id)):
                profile.is_active = False

    # Premium methods

    async def grant_premium(
        self, admin_id: int | None, user_id: int, plan_code: str, event_id: str | None = None
    ) -> datetime:
        """Grant Premium to user. Returns new premium_until."""
        async with self.db.sessions.begin() as session:
            return await self.grant_premium_in_session(
                session,
                admin_id,
                user_id,
                plan_code,
                event_id=event_id,
                source="admin",
            )

    async def grant_premium_in_session(
        self,
        session: AsyncSession,
        admin_id: int | None,
        user_id: int,
        plan_code: str,
        *,
        event_id: str | None,
        source: str,
        order_id: str | None = None,
        now: datetime | None = None,
    ) -> datetime:
        """Grant or extend Premium inside the caller's transaction."""
        from bot.services.premium import PREMIUM_PLANS

        if plan_code not in PREMIUM_PLANS or source not in {"admin", "stars"}:
            raise RuleError("Недопустимый план Premium.")
        if event_id:
            existing = await session.scalar(
                select(PremiumGrant).where(PremiumGrant.event_id == event_id)
            )
            if existing and existing.new_until:
                return existing.new_until

        user = await session.scalar(select(User).where(User.id == user_id).with_for_update())
        if not user:
            raise RuleError("Пользователь не найден.")

        granted_at = now or datetime.now(UTC)
        previous_until = user.premium_until
        starts_at = max(
            value
            for value in (granted_at, previous_until, user.trial_ends_at)
            if value is not None
        )
        new_until = calculate_premium_end(
            previous_until,
            cast(Any, plan_code),
            granted_at,
            trial_until=user.trial_ends_at,
        )
        user.premium_until = new_until

        session.add(
            PremiumGrant(
                user_id=user_id,
                granted_by=admin_id,
                action="grant",
                plan_code=plan_code,
                event_id=event_id,
                source=source,
                order_id=order_id,
                previous_until=previous_until,
                new_until=new_until,
                starts_at=starts_at,
                ends_at=new_until,
                created_at=granted_at,
            )
        )

        return new_until

    async def grant_premium_by_telegram(
        self,
        admin_telegram_id: int,
        target_telegram_id: int,
        plan_code: str,
        event_id: str | None = None,
    ) -> datetime:
        """Grant Premium by Telegram ID. Requires admin privileges."""
        self.require_admin(admin_telegram_id)
        async with self.db.sessions() as session:
            admin = await session.scalar(select(User).where(User.telegram_id == admin_telegram_id))
            target = await session.scalar(
                select(User).where(User.telegram_id == target_telegram_id)
            )
            if not target:
                raise RuleError("Пользователь не найден.")
            admin_id = admin.id if admin else None
            target_id = target.id
        return await self.grant_premium(admin_id, target_id, plan_code, event_id)

    async def revoke_premium(self, admin_id: int | None, user_id: int) -> None:
        """Revoke Premium from user."""
        async with self.db.sessions.begin() as session:
            user = await session.scalar(select(User).where(User.id == user_id).with_for_update())
            if not user:
                raise RuleError("Пользователь не найден.")

            previous_until = user.premium_until
            user.premium_until = None

            # Clear Premium-specific settings
            profile = await session.get(Profile, user_id)
            if profile:
                profile.premium_radius_km = None

            now = datetime.now(UTC)
            session.add(
                PremiumGrant(
                    user_id=user_id,
                    granted_by=admin_id,
                    action="revoke",
                    plan_code=None,
                    event_id=None,
                    source="admin",
                    previous_until=previous_until,
                    new_until=None,
                    created_at=now,
                )
            )

    async def revoke_premium_by_telegram(
        self, admin_telegram_id: int, target_telegram_id: int
    ) -> None:
        """Revoke Premium by Telegram ID. Requires admin privileges."""
        self.require_admin(admin_telegram_id)
        async with self.db.sessions() as session:
            admin = await session.scalar(select(User).where(User.telegram_id == admin_telegram_id))
            target = await session.scalar(
                select(User).where(User.telegram_id == target_telegram_id)
            )
            if not target:
                raise RuleError("Пользователь не найден.")
            admin_id = admin.id if admin else None
            target_id = target.id
        await self.revoke_premium(admin_id, target_id)

    async def premium_status_info(self, target_telegram_id: int) -> dict[str, Any]:
        """Get Premium status info for a user by telegram_id."""
        async with self.db.sessions() as session:
            user = await session.scalar(
                select(User).where(User.telegram_id == target_telegram_id)
            )
            if not user:
                raise RuleError("Пользователь не найден.")
            status = premium_status(user)
            return {
                "is_premium": status.is_premium,
                "until": status.until,
                "days_left": status.days_left,
            }

    async def toggle_premium_badge(self, user_id: int) -> bool:
        """Toggle show_premium_badge setting for user. Returns new value."""
        async with self.db.sessions.begin() as session:
            user = await session.get(User, user_id)
            if not user:
                raise RuleError("Пользователь не найден.")
            user.show_premium_badge = not user.show_premium_badge
            return user.show_premium_badge

    async def undo_last_pass(self, actor: int) -> Profile | None:
        """Undo last pass reaction and return the un-passed profile."""
        async with self.db.sessions.begin() as session:
            await self._actor(session, actor, active=True)
            target = await session.scalar(
                select(Reaction.to_user_id)
                .where(Reaction.from_user_id == actor, Reaction.kind == "pass")
                .order_by(Reaction.created_at.desc())
                .limit(1)
            )
            if not target:
                return None

            await session.execute(
                delete(Reaction).where(
                    Reaction.from_user_id == actor,
                    Reaction.to_user_id == target,
                    Reaction.kind == "pass",
                )
            )
            return await session.get(Profile, target)

    async def count_likes_today(self, user_id: int, now: datetime | None = None) -> int:
        """Count likes sent today by user."""
        if now is None:
            from datetime import UTC

            now = datetime.now(UTC)

        start_of_day = daily_limit_start(now)

        async with self.db.sessions() as session:
            count = await session.scalar(
                select(func.count())
                .select_from(Reaction)
                .where(
                    Reaction.from_user_id == user_id,
                    Reaction.kind == "like",
                    Reaction.created_at >= start_of_day,
                )
            )
            return count or 0

    async def count_undos_today(self, user_id: int) -> int:
        """Count undo operations today. (Placeholder - implement when undo tracking is added)"""
        # This would need a separate undo_history table or reaction modification tracking
        # For now, return 0 as undo feature is not yet implemented
        return 0

    async def record_undo(self, user_id: int, target_id: int, now: datetime) -> None:
        """Record an undo operation. (Placeholder - implement when undo feature is added)"""
        # This would delete the most recent pass reaction and optionally log it
        async with self.db.sessions.begin() as session:
            await session.execute(
                delete(Reaction).where(
                    Reaction.from_user_id == user_id,
                    Reaction.to_user_id == target_id,
                    Reaction.kind == "pass",
                )
            )

    async def last_pass_target(self, user_id: int) -> int | None:
        """Get the last profile user passed on."""
        async with self.db.sessions() as session:
            result = await session.scalar(
                select(Reaction.to_user_id)
                .where(Reaction.from_user_id == user_id, Reaction.kind == "pass")
                .order_by(Reaction.created_at.desc())
                .limit(1)
            )
            return result

    # Profile photos (multiple photos)

    async def get_profile_photos(self, user_id: int) -> list[ProfilePhoto]:
        """Get all photos for user, ordered by position."""
        async with self.db.sessions() as session:
            return list(
                await session.scalars(
                    select(ProfilePhoto)
                    .where(ProfilePhoto.user_id == user_id)
                    .order_by(ProfilePhoto.position)
                )
            )

    async def add_profile_photo(self, user_id: int, file_id: str) -> ProfilePhoto:
        """Add a new photo to user's profile. Checks Premium photo limit."""
        async with self.db.sessions.begin() as session:
            user = await session.get(User, user_id)
            if not user:
                raise RuleError("Пользователь не найден.")

            existing_count = (
                await session.scalar(
                    select(func.count())
                    .select_from(ProfilePhoto)
                    .where(ProfilePhoto.user_id == user_id)
                )
                or 0
            )

            limit = photo_limit(user)
            if existing_count >= limit:
                if limit == FREE_PHOTO_LIMIT:
                    raise RuleError(
                        f"Достигнут лимит фото ({limit}).\n\n"
                        f"💎 Premium позволяет добавить до {PREMIUM_PHOTO_LIMIT} фото."
                    )
                else:
                    raise RuleError(f"Достигнут лимит фото ({limit}).")

            # Find next available position
            max_position = await session.scalar(
                select(func.max(ProfilePhoto.position)).where(ProfilePhoto.user_id == user_id)
            )
            next_position = (max_position + 1) if max_position is not None else 0

            photo = ProfilePhoto(
                user_id=user_id,
                file_id=file_id,
                is_primary=(existing_count == 0),
                position=next_position,
            )
            session.add(photo)
            await session.flush()
            await session.refresh(photo)
            return photo

    async def remove_profile_photo(self, user_id: int, photo_id: int) -> None:
        """Remove a photo. Cannot remove if it's the only photo."""
        async with self.db.sessions.begin() as session:
            photo_count = await session.scalar(
                select(func.count())
                .select_from(ProfilePhoto)
                .where(ProfilePhoto.user_id == user_id)
            )

            if photo_count is None or photo_count <= 1:
                raise RuleError("Нельзя удалить единственное фото. Сначала добавь другое.")

            photo = await session.get(ProfilePhoto, photo_id)
            if not photo or photo.user_id != user_id:
                raise RuleError("Фото не найдено.")

            was_primary = photo.is_primary
            await session.delete(photo)

            # If removed photo was primary, set another as primary
            if was_primary:
                new_primary = await session.scalar(
                    select(ProfilePhoto)
                    .where(ProfilePhoto.user_id == user_id)
                    .order_by(ProfilePhoto.position)
                    .limit(1)
                )
                if new_primary:
                    new_primary.is_primary = True

    async def set_primary_photo(self, user_id: int, photo_id: int) -> None:
        """Set a photo as primary (main profile photo)."""
        async with self.db.sessions.begin() as session:
            photo = await session.get(ProfilePhoto, photo_id)
            if not photo or photo.user_id != user_id:
                raise RuleError("Фото не найдено.")

            # Unset all other primary flags
            await session.execute(
                select(ProfilePhoto)
                .where(ProfilePhoto.user_id == user_id, ProfilePhoto.is_primary.is_(True))
                .with_for_update()
            )

            # Set new primary
            photo.is_primary = True

            # Update Profile.photo_file_id to match
            profile = await session.get(Profile, user_id)
            if profile:
                profile.photo_file_id = photo.file_id

    # Boost

    async def activate_boost(self, user_id: int, now: datetime) -> BoostHistory:
        """Activate Boost for Premium user."""
        from datetime import timedelta

        async with self.db.sessions.begin() as session:
            user = await session.get(User, user_id)
            if not user:
                raise RuleError("Пользователь не найден.")

            if not has_premium(user, now):
                raise RuleError("Boost доступен только с Premium.")

            can_activate, error = await self._can_activate_boost_internal(session, user_id, now)
            if not can_activate:
                raise RuleError(error)

            boost = BoostHistory(
                user_id=user_id,
                started_at=now,
                ends_at=now + timedelta(minutes=BOOST_DURATION_MINUTES),
                next_available_at=now + timedelta(hours=BOOST_COOLDOWN_HOURS),
            )
            session.add(boost)
            await session.flush()
            await session.refresh(boost)
            return boost

    async def _can_activate_boost_internal(
        self, session: AsyncSession, user_id: int, now: datetime
    ) -> tuple[bool, str]:
        """Internal helper to check boost activation eligibility."""
        last_boost = await session.scalar(
            select(BoostHistory)
            .where(BoostHistory.user_id == user_id)
            .order_by(BoostHistory.id.desc())
            .limit(1)
        )

        if last_boost and last_boost.next_available_at > now:
            hours_left = (last_boost.next_available_at - now).total_seconds() / 3600
            return (
                False,
                f"Boost можно активировать снова через {hours_left:.1f} ч.\n"
                f"Следующая активация: {last_boost.next_available_at.strftime('%H:%M')} UTC.",
            )

        return True, ""

    async def can_activate_boost(self, user_id: int, now: datetime) -> tuple[bool, str]:
        """Check if user can activate Boost."""
        async with self.db.sessions() as session:
            user = await session.get(User, user_id)
            if not user:
                return False, "Пользователь не найден."

            if not has_premium(user, now):
                return False, "Boost доступен только с Premium."

            return await self._can_activate_boost_internal(session, user_id, now)

    async def current_boost(self, user_id: int, now: datetime) -> BoostHistory | None:
        """Get current active Boost for user."""
        async with self.db.sessions() as session:
            return await session.scalar(
                select(BoostHistory)
                .where(
                    BoostHistory.user_id == user_id,
                    BoostHistory.started_at <= now,
                    BoostHistory.ends_at > now,
                )
                .order_by(BoostHistory.id.desc())
                .limit(1)
            )

    # Incoming likes with sorting

    async def get_profile_with_photos(self, user_id: int) -> tuple[Profile | None, list[str]]:
        """Get profile and list of photo file_ids for gallery navigation."""
        async with self.db.sessions() as session:
            profile = await session.get(Profile, user_id)
            if not profile:
                return None, []

            photos = await session.scalars(
                select(ProfilePhoto.file_id)
                .where(ProfilePhoto.user_id == user_id)
                .order_by(ProfilePhoto.position)
            )
            return profile, list(photos)

    async def incoming_likes_list(
        self, actor_id: int, sort_by: str = "time", page: int = 0
    ) -> list[tuple[Profile, float | None]]:
        """
        Get incoming likes sorted by time (newest) or distance (nearest).
        Returns list of (Profile, distance_km).
        """
        if sort_by not in {"time", "distance"}:
            raise RuleError("Недопустимая сортировка.")

        if not 0 <= page <= 1_000_000:
            raise RuleError("Недопустимая страница.")

        async with self.db.sessions() as session:
            user = await self._actor(session, actor_id)

            if not has_premium(user):
                raise RuleError("Список входящих лайков доступен только с Premium.")

            own = aliased(Profile)
            has_locations = and_(
                own.latitude.is_not(None),
                own.longitude.is_not(None),
                Profile.latitude.is_not(None),
                Profile.longitude.is_not(None),
            )
            own_latitude = func.radians(own.latitude)
            own_longitude = func.radians(own.longitude)
            candidate_latitude = func.radians(Profile.latitude)
            candidate_longitude = func.radians(Profile.longitude)
            haversine = func.power(func.sin((candidate_latitude - own_latitude) / 2), 2) + (
                func.cos(own_latitude)
                * func.cos(candidate_latitude)
                * func.power(func.sin((candidate_longitude - own_longitude) / 2), 2)
            )
            distance = case(
                (
                    has_locations,
                    6_371.0088 * 2 * func.asin(func.least(1.0, func.sqrt(haversine))),
                ),
                else_=None,
            ).label("distance_km")

            query = (
                select(Profile, distance, Reaction.created_at)
                .join(User, User.id == Profile.user_id)
                .join(own, own.user_id == actor_id)
                .join(
                    Reaction,
                    and_(
                        Reaction.from_user_id == Profile.user_id,
                        Reaction.to_user_id == actor_id,
                        Reaction.kind == "like",
                    ),
                )
                .where(
                    Profile.is_active.is_(True),
                    User.is_banned.is_(False),
                    User.username.is_not(None),
                    ~exists().where(
                        pair_clause(Block.blocker_id, Block.blocked_id, actor_id, Profile.user_id)
                    ),
                    ~exists().where(
                        pair_clause(
                            Match.user_low_id, Match.user_high_id, actor_id, Profile.user_id
                        )
                    ),
                )
            )

            if sort_by == "time":
                query = query.order_by(Reaction.created_at.desc())
            else:  # distance
                query = query.order_by(distance.is_(None), distance, Reaction.created_at.desc())

            query = query.offset(page * 10).limit(10)

            result = await session.execute(query)
            rows = result.all()

            return [
                (profile, round(float(dist), 1) if dist is not None else None)
                for profile, dist, _ in rows
            ]
