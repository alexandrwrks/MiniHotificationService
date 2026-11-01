from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Services
from services.schema import ServiceCreateSchema


async def create_service(session: AsyncSession, data: ServiceCreateSchema) -> Services:
    service = Services(**data.model_dump())
    session.add(service)
    await session.commit()
    return service
