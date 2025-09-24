import json, math, os, csv
from pathlib import Path
import geopandas as gpd
import numpy as np
from rasterio import features
from rasterio.transform import from_origin
from shapely.ops import unary_union
from shapely.geometry import mapping, Polygon, box
import networkx as nx
from PIL import Image, ImageDraw
import warnings
import pandas as pd
from scipy.interpolate import griddata
warnings.filterwarnings('ignore')

print("🏔️ STATEN ISLAND TOPOGRAPHIC 2D MAP GENERATOR")
print("=" * 60)

# -----------------------
# CONFIG
# -----------------------
DATA = Path("staten_island_osm")
OUT  = Path("game_tiles_topographic")
OUT.mkdir(exist_ok=True)

CELL_M = 5.0                    # meters per grid cell
TILE_SIZE = 256                 # cells per tile (256x256)
CRS_UTM = "EPSG:32618"          # UTM zone 18N (meters)

print(f"🗺️ Configuration:")
print(f"   • Cell size: {CELL_M}m per cell")
print(f"   • Tile size: {TILE_SIZE}x{TILE_SIZE} cells")
print(f"   • CRS: {CRS_UTM}")
print(f"   • Enhanced: Topography + Original Terrain")

# -----------------------
# LOAD DATA EFFICIENTLY
# -----------------------
def read_geofile(filepath, chunk_size=10000):
    """Read large GeoJSON files in chunks to save memory."""
    if not filepath.exists():
        return None
    
    print(f"📂 Loading {filepath.name}...")
    gdf = gpd.read_file(filepath)
    
    if gdf.empty:
        return None
    
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    
    gdf = gdf.to_crs(CRS_UTM)
    
    if len(gdf) > chunk_size:
        print(f"   • Large dataset ({len(gdf)} features), simplifying...")
        gdf['geometry'] = gdf.geometry.simplify(2.0)
    
    return gdf

# Load data files
print("\n📊 Loading Staten Island data...")
buildings = read_geofile(DATA / "buildings.geojson") if (DATA / "buildings.geojson").exists() else None
if not buildings:
    # Try compressed version
    import gzip
    try:
        with gzip.open("game_tiles_compressed/buildings.geojson.gz", 'rt') as f:
            buildings = gpd.read_file(f)
            buildings = buildings.to_crs(CRS_UTM)
        print("📂 Loaded buildings from compressed file...")
    except:
        pass

shops = read_geofile(DATA / "shops.geojson")
roads = read_geofile(DATA / "roads.geojson")
green = read_geofile(DATA / "landuse_green.geojson")
water = read_geofile(DATA / "water.geojson")

print(f"\n✅ Data loaded:")
if buildings is not None: print(f"   • Buildings: {len(buildings):,} features")
if shops is not None: print(f"   • Shops: {len(shops):,} features") 
if roads is not None: print(f"   • Roads: {len(roads):,} features")
if green is not None: print(f"   • Green areas: {len(green):,} features")
if water is not None: print(f"   • Water bodies: {len(water):,} features")

# -----------------------
# EXTRACT ELEVATION DATA
# -----------------------
print("\n🏔️ Extracting elevation data for topography...")

elevation_points = []

# Extract elevation from green areas
if green is not None and 'ele' in green.columns:
    green_ele = green[green['ele'].notna()].copy()
    if not green_ele.empty:
        for idx, row in green_ele.iterrows():
            try:
                ele_val = float(row['ele'])
                geom = row.geometry
                if geom and hasattr(geom, 'centroid'):
                    centroid = geom.centroid
                    elevation_points.append({
                        'x': centroid.x,
                        'y': centroid.y, 
                        'elevation': ele_val,
                        'source': 'landuse'
                    })
            except (ValueError, TypeError):
                continue
        print(f"   🌳 Extracted {len([p for p in elevation_points if p['source'] == 'landuse'])} elevation points from landuse")

# Extract elevation from water bodies
if water is not None and 'ele' in water.columns:
    water_ele = water[water['ele'].notna()].copy()
    if not water_ele.empty:
        for idx, row in water_ele.iterrows():
            try:
                ele_val = float(row['ele'])
                geom = row.geometry
                if geom and hasattr(geom, 'centroid'):
                    centroid = geom.centroid
                    elevation_points.append({
                        'x': centroid.x,
                        'y': centroid.y,
                        'elevation': ele_val,
                        'source': 'water'
                    })
            except (ValueError, TypeError):
                continue
        print(f"   💧 Extracted {len([p for p in elevation_points if p['source'] == 'water'])} elevation points from water")

