import asyncio

from faststream import FastStream

from app.logging import setup_logging
from app.rabbitmq.connection import rabbitmq_connection

setup_logging()

app = FastStream(rabbitmq_connection.broker)


async def main():
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())
