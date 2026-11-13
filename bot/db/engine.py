from colorama import Fore
from sqlalchemy import MetaData
from sqlalchemy.engine import URL
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

host = os.getenv('POSTGRES_HOST') or "localhost"
port = os.getenv('POSTGRES_PORT') or 5432
print(f'{Fore.BLACK}host :::{Fore.BLUE} {host}:{port} {Fore.BLACK}\n');

def _db_url() -> URL:
    return URL.create(
        "postgresql+asyncpg",
        username=os.getenv('POSTGRES_USER'),
        host=host,
        database=os.getenv("POSTGRES_DB"),
        password=os.getenv('POSTGRES_PASSWORD'),
        port=port,
    )

def get_engine() -> AsyncEngine:
    DB_URL = _db_url()

    # echo - show SQL queries, pool_pre_ping - check connection before use
    return create_async_engine(DB_URL, echo=False, pool_pre_ping=True)

async def procceed_shemas(engine: AsyncEngine, metadata: MetaData) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(metadata.create_all)

# One engine (one connection pool) per process. Previously every session_maker()
# call created a NEW engine with its own pool that was never disposed, so a burst of
# updates (e.g. 65 group migrations at once) exhausted Postgres max_connections.
_engine: AsyncEngine | None = None

def get_shared_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _db_url(), echo=False, pool_pre_ping=True,
            pool_size=10, max_overflow=10, pool_timeout=60,
        )
    return _engine

def session_maker() -> AsyncSession:
    return AsyncSession(get_shared_engine(), expire_on_commit=False)
