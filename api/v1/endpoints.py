import logging
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Path
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.deps.security import get_api_key
from app.models.outbox import Outbox
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    dependencies=[Depends(get_api_key)],
)
settings = get_settings()


@router.post(
    "/payments",
    status_code=202,
    response_model=PaymentResponse,
    summary="Создать новый платёж",
    description="Создание нового платежа с проверкой идемпотентности",
)
async def create_payment(
    payment_data: PaymentCreate,
    idempotency_key: Annotated[
        uuid.UUID,
        Header(description="Уникальный ключ для защиты от дублей"),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    async with db.begin():
        result = await db.execute(select(Payment).where(Payment.idempotency_key == idempotency_key))

        existing_payment = result.scalar_one_or_none()

        if existing_payment is not None:
            logger.debug("Payment already exists: %s", idempotency_key)
            return existing_payment

        payment = Payment(
            id=uuid.uuid4(),
            amount=payment_data.amount,
            currency=payment_data.currency,
            description=payment_data.description,
            meta=payment_data.meta,
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            webhook_url=payment_data.webhook_url,
            created_at=datetime.utcnow(),
        )
        db.add(payment)

        outbox_record = Outbox(
            payment_id=payment.id,
            event_type="payments.new",
            payload=payment_data.model_dump(mode="json"),
            created_at=datetime.utcnow(),
        )
        db.add(outbox_record)

    await db.refresh(payment)

    return payment


@router.get(
    "/payments/{payment_id}",
    response_model=PaymentResponse,
    summary="Получить информацию о платёже",
    description="Возвращает детальную информацию о платеже",
)
async def get_payment(
    payment_id: Annotated[
        uuid.UUID,
        Path(description="UUID платежа"),
    ],
    db: Annotated[
        AsyncSession,
        Depends(get_db),
    ],
):
    payment = await db.get(Payment, payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail={"error": "Платёж не найден"})

    return payment