if elevation_points:
    elevations = [p['elevation'] for p in elevation_points]
    print(f"\n📊 Elevation Statistics:")
    print(f"   • Total elevation points: {len(elevation_points)}")
    print(f"   • Elevation range: {min(elevations):.1f}m to {max(elevations):.1f}m")
    print(f"   • Mean elevation: {np.mean(elevations):.1f}m")
else:
    print(f"   ⚠️ No elevation data found, creating flat topography")

# -----------------------
# CALCULATE BOUNDS
# -----------------------
print("\n🌍 Calculating world bounds...")

all_bounds = []
if buildings is not None: all_bounds.append(buildings.total_bounds)
if shops is not None: all_bounds.append(shops.total_bounds)  
if roads is not None: all_bounds.append(roads.total_bounds)
if green is not None: all_bounds.append(green.total_bounds)
if water is not None: all_bounds.append(water.total_bounds)

if not all_bounds:
    raise ValueError("No data found!")

bounds = np.array(all_bounds)
xmin = bounds[:, 0].min()
ymin = bounds[:, 1].min()
xmax = bounds[:, 2].max()
ymax = bounds[:, 3].max()

def snap_down(v, q): return math.floor(v / q) * q
def snap_up(v, q): return math.ceil(v / q) * q

xmin = snap_down(xmin, CELL_M)
ymin = snap_down(ymin, CELL_M)
xmax = snap_up(xmax, CELL_M)
ymax = snap_up(ymax, CELL_M)

width = int(round((xmax - xmin) / CELL_M))
height = int(round((ymax - ymin) / CELL_M))
transform = from_origin(xmin, ymax, CELL_M, CELL_M)

print(f"\n📏 Grid specifications:")
print(f"   • Grid size: {width:,} × {height:,} cells")
print(f"   • Real size: {width*CELL_M/1000:.1f}km × {height*CELL_M/1000:.1f}km")
print(f"   • Total cells: {width*height:,}")

# -----------------------
# CREATE ELEVATION GRID
# -----------------------
print(f"\n🏔️ Creating elevation interpolation grid...")

ELEVATION_GRID = np.zeros((height, width), dtype=np.float32)

if elevation_points:
    # Create coordinate arrays for interpolation
    xi = np.arange(xmin, xmax, CELL_M) + CELL_M/2  # Cell centers
    yi = np.arange(ymax, ymin, -CELL_M) - CELL_M/2
    xi_grid, yi_grid = np.meshgrid(xi, yi)
    
    # Prepare point data for interpolation
    points = np.array([[p['x'], p['y']] for p in elevation_points])
    values = np.array([p['elevation'] for p in elevation_points])
    
    print(f"   • Interpolating elevations across {width*height:,} grid cells...")
    print(f"   • Using {len(points)} known elevation points...")
    
    # Use griddata for interpolation (nearest neighbor for robustness)
    try:
        interpolated = griddata(points, values, (xi_grid, yi_grid), method='nearest')
        ELEVATION_GRID = np.nan_to_num(interpolated, nan=0.0)
        
        # Smooth the elevation data slightly
        from scipy.ndimage import gaussian_filter
        ELEVATION_GRID = gaussian_filter(ELEVATION_GRID, sigma=1.0)
        
        print(f"   ✓ Elevation grid created successfully")
        print(f"   • Grid elevation range: {ELEVATION_GRID.min():.1f}m to {ELEVATION_GRID.max():.1f}m")
        
    except Exception as e:
        print(f"   ⚠️ Interpolation failed: {e}, using flat topography")
        ELEVATION_GRID = np.zeros((height, width), dtype=np.float32)
else:
    print(f"   • No elevation data available, creating flat topography")

# -----------------------
# CREATE TERRAIN GRID (ORIGINAL)
# -----------------------
print(f"\n🎨 Generating base terrain layers...")

TERRAIN_GRID = np.zeros((height, width), dtype=np.uint8)

