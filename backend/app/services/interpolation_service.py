import numpy as np
import pandas as pd
from fastapi import HTTPException
from scipy.interpolate import griddata


def build_terrain_grid(dataframe: pd.DataFrame, grid_size: int = 50) -> dict:
    x_values = dataframe["x"].to_numpy()
    y_values = dataframe["y"].to_numpy()
    z_values = dataframe["z"].to_numpy()

    grid_x = np.linspace(x_values.min(), x_values.max(), grid_size)
    grid_y = np.linspace(y_values.min(), y_values.max(), grid_size)

    mesh_x, mesh_y = np.meshgrid(grid_x, grid_y)

    try:
        grid_z = griddata(
            points=(x_values, y_values),
            values=z_values,
            xi=(mesh_x, mesh_y),
            method="linear",
        )
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Could not interpolate terrain grid: {str(error)}",
        )

    if np.isnan(grid_z).any():
        nearest_grid_z = griddata(
            points=(x_values, y_values),
            values=z_values,
            xi=(mesh_x, mesh_y),
            method="nearest",
        )

        grid_z = np.where(np.isnan(grid_z), nearest_grid_z, grid_z)

    return {
        "x": grid_x.tolist(),
        "y": grid_y.tolist(),
        "z": grid_z.tolist(),
    }