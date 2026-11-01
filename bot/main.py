import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, MenuButtonCommands

from bot.middleware import SessionMiddleware
from bot.routers import account, fallback, orders
from database.config import engine
from utils.settings import settings

COMMANDS = [
    BotCommand(command="orders", description="📋 Мои активные заказы"),
    BotCommand(command="history", description="🗂 История заказов"),
    BotCommand(command="order", description="🔎 Открыть заказ по номеру"),
    BotCommand(command="profile", description="👤 Мой профиль"),
    BotCommand(command="help", description="❓ Помощь"),
    BotCommand(command="start", description="👋 Начать работу"),
]


async def start_bot():
    logging.basicConfig(level=logging.INFO)
    dp = Dispatcher()
    private = Router(name="private")
    private.message.filter(F.chat.type == "private", F.from_user)
    private.callback_query.filter(F.message.chat.type == "private")
    private.message.middleware(SessionMiddleware())
    private.callback_query.middleware(SessionMiddleware())
    private.include_routers(account.router, orders.router)
    dp.include_router(private)

    dp.include_router(fallback.router)

    try:
        async with Bot(
            settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        ) as bot:
            await bot.set_my_commands(COMMANDS)
            await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
            await dp.start_polling(bot)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(start_bot())
