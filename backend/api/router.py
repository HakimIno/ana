from fastapi import APIRouter
from api.endpoints import chat, files, models

api_router = APIRouter()

api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(files.router, tags=["files"])
api_router.include_router(models.router, tags=["models"])
