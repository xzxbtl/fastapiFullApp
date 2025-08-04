import json
from math import ceil
from typing import Annotated, Dict, Union, Any
from fastapi import APIRouter, Body, HTTPException, Request
from fastapi import Header
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from PetProject.src.api.dependensis import SessionDeep, SessionRedis, Pagintaion, SessionTokens
from PetProject.src.models.basemethods import get_all, get_one
from PetProject.src.models.tasks import ToDoModel
from PetProject.src.models.users import Users
from PetProject.src.schemas.tasks import TaskResponse, TaskCreate, PaginatedTasksResponse
from PetProject.src.schemas.users import UserResponse
from PetProject.src.utils.ratelimit import rate_limit
from datetime import datetime
from PetProject.src.utils.logs.logs import logger
from PetProject.src.schemas.pagination import SortEnum
from PetProject.src.api.pages.pages import templates
from PetProject.src.utils.token_generation import config
from PetProject.src.utils.token_generation import verify_jwt_token
from faststream.rabbit.fastapi import RabbitRouter


router = APIRouter(tags=["Tasks 💻"])
rabbit_tasks_router = RabbitRouter("amqp://rmuser:rmpassword@rabbitmq:5672/")


@router.post("/tasks/create/", response_model=TaskResponse, status_code=201,
             responses={
                 200: {
                     "content": {
                         "application/json": {},
                         "text/html": {}
                     },
                     "description": "Returns either JSON or HTML based on Accept header"
                 }
             }
        )
