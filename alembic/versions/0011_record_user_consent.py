
"""Record one-time 18+/consent acceptance on the user row.

Revision: 0011
Revises: 0010
"""

import sqlalchemy as sa

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("consent_at", sa.DateTime(timezone=True)))
    # Users with an anketa have already accepted the 18+/consent screens once;
    # the timestamp must survive anketa deletion so the screens never reappear.
    op.execute(
        "UPDATE users SET consent_at = profiles.consent_at "
        "FROM profiles WHERE users.id = profiles.user_id"
    )


def downgrade() -> None:
    op.drop_column("users", "consent_at")
