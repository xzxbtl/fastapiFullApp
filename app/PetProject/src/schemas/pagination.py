from enum import Enum
from pydantic import BaseModel
from fastapi import Query


class SortEnum(Enum):
    ASC = "asc"
    DESC = "desc"


class Pagination(BaseModel):
    perPage: int
    page: int
    order: SortEnum


class PaginationData(BaseModel):
    total: int
    page: int
    perPage: int
    totalPages: int


def pagination_params(
        page: int = Query(ge=1, default=1, le=5000,
                          title="Номер Страницы", description="Номер страницы (начиная с 1)"),
        perPage: int = Query(ge=1, default=2, le=100,
                             title="Кол-во Элементов", description="Количество элементов на странице"),
        order: SortEnum = Query(
            default=SortEnum.DESC,
            title="Порядок Сортировки",
            description="Порядок сортировки: asc (по возрастанию) или desc (по убыванию)",
            example="desc"
        )
):
    return Pagination(perPage=perPage, page=page, order=order.value)
