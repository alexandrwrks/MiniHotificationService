from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.enum import OrderStatusType
from database.models import Orders, Services
from orders.schema import OrderSchema


class OrderRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _query():
        return select(
            Orders.id,
            Orders.service_id,
            Services.name.label("service_name"),
            Orders.status,
            Orders.created_by,
            Orders.assigned_employee_id,
            Orders.created_at,
            Orders.updated_at,
        ).join(Services, Orders.service_id == Services.id)

    async def get(self, order_id: int) -> OrderSchema | None:
        row = (
            (await self.session.execute(self._query().where(Orders.id == order_id)))
            .mappings()
            .one_or_none()
        )
        return OrderSchema.model_validate(row) if row else None

    async def list_for_employee(
        self,
        employee_id: int,
        statuses: tuple[OrderStatusType, ...],
        offset: int,
        limit: int,
    ) -> list[OrderSchema]:
        rows = (
            await self.session.execute(
                self._query()
                .where(
                    Orders.assigned_employee_id == employee_id,
                    Orders.status.in_(statuses),
                )
                .order_by(Orders.created_at.desc(), Orders.id.desc())
                .offset(offset)
                .limit(limit)
            )
        ).mappings()
        return [OrderSchema.model_validate(row) for row in rows]

    async def update_status(
        self,
        order_id: int,
        employee_id: int,
        expected: OrderStatusType,
        target: OrderStatusType,
    ) -> bool:
        result = await self.session.execute(
            update(Orders)
            .where(
                Orders.id == order_id,
                Orders.assigned_employee_id == employee_id,
                Orders.status == expected,
            )
            .values(status=target, updated_at=datetime.now(timezone.utc))
            .execution_options(synchronize_session=False)
        )
        return result.rowcount == 1
