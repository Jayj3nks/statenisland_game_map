# 🗺️ Staten Island Game Map

> **Massive 2D game-ready map of Staten Island with terrain classification and topographic elevation data**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Game Ready](https://img.shields.io/badge/Game%20Ready-Unity%20|%20Godot%20|%20Custom-green.svg)](#game-engine-integration)

## 🚀 Quick Start

**1. Extract compressed files:**
```bash
python3 decompress_topographic_files.py
```

**2. View your map:**
```bash
python3 -m http.server 8080
# Open: http://localhost:8080/map_viewer.html
```

**3. For Unity development, use:**
```
/game_tiles_topographic/ folder
```

---

## 📊 Map Specifications

| Property | Value |
|----------|--------|
| **Grid Size** | 5,783 × 6,757 cells |
| **Total Cells** | 39,075,731 |
| **Real World Size** | 28.9km × 33.8km |
| **Total Area** | 976.9 km² |
| **Resolution** | 5 meters per cell |
| **PNG Tiles** | 621 files (256×256 cells each) |
| **Coordinate System** | EPSG:32618 (UTM Zone 18N) |

---

## 🎨 What You Get

### **Unified Map System** 
Your map combines **both** terrain classification AND topographic elevation:

**7 Terrain Types:**
- 🌊 Ocean/Empty (45.3%) - `#001133`
- 💧 Water Bodies (35.7%) - `#4682B4` 
- 🏞️ Land Areas (9.9%) - `#D2B48C` + elevation variations
- 🌳 Parks/Green (4.7%) - `#228B22`
- 🏢 Buildings (3.5%) - `#A9A9A9`
- 🛣️ Roads (1.0%) - `#707070`
- 🛍️ Retail (0.0%) - `#FF8C00`

**Elevation Data:**
- 76 real geographic data points
- Height range: 0-45.7 meters
- 5 elevation zones with visual color variations
- Strategic gameplay advantages (high ground, line-of-sight)

---

## 📁 File Structure

```
staten-island-map/
├── 🎯 game_tiles_topographic/     ← USE THIS FOR UNITY
│   ├── metadata.json              ← Map configuration + elevation
│   ├── tiles/                     ← 621 PNG files (terrain + elevation)
│   └── road_network.json          ← AI pathfinding graph
├── 🗺️ game_tiles/                ← Standard version (backup)
│   ├── metadata.json
│   ├── tiles/ 
│   ├── grid_uint8.npy             ← Raw terrain data (37MB)
│   └── tilemap.csv                ← Human-readable grid (75MB)
├── 📊 staten_island_osm/          ← Source OpenStreetMap data
│   └── buildings.geojson          ← 142,124 building polygons (557MB)
├── 🖥️ map_viewer.html             ← Interactive map preview
└── 📖 README.md                   ← This file
```

---

## 🎮 Unity Integration

### Basic Setup
```csharp
// Load unified map configuration
string metadataPath = "game_tiles_topographic/metadata.json";
string json = File.ReadAllText(metadataPath);
MapConfig config = JsonUtility.FromJson<MapConfig>(json);

// Check elevation availability
bool hasElevation = config.elevation.available; // true
float maxHeight = config.elevation.range_meters[1]; // 45.7m
```

### Tile Streaming
```csharp
// Calculate tile coordinates from world position
Vector2 playerPos = player.transform.position;
int tileX = Mathf.FloorToInt(playerPos.x / (256 * 5f)); // 5m per cell
int tileY = Mathf.FloorToInt(playerPos.y / (256 * 5f));

// Load unified terrain + elevation tile
string tilePath = $"game_tiles_topographic/tiles/topo_{tileY:D3}_{tileX:D3}.png";
Texture2D unifiedTile = Resources.Load<Texture2D>(tilePath);
```

### Gameplay Mechanics
```csharp
// Apply elevation-based tactical advantages
if (IsOnHighGround(unit.position)) {
    unit.damageMultiplier = 1.5f;    // 50% damage bonus
    unit.visibilityRange *= 1.5f;    // Extended sight range
}

// Movement cost based on elevation change
float heightDiff = GetElevationDiff(fromPos, toPos);
float movementCost = 1.0f + (heightDiff * 0.1f); // 10% per meter uphill
```

---

## 🖥️ Map Viewer

**Interactive HTML viewer to preview your map:**

```bash
# Start local server
python3 -m http.server 8080

# Open in browser
http://localhost:8080/map_viewer.html
```

**Features:**
- ✅ View complete 621-tile map grid
- ✅ Switch between topographic and standard versions  
- ✅ Zoom and pan functionality
- ✅ Click tiles for detailed information
- ✅ Real-time tile loading statistics

**Keyboard Shortcuts:**
- `1` - Topographic map (recommended)
- `2` - Standard map  
- `+/-` - Zoom in/out
- `R` - Reload tiles

---

## ⚡ Performance Tips

### For Unity Development:
1. **Tile Streaming**: Load only 5-9 tiles around player (2-tile radius)
2. **LOD System**: Use lower resolution for distant tiles  
3. **Memory Management**: Unload tiles outside view distance
4. **Async Loading**: Load tiles in background to prevent frame drops

### File Sizes (After Decompression):
- **Total map data**: ~860MB
- **Runtime memory**: Load tiles on-demand
- **Each tile**: 1.28km × 1.28km coverage

---

## 🎯 Game Types Supported

### ✅ Perfect For:
- **Strategy Games**: High ground tactical advantages
- **Racing Games**: Real road network and elevation changes  
- **Open World**: Massive explorable Staten Island environment
- **Tactical RPGs**: Line-of-sight and movement cost mechanics
- **City Builders**: Authentic urban planning constraints

### 🚀 Advanced Features Available:
- Height-based combat bonuses
- Elevation-aware line-of-sight calculations
- Realistic movement costs (uphill/downhill)
- Artillery range modifications
- Strategic positioning gameplay

---

## 🔧 Development Workflow

### 1. Setup
```bash
# Extract compressed files
python3 decompress_topographic_files.py

# Preview your map
python3 -m http.server 8080
# Visit: http://localhost:8080/map_viewer.html
```

### 2. Unity Import
1. Copy `/game_tiles_topographic/` to your Unity project
2. Import 621 PNG tiles as Texture2D assets
3. Parse `metadata.json` for world coordinates
4. Implement tile streaming based on player position

### 3. Add Gameplay
1. Use terrain type data (0-6) for collision detection
2. Implement elevation-based mechanics for strategy
3. Use road network data for AI pathfinding

---

## 📄 License

**Map Data**: © [OpenStreetMap](https://www.openstreetmap.org/) contributors, [ODbL License](https://opendatacommons.org/licenses/odbl/)  
**Generated Content**: Available for game development use

---

## ✅ Ready for Production

Your unified Staten Island map provides:
- ✅ **39+ million cells** of authentic geographic data
- ✅ **Terrain classification** for collision and gameplay mechanics  
- ✅ **Topographic elevation** for strategic advantages
- ✅ **Unity-ready tile system** with 621 optimized PNG files
- ✅ **Complete metadata** with coordinate system specifications
- ✅ **AI pathfinding** graph with 14,449 nodes

**🎮 Start building your game with realistic Staten Island geography!**