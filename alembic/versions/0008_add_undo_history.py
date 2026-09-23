"""Add persistent daily profile-return history.

Revision: 0008
Revises: 0007
"""

import sqlalchemy as sa

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "undo_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("user_id != target_user_id", name="ck_undo_self"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_undo_history_user_id", "undo_history", ["user_id"])
    op.create_index(
        "ix_undo_history_user_created",
        "undo_history",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_undo_history_user_created", table_name="undo_history")
    op.drop_index("ix_undo_history_user_id", table_name="undo_history")
    op.drop_table("undo_history")
