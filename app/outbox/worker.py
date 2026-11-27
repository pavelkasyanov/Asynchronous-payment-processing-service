import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.outbox import Outbox, OutboxStatus
from app.rabbitmq.connection import RabbitMQConnection

logger = logging.getLogger(__name__)

BATCH_SIZE = 50
PROCESSING_TIMEOUT = timedelta(minutes=10)
MAX_RETRIES = 5


class OutboxWorker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        rabbitmq_connection: RabbitMQConnection,
    ):
        self.session_factory = session_factory
        self.rabbitmq = rabbitmq_connection

    async def claim_batch(
        self,
        limit: int = BATCH_SIZE,
    ) -> list[dict[str, Any]]:

        now = datetime.now(UTC)
        stale_before = now - PROCESSING_TIMEOUT

        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(Outbox)
                    .where(
                        Outbox.status == OutboxStatus.PROCESSING.value,
                        Outbox.processing_started_at < stale_before,
                    )
                    .values(
                        status=OutboxStatus.NEW.value,
                        processing_started_at=None,
                    )
                )

                result = await session.execute(
                    select(Outbox)
                    .where(
                        Outbox.status == OutboxStatus.NEW.value,
                        Outbox.retry_count < MAX_RETRIES,
                    )
                    .order_by(Outbox.created_at)
                    .limit(limit)
                    .with_for_update(skip_locked=True)
                )

                events = result.scalars().all()
                batch = []

                for event in events:
                    event.status = OutboxStatus.PROCESSING.value
                    event.processing_started_at = now

                    batch.append(
                        {
                            "id": event.id,
                            "event_type": event.event_type,
                            "payload": event.payload,
                            "created_at": event.created_at.isoformat(),
                        }
                    )

            return batch

    async def mark_published_batch(
        self,
        event_ids: list[UUID],
    ) -> None:

        if not event_ids:
            return

        now = datetime.now(UTC)

        async with self.session_factory() as session:
            async with session.begin():
                await session.execute(
                    update(Outbox)
                    .where(
                        Outbox.id.in_(event_ids),
                        Outbox.status == OutboxStatus.PROCESSING.value,
                    )
                    .values(
                        status=OutboxStatus.PUBLISHED.value,
                        published_at=now,
                        processing_started_at=None,
                        last_error=None,
                    )
                )

    async def mark_failed_batch(
        self,
        failed_events: list[tuple[UUID, str]],
    ) -> None:

        if not failed_events:
            return

        async with self.session_factory() as session:
            async with session.begin():
                for event_id, error_message in failed_events:
                    await session.execute(
                        update(Outbox)
                        .where(
                            Outbox.id == event_id,
                            Outbox.status == OutboxStatus.PROCESSING.value,
                        )
                        .values(
                            status=OutboxStatus.FAILED.value
                            if (
                                await self._get_retry_count(
                                    session,
                                    event_id,
                                )
                            )
                            + 1
                            >= MAX_RETRIES
                            else OutboxStatus.NEW.value,
                            processing_started_at=None,
                            retry_count=Outbox.retry_count + 1,
                            last_error=error_message[:2000],
                        )
                    )

    async def _get_retry_count(
        self,
        session: AsyncSession,
        event_id: UUID,
    ) -> int:
        result = await session.execute(select(Outbox.retry_count).where(Outbox.id == event_id))
        return result.scalar_one()

    async def process_outbox_batch(
        self,
        limit: int = BATCH_SIZE,
    ) -> int:

        events = await self.claim_batch(limit)

        if not events:
            return 0

        published_ids: list[UUID] = []
        failed_events: list[tuple[UUID, str]] = []

        for event in events:
            event_id = event["id"]

            message = {
                "event_id": str(event_id),
                "event_type": event["event_type"],
                "payload": event["payload"],
                "created_at": event["created_at"],
            }

            try:
                confirmation = await self.rabbitmq.publish(
                    event["event_type"],
                    message,
                )

                if not confirmation:
                    raise RuntimeError("RabbitMQ rejected message")

                published_ids.append(event_id)

                logger.info(
                    "Outbox event %s published",
                    event_id,
                )

            except Exception as exc:
                logger.exception(
                    "Failed to publish event %s",
                    event_id,
                )

                failed_events.append((event_id, str(exc)))

        await self.mark_published_batch(published_ids)
        await self.mark_failed_batch(failed_events)

        logger.info(
            "Outbox batch processed: published=%s, failed=%s",
            len(published_ids),
            len(failed_events),
        )

        return len(published_ids)
