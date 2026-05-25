import numpy as np
import pandas as pd
from fastapi import HTTPException
from scipy.spatial import Delaunay


MIN_TIN_POINTS = 100
MAX_TIN_POINTS = 250_000


def _round_vertices(array: np.ndarray, decimals: int = 3) -> list[list[float]]:
    rounded = np.round(array.astype(np.float32), decimals)
    return rounded.tolist()


def _sample_dataframe(dataframe: pd.DataFrame, max_points: int) -> pd.DataFrame:
    if len(dataframe) <= max_points:
        return dataframe.copy()

    return dataframe.sample(
        n=max_points,
        random_state=42,
    ).copy()


def build_tin_mesh(dataframe: pd.DataFrame, max_points: int = 50_000) -> dict:
    if max_points < MIN_TIN_POINTS:
        raise HTTPException(
            status_code=400,
            detail=f"tin_max_points must be at least {MIN_TIN_POINTS}",
        )

    if max_points > MAX_TIN_POINTS:
        raise HTTPException(
            status_code=400,
            detail=f"tin_max_points is too large. Maximum allowed value is {MAX_TIN_POINTS}",
        )

    clean_dataframe = dataframe[["x", "y", "z"]].dropna().copy()

    clean_dataframe = clean_dataframe.drop_duplicates(subset=["x", "y"])

    if len(clean_dataframe) < 3:
        raise HTTPException(
            status_code=400,
            detail="Not enough unique XYZ points to build TIN mesh",
        )

    sampled_dataframe = _sample_dataframe(clean_dataframe, max_points)

    points_2d = sampled_dataframe[["x", "y"]].to_numpy(dtype=np.float32)
    z_values = sampled_dataframe["z"].to_numpy(dtype=np.float32)

    try:
        triangulation = Delaunay(points_2d)
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not build TIN mesh: {str(error)}",
        )

    vertices = np.column_stack(
        (
            points_2d[:, 0],
            points_2d[:, 1],
            z_values,
        )
    )

    faces = triangulation.simplices.astype(np.int32)

    return {
        "vertices": _round_vertices(vertices),
        "faces": faces.tolist(),
        "source_points_count": int(len(clean_dataframe)),
        "mesh_points_count": int(len(vertices)),
        "triangles_count": int(len(faces)),
        "max_points": int(max_points),
    }