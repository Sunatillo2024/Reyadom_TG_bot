"""Add persistent one-time welcome Premium trial state.

Revision: 0006
Revises: 0005
"""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("trial_started_at", sa.DateTime(timezone=True)))
    op.add_column("users", sa.Column("trial_ends_at", sa.DateTime(timezone=True)))
    op.add_column(
        "users",
        sa.Column("trial_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column("users", sa.Column("trial_welcome_sent_at", sa.DateTime(timezone=True)))
    op.add_column("users", sa.Column("trial_reminder_sent_at", sa.DateTime(timezone=True)))
    op.add_column("users", sa.Column("trial_expired_sent_at", sa.DateTime(timezone=True)))

    # Every row present at deploy time is legacy and must never receive a welcome trial.
    op.execute("UPDATE users SET trial_used = true")

    op.create_check_constraint(
        "ck_user_trial_period",
        "users",
        "trial_started_at IS NULL OR trial_ends_at > trial_started_at",
    )
    op.create_check_constraint(
        "ck_user_trial_requires_used",
        "users",
        "trial_used OR (trial_started_at IS NULL AND trial_ends_at IS NULL)",
    )
    op.create_index("ix_users_trial_ends_at", "users", ["trial_ends_at"])


def downgrade() -> None:
    op.drop_index("ix_users_trial_ends_at", table_name="users")
    op.drop_constraint("ck_user_trial_requires_used", "users", type_="check")
    op.drop_constraint("ck_user_trial_period", "users", type_="check")
    op.drop_column("users", "trial_expired_sent_at")
    op.drop_column("users", "trial_reminder_sent_at")
    op.drop_column("users", "trial_welcome_sent_at")
    op.drop_column("users", "trial_used")
    op.drop_column("users", "trial_ends_at")
    op.drop_column("users", "trial_started_at")
