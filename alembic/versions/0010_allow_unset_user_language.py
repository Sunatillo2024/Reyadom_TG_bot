"""Allow new users to have no selected language.

Revision: 0010
Revises: 0009
"""

import sqlalchemy as sa

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "users",
        "language",
        existing_type=sa.String(length=2),
        nullable=True,
        server_default=None,
    )



def downgrade() -> None:
    op.execute("UPDATE users SET language = 'ru' WHERE language IS NULL")
    op.alter_column(
        "users",
        "language",
        existing_type=sa.String(length=2),
        nullable=False,
        server_default="ru",
    )
