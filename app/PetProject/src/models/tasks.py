from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from PetProject.src.database import Base
from PetProject.src.models.users import Users


class ToDoModel(Base):
    __tablename__ = 'todos'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str]
    description: Mapped[str]
    author_name: Mapped[str] = mapped_column(ForeignKey("users.username"))

    author: Mapped[Users] = relationship("Users", back_populates="todos")
