import asyncio
import logging

from app.database import async_session_factory
from app.logging import setup_logging
from app.outbox.worker import OutboxWorker
from app.rabbitmq.connection import rabbitmq_connection

setup_logging()

logger = logging.getLogger(__name__)


class OutboxWorkerRunner:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.rabbitmq = rabbitmq_connection

    async def run(self) -> None:
        await self.rabbitmq.connect()

        try:
            worker = OutboxWorker(
                session_factory=self.session_factory,
                rabbitmq_connection=self.rabbitmq,
            )

            logger.info("Outbox Worker started")

            while True:
                try:
                    result = await worker.process_outbox_batch(limit=100)
                    logger.info("Processed: %s", result)

                except Exception:
                    logger.exception("Outbox processing error")

                await asyncio.sleep(5)

        finally:
            await self.rabbitmq.close()


async def main():
    runner = OutboxWorkerRunner(async_session_factory)
    await runner.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Outbox Worker stopped")
