from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from jose import jwt, ExpiredSignatureError, JWTError
from datetime import datetime, timedelta
from PetProject.src.api.login_registration.config import AuthXConfigModel
from PetProject.src.utils.logs.logs import logger

config = AuthXConfigModel()
PUBLIC_PREFIXES = [
    # Документация
    "/docs",
    "/openapi.json",
    "/redoc",

    # Статика
    "/static/",
    "/favicon.ico",
    "/robots.txt",
    "/templates/"

    # Аутентификация
    "/api/auth",
    "/api/login",
    "/api/register",
    "/api/auth/registration",
    "/api/auth/login",

    # Админ
    "/users/admin/authorization"
]


async def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire,
                      "type": "access",
                      "iat": datetime.utcnow().timestamp()})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire,
                      "type": "refresh",
                      "iat": datetime.utcnow().timestamp()})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid access token")


async def verify_refresh_token(token: str):
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


"""
async def verify_jwt_token(token: str):
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms="HS256")

        if 'exp' in payload and payload['exp'] < datetime.utcnow().timestamp():
            logger.warning('JWT token is expired')
            raise HTTPException(status_code=401, detail="Token expired")
        return payload

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
"""


async def set_created_tokens(user, response):
    access_token, refresh_token = await create_tokens(user)

    response.set_cookie(
        key=config.JWT_REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=604800,
        path="/"
    )
    response.set_cookie(
        key=config.JWT_ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=1800,
        path="/"
    )


async def delete_tokens(request, response):
    access_token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    refresh_token = request.cookies.get(config.JWT_REFRESH_COOKIE_NAME)

    response.delete_cookie(access_token,
                           path="/")

    response.delete_cookie(refresh_token,
                           path="/")


async def create_tokens(user):
    access_token_expires = timedelta(minutes=30)
    access_level = getattr(user, 'access_lvl', None) or getattr(user, 'access_level', None)

    access_token = await create_access_token(
        data={
            "sub": user.username,
            "lvl": access_level,
            "type": "access",
            "iat": datetime.utcnow().timestamp()
        },
        expires_delta=access_token_expires
    )
    refresh_token_expires = timedelta(days=7)
    refresh_token = await create_refresh_token(
        data={
            "sub": user.username,
            "lvl": access_level,
            "type": "refresh",
            "iat": datetime.utcnow().timestamp()
        },
        expires_delta=refresh_token_expires
    )
    return access_token, refresh_token


async def get_update_refresh_token(token: str) -> bool:
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=["HS256"])
        expires_in = payload['exp'] - datetime.utcnow().timestamp()
        return expires_in <= 86400

    except JWTError:
        return False


async def auth_middleware(request: Request, call_next):
    logger.debug(f"Incoming cookies: {request.cookies}")
    if any(request.url.path.startswith(prefix) for prefix in PUBLIC_PREFIXES) \
            or request.method == "OPTIONS":
        logger.debug("Skipping auth for public route")
        return await call_next(request)

    try:
        access_token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
        logger.debug(f"Access token: {access_token}")
    except Exception:
        access_token = None

    try:
        if access_token:
            payload = await verify_access_token(access_token)
            logger.debug(f"Token payload: {payload}")
            request.state.user = {
                "sub": payload["sub"],
                "lvl": payload.get("lvl", 1),
                "authenticated": True
            }
            response = await call_next(request)
            return response
        elif request.url.path == "/":
            return await call_next(request)
        else:
            response = RedirectResponse(
                url="/api/login",
                status_code=303
            )
            return response

    except HTTPException as access_error:
        if access_error.detail != "Access token expired":
            raise

        refresh_token = request.cookies.get(config.JWT_REFRESH_COOKIE_NAME)
        if not refresh_token:
            raise HTTPException(401, "Refresh token required")

        try:
            refresh_payload = await verify_refresh_token(refresh_token)
            request.state.user = {
                "sub": refresh_payload["sub"],
                "lvl": refresh_payload.get("lvl", 1),
                "authenticated": True
            }
            should_update_refresh = await get_update_refresh_token(refresh_token)

            new_access = await create_access_token({
                "sub": refresh_payload["sub"],
                "lvl": refresh_payload.get("lvl", 1),
                "type": "access",
                "iat": datetime.utcnow().timestamp()
            })

            response = await call_next(request)

            if should_update_refresh:
                new_refresh = await create_refresh_token({
                    "sub": refresh_payload["sub"],
                    "lvl": refresh_payload.get("lvl", 1),
                    "type": "refresh",
                    "iat": datetime.utcnow().timestamp()
                })
                response.set_cookie(
                    key=config.JWT_REFRESH_COOKIE_NAME,
                    value=new_refresh,
                    httponly=True,
                    secure=True,
                    samesite='strict',
                    max_age=604800,
                    path="/"
                )

            response.set_cookie(
                key=config.JWT_ACCESS_COOKIE_NAME,
                value=new_access,
                httponly=True,
                secure=True,
                samesite='strict',
                max_age=1800,
                path="/"
            )

            return response

        except HTTPException:
            response = RedirectResponse(
                url="/api/auth/login/",
                status_code=401
            )
            response.delete_cookie(config.JWT_REFRESH_COOKIE_NAME, path="/")
            response.delete_cookie(config.JWT_ACCESS_COOKIE_NAME, path="/")
            return response
