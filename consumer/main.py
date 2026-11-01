import asyncio
from functools import partial

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from consumer.handler import process_order
from database.config import engine
from messaging.broker import (
    connect_rabbitmq,
    declare_notification_queue,
    declare_order_exchange,
)
from utils.settings import settings


async def main():
    connection = await connect_rabbitmq()
    try:
        async with Bot(
            settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        ) as bot:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            exchange = await declare_order_exchange(channel)
            queue = await declare_notification_queue(channel, exchange)
            await queue.consume(partial(process_order, bot=bot))
            await asyncio.Future()
    finally:
        await connection.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
