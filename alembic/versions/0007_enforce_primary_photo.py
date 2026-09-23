"""Enforce one primary gallery photo per user.

Revision: 0007
Revises: 0006
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Repair rows created before the invariant was enforced. Prefer the photo already
    # referenced by profiles.photo_file_id, then the lowest stable gallery position.
    op.execute(
        """
        WITH ranked AS (
            SELECT pp.id,
                   row_number() OVER (
                       PARTITION BY pp.user_id
                       ORDER BY (pp.file_id = p.photo_file_id) DESC, pp.position, pp.id
                   ) AS rank
            FROM profile_photos AS pp
            JOIN profiles AS p ON p.user_id = pp.user_id
        )
        UPDATE profile_photos AS pp
        SET is_primary = (ranked.rank = 1)
        FROM ranked
        WHERE pp.id = ranked.id
        """
    )
    op.execute(
        """
        UPDATE profiles AS p
        SET photo_file_id = pp.file_id
        FROM profile_photos AS pp
        WHERE pp.user_id = p.user_id AND pp.is_primary
        """
    )
    op.drop_index("ix_profile_photos_primary", table_name="profile_photos")
    op.create_index(
        "ix_profile_photos_primary",
        "profile_photos",
        ["user_id"],
        unique=True,
        postgresql_where="is_primary",
    )


def downgrade() -> None:
    op.drop_index("ix_profile_photos_primary", table_name="profile_photos")
    op.create_index(
        "ix_profile_photos_primary",
        "profile_photos",
        ["user_id", "is_primary"],
    )
