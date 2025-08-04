from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from PetProject.src.api.login_registration.config import AuthXConfigModel, security
from PetProject.src.database import get_session, get_redis
from PetProject.src.schemas.pagination import Pagination, pagination_params
from redis import Redis


SessionDeep = Annotated[AsyncSession, Depends(get_session)]
SessionRedis = Annotated[Redis, Depends(get_redis)]
SessionTokens = Annotated[AuthXConfigModel, Depends(security.access_token_required)]
Pagintaion = Annotated[Pagination, Depends(pagination_params)]
