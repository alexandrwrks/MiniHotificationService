from typing import Literal

from aio_pika.abc import AbstractExchange

from common.errors import AppError
from messaging.broker import ORDER_ROUTING_KEY, publish_json
from messaging.schema import EventDataSchema
from orders.schema import OrderSchema
from utils.log import rabbitmq_logger


async def publish_order(
    exchange: AbstractExchange,
    order: OrderSchema,
    event: Literal["order.created", "order.notification_requested"],
) -> str:
    payload = EventDataSchema(event=event, order=order)
    try:
        await publish_json(
            exchange=exchange,
            routing_key=ORDER_ROUTING_KEY,
            data=payload.model_dump(mode="json"),
        )
    except Exception as error:
        rabbitmq_logger.exception("Не удалось поставить уведомление в очередь")
        message = (
            "Order saved, notification not confirmed. Retry POST /send with order_id."
        )
        raise AppError(
            "unavailable", message, {"message": message, "order_id": order.id}
        ) from error
    return payload.event_id
