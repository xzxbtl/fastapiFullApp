from fastapi import HTTPException
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from PetProject.src.api.dependensis import SessionTokens
from PetProject.src.utils.token_generation import config
from PetProject.src.utils.token_generation import verify_jwt_token
from PetProject.src.utils.logs.logs import logger

router = APIRouter(tags=["FrontEnd 🌐"])
templates = Jinja2Templates(directory="/app/PetProject/src/public/templates")


@router.get("/", status_code=200)
async def get_home_page(request: Request):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)
    token_status = False

    if token:
        try:
            payload = await verify_jwt_token(token)
            token_status = True
        except HTTPException:
            token_status = False

    return templates.TemplateResponse(name="index.html",
                        context={"token_status": token_status, "request": request})


@router.get("/tasks/create/", status_code=200)
async def task_create_form_redirected(request: Request):
    return templates.TemplateResponse("create-task.html", {"request": request})


@router.get("/users/create/", status_code=200)
async def user_create_form_redirected(request: Request):
    return templates.TemplateResponse("create-user.html", {"request": request})


@router.get("/users/search/", status_code=200)
async def user_search_form_redirected(request: Request):
    return templates.TemplateResponse("search-user.html", {"request": request})


@router.get("/tasks/search/", status_code=200)
async def task_search_form_redirected(request: Request):
    return templates.TemplateResponse("search-task.html", {"request": request})


@router.get("/users/admin/search/", status_code=200)
async def user_edit_form_redirected(request: Request, token: SessionTokens):
    token = request.cookies.get(config.JWT_ACCESS_COOKIE_NAME)

    if token:
        payload = await verify_jwt_token(token)
        token_lvl = payload.get('lvl', 1)
        return templates.TemplateResponse(
            "edit-user.html", context={
                "request": request,
                "token_lvl": token_lvl
            }
        )
    else:
        raise HTTPException(status_code=401, detail="Unauthorized User")
