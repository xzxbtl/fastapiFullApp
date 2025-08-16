import asyncio
import os
from aiogram import Bot, Dispatcher
from datetime import datetime
from aiogram.enums import ParseMode
from bot.logs.logg import logger
from dotenv import load_dotenv
from bot.handlers import start
from broker.broker_service import broker
from bot.base.main.core import get_bot_users, get_admin_bot_users


load_dotenv("bot_settings__.env")
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)


@broker.subscriber("user_actions")
async def handle_messages(data: str):
    task = asyncio.create_task(global_message(data))


async def admin_global_message(data: str):
    ADMIN_IDS = await get_admin_bot_users()
    logger.info(f"Получено админ действие - {data}")
    for user_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=user_id, text=data, parse_mode=ParseMode.MARKDOWN)
            await asyncio.sleep(0.15)
        except Exception as e:
            logger.error(f"Error sending to admin {user_id}: {e}")
    else:
        logger.debug("Рассылка админам - Успешна")


async def global_message(data: str):
    USER_IDS = await get_bot_users()
    logger.info(f"Получено действие пользователя - {data}")
    for user_id in USER_IDS:
        try:
            await bot.send_message(chat_id=user_id, text=data, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Error sending message: {e}")


@broker.subscriber("admin_actions")
async def handle_admin_messages(data: str):
    task = asyncio.create_task(admin_global_message(data))


async def main():
    async with broker:
        dp = Dispatcher()
        dp.include_routers(start.start_router)
        dp["started_at"] = datetime.now().strftime("%d-%m-%Y %H:%M")
        try:
            await broker.start()
        except Exception as e:
            logger.error(f"Error connecting to broker: {e}")

        await dp.start_polling(bot, skip_updates=True)
    logger.error("Брокер закрылся | Бот выключен")


if __name__ == "__main__":
    asyncio.run(main())
