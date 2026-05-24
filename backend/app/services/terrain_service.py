from io import BytesIO

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.services.statistics_service import calculate_terrain_stats
from app.utils.validators import validate_file_extension, validate_xyz_columns


async def read_xyz_file(file: UploadFile) -> pd.DataFrame:
    validate_file_extension(file)

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    try:
        dataframe = pd.read_csv(
            BytesIO(content),
            sep=None,
            engine="python",
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read file: {str(error)}",
        )

    dataframe.columns = [str(column).strip().lower() for column in dataframe.columns]

    validate_xyz_columns(list(dataframe.columns))

    dataframe = dataframe[["x", "y", "z"]].copy()

    for column in ["x", "y", "z"]:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    dataframe = dataframe.dropna(subset=["x", "y", "z"])

    if dataframe.empty:
        raise HTTPException(
            status_code=400,
            detail="File does not contain valid XYZ numeric data",
        )

    return dataframe


async def process_uploaded_xyz_file(file: UploadFile) -> dict:
    dataframe = await read_xyz_file(file)

    stats = calculate_terrain_stats(dataframe)
    preview = dataframe.head(10).to_dict(orient="records")

    return {
        "filename": file.filename,
        "points_count": len(dataframe),
        "columns": ["x", "y", "z"],
        "preview": preview,
        "stats": stats,
        "status": "uploaded",
    }