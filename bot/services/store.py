from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import and_, case, delete, exists, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from bot.db.database import Database
from bot.db.models import Block, Match, Profile, Reaction, Report, User
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


def pair_clause(left, right, actor: int, target: int):
    return or_(and_(left == actor, right == target), and_(left == target, right == actor))


class Store:
    def __init__(self, db: Database, admin_ids: list[int]) -> None:
        self.db = db
        self.admin_ids = frozenset(admin_ids)

    async def sync_user(self, telegram_id: int, username: str | None) -> User:
        async with self.db.sessions.begin() as session:
            user_id = await session.scalar(
                insert(User)
                .values(telegram_id=telegram_id, username=username)
                .on_conflict_do_update(
                    index_elements=[User.telegram_id], set_={"username": username}
                )
                .returning(User.id)
            )
            user = await session.get(User, user_id)
            if not username:
                profile = await session.get(Profile, user.id)
                if profile:
                    profile.is_active = False
            return user

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

    async def save_profile(self, actor: int, draft: dict[str, Any]) -> None:
        if "latitude" in draft and "longitude" in draft:
            latitude, longitude = coordinates(draft["latitude"], draft["longitude"])
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
        if values["gender"] not in {"male", "female"} or values["seeking"] not in {
            "male",
            "female",
            "any",
        }:
            raise RuleError("Выбери пол с помощью кнопки.")
        if not values["photo_file_id"] or not isinstance(draft.get("consent_at"), datetime):
            raise RuleError("Нужны фото и твоё согласие. Начни заново с /start.")
        values["city_normalized"] = normalize_city(values["city"])
        async with self.db.sessions.begin() as session:
            user = await self._actor(session, actor)
            if not user.username:
                raise RuleError("Добавь имя пользователя в настройках Telegram.")
            if await session.get(Profile, actor):
                raise RuleError("Анкета уже существует. Измени её в разделе «Моя анкета».")
            session.add(Profile(user_id=actor, consent_at=draft["consent_at"], **values))

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
        query = (
            select(Profile, distance)
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
        return query.order_by(distance.is_(None), distance, Profile.user_id)

    async def next_profile(self, actor: int, incoming: bool = False) -> Profile | None:
        async with self.db.sessions() as session:
            await self._actor(session, actor, active=True)
            result = await session.execute(self._candidates(actor, incoming=incoming).limit(1))
            row = result.first()
            if not row:
                return None
            profile, distance = row
            profile.distance_km = round(float(distance), 1) if distance is not None else None
            return profile

    async def decide(self, actor: int, target: int, kind: str) -> Decision:
        if kind not in {"like", "pass"} or actor == target:
            raise RuleError("Недопустимая реакция.")
        async with self.db.sessions.begin() as session:
            low, high = sorted((actor, target))
            await session.execute(select(func.pg_advisory_xact_lock(low, high)))
            await self._actor(session, actor, active=True)
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
            return list((await session.execute(query)).all())

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
            users = await session.scalar(select(func.count()).select_from(User))
            profiles = await session.scalar(
                select(func.count())
                .select_from(Profile)
                .join(User, User.id == Profile.user_id)
                .where(Profile.is_active.is_(True), User.is_banned.is_(False))
            )
            matches = await session.scalar(select(func.count()).select_from(Match))
            reports = await session.scalar(
                select(func.count()).select_from(Report).where(Report.status == "pending")
            )
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
