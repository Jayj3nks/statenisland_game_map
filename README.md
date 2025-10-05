# 🗺️ Staten Island Game Map Collection

> **Complete game-ready map collection of Staten Island with multiple formats for different game types**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Game Ready](https://img.shields.io/badge/Game%20Ready-Unity%20|%20Godot%20|%202D%20Engines-green.svg)](#-quick-start)

## 🚀 Quick Start

**1. Extract compressed files:**
```bash
python3 decompress_topographic_files.py
```

**2. Choose your map format:**
- **🏔️ Unity/3D Games**: Use `game_tiles_topographic/` 
- **🎮 2D RPG Games**: Use `game_ready_map/`

**3. Preview your maps:**
```bash
python3 -m http.server 8080
# Unity preview: http://localhost:8080/game_tiles/map_viewer.html
# 2D RPG preview: http://localhost:8080/game_ready_map/rpg_viewer.html
```

---

## 📊 Map Collection Overview

| Format | Use Case | Resolution | Coverage | Files |
|--------|----------|------------|----------|-------|
| **🏔️ Topographic** | Unity, 3D, Strategy | 5m per cell | 39M+ cells | 621 PNG tiles + metadata |
| **🎮 RPG Style** | 2D RPG, Pokémon-like | 1m per tile | 1.5M tiles | TMX + 16×16px tileset |

### **Real-World Coverage**
- **Area**: 976.9 km² of authentic Staten Island
- **Dimensions**: 28.9km × 33.8km  
- **Features**: Roads, buildings, parks, water, elevation data
- **Source**: OpenStreetMap + real topographic data

---

## 📁 Repository Structure

```
staten-island-maps/
├── 🎯 game_tiles_topographic/        # Unity/3D Games (RECOMMENDED)
│   ├── metadata.json                 # Map specs + elevation data
│   ├── tiles/                        # 621 PNG tiles (256×256 cells)
│   ├── road_network.json            # AI pathfinding graph
│   └── topographic_viewer.html      # Interactive preview
├── 🎮 game_ready_map/               # 2D RPG Games
│   ├── pokemon_tileset.png          # 16×16px tileset
│   ├── staten_island_pokemon.tmx    # TMX tilemap
│   ├── pokemon_metadata.json       # 2D game specifications  
│   ├── rpg_viewer.html             # RPG-style viewer
│   └── README.md                   # 2D integration guide
├── 📊 game_tiles/                  # Standard version (backup)
│   ├── metadata.json
│   ├── tiles/
│   ├── grid_uint8.npy             # Raw data (37MB)
│   ├── tilemap.csv                # Human-readable (75MB)
│   └── map_viewer.html            # Basic viewer
├── 🗜️ [compressed folders]/        # Compressed source data
├── 📖 README.md                    # This file
├── 📋 QUICK_START.md              # 2-step setup
└── 🔧 [utility scripts]/          # Data processing tools
```

---

## 🎮 Unity Integration (Recommended)

### **Use: `game_tiles_topographic/`**

**Quick Setup:**
```csharp
// Load map configuration
string metadataPath = "game_tiles_topographic/metadata.json";
string json = File.ReadAllText(metadataPath);
MapConfig config = JsonUtility.FromJson<MapConfig>(json);

// Tile streaming system
Vector2 playerPos = player.transform.position;
int tileX = Mathf.FloorToInt(playerPos.x / (256 * 5f)); // 5m per cell
int tileY = Mathf.FloorToInt(playerPos.y / (256 * 5f));

// Load terrain + elevation tile
string tilePath = $"game_tiles_topographic/tiles/topo_{tileY:D3}_{tileX:D3}.png";
```

**Features:**
- ✅ **39+ million cells** of detailed terrain data
- ✅ **Elevation data** (0-45.7m) for tactical gameplay  
- ✅ **7 terrain types**: Ocean, water, land, parks, buildings, roads, retail
- ✅ **Tile streaming** optimized for performance
- ✅ **Real coordinates** with UTM projection system

---

## 🕹️ 2D RPG Integration

### **Use: `game_ready_map/`**

**Quick Setup:**
- **Tiled Editor**: Open `staten_island_pokemon.tmx` directly
- **Godot**: Import TMX file → TileMap node
- **Unity**: Use TMX importer + `pokemon_tileset.png`
- **GameMaker**: Import tileset + use CSV layer data

**Features:**
- ✅ **1,156 × 1,351 tiles** in Pokémon Emerald style
- ✅ **16×16 pixel tiles** for classic 2D RPG feel
- ✅ **TMX format** compatible with all major 2D engines
- ✅ **8 terrain types** with walkability data
- ✅ **Interactive RPG viewer** with Game Boy Advance-style viewport

---

## 🔧 Available Tools

### **Data Processing:**
- `decompress_topographic_files.py` - Extract compressed map data
- `decompress_files.py` - Extract standard map data  
- `pokemon_emerald_converter.py` - Convert to 2D RPG format
- `Staten_island.py` - Download fresh OpenStreetMap data

### **Viewers:**
- `game_tiles/map_viewer.html` - Standard map preview
- `game_tiles_topographic/topographic_viewer.html` - Enhanced preview
- `game_ready_map/rpg_viewer.html` - 2D RPG-style viewer

---

## 🎯 Game Types Supported

### **🏗️ Strategy & Simulation**
- **High ground advantages** using elevation data
- **Real road networks** for pathfinding and logistics  
- **Authentic geography** for realistic city building
- **Resource placement** based on terrain types

### **🎮 2D RPGs & Adventures**  
- **Pokémon-style exploration** with classic 16×16 tiles
- **Overworld adventure** with authentic Staten Island layout
- **Route-based progression** using real road systems
- **Town and wilderness** areas clearly defined

### **🚗 Racing & Open World**
- **Real street networks** for authentic racing experiences
- **Elevation changes** for hill climbs and terrain variety
- **Massive open world** covering entire Staten Island
- **Landmarks and POIs** from real geographic data

---

## ⚡ Performance Specifications

### **Memory Usage**
- **Unity version**: ~38MB grid data + on-demand tile loading
- **2D RPG version**: ~1.6MB grid + 2KB tileset
- **Streaming**: Only visible tiles loaded at runtime

### **Recommended Viewport Sizes**
- **Unity**: Adjustable camera with LOD system
- **2D RPG**: 240×160 (GBA) to 800×600 (modern)
- **Web preview**: 640×480 default with zoom controls

---

## 📄 Data Sources & License

**Map Data**: © [OpenStreetMap](https://www.openstreetmap.org/) contributors ([ODbL License](https://opendatacommons.org/licenses/odbl/))  
**Elevation Data**: Real topographic points from geographic surveys  
**Generated Assets**: Available for game development use under MIT License

### **Authenticity**
- ✅ **142,124 real buildings** from OpenStreetMap
- ✅ **23,439 road segments** with accurate geometry  
- ✅ **76 elevation points** from actual geographic data
- ✅ **Recognizable landmarks** and authentic Staten Island shape

---

## 🚀 Getting Started

### **For Unity Developers**
1. Extract files: `python3 decompress_topographic_files.py`
2. Import `game_tiles_topographic/` folder to Unity project
3. Use metadata.json for coordinate system and tile specifications
4. Implement tile streaming based on player position
5. Add elevation-based gameplay mechanics

### **For 2D Game Developers**  
1. Open `game_ready_map/staten_island_pokemon.tmx` in Tiled Editor
2. Import tileset and tilemap to your game engine
3. Use walkability data from metadata for collision detection
4. Add player movement and camera following
5. Build your Staten Island RPG adventure!

### **For Custom Engines**
1. Load `grid_uint8.npy` with NumPy for direct data access
2. Parse `metadata.json` for terrain types and coordinates
3. Implement your own rendering and game logic
4. Use road network data for AI pathfinding

---

## ✅ Production Ready

Your Staten Island map collection provides:
- ✅ **Multiple formats** for different game genres
- ✅ **Authentic geography** with real-world accuracy  
- ✅ **Performance optimized** with tile streaming systems
- ✅ **Complete documentation** with integration examples
- ✅ **Interactive viewers** for testing and preview
- ✅ **Cross-platform compatibility** for all major game engines

**🎮 Build amazing games with authentic Staten Island geography!**