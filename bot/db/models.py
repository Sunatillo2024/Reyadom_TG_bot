from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    username: Mapped[str | None] = mapped_column(String(64))
    language: Mapped[str | None] = mapped_column(String(2), default=None, nullable=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    premium_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    trial_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    trial_welcome_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_reminder_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    trial_expired_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    show_premium_badge: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true")
    )
    # One-time 18+/consent acceptance. Lives on the user row (not the profile)
    # so the screens never reappear after an anketa is deleted.
    consent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        CheckConstraint("telegram_id > 0", name="ck_user_telegram_id"),
        CheckConstraint(
            "language IS NULL OR language IN ('ru', 'uz', 'en', 'kg')", name="ck_user_language"
        ),
        CheckConstraint(
            "trial_started_at IS NULL OR trial_ends_at > trial_started_at",
            name="ck_user_trial_period",
        ),
        CheckConstraint(
            "trial_used OR (trial_started_at IS NULL AND trial_ends_at IS NULL)",
            name="ck_user_trial_requires_used",
        ),
    )


class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    name: Mapped[str] = mapped_column(String(40))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(6))
    seeking: Mapped[str] = mapped_column(String(6))
    city: Mapped[str] = mapped_column(String(60))
    city_normalized: Mapped[str] = mapped_column(String(120), index=True)
    latitude: Mapped[float | None] = mapped_column()
    longitude: Mapped[float | None] = mapped_column()
    bio: Mapped[str] = mapped_column(String(300), default="")
    photo_file_id: Mapped[str] = mapped_column(String(512))
    min_age: Mapped[int] = mapped_column(Integer, default=18)
    max_age: Mapped[int] = mapped_column(Integer, default=99)
    own_city_only: Mapped[bool] = mapped_column(Boolean, default=True)
    premium_radius_km: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    __table_args__ = (
        CheckConstraint("age BETWEEN 18 AND 99", name="ck_profile_age"),
        CheckConstraint(
            "18 <= min_age AND min_age <= max_age AND max_age <= 99", name="ck_profile_range"
        ),
        CheckConstraint("gender IN ('male', 'female')", name="ck_profile_gender"),
        CheckConstraint("seeking IN ('male', 'female', 'any')", name="ck_profile_seeking"),
        CheckConstraint("length(name) BETWEEN 2 AND 40", name="ck_profile_name"),
        CheckConstraint("length(city) BETWEEN 2 AND 60", name="ck_profile_city"),
        CheckConstraint("length(bio) <= 300", name="ck_profile_bio"),
        CheckConstraint("length(photo_file_id) > 0", name="ck_profile_photo"),
        CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90", name="ck_profile_latitude"
        ),
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180", name="ck_profile_longitude"
        ),
        CheckConstraint(
            "premium_radius_km IS NULL OR premium_radius_km IN (10, 25, 50, 100)",
            name="ck_profile_premium_radius",
        ),
        Index("ix_profiles_location", "latitude", "longitude"),
    )


class Reaction(Base):
    __tablename__ = "reactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    from_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    to_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(4))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_reaction_pair"),
        CheckConstraint("from_user_id != to_user_id", name="ck_reaction_self"),
        CheckConstraint("kind IN ('like', 'pass')", name="ck_reaction_kind"),
        Index("ix_reactions_from_created", "from_user_id", "created_at"),
    )


class UndoHistory(Base):
    __tablename__ = "undo_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        CheckConstraint("user_id != target_user_id", name="ck_undo_self"),
        Index("ix_undo_history_user_created", "user_id", "created_at"),
    )


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_low_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user_high_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("user_low_id", "user_high_id", name="uq_match_pair"),
        CheckConstraint("user_low_id < user_high_id", name="ck_match_order"),
    )


