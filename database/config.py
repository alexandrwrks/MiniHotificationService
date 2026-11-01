from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from utils.settings import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

new_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_async_session():
    async with new_session() as session:
        yield session


async def init_db():
    from database.models import Base

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
