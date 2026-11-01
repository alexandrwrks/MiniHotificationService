from aio_pika.abc import AbstractIncomingMessage
from aiogram import Bot

from bot.presentation import order_keyboard, order_text
from common.errors import AppError
from database.config import new_session
from messaging.schema import EventDataSchema
from orders.service import get_order
from users.repo import UserRepo
from utils.log import rabbitmq_logger


async def process_order(message: AbstractIncomingMessage, bot: Bot):
    async with message.process():
        try:
            event = EventDataSchema.model_validate_json(message.body)
            async with new_session() as session:
                order = await get_order(session, event.order.id)
                employee = await UserRepo(session).get_by_id(order.assigned_employee_id)
                if employee is None:
                    raise AppError("not_found", "Назначенный сотрудник не найден.")
                telegram_id = employee.telegram_id
            await bot.send_message(
                chat_id=telegram_id,
                text=order_text(order),
                reply_markup=order_keyboard(order),
            )
        except Exception:
            rabbitmq_logger.exception("Не удалось обработать уведомление о заказе")
            raise
