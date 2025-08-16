import json
from secrets import compare_digest
from datetime import datetime
from sqlalchemy import or_
from typing import Annotated, Dict, Union, Any
from fastapi import APIRouter, Body, HTTPException, Request, Response
from math import ceil
from PetProject.src.api.dependensis import SessionDeep, SessionRedis, SessionTokens, Pagintaion
from PetProject.src.models.basemethods import get_all, get_one
from PetProject.src.models.users import Users
from PetProject.src.schemas.users import UserCreate, UserResponse, UserRedactAdmin, PaginatedUsersResponse
from PetProject.src.utils.hashfunc import hash_password
from PetProject.src.utils.ratelimit import rate_limit
from PetProject.src.utils.logs.logs import logger
from PetProject.src.utils.token_generation import set_created_tokens, config, auth_middleware
from PetProject.src.api.login_registration.config import admin_config
from sqlalchemy import select, func
from PetProject.src.schemas.pagination import SortEnum
from fastapi import Header
from PetProject.src.api.pages.pages import templates
from broker.broker_service import broker

rabbit_user_router = broker
router = APIRouter(tags=["Users 🤦‍♂️"])


@router.post(
    path="/users/admin/authorization/", response_model=Dict, status_code=200
)
async def admin_authorization(
        request: Request,
        user: Annotated[
            UserCreate,
            Body(
                ..., example={
                    "username": "admin",
                    "email": "xzxbtl@mail.ru",
                    "password": "rootroot"
                }
            )
        ],
        response: Response,
) -> Dict:
    """
    Авторизация для админа, создает JWT TOKEN с 3 уровнем доступа (или меньшим) в зависимости от
    вводимого пользователя, сохраняет в куках ваш токен, чтобы управлять правами доступа

    :param request:(request:from FastAPI import Request):
    :param user:UserCreate (schemas:UserCreate):
    :param response:(response:from FastAPI import Response)
    :return:
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")
    try:
        if (compare_digest(user.username, admin_config.ADMIN_USERNAME) and
                compare_digest(user.password, admin_config.ADMIN_PASSWORD) and
                compare_digest(user.email, admin_config.ADMIN_EMAIL)):

            access_level = int(admin_config.ADMIN_BACKEND_LVL)
            user.access_level = access_level
            try:
                await set_created_tokens(user, response)

                logger.info(msg=f"Авторизован админ {client_ip} - {user.username}")

                await rabbit_user_router.publish(
                    f"🔐 *Admin Auth Event*\n\n"
                    f"🆔 *User:* `{user.username}`\n"
                    f"🌐 *IP:* `{client_ip}`\n"
                    f"🕒 *Time:* `{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}`\n"
                    f"🔗 *Referer:* `{referer or 'Direct'}`\n"
                    f"🖥️ *User-Agent:* \n`{user_agent}`\n\n"
                    f"✅ *Status:* `200` - *Successful* login",
                    queue="admin_actions"
                )
                return {"status": "Authorization complete"}

            except Exception as e:
                logger.warning(msg=f"{client_ip} - Ошибка при Аунтефикации Админом", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        else:
            logger.info(msg=f"{client_ip} - Не пройдена аунтефикация на Админа")
            await rabbit_user_router.publish(
                f"🔐 *Admin Auth Event*\n\n"
                f"🆔 *User:* `{user.username}`\n"
                f"🌐 *IP:* `{client_ip}`\n"
                f"🕒 *Time:* `{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}`\n"
                f"🔗 *Referer:* `{referer or 'Direct'}`\n"
                f"🖥️ *User-Agent:* \n`{user_agent}`\n\n"
                f"❌ *Status:* `401` - *Failed admin credentials*",
                queue="admin_actions"
            )
            raise HTTPException(status_code=401, detail="Invalid admin credentials")

    except Exception as e:
        logger.warning(msg=f"Ошибка на адресе авторизации админа - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/create/", response_model=UserRedactAdmin, status_code=201,
             responses={
                 200: {
                     "content": {
                         "application/json": {},
                         "text/html": {}
                     },
                     "description": "Returns either JSON or HTML based on Accept header"
                 }
             })
@rate_limit(max_calls=5, time_frame=60)
async def create_user(request: Request, user: Annotated[
    UserCreate,
    Body(
        ..., example={
            "username": "xzxbtl",
            "age": 18,
            "email": "xzxbtl@mail.ru",
            "password": "sfsaschreass21",
            "bio": "Hello, I'm Jack",
            "access_level": 1
        }
    )
], session: SessionDeep, response: Response,
                      accept: str = Header(default="application/json")) -> Any:
    """
    Создает пользователя, требует обязательные параметры указанные в example, за исключением возраста
    Хеширует пароль на входе в БД

    :param response:(response:from FastAPI import Response)
    :param request:(request:from FastAPI import Request):
    :param user:UserCreate (schemas:UserCreate):
    :param session:(dependensis:SessionDeep):
    :return: UserRedactAdmin:(schema:UserRedactAdmin):
    :param accept:
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    if not hasattr(request.state, 'user') or not request.state.user.get("authenticated"):
        logger.info(msg=f"{client_ip} - Неавторизованный пользователь")
        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": 401,
                    "error_title": "Unauthorized User",
                    "error_type": "Error Unauthorized User",
                    "redirect_url": "/"
                }
            )
        raise HTTPException(status_code=401, detail="Unauthorized User")

    # Проверка уровня доступа
    if request.state.user.get("lvl", 1) < 2:
        logger.info(msg=f"{client_ip} - Недостаточный уровень доступа")
        await rabbit_user_router.publish(
            f"🔐 *Admin Create Event*\n\n"
            f"🌐 *IP:* `{client_ip}`\n"
            f"🔑 *LVL:* {request.state.user.get('lvl', 1)}\n"
            f"🕒 *Time:* `{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}`\n"
            f"🔗 *Referer:* `{referer or 'Direct'}`\n"
            f"🖥️ *User-Agent:* \n`{user_agent}`\n\n"
            f"❌ *Status:* `403` - *Low level Token*",
            queue="admin_actions"
        )
        raise HTTPException(status_code=403,
                            detail="Your privileges do not allow you to create a user")

    try:
        # Проверка существующего пользователя (исправленная версия)
        existing_user = await session.execute(
            select(Users)
            .where(or_(
                Users.username == user.username,
                Users.email == user.email
            ))
        )

        if existing_user.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Username or email already exists"
            )

        new_db_user = Users(
            username=user.username,
            age=user.age,
            email=user.email,
            password=await hash_password(user.password),
            access_lvl=user.access_level,
            bio=user.bio
        )

        session.add(new_db_user)
        await session.commit()
        await session.refresh(new_db_user)

        user_response = UserRedactAdmin(
            id=new_db_user.id,
            username=new_db_user.username,
            age=new_db_user.age,
            email=new_db_user.email,
            password=user.password,
            bio=new_db_user.bio,
            access_level=new_db_user.access_lvl,
        )

        creation_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        notification_msg = (
            "✨ *New User Created!* ✨\n\n"
            f"🆔 *ID:* `{new_db_user.id}`\n"
            f"👤 *Username:* `{new_db_user.username}`\n"
            f"📧 *Email:* `{new_db_user.email}`\n"
            f"🔒 *Access Level:* `{new_db_user.access_lvl}`\n\n"
            "🔧 *Details Operation:*\n"
            f"   🌐 *IP:* `{client_ip}`\n"
            f"   🕒 *Time:* `{creation_time}`\n"
            f"   🖥️ *User-Agent:* \n`{user_agent}`\n\n"
            "✅ *Status:* `201` - *Success Created User!*\n\n"
        )

        logger.info(msg=f"Создан новый пользователь {client_ip} - {new_db_user.username}")
        await rabbit_user_router.publish(notification_msg, queue="admin_actions")

        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "create-user.html",
                context={
                    "request": request,
                    "user": user_response,
                    "message": "✅ User created successfully!"
                }
            )
        return user_response

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(msg=f"{client_ip} - Ошибка создания пользователя - {e}", exc_info=True)
        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": 500,
                    "error_title": "Error Creating User",
                    "error_type": "Ошибка создания пользователя",
                    "redirect_url": "/"
                },
                status_code=500
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/", response_model=Union[PaginatedUsersResponse, Dict[str, str]], status_code=200)
@rate_limit(max_calls=20, time_frame=10)
async def get_users(request: Request, session: SessionDeep, redis: SessionRedis,
                    pagination: Pagintaion,
                    accept: str = Header(default="application/json")) -> Any:
    """
    Возвращает всех пользователей, не учитывая пароли,
    которые создаются в схеме UserCreate
    :param request:(request:from FastAPI import Request)
    :param redis:(dependensis:SessionRedis)
    :param session:(dependensis:SessionDeep)
    :param pagination:(dependensis: Pagination)
    :param accept
    :return PaginatedResponse:(schema.user.List[PaginatedResponse] || HTML)
    """
    client_ip = request.client.host
    try:
        cache_key = f"users:{pagination.page}:{pagination.perPage}:{pagination.order}"
        count_key = f"users_count"

        cached_users = await redis.get(cache_key)
        total_users = await redis.get(count_key)

        if total_users:
            total_users = int(total_users)

        if cached_users and total_users:
            logger.info(f"{client_ip} - Данные из Redis")
            users_data = json.loads(cached_users)

            if "text/html" in accept.lower():
                total_pages = ceil(total_users / pagination.perPage) if total_users else 1
                pagination_data = {
                    "current_page": pagination.page,
                    "total_pages": total_pages,
                    "has_prev": pagination.page > 1,
                    "has_next": pagination.page < total_pages,
                    "next_num": pagination.page + 1,
                    "prev_num": pagination.page - 1,
                    "query_params": request.query_params,
                }
                return templates.TemplateResponse(
                    "users.html",
                    context={
                        "users": users_data,
                        "pagination": pagination_data,
                        "request": request,
                        "token_status": request.state.user.get("authenticated", False),
                        "token_lvl": request.state.user.get("lvl", 1),
                        "username": request.state.user.get("sub", None)
                    }
                )
            return PaginatedUsersResponse(
                users=json.loads(cached_users),
                pagination={
                    "total": int(total_users),
                    "page": pagination.page,
                    "perPage": pagination.perPage,
                    "totalPages": (int(total_users) + pagination.perPage - 1) // pagination.perPage
                }
            )

        total_users = await session.scalar(select(func.count(Users.id)))
        query = select(Users)
        if pagination.order == SortEnum.ASC:
            query = query.order_by(Users.id.asc())
        else:
            query = query.order_by(Users.id.desc())

        query = query.limit(pagination.perPage).offset((pagination.page - 1) * pagination.perPage)
        users = await session.execute(query)
        users = users.scalars().all()

        if not users:
            raise HTTPException(status_code=404, detail="users not found")

        user_responses = []
        for user in users:
            user_data = UserResponse.from_orm(user)

            if user.avatar:
                user_data.image = f"/static/media/avatars/{user.avatar}"

            user_responses.append(user_data)

        users_data = [user.dict() for user in user_responses]

        await redis.set(cache_key, json.dumps([user.dict() for user in user_responses]), ex=10)
        await redis.set(count_key, total_users, ex=30)

        if "text/html" in accept.lower():
            total_pages = ceil(total_users / pagination.perPage) if total_users else 1
            pagination_data = {
                "current_page": pagination.page,
                "total_pages": total_pages,
                "has_prev": pagination.page > 1,
                "has_next": pagination.page < total_pages,
                "next_num": pagination.page + 1,
                "prev_num": pagination.page - 1,
                "query_params": request.query_params,
            }
            return templates.TemplateResponse(
                "users.html",
                context={
                    "users": users_data,
                    "pagination": pagination_data,
                    "request": request,
                    "token_status": request.state.user.get("authenticated", False),
                    "token_lvl": request.state.user.get("lvl", 1),
                    "username": request.state.user.get("sub", None)
                }
            )

        return PaginatedUsersResponse(
            users=user_responses,
            pagination={
                "total": total_users,
                "page": pagination.page,
                "perPage": pagination.perPage,
                "totalPages": (total_users + pagination.perPage - 1) // pagination.perPage
            }
        )

    except Exception as e:
        logger.warning(msg=f"{client_ip} - Ошибка при получении пользователей - {e}", exc_info=True)
        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": 500,
                    "error_title": "Error Get Users",
                    "error_type": "Ошибка при получении пользователей",
                    "redirect_url": "/"
                }
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id_or_username}", response_model=UserResponse, status_code=200)
async def get_user(user_id_or_username: str, session: SessionDeep, request: Request,
                   accept: str = Header(default="application/json")) -> UserResponse:
    """
    Возвращает определенного пользователя по его username или id с учетом его пароля!!!
    смотри models -> users.py

    :param accept:
    :param request:(request:from FastAPI import Request)
    :param user_id_or_username:str|int
    :param session:(dependensis:SessionDeep)
    :return use_admin - UserCreate
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    try:
        user_id = int(user_id_or_username)
        user = await get_one(Users, user_id, session)
    except ValueError as e:
        logger.warning(msg=f"{client_ip} - Ошибка при попытке получения пользователя {e}", exc_info=True)
        user = await get_one(Users, user_id_or_username, session)

    user_admin = UserResponse.from_orm(user)
    creation_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')

    if user:
        notification_msg = (
            "🎉 *SUCCESS! USER FOUND* 🎉\n\n"
            f"📌 *User Details:*\n"
            f"   ▫️ *ID:* `{user_admin.id}`\n"
            f"   ▫️ *Username:* `{user_admin.username}`\n"
            f"   ▫️ *Bio:* _{user_admin.bio[:100] + '...' if user_admin.bio else 'Not specified'}_\n\n"
            f"🔍 *Search Details:*\n"
            f"   ▫️ *By IP:* `{client_ip}`\n"
            f"   ▫️ *User-Agent:* `{user_agent}`\n\n"
            f"   ▫️ *Referer:* `{referer}`\n"
            f"   ▫️ *At:* `{creation_time}`\n"
            "✅ *Status:* Successfully found (200)"
        )
    else:
        notification_msg = (
            "❌ *USER NOT FOUND* ❌\n\n"
            f"⚠️ *Search Failed For:*\n"
            f"   ▫️ *Request From IP:* `{client_ip}`\n"
            f"   ▫️ *At Time:* `{creation_time}`\n\n"
            f"🛠 *Technical Info:*\n"
            f"   ▫️ *By IP:* `{client_ip}`\n"
            f"   ▫️ *User-Agent:* `{user_agent}`\n\n"
            f"   ▫️ *Referer:* `{referer}`\n"
            f"   ▫️ *At:* `{creation_time}`\n"
            "🔎 *Status:* User not found (404)"
        )

    await rabbit_user_router.publish(
        message=notification_msg,
        queue="user_actions"
    )

    if user is not None:
        logger.info(f"Найден пользователь - {user_admin.username}")
        return user_admin
    logger.warning(msg=f"{client_ip} - Не найдено пользователь в БД")
    if "text/html" in accept.lower():
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": 404,
                "error_title": "Not Found",
                "error_type": "User not Found",
                "redirect_url": "/"
            }
        )
    raise HTTPException(status_code=404, detail="User not found")


@router.get("/users/admin/search/{user_id_or_username}", response_model=UserRedactAdmin, status_code=200)
async def get_full_user_info(user_id_or_username: str, session: SessionDeep, request: Request,
                             accept: str = Header(default="application/json")) -> UserRedactAdmin:
    """
    Отдельная админ ручка для отображения полной информации пользователя

    :param accept:
    :param user_id_or_username: str|int
    :param session:(dependensis:SessionDeep)
    :param request:(request:from FastAPI import Request)
    :return UserRedactAdmin:
    """
    client_ip = request.client.host

    if not hasattr(request.state, 'user') or not request.state.user.get("authenticated"):
        logger.info(msg=f"{client_ip} - Необходим токен для выполнения функции")
        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": 401,
                    "error_title": "Error Token",
                    "error_type": "Token is required",
                    "redirect_url": "/"
                }
            )
        raise HTTPException(status_code=401, detail="Token is required")

    if request.state.user.get("lvl", 1) < 2:
        logger.info(msg=f"{client_ip} - Недостаточно прав для выполнения команды")
        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": 403,
                    "error_title": "Error permissions",
                    "error_type": "Insufficient permissions",
                    "redirect_url": "/"
                }
            )
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        user_id = int(user_id_or_username)
        user = await get_one(Users, user_id, session)
    except ValueError as e:
        logger.warning(msg=f"{client_ip} - Ошибка при попытке получения пользователя {e}", exc_info=True)
        user = await get_one(Users, user_id_or_username, session)

    user_admin = UserRedactAdmin.from_orm(user)
    if user is not None:
        return user_admin
    logger.warning(msg=f"{client_ip} - Не найдено пользователь в БД")
    raise HTTPException(status_code=404, detail="User not found")


@router.patch("/users/edit/{user_id_or_username}", response_model=UserRedactAdmin, status_code=200)
async def update_user(user_id_or_username: str, request: Request, session: SessionDeep,
                      user_data: UserRedactAdmin,
                      accept: str = Header(default="application/json")) -> UserRedactAdmin:
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    if not hasattr(request.state, 'user') or not request.state.user.get("authenticated"):
        logger.info(msg=f"{client_ip} - Необходим токен для выполнения функции")
        raise HTTPException(status_code=401, detail="Token is required")


    access_level = request.state.user.get("lvl", 1)
    if access_level < 2:
        logger.info(msg=f"{client_ip} - Недостаточно прав для выполнения команды")
        await rabbit_user_router.publish(
            f"🔐 *Admin Edit Event*\n\n"
            f"🌐 *IP:* `{client_ip}`\n"
            f"🔑 *LVL:* `{access_level}`\n"
            f"🕒 *Time:* `{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}`\n"
            f"🔗 *Referer:* `{referer or 'Direct'}`\n"
            f"🖥️ *User-Agent:* \n`{user_agent}`\n\n"
            f"❌ *Status:* `403` - *Low level Token*",
            queue="admin_actions"
        )
        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": 403,
                    "error_title": "Error permissions",
                    "error_type": "Insufficient permissions",
                    "redirect_url": "/"
                }
            )
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    try:
        user_id = int(user_id_or_username)
        user = await get_one(Users, user_id, session)
    except ValueError:
        logger.warning(msg=f"{client_ip} - Ошибка при попытке получения пользователя {user_id_or_username}",
                       exc_info=True)
        user = await get_one(Users, user_id_or_username, session)

    if user is None:
        logger.warning(msg=f"{client_ip} - Пользователь не найден")
        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": 404,
                    "error_title": "Not Found",
                    "error_type": "User not found",
                    "redirect_url": "/"
                }
            )
        raise HTTPException(status_code=404, detail="User not found")

    """Проверка на уровень токенна + юзернейм в токене, 
    так как это админ функция, то убрана проверка на юзернейм
    
    if payload.get('sub') != existing_user.username and access_level < 2:
        logger.info(msg=f"{client_ip} - Недостаточно прав для выполнения команды")
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    """

    user.username = user_data.username
    user.age = user_data.age
    user.email = user_data.email
    user.bio = user_data.bio

    if user_data.password:
        user.password = await hash_password(user_data.password)
    else:
        logger.info(msg="Недостаточно прав для изменения пароля")
        user.password = user.password

    if user_data.access_level:
        if access_level == 3:
            if user_data.access_level != 1:
                user.access_lvl = user_data.access_level
            else:
                user.access_lvl = user.access_lvl
        else:
            logger.info(msg="Недостаточно прав для изменения уровня доступа")
            user.access_lvl = user.access_lvl

    await session.commit()
    await session.refresh(user)

    creation_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    notification_msg = (
        "✨ *User Edited!* ✨\n\n"
        f"🆔 *ID:* `{user.id}`\n"
        f"👤 *Username:* `{user.username}`\n"
        f"🔑 *Password:* `{user_data.password}`\n"
        f"📧 *Email:* `{user.email}`\n"
        f"📝 *BIO:* `{user.bio[:100] + '...' if user.bio else 'Not specified'}`\n"
        f"🔒 *Access Level:* `{user.access_lvl}`\n"
        "🔧 *Details Operation:*\n"
        f"   🌐 *IP:* `{client_ip}`\n"
        f"   🕒 *Time:* `{creation_time}`\n"
        f"   🖥️ *User-Agent:* \n`{user_agent}`\n\n"
        "✅ *Status:* `200` - *Success Edited User!*\n\n"
    )
    await rabbit_user_router.publish(
        notification_msg,
        queue="admin_actions"
    )

    logger.info(msg=f"{client_ip} - Пользователь {user.username} успешно обновлён")
    return UserRedactAdmin.from_orm(user)
