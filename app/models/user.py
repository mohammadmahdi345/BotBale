import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import utc_now
from app.db.base import Base
from app.models.enums import SubscriptionType


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("phone_number_hash", name="uq_users_phone_hash"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number_ciphertext: Mapped[str] = mapped_column(String(512), nullable=False)
    phone_number_hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        Enum(SubscriptionType, name="subscription_type"),
        default=SubscriptionType.FREE,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(default=True)
    is_verified: Mapped[bool] = mapped_column(default=True)

    sessions = relationship("ConversationSession", back_populates="user")
    consultations = relationship("Consultation", back_populates="user")
    usage_counters = relationship("UsageCounter", back_populates="user")
