import asyncio
import os
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from PetProject.src.base.main.config import settings
from fastapi import Request
from redis import Redis
from PetProject.src.utils.logs.logs import logger
from PetProject.src.models.bot_users import BotUsers, BotAdminUsers
from .base import Base


if sys.platform.startswith('win') and os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


engine = create_async_engine(
    settings.DataBase_URL_psycopg,
    echo=False,
    pool_size=5,
    max_overflow=10,
)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def create_admins_bot_users():
    async with Session() as session:
        default_admin = {
            "user_id": 745409469,
            "email": "xzxbtl@mail.ru"
        }
        existing_admin = await session.execute(
            select(BotAdminUsers).with_for_update()
        )
        existing_admin = existing_admin.scalars().one_or_none()

        if not existing_admin:
            logger.info(f"Creating admin user with email: {default_admin.get('email')}")
            try:
                admin = BotAdminUsers(
                    user_id=default_admin.get('user_id'),
                    email=default_admin.get('email'),
                    admin_level=3
                )
                session.add(admin)
                await session.commit()
                await session.refresh(admin)
                logger.info(f"Admin user with: {default_admin.get('email')} created successfully.")

            except Exception as e:
                logger.error(f"Error Creating admin user - {e}")
        else:
            logger.debug(f"Already existing admin user with: {default_admin.get('email')}")


async def setup_database():
    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            logger.debug("Database setup successfully.")
            return True
        except Exception as e:
            logger.error(f"Database creation failed: {e}", exc_info=True)
            return False


async def get_session():
    async with Session() as session:
        yield session


async def get_redis(request: Request) -> Redis:
    return request.app.state.redis
