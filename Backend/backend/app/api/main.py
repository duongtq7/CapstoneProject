from fastapi import APIRouter

from app.api.routes import albums, login, media, users, search

# from app.api.routes import private, utils

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(albums.router, prefix="/albums", tags=["albums"])
api_router.include_router(media.router, prefix="/media", tags=["media"])
api_router.include_router(search.router, prefix="/search", tags=["search"])

# if settings.ENVIRONMENT == "local":
#     api_router.include_router(private.router)
