from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_async_session
from messaging.publisher import publish_order
from orders.schema import OrderCreateSchema, OrderSchema, SendOrderSchema
from orders.service import create_order, get_order

router = APIRouter(tags=["Orders"])


@router.post("/orders", response_model=OrderSchema, status_code=201)
async def create_order_route(
    data: OrderCreateSchema,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order = await create_order(session, data)
    await publish_order(request.app.state.order_exchange, order, "order.created")
    return order


@router.get("/orders/{order_id}", response_model=OrderSchema)
async def read_order(order_id: int, session: AsyncSession = Depends(get_async_session)):
    return await get_order(session, order_id)


@router.post("/send", status_code=202)
async def send_order(
    data: SendOrderSchema,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    order = await get_order(session, data.order_id)
    event_id = await publish_order(
        request.app.state.order_exchange, order, "order.notification_requested"
    )
    return {
        "message": "Notification queued",
        "event_id": event_id,
        "order_id": order.id,
    }
