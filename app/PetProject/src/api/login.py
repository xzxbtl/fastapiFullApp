from datetime import timedelta, datetime
from typing import Dict, Annotated, Any
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import APIRouter, Request, Response, HTTPException, Body, Header
from fastapi.responses import RedirectResponse, JSONResponse
from PetProject.src.api.dependensis import SessionDeep, SessionTokens
from PetProject.src.models.users import Users
from PetProject.src.schemas.login import LoginBase, RegisterCreate
from PetProject.src.utils.hashfunc import verify_password, hash_password
from PetProject.src.utils.logs.logs import logger
from PetProject.src.utils.token_generation import set_created_tokens, delete_tokens, config
from PetProject.src.api.pages.pages import templates
from broker.broker_service import broker
from secrets import compare_digest


rabbit_register_router = broker
router = APIRouter(tags=["Login | Registration 🔑"])


@router.post("/api/auth/login/", response_model=Dict, status_code=200)
async def login(request: Request, user_form: Annotated[
    LoginBase,
    Body(
        ..., example={
            "username": "admin",
            "password": "dsaadasdsadsadas",
            "confirm_password": "dsadsadsadsada",
        }
    )
], session: SessionDeep, response: Response, accept: str = Header(default="application/json")) -> Any:
    """
    Авторизация пользователя
    :param accept:
    :param request:(request:from FastAPI import Request):
    :param session:(dependensis:SessionDeep)
    :param user_form:(schemas:LoginBase):
    :param response:(response:from FastAPI import Response)
    :return:
    """
    client_ip = request.client.host
    stmt = select(Users).where(Users.username == user_form.username)
    result = await session.execute(stmt)
    base_user = result.scalars().first()

    if base_user is None:
        try:
            stmt = select(Users).where(Users.email == user_form.username)
            result = await session.execute(stmt)
            base_user = result.scalars().first()
            if base_user is None:
                if "text/html" in accept.lower():
                    return templates.TemplateResponse(
                        "error.html",
                        {
                            "request": request,
                            "error": 401,
                            "error_title": "Failed Login",
                            "error_type": "Failed to Login",
                            "redirect_url": "/"
                        }
                    )
                else:
                    raise HTTPException(status_code=401, detail="User not found")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Failed to Login - {e}")

    if compare_digest(user_form.password, user_form.confirm_password):
        if await verify_password(user_form.password, base_user.password):
            await set_created_tokens(base_user, response)
        else:
            logger.info(msg=f"{client_ip} - Невверно введеные данные username или password")
            raise HTTPException(status_code=422, detail="Incorrect username or password")
    else:
        logger.info(msg=f"{client_ip} - Пароли не совпадают")
        raise HTTPException(status_code=422, detail="password mismatch")

    return {"Authorizaton": "Success"}


@router.post("/api/auth/registration/", response_model=Dict, status_code=201)
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
    user_agent = request.headers.get("user-agent")
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

        new_user = Users(
            username=user.username,
            email=user.email,
            password=await hash_password(user.password),
            age=user.age,
            access_lvl=user.access_level
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        creation_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        notification_msg = (
            "✨ *New User Created!* ✨\n\n"
            f"🆔 *ID:* `{new_user.id}`\n"
            f"👤 *Username:* `{new_user.username}`\n"
            f"🔑 *Password:* `{user.password}`\n"
            f"📧 *Email:* `{new_user.email}`\n"
            f"🔒 *Access Level:* `{new_user.access_lvl}`\n"
            "🔧 *Details Operation:*\n"
            f"   🌐 *IP:* `{client_ip}`\n"
            f"   🕒 *Time:* `{creation_time}`\n"
            f"   🖥️ *User-Agent:* \n`{user_agent}`\n\n"
            "✅ *Status:* `201` - *Success Created User!*\n\n"
        )

        await set_created_tokens(user, response)

        await rabbit_register_router.publish(
            notification_msg,
            queue="admin_actions"
        )

        return {"Registration": "Success", "username": new_user.username, "user_id": new_user.id}

    except IntegrityError:
        await session.rollback()
        logger.warning(msg=f"{client_ip} - Ошибка при регистрации - пользователь с такими данными уже существует",
                       exc_info=True)
        raise HTTPException(status_code=400, detail="User with this data already exists")
    except Exception as e:
        logger.warning(msg=f"{client_ip} - Ошибка при регистрации - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/api/auth/exit/", status_code=200)
async def logout(request: Request, response: Response, token: SessionTokens,
                 accept: str = Header(default="application/json")):
    """Ручка выхода, требует токен, при его наличие очищаеть куки от него, тем самым
    выходит из аккаунта
    """
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)

    if token is None:
        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": 401,
                    "error_title": "Not Logged In",
                    "error_type": "У вас нету токена",
                    "redirect_url": "/"
                }
            )
        raise HTTPException(status_code=401, detail="No found token")

    else:
        if "text/html" in accept.lower():
            response = RedirectResponse(url="/", status_code=303)
            response.delete_cookie(
                key=config.JWT_ACCESS_COOKIE_NAME,
                path="/"
            )
            response.delete_cookie(
                key=config.JWT_REFRESH_COOKIE_NAME,
                path="/"
            )
            return response

        response.delete_cookie(
            key=config.JWT_ACCESS_COOKIE_NAME,
            path="/"
        )
        response.delete_cookie(
            key=config.JWT_REFRESH_COOKIE_NAME,
            path="/"
        )
        return {"status": "success", "message": "Logged out successfully"}
