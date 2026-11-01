import os
import unittest
from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ["BOT_TOKEN"] = "123456:test_token"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"

from common.errors import AppError
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.models import Base, Services
from users.schema import UsersRequestSchema
from users.service import UserService
from orders.schema import OrderCreateSchema, SendOrderSchema
from messaging.schema import EventDataSchema
from orders.service import create_order, change_status, get_order
from database.enum import OrderStatusType as Status
from bot.presentation import order_keyboard
from pydantic import ValidationError
from api.orders import send_order, create_order_route
from consumer.handler import process_order
from bot.routers.account import register


class IncomingMessage:
    def __init__(self, body):
        self.body = body

    @asynccontextmanager
    async def process(self):
        yield


class NotificationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def create_user(self, telegram_id):
        async with self.sessions() as session:
            return await UserService(session).create_user(
                UsersRequestSchema(username="Employee", telegram_id=telegram_id)
            )

    async def create_order(self, employee_id):
        async with self.sessions() as session:
            service = Services(name="Repair", price=100)
            session.add(service)
            await session.commit()
            return await create_order(session, OrderCreateSchema(
                service_id=service.id, created_by=employee_id, assigned_employee_id=employee_id,
            ))

    async def test_status_changes_and_terminal_order(self):
        employee = await self.create_user(9000000004)
        order = await self.create_order(employee["user_id"])
        async with self.sessions() as session:
            updated = await change_status(session, order.id, 9000000004, Status.NEW, Status.IN_PROGRESS)
            self.assertEqual(updated.status, Status.IN_PROGRESS)
            updated = await change_status(session, order.id, 9000000004, Status.IN_PROGRESS, Status.COMPLETED)
            self.assertEqual(updated.status, Status.COMPLETED)
            self.assertIsNone(order_keyboard(updated))
            with self.assertRaises(AppError) as error:
                await change_status(session, order.id, 9000000004, Status.COMPLETED, Status.NEW)
            self.assertEqual(error.exception.code, "conflict")

    async def test_other_employee_cannot_change_status(self):
        owner = await self.create_user(9000000005)
        await self.create_user(9000000006)
        order = await self.create_order(owner["user_id"])
        async with self.sessions() as session:
            with self.assertRaises(AppError) as error:
                await change_status(session, order.id, 9000000006, Status.NEW, Status.CANCELED)
            self.assertEqual(error.exception.code, "forbidden")
            self.assertEqual((await get_order(session, order.id)).status, Status.NEW)

    async def test_stale_button_does_not_change_status(self):
        owner = await self.create_user(9000000007)
        order = await self.create_order(owner["user_id"])
        async with self.sessions() as session:
            await change_status(session, order.id, 9000000007, Status.NEW, Status.ASSIGNED)
            with self.assertRaises(AppError) as error:
                await change_status(session, order.id, 9000000007, Status.NEW, Status.CANCELED)
            self.assertEqual(error.exception.code, "conflict")

    async def test_creation_schema_rejects_client_status_and_id(self):
        with self.assertRaises(ValidationError):
            OrderCreateSchema(service_id=1, created_by=1, assigned_employee_id=1,
                              id=123, status="COMPLETED")

    async def test_publish_failure_keeps_saved_order(self):
        owner = await self.create_user(9000000008)
        order = await self.create_order(owner["user_id"])
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(order_exchange=object())))
        with patch("messaging.publisher.publish_json", new_callable=AsyncMock, side_effect=RuntimeError("offline")), \
             patch("messaging.publisher.rabbitmq_logger"):
            async with self.sessions() as session:
                with self.assertRaises(AppError) as error:
                    await send_order(SendOrderSchema(order_id=order.id), request, session)
                self.assertEqual(error.exception.code, "unavailable")
                self.assertEqual(error.exception.details["order_id"], order.id)
                self.assertEqual((await get_order(session, order.id)).id, order.id)

    async def test_create_api_saves_order_and_publishes_snapshot(self):
        owner = await self.create_user(9000000009)
        async with self.sessions() as session:
            service = Services(name="Test service", price=50)
            session.add(service)
            await session.commit()
            request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(order_exchange=object())))
            with patch("messaging.publisher.publish_json", new_callable=AsyncMock) as publish:
                order = await create_order_route(OrderCreateSchema(service_id=service.id,
                    created_by=owner["user_id"], assigned_employee_id=owner["user_id"]), request, session)
            self.assertEqual(order.status, Status.NEW)
            event = EventDataSchema.model_validate(publish.call_args.kwargs["data"])
            self.assertEqual(event.event, "order.created")
            self.assertEqual(event.order.id, order.id)
            self.assertEqual(event.order.service_name, "Test service")
            self.assertEqual((await get_order(session, order.id)).id, order.id)

    async def test_duplicate_registration(self):
        await self.create_user(9000000001)
        with self.assertRaises(AppError) as error:
            await self.create_user(9000000001)
        self.assertEqual(error.exception.code, "conflict")

    async def test_notification_goes_only_to_assigned_employee(self):
        await self.create_user(9000000001)
        employee = await self.create_user(9000000002)
        order = await self.create_order(employee["user_id"])
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(order_exchange=object())))
        with patch("messaging.publisher.publish_json", new_callable=AsyncMock) as publish:
            async with self.sessions() as session:
                await send_order(SendOrderSchema(order_id=order.id), request, session)
            event = EventDataSchema.model_validate(publish.call_args.kwargs["data"])
        send = AsyncMock()
        bot = SimpleNamespace(send_message=send)
        with patch("consumer.handler.new_session", self.sessions):
            await process_order(IncomingMessage(event.model_dump_json().encode()), bot)
        send.assert_awaited_once()
        self.assertEqual(send.call_args.kwargs["chat_id"], 9000000002)
        self.assertIn(f"№{order.id}", send.call_args.kwargs["text"])
        self.assertIsNotNone(send.call_args.kwargs["reply_markup"])

    async def test_unknown_employee_is_not_published(self):
        with patch("messaging.publisher.publish_json", new_callable=AsyncMock) as publish:
            async with self.sessions() as session:
                with self.assertRaises(AppError) as error:
                    await create_order(session, OrderCreateSchema(service_id=1, created_by=1, assigned_employee_id=99))
        self.assertEqual(error.exception.code, "not_found")
        publish.assert_not_awaited()

    async def test_start_is_idempotent(self):
        message = SimpleNamespace(
            chat=SimpleNamespace(type="private"),
            from_user=SimpleNamespace(id=9000000003, username="employee", full_name="Employee"),
            answer=AsyncMock(),
        )
        async with self.sessions() as session:
            await register(message, session)
            await register(message, session)
        self.assertEqual(message.answer.await_args_list[0], message.answer.await_args_list[1])


if __name__ == "__main__":
    unittest.main()

