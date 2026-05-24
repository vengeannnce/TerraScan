from fastapi import APIRouter, File, Form, UploadFile

from app.models.response_models import ProcessingResponse
from app.services.interpolation_service import build_terrain_grid
from app.services.statistics_service import calculate_terrain_stats
from app.services.terrain_service import read_xyz_file

router = APIRouter()


@router.get("/")
def processing_status():
    return {"module": "processing", "status": "ready"}


@router.post("/", response_model=ProcessingResponse)
async def process_xyz_file(
    file: UploadFile = File(...),
    grid_size: int = Form(50),
):
    dataframe = await read_xyz_file(file)

    grid = build_terrain_grid(dataframe, grid_size=grid_size)
    stats = calculate_terrain_stats(dataframe)

    return {
        "filename": file.filename,
        "points_count": len(dataframe),
        "grid_size": grid_size,
        "grid": grid,
        "stats": stats,
        "status": "processed",
    }