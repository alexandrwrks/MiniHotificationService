from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database.config import get_async_session
from users.schema import UsersRequestSchema
from users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", status_code=201)
async def create_user(
    data: UsersRequestSchema, session: AsyncSession = Depends(get_async_session)
):
    return await UserService(session).create_user(data)
