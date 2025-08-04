from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from PetProject.src.schemas.pagination import PaginationData


class UserBase(BaseModel):
    username: str = Field(title="username", min_length=1, max_length=64)
    age: Optional[int] = Field(default=18)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(title="password", min_length=8, max_length=64, pattern=r"^[^а-яА-ЯёЁ]*$")
    access_level: Optional[int] = Field(default=1, title="access level", ge=1, le=3)
    bio: Optional[str] = Field(title="Bio", description="Био пользователя", max_length=140, default="")

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int = Field(..., title='ID User', ge=1)
    bio: Optional[str] = Field(title="Bio", description="Био пользователя", max_length=140, default="")
    image: Optional[str] = Field(None, title="Avatar", description="URL аватара пользователя")

    class Config:
        from_attributes = True


class UserRedactAdmin(UserCreate):
    id: int = Field(..., title='ID User', ge=1)
    access_level: Optional[int] = Field(default=1, title="access level", description="Уровень доступа", ge=1, le=3)

    class Config:
        from_attributes = True


class PaginatedUsersResponse(BaseModel):
    users: List[UserResponse]
    pagination: PaginationData
