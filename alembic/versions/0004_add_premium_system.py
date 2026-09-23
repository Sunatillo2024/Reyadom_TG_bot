"""Add Premium system

Revision: 0004
Revises: 0003
"""

import sqlalchemy as sa

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Premium fields to users table
    op.add_column("users", sa.Column("premium_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "users",
        sa.Column(
            "show_premium_badge", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
    )
    op.create_index(op.f("ix_users_premium_until"), "users", ["premium_until"], unique=False)

    # Add Premium radius setting to profiles
    op.add_column("profiles", sa.Column("premium_radius_km", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_profile_premium_radius",
        "profiles",
        "premium_radius_km IS NULL OR premium_radius_km IN (10, 25, 50, 100)",
    )

    # Create profile_photos table (replaces single photo_file_id)
    op.create_table(
        "profile_photos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.String(length=512), nullable=False),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("length(file_id) > 0", name="ck_photo_file_id"),
        sa.CheckConstraint("position >= 0 AND position < 5", name="ck_photo_position"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "position", name="uq_photo_position"),
    )
    op.create_index(op.f("ix_profile_photos_user_id"), "profile_photos", ["user_id"], unique=False)
    op.create_index(
        "ix_profile_photos_primary",
        "profile_photos",
        ["user_id", "is_primary"],
        unique=False,
    )

    # Migrate existing photos to profile_photos table
    op.execute(
        """
        INSERT INTO profile_photos (user_id, file_id, is_primary, position, created_at)
        SELECT user_id, photo_file_id, true, 0, NOW()
        FROM profiles
        WHERE photo_file_id IS NOT NULL AND photo_file_id != ''
        """
    )

    # Create boost_history table
    op.create_table(
        "boost_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("next_available_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_boost_history_user_id"), "boost_history", ["user_id"], unique=False)
    op.create_index(op.f("ix_boost_history_ends_at"), "boost_history", ["ends_at"], unique=False)

    # Create premium_grants table (audit log)
    op.create_table(
        "premium_grants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("granted_by", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=10), nullable=False),
        sa.Column("plan_code", sa.String(length=20), nullable=True),
        sa.Column("event_id", sa.String(length=128), nullable=True),
        sa.Column("previous_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("new_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("action IN ('grant', 'revoke')", name="ck_grant_action"),
        sa.CheckConstraint(
            "plan_code IS NULL OR plan_code IN ('premium_3d', 'premium_1m', 'premium_3m')",
            name="ck_grant_plan",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_grant_event_id"),
    )
    op.create_index(op.f("ix_premium_grants_user_id"), "premium_grants", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_premium_grants_event_id"), "premium_grants", ["event_id"], unique=False
    )

    # Add index to reactions for daily like counting
    op.create_index(
        "ix_reactions_from_created",
        "reactions",
        ["from_user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_reactions_from_created", table_name="reactions")
    op.drop_index(op.f("ix_premium_grants_event_id"), table_name="premium_grants")
    op.drop_index(op.f("ix_premium_grants_user_id"), table_name="premium_grants")
    op.drop_table("premium_grants")
    op.drop_index(op.f("ix_boost_history_ends_at"), table_name="boost_history")
    op.drop_index(op.f("ix_boost_history_user_id"), table_name="boost_history")
    op.drop_table("boost_history")
    op.drop_index("ix_profile_photos_primary", table_name="profile_photos")
    op.drop_index(op.f("ix_profile_photos_user_id"), table_name="profile_photos")
    op.drop_table("profile_photos")
    op.drop_constraint("ck_profile_premium_radius", "profiles", type_="check")
    op.drop_column("profiles", "premium_radius_km")
    op.drop_index(op.f("ix_users_premium_until"), table_name="users")
    op.drop_column("users", "show_premium_badge")
    op.drop_column("users", "premium_until")
