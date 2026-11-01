from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from orders.schema import OrderSchema


class EventDataSchema(BaseModel):
    schema_version: Literal[1] = 1
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event: Literal["order.created", "order.notification_requested"]
    order: OrderSchema
