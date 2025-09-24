import json, math, os, csv
from pathlib import Path

import geopandas as gpd
import numpy as np
from rasterio import features
from rasterio.transform import from_origin
from shapely.ops import unary_union
from shapely.geometry import mapping, Polygon
import networkx as nx

# -----------------------
# CONFIG
# -----------------------
DATA = Path("staten_island_osm")
OUT  = Path("game_tiles")
OUT.mkdir(exist_ok=True)

CELL_M = 5.0                    # meters per grid cell (massive 2D world!)
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

print("[INFO] Loading GeoJSON files...")
buildings = read_gj(F_BUILDINGS)
shops     = read_gj(F_SHOPS)
roads     = read_gj(F_ROADS)
green     = read_gj(F_GREEN)
water     = read_gj(F_WATER) if F_WATER.exists() else None

# Fallback: create a "water" subset from green where natural==water if present
if water is None and green is not None:
    water = green[green.get("natural").fillna("").str.contains("water|bay|strait")].copy()

print(f"[LOADED] Buildings: {len(buildings) if buildings is not None else 0}")
print(f"[LOADED] Shops: {len(shops) if shops is not None else 0}")
print(f"[LOADED] Roads: {len(roads) if roads is not None else 0}")
print(f"[LOADED] Green areas: {len(green) if green is not None else 0}")
print(f"[LOADED] Water: {len(water) if water is not None else 0}")

# World bounds from everything
layers = [g for g in [buildings, shops, roads, green, water] if g is not None and not g.empty]
assert layers, "No layers found!"
bounds = gpd.GeoSeries([unary_union([g.unary_union for g in layers])], crs=CRS_UTM).total_bounds
xmin, ymin, xmax, ymax = bounds

print(f"[BOUNDS] X: {xmin:.0f} to {xmax:.0f} meters ({(xmax-xmin)/1000:.1f} km)")
print(f"[BOUNDS] Y: {ymin:.0f} to {ymax:.0f} meters ({(ymax-ymin)/1000:.1f} km)")

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

print(f"[GRID] {width}×{height} cells @ {CELL_M}m = {width*CELL_M/1000:.1f}km × {height*CELL_M/1000:.1f}km")
print(f"[GRID] Total cells: {width*height:,}")

# -----------------------
# RASTERIZE PER CLASS
# -----------------------
GRID = np.zeros((height, width), dtype=np.uint8)

# Create a Staten Island boundary polygon for "Land" areas
print("[INFO] Creating Staten Island land boundary...")
all_geoms = []
for layer in layers:
    if layer is not None and not layer.empty:
        all_geoms.extend(layer.geometry.tolist())

# Create convex hull or union of all features to define land area
if all_geoms:
    staten_island_boundary = unary_union(all_geoms)
    # Buffer it slightly to ensure all land is covered
    if hasattr(staten_island_boundary, 'buffer'):
        staten_island_boundary = staten_island_boundary.buffer(50)  # 50 meter buffer
    
    # Fill entire land area with "land" first (tile type 6)
    print("[INFO] Rasterizing land areas...")
    land_shapes = [(staten_island_boundary, 6)]
    land_arr = features.rasterize(
        shapes=land_shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8
    )
    # Apply land mask - only where there's actual land
    land_mask = land_arr == 6
    GRID[land_mask] = 6

def burn(gdf, value, all_touched=False, description=""):
    if gdf is None or gdf.empty: 
        print(f"[SKIP] {description} - no data")
        return
    print(f"[BURN] {description} - {len(gdf)} features as tile type {value}")
    
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

# Separate different landuse types
parks_like = None
roads_like = roads
water_like = water
buildings_like = buildings

# Create parks from green data
if green is not None:
    # Parks, woods, natural areas (green tiles)
    park_conditions = (
        green.get("leisure").fillna("").str.contains("park") |
        green.get("natural").fillna("").str.contains("wood|scrub|grassland") |
        green.get("landuse").fillna("").str.contains("meadow|grass")
    )
    parks_like = green[park_conditions].copy() if park_conditions.any() else None

print("\n[INFO] Burning layers in priority order (lower = overwritten by higher)...")

# Burn in priority order (lower first, top last)
# 0: empty/ocean, 1: road (gray), 2: park (green), 3: water (blue), 
# 4: building, 5: retail, 6: land (light brown/beige)

# Land is already applied as base layer
burn(parks_like,    2, all_touched=True, description="Parks & Green Areas")
burn(roads_like,    1, all_touched=True, description="Roads & Streets")  
burn(buildings_like,4, all_touched=True, description="Buildings")
burn(water_like,    3, all_touched=True, description="Water Bodies")

# Optional retail hotspots mask
retail_mask = None
if shops is not None and not shops.empty:
    print(f"[BURN] Retail hotspots - {len(shops)} shops as tile type 5")
    arr = features.rasterize(
        ((geom, 5) for geom in shops.geometry),
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8
    )
    retail_mask = arr == 5
    # Apply retail mask on top of buildings where shops exist
    GRID[retail_mask] = 5

