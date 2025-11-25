from datetime import datetime
from typing import Optional, Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict, StringConstraints

from app.users.models import DomainType, Environment


class UserBase(BaseModel):
    """
    Базовая схема пользователя с общими полями.
    
    Attributes:
        login: Email пользователя
        project_id: UUID проекта
        env: Окружение
        domain: Тип домена
    """
    
    login: EmailStr
    project_id: UUID
    env: Environment
    domain: DomainType


class UserCreate(UserBase):
    """
    Схема для создания нового пользователя.
    
    Attributes:
        password: Пароль (минимум 8 символов, будет захеширован)
    """
    
    password: Annotated[str, StringConstraints(min_length=8)]


class UserResponse(BaseModel):
    """
    Схема ответа с данными пользователя (без пароля).
    
    Attributes:
        id: UUID пользователя
        created_at: Дата создания
        login: Email пользователя
        project_id: UUID проекта
        env: Окружение
        domain: Тип домена
        locktime: Временная метка блокировки
    """
    
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    created_at: datetime
    login: str
    project_id: UUID
    env: str
    domain: str
    
    locktime: Optional[datetime] = Field(default=None)


class AcquireLockRequest(BaseModel):
    """
    Схема запроса на блокировку пользователя.
    
    Attributes:
        user_id: UUID пользователя для блокировки
    """
    
    user_id: UUID


class ReleaseLockRequest(BaseModel):
    """
    Схема запроса на разблокировку пользователя.
    
    Attributes:
        user_id: UUID пользователя для разблокировки
    """
    
    user_id: UUID

class UserLogin(BaseModel):
    """
    Схема для аутентификации пользователя.
    
    Attributes:
        login: Email пользователя
        password: Пароль пользователя
    """
    
    login: EmailStr
    password: str

class Token(BaseModel):
    """
    Схема JWT токена.
    
    Attributes:
        access_token: JWT токен доступа
        token_type: Тип токена (bearer)
    """
    
    access_token: str
    token_type: str = Field(default="bearer")


class TokenData(BaseModel):
    """
    Схема данных из JWT токена.
    
    Attributes:
        login: Email пользователя из токена
    """
    
    login: Optional[EmailStr] = Field(default=None)