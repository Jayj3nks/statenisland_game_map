# 🎮 MASSIVE 2D STATEN ISLAND MAP

> **Real-world Staten Island as a massive 2D game map with 39+ million cells**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Game Ready](https://img.shields.io/badge/Game%20Ready-Unity%20|%20Godot%20|%20Custom-green.svg)](README.md)

## 🚀 Quick Start

**Important**: This repository uses compressed files to stay within GitHub's limits. Run this first:

```bash
python3 decompress_files.py
```

This will extract the compressed map data (~670MB total) for use in your game engine.

## 📐 Map Specifications

- **📏 Grid Size**: 5,783 × 6,757 cells (39,075,731 total)
- **🌍 Real Size**: 28.9km × 33.8km (authentic Staten Island dimensions)
- **🔍 Resolution**: 5 meters per cell (massive scale for exploration)
- **🎨 Tiles**: 621 PNG tiles (256×256 cells each = 1.28km × 1.28km)
- **📊 Total Area**: 976.9 km² of real-world geography

## 🎨 Terrain Types & Colors

| Terrain | Color | Hex | Coverage | Use Case |
|---------|-------|-----|----------|----------|
| 🌊 Ocean/Empty | Dark Blue | `#001133` | 45.3% | Ocean boundaries, empty space |
| 💧 Water Bodies | Steel Blue | `#4682B4` | 35.7% | Rivers, bays, coastline |
| 🏞️ Land Areas | Tan/Beige | `#D2B48C` | 9.9% | General terrain for buildings |
| 🌳 Parks/Green | Forest Green | `#228B22` | 4.7% | Parks, forests, recreational areas |
| 🏢 Buildings | Dark Gray | `#A9A9A9` | 3.5% | Residential, commercial structures |
| 🛣️ Roads | Gray | `#707070` | 1.0% | Streets, highways, pathways |
| 🛍️ Retail | Orange | `#FF8C00` | <0.1% | Shopping centers, commercial zones |

## 📂 Repository Structure

```
📦 staten-island-map/
├── 🗜️ game_tiles_compressed/           # Compressed large files
│   ├── buildings.geojson.gz            # (12.7MB → 557MB when extracted)
│   ├── tilemap.csv.gz                  # (1.0MB → 75MB when extracted)
│   └── grid_uint8.npy.gz              # (0.8MB → 38MB when extracted)
├── 🎮 game_tiles/                      # Ready-to-use game assets
│   ├── metadata.json                   # Map configuration & bounds
│   ├── road_network.json              # AI navigation graph (3MB)
│   ├── map_viewer.html                 # Interactive map preview
│   └── tiles/                          # 621 PNG tiles (256×256 each)
├── 🗺️ staten_island_osm/              # OpenStreetMap source data
│   ├── building_centroids.geojson     # Building center points (26MB)
│   ├── landuse_green.geojson          # Parks & green spaces (24MB)
│   ├── roads.geojson                   # Road network (8.3MB)
│   ├── shops.geojson                   # Commercial locations (6.8MB)
│   ├── water.geojson                   # Water bodies (2.3MB)
│   └── shop_centroids.geojson         # Shop center points (393KB)
├── 🐍 Python Scripts
│   ├── decompress_files.py            # ⚡ EXTRACT COMPRESSED FILES FIRST
│   ├── memory_efficient_tiles.py      # Map generation script
│   └── Staten_island.py               # Data download script
└── 📖 README.md                        # This file
```

## ⚡ Getting Started

### 1. Clone & Extract
```bash
git clone https://github.com/Jayj3nks/staten-island-map.git
cd staten-island-map

# IMPORTANT: Extract compressed files first!
python3 decompress_files.py
```

### 2. Install Dependencies (for regeneration)
```bash
pip install geopandas rasterio pillow networkx shapely
```

### 3. View the Map
```bash
# Open map_viewer.html in your browser
open game_tiles/map_viewer.html
```

## 🎮 Game Engine Integration

### 🔷 Unity
```csharp
// Load map metadata
string json = File.ReadAllText("game_tiles/metadata.json");
MapConfig config = JsonUtility.FromJson<MapConfig>(json);

// Stream tiles based on player position
Vector2 playerPos = player.transform.position;
int tileX = Mathf.FloorToInt(playerPos.x / (256 * 5f)); // 5m per cell
int tileY = Mathf.FloorToInt(playerPos.y / (256 * 5f));

// Load tile texture
string tilePath = $"game_tiles/tiles/tile_{tileY:D3}_{tileX:D3}.png";
```

### 🟢 Godot
```gdscript
# Load decompressed tilemap
var file = File.new()
file.open("game_tiles/tilemap.csv", File.READ)
var map_data = file.get_as_text()

# Parse CSV grid (skip header comments)
for line in map_data.split("\n"):
    if not line.begins_with("#"):
        var row_data = line.split(",")
        # Each cell value represents terrain type (0-6)
```

### 🔧 Custom Engine
```python
import numpy as np
import json

# Load the master grid (after decompression!)
grid = np.load("game_tiles/grid_uint8.npy")  # Shape: (6757, 5783)

# Load configuration
with open("game_tiles/metadata.json") as f:
    config = json.load(f)

# Convert world coordinates to grid indices
def world_to_grid(world_x, world_y):
    cell_x = int((world_x - config["transform"]["xmin"]) / 5.0)
    cell_y = int((config["transform"]["ymax"] - world_y) / 5.0)
    return cell_x, cell_y

# Get terrain at position
terrain_type = grid[grid_y, grid_x]  # Returns 0-6
```

## 🤖 AI Navigation

```python
# Load road network for pathfinding
import json
with open("game_tiles/road_network.json") as f:
    roads = json.load(f)

# Contains 14,449 nodes and 19,544 edges
# Perfect for A* pathfinding algorithms
nodes = roads["nodes"]  # [{"id": 0, "x": 560799.0, "y": 4506875.0}, ...]
edges = roads["edges"]  # [{"from": 0, "to": 1, "length": 25.3}, ...]
```

## 🚀 Performance Tips

### 🔄 Tile Streaming System
```python
LOAD_RADIUS = 2  # Load 2 tiles around player

def update_loaded_tiles(player_tile_x, player_tile_y):
    for dy in range(-LOAD_RADIUS, LOAD_RADIUS + 1):
        for dx in range(-LOAD_RADIUS, LOAD_RADIUS + 1):
            tile_x = player_tile_x + dx  
            tile_y = player_tile_y + dy
            
            if not is_tile_loaded(tile_x, tile_y):
                load_tile_async(tile_x, tile_y)
```

### 🎯 Procedural Asset Placement
```python
# Place assets based on terrain type
for y in range(height):
    for x in range(width):
        terrain = grid[y, x]
        world_x, world_y = x * 5, y * 5  # Convert to world coordinates
        
        if terrain == 2:    # Parks - spawn trees
            if random.random() < 0.15:
                spawn_tree(world_x, world_y)
        elif terrain == 4:  # Buildings - spawn structures  
            spawn_building(world_x, world_y)
        elif terrain == 1:  # Roads - spawn street items
            if random.random() < 0.05:
                spawn_street_light(world_x, world_y)
```

## 📊 Technical Details

### File Sizes (After Decompression)
- **grid_uint8.npy**: 38MB (master array)
- **tilemap.csv**: 75MB (human-readable format)  
- **buildings.geojson**: 557MB (detailed building data)
- **PNG tiles**: ~3MB total (621 optimized images)

### Coordinate System
- **Projection**: EPSG:32618 (UTM Zone 18N)
- **Origin**: (560,795m, 4,506,875m) in UTM coordinates
- **Cell Resolution**: 5m × 5m per grid cell
- **Tile Coverage**: 1.28km × 1.28km per PNG tile

### Real-World Data Sources
- **Buildings**: 142,124 structures from OpenStreetMap
- **Roads**: 23,439 road segments with accurate geometry
- **Parks**: 9,764 green spaces and recreational areas  
- **Water**: 1,190 water bodies including full coastline
- **Retail**: 2,270 commercial and shopping locations

## 🔧 Regenerating the Map

To recreate the map with different parameters:

```bash
# Download fresh OpenStreetMap data
python3 Staten_island.py

# Generate tiles with custom settings
python3 memory_efficient_tiles.py

# Compress large files for GitHub
python3 -c "
import gzip
with open('game_tiles/tilemap.csv', 'rb') as f_in:
    with gzip.open('game_tiles_compressed/tilemap.csv.gz', 'wb') as f_out:
        f_out.writelines(f_in)
"
```

## 🎮 Example Game Types

- **🏎️ Racing Games**: Use real road network for authentic tracks
- **🌍 Open World**: Massive explorable Staten Island environment
- **⚔️ Strategy**: Large-scale tactical gameplay with realistic terrain
- **🏗️ City Builder**: Expand on real urban planning data
- **🎯 Survival**: Navigate realistic geography and landmarks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b amazing-feature`)
3. Make your changes
4. Test with the decompression script
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Map data © [OpenStreetMap](https://www.openstreetmap.org/) contributors, licensed under [ODbL](https://opendatacommons.org/licenses/odbl/).

## ⭐ Acknowledgments

- **OpenStreetMap Contributors**: For providing real-world geographic data
- **Staten Island, NY**: For being an amazing island to map! 🗽
- **Game Developers**: Who will bring this map to life in their projects

---

### 🚀 Ready to Build Amazing Games?

This massive Staten Island map provides **39+ million cells** of authentic geographic data, perfect for creating immersive 2D games with realistic proportions and detailed terrain variety.

**Don't forget to run `python3 decompress_files.py` first!** ⚡
