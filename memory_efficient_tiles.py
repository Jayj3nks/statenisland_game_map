import json, math, os, csv
from pathlib import Path

import geopandas as gpd
import numpy as np
from rasterio import features
from rasterio.transform import from_origin
from shapely.ops import unary_union
from shapely.geometry import mapping, Polygon, box
import networkx as nx
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

print("🎮 STATEN ISLAND MASSIVE 2D MAP GENERATOR")
print("=" * 50)

# -----------------------
# CONFIG
# -----------------------
DATA = Path("staten_island_osm")
OUT  = Path("game_tiles")
OUT.mkdir(exist_ok=True)

CELL_M = 5.0                    # meters per grid cell (massive scale!)
TILE_SIZE = 256                 # cells per tile (256x256)
CRS_UTM = "EPSG:32618"          # UTM zone 18N (meters)

print(f"📐 Configuration:")
print(f"   • Cell size: {CELL_M}m per cell")
print(f"   • Tile size: {TILE_SIZE}x{TILE_SIZE} cells")
print(f"   • CRS: {CRS_UTM}")

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
    
    # Set CRS if missing
    if gdf.crs is None:
        gdf.set_crs("EPSG:4326", inplace=True)
    
    # Convert to UTM for meter-based calculations
    gdf = gdf.to_crs(CRS_UTM)
    
    # Simplify geometries to reduce memory usage
    if len(gdf) > chunk_size:
        print(f"   • Large dataset ({len(gdf)} features), simplifying...")
        gdf['geometry'] = gdf.geometry.simplify(2.0)  # 2m tolerance
    
    return gdf

# Load data files
print("\n📊 Loading Staten Island data...")
buildings = read_geofile(DATA / "buildings.geojson")
shops = read_geofile(DATA / "shops.geojson")
roads = read_geofile(DATA / "roads.geojson")
green = read_geofile(DATA / "landuse_green.geojson")
water = read_geofile(DATA / "water.geojson")

# Report loaded data
print(f"\n✅ Data loaded:")
if buildings is not None: print(f"   • Buildings: {len(buildings):,} features")
if shops is not None: print(f"   • Shops: {len(shops):,} features") 
if roads is not None: print(f"   • Roads: {len(roads):,} features")
if green is not None: print(f"   • Green areas: {len(green):,} features")
if water is not None: print(f"   • Water bodies: {len(water):,} features")

# -----------------------
# CALCULATE BOUNDS
# -----------------------
print("\n🌍 Calculating world bounds...")

# Collect all geometries to determine bounds
all_bounds = []
if buildings is not None: all_bounds.append(buildings.total_bounds)
if shops is not None: all_bounds.append(shops.total_bounds)  
if roads is not None: all_bounds.append(roads.total_bounds)
if green is not None: all_bounds.append(green.total_bounds)
if water is not None: all_bounds.append(water.total_bounds)

if not all_bounds:
    raise ValueError("No data found!")

# Calculate overall bounds
bounds = np.array(all_bounds)
xmin = bounds[:, 0].min()
ymin = bounds[:, 1].min()
xmax = bounds[:, 2].max()
ymax = bounds[:, 3].max()

print(f"Raw bounds: X: {xmin:.0f} to {xmax:.0f} meters ({(xmax-xmin)/1000:.1f} km)")
print(f"            Y: {ymin:.0f} to {ymax:.0f} meters ({(ymax-ymin)/1000:.1f} km)")

# Snap bounds to cell grid
def snap_down(v, q): return math.floor(v / q) * q
def snap_up(v, q): return math.ceil(v / q) * q

xmin = snap_down(xmin, CELL_M)
ymin = snap_down(ymin, CELL_M)
xmax = snap_up(xmax, CELL_M)
ymax = snap_up(ymax, CELL_M)

width = int(round((xmax - xmin) / CELL_M))
height = int(round((ymax - ymin) / CELL_M))

transform = from_origin(xmin, ymax, CELL_M, CELL_M)

print(f"\n📏 Final grid:")
print(f"   • Grid size: {width:,} × {height:,} cells")
print(f"   • Real size: {width*CELL_M/1000:.1f}km × {height*CELL_M/1000:.1f}km")
print(f"   • Total cells: {width*height:,}")
print(f"   • Memory needed: ~{(width*height*1)//1024//1024:.0f} MB")

# -----------------------
# RASTERIZE IN CHUNKS
# -----------------------
print(f"\n🎨 Generating tile data...")

# Initialize grid
GRID = np.zeros((height, width), dtype=np.uint8)

