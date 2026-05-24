from fastapi import APIRouter, File, UploadFile

from app.models.response_models import UploadResponse
from app.services.terrain_service import process_uploaded_xyz_file

router = APIRouter()


@router.get("/")
def upload_status():
    return {"module": "upload", "status": "ready"}


@router.post("/", response_model=UploadResponse)
async def upload_xyz_file(file: UploadFile = File(...)):
    return await process_uploaded_xyz_file(file)