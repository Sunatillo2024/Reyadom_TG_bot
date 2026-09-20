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
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (CheckConstraint("telegram_id > 0", name="ck_user_telegram_id"),)


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
