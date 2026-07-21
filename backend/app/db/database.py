"""
Async SQLAlchemy database engine and session factory.
Uses aioodbc for SQL Server (MSSQL) connections.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus
import os

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_BACKEND_ROOT / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "1433")
DB_USER = os.getenv("DB_USER", "sa")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "brand_builder")
DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")

_odbc_params = quote_plus(
    f"DRIVER={{{DB_DRIVER}}};SERVER={DB_HOST},{DB_PORT};DATABASE={DB_NAME};"
    f"UID={DB_USER};PWD={DB_PASSWORD}"
)
DATABASE_URL = f"mssql+aioodbc:///?odbc_connect={_odbc_params}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """FastAPI dependency – yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (for development bootstrapping)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
