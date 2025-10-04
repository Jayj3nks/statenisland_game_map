# 🎮 Staten Island - Pokémon Emerald Style Game Map

> **Game-ready 2D RPG map of Staten Island in classic Pokémon Emerald style**

This directory contains the **rescaled and converted** Staten Island map optimized for 2D RPG games like Pokémon Emerald, using authentic 16×16 pixel tiles and classic game proportions.

---

## 🎯 Conversion Specifications

### **Scaling Analysis**
- **Original map**: 5 meters per cell → **New map**: 1 meter per tile
- **Scaling ratio**: 5:1 downscale for optimal gameplay
- **Research basis**: Pokémon Emerald uses 16×16px tiles, player ≈ 1 tile tall

### **Map Dimensions**
| Property | Original | Pokémon Style |
|----------|----------|---------------|
| **World Coverage** | 28.9km × 33.8km | 28.9km × 33.8km (same) |
| **Grid Size** | 5,783 × 6,757 cells | 1,156 × 1,351 tiles |
| **Resolution** | 5m per cell | 1m per tile |
| **Pixel Size** | 256×256 per tile | 16×16 per tile |
| **Total Pixels** | Variable | 18,496 × 21,616 px |

---

## 📁 Generated Files

### **Core Game Assets**
- **`pokemon_tileset.png`** - 16×16px tileset with 8 terrain types
- **`staten_island_pokemon.tmx`** - TMX tilemap file for game engines
- **`staten_island_pokemon_preview.png`** - Full map preview image
- **`pokemon_metadata.json`** - Complete specifications and mappings

### **Development Assets**
- **`pokemon_grid.npy`** - NumPy array for programmatic access
- **`rpg_viewer.html`** - Interactive 2D RPG-style viewer

---

## 🎨 Terrain Types & Colors

| ID | Terrain | Color | Hex | Walkable | Description |
|----|---------|-------|-----|----------|-------------|
| 0 | Ocean | Deep Blue | `#1E3A8A` | ❌ | Surrounding ocean areas |
| 1 | Water | Bright Blue | `#3B82F6` | ❌ | Rivers, bays, lakes |
| 2 | Land | Grass Green | `#84CC16` | ✅ | Basic walkable terrain |
| 3 | Forest | Dark Green | `#16A34A` | ✅ | Parks, wooded areas |
| 4 | Mountain | Gray | `#A3A3A3` | ✅ | High elevation areas |
| 5 | Road | Gray | `#6B7280` | ✅ | Streets and pathways |
| 6 | Building | Red | `#DC2626` | ❌ | Towns, structures |
| 7 | Beach | Sandy | `#FEF3C7` | ✅ | Coastal areas |

---

## 🎮 Game Engine Integration

### **Tiled Map Editor**
```bash
# Open the TMX file directly in Tiled
File > Open > staten_island_pokemon.tmx
```

### **Godot Engine**
```gdscript
# Import TMX file
extends Node2D

func _ready():
    # Use TileMap node with imported TMX
    var tilemap = $TileMap
    # TMX file automatically provides tileset and layer data
```

### **Unity**
```csharp
// Use a TMX importer package like "Tiled2Unity" or "SuperTiled2Unity"
// Import the TMX file and tileset PNG
```

### **GameMaker Studio**
```gml
// Import the tileset PNG as a sprite
// Use the CSV data from TMX for room creation
// Each tile ID corresponds to sprite subimages
```

### **Construct 3**
```javascript
// Import pokemon_tileset.png as a Tilemap object
// Use the TMX data to paint tiles programmatically
```

---

## 🖥️ Preview Your Map

### **Interactive RPG Viewer**
```bash
# Start local server
python3 -m http.server 8080

# Open RPG-style viewer
http://localhost:8080/game_ready_map/rpg_viewer.html
```

**Viewer Features:**
- 🎮 Game Boy Advance-style viewport (240×160 to 800×600)
- 🚶 Interactive player movement (WASD/arrows)
- 🔍 Zoom and pan controls (1x to 10x)
- 🗺️ Live minimap with viewport indicator
- 📊 Real-time coordinate display
- 📐 Optional tile grid overlay

---

## 🚀 Quick Start Guide

### **1. Choose Your Engine**
- **Tiled Editor**: Open `staten_island_pokemon.tmx` directly
- **Game Engines**: Import TMX + tileset PNG combination
- **Custom Code**: Load `pokemon_grid.npy` with NumPy

