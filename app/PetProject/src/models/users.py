from typing import List
from PetProject.src.database import Base
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, index=True, unique=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    age: Mapped[int] = mapped_column(nullable=True, default=18)
    password: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    bio: Mapped[str] = mapped_column(String(140), nullable=True)
    avatar: Mapped[str] = mapped_column(String(255), nullable=True)
    access_lvl: Mapped[int] = mapped_column(nullable=False, default=1)
    token: Mapped[str] = mapped_column(nullable=False, unique=True)

    todos: Mapped[List["ToDoModel"]] = relationship(back_populates="author")
