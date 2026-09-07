"""Build Blender/game-ready Staten Island elevation files from USGS 3DEP tiles."""

import json
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from PIL import Image
from rasterio.features import geometry_mask
from rasterio.merge import merge
from rasterio.vrt import WarpedVRT
from rasterio.enums import Resampling


SOURCE_DIR = Path("data/elevation/source_1m")
COUNTIES = Path("/tmp/tl_2025_us_county/tl_2025_us_county.shp")
OUT_DIR = Path("data/elevation")
TARGET_CRS = "EPSG:32618"  # same CRS used by make_tiles.py
RESOLUTION_M = 5.0
NODATA = -9999.0


def snap_down(value: float, size: float) -> float:
    return math.floor(value / size) * size


def snap_up(value: float, size: float) -> float:
    return math.ceil(value / size) * size


OUT_DIR.mkdir(parents=True, exist_ok=True)
tiles = sorted(SOURCE_DIR.glob("*.tif"))
if not tiles:
    raise SystemExit(f"No source GeoTIFFs found in {SOURCE_DIR}")

counties = gpd.read_file(COUNTIES)
island = counties[(counties["STATEFP"] == "36") & (counties["COUNTYFP"] == "085")]
if len(island) != 1:
    raise SystemExit("Could not uniquely select Richmond County, NY (FIPS 36085)")
island = island.to_crs(TARGET_CRS)
geom = island.geometry.iloc[0]
minx, miny, maxx, maxy = geom.bounds
bounds = (
    snap_down(minx, RESOLUTION_M),
    snap_down(miny, RESOLUTION_M),
    snap_up(maxx, RESOLUTION_M),
    snap_up(maxy, RESOLUTION_M),
)

datasets = [rasterio.open(path) for path in tiles]
vrts = [
    WarpedVRT(
        src,
        crs=TARGET_CRS,
        resampling=Resampling.bilinear,
        nodata=NODATA,
    )
    for src in datasets
]

try:
    mosaic, transform = merge(
        vrts,
        bounds=bounds,
        res=RESOLUTION_M,
        nodata=NODATA,
        dtype="float32",
        method="first",
    )
finally:
    for vrt in vrts:
        vrt.close()
    for src in datasets:
        src.close()

dem = mosaic[0]
inside = geometry_mask(
    [geom.__geo_interface__],
    out_shape=dem.shape,
    transform=transform,
    invert=True,
)
valid = inside & np.isfinite(dem) & (dem != NODATA)
dem[~valid] = NODATA

tif_path = OUT_DIR / "staten_island_dem_5m.tif"
with rasterio.open(
    tif_path,
    "w",
    driver="GTiff",
    height=dem.shape[0],
    width=dem.shape[1],
    count=1,
    dtype="float32",
    crs=TARGET_CRS,
    transform=transform,
    nodata=NODATA,
    compress="DEFLATE",
    predictor=3,
    tiled=True,
    blockxsize=256,
    blockysize=256,
) as dst:
    dst.write(dem, 1)

min_elev = float(np.min(dem[valid]))
max_elev = float(np.max(dem[valid]))
# Blender terrain should meet the ocean at zero; retain the original negative
# coastal/bathymetric values in the GeoTIFF, but clamp them in the PNG.
heightmap_min_elev = 0.0
height_range = max_elev - heightmap_min_elev
normalized = np.zeros(dem.shape, dtype=np.uint16)
normalized[valid] = np.round(
    np.clip((dem[valid] - heightmap_min_elev) / height_range, 0.0, 1.0) * 65535.0
).astype(np.uint16)
png_path = OUT_DIR / "staten_island_heightmap_16bit.png"
Image.fromarray(normalized).save(png_path)

metadata = {
    "source": "USGS 3DEP one-meter bare-earth DEM, NY CMPG 2013",
    "source_vertical_datum": "NAVD88",
    "output_crs": TARGET_CRS,
    "output_resolution_m": RESOLUTION_M,
    "bounds_m": list(bounds),
    "width_px": int(dem.shape[1]),
    "height_px": int(dem.shape[0]),
    "nodata": NODATA,
    "min_elevation_m": min_elev,
    "max_elevation_m": max_elev,
    "heightmap_min_elevation_m": heightmap_min_elev,
    "heightmap_encoding": "uint16 = round(clamp(elevation_m, 0, max_elevation_m) / max_elevation_m * 65535)",
}
(OUT_DIR / "staten_island_elevation_metadata.json").write_text(
    json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps(metadata, indent=2))
