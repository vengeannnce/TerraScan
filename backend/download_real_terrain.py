import os
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
import requests
from dotenv import load_dotenv
from rasterio.io import MemoryFile
from rasterio.transform import xy


load_dotenv()

API_KEY = os.getenv("OPENTOPOGRAPHY_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENTOPOGRAPHY_API_KEY is not set in backend/.env")

OUTPUT_FILE = Path("grand_canyon_real_xyz.csv")

# Real terrain area: Grand Canyon, Arizona
PARAMS = {
    "demtype": "SRTMGL1",
    "south": 36.05,
    "north": 36.25,
    "west": -112.25,
    "east": -112.05,
    "outputFormat": "GTiff",
    "API_Key": API_KEY,
}

URL = "https://portal.opentopography.org/API/globaldem"


def main():
    print("Downloading real terrain DEM from OpenTopography...")

    response = requests.get(URL, params=PARAMS, timeout=120)
    response.raise_for_status()

    with MemoryFile(response.content) as memory_file:
        with memory_file.open() as dataset:
            elevation = dataset.read(1)
            nodata = dataset.nodata

            if nodata is None:
                valid_mask = ~np.isnan(elevation)
            else:
                valid_mask = elevation != nodata

            rows, cols = np.where(valid_mask)
            values = elevation[rows, cols].astype(float)

            coordinates = [
                xy(dataset.transform, row, col)
                for row, col in zip(rows, cols)
            ]

            xs = [coord[0] for coord in coordinates]
            ys = [coord[1] for coord in coordinates]

            dataframe = pd.DataFrame(
                {
                    "x": xs,
                    "y": ys,
                    "z": values,
                }
            )

            dataframe = dataframe.dropna(subset=["x", "y", "z"])
            dataframe.to_csv(OUTPUT_FILE, index=False)

    print(f"Saved: {OUTPUT_FILE.resolve()}")
    print(f"Points: {len(dataframe):,}")


if __name__ == "__main__":
    main()