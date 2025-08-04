from datetime import timedelta
from typing import Dict, Annotated
from sqlalchemy import select
from fastapi import APIRouter, Request, Response, HTTPException, Body
from PetProject.src.api.dependensis import SessionDeep, SessionTokens
from PetProject.src.models.users import Users
from PetProject.src.schemas.login import LoginBase, RegisterCreate
from PetProject.src.utils.hashfunc import verify_password, hash_password
from PetProject.src.utils.logs.logs import logger
from PetProject.src.utils.token_generation import create_access_token, config
from sqlalchemy.exc import IntegrityError

router = APIRouter(tags=["Login | Registration 🔑"])


@router.post("/users/login/", response_model=Dict, status_code=200)
async def login(request: Request, user_form: Annotated[
    LoginBase,
    Body(
        ..., example={
            "username": "admin",
            "password": "dsaadasdsadsadas",
            "confirm_password": "dsadsadsadsada",
        }
    )
], session: SessionDeep, response: Response) -> Dict:
    """
    Авторизация пользователя
    :param request:(request:from FastAPI import Request):
    :param session:(dependensis:SessionDeep)
    :param user_form:(schemas:LoginBase):
    :param response:(response:from FastAPI import Response)
    :return:
    """
    client_ip = request.client.host
    try:
        stmt = select(Users).where(Users.username == user_form.username)
        result = await session.execute(stmt)
        base_user = result.scalars().first()

        if base_user is None:
            logger.info(msg=f"{client_ip} - Пользователь не найден")
            raise HTTPException(status_code=401, detail="User not found")

        if user_form.password == user_form.confirm_password:
            if await verify_password(user_form.password, base_user.password):
                access_token_expires = timedelta(days=1)
                access_token = await create_access_token(
                    data={"sub": user_form.username, "lvl": base_user.access_lvl},
                    expires_delta=access_token_expires)
                response.set_cookie(key=config.JWT_ACCESS_COOKIE_NAME, value=str(access_token),
                                    httponly=True, secure=True)
            else:
                logger.info(msg=f"{client_ip} - Невверно введеные данные username или password")
                raise HTTPException(status_code=401, detail="Incorrect username or password")
        else:
            logger.info(msg=f"{client_ip} - Пароли не совпадают")
            raise HTTPException(status_code=401, detail="password mismatch")

        return {"Authorizaton": "Success"}

    except Exception as e:
        logger.info(msg=f"Ошибка при попытке авторизации - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/users/registration/", response_model=Dict, status_code=201)
async def registration(request: Request, user: Annotated[
    RegisterCreate,
    Body(
        ..., example={
            "username": "santaniel",
            "email": "santaniel@mail.ru",
            "password": "treds23412fs",
            "confirm_password": "treds23412fs",
            "age": 18
        }
    )
], response: Response, session: SessionDeep) -> Dict:
    """
    Регистрация пользователя
    :param request:(request:from FastAPI import Request):
    :param user:(schemas:RegisterCreate)
    :param response:(response:from FastAPI import Response)
    :param session:(dependensis:SessionDeep)
    :return:
    """
    client_ip = request.client.host
    stmt = select(Users).filter((Users.username == user.username) | (Users.email == user.email))
    result = await session.execute(stmt)
    existing_user = result.scalars().first()

    if existing_user:
        logger.info(msg=f"{client_ip} - Пользователь с таким именем или email уже существует")
        raise HTTPException(status_code=400, detail="User with this username or email already exists")

    if user.password != user.confirm_password:
        logger.info(msg=f"{client_ip} - Пароли не совпадают")
        raise HTTPException(status_code=401, detail="Password mismatch")

    try:
        access_token_expires = timedelta(days=1)
        access_token = await create_access_token(data={"sub": user.username, "lvl": user.access_level},
                                                 expires_delta=access_token_expires)

        new_user = Users(
            username=user.username,
            email=user.email,
            password=await hash_password(user.password),
            age=user.age,
            access_lvl=user.access_level,
            token=str(access_token)
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        response.set_cookie(key=config.JWT_ACCESS_COOKIE_NAME, value=str(access_token), httponly=True, secure=True)

        return {"Registration": "Success", "username": new_user.username, "user_id": new_user.id}

    except IntegrityError:
        await session.rollback()
        logger.warning(msg=f"{client_ip} - Ошибка при регистрации - пользователь с такими данными уже существует",
                       exc_info=True)
        raise HTTPException(status_code=400, detail="User with this data already exists")
    except Exception as e:
        logger.warning(msg=f"{client_ip} - Ошибка при регистрации - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
