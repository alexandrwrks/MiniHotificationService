"""Run explicitly inside Compose; uses and removes an isolated PostgreSQL schema."""
import asyncio
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.models import Base, Users, Services
from database.enum import OrderStatusType as Status
from orders.service import create_order, change_status
from orders.schema import OrderCreateSchema
from utils.settings import settings


async def main():
    schema = "verify_orders_" + uuid4().hex
    admin = create_async_engine(settings.DATABASE_URL)
    async with admin.begin() as connection:
        await connection.execute(text(f"CREATE SCHEMA {schema}"))
    engine = create_async_engine(settings.DATABASE_URL,
        connect_args={"server_settings": {"search_path": schema}})
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        sessions = async_sessionmaker(engine, expire_on_commit=False)
        async with sessions() as session:
            user = Users(username="verification", telegram_id=9999999999)
            service = Services(name="Verification", price=100)
            session.add_all([user, service])
            await session.commit()
            order = await create_order(session, OrderCreateSchema(service_id=service.id,
                created_by=user.id, assigned_employee_id=user.id))
            order = await change_status(session, order.id, user.telegram_id, Status.NEW, Status.IN_PROGRESS)
            order = await change_status(session, order.id, user.telegram_id, Status.IN_PROGRESS, Status.COMPLETED)
            assert order.status == Status.COMPLETED
            print("PostgreSQL: order creation and status changes OK")
    finally:
        await engine.dispose()
        async with admin.begin() as connection:
            await connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        await admin.dispose()


if __name__ == "__main__":
    asyncio.run(main())
