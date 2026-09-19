"""Initial SQLite schema. Frozen independently of future ORM model changes."""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(64)),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("telegram_id"),
        sa.CheckConstraint("telegram_id > 0", name="ck_user_telegram_id"),
    )
    op.create_table(
        "profiles",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("name", sa.String(40), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(6), nullable=False),
        sa.Column("seeking", sa.String(6), nullable=False),
        sa.Column("city", sa.String(60), nullable=False),
        sa.Column("city_normalized", sa.String(120), nullable=False),
        sa.Column("bio", sa.String(300), nullable=False),
        sa.Column("photo_file_id", sa.String(512), nullable=False),
        sa.Column("min_age", sa.Integer(), nullable=False),
        sa.Column("max_age", sa.Integer(), nullable=False),
        sa.Column("own_city_only", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("consent_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("age BETWEEN 18 AND 99", name="ck_profile_age"),
        sa.CheckConstraint(
            "18 <= min_age AND min_age <= max_age AND max_age <= 99", name="ck_profile_range"
        ),
        sa.CheckConstraint("gender IN ('male', 'female')", name="ck_profile_gender"),
        sa.CheckConstraint("seeking IN ('male', 'female', 'any')", name="ck_profile_seeking"),
        sa.CheckConstraint("length(name) BETWEEN 2 AND 40", name="ck_profile_name"),
        sa.CheckConstraint("length(city) BETWEEN 2 AND 60", name="ck_profile_city"),
        sa.CheckConstraint("length(bio) <= 300", name="ck_profile_bio"),
        sa.CheckConstraint("length(photo_file_id) > 0", name="ck_profile_photo"),
    )
    op.create_index("ix_profiles_city_normalized", "profiles", ["city_normalized"])
    op.create_index("ix_profiles_is_active", "profiles", ["is_active"])
    op.create_table(
        "reactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("to_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("kind", sa.String(4), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("from_user_id", "to_user_id", name="uq_reaction_pair"),
        sa.CheckConstraint("from_user_id != to_user_id", name="ck_reaction_self"),
        sa.CheckConstraint("kind IN ('like', 'pass')", name="ck_reaction_kind"),
    )
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_low_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("user_high_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("user_low_id", "user_high_id", name="uq_match_pair"),
        sa.CheckConstraint("user_low_id < user_high_id", name="ck_match_order"),
    )
    op.create_table(
        "blocks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("blocker_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("blocked_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("blocker_id", "blocked_id", name="uq_block_pair"),
        sa.CheckConstraint("blocker_id != blocked_id", name="ck_block_self"),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporter_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reported_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.String(320), nullable=False),
        sa.Column("status", sa.String(8), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id")),
        sa.CheckConstraint("reporter_id != reported_user_id", name="ck_report_self"),
        sa.CheckConstraint("status IN ('pending', 'reviewed')", name="ck_report_status"),
        sa.CheckConstraint("length(reason) BETWEEN 1 AND 320", name="ck_report_reason"),
    )
    for table, columns in {
        "reactions": ("from_user_id", "to_user_id"),
        "matches": ("user_low_id", "user_high_id"),
        "blocks": ("blocker_id", "blocked_id"),
        "reports": ("reporter_id", "reported_user_id", "status"),
    }.items():
        for column in columns:
            op.create_index(f"ix_{table}_{column}", table, [column])
    op.create_index(
        "uq_report_pending",
        "reports",
        ["reporter_id", "reported_user_id"],
        unique=True,
        sqlite_where=sa.text("status = 'pending'"),
    )


def downgrade() -> None:
    for table in ("reports", "blocks", "matches", "reactions", "profiles", "users"):
        op.drop_table(table)
