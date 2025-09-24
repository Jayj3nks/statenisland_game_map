import json, math, os, csv
from pathlib import Path
import geopandas as gpd
import numpy as np
from shapely.ops import unary_union
from shapely.geometry import Point, Polygon
from PIL import Image, ImageDraw
import warnings
import pandas as pd
warnings.filterwarnings('ignore')

print("🏔️ STATEN ISLAND TOPOGRAPHIC 2D MAP GENERATOR")
print("=" * 60)

# -----------------------
# CONFIG  
# -----------------------
DATA = Path("staten_island_osm")
OUT = Path("game_tiles_topographic")
OUT.mkdir(exist_ok=True)

CELL_M = 5.0
TILE_SIZE = 256
CRS_UTM = "EPSG:32618"

print(f"🗺️ Configuration:")
print(f"   • Cell size: {CELL_M}m per cell")
print(f"   • Tile size: {TILE_SIZE}x{TILE_SIZE} cells")
print(f"   • Enhanced: Topography + Original Terrain")

# -----------------------
# LOAD EXISTING RESULTS
# -----------------------
print(f"\n📂 Loading existing map data...")

# Load existing grid and metadata
if not Path("game_tiles/metadata.json").exists():
    print("❌ Error: Original map data not found. Please run memory_efficient_tiles.py first.")
    exit(1)

# Load metadata from original
with open("game_tiles/metadata.json", "r") as f:
    original_metadata = json.load(f)

# Load compressed grid if needed
grid_file = Path("game_tiles/grid_uint8.npy")
if not grid_file.exists():
    # Try decompressing
    import gzip
    try:
        with gzip.open("game_tiles_compressed/grid_uint8.npy.gz", "rb") as f_in:
            with open("game_tiles/grid_uint8.npy", "wb") as f_out:
                f_out.write(f_in.read())
        print("✓ Decompressed grid from archive")
    except Exception as e:
        print(f"❌ Error loading grid: {e}")
        exit(1)

TERRAIN_GRID = np.load("game_tiles/grid_uint8.npy")
height, width = TERRAIN_GRID.shape

# Get bounds from metadata
transform = original_metadata["transform"]
xmin = transform["xmin"]
ymax = transform["ymax"]
xmax = xmin + (width * CELL_M)
ymin = ymax - (height * CELL_M)

print(f"✓ Loaded existing terrain grid: {width} × {height}")
print(f"✓ Real size: {(xmax-xmin)/1000:.1f}km × {(ymax-ymin)/1000:.1f}km")

# -----------------------
# LOAD ELEVATION DATA
# -----------------------
print(f"\n🏔️ Loading elevation data...")

elevation_points = []

# Load green areas with elevation data
if (DATA / "landuse_green.geojson").exists():
    green_gdf = gpd.read_file(DATA / "landuse_green.geojson")
    green_gdf = green_gdf.to_crs(CRS_UTM)
    
    if 'ele' in green_gdf.columns:
        green_ele = green_gdf[green_gdf['ele'].notna()].copy()
        
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
        
        print(f"   🌳 Found {len([p for p in elevation_points if p['source'] == 'landuse'])} elevation points from landuse")

# Load water areas with elevation data  
if (DATA / "water.geojson").exists():
    water_gdf = gpd.read_file(DATA / "water.geojson")
    water_gdf = water_gdf.to_crs(CRS_UTM)
    
    if 'ele' in water_gdf.columns:
        water_ele = water_gdf[water_gdf['ele'].notna()].copy()
        
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
        
        print(f"   💧 Found {len([p for p in elevation_points if p['source'] == 'water'])} elevation points from water")

if elevation_points:
    elevations = [p['elevation'] for p in elevation_points]
    print(f"\n📊 Elevation Statistics:")
    print(f"   • Total elevation points: {len(elevation_points)}")
    print(f"   • Range: {min(elevations):.1f}m to {max(elevations):.1f}m")
    print(f"   • Mean: {np.mean(elevations):.1f}m")
else:
    print(f"   ⚠️ No elevation data found")

# -----------------------
# CREATE ELEVATION GRID
# -----------------------
print(f"\n🏔️ Creating elevation interpolation...")

ELEVATION_GRID = np.zeros((height, width), dtype=np.float32)

