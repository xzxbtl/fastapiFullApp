import asyncio
import os
from aiogram import Bot, Dispatcher
from datetime import datetime
from aiogram.enums import ParseMode
from logs.logg import logger
from aiogram.types import Message
from faststream.rabbit import RabbitBroker
from dotenv import load_dotenv


load_dotenv("bot_settings__.env")
TOKEN = os.getenv("BOT_TOKEN")
broker = RabbitBroker(url="amqp://rmuser:rmpassword@localhost:5672/")

ADMIN_IDS = frozenset([745409469])


@broker.subscriber("user_actions")
async def handle_messages(data: str, message: Message, bot: Bot):
    try:
        await bot.send_message(chat_id=message.chat.id, text=data, parse_mode=ParseMode.MARKDOWN)
        logger.info(f"Получено действие пользователя - {data}")
    except Exception as e:
        logger.error(f"Error sending message: {e}")


async def global_message(data: str, bot: Bot):
    for user_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=user_id, text=data, parse_mode=ParseMode.MARKDOWN)
            logger.info(f"Получено админ действие - {data}")
            await asyncio.sleep(0.15)
        except Exception as e:
            logger.error(f"Error sending to admin {user_id}: {e}")
    else:
        logger.debug("Рассылка админам - Успешна")


@broker.subscriber("admin_actions")
async def handle_admin_messages(data: str, bot: Bot):
    task = asyncio.create_task(global_message(data, bot))



async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp["started_at"] = datetime.now().strftime("%d-%m-%Y %H:%M")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())