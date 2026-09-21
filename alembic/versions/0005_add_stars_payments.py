"""Add Telegram Stars Premium orders and payments.

Revision: 0005
Revises: 0004
"""

import sqlalchemy as sa

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "premium_orders",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("buyer_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("plan_code", sa.String(length=20), nullable=False),
        sa.Column("price_stars", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="XTR", nullable=False),
        sa.Column("duration_value", sa.Integer(), nullable=False),
        sa.Column("duration_unit", sa.String(length=6), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("invoice_message_id", sa.BigInteger(), nullable=True),
        sa.Column("notification_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "plan_code IN ('premium_3d', 'premium_1m', 'premium_3m')",
            name="ck_premium_order_plan",
        ),
        sa.CheckConstraint("price_stars > 0", name="ck_premium_order_price"),
        sa.CheckConstraint("currency = 'XTR'", name="ck_premium_order_currency"),
        sa.CheckConstraint("duration_value > 0", name="ck_premium_order_duration"),
        sa.CheckConstraint(
            "duration_unit IN ('days', 'months')", name="ck_premium_order_duration_unit"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'invoice_sending', 'invoice_sent', 'invoice_error', "
            "'checkout', 'completed', 'review', 'refund_pending', 'refund_unknown', "
            "'refunded')",
            name="ck_premium_order_status",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_premium_orders_user_id", "premium_orders", ["user_id"])
    op.create_index(
        "ix_premium_orders_buyer_telegram_id", "premium_orders", ["buyer_telegram_id"]
    )
    op.create_index("ix_premium_orders_status", "premium_orders", ["status"])
    op.create_index("ix_premium_orders_expires_at", "premium_orders", ["expires_at"])
    op.create_index(
        "ix_premium_orders_user_plan",
        "premium_orders",
        ["user_id", "plan_code", "status"],
    )

    op.create_table(
        "premium_payments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.String(length=32), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("buyer_telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_payment_charge_id", sa.String(length=128), nullable=False),
        sa.Column("provider_payment_charge_id", sa.String(length=128), nullable=True),
        sa.Column("invoice_payload", sa.String(length=128), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("failure_reason", sa.String(length=255), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("amount > 0", name="ck_premium_payment_amount"),
        sa.CheckConstraint(
            "status IN ('completed', 'review', 'refund_pending', 'refund_unknown', 'refunded')",
            name="ck_premium_payment_status",
        ),
        sa.ForeignKeyConstraint(["order_id"], ["premium_orders.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_payment_charge_id"),
    )
    op.create_index("ix_premium_payments_order_id", "premium_payments", ["order_id"])
    op.create_index("ix_premium_payments_user_id", "premium_payments", ["user_id"])
    op.create_index(
        "ix_premium_payments_buyer_telegram_id",
        "premium_payments",
        ["buyer_telegram_id"],
    )
    op.create_index("ix_premium_payments_status", "premium_payments", ["status"])
    op.create_index(
        "ix_premium_payments_order_status",
        "premium_payments",
        ["order_id", "status"],
    )

    op.add_column(
        "premium_grants",
        sa.Column("source", sa.String(length=10), server_default="admin", nullable=False),
    )
    op.add_column("premium_grants", sa.Column("order_id", sa.String(length=32), nullable=True))
    op.add_column(
        "premium_grants", sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "premium_grants", sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "premium_grants", sa.Column("reversed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.drop_constraint("ck_grant_action", "premium_grants", type_="check")
    op.create_check_constraint(
        "ck_grant_action", "premium_grants", "action IN ('grant', 'revoke', 'refund')"
    )
    op.create_check_constraint(
        "ck_grant_source", "premium_grants", "source IN ('admin', 'stars')"
    )
    op.create_foreign_key(
        "fk_premium_grants_order_id", "premium_grants", "premium_orders", ["order_id"], ["id"]
    )
    op.create_index("ix_premium_grants_order_id", "premium_grants", ["order_id"])
    op.execute(
        """
        UPDATE premium_grants
        SET starts_at = GREATEST(created_at, COALESCE(previous_until, created_at)),
            ends_at = new_until
        WHERE action = 'grant'
        """
    )


def downgrade() -> None:
    op.drop_index("ix_premium_grants_order_id", table_name="premium_grants")
    op.drop_constraint("fk_premium_grants_order_id", "premium_grants", type_="foreignkey")
    op.drop_constraint("ck_grant_source", "premium_grants", type_="check")
    op.drop_constraint("ck_grant_action", "premium_grants", type_="check")
    op.create_check_constraint(
        "ck_grant_action", "premium_grants", "action IN ('grant', 'revoke')"
    )
    op.drop_column("premium_grants", "reversed_at")
    op.drop_column("premium_grants", "ends_at")
    op.drop_column("premium_grants", "starts_at")
    op.drop_column("premium_grants", "order_id")
    op.drop_column("premium_grants", "source")
    op.drop_table("premium_payments")
    op.drop_table("premium_orders")
