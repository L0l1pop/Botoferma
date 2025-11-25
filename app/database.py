from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.users.models import Base


def init_engine() -> AsyncEngine:
    global engine
    if engine is None:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True
        )
    return engine


def init_session_maker() -> sessionmaker:
    global async_session_maker
    if async_session_maker is None:
        async_session_maker = sessionmaker(
            init_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return async_session_maker


async def init_db() -> None:
    engine = init_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session_maker = init_session_maker()
    async with session_maker() as session:
        yield session