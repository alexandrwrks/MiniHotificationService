from aiogram import Router
from aiogram.types import CallbackQuery, Message

router = Router(name="fallback")


@router.message()
async def unknown_message(message: Message):
    text = "Выберите команду в меню или откройте /help."
    if message.chat.type != "private":
        text = "Для работы с заказами откройте личный чат со мной и отправьте /start."
    await message.answer(text)


@router.callback_query()
async def outdated_button(callback: CallbackQuery):
    await callback.answer(
        "Эта кнопка недоступна. Откройте /orders заново.", show_alert=True,
    )
