from typing import Optional

from pydantic import BaseModel, Field, EmailStr


class LoginBase(BaseModel):
    username: str = Field(title="username", min_length=1, max_length=64)
    password: str = Field(title="password", min_length=8, max_length=64, pattern=r"^[^а-яА-ЯёЁ]*$")
    confirm_password: str = Field(title="password", min_length=8, max_length=64, pattern=r"^[^а-яА-ЯёЁ]*$")


class RegisterBase(BaseModel):
    username: str = Field(title="username", min_length=1, max_length=64)
    email: EmailStr
    age: Optional[int] = Field(default=18)
    password: str = Field(title="password", min_length=8, max_length=64, pattern=r"^[^а-яА-ЯёЁ]*$")
    confirm_password: str = Field(title="password", min_length=8, max_length=64, pattern=r"^[^а-яА-ЯёЁ]*$")

    class Config:
        from_attributes = True


class RegisterCreate(RegisterBase):
    access_level: Optional[int] = Field(default=1, title="access level", ge=1, le=3)

    class Config:
        from_attributes = True