def rasterize_layer(gdf, tile_value, description, all_touched=True):
    """Rasterize a layer with progress tracking."""
    if gdf is None or gdf.empty:
        print(f"   ⏭️  Skipping {description} (no data)")
        return
        
    print(f"   🖌️  {description}: {len(gdf)} features → tile type {tile_value}")
    
    # Create shapes iterator
    shapes = [(geom, tile_value) for geom in gdf.geometry if geom and not geom.is_empty]
    
    # Rasterize
    arr = features.rasterize(
        shapes=shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=all_touched,
        dtype=np.uint8
    )
    
    # Apply to main grid (higher values overwrite lower ones)
    mask = arr > 0
    GRID[mask] = arr[mask]
    
    affected_cells = np.sum(mask)
    print(f"      ✓ {affected_cells:,} cells affected")

# Process landuse for parks/green
parks = None
if green is not None:
    print("   🌳 Processing green areas...")
    # Filter for parks, woods, and natural areas
    park_conditions = (
        green.get("leisure", "").fillna("").str.contains("park|recreation|garden", case=False, na=False) |
        green.get("natural", "").fillna("").str.contains("wood|scrub|grassland|forest", case=False, na=False) |
        green.get("landuse", "").fillna("").str.contains("meadow|grass|forest", case=False, na=False)
    )
    parks = green[park_conditions].copy() if park_conditions.any() else None

# Create land base layer first (everything starts as land)
print("\n   🏝️  Creating Staten Island land boundary...")
all_geoms = []
for gdf in [buildings, shops, roads, green, water]:
    if gdf is not None and not gdf.empty:
        # Use convex hull for efficiency on large datasets
        if len(gdf) > 5000:
            hull = gdf.unary_union.convex_hull
            all_geoms.append(hull)
        else:
            all_geoms.extend(gdf.geometry.tolist())

if all_geoms:
    # Create land boundary
    land_boundary = unary_union(all_geoms)
    if hasattr(land_boundary, 'buffer'):
        land_boundary = land_boundary.buffer(100)  # 100m buffer for safety
    
    # Rasterize land (tile type 6 = tan/beige land)
    print("   🏞️  Land areas: Base layer → tile type 6")
    land_shapes = [(land_boundary, 6)]
    land_arr = features.rasterize(
        shapes=land_shapes,
        out_shape=(height, width),
        transform=transform,
        fill=0,
        all_touched=True,
        dtype=np.uint8
    )
    
    # Apply land as base
    land_mask = land_arr == 6
    GRID[land_mask] = 6
    print(f"      ✓ {np.sum(land_mask):,} cells of land created")

# Rasterize layers in order (lower priority first, higher priority overwrites)
print(f"\n🎨 Applying terrain layers (priority order):")

# 1. Parks/Green areas (tile type 2)
rasterize_layer(parks, 2, "Parks & Green Spaces")

# 2. Roads (tile type 1) 
rasterize_layer(roads, 1, "Roads & Streets")

# 3. Water bodies (tile type 3)
rasterize_layer(water, 3, "Water Bodies & Coastline")

# 4. Buildings (tile type 4)
rasterize_layer(buildings, 4, "Buildings & Structures")

# 5. Retail/Commercial (tile type 5) - overlay on buildings where shops exist
if shops is not None and not shops.empty:
    print(f"   🛍️  Retail Areas: {len(shops)} shops → tile type 5")
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
    GRID[retail_mask] = 5
    print(f"      ✓ {np.sum(retail_mask):,} retail cells marked")

# -----------------------
# SAVE RESULTS
# -----------------------
print(f"\n💾 Saving results...")

# Count tile distribution
unique, counts = np.unique(GRID, return_counts=True)
tile_counts = dict(zip(unique, counts))
total_cells = width * height

print(f"\n📊 Tile distribution:")
tile_names = {
    0: "Empty/Ocean",
    1: "Roads (Gray)",
    2: "Parks (Green)", 
    3: "Water (Blue)",
    4: "Buildings (Gray)",
    5: "Retail (Orange)",
    6: "Land (Tan/Beige)"
}

for tile_type in sorted(tile_counts.keys()):
    count = tile_counts[tile_type] 
    percentage = (count / total_cells) * 100
    name = tile_names.get(tile_type, f"Type {tile_type}")
    print(f"   • {name}: {count:,} cells ({percentage:.1f}%)")

# Save master grid as NPY
grid_file = OUT / "grid_uint8.npy"
np.save(grid_file, GRID)
print(f"   ✓ Master grid: {grid_file}")

