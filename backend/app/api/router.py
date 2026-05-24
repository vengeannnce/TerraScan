from fastapi import APIRouter

from app.api.routes import upload, processing, stats, export

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(processing.router, prefix="/process", tags=["Processing"])
api_router.include_router(stats.router, prefix="/stats", tags=["Statistics"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])