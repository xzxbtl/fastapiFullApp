from fastapi import HTTPException
from jose import jwt, ExpiredSignatureError
from datetime import datetime, timedelta
from PetProject.src.api.login_registration.config import AuthXConfigModel
from PetProject.src.utils.logs.logs import logger

config = AuthXConfigModel()


async def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=1)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt


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

