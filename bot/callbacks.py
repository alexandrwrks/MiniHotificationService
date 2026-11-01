from aiogram.filters.callback_data import CallbackData
from pydantic import Field

from database.enum import OrderStatusType


class OrderStatusCallback(CallbackData, prefix="order"):
    order_id: int = Field(gt=0)
    expected: OrderStatusType
    target: OrderStatusType


class OrderViewCallback(CallbackData, prefix="view"):
    order_id: int = Field(gt=0)


class OrderListCallback(CallbackData, prefix="orders"):
    page: int = Field(ge=0, le=100000)
    archived: bool = False