# Create metadata
metadata = {
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
        "0": "#001133",  # Dark blue ocean
        "1": "#707070",  # Gray roads
        "2": "#228B22",  # Forest green parks
        "3": "#4682B4",  # Steel blue water
        "4": "#A9A9A9",  # Dark gray buildings
        "5": "#FF8C00",  # Dark orange retail
        "6": "#D2B48C"   # Tan land
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
    "tile_counts": {int(k): int(v) for k, v in tile_counts.items()},
    "total_cells": total_cells
}

# Save metadata as JSON
metadata_file = OUT / "metadata.json"
with open(metadata_file, "w") as f:
    json.dump(metadata, f, indent=2)
print(f"   ✓ Metadata: {metadata_file}")

# -----------------------
# EXPORT AS CSV
# -----------------------
print(f"\n📄 Exporting CSV tilemap...")
csv_file = OUT / "tilemap.csv"

with open(csv_file, "w", newline='') as f:
    writer = csv.writer(f)
    # Write header information
    writer.writerow([f"# MASSIVE STATEN ISLAND 2D GAME TILEMAP"])
    writer.writerow([f"# Generated for low-poly 2D game development"])
    writer.writerow([f"# Grid Size: {width}x{height} cells"])  
    writer.writerow([f"# Cell Size: {CELL_M}m per cell"])
    writer.writerow([f"# Real World Size: {(xmax-xmin)/1000:.1f}km x {(ymax-ymin)/1000:.1f}km"])
    writer.writerow([f"# Staten Island, New York, USA"])
    writer.writerow([f"# Tile Types:"])
    for k, v in metadata["classes"].items():
        color = metadata["colors"][k]
        writer.writerow([f"#   {k}={v} (color: {color})"])
    writer.writerow([])  # Empty separator
    
    # Write grid data
    for row in GRID:
        writer.writerow(row)

print(f"   ✓ CSV tilemap: {csv_file}")

# -----------------------
# GENERATE PNG TILES  
# -----------------------
print(f"\n🖼️  Generating PNG tiles ({TILE_SIZE}x{TILE_SIZE} each)...")

tiles_dir = OUT / "tiles"
tiles_dir.mkdir(exist_ok=True)

# Color mapping for PNG visualization
color_map = {
    0: (0, 17, 51),      # Dark blue ocean
    1: (112, 112, 112),  # Gray roads
    2: (34, 139, 34),    # Forest green parks
    3: (70, 130, 180),   # Steel blue water
    4: (169, 169, 169),  # Dark gray buildings
    5: (255, 140, 0),    # Dark orange retail
    6: (210, 180, 140),  # Tan land
}

def create_tile_png(y_start, x_start, tile_y, tile_x):
    """Create a colored PNG tile from grid data."""
    y_end = min(y_start + TILE_SIZE, height)
    x_end = min(x_start + TILE_SIZE, width)
    
    # Extract tile data
    tile_data = GRID[y_start:y_end, x_start:x_end]
    
    # Create RGB image
    tile_height, tile_width = tile_data.shape
    rgb_tile = np.zeros((tile_height, tile_width, 3), dtype=np.uint8)
    
    # Apply color mapping
    for tile_type, color in color_map.items():
        mask = tile_data == tile_type
        rgb_tile[mask] = color
    
    # Pad to full tile size if needed
    if tile_height < TILE_SIZE or tile_width < TILE_SIZE:
        padded_tile = np.zeros((TILE_SIZE, TILE_SIZE, 3), dtype=np.uint8)
        padded_tile[:tile_height, :tile_width] = rgb_tile
        rgb_tile = padded_tile
    
    # Save as PNG
    img = Image.fromarray(rgb_tile, mode="RGB")
    tile_filename = f"tile_{tile_y:03d}_{tile_x:03d}.png"
    img.save(tiles_dir / tile_filename)
    
    return tile_filename

# Generate tiles
tile_count = 0
tiles_x = (width + TILE_SIZE - 1) // TILE_SIZE
tiles_y = (height + TILE_SIZE - 1) // TILE_SIZE

print(f"   Creating {tiles_x} × {tiles_y} = {tiles_x * tiles_y} tiles...")

for tile_y in range(tiles_y):
    for tile_x in range(tiles_x):
        y_start = tile_y * TILE_SIZE
        x_start = tile_x * TILE_SIZE
        
        filename = create_tile_png(y_start, x_start, tile_y, tile_x)
        tile_count += 1
        
        if tile_count % 100 == 0:
            print(f"      Generated {tile_count} tiles...")

