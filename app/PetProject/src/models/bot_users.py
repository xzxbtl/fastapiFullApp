from shared.base import Base
from sqlalchemy.orm import mapped_column, Mapped


class BotAdminUsers(Base):
    __tablename__ = 'bot_admin_users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False,
                                    unique=True, index=True)
    user_id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(autoincrement=True, nullable=False, unique=False, index=True)
    admin_level: Mapped[int] = mapped_column(autoincrement=True, default=2, nullable=False, unique=False, index=True)


class BotUsers(Base):
    __tablename__ = 'bot_users'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, nullable=False,
                                    unique=True, index=True)
    user_id: Mapped[int] = mapped_column(autoincrement=True, nullable=False, unique=True, index=True)