from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import TypeDecorator, CHAR


class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID as PGUUID
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, UUID):
                return value
            else:
                return UUID(value)


class Base(DeclarativeBase):
    pass


class DomainType(str, Enum):
    CANARY = "canary"
    REGULAR = "regular"


class Environment(str, Enum):
    PROD = "prod"
    PREPROD = "preprod"
    STAGE = "stage"


class User(Base):
    """
    Модель пользователя ботофермы.
    
    Attributes:
        id: Уникальный идентификатор пользователя
        created_at: Дата и время создания пользователя
        login: Логин (email) пользователя
        password: Хешированный пароль
        project_id: ID проекта, к которому принадлежит пользователь
        env: Окружение (prod, preprod, stage)
        domain: Тип домена (canary, regular)
        locktime: Временная метка блокировки для E2E-теста
    """
    
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid4,
        index=True,
        doc="Уникальный идентификатор пользователя"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Дата создания пользователя"
    )
    
    login: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Логин пользователя (email)"
    )
    
    password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Хешированный пароль пользователя"
    )
    
    project_id: Mapped[UUID] = mapped_column(
        GUID,
        index=True,
        nullable=False,
        doc="UUID проекта, к которому принадлежит пользователь"
    )
    
    env: Mapped[str] = mapped_column(
        nullable=False,
        doc="Окружение развертывания"
    )
    
    domain: Mapped[str] = mapped_column(
        nullable=False,
        doc="Тип домена"
    )
    
    locktime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        default=None,
        doc="Временная метка блокировки пользователя для теста"
    )