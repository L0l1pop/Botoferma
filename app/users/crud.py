from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User
from app.users.schemas import UserCreate
from app.users.utils import hash_password


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """
    Создает нового пользователя в базе данных.
    
    Args:
        session: Асинхронная сессия БД
        user_data: Данные для создания пользователя
        
    Returns:
        User: Созданный пользователь
        
    Raises:
        IntegrityError: Если пользователь с таким login уже существует
    """
    hashed_password: str = hash_password(user_data.password)
    
    user: User = User(
        login=user_data.login,
        password=hashed_password,
        project_id=user_data.project_id,
        env=user_data.env.value,
        domain=user_data.domain.value
    )
    
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_login(session: AsyncSession, login: str) -> Optional[User]:
    """
    Получает пользователя по логину (email).
    
    Args:
        session: Асинхронная сессия БД
        login: Email пользователя
        
    Returns:
        Optional[User]: Пользователь или None если не найден
    """
    result = await session.execute(select(User).where(User.login == login))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Получает пользователя по UUID.
    
    Args:
        session: Асинхронная сессия БД
        user_id: UUID пользователя
        
    Returns:
        Optional[User]: Пользователь или None если не найден
    """
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_users(session: AsyncSession) -> list[User]:
    """
    Получает список всех пользователей.
    
    Args:
        session: Асинхронная сессия БД
        
    Returns:
        list[User]: Список всех пользователей
    """
    result = await session.execute(select(User))
    return list(result.scalars().all())


async def acquire_lock(session: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Блокирует пользователя для E2E-теста.
    
    Устанавливает locktime в текущее время, если пользователь свободен.
    Пользователь считается занятым, если locktime не None.
    
    Args:
        session: Асинхронная сессия БД
        user_id: UUID пользователя для блокировки
        
    Returns:
        Optional[User]: Заблокированный пользователь или None если:
            - пользователь не найден
            - пользователь уже заблокирован
    """
    user: Optional[User] = await get_user_by_id(session, user_id)
    
    if not user:
        return None
    
    if user.locktime is not None:
        return None
    
    user.locktime = datetime.utcnow()
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def release_lock(session: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Разблокирует пользователя после завершения E2E-теста.
    
    Устанавливает locktime в None.
    
    Args:
        session: Асинхронная сессия БД
        user_id: UUID пользователя для разблокировки
        
    Returns:
        Optional[User]: Разблокированный пользователь или None если не найден
    """
    user: Optional[User] = await get_user_by_id(session, user_id)
    
    if not user:
        return None
    
    user.locktime = None
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user