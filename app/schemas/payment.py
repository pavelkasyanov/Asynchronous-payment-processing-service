import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PaymentData(BaseModel):
    amount: Decimal
    currency: str = Field(..., pattern="^(RUB|USD|EUR)$")
    description: str
    meta: dict = Field(default_factory=dict)
    webhook_url: str = Field(..., min_length=1, max_length=500)


class PaymentCreate(PaymentData):
    pass


class PaymentResponse(PaymentData):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    status: str = Field(default="pending")
    created_at: datetime
    processed_at: datetime | None = None


class PaymentEvent(PaymentData):
    id: uuid.UUID
    idempotency_key: str
