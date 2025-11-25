from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings
from app.database import get_session
from app.users import crud
from app.users.models import User
from app.users.schemas import TokenData


security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT access token.
    
    Args:
        data: Данные для кодирования в токен
        expires_delta: Время жизни токена
        
    Returns:
        str: Закодированный JWT токен
    """
    to_encode: dict = data.copy()
    
    if expires_delta:
        expire: datetime = datetime.now(timezone.utc) + expires_delta
    else:
        expire: datetime = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Декодирует и валидирует JWT токен.
    
    Args:
        token: JWT токен
        
    Returns:
        Optional[TokenData]: Данные из токена или None если токен невалиден
    """
    try:
        payload: dict = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        login: Optional[str] = payload.get("sub")
        
        if login is None:
            return None
        
        return TokenData(login=login)
    except JWTError:
        return None


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), session: AsyncSession = Depends(get_session)) -> User:
    """
    Dependency для получения текущего аутентифицированного пользователя.
    
    Извлекает JWT токен из заголовка Authorization,
    валидирует его и возвращает пользователя из БД.
    
    Args:
        credentials: HTTP Bearer credentials из заголовка
        session: Асинхронная сессия БД
        
    Returns:
        User: Текущий аутентифицированный пользователь
        
    Raises:
        HTTPException: 401 если токен невалиден или пользователь не найден
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token: str = credentials.credentials
    token_data: Optional[TokenData] = decode_access_token(token)
    
    if token_data is None or token_data.login is None:
        raise credentials_exception
    
    user: Optional[User] = await crud.get_user_by_login(session, login=token_data.login)
    
    if user is None:
        raise credentials_exception
    
    return user


async def authenticate_user(session: AsyncSession, login: str, password: str) -> Optional[User]:
    """
    Аутентифицирует пользователя по логину и паролю.
    
    Args:
        session: Асинхронная сессия БД
        login: Email пользователя
        password: Пароль в открытом виде
        
    Returns:
        Optional[User]: Пользователь если аутентификация успешна, иначе None
    """
    from app.users.utils import verify_password
    
    user: Optional[User] = await crud.get_user_by_login(session, login)
    
    if not user:
        return None
    
    if not verify_password(password, user.password):
        return None
    
    return user