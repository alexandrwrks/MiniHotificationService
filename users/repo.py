from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Users
from users.schema import UsersRequestSchema


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Users | None:
        return await self.session.get(Users, user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> Users | None:
        return await self.session.scalar(
            select(Users).where(Users.telegram_id == telegram_id)
        )

    async def create_user(self, params: UsersRequestSchema) -> int:
        result = await self.session.execute(
            insert(Users).values(**params.model_dump()).returning(Users.id)
        )
        return result.scalar_one()
