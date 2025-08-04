import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from PetProject.src.base.main.config import settings
from fastapi import Request
from redis import Redis

if sys.platform.startswith('win') and os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

engine = create_async_engine(
    settings.DataBase_URL_psycopg,
    echo=False,
    pool_size=5,
    max_overflow=10,
)
Session = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()


async def setup_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    return "Base Table Created"


async def get_session():
    async with Session() as session:
        yield session


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis
