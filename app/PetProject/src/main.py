import httpx
import sentry_sdk
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from PetProject.src.api import main_router
from shared.database import setup_database, create_admins_bot_users
from PetProject.src.utils.logs.logs import logger
from redis.asyncio import Redis
from fastapi.staticfiles import StaticFiles
from broker.broker_service import broker
from PetProject.src.utils.token_generation import auth_middleware


@asynccontextmanager
async def lifespan(_: FastAPI):
    await broker.start()
    logger.debug(msg="Создание таблиц базы данных...")
    try:
        db_status = await setup_database()
        if db_status:
            await create_admins_bot_users()
        logger.info(msg="Таблицы базы данных созданы.")
    except Exception as e:
        logger.error(msg=f"База данных не создалась {e}", exc_info=True)
    try:
        app.state.redis = Redis(
            host="redis",
            port=6379,
            decode_responses=True,
        )
        app.state.http_client = httpx.AsyncClient()
        logger.info(msg="Соеднинение с Redis установленно")
    except Exception as e:
        logger.error(msg=f"Соединение с Redis не установлено : {e}", exc_info=True)

    yield

    await app.state.http_client.aclose()
    await app.state.redis.close()
    await broker.stop()
    logger.info("Соединение с Redis закрыто")
    logger.info("Соеднинение с RabbitMQ закрыто")


load_dotenv(dotenv_path='sentry.env')

sentry_sdk.init(
    dsn=str(os.getenv('SENTRY_LINK')),
    send_default_pii=True
)

app = FastAPI(lifespan=lifespan,
              title="FullSite FastAPI",
              description="""
              Полностью рабочий сайт, написанный на чистом JS и FastAPI.

              ### Основные технологии:
              - **Backend**: FastAPI
              - **База данных**: SQLAlchemy 3
              - **Кэширование**: Redis (async)
              - **Очереди сообщений**: RabbitMQ
              - **Frontend**: Чистый JavaScript

              ### Контакты автора:
              - **Автор проекта**: xzxbtl
              - **Telegram**: [qxzxbtlqq](https://t.me/qxzxbtlqq)
              """,
              version="1.0.0",
              contact={
                  "name": "xzxbtl",
                  "url": "https://github.com/xzxbtl",
              },
              license_info={
                  "name": "xxxBTL License",
              })
app.mount("/static", StaticFiles(directory="/app/PetProject/src/public/static"), name="static")
app.include_router(main_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(auth_middleware)