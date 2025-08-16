from typing import TypeVar, Generic, List, Union
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from PetProject.src.api.dependensis import SessionDeep
from shared.base import Base
from PetProject.src.utils.logs.logs import logger

VT = TypeVar('VT', bound=Base)


async def get_all(obj: Generic[VT], session: SessionDeep) -> List[VT]:
    try:
        # if obj.__name__ == "ToDoModel":
        #     result = await session.execute(
        #         select(obj).options(selectinload(obj.author))
        #     )
        #     return list(result.scalars().all())
        # else:
        #     result = await session.execute(select(obj))
        #     return list(result.scalars().all())

        stmt = select(obj)
        if hasattr(obj, 'author'):
            stmt = stmt.options(selectinload(obj.author))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    except Exception as e:
        logger.warning(f"Ошибка при попытке получения всех записей!: {e}", exc_info=True)


async def get_one(obj: Generic[VT], attr: Union[int, str], session: SessionDeep) -> VT | None:
    try:
        stmt = select(obj).order_by(desc(obj.id))

        if isinstance(attr, int):
            stmt = stmt.where(obj.id == attr)
        elif isinstance(attr, str):
            stmt = stmt.where(obj.username == attr)
        else:
            raise ValueError("Not found username | author_name or id")

        result = await session.execute(stmt)
        inst = result.scalar()
        return inst
    except Exception as e:
        logger.warning(f"Ошибка при получении одного объекта: {e}", exc_info=True)


