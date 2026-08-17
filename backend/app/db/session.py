"""
Database session management for SQLAlchemy async operations.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from loguru import logger

from sqlalchemy.pool import NullPool

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development" and settings.DEBUG),
    connect_args={"check_same_thread": False, "timeout": 30} if "sqlite" in settings.DATABASE_URL else {},
    poolclass=NullPool
)

                                  
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def init_db() -> None:
    """
    Initializes the database by creating all tables.
    """
    from app.db.base import Base
    import app.db.models
    from sqlalchemy import select
    from app.core.security import get_password_hash

    try:
        from sqlalchemy import text
        async with engine.begin() as conn:
            if "sqlite" in settings.DATABASE_URL:
                await conn.execute(text("PRAGMA journal_mode=WAL;"))
                await conn.execute(text("PRAGMA busy_timeout=10000;"))
            await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(app.db.models.User).filter_by(email="admin@vizage.local"))
            admin_user = result.scalars().first()
            if not admin_user:
                new_admin = app.db.models.User(
                    email="admin@vizage.local",
                    hashed_password=get_password_hash("admin")
                )
                session.add(new_admin)
                await session.commit()
                logger.info("Created default admin user (admin@vizage.local)")

        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency generator for FastAPI routes to obtain a database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