print(f"   ✓ {tile_count} PNG tiles created in {tiles_dir}")

# -----------------------
# CREATE ROAD NETWORK FOR AI
# -----------------------
if roads is not None and not roads.empty:
    print(f"\n🛣️  Building road network for AI navigation...")
    
    G = nx.Graph()
    
    # Sample roads for AI pathfinding (every ~25 meters)
    SAMPLE_DISTANCE = 25.0
    
    for idx, row in roads.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
            
        # Extract coordinates based on geometry type
        coords = []
        if geom.geom_type == "LineString":
            coords = list(geom.coords)
        elif geom.geom_type == "MultiLineString":
            for line in geom.geoms:
                coords.extend(list(line.coords))
        else:
            continue
            
        if len(coords) < 2:
            continue
            
        # Sample points along the road
        last_point = None
        accumulated_distance = 0.0
        
        for i in range(1, len(coords)):
            x1, y1 = coords[i-1]
            x2, y2 = coords[i]
            
            segment_length = math.hypot(x2 - x1, y2 - y1)
            
            if last_point is None:
                last_point = (x1, y1)
                G.add_node(last_point)
                
            accumulated_distance += segment_length
            
            if accumulated_distance >= SAMPLE_DISTANCE or i == len(coords) - 1:
                current_point = (x2, y2)
                G.add_node(current_point)
                
                # Calculate actual distance between points
                distance = math.hypot(current_point[0] - last_point[0], 
                                    current_point[1] - last_point[1])
                G.add_edge(last_point, current_point, length=distance)
                
                last_point = current_point
                accumulated_distance = 0.0
    
    # Export road network
    nodes_list = list(G.nodes())
    road_network = {
        "crs": CRS_UTM,
        "sample_distance_meters": SAMPLE_DISTANCE,
        "nodes": [{"id": i, "x": float(node[0]), "y": float(node[1])} 
                 for i, node in enumerate(nodes_list)],
        "edges": [{"from": nodes_list.index(u), "to": nodes_list.index(v), "length": float(data["length"])} 
                 for u, v, data in G.edges(data=True)]
    }
    
    road_file = OUT / "road_network.json"
    with open(road_file, "w") as f:
        json.dump(road_network, f, indent=2)
    
    print(f"   ✓ Road network: {len(G.nodes())} nodes, {len(G.edges())} edges")
    print(f"   ✓ Saved to: {road_file}")

# -----------------------
# FINAL SUMMARY
# -----------------------
print(f"\n" + "=" * 60)
print(f"🎮 MASSIVE 2D STATEN ISLAND MAP COMPLETE! 🎮")
print(f"=" * 60)
print(f"📐 Map Specifications:")
print(f"   • Grid Size: {width:,} × {height:,} cells")
print(f"   • Real Size: {(xmax-xmin)/1000:.1f}km × {(ymax-ymin)/1000:.1f}km")
print(f"   • Resolution: {CELL_M}m per cell (massive scale!)")
print(f"   • Total Area: {((xmax-xmin)/1000) * ((ymax-ymin)/1000):.1f} km²")

print(f"\n🎨 Terrain Types:")
print(f"   • 7 different tile types with distinct colors")
print(f"   • Roads: Gray ({tile_counts.get(1, 0):,} cells)")
print(f"   • Parks: Green ({tile_counts.get(2, 0):,} cells)")  
print(f"   • Water: Blue ({tile_counts.get(3, 0):,} cells)")
print(f"   • Buildings: Gray ({tile_counts.get(4, 0):,} cells)")
print(f"   • Retail: Orange ({tile_counts.get(5, 0):,} cells)")
print(f"   • Land: Tan/Beige ({tile_counts.get(6, 0):,} cells)")

print(f"\n💾 Generated Files:")
print(f"   • {grid_file} - Master grid (NumPy array)")
print(f"   • {metadata_file} - JSON metadata")
print(f"   • {csv_file} - CSV tilemap for debugging")
print(f"   • {tiles_dir}/ - {tile_count} PNG tiles ({TILE_SIZE}x{TILE_SIZE})")
if roads is not None:
    print(f"   • {road_file} - Road network for AI")

print(f"\n🚀 Ready for 2D Game Development!")
print(f"   • Perfect for Unity, Godot, or custom engines")
print(f"   • Supports procedural asset placement")
print(f"   • AI-ready road network included")
print(f"   • Low-poly aesthetic with realistic proportions")

print(f"\n📂 Output Directory: {OUT.resolve()}")