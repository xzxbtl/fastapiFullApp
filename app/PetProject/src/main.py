import httpx
import sentry_sdk
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from PetProject.src.api import main_router
from PetProject.src.database import setup_database
from PetProject.src.utils.logs.logs import logger
from redis.asyncio import Redis
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(msg="Создание таблиц базы данных...")
    try:
        await setup_database()
        logger.info(msg="Таблицы базы данных созданы.")
    except Exception as e:
        logger.warning(msg=f"База данных не создалась {e}", exc_info=True)
    try:
        app.state.redis = Redis(
            host="redis",
            port=6379,
            decode_responses=True,
        )
        app.state.http_client = httpx.AsyncClient()
        logger.info(msg="Соеднинение с Redis установленно")
    except Exception as e:
        logger.warning(msg=f"Соединение с Redis не установлено : {e}", exc_info=True)

    yield

    await app.state.http_client.aclose()
    await app.state.redis.close()
    logger.info("Соединение с Redis закрыто")


load_dotenv(dotenv_path='sentry.env')

sentry_sdk.init(
    dsn=str(os.getenv('SENTRY_LINK')),
    send_default_pii=True
)

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="/app/PetProject/src/public/static"), name="static")
app.include_router(main_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
