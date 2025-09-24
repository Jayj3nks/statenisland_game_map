import json, math, os
from pathlib import Path

import geopandas as gpd
import numpy as np
from rasterio import features
from rasterio.transform import from_origin
from shapely.ops import unary_union
from shapely.geometry import mapping
import networkx as nx

# -----------------------
# CONFIG
# -----------------------
DATA = Path("staten_island_osm")
OUT  = Path("game_tiles")
OUT.mkdir(exist_ok=True)

CELL_M = 5.0                    # meters per grid cell
TILE   = 256                    # cells per tile (tile size)
CRS_UTM = "EPSG:32618"          # UTM zone 18N (meters)

# Input files you already made
F_BUILDINGS = DATA / "buildings.geojson"
F_BUILD_CT  = DATA / "building_centroids.geojson"  # optional hotspots
F_SHOPS     = DATA / "shops.geojson"
F_ROADS     = DATA / "roads.geojson"
F_GREEN     = DATA / "landuse_green.geojson"
F_WATER     = DATA / "water.geojson"               # if you wrote it; else derive from green file for now

# -----------------------
# LOAD + STANDARDIZE CRS
# -----------------------
def read_gj(p):
    if not p.exists(): return None
    gdf = gpd.read_file(p)
    if gdf.empty: return None
    if gdf.crs is None: gdf.set_crs("EPSG:4326", inplace=True)
    gdf = gdf.to_crs(CRS_UTM)
    return gdf

buildings = read_gj(F_BUILDINGS)
shops     = read_gj(F_SHOPS)
roads     = read_gj(F_ROADS)
green     = read_gj(F_GREEN)
water     = read_gj(F_WATER) if F_WATER.exists() else None

# Fallback: create a “water” subset from green where natural==water if present
if water is None:
    water = green[green.get("natural").fillna("").str.contains("water|bay|strait")].copy() if green is not None else None

# World bounds from everything
layers = [g for g in [buildings, shops, roads, green, water] if g is not None and not g.empty]
assert layers, "No layers found!"
bounds = gpd.GeoSeries([unary_union([g.unary_union for g in layers])], crs=CRS_UTM).total_bounds
xmin, ymin, xmax, ymax = bounds

# Align bounds to CELL_M
def snap_down(v, q): return math.floor(v / q) * q
def snap_up(v, q):   return math.ceil(v / q)  * q

xmin = snap_down(xmin, CELL_M)
ymin = snap_down(ymin, CELL_M)
xmax = snap_up(xmax, CELL_M)
ymax = snap_up(ymax, CELL_M)

width  = int(round((xmax - xmin) / CELL_M))
height = int(round((ymax - ymin) / CELL_M))

transform = from_origin(xmin, ymax, CELL_M, CELL_M)  # affine

print(f"Grid: {width}×{height} cells @ {CELL_M} m (≈ {width*CELL_M/1000:.1f} km × {height*CELL_M/1000:.1f} km)")

# -----------------------
# RASTERIZE PER CLASS
# -----------------------
GRID = np.zeros((height, width), dtype=np.uint8)

def burn(gdf, value, all_touched=False):
    if gdf is None or gdf.empty: return
    shapes = ((geom, value) for geom in gdf.geometry if geom and not geom.is_empty)
    arr = features.rasterize(
        shapes=shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=all_touched,
        dtype=np.uint8
    )
    # priority write: nonzeros in arr overwrite GRID
    mask = arr > 0
    GRID[mask] = arr[mask]

# Make quick subsets
roads_like = roads
parks_like = green
water_like = water
buildings_like = buildings

# Burn in priority order (lower first, top last)
burn(parks_like,    2, all_touched=True)
burn(roads_like,    1, all_touched=True)
burn(buildings_like,4, all_touched=True)
burn(water_like,    3, all_touched=True)

# Optional retail hotspots mask
retail_mask = None
if shops is not None and not shops.empty:
    arr = features.rasterize(
        ((geom, 5) for geom in shops.geometry),
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8
    )
    retail_mask = arr == 5

# Save the master grid
np.save(OUT / "grid_uint8.npy", GRID)

legend = {
    "cell_meters": CELL_M,
    "classes": { "0":"empty","1":"road","2":"park","3":"water","4":"building","5":"retail" },
    "transform": {  # rasterio-style affine (from_origin)
        "xmin": xmin, "ymax": ymax, "cell": CELL_M, "crs": CRS_UTM
    },
    "grid_size": [int(height), int(width)],
    "tile": TILE
}
with open(OUT / "metadata.json", "w") as f:
    json.dump(legend, f, indent=2)

# -----------------------
# CHUNK TO PNG TILES
# -----------------------
from PIL import Image

tiles_dir = OUT / "tiles"
tiles_dir.mkdir(exist_ok=True)

def save_tile(y0, x0):
    tile = GRID[y0:y0+TILE, x0:x0+TILE]
    if tile.size == 0: return
    # pad edges
    ty, tx = tile.shape
    if ty < TILE or tx < TILE:
        pad = np.zeros((TILE, TILE), dtype=np.uint8)
        pad[:ty, :tx] = tile
        tile = pad
    img = Image.fromarray(tile, mode="L")
    img.save(tiles_dir / f"t_{y0//TILE}_{x0//TILE}.png")

for y0 in range(0, height, TILE):
    for x0 in range(0, width, TILE):
        save_tile(y0, x0)

print("Tiles written to", tiles_dir)

# -----------------------
# ROAD GRAPH EXPORT (for AI)
# -----------------------
# Build graph by reading lines as edges between sampled points
G = nx.Graph()
if roads_like is not None and not roads_like.empty:
    for _, row in roads_like.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty: continue
        if geom.geom_type == "LineString":
            coords = list(geom.coords)
        elif geom.geom_type == "MultiLineString":
            coords = [c for ls in geom.geoms for c in ls.coords]
        else:
            continue

        # sample every ~25 m to keep graph reasonable
        last = None
        acc = 0.0
        for i in range(1, len(coords)):
            x1,y1 = coords[i-1]
            x2,y2 = coords[i]
            seg_len = math.hypot(x2-x1, y2-y1)
            if last is None:
                last = (x1,y1)
                G.add_node(last)
            acc += seg_len
            if acc >= 25 or i == len(coords)-1:
                cur = (x2,y2)
                G.add_node(cur)
                G.add_edge(last, cur, length=math.hypot(cur[0]-last[0], cur[1]-last[1]))
                last = cur
                acc = 0.0

# serialize
graph_json = {
    "crs": CRS_UTM,
    "nodes": [{"id": i, "x": n[0], "y": n[1]} for i, n in enumerate(G.nodes)],
    "edges": [{"u": list(G.nodes).index(u), "v": list(G.nodes).index(v), "len": d["length"]} for u, v, d in G.edges(data=True)]
}
with open(OUT / "roads_graph.json", "w") as f:
    json.dump(graph_json, f)

# -----------------------
# BUILDING COLLIDERS (simplified)
# -----------------------
if buildings_like is not None and not buildings_like.empty:
    b = buildings_like.copy()
    # dissolve small slivers and simplify for runtime
    b["geom"] = b.geometry.buffer(0.5).simplify(0.7)  # tune meters
    b = gpd.GeoDataFrame(geometry=b["geom"], crs=CRS_UTM)
    b.to_crs("EPSG:4326").to_file(OUT / "building_colliders.geojson", driver="GeoJSON")

print("Done.")

