from fastapi import APIRouter
from PetProject.src.api.tasks import router as tasks_router
from PetProject.src.api.users import router as users_router
from PetProject.src.api.login import router as login_router
from PetProject.src.api.pages.pages import router as pages_router


main_router = APIRouter()
main_router.include_router(tasks_router)
main_router.include_router(users_router)
main_router.include_router(login_router)
main_router.include_router(pages_router)
