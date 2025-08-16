from aiogram import Router, Bot
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.filters import CommandStart
from bot.base.main.core import add_user


start_router = Router()


@start_router.message(CommandStart())
async def start_menu(message: Message, bot: Bot):
    await add_user(message.from_user.id)
    await bot.send_message(
        text="*Бот успешно запущен и работает!*",
        chat_id=message.chat.id,
        parse_mode=ParseMode.MARKDOWN
    )


