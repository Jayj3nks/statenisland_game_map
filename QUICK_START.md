# 🚀 Staten Island 2D Map - Quick Start

## 🎯 Generate Your 2D Map (2 steps):
1. **Extract data**: `python3 decompress_topographic_files.py`
2. **Create 2D map**: `python3 poke_inspired_converter.py`

## 🎮 Use Your Map:
**For 2D Games**: Import `poke_inspired_2d_map/` folder to your engine  
**For Unity/3D**: Use `game_tiles_topographic/` folder

## 🖥️ Preview Your Map:
```bash
python3 -m http.server 8080
# Open: http://localhost:8080/poke_inspired_2d_map/rpg_viewer.html
```

## 📊 What You Get:
- **Area**: 976.9 km² of authentic Staten Island (28.9×33.8km)
- **Style**: Classic 2D RPG visual quality with 16×16 pixel tiles
- **Features**: Roads, buildings, parks, water + realistic geography
- **Formats**: TMX tilemap + sprite sheet + metadata

## 🎨 Character Setup:
- **Sprite Size**: 16×16 pixels (same as tiles)
- **Movement**: Grid-based (1 tile per step)
- **Camera**: Pixel-perfect, 240×160 or 320×240 viewport

## 📖 Full Guide:
See `README.md` for complete integration examples and game engine setup.