def rasterize_layer(gdf, tile_value, description, all_touched=True):
    """Rasterize a layer with progress tracking."""
    if gdf is None or gdf.empty:
        print(f"   ⏭️  Skipping {description} (no data)")
        return
        
    print(f"   🖌️  {description}: {len(gdf)} features → terrain type {tile_value}")
    
    shapes = [(geom, tile_value) for geom in gdf.geometry if geom and not geom.is_empty]
    
    arr = features.rasterize(
        shapes=shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=all_touched,
        dtype=np.uint8
    )
    
    mask = arr > 0
    TERRAIN_GRID[mask] = arr[mask]
    print(f"      ✓ {np.sum(mask):,} cells affected")

# Create land base layer
print("\n   🏝️  Creating Staten Island land boundary...")
all_geoms = []
for gdf in [buildings, shops, roads, green, water]:
    if gdf is not None and not gdf.empty:
        if len(gdf) > 5000:
            hull = gdf.unary_union.convex_hull
            all_geoms.append(hull)
        else:
            all_geoms.extend(gdf.geometry.tolist())

if all_geoms:
    land_boundary = unary_union(all_geoms)
    if hasattr(land_boundary, 'buffer'):
        land_boundary = land_boundary.buffer(100)
    
    land_shapes = [(land_boundary, 6)]
    land_arr = features.rasterize(
        shapes=land_shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8
    )
    land_mask = land_arr == 6
    TERRAIN_GRID[land_mask] = 6
    print(f"   🏞️  Land base: {np.sum(land_mask):,} cells")

# Process green areas for parks
parks = None
if green is not None:
    park_conditions = (
        green.get("leisure", "").fillna("").str.contains("park|recreation|garden", case=False, na=False) |
        green.get("natural", "").fillna("").str.contains("wood|scrub|grassland|forest", case=False, na=False) |
        green.get("landuse", "").fillna("").str.contains("meadow|grass|forest", case=False, na=False)
    )
    parks = green[park_conditions].copy() if park_conditions.any() else None

# Apply terrain layers in priority order
print(f"\n🎨 Applying terrain layers:")
rasterize_layer(parks, 2, "Parks & Green Spaces")
rasterize_layer(roads, 1, "Roads & Streets")
rasterize_layer(water, 3, "Water Bodies & Coastline")
rasterize_layer(buildings, 4, "Buildings & Structures")

if shops is not None and not shops.empty:
    print(f"   🛍️  Retail Areas: {len(shops)} shops → terrain type 5")
    shop_shapes = [(geom, 5) for geom in shops.geometry if geom and not geom.is_empty]
    shop_arr = features.rasterize(
        shapes=shop_shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8
    )
    retail_mask = shop_arr == 5
    TERRAIN_GRID[retail_mask] = 5
    print(f"      ✓ {np.sum(retail_mask):,} retail cells marked")

# -----------------------
# CREATE TOPOGRAPHIC TILES
# -----------------------
print(f"\n🏔️ Creating topographic visualization...")

# Define elevation zones for visual representation
elevation_ranges = [
    (0, 10, "Sea Level", "#1e3a8a"),      # Deep blue
    (10, 25, "Low Land", "#22c55e"),       # Green  
    (25, 40, "Mid Land", "#eab308"),       # Yellow
    (40, 60, "High Land", "#f97316"),      # Orange
    (60, 100, "Hills", "#dc2626")          # Red
]

print(f"   🎨 Elevation zones defined:")
for min_e, max_e, name, color in elevation_ranges:
    count = np.sum((ELEVATION_GRID >= min_e) & (ELEVATION_GRID < max_e))
    print(f"      {name}: {min_e}-{max_e}m ({count:,} cells) - {color}")

