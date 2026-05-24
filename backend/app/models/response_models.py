from pydantic import BaseModel


class TerrainStats(BaseModel):
    x_min: float
    x_max: float
    y_min: float
    y_max: float
    z_min: float
    z_max: float
    z_mean: float


class UploadResponse(BaseModel):
    filename: str
    points_count: int
    columns: list[str]
    preview: list[dict[str, float]]
    stats: TerrainStats
    status: str