@rate_limit(max_calls=5, time_frame=60)
async def create_task(
        request: Request,
        task: Annotated[
            TaskCreate,
            Body(
                ..., example={
                    "title": "strasasa",
                    "description": "stsadadsadar"
                }
            )
        ],
        session: SessionDeep,
        token: SessionTokens,
        accept: str = Header(default="application/json")
) -> Any:
    """Создает таск + описание в docs в качестве example
        Коммит всего этого в БД и ответ полной схемой TaskResponse

        :param request:(request:from FastAPI import Request):
        :param task:(schemas.tasks:TaskCreate):
        :param session:(dependencies:SessionDeep):
        :return TaskResponse:(schemas.tasks:TaskResponse):
        :param token:(dependensis:SessionTokens):
        :param accept:
    """
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent")
    referer = request.headers.get("referer")

    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    try:
        if token:
            payload = await verify_jwt_token(token)
            author_name = payload.get("sub")

        else:
            logger.info(msg=f"{client_ip} - Неавторизованный пользователь")
            await rabbit_tasks_router.broker.publish(
                f"🔐 *Task Create Event*\n\n"
                f"🌐 *IP:* `{client_ip}`\n"
                f"🕒 *Time:* `{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}`\n"
                f"🔗 *Referer:* `{referer or 'Direct'}`\n"
                f"🖥️ *User-Agent:* \n`{truncate(user_agent, 50)}`\n\n"
                f"❌ *Status:* `401` - *Unauthorized User*",
                queue="user_actions"
            )
            raise HTTPException(status_code=401, detail="Unauthorized User")

        result = await session.execute(select(Users).where(Users.username == str(author_name)))
        author = result.scalars().first()


        if author is None:
            logger.warning(msg=f"{client_ip} - Автор не найден")
            raise HTTPException(status_code=404, detail="Author not found")

        new_task = ToDoModel(
            title=task.title,
            description=task.description,
            author_name=author.username
        )
        new_task.author = author
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)

        task_response = TaskResponse(
            id=new_task.id,
            title=new_task.title,
            description=new_task.description,
            author_name=new_task.author_name,
            author=UserResponse.from_orm(author)
        )

        creation_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        notification_msg = (
            "✨ *New Task Created!* ✨\n\n"
            f"🆔 *ID:* `{new_task.id}`\n"
            f"📛 *Title:* `{new_task.title}`\n"
            f"📄 *Description:* `{new_task.description[:100] + "..."}`\n"
            f"👨‍💻 *Author:* `{new_task.author_name}`\n\n"
            "🔧 *Details Operation:*\n"
            f"   🌐 *IP:* `{client_ip}`\n"
            f"   🕒 *Time:* `{creation_time}`\n"
            f"   🖥️ *User-Agent:* \n`{truncate(user_agent, 50)}`\n\n"
            "✅ *Status:* `200` - *Success Created Task!*\n\n"
        )

        await rabbit_tasks_router.broker.publish(
            notification_msg,
            queue="user_actions"
        )

        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "create-task.html",
                context={
                    "request": request,
                    "task": task_response,
                    "message": "Task successfully created!"
                }
            )
        return task_response

    except Exception as e:
        await session.rollback()
        logger.warning(msg=f"{client_ip} - Ошибка при создании задачи - {e}", exc_info=True)
        if "text/html" in accept.lower():
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error": str(e)
                },
                status_code=500
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/", response_model=Union[PaginatedTasksResponse, Dict], status_code=200)
@rate_limit(max_calls=20, time_frame=10)
async def get_tasks(request: Request,
                    session: SessionDeep, redis: SessionRedis,
                    pagination: Pagintaion, accept: str = Header(default="application/json")) -> Any:
    """
    Отображает все имеющиеся таски и выводит их списком,
    не работает при отсутствии автора(хотя бы одного пользователя)
    :param accept:
    :param request:(request:from FastAPI import Request):
    :param redis:(dependencies:SessionRedis)
    :param session:(dependensis:SessionDeep)
    :param pagination:(dependensis: Pagination)
    :return: PaginatedTasksResponse - (schemas.tasks:PaginatedTasksResponse)
    """
    client_ip = request.client.host
    try:
        cache_key = f"tasks:{pagination.page}:{pagination.perPage}:{pagination.order}"
        count_key = "tasks_count"

        cache_tasks = await redis.get(cache_key)
        total_tasks = await redis.get(count_key)

        if total_tasks:
            total_tasks = int(total_tasks)

        if cache_tasks and total_tasks:
            logger.info(msg=f"{client_ip} - Данные о задаче получены из Redis")
            tasks_data = json.loads(cache_tasks)

            if "text/html" in accept.lower():
                total_pages = ceil(total_tasks / pagination.perPage) if total_tasks else 1
                pagination_data = {
                    "current_page": pagination.page,
                    "total_pages": total_pages,
                    "has_prev": pagination.page > 1,
                    "has_next": pagination.page < total_pages,
                    "next_num": pagination.page + 1,
                    "prev_num": pagination.page - 1,
                    "query_params": request.query_params,
                }
                return templates.TemplateResponse(
                    "tasks.html",
                    context={
                        "paginated_tasks": tasks_data,
                        "pagination": pagination_data,
                        "request": request,
                    }
                )
            return PaginatedTasksResponse(
                tasks=json.loads(cache_tasks),
                pagination={
                    "total": int(total_tasks),
                    "page": pagination.page,
                    "perPage": pagination.perPage,
                    "totalPages": (int(total_tasks) + pagination.perPage - 1) // pagination.perPage
                }
            )

        total_tasks = await session.scalar(select(func.count(ToDoModel.id)))
        total_tasks = int(total_tasks)
        query = select(ToDoModel).options(selectinload(ToDoModel.author))

        if pagination.order == SortEnum.ASC:
            query = query.order_by(ToDoModel.id.asc())
        else:
            query = query.order_by(ToDoModel.id.desc())

        query = query.limit(pagination.perPage).offset((pagination.page - 1) * pagination.perPage)
        tasks = await session.execute(query)
        tasks = tasks.scalars().all()

        if not tasks:
            raise HTTPException(status_code=404, detail="Tasks not found")

        tasks_responses = [TaskResponse.from_orm(task) for task in tasks]
        tasks_data = [task.dict() for task in tasks_responses]

        await redis.set(cache_key, json.dumps(tasks_data), ex=10)
        await redis.set(count_key, str(total_tasks), ex=30)


        if "text/html" in accept.lower():
            total_pages = ceil(total_tasks / pagination.perPage) if total_tasks else 1
            pagination_data = {
                "current_page": pagination.page,
                "total_pages": total_pages,
                "has_prev": pagination.page > 1,
                "has_next": pagination.page < total_pages,
                "next_num": pagination.page + 1,
                "prev_num": pagination.page - 1,
                "query_params": request.query_params,
            }
            return templates.TemplateResponse(
                "tasks.html",
                context={
                    "paginated_tasks": tasks_data,
                    "pagination": pagination_data,
                    "request": request,
                }
            )
        return PaginatedTasksResponse(
            tasks=tasks_responses,
            pagination={
                "total": total_tasks,
                "page": pagination.page,
                "perPage": pagination.perPage,
                "totalPages": (int(total_tasks) + pagination.perPage - 1) // pagination.perPage
            }
        )

    except Exception as e:
        logger.warning(msg=f"{client_ip} - Ошибка при получении всех зачад - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", status_code=200)
async def get_task(task_id: int, session: SessionDeep):
    """
    Ищет таску из БД, по айди
    :param task_id:int
    :param session:(dependensis:SessionDeep)
    :return: task[VT] - (basemethods:get_one())
    """
    try:
        task = await get_one(ToDoModel, task_id, session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if task is not None:
        return task
    logger.warning(msg=f"Не найдено созданных задач")
    raise HTTPException(status_code=404, detail="task not found")
