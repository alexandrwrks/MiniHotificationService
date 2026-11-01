import json

import aio_pika
from aio_pika.abc import (
    AbstractChannel,
    AbstractExchange,
    AbstractQueue,
    AbstractRobustConnection,
)

from utils.settings import settings

NOTIFICATION_QUEUE = "notifications.order_created"
ORDER_EXCHANGE = "order"
ORDER_ROUTING_KEY = "order.created"


async def connect_rabbitmq() -> AbstractRobustConnection:
    return await aio_pika.connect_robust(settings.RABBITMQ_URL)


async def declare_order_exchange(channel: AbstractChannel) -> AbstractExchange:
    return await channel.declare_exchange(
        name=ORDER_EXCHANGE,
        durable=True,
    )


async def declare_notification_queue(
    channel: AbstractChannel, exchange: AbstractExchange
) -> AbstractQueue:
    queue: AbstractQueue = await channel.declare_queue(
        name=NOTIFICATION_QUEUE, durable=True
    )

    await queue.bind(exchange, routing_key=ORDER_ROUTING_KEY)

    return queue


async def publish_json(exchange: AbstractExchange, routing_key: str, data: dict):
    message = aio_pika.Message(
        body=json.dumps(data).encode(),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await exchange.publish(message, routing_key=routing_key)
