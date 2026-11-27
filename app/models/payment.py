import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, Column, DateTime, Numeric, String, Uuid
from sqlalchemy.orm import relationship

from app.database import Base


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)

    amount = Column(Numeric(18, 2), nullable=False)

    currency = Column(String(3), nullable=False, default="RUB")

    description = Column(String(500), nullable=False)

    meta = Column(JSON, default=dict)

    status = Column(String(20), nullable=False, default=PaymentStatus.PENDING)

    idempotency_key = Column(Uuid, unique=True, index=True, nullable=False)
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    outbox_record = relationship("Outbox", back_populates="payment", uselist=False)
