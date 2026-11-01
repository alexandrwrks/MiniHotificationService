from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServiceCreateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=255)
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class ServiceSchema(ServiceCreateSchema):
    model_config = ConfigDict(from_attributes=True)
    id: int
