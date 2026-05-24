import pandas as pd


def calculate_terrain_stats(dataframe: pd.DataFrame) -> dict:
    return {
        "x_min": float(dataframe["x"].min()),
        "x_max": float(dataframe["x"].max()),
        "y_min": float(dataframe["y"].min()),
        "y_max": float(dataframe["y"].max()),
        "z_min": float(dataframe["z"].min()),
        "z_max": float(dataframe["z"].max()),
        "z_mean": float(dataframe["z"].mean()),
    }