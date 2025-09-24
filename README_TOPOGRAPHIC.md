# 🏔️ MASSIVE 2D STATEN ISLAND MAP - TOPOGRAPHIC EDITION

> **Real-world Staten Island with authentic topography as a massive 2D game map**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Topographic](https://img.shields.io/badge/Topographic-Enhanced-red.svg)](README.md)
[![Game Ready](https://img.shields.io/badge/Game%20Ready-Unity%20|%20Godot%20|%20Custom-green.svg)](README.md)

## 🚀 Quick Start

**Important**: This repository uses compressed files to stay within GitHub's limits. **Run this first:**

```bash
python3 decompress_topographic_files.py
```

This extracts both original (~670MB) and topographic (~190MB) map data for complete functionality.

## 🏔️ What's New in Topographic Edition

### ✨ Enhanced Features
- **📊 Real elevation data** from 76 OpenStreetMap geographic points
- **🎨 Height-based terrain coloring** - land varies by elevation
- **🗻 Elevation range** 0-45.7 meters (authentic Staten Island topography)
- **🎮 New gameplay mechanics** for height-based advantages
- **✅ Full backward compatibility** with original version

### 🎯 Topographic Advantages
- **Strategic positioning** with high ground tactical benefits
- **Line-of-sight calculations** affected by terrain elevation
- **Realistic movement costs** for uphill/downhill travel
- **Enhanced visual depth** showing natural terrain variation
- **Height-based ballistics** for projectile physics

## 📐 Specifications

- **📏 Grid Size**: 5,783 × 6,757 cells (39,075,731 total)
- **🌍 Real Size**: 28.9km × 33.8km (authentic Staten Island dimensions)
- **🔍 Resolution**: 5 meters per cell (massive scale)
- **🗻 Elevation**: 76 real data points, 0-45.7m range
- **🎨 Visual Zones**: 5 elevation-based color zones
- **📱 Tiles**: 621 enhanced PNG tiles (256×256 cells each)

## 📂 Repository Structure

```
📦 staten-island-topographic-map/
├── 🗜️ Compressed Files (GitHub-compatible)
│   ├── game_tiles_compressed/           # Original map compressed
│   │   ├── buildings.geojson.gz         # (12.7MB → 557MB)
│   │   ├── tilemap.csv.gz              # (1.0MB → 75MB)
│   │   └── grid_uint8.npy.gz           # (0.8MB → 38MB)
│   └── game_tiles_topographic_compressed/  # Topographic compressed
│       ├── elevation_grid.npy.gz       # (9.0MB → 149MB) ⭐ NEW
│       └── terrain_grid.npy.gz         # (0.8MB → 38MB)
├── 🎮 Ready-to-Use Assets
│   ├── game_tiles/                     # Original map assets
│   │   ├── metadata.json               # Original map config
│   │   ├── road_network.json          # AI navigation (3MB)
│   │   ├── map_viewer.html            # Original map preview
│   │   └── tiles/                      # 621 standard PNG tiles
│   └── game_tiles_topographic/         # ⭐ ENHANCED TOPOGRAPHIC
│       ├── metadata.json               # Enhanced with elevation specs
│       ├── road_network.json          # AI navigation (copied)
│       ├── topographic_viewer.html    # Topographic preview
│       └── tiles/                      # 621 topographic PNG tiles
├── 🗺️ Source Data
│   └── staten_island_osm/              # OpenStreetMap data
├── 🐍 Scripts
│   ├── decompress_topographic_files.py # ⚡ EXTRACT FILES FIRST
│   └── fast_topographic_tiles.py       # Topographic generator
└── 📖 Documentation
    ├── README_TOPOGRAPHIC.md           # This file
    └── TOPOGRAPHIC_ENHANCEMENT_SUMMARY.md
```

## ⚡ Getting Started

### 1. Clone & Extract
```bash
git clone https://github.com/YOUR_USERNAME/staten-island-topographic-map.git
cd staten-island-topographic-map

# CRITICAL: Extract compressed files first!
python3 decompress_topographic_files.py
```

### 2. Choose Your Version
```bash
# Original flat map (backward compatibility)
ls game_tiles/

# Enhanced topographic map (recommended)  
ls game_tiles_topographic/
```

### 3. Preview Maps
```bash
# View original map
open game_tiles/map_viewer.html

# View topographic enhancements
open game_tiles_topographic/topographic_viewer.html
```

## 🏔️ Elevation Zones

| Zone | Height | Color Hint | Strategic Value | Gameplay Impact |
|------|--------|------------|-----------------|------------------|
| 🌊 Sea Level | 0-10m | Deep blue tones | Ports, water access | Standard movement |
| 🟢 Low Land | 10-25m | Green variations | Farmland, settlements | Easy terrain |
| 🟡 Mid Land | 25-40m | Yellow-brown | Mixed development | Moderate elevation |
| 🟠 High Land | 40-60m | Orange-brown | Strategic positions | Movement penalties |
| 🔴 Hills/Peaks | 60m+ | Red-brown | Commanding heights | Maximum advantage |

## 🎮 Game Engine Integration

### 🔷 Unity - Enhanced Integration
```csharp
// Load topographic metadata
string json = File.ReadAllText("game_tiles_topographic/metadata.json");
TopographicConfig config = JsonUtility.FromJson<TopographicConfig>(json);

// Check elevation availability
if (config.elevation.available) {
    // Load elevation grid for height calculations
    float[,] elevationGrid = LoadNumpyGrid("game_tiles_topographic/elevation_grid.npy");
    
    // Get height at world position
    float height = GetElevationAtPosition(worldX, worldY, elevationGrid);
    
    // Apply height-based game mechanics
    if (height > 30f) {
        unit.ApplyHighGroundBonus(1.25f); // 25% damage bonus
        unit.SetVisibilityRadius(unit.baseRadius * 1.5f); // Extended sight
    }
}

// Load topographic tiles for enhanced visuals
string tilePath = $"game_tiles_topographic/tiles/topo_{tileY:D3}_{tileX:D3}.png";
```

### 🟢 Godot - Topographic Implementation  
```gdscript
# Load enhanced metadata
var config = JSON.parse(file.get_as_text()).result
var elevation_data = config.elevation

# Implement elevation-based mechanics
func calculate_movement_cost(from_pos, to_pos, elevation_grid):
    var from_height = elevation_grid[from_pos.y][from_pos.x] 
    var to_height = elevation_grid[to_pos.y][to_pos.x]
    var height_diff = to_height - from_height
    
    var base_cost = 1.0
    if height_diff > 0:  # Uphill
        base_cost *= (1.0 + height_diff * 0.1)  # 10% per meter uphill
    else:  # Downhill  
        base_cost *= max(0.5, 1.0 + height_diff * 0.05)  # Faster downhill
    
    return base_cost

# Line-of-sight with elevation
func can_see_target(observer_pos, target_pos, elevation_grid):
    var observer_height = elevation_grid[observer_pos.y][observer_pos.x]
    var target_height = elevation_grid[target_pos.y][target_pos.x]
    
    # Check if terrain between blocks view considering height
    return check_line_of_sight_with_elevation(observer_pos, target_pos, 
                                             observer_height, target_height)
```

### 🔧 Custom Engine - Advanced Features
```python
import numpy as np
import json

# Load both terrain and elevation
terrain_grid = np.load("game_tiles_topographic/terrain_grid.npy")
elevation_grid = np.load("game_tiles_topographic/elevation_grid.npy")

# Advanced height-based mechanics
class TopographicGameplay:
    def __init__(self, terrain_grid, elevation_grid):
        self.terrain = terrain_grid
        self.elevation = elevation_grid
        
    def get_tactical_advantage(self, attacker_pos, defender_pos):
        """Calculate tactical advantage based on elevation difference."""
        attacker_height = self.elevation[attacker_pos[0], attacker_pos[1]]
        defender_height = self.elevation[defender_pos[0], defender_pos[1]]
        
        height_advantage = attacker_height - defender_height
        
        if height_advantage > 10:  # Significant high ground
            return 1.5  # 50% damage bonus
        elif height_advantage > 5:  # Moderate high ground
            return 1.25  # 25% damage bonus
        elif height_advantage < -10:  # Attacking uphill
            return 0.75  # 25% damage penalty
        else:
            return 1.0  # No modifier
    
    def calculate_visibility_range(self, observer_pos, base_range):
        """Calculate visibility based on elevation and terrain."""
        observer_height = self.elevation[observer_pos[0], observer_pos[1]]
        
        # Higher elevation = better visibility
        height_bonus = min(observer_height / 10.0, 2.0)  # Max 2x range
        
        return base_range * (1.0 + height_bonus)
    
    def get_artillery_range_modifier(self, gun_pos, target_pos):
        """Modify artillery range based on elevation difference."""
        gun_height = self.elevation[gun_pos[0], gun_pos[1]]
        target_height = self.elevation[target_pos[0], target_pos[1]]
        
        height_diff = gun_height - target_height
        
        # Shooting downhill increases range, uphill decreases it
        return 1.0 + (height_diff / 100.0)  # 1% per meter difference
```

## 🚀 Advanced Gameplay Examples

### 🏰 Strategy Game Integration
```python
# Castle placement on high ground
def find_optimal_castle_positions(elevation_grid, min_height=35):
    high_ground = np.where(elevation_grid >= min_height)
    positions = list(zip(high_ground[0], high_ground[1]))
    
    # Sort by elevation (highest first)
    return sorted(positions, key=lambda pos: elevation_grid[pos], reverse=True)

# Siege warfare with elevation
def calculate_siege_effectiveness(attacker_pos, castle_pos, elevation_grid):
    attacker_height = elevation_grid[attacker_pos]
    castle_height = elevation_grid[castle_pos]
    
    if castle_height > attacker_height + 20:
        return 0.5  # Very difficult uphill siege
    elif castle_height > attacker_height + 10:
        return 0.75  # Difficult siege
    else:
        return 1.0  # Standard siege difficulty
```

### 🏎️ Racing Game Integration
```python
# Dynamic track difficulty based on elevation
def calculate_track_section_difficulty(start_pos, end_pos, elevation_grid):
    start_height = elevation_grid[start_pos]
    end_height = elevation_grid[end_pos]
    
    gradient = abs(end_height - start_height) / distance(start_pos, end_pos)
    
    if gradient > 0.15:  # Steep (>15% grade)
        return "expert"
    elif gradient > 0.08:  # Moderate (8-15% grade)  
        return "intermediate"
    else:
        return "beginner"
```

## 📊 Performance & Optimization

### File Sizes After Decompression
- **Original map data**: ~670MB total
- **Topographic additions**: ~190MB total  
- **Combined working set**: ~860MB
- **Runtime memory**: Grids loaded on-demand

### Optimization Strategies
```python
# Memory-efficient elevation access
class ElevationManager:
    def __init__(self, elevation_file):
        self.elevation_mmap = np.memmap(elevation_file, dtype=np.float32, mode='r')
        self.cache = {}  # Cache frequently accessed areas
    
    def get_elevation(self, x, y):
        cache_key = (x // 64, y // 64)  # 64x64 cell cache blocks
        if cache_key not in self.cache:
            # Load 64x64 block into cache
            self.cache[cache_key] = self.elevation_mmap[y:y+64, x:x+64].copy()
        
        return self.cache[cache_key][y % 64, x % 64]
```

## 🎯 Game Types Perfect for Topographic Features

### 🏰 **Strategy Games**
- **High ground advantages** in combat
- **Defensive positions** on hills and ridges
- **Supply line challenges** over difficult terrain
- **Artillery placement** for maximum effectiveness

### 🎮 **Tactical RPGs**  
- **Movement costs** based on elevation changes
- **Line-of-sight mechanics** for spells and abilities
- **Environmental storytelling** through terrain
- **Ambush positions** in elevated locations

### 🚗 **Racing/Driving Games**
- **Hill climbs** and mountain passes
- **Elevation-based track difficulty**
- **Realistic physics** for uphill/downhill sections
- **Scenic routes** following natural topography

### 🎯 **Simulation Games**
- **Water flow** and drainage systems
- **Building placement** considering foundations
- **Transportation networks** adapting to terrain
- **Urban planning** with elevation constraints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b amazing-topographic-feature`)
3. Test with decompression script (`python3 decompress_topographic_files.py`)
4. Commit changes (`git commit -m 'Add amazing topographic feature'`)
5. Push to branch (`git push origin amazing-topographic-feature`)
6. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Map data © [OpenStreetMap](https://www.openstreetmap.org/) contributors, licensed under [ODbL](https://opendatacommons.org/licenses/odbl/).

## ⭐ Key Advantages of Topographic Edition

### 🏔️ **Realistic Terrain**
- Authentic Staten Island elevation data
- Natural terrain variation and depth
- Strategic gameplay opportunities

### 🎮 **Enhanced Gameplay**
- Height-based tactical advantages
- Line-of-sight calculations
- Elevation-aware movement costs
- Artillery and projectile physics

### 🎨 **Visual Appeal**
- Terrain colors vary by elevation
- Natural-looking landscape
- Enhanced depth perception
- Professional cartographic appearance

### 💻 **Technical Excellence**
- Backward compatible with original
- Memory-efficient implementation
- Cross-platform compatibility
- Production-ready optimization

---

### 🚀 Ready for Advanced 2D Gaming!

This topographic Staten Island map provides **authentic elevation data** integrated with **39+ million cells** of detailed terrain, perfect for creating immersive 2D games with realistic topographic advantages and strategic gameplay depth.

**Don't forget: Run `python3 decompress_topographic_files.py` first!** 🏔️⚡