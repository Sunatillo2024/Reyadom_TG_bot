"""Allow Kyrgyz as a per-user interface language.

Revision: 0012
Revises: 0011
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_user_language", "users", type_="check")
    op.create_check_constraint(
        "ck_user_language", "users", "language IS NULL OR language IN ('ru', 'uz', 'en', 'kg')"
    )


def downgrade() -> None:
    op.execute("UPDATE users SET language = 'ru' WHERE language = 'kg'")
    op.drop_constraint("ck_user_language", "users", type_="check")
    op.create_check_constraint(
        "ck_user_language", "users", "language IS NULL OR language IN ('ru', 'uz', 'en')"
    )