# Enhanced color mapping with topography
def get_topographic_color(terrain_type, elevation):
    """Get color combining terrain and elevation."""
    
    # Base terrain colors
    base_colors = {
        0: (0, 17, 51),      # Ocean
        1: (112, 112, 112),  # Roads  
        2: (34, 139, 34),    # Parks
        3: (70, 130, 180),   # Water
        4: (169, 169, 169),  # Buildings
        5: (255, 140, 0),    # Retail
        6: (210, 180, 140),  # Land
    }
    
    base_color = base_colors.get(terrain_type, (128, 128, 128))
    
    # Don't modify water, roads, or buildings much
    if terrain_type in [1, 3, 4, 5]:
        return base_color
    
    # Apply elevation-based modification to land and parks
    elevation_factor = min(max(elevation / 80.0, 0), 1)  # Normalize to 0-1
    
    if terrain_type == 6:  # Land - vary from tan to brown based on elevation
        r = int(210 - elevation_factor * 80)  # Darker with height
        g = int(180 - elevation_factor * 60)
        b = int(140 - elevation_factor * 40)
        return (max(r, 100), max(g, 80), max(b, 60))
    
    elif terrain_type == 2:  # Parks - vary green intensity
        r = int(34 + elevation_factor * 50)   # Slightly more brown at height
        g = int(139 + elevation_factor * 50)  # Brighter green at height  
        b = int(34 + elevation_factor * 20)
        return (min(r, 100), min(g, 200), min(b, 80))
    
    elif terrain_type == 0:  # Ocean - depth-based blue
        depth_factor = max(0, -elevation / 20.0)  # Deeper = darker
        r = max(int(0 + depth_factor * 30), 0)
        g = max(int(17 + depth_factor * 50), 0) 
        b = max(int(51 + depth_factor * 100), 0)
        return (r, g, b)
    
    return base_color

# -----------------------
# SAVE ENHANCED RESULTS
# -----------------------
print(f"\n💾 Saving topographic results...")

# Count terrain distribution
unique, counts = np.unique(TERRAIN_GRID, return_counts=True)
terrain_counts = dict(zip(unique, counts))
total_cells = width * height

print(f"\n📊 Terrain distribution:")
terrain_names = {
    0: "Empty/Ocean",
    1: "Roads", 
    2: "Parks",
    3: "Water", 
    4: "Buildings",
    5: "Retail",
    6: "Land"
}

for terrain_type in sorted(terrain_counts.keys()):
    count = terrain_counts[terrain_type]
    percentage = (count / total_cells) * 100
    name = terrain_names.get(terrain_type, f"Type {terrain_type}")
    print(f"   • {name}: {count:,} cells ({percentage:.1f}%)")

# Enhanced metadata with topography
metadata = {
    "version": "2.0-topographic",
    "cell_meters": CELL_M,
    "classes": {
        "0": "empty/ocean",
        "1": "road",
        "2": "park", 
        "3": "water",
        "4": "building",
        "5": "retail", 
        "6": "land"
    },
    "colors": {
        "0": "#001133",
        "1": "#707070", 
        "2": "#228B22",
        "3": "#4682B4",
        "4": "#A9A9A9",
        "5": "#FF8C00",
        "6": "#D2B48C"
    },
    "elevation": {
        "available": len(elevation_points) > 0,
        "points_used": len(elevation_points),
        "range_meters": [float(ELEVATION_GRID.min()), float(ELEVATION_GRID.max())] if len(elevation_points) > 0 else [0, 0],
        "zones": [{"min": r[0], "max": r[1], "name": r[2], "color": r[3]} for r in elevation_ranges]
    },
    "transform": {
        "xmin": xmin, 
        "ymax": ymax,
        "cell": CELL_M,
        "crs": CRS_UTM
    },
    "grid_size": [int(height), int(width)],
    "tile_size": TILE_SIZE,
    "real_world_size_km": {
        "width": round((xmax-xmin)/1000, 1),
        "height": round((ymax-ymin)/1000, 1)
    },
    "terrain_counts": {int(k): int(v) for k, v in terrain_counts.items()},
    "total_cells": total_cells
}

# Save enhanced metadata
metadata_file = OUT / "metadata.json"
with open(metadata_file, "w") as f:
    json.dump(metadata, f, indent=2)
print(f"   ✓ Enhanced metadata: {metadata_file}")

# Save terrain grid
np.save(OUT / "terrain_grid.npy", TERRAIN_GRID)
print(f"   ✓ Terrain grid: {OUT / 'terrain_grid.npy'}")

# Save elevation grid  
np.save(OUT / "elevation_grid.npy", ELEVATION_GRID)
print(f"   ✓ Elevation grid: {OUT / 'elevation_grid.npy'}")

