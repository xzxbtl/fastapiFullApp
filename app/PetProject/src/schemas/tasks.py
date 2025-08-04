from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter
from PetProject.src.schemas.users import UserResponse

from PetProject.src.schemas.pagination import PaginationData

router = APIRouter()


class TaskBase(BaseModel):
    title: str = Field(title="Add Task", min_length=1, max_length=80)
    description: Optional[str] = Field(title="Description Task", max_length=300)


class TaskCreate(TaskBase):
    ...


class TaskResponse(TaskBase):
    id: int = Field(..., title='ID Task', ge=1)
    author_name: str = Field(title="Author Name", min_length=1, max_length=64)
    author: UserResponse

    class Config:
        from_attributes = True


class PaginatedTasksResponse(BaseModel):
    tasks: List[TaskResponse]
    pagination: PaginationData
