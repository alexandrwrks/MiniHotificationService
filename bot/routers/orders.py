from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.callbacks import OrderListCallback, OrderStatusCallback, OrderViewCallback
from bot.presentation import PAGE_SIZE, order_keyboard, order_list, order_text
from common.errors import AppError
from orders.service import change_status, get_employee_order, list_employee_orders

router = Router(name="orders")


async def edit_card(callback: CallbackQuery, text: str, keyboard):
    if not isinstance(callback.message, Message):
        await callback.answer("Откройте заказ заново через /orders.", show_alert=True)
        return
    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest as error:
        if "message is not modified" not in error.message:
            await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.message(Command("orders", "history"))
async def show_orders(message: Message, command: CommandObject, session: AsyncSession):
    archived = command.command == "history"
    orders = await list_employee_orders(
        session, message.from_user.id, 0, PAGE_SIZE, archived
    )
    text, keyboard = order_list(orders, 0, archived)
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(OrderListCallback.filter())
async def browse_orders(
    callback: CallbackQuery, callback_data: OrderListCallback, session: AsyncSession
):
    orders = await list_employee_orders(
        session,
        callback.from_user.id,
        callback_data.page,
        PAGE_SIZE,
        callback_data.archived,
    )
    text, keyboard = order_list(orders, callback_data.page, callback_data.archived)
    await edit_card(callback, text, keyboard)


@router.message(Command("order"))
async def show_order(message: Message, command: CommandObject, session: AsyncSession):
    if not command.args or not command.args.isdecimal() or int(command.args) <= 0:
        raise AppError("invalid", "Укажите номер заказа, например: /order 123")
    order = await get_employee_order(session, int(command.args), message.from_user.id)
    await message.answer(order_text(order), reply_markup=order_keyboard(order))


@router.callback_query(OrderViewCallback.filter())
async def open_order(
    callback: CallbackQuery, callback_data: OrderViewCallback, session: AsyncSession
):
    order = await get_employee_order(
        session, callback_data.order_id, callback.from_user.id
    )
    await edit_card(callback, order_text(order), order_keyboard(order))


@router.callback_query(OrderStatusCallback.filter())
async def update_order(
    callback: CallbackQuery, callback_data: OrderStatusCallback, session: AsyncSession
):
    order = await change_status(
        session,
        callback_data.order_id,
        callback.from_user.id,
        callback_data.expected,
        callback_data.target,
    )
    # The saved status remains valid even if Telegram cannot update this card.
    await edit_card(callback, order_text(order), order_keyboard(order))
