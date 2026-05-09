"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-09 12:53:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

subscription_type = sa.Enum("FREE", "PREMIUM", name="subscription_type")
session_state = sa.Enum(
    "START",
    "AWAITING_PHONE",
    "AWAITING_OTP",
    "AWAITING_NAME",
    "AUTHENTICATED_MENU",
    "CHOOSING_IMMIGRATION_METHOD",
    "IN_CONSULTATION",
    name="session_state",
)
consultation_status = sa.Enum("IN_PROGRESS", "COMPLETED", "CANCELLED", name="consultation_status")
message_direction = sa.Enum("INBOUND", "OUTBOUND", name="message_direction")


def upgrade() -> None:
    bind = op.get_bind()
    subscription_type.create(bind, checkfirst=True)
    session_state.create(bind, checkfirst=True)
    consultation_status.create(bind, checkfirst=True)
    message_direction.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone_number_ciphertext", sa.String(length=512), nullable=False),
        sa.Column("phone_number_hash", sa.String(length=128), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("subscription_type", subscription_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("phone_number_hash", name="uq_users_phone_hash"),
    )
    op.create_index("ix_users_phone_number_hash", "users", ["phone_number_hash"])

    op.create_table(
        "otp_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone_number_hash", sa.String(length=128), nullable=False),
        sa.Column("phone_number_ciphertext", sa.String(length=512), nullable=False),
        sa.Column("otp_hash", sa.String(length=128), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_otp_challenges_phone_number_hash", "otp_challenges", ["phone_number_hash"])

    op.create_table(
        "conversation_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("bale_chat_id", sa.String(length=128), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("state", session_state, nullable=False),
        sa.Column("context", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("authenticated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("bale_chat_id"),
    )
    op.create_index("ix_conversation_sessions_bale_chat_id", "conversation_sessions", ["bale_chat_id"])

    op.create_table(
        "consultations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("status", consultation_status, nullable=False),
        sa.Column("collected_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_consultations_user_id", "consultations", ["user_id"])

    op.create_table(
        "usage_counters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usage_date", sa.Date(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "usage_date", name="uq_usage_user_date"),
    )
    op.create_index("ix_usage_counters_user_id", "usage_counters", ["user_id"])
    op.create_index("ix_usage_counters_usage_date", "usage_counters", ["usage_date"])

    op.create_table(
        "conversation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("bale_chat_id", sa.String(length=128), nullable=False),
        sa.Column("direction", message_direction, nullable=False),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("event_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_conversation_logs_bale_chat_id", "conversation_logs", ["bale_chat_id"])
    op.create_index("ix_conversation_logs_user_id", "conversation_logs", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_conversation_logs_user_id", table_name="conversation_logs")
    op.drop_index("ix_conversation_logs_bale_chat_id", table_name="conversation_logs")
    op.drop_table("conversation_logs")
    op.drop_index("ix_usage_counters_usage_date", table_name="usage_counters")
    op.drop_index("ix_usage_counters_user_id", table_name="usage_counters")
    op.drop_table("usage_counters")
    op.drop_index("ix_consultations_user_id", table_name="consultations")
    op.drop_table("consultations")
    op.drop_index("ix_conversation_sessions_bale_chat_id", table_name="conversation_sessions")
    op.drop_table("conversation_sessions")
    op.drop_index("ix_otp_challenges_phone_number_hash", table_name="otp_challenges")
    op.drop_table("otp_challenges")
    op.drop_index("ix_users_phone_number_hash", table_name="users")
    op.drop_table("users")

    message_direction.drop(op.get_bind(), checkfirst=True)
    consultation_status.drop(op.get_bind(), checkfirst=True)
    session_state.drop(op.get_bind(), checkfirst=True)
    subscription_type.drop(op.get_bind(), checkfirst=True)
