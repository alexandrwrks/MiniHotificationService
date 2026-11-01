from html import escape

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.callbacks import OrderListCallback, OrderStatusCallback, OrderViewCallback
from database.enum import OrderStatusType as Status
from orders.schema import OrderSchema
from orders.status import TRANSITIONS

PAGE_SIZE = 5
STATUS_LABELS = {
    Status.NEW: "🆕 Новый",
    Status.ASSIGNED: "📌 Принят",
    Status.IN_PROGRESS: "🔧 В работе",
    Status.COMPLETED: "✅ Выполнен",
    Status.CANCELED: "❌ Отменён",
}
ACTION_LABELS = {
    Status.ASSIGNED: "📌 Принять заказ",
    Status.IN_PROGRESS: "🔧 Начать работу",
    Status.COMPLETED: "✅ Завершить",
    Status.CANCELED: "❌ Отменить заказ",
}
HELP_TEXT = (
    "<b>Помощник по заказам</b>\n\n"
    "Здесь вы получаете назначения и отмечаете ход работы.\n\n"
    "/orders — мои активные заказы\n"
    "/history — выполненные и отменённые\n"
    "/order 123 — открыть заказ по номеру\n"
    "/profile — профиль и ID сотрудника\n"
    "/help — эта справка\n\n"
    "Откройте карточку заказа и выберите действие под сообщением. "
    "Менять статус может только назначенный сотрудник.\n"
    "Время в карточках указано в UTC."
)


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 Мои заказы", callback_data=OrderListCallback(page=0).pack()
                ),
                InlineKeyboardButton(
                    text="🗂 История",
                    callback_data=OrderListCallback(page=0, archived=True).pack(),
                ),
            ]
        ]
    )


def order_text(order: OrderSchema) -> str:
    return (
        f"<b>Заказ №{order.id}</b>\n\n"
        f"<b>Услуга:</b> {escape(order.service_name)}\n"
        f"<b>Статус:</b> {STATUS_LABELS[order.status]}\n"
        f"<b>Создан:</b> {order.created_at:%d.%m.%Y %H:%M} UTC\n"
        f"<b>Обновлён:</b> {order.updated_at:%d.%m.%Y %H:%M} UTC"
    )


def order_keyboard(order: OrderSchema) -> InlineKeyboardMarkup | None:
    rows = [
        [
            InlineKeyboardButton(
                text=ACTION_LABELS[target],
                callback_data=OrderStatusCallback(
                    order_id=order.id, expected=order.status, target=target
                ).pack(),
            )
        ]
        for target in TRANSITIONS[order.status]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


def order_list(orders: list[OrderSchema], page: int, archived: bool):
    title = "🗂 История заказов" if archived else "📋 Мои активные заказы"
    text = f"<b>{title}</b>\n\n"
    rows = []
    for order in orders[:PAGE_SIZE]:
        text += f"<b>№{order.id}</b> · {escape(order.service_name)}\n{STATUS_LABELS[order.status]}\n\n"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"Открыть заказ №{order.id}",
                    callback_data=OrderViewCallback(order_id=order.id).pack(),
                )
            ]
        )
    if not orders:
        text += "Здесь пока нет заказов."
    else:
        text += f"Страница {page + 1} · выберите заказ ниже."
    navigation = []
    if page:
        navigation.append(
            InlineKeyboardButton(
                text="← Назад",
                callback_data=OrderListCallback(
                    page=page - 1, archived=archived
                ).pack(),
            )
        )
    if len(orders) > PAGE_SIZE:
        navigation.append(
            InlineKeyboardButton(
                text="Далее →",
                callback_data=OrderListCallback(
                    page=page + 1, archived=archived
                ).pack(),
            )
        )
    if navigation:
        rows.append(navigation)
    return text, InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
