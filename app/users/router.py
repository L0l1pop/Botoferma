from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Annotated

from app.users.auth import authenticate_user, create_access_token, get_current_user
from app.database import get_session
from app.users import crud
from app.users.models import User
from app.users.schemas import AcquireLockRequest, ReleaseLockRequest, Token,UserCreate, UserLogin, UserResponse


router = APIRouter(prefix="/api", tags=["users"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, session: Annotated[AsyncSession, Depends(get_session)]) -> User:
    """
    Регистрирует нового пользователя.
    
    Args:
        user_data: Данные нового пользователя
        session: Сессия базы данных
        
    Returns:
        User: Созданный пользователь
        
    Raises:
        HTTPException 400: Если пользователь с таким email уже существует
    """
    try:
        user: User = await crud.create_user(session, user_data)
        return user
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, session: Annotated[AsyncSession, Depends(get_session)]) -> Token:
    """
    Аутентифицирует пользователя и возвращает JWT токен.
    
    Args:
        user_data: Email и пароль пользователя
        session: Сессия базы данных
        
    Returns:
        Token: JWT токен для доступа к защищенным эндпоинтам
        
    Raises:
        HTTPException 401: Если email или пароль неверны
    """
    user: User | None = await authenticate_user(
        session, 
        user_data.login, 
        user_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token: str = create_access_token(data={"sub": user.login})
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """
    Возвращает информацию о текущем аутентифицированном пользователе.
    
    Args:
        current_user: Текущий пользователь из JWT токена
        
    Returns:
        User: Данные пользователя
    """
    return current_user


@router.get("/users", response_model=list[UserResponse])
async def get_users(session: Annotated[AsyncSession, Depends(get_session)], current_user: Annotated[User, Depends(get_current_user)]) -> list[User]:
    """
    Возвращает список всех пользователей (требуется аутентификация).
    
    Args:
        session: Сессия базы данных
        current_user: Текущий пользователь (для проверки аутентификации)
        
    Returns:
        list[User]: Список всех пользователей
    """
    users: list[User] = await crud.get_all_users(session)
    return users


@router.post("/users/acquire", response_model=UserResponse)
async def acquire_user_lock(request: AcquireLockRequest, session: Annotated[AsyncSession, Depends(get_session)], current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """
    Блокирует пользователя для E2E-теста.
    
    Args:
        request: UUID пользователя для блокировки
        session: Сессия базы данных
        current_user: Текущий пользователь (для проверки аутентификации)
        
    Returns:
        User: Заблокированный пользователь с установленным locktime
        
    Raises:
        HTTPException 404: Если пользователь не найден
        HTTPException 423: Если пользователь уже заблокирован
    """
    user: User | None = await crud.acquire_lock(session, request.user_id)
    
    if user is None:
        existing_user = await crud.get_user_by_id(session, request.user_id)
        if existing_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="User is already locked by another test"
            )
    
    return user


@router.post("/users/release", response_model=UserResponse)
async def release_user_lock(request: ReleaseLockRequest, session: Annotated[AsyncSession, Depends(get_session)], current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """
    Разблокирует пользователя после завершения E2E-теста.
    
    Args:
        request: UUID пользователя для разблокировки
        session: Сессия базы данных
        current_user: Текущий пользователь (для проверки аутентификации)
        
    Returns:
        User: Разблокированный пользователь с locktime = None
        
    Raises:
        HTTPException 404: Если пользователь не найден
    """
    user: User | None = await crud.release_lock(session, request.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user