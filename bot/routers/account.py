from html import escape

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.presentation import HELP_TEXT, home_keyboard
from common.errors import AppError
from users.repo import UserRepo
from users.schema import UsersRequestSchema
from users.service import UserService

router = Router(name="account")


@router.message(CommandStart())
async def register(message: Message, session: AsyncSession):
    user = await UserService(session).register(
        UsersRequestSchema(
            username=message.from_user.username or message.from_user.full_name,
            telegram_id=message.from_user.id,
        )
    )
    await message.answer(
        f"<b>Добро пожаловать, {escape(user.username)}!</b>\n\n"
        f"Ваш ID сотрудника: <code>{user.id}</code>\n"
        "Новые назначения будут приходить сюда. "
        "Открывайте заказ и обновляйте его статус кнопками под карточкой.\n\n"
        "Выберите раздел ниже или откройте /help.",
        reply_markup=home_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(HELP_TEXT, reply_markup=home_keyboard())


@router.message(Command("profile"))
async def profile(message: Message, session: AsyncSession):
    user = await UserRepo(session).get_by_telegram_id(message.from_user.id)
    if user is None:
        raise AppError("forbidden", "Для регистрации отправьте /start.")
    await message.answer(
        f"<b>👤 Мой профиль</b>\n\nИмя: {escape(user.username)}\n"
        f"ID сотрудника: <code>{user.id}</code>\n"
        f"Telegram ID: <code>{user.telegram_id}</code>",
        reply_markup=home_keyboard(),
    )