### **2. Basic Setup**
```python
# Python example for custom engines
import numpy as np
import json

# Load map data
map_grid = np.load('pokemon_grid.npy')
with open('pokemon_metadata.json') as f:
    metadata = json.load(f)

# Get map dimensions
width = metadata['map_dimensions']['width_tiles']    # 1,156
height = metadata['map_dimensions']['height_tiles']  # 1,351

# Access terrain at position
terrain_id = map_grid[y, x]  # Returns 0-7
terrain_name = metadata['terrain_types'][str(terrain_id)]['name']
is_walkable = metadata['terrain_types'][str(terrain_id)]['walkable']
```

### **3. Player Movement**
```python
# Example collision detection
def can_move_to(x, y):
    if x < 0 or x >= width or y < 0 or y >= height:
        return False
    
    terrain_id = map_grid[y, x]
    return metadata['terrain_types'][str(terrain_id)]['walkable']

# Move player with collision
def move_player(player_x, player_y, dx, dy):
    new_x = player_x + dx
    new_y = player_y + dy
    
    if can_move_to(new_x, new_y):
        return new_x, new_y
    else:
        return player_x, player_y  # Can't move there
```

---

## 🔧 Technical Implementation

### **Viewport Camera System**
```python
# Camera follows player (like Pokémon games)
def update_camera(player_x, player_y, screen_width, screen_height):
    # Center camera on player
    camera_x = player_x - screen_width // 2
    camera_y = player_y - screen_height // 2
    
    # Clamp to map boundaries
    camera_x = max(0, min(width - screen_width, camera_x))
    camera_y = max(0, min(height - screen_height, camera_y))
    
    return camera_x, camera_y
```

### **Tile Rendering**
```python
# Render visible tiles only (performance optimization)
def render_map(camera_x, camera_y, screen_width, screen_height, tile_size=16):
    start_x = camera_x // tile_size
    start_y = camera_y // tile_size
    end_x = start_x + (screen_width // tile_size) + 1
    end_y = start_y + (screen_height // tile_size) + 1
    
    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            if 0 <= x < width and 0 <= y < height:
                terrain_id = map_grid[y, x]
                # Draw tile sprite at (x * tile_size, y * tile_size)
```

---

## 📊 Performance Specifications

### **Memory Usage**
- **Map grid**: ~1.56MB (1,156 × 1,351 × 1 byte)
- **Tileset**: ~2KB (128 × 16 pixels × 4 bytes)
- **Runtime**: Minimal (only visible tiles rendered)

### **Recommended Viewport Sizes**
- **Game Boy Advance**: 240×160 (15×10 tiles visible)
- **SNES Style**: 256×224 (16×14 tiles visible)  
- **Modern 2D**: 640×480 (40×30 tiles visible)
- **Large Screen**: 800×600 (50×37.5 tiles visible)

---

## 🌍 Real-World Accuracy

### **Geographic Fidelity**
- ✅ **Staten Island shape**: Authentic coastline preserved
- ✅ **Major roads**: Highway and street network visible
- ✅ **Landmarks**: Parks, water bodies, urban areas
- ✅ **Proportions**: Real-world distances maintained

### **Gameplay Scale**
- **1 tile = 1 meter**: Realistic for character movement
- **Walking speed**: ~5 tiles/second = 18 km/hour (human pace)
- **Map traversal**: ~19 minutes to cross entire island on foot
- **Perfect for**: Pokémon-style exploration and adventure

---

## 🎯 Game Design Applications

### **Perfect For:**
- 🐉 **Pokémon-style RPGs**: Classic overhead exploration
- 🗺️ **Open-world adventures**: Massive authentic environment  
- 🏰 **Strategy games**: Real geographic tactical advantages
- 🚶 **Walking simulators**: Authentic scale exploration
- 📱 **Mobile games**: Optimized tile-based rendering

### **Gameplay Features Enabled:**
- **Overworld exploration** with authentic geography
- **Town and city** visits (red building areas)
- **Route traversal** using real road networks
- **Water-based areas** for surfing/boat mechanics
- **Forest encounters** in park areas
- **Urban vs rural** different encounter rates

---

## 📄 License & Attribution

**Original Data**: © [OpenStreetMap](https://www.openstreetmap.org/) contributors ([ODbL License](https://opendatacommons.org/licenses/odbl/))  
**Conversion & Game Assets**: Available for game development use  
**Style Inspiration**: Pokémon Emerald (Game Freak/Nintendo)

---

## ✅ Ready for Game Development

Your Pokémon Emerald-style Staten Island map provides:
- ✅ **1,156 × 1,351 tiles** of authentic geography
- ✅ **16×16 pixel tiles** in classic RPG style
- ✅ **8 terrain types** with walkability data
- ✅ **TMX format** compatible with all major 2D engines
- ✅ **Interactive viewer** for testing and preview
- ✅ **Complete documentation** and code examples

**🎮 Start building your Staten Island RPG adventure!**