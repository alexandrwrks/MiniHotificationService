from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from common.errors import AppError
from database.models import Users
from users.repo import UserRepo
from users.schema import UsersRequestSchema


class UserService:
    def __init__(self, session: AsyncSession):
        self.db = session
        self.repo = UserRepo(session)

    async def create_user(self, params: UsersRequestSchema):
        try:
            if await self.repo.get_by_telegram_id(params.telegram_id):
                raise AppError("conflict", "Пользователь Telegram уже зарегистрирован.")
            user_id = await self.repo.create_user(params)
            await self.db.commit()
            return {
                "user_id": user_id,
                "telegram_id": params.telegram_id,
                "status": "success",
            }
        except IntegrityError as exc:
            await self.db.rollback()
            raise AppError(
                "conflict", "Пользователь Telegram уже зарегистрирован."
            ) from exc

    async def register(self, params: UsersRequestSchema) -> Users:
        user = await self.repo.get_by_telegram_id(params.telegram_id)
        if user is None:
            try:
                await self.create_user(params)
            except AppError as exc:
                if exc.code != "conflict":
                    raise
            user = await self.repo.get_by_telegram_id(params.telegram_id)
        if user is None:
            raise AppError(
                "conflict", "Не удалось зарегистрироваться. Повторите /start."
            )
        return user
