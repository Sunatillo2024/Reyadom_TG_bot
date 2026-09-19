"""Add optional coordinates for location-based discovery."""

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("profiles") as batch:
        batch.add_column(sa.Column("latitude", sa.Float(), nullable=True))
        batch.add_column(sa.Column("longitude", sa.Float(), nullable=True))
        batch.create_check_constraint(
            "ck_profile_latitude", "latitude IS NULL OR latitude BETWEEN -90 AND 90"
        )
        batch.create_check_constraint(
            "ck_profile_longitude", "longitude IS NULL OR longitude BETWEEN -180 AND 180"
        )
        batch.create_index("ix_profiles_location", ["latitude", "longitude"])


def downgrade() -> None:
    with op.batch_alter_table("profiles") as batch:
        batch.drop_index("ix_profiles_location")
        batch.drop_constraint("ck_profile_longitude", type_="check")
        batch.drop_constraint("ck_profile_latitude", type_="check")
        batch.drop_column("longitude")
        batch.drop_column("latitude")
