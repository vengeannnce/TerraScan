import numpy as np
import pandas as pd
from fastapi import HTTPException
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree


def _round_array(array: np.ndarray, decimals: int = 3) -> np.ndarray:
    return np.round(array.astype(np.float32), decimals)


def _fill_nan_grid(grid_z: np.ndarray) -> np.ndarray:
    dataframe = pd.DataFrame(grid_z)

    dataframe = dataframe.interpolate(axis=0, limit_direction="both")
    dataframe = dataframe.interpolate(axis=1, limit_direction="both")
    dataframe = dataframe.ffill(axis=0).bfill(axis=0).ffill(axis=1).bfill(axis=1)

    return dataframe.to_numpy(dtype=np.float32)


def _try_build_regular_grid(dataframe: pd.DataFrame, grid_size: int) -> dict | None:
    unique_x = np.sort(dataframe["x"].unique())
    unique_y = np.sort(dataframe["y"].unique())

    expected_points = len(unique_x) * len(unique_y)

    # Если данные похожи на регулярную сетку, не делаем дорогую интерполяцию
    if expected_points != len(dataframe):
        return None

    pivot = dataframe.pivot_table(
        index="y",
        columns="x",
        values="z",
        aggfunc="mean",
    )

    pivot = pivot.reindex(index=unique_y, columns=unique_x)

    grid_z = pivot.to_numpy(dtype=np.float32)

    if np.isnan(grid_z).any():
        grid_z = _fill_nan_grid(grid_z)

    x_indices = np.linspace(0, len(unique_x) - 1, grid_size).round().astype(int)
    y_indices = np.linspace(0, len(unique_y) - 1, grid_size).round().astype(int)

    grid_x = unique_x[x_indices]
    grid_y = unique_y[y_indices]
    grid_z = grid_z[np.ix_(y_indices, x_indices)]

    grid_z = gaussian_filter(grid_z, sigma=0.6)

    return {
        "x": _round_array(grid_x).tolist(),
        "y": _round_array(grid_y).tolist(),
        "z": _round_array(grid_z).tolist(),
    }


def _build_idw_grid(dataframe: pd.DataFrame, grid_size: int) -> dict:
    x_values = dataframe["x"].to_numpy(dtype=np.float32)
    y_values = dataframe["y"].to_numpy(dtype=np.float32)
    z_values = dataframe["z"].to_numpy(dtype=np.float32)

    grid_x = np.linspace(x_values.min(), x_values.max(), grid_size, dtype=np.float32)
    grid_y = np.linspace(y_values.min(), y_values.max(), grid_size, dtype=np.float32)

    mesh_x, mesh_y = np.meshgrid(grid_x, grid_y)

    source_points = np.column_stack((x_values, y_values))
    tree = cKDTree(source_points)

    target_points = np.column_stack((mesh_x.ravel(), mesh_y.ravel()))

    k = min(8, len(source_points))
    chunk_size = 100_000

    result_z = np.empty(len(target_points), dtype=np.float32)

    for start in range(0, len(target_points), chunk_size):
        end = start + chunk_size
        chunk = target_points[start:end]

        distances, indices = tree.query(chunk, k=k, workers=-1)

        if k == 1:
            result_z[start:end] = z_values[indices]
            continue

        distances = np.maximum(distances, 1e-6)
        weights = 1.0 / (distances ** 2)

        weighted_z = np.sum(weights * z_values[indices], axis=1)
        weights_sum = np.sum(weights, axis=1)

        result_z[start:end] = weighted_z / weights_sum

    grid_z = result_z.reshape((grid_size, grid_size))

    grid_z = gaussian_filter(grid_z, sigma=0.6)

    return {
        "x": _round_array(grid_x).tolist(),
        "y": _round_array(grid_y).tolist(),
        "z": _round_array(grid_z).tolist(),
    }


def build_terrain_grid(dataframe: pd.DataFrame, grid_size: int = 50) -> dict:
    if grid_size < 5:
        raise HTTPException(
            status_code=400,
            detail="grid_size must be at least 5",
        )

    if grid_size > 1000:
        raise HTTPException(
            status_code=400,
            detail="grid_size is too large. Maximum allowed value is 1000",
        )

    regular_grid = _try_build_regular_grid(dataframe, grid_size)

    if regular_grid is not None:
        return regular_grid

    return _build_idw_grid(dataframe, grid_size)