if elevation_points:
    print(f"   • Interpolating across {width*height:,} cells using {len(elevation_points)} points...")
    
    # Simple distance-weighted interpolation
    for i in range(height):
        for j in range(width):
            # Calculate world coordinates of cell center
            world_x = xmin + (j + 0.5) * CELL_M
            world_y = ymax - (i + 0.5) * CELL_M
            
            # Find nearest elevation points and interpolate
            distances = []
            values = []
            
            for point in elevation_points:
                dist = math.sqrt((world_x - point['x'])**2 + (world_y - point['y'])**2)
                distances.append(dist)
                values.append(point['elevation'])
            
            # Use inverse distance weighting for nearest 3 points
            if distances:
                # Find indices of 3 nearest points
                nearest_indices = np.argsort(distances)[:min(3, len(distances))]
                
                total_weight = 0
                weighted_elevation = 0
                
                for idx in nearest_indices:
                    dist = distances[idx]
                    if dist < 1.0:  # Very close point
                        ELEVATION_GRID[i, j] = values[idx]
                        break
                    else:
                        weight = 1.0 / (dist + 1.0)  # Add 1 to avoid division by zero
                        weighted_elevation += values[idx] * weight
                        total_weight += weight
                
                if total_weight > 0:
                    ELEVATION_GRID[i, j] = weighted_elevation / total_weight
        
        # Progress indicator
        if i % (height // 10) == 0:
            progress = (i / height) * 100
            print(f"      Progress: {progress:.0f}%")
    
    print(f"   ✓ Elevation interpolation complete")
    print(f"   • Grid elevation range: {ELEVATION_GRID.min():.1f}m to {ELEVATION_GRID.max():.1f}m")

# -----------------------
# ENHANCED COLORING
# -----------------------
print(f"\n🎨 Creating topographic color scheme...")

def get_topographic_color(terrain_type, elevation):
    """Get color combining terrain and elevation."""
    
    # Base terrain colors (from original)
    base_colors = {
        0: (0, 17, 51),      # Dark blue ocean
        1: (112, 112, 112),  # Gray roads  
        2: (34, 139, 34),    # Forest green parks
        3: (70, 130, 180),   # Steel blue water
        4: (169, 169, 169),  # Dark gray buildings
        5: (255, 140, 0),    # Orange retail
        6: (210, 180, 140),  # Tan land
    }
    
    base_color = list(base_colors.get(terrain_type, (128, 128, 128)))
    
    # Don't modify certain terrain types much
    if terrain_type in [1, 4, 5]:  # Roads, buildings, retail
        return tuple(base_color)
    
    # Apply elevation-based modification
    if len(elevation_points) > 0:
        # Normalize elevation (0-1 range)
        max_elevation = max([p['elevation'] for p in elevation_points])
        elevation_factor = min(max(elevation / max_elevation, 0), 1) if max_elevation > 0 else 0
        
        if terrain_type == 6:  # Land - vary from tan to brown/red with elevation
            # Higher elevation = more brown/red
            base_color[0] = min(255, int(210 + elevation_factor * 45))  # More red
            base_color[1] = max(100, int(180 - elevation_factor * 80))  # Less green  
            base_color[2] = max(60, int(140 - elevation_factor * 80))   # Less blue
            
        elif terrain_type == 2:  # Parks - vary green with elevation
            # Higher elevation = different green shade
            base_color[0] = min(100, int(34 + elevation_factor * 66))   # Slightly more red
            base_color[1] = min(255, int(139 + elevation_factor * 116)) # Brighter green
            base_color[2] = min(80, int(34 + elevation_factor * 46))    # More blue
            
        elif terrain_type == 0:  # Ocean - depth variation
            # Lower "elevation" (depth) = darker blue  
            depth_factor = max(0, -elevation / 20.0) if elevation < 0 else 0
            base_color[0] = max(0, int(0 + depth_factor * 30))
            base_color[1] = max(0, int(17 + depth_factor * 50))
            base_color[2] = max(0, int(51 + depth_factor * 100))
    
    return tuple(base_color)

# -----------------------
# GENERATE TOPOGRAPHIC TILES
# -----------------------
print(f"\n🖼️ Generating topographic PNG tiles...")

tiles_dir = OUT / "tiles"
tiles_dir.mkdir(exist_ok=True)

def create_topographic_tile(y_start, x_start, tile_y, tile_x):
    """Create a topographic PNG tile."""
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
    
    # Save as PNG
    img = Image.fromarray(rgb_tile, mode="RGB")
    tile_filename = f"topo_{tile_y:03d}_{tile_x:03d}.png"
    img.save(tiles_dir / tile_filename)
    
    return tile_filename

# Generate tiles
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
        
        if tile_count % 50 == 0:
            print(f"      Generated {tile_count} tiles...")

print(f"   ✓ {tile_count} topographic PNG tiles created")

# -----------------------
# SAVE ENHANCED METADATA
# -----------------------
print(f"\n💾 Saving enhanced metadata...")

# Create elevation zones for reference
elevation_zones = [
    {"min": 0, "max": 10, "name": "Sea Level", "color": "#1e3a8a"},
    {"min": 10, "max": 25, "name": "Low Land", "color": "#22c55e"},
    {"min": 25, "max": 40, "name": "Mid Land", "color": "#eab308"},
    {"min": 40, "max": 60, "name": "High Land", "color": "#f97316"},
    {"min": 60, "max": 100, "name": "Hills", "color": "#dc2626"}
]

# Enhanced metadata
enhanced_metadata = original_metadata.copy()
enhanced_metadata.update({
    "version": "2.0-topographic",
    "elevation": {
        "available": len(elevation_points) > 0,
        "points_used": len(elevation_points),
        "range_meters": [float(ELEVATION_GRID.min()), float(ELEVATION_GRID.max())] if len(elevation_points) > 0 else [0, 0],
        "zones": elevation_zones,
        "interpolation_method": "inverse_distance_weighting"
    },
    "topographic_features": {
        "elevation_based_coloring": True,
        "terrain_elevation_blend": True,
        "compatible_with_original": True
    }
})

# Save enhanced metadata
metadata_file = OUT / "metadata.json"
with open(metadata_file, "w") as f:
    json.dump(enhanced_metadata, f, indent=2)
print(f"   ✓ Enhanced metadata: {metadata_file}")

# Save grids
np.save(OUT / "terrain_grid.npy", TERRAIN_GRID)
np.save(OUT / "elevation_grid.npy", ELEVATION_GRID)
print(f"   ✓ Terrain grid: {OUT / 'terrain_grid.npy'}")
print(f"   ✓ Elevation grid: {OUT / 'elevation_grid.npy'}")

# Copy other essential files
import shutil
essential_files = ["road_network.json"]
for file in essential_files:
    src = Path("game_tiles") / file
    if src.exists():
        shutil.copy2(src, OUT / file)
        print(f"   ✓ Copied: {file}")

# -----------------------
# CREATE COMPARISON VIEWER
# -----------------------
print(f"\n🔍 Creating comparison viewer...")

viewer_html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Staten Island: Original vs Topographic</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 20px;
            background: #000;
            color: #00ff00;
        }}
        .container {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}
        .map-section {{
            flex: 1;
            min-width: 400px;
            border: 2px solid #00ffff;
            padding: 15px;
            border-radius: 10px;
        }}
        h1, h2 {{ 
            color: #00ffff;
            text-align: center;
        }}
        .stats {{
            background: rgba(0, 255, 0, 0.1);
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .sample-tiles {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 5px;
            margin: 10px 0;
        }}
        .tile-img {{
            width: 100%;
            image-rendering: pixelated;
            border: 1px solid #666;
        }}
        .legend {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 5px;
            font-size: 12px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .color-box {{
            width: 15px;
            height: 15px;
            border: 1px solid #fff;
        }}
    </style>
</head>
<body>
    <h1>🏔️ Staten Island 2D Map: Topographic Enhancement</h1>
    
    <div class="container">
        <div class="map-section">
            <h2>🗺️ Original Map</h2>
            <div class="stats">
                <strong>Features:</strong><br>
                • Standard terrain types<br>
                • Flat coloring scheme<br>
                • 7 terrain categories<br>
                • Game-ready format
            </div>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="color-box" style="background: #001133;"></div>
                    <span>Ocean</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #707070;"></div>
                    <span>Roads</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #228B22;"></div>
                    <span>Parks</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #4682B4;"></div>
                    <span>Water</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #A9A9A9;"></div>
                    <span>Buildings</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #FF8C00;"></div>
                    <span>Retail</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #D2B48C;"></div>
                    <span>Land</span>
                </div>
            </div>
        </div>
        
        <div class="map-section">
            <h2>🏔️ Topographic Map</h2>
            <div class="stats">
                <strong>Enhanced Features:</strong><br>
                • Elevation-based coloring<br>
                • {len(elevation_points)} elevation points<br>
                • Height range: {ELEVATION_GRID.min():.1f}m - {ELEVATION_GRID.max():.1f}m<br>
                • Terrain + topography blend
            </div>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="color-box" style="background: #1e3a8a;"></div>
                    <span>Sea Level (0-10m)</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #22c55e;"></div>
                    <span>Low Land (10-25m)</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #eab308;"></div>
                    <span>Mid Land (25-40m)</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #f97316;"></div>
                    <span>High Land (40-60m)</span>
                </div>
                <div class="legend-item">
                    <div class="color-box" style="background: #dc2626;"></div>
                    <span>Hills (60m+)</span>
                </div>
            </div>
        </div>
    </div>
    
    <div style="text-align: center; margin-top: 30px;">
        <h2>📊 Technical Details</h2>
        <div class="stats">
            <strong>Grid:</strong> {width:,} × {height:,} cells ({width*height:,} total)<br>
            <strong>Resolution:</strong> {CELL_M}m per cell<br>
            <strong>Real Size:</strong> {(xmax-xmin)/1000:.1f}km × {(ymax-ymin)/1000:.1f}km<br>
            <strong>Tiles Generated:</strong> {tile_count} topographic PNG tiles<br>
            <strong>Elevation Data:</strong> {"Available" if len(elevation_points) > 0 else "Simulated"}<br>
            <strong>Compatibility:</strong> Fully backward compatible with original
        </div>
    </div>
</body>
</html>'''

with open(OUT / "topographic_viewer.html", "w") as f:
    f.write(viewer_html)

print(f"   ✓ Comparison viewer: {OUT / 'topographic_viewer.html'}")

# -----------------------
# FINAL SUMMARY
# -----------------------
print(f"\n" + "=" * 70)
print(f"🏔️ TOPOGRAPHIC STATEN ISLAND MAP COMPLETE! 🏔️")
print(f"=" * 70)

print(f"\n📐 Enhanced Specifications:")
print(f"   • Grid Size: {width:,} × {height:,} cells")  
print(f"   • Real Size: {(xmax-xmin)/1000:.1f}km × {(ymax-ymin)/1000:.1f}km")
print(f"   • Resolution: {CELL_M}m per cell")
print(f"   • Elevation Points: {len(elevation_points)}")
if len(elevation_points) > 0:
    print(f"   • Elevation Range: {ELEVATION_GRID.min():.1f}m to {ELEVATION_GRID.max():.1f}m")

print(f"\n🏔️ Topographic Features Added:")
print(f"   ✅ Elevation-based terrain coloring")
print(f"   ✅ Height-aware land and park visualization") 
print(f"   ✅ 5 elevation zones for gameplay")
print(f"   ✅ Preserved all original terrain data")
print(f"   ✅ Full backward compatibility")

print(f"\n💾 New Files Generated:")
print(f"   • {metadata_file} - Enhanced metadata with elevation")
print(f"   • {OUT / 'terrain_grid.npy'} - Original terrain grid")
print(f"   • {OUT / 'elevation_grid.npy'} - Elevation height grid")
print(f"   • {tiles_dir}/ - {tile_count} topographic PNG tiles")
print(f"   • {OUT / 'topographic_viewer.html'} - Comparison viewer")

print(f"\n🎮 Game Development Benefits:")
print(f"   • Height-based gameplay mechanics")
print(f"   • Realistic terrain visualization") 
print(f"   • Line-of-sight calculations possible")
print(f"   • Strategic elevation advantages")
print(f"   • Enhanced visual depth and realism")

print(f"\n🚀 Ready for Enhanced 2D Game Development!")
print(f"📂 Output Directory: {OUT.resolve()}")