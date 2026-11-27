import asyncio
import logging
import random
from datetime import datetime

from faststream import AckPolicy
from faststream.rabbit.annotations import RabbitMessage

from app.config import get_settings
from app.database import async_session_factory
from app.models.payment import Payment, PaymentStatus
from app.rabbitmq.connection import rabbitmq_connection
from app.schemas.payment import PaymentEvent

settings = get_settings()

logger = logging.getLogger(__name__)


async def send_webhook(url: str | None, payload: dict, payment_id: str) -> bool:
    if not url:
        logger.warning(f"[Webhook] No URL specified for payment {payment_id}")
        return True

    logger.info(f"[Webhook] Sending a notification to {url} for the payment {payment_id}...")

    for attempt in range(settings.WEBHOOK_RETRY_ATTEMPTS):
        try:
            import aiohttp

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    status = response.status

                    if status == 200:
                        logger.info(f"[Webhook] Successfully delivered to {url}")
                        return True
                    elif status == 429:  # Rate limited
                        delay = settings.WEBHOOK_RETRY_BASE_DELAY
                        logger.error(f"[Webhook] Rate limited, repeat after {delay}s")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"[Webhook] Ошибка {status} от {url}")

                        if 500 <= status < 600:
                            delay = settings.WEBHOOK_RETRY_BASE_DELAY * (2**attempt)
                            logger.info(f"[Webhook] Server error, repeat after {delay}s")
                            await asyncio.sleep(delay)
                            continue
        except Exception as e:
            logger.error(f"[Webhook] Error while sending to {url}: {e}")

            if "Connection" in str(type(e)) or hasattr(e, "errno"):
                delay = settings.WEBHOOK_RETRY_BASE_DELAY * (2**attempt)
                logger.error(f"[Webhook] Network error, repeat after {delay}s")
                await asyncio.sleep(delay)
                continue

    logger.info(f"[Webhook] Maximum number of payment attempts reached {payment_id}")
    return False


@rabbitmq_connection.subscribe(settings.QUEUE_NAME, ack_policy=AckPolicy.MANUAL)
async def process_payment_event(
    event: dict,
    msg: RabbitMessage,
):
    logger.info(f"\n[Consumer] Event received for processing: {event}")

    try:
        payment_data = PaymentEvent(**event["payload"])
        payment_id = str(payment_data.id)

        logger.info(f"[Consumer] Payment processing {payment_id} (amount: {payment_data.amount} {payment_data.currency})")

        processing_time = random.uniform(2, 5)
        logger.info(f"[Consumer] Payment processing {payment_id}...")

        await asyncio.sleep(processing_time)

        success = random.random() < 0.9

        if success:
            new_status = PaymentStatus.SUCCEEDED
            message = "Successfully processed"
        else:
            new_status = PaymentStatus.FAILED
            message = "Payment processing error"

        async with async_session_factory() as session:
            payment = await session.get(Payment, payment_id)
            if payment:
                payment.status = new_status.value
                payment.processed_at = datetime.utcnow()
                await session.commit()
                logger.info(f"[Consumer] Payment status {payment_id}: {new_status.value}")

        webhook_success = True
        if payment_data.webhook_url:
            payload = {
                "event": "payment.processed",
                "data": {
                    "payment_id": payment_id,
                    "amount": str(payment_data.amount),
                    "currency": payment_data.currency,
                    "status": new_status.value,
                    "processed_at": datetime.utcnow().isoformat(),
                    "message": message,
                },
            }
            webhook_success = await send_webhook(url=payment_data.webhook_url, payload=payload, payment_id=payment_id)

        if webhook_success:
            logger.info(f"[Consumer] Payment {payment_id} processed: {new_status.value}, webhook delivered")
            await msg.ack()
        else:
            logger.error(f"[Consumer] Payment {payment_id} proccessed, but the webhook was not delivered: {new_status.value}")
            await msg.nack(requeue=True)

    except Exception as e:
        logger.exception(f"[Consumer] Proccess payment error{event.get('payment_id', 'unknown')}: {e}")
        await msg.nack(requeue=False)
        raise


@rabbitmq_connection.subscribe(settings.DEAD_LETTER_QUEUE, ack_policy=AckPolicy.MANUAL)
async def process_dlq_message(
    event: dict,
    msg: RabbitMessage,
):
    logger.info(f"\n[DLQ] Received msg from DLQ: {event}")
    await msg.ack()