class Block(Base):
    __tablename__ = "blocks"
    id: Mapped[int] = mapped_column(primary_key=True)
    blocker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    blocked_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_block_pair"),
        CheckConstraint("blocker_id != blocked_id", name="ck_block_self"),
    )


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reported_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[str] = mapped_column(String(320))
    status: Mapped[str] = mapped_column(String(8), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (
        CheckConstraint("reporter_id != reported_user_id", name="ck_report_self"),
        CheckConstraint("status IN ('pending', 'reviewed')", name="ck_report_status"),
        CheckConstraint("length(reason) BETWEEN 1 AND 320", name="ck_report_reason"),
        Index(
            "uq_report_pending",
            "reporter_id",
            "reported_user_id",
            unique=True,
            postgresql_where=text("status = 'pending'"),
        ),
    )


class ProfilePhoto(Base):
    __tablename__ = "profile_photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    file_id: Mapped[str] = mapped_column(String(512))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    position: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        CheckConstraint("length(file_id) > 0", name="ck_photo_file_id"),
        CheckConstraint("position >= 0 AND position < 5", name="ck_photo_position"),
        UniqueConstraint("user_id", "position", name="uq_photo_position"),
        Index(
            "ix_profile_photos_primary",
            "user_id",
            unique=True,
            postgresql_where=text("is_primary"),
        ),
    )


class BoostHistory(Base):
    __tablename__ = "boost_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    next_available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PremiumGrant(Base):
    __tablename__ = "premium_grants"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    granted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(10))
    plan_code: Mapped[str | None] = mapped_column(String(20))
    event_id: Mapped[str | None] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(10), default="admin", server_default="admin")
    order_id: Mapped[str | None] = mapped_column(ForeignKey("premium_orders.id"), index=True)
    previous_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    new_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        CheckConstraint("action IN ('grant', 'revoke', 'refund')", name="ck_grant_action"),
        CheckConstraint("source IN ('admin', 'stars')", name="ck_grant_source"),
        CheckConstraint(
            "plan_code IS NULL OR plan_code IN ('premium_3d', 'premium_1m', 'premium_3m')",
            name="ck_grant_plan",
        ),
        UniqueConstraint("event_id", name="uq_grant_event_id"),
        Index("ix_premium_grants_event_id", "event_id"),
    )


class PremiumOrder(Base):
    __tablename__ = "premium_orders"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    buyer_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    plan_code: Mapped[str] = mapped_column(String(20))
    price_stars: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3), default="XTR", server_default="XTR")
    duration_value: Mapped[int] = mapped_column(Integer)
    duration_unit: Mapped[str] = mapped_column(String(6))
    status: Mapped[str] = mapped_column(String(20), index=True)
    terms_accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    invoice_message_id: Mapped[int | None] = mapped_column(BigInteger)
    notification_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    __table_args__ = (
        CheckConstraint(
            "plan_code IN ('premium_3d', 'premium_1m', 'premium_3m')",
            name="ck_premium_order_plan",
        ),
        CheckConstraint("price_stars > 0", name="ck_premium_order_price"),
        CheckConstraint("currency = 'XTR'", name="ck_premium_order_currency"),
        CheckConstraint("duration_value > 0", name="ck_premium_order_duration"),
        CheckConstraint(
            "duration_unit IN ('days', 'months')", name="ck_premium_order_duration_unit"
        ),
        CheckConstraint(
            "status IN ('pending', 'invoice_sending', 'invoice_sent', 'invoice_error', "
            "'checkout', 'completed', 'review', 'refund_pending', 'refund_unknown', "
            "'refunded')",
            name="ck_premium_order_status",
        ),
        Index("ix_premium_orders_user_plan", "user_id", "plan_code", "status"),
    )


class PremiumPayment(Base):
    __tablename__ = "premium_payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str | None] = mapped_column(ForeignKey("premium_orders.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    buyer_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    telegram_payment_charge_id: Mapped[str] = mapped_column(String(128), unique=True)
    provider_payment_charge_id: Mapped[str | None] = mapped_column(String(128))
    invoice_payload: Mapped[str] = mapped_column(String(128))
    currency: Mapped[str] = mapped_column(String(3))
    amount: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), index=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_premium_payment_amount"),
        CheckConstraint(
            "status IN ('completed', 'review', 'refund_pending', 'refund_unknown', 'refunded')",
            name="ck_premium_payment_status",
        ),
        Index("ix_premium_payments_order_status", "order_id", "status"),
    )
