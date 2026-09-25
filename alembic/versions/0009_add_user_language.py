"""Add per-user interface language.

Revision: 0009
Revises: 0008
"""

import sqlalchemy as sa

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("language", sa.String(length=2), server_default="ru", nullable=False),
    )
    op.create_check_constraint(
        "ck_user_language", "users", "language IN ('ru', 'uz', 'en')"
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_language", "users", type_="check")
    op.drop_column("users", "language")
