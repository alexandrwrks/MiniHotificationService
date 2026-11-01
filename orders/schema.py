from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from database.enum import OrderStatusType


class OrderCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    service_id: int = Field(gt=0)
    created_by: int = Field(gt=0)
    assigned_employee_id: int = Field(gt=0)


class OrderSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int = Field(gt=0)
    service_id: int
    service_name: str
    status: OrderStatusType
    created_by: int
    assigned_employee_id: int
    created_at: datetime
    updated_at: datetime


class SendOrderSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: int = Field(gt=0)
