import logging
from typing import Any

from faststream.rabbit import RabbitBroker

from app.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    def __init__(self):
        self.broker = RabbitBroker(settings.RABBITMQ_URL)

    async def connect(self) -> None:
        await self.broker.connect()
        logger.info("Connected to RabbitMQ")

    async def close(self) -> None:
        await self.broker.stop()
        logger.info("RabbitMQ connection closed")

    async def publish(
        self,
        event_type: str,
        message: dict[str, Any],
        exchange: str = "",
    ) -> bool:
        try:
            await self.broker.publish(
                message,
                routing_key=event_type,
                exchange=exchange or settings.EXCHANGE_NAME,
            )
            return True

        except Exception:
            logger.exception("RabbitMQ publish error")
            return False

    def subscribe(self, queue: str, exchange: str = "", **kwargs):
        return self.broker.subscriber(
            queue,
            exchange=exchange or settings.EXCHANGE_NAME,
            **kwargs,
        )


rabbitmq_connection = RabbitMQConnection()
