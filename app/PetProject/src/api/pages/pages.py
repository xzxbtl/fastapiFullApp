from fastapi import HTTPException
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from PetProject.src.api.dependensis import SessionTokens
from PetProject.src.utils.token_generation import config
from PetProject.src.utils.token_generation import config, auth_middleware
from PetProject.src.utils.logs.logs import logger


router = APIRouter(tags=["FrontEnd 🌐"])
templates = Jinja2Templates(directory="/app/PetProject/src/public/templates")


async def get_auth_context(request: Request):
    context = {
        "request": request,
        "token_status": False,
        "token_lvl": 1,
        "username": None
    }

    if hasattr(request.state, 'user') and request.state.user.get("authenticated", False):
        context.update({
            "token_status": True,
            "token_lvl": request.state.user.get("lvl", 1),
            "username": request.state.user.get("sub")
        })

    logger.debug(f"Auth context: {context}")
    return context


@router.get("/")
async def get_home_page(request: Request):
    context = await get_auth_context(request)
    return templates.TemplateResponse("index.html", context=context)


@router.get("/tasks/create/", status_code=200)
async def task_create_form_redirected(request: Request):
    context = await get_auth_context(request)
    return templates.TemplateResponse("create-task.html", context=context)


@router.get("/users/create/", status_code=200)
async def user_create_form_redirected(request: Request):
    context = await get_auth_context(request)
    return templates.TemplateResponse("create-user.html", context=context)


@router.get("/users/search/", status_code=200)
async def user_search_form_redirected(request: Request):
    context = await get_auth_context(request)
    return templates.TemplateResponse("search-user.html", context=context)


@router.get("/tasks/search/", status_code=200)
async def task_search_form_redirected(request: Request):
    context = await get_auth_context(request)
    return templates.TemplateResponse("search-task.html", context=context)


@router.get("/users/admin/search/", status_code=200)
async def user_edit_form_redirected(request: Request):
    context = await get_auth_context(request)
    if not context["token_status"] or context["token_lvl"] < 2:
        raise HTTPException(status_code=403, detail="Forbidden")
    return templates.TemplateResponse("edit-user.html", context=context)


@router.get("/api/login/", status_code=200)
async def api_login_form_redirected(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/api/register/", status_code=200)
async def api_register_form_redirected(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})
