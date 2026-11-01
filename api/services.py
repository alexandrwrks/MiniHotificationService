from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_async_session
from services.schema import ServiceCreateSchema, ServiceSchema
from services.service import create_service

router = APIRouter(prefix="/services", tags=["Services"])


@router.post("", response_model=ServiceSchema, status_code=201)
async def create_service_route(
    data: ServiceCreateSchema, session: AsyncSession = Depends(get_async_session)
):
    return await create_service(session, data)