# -----------------------
# GENERATE TOPOGRAPHIC PNG TILES
# -----------------------
print(f"\n🖼️  Generating topographic PNG tiles...")

tiles_dir = OUT / "tiles"
tiles_dir.mkdir(exist_ok=True)

def create_topographic_tile(y_start, x_start, tile_y, tile_x):
    """Create a topographic PNG tile combining terrain and elevation."""
    y_end = min(y_start + TILE_SIZE, height)
    x_end = min(x_start + TILE_SIZE, width)
    
    terrain_tile = TERRAIN_GRID[y_start:y_end, x_start:x_end]
    elevation_tile = ELEVATION_GRID[y_start:y_end, x_start:x_end]
    
    tile_height, tile_width = terrain_tile.shape
    rgb_tile = np.zeros((tile_height, tile_width, 3), dtype=np.uint8)
    
    # Apply topographic coloring
    for y in range(tile_height):
        for x in range(tile_width):
            terrain = terrain_tile[y, x]
            elevation = elevation_tile[y, x]
            color = get_topographic_color(terrain, elevation)
            rgb_tile[y, x] = color
    
    # Pad to full tile size if needed
    if tile_height < TILE_SIZE or tile_width < TILE_SIZE:
        padded_tile = np.zeros((TILE_SIZE, TILE_SIZE, 3), dtype=np.uint8)
        padded_tile[:tile_height, :tile_width] = rgb_tile
        rgb_tile = padded_tile
    
    img = Image.fromarray(rgb_tile, mode="RGB")
    tile_filename = f"topo_{tile_y:03d}_{tile_x:03d}.png"
    img.save(tiles_dir / tile_filename)
    
    return tile_filename

# Generate topographic tiles
tile_count = 0
tiles_x = (width + TILE_SIZE - 1) // TILE_SIZE
tiles_y = (height + TILE_SIZE - 1) // TILE_SIZE

print(f"   Creating {tiles_x} × {tiles_y} = {tiles_x * tiles_y} topographic tiles...")

for tile_y in range(tiles_y):
    for tile_x in range(tiles_x):
        y_start = tile_y * TILE_SIZE
        x_start = tile_x * TILE_SIZE
        
        create_topographic_tile(y_start, x_start, tile_y, tile_x)
        tile_count += 1
        
        if tile_count % 100 == 0:
            print(f"      Generated {tile_count} tiles...")

print(f"   ✓ {tile_count} topographic PNG tiles created")

# -----------------------
# COPY ESSENTIAL ASSETS
# -----------------------
print(f"\n📋 Copying essential assets from original...")

# Copy road network if it exists
if (Path("game_tiles/road_network.json")).exists():
    import shutil
    shutil.copy2("game_tiles/road_network.json", OUT / "road_network.json")
    print(f"   ✓ Road network copied")

print(f"\n" + "=" * 70)
print(f"🏔️ TOPOGRAPHIC STATEN ISLAND MAP COMPLETE! 🏔️")
print(f"=" * 70)

print(f"\n📐 Enhanced Map Specifications:")
print(f"   • Grid Size: {width:,} × {height:,} cells")
print(f"   • Real Size: {(xmax-xmin)/1000:.1f}km × {(ymax-ymin)/1000:.1f}km")
print(f"   • Resolution: {CELL_M}m per cell")
print(f"   • Elevation Points: {len(elevation_points)} known elevations")
print(f"   • Elevation Range: {ELEVATION_GRID.min():.1f}m to {ELEVATION_GRID.max():.1f}m")

print(f"\n🏔️ Topographic Features:")
print(f"   • Terrain-aware coloring based on elevation")
print(f"   • 5 elevation zones with distinct visual representation")
print(f"   • Preserved all original terrain types")
print(f"   • Compatible with existing game engine integration")

print(f"\n💾 Enhanced Files Generated:")
print(f"   • {metadata_file} - Enhanced metadata with elevation")
print(f"   • {OUT / 'terrain_grid.npy'} - Terrain classification grid")
print(f"   • {OUT / 'elevation_grid.npy'} - Elevation height grid")
print(f"   • {tiles_dir}/ - {tile_count} topographic PNG tiles")

print(f"\n🚀 Ready for Topographic 2D Game Development!")
print(f"   📂 Output Directory: {OUT.resolve()}")