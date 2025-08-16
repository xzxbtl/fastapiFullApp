from sqlalchemy import select
from bot.logs.logg import logger
from PetProject.src.models.bot_users import BotUsers, BotAdminUsers
from shared.database import Session


async def add_user(user_id):
    async with Session() as session:
        result = await session.execute(select(BotUsers).where(BotUsers.user_id == user_id).with_for_update())
        user = result.scalar_one_or_none()

        if user is None:
            user = BotUsers(user_id=user_id)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def get_admin_bot_users():
    async with Session() as session:
        query = await session.execute(select(BotAdminUsers.user_id).with_for_update())
        admins_ids = query.scalars().all()

        if not admins_ids:
            logger.error("Admin BotUsers not found")
            return

        return admins_ids


async def get_bot_users():
    async with Session() as session:
        query = await session.execute(select(BotUsers.user_id).with_for_update())
        BotUsers_ids = query.scalars().all()

        if not BotUsers_ids:
            logger.error("BotUsers not found")
            return

        return BotUsers_ids
