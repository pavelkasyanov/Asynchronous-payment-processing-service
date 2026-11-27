import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.constants import OutboxStatus


class Outbox(Base):
    __tablename__ = "outbox"

    __table_args__ = (
        CheckConstraint(
            "retry_count >= 0",
            name="ck_outbox_retry_count_non_negative",
        ),
    )

    id = Column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
    )

    payment_id = Column(
        Uuid,
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(
        String(100),
        nullable=False,
        default="payments.new",
    )

    payload = Column(
        JSON,
        nullable=False,
    )

    status = Column(
        String(20),
        nullable=False,
        default=OutboxStatus.NEW.value,
        index=True,
    )

    retry_count = Column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    processing_started_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    published_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_error = Column(
        String(2000),
        nullable=True,
    )

    payment = relationship(
        "Payment",
        back_populates="outbox_record",
    )
