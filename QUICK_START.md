# 🚀 Staten Island Maps - Quick Start

## 🎯 Choose Your Format:
**Unity/3D Games**: `game_tiles_topographic/` (39M cells, elevation data)  
**2D RPG Games**: `game_ready_map/` (1.5M tiles, Pokémon-style)

## ⚡ 2-Step Setup:
1. **Extract data**: `python3 decompress_topographic_files.py`
2. **Preview maps**: `python3 -m http.server 8080`

## 🖥️ Viewers:
- **Unity preview**: `http://localhost:8080/game_tiles/map_viewer.html`
- **RPG preview**: `http://localhost:8080/game_ready_map/rpg_viewer.html`

## 📊 What You Get:
- **Area**: 976.9 km² of authentic Staten Island (28.9×33.8km)
- **Features**: Roads, buildings, parks, water + elevation data
- **Formats**: PNG tiles + TMX tilemap + metadata + viewers

## 📖 Full Guide:
See `README.md` for complete integration examples and documentation.
