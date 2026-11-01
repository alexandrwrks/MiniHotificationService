from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from loguru import logger

from common.errors import AppError
from database.config import new_session


class SessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with new_session() as session:
            data["session"] = session
            try:
                return await handler(event, data)
            except AppError as error:
                await session.rollback()
                text = error.message
            except Exception:
                await session.rollback()
                logger.exception("Ошибка обработки команды Telegram")
                text = "Не удалось выполнить действие. Попробуйте ещё раз или откройте /help."
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
        else:
            await event.answer(text)
