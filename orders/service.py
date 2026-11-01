from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from common.errors import AppError
from database.enum import OrderStatusType as Status
from database.models import Orders, Services
from orders.repo import OrderRepo
from orders.schema import OrderCreateSchema, OrderSchema
from orders.status import ACTIVE_STATUSES, TRANSITIONS
from users.repo import UserRepo


async def get_order(session: AsyncSession, order_id: int) -> OrderSchema:
    order = await OrderRepo(session).get(order_id)
    if order is None:
        raise AppError("not_found", "Заказ не найден.")
    return order


async def get_employee_order(
    session: AsyncSession, order_id: int, telegram_id: int
) -> OrderSchema:
    user = await UserRepo(session).get_by_telegram_id(telegram_id)
    if user is None:
        raise AppError("forbidden", "Сначала зарегистрируйтесь командой /start.")
    order = await get_order(session, order_id)
    if order.assigned_employee_id != user.id:
        raise AppError("forbidden", "Этот заказ назначен другому сотруднику.")
    return order


async def list_employee_orders(
    session: AsyncSession,
    telegram_id: int,
    page: int,
    page_size: int,
    archived: bool = False,
) -> list[OrderSchema]:
    user = await UserRepo(session).get_by_telegram_id(telegram_id)
    if user is None:
        raise AppError("forbidden", "Сначала зарегистрируйтесь командой /start.")
    return await OrderRepo(session).list_for_employee(
        user.id,
        (Status.COMPLETED, Status.CANCELED) if archived else ACTIVE_STATUSES,
        page * page_size,
        page_size + 1,
    )


async def create_order(session: AsyncSession, data: OrderCreateSchema) -> OrderSchema:
    users = UserRepo(session)
    if await users.get_by_id(data.assigned_employee_id) is None:
        raise AppError("not_found", "Назначенный сотрудник не зарегистрирован.")
    if await users.get_by_id(data.created_by) is None:
        raise AppError("not_found", "Создатель заказа не зарегистрирован.")
    if await session.get(Services, data.service_id) is None:
        raise AppError("not_found", "Услуга не найдена.")
    now = datetime.now(timezone.utc)
    order = Orders(
        **data.model_dump(), status=Status.NEW, created_at=now, updated_at=now
    )
    session.add(order)
    await session.commit()
    return await get_order(session, order.id)


async def change_status(
    session: AsyncSession,
    order_id: int,
    telegram_id: int,
    expected: Status,
    target: Status,
) -> OrderSchema:
    order = await get_employee_order(session, order_id, telegram_id)
    if order.status != expected:
        raise AppError(
            "conflict", "Статус уже изменён. Откройте заказ заново командой /order."
        )
    if target not in TRANSITIONS[expected]:
        raise AppError("conflict", "Такой переход статуса недоступен.")
    changed = await OrderRepo(session).update_status(
        order_id,
        order.assigned_employee_id,
        expected,
        target,
    )
    if not changed:
        await session.rollback()
        raise AppError("conflict", "Статус уже изменён. Откройте заказ заново.")
    await session.commit()
    return await get_order(session, order_id)
