from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifecycle manager для FastAPI приложения.
    
    Args:
        app: Экземпляр FastAPI приложения
        
    Yields:
        None
    """
    try:
        from app.database import init_db
        await init_db()
    except Exception as e:
        print(f"Database init skipped: {e}")
    
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(users_router)