# Save the master grid
print(f"\n[SAVE] Master grid: {OUT / 'grid_uint8.npy'}")
np.save(OUT / "grid_uint8.npy", GRID)

# Count tile types
unique, counts = np.unique(GRID, return_counts=True)
tile_counts = dict(zip(unique, counts))

print(f"\n[STATS] Tile distribution:")
for tile_type, count in tile_counts.items():
    percentage = (count / (width * height)) * 100
    print(f"  Type {tile_type}: {count:,} cells ({percentage:.1f}%)")

legend = {
    "cell_meters": CELL_M,
    "classes": { 
        "0":"empty/ocean",
        "1":"road", 
        "2":"park", 
        "3":"water", 
        "4":"building",
        "5":"retail",
        "6":"land"
    },
    "colors": {
        "0":"#000080",  # dark blue for ocean
        "1":"#808080",  # gray for roads
        "2":"#00FF00",  # green for parks
        "3":"#0080FF",  # blue for water
        "4":"#A0A0A0",  # light gray for buildings
        "5":"#FF8000",  # orange for retail
        "6":"#D2B48C"   # tan/beige for general land
    },
    "transform": {
        "xmin": xmin, "ymax": ymax, "cell": CELL_M, "crs": CRS_UTM
    },
    "grid_size": [int(height), int(width)],
    "tile_size": TILE,
    "real_world_size_km": {
        "width": round((xmax-xmin)/1000, 1),
        "height": round((ymax-ymin)/1000, 1)
    },
    "tile_counts": tile_counts
}

print(f"[SAVE] Metadata: {OUT / 'metadata.json'}")
with open(OUT / "metadata.json", "w") as f:
    json.dump(legend, f, indent=2)

# -----------------------
# EXPORT AS CSV
# -----------------------
print(f"[SAVE] CSV tilemap: {OUT / 'tilemap.csv'}")
with open(OUT / "tilemap.csv", "w", newline='') as f:
    writer = csv.writer(f)
    # Header with metadata
    writer.writerow([f"# Staten Island 2D Game Tilemap"])
    writer.writerow([f"# Grid Size: {width}x{height} cells"])
    writer.writerow([f"# Cell Size: {CELL_M}m per cell"])
    writer.writerow([f"# Real Size: {(xmax-xmin)/1000:.1f}km x {(ymax-ymin)/1000:.1f}km"])
    writer.writerow([f"# Tile Types: 0=ocean, 1=road(gray), 2=park(green), 3=water(blue), 4=building, 5=retail, 6=land(beige)"])
    writer.writerow([])  # Empty row separator
    
    # Write the grid data
    for row in GRID:
        writer.writerow(row)

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

print(f"[SAVE] PNG tiles: {tiles_dir}")
tile_count = 0
for y0 in range(0, height, TILE):
    for x0 in range(0, width, TILE):
        save_tile(y0, x0)
        tile_count += 1

print(f"[TILES] Generated {tile_count} PNG tiles ({TILE}x{TILE} each)")

# -----------------------
# ROAD GRAPH EXPORT (for AI)
# -----------------------
print("[INFO] Building road graph for AI navigation...")
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

print(f"[SAVE] Road graph: {OUT / 'roads_graph.json'} ({len(G.nodes)} nodes, {len(G.edges)} edges)")
with open(OUT / "roads_graph.json", "w") as f:
    json.dump(graph_json, f)

# -----------------------
# BUILDING COLLIDERS (simplified)
# -----------------------
if buildings_like is not None and not buildings_like.empty:
    print("[INFO] Creating building colliders...")
    b = buildings_like.copy()
    # dissolve small slivers and simplify for runtime
    b["geom"] = b.geometry.buffer(0.5).simplify(0.7)  # tune meters
    b = gpd.GeoDataFrame(geometry=b["geom"], crs=CRS_UTM)
    b.to_crs("EPSG:4326").to_file(OUT / "building_colliders.geojson", driver="GeoJSON")
    print(f"[SAVE] Building colliders: {OUT / 'building_colliders.geojson'}")

print(f"\n🎮 MASSIVE 2D STATEN ISLAND MAP COMPLETE! 🎮")
print(f"   📐 Grid: {width:,} × {height:,} cells ({width*height:,} total)")
print(f"   🌍 Size: {(xmax-xmin)/1000:.1f}km × {(ymax-ymin)/1000:.1f}km")
print(f"   📏 Resolution: {CELL_M}m per cell")
print(f"   🎨 Tile Types: 7 different terrain types")
print(f"   💾 Files: JSON metadata, CSV tilemap, PNG tiles, road graph")
print(f"   📂 Output directory: {OUT}")
print(f"\n🚀 Ready for 2D game development!")