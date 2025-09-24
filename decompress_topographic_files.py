#!/usr/bin/env python3
"""
🏔️ Staten Island Topographic Map Decompression Tool
===================================================

This script decompresses both the original and topographic files that were 
compressed for GitHub compatibility.

Usage:
    python3 decompress_topographic_files.py

This will extract:
- Original files:
  • buildings.geojson.gz (12.7MB) → buildings.geojson (557MB)
  • tilemap.csv.gz (1.0MB) → tilemap.csv (75MB)
  • grid_uint8.npy.gz (0.8MB) → grid_uint8.npy (38MB)

- Topographic files:
  • elevation_grid.npy.gz (9.0MB) → elevation_grid.npy (149MB)
  • terrain_grid.npy.gz (0.8MB) → terrain_grid.npy (38MB)
"""

import gzip
import os
from pathlib import Path
import sys

def decompress_file(compressed_path, output_path):
    """Decompress a gzipped file."""
    print(f"📦 Decompressing {compressed_path.name}...")
    
    compressed_size = compressed_path.stat().st_size
    print(f"   📏 Compressed size: {compressed_size/1024/1024:.1f} MB")
    
    try:
        with gzip.open(compressed_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                # Read in chunks to handle large files
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = f_in.read(chunk_size)
                    if not chunk:
                        break
                    f_out.write(chunk)
        
        decompressed_size = output_path.stat().st_size
        print(f"   ✅ Decompressed to: {decompressed_size/1024/1024:.1f} MB")
        print(f"   📊 Compression ratio: {compressed_size/decompressed_size:.1%}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🏔️ STATEN ISLAND MAP - COMPLETE DECOMPRESSION")
    print("=" * 60)
    print("This will restore both original and topographic files from compressed versions.")
    print("Make sure you have enough disk space (~900MB total).\n")
    
    # Check directories
    required_dirs = ["game_tiles_compressed", "game_tiles_topographic_compressed"]
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            print(f"❌ Error: {dir_name}/ directory not found!")
            print(f"   Make sure you're running this from the project root directory.")
            return False
    
    # Create output directories
    Path("game_tiles").mkdir(exist_ok=True)
    Path("game_tiles_topographic").mkdir(exist_ok=True)
    Path("staten_island_osm").mkdir(exist_ok=True)
    
    # Files to decompress
    files_to_decompress = [
        # Original map files
        {
            "compressed": Path("game_tiles_compressed/buildings.geojson.gz"),
            "output": Path("staten_island_osm/buildings.geojson"),
            "description": "Building data (OpenStreetMap)",
            "category": "Original"
        },
        {
            "compressed": Path("game_tiles_compressed/tilemap.csv.gz"), 
            "output": Path("game_tiles/tilemap.csv"),
            "description": "Full tilemap CSV",
            "category": "Original"
        },
        {
            "compressed": Path("game_tiles_compressed/grid_uint8.npy.gz"),
            "output": Path("game_tiles/grid_uint8.npy"),
            "description": "Master grid NumPy array",
            "category": "Original"
        },
        
        # Topographic map files
        {
            "compressed": Path("game_tiles_topographic_compressed/elevation_grid.npy.gz"),
            "output": Path("game_tiles_topographic/elevation_grid.npy"),
            "description": "Elevation height grid (topographic)",
            "category": "Topographic"
        },
        {
            "compressed": Path("game_tiles_topographic_compressed/terrain_grid.npy.gz"),
            "output": Path("game_tiles_topographic/terrain_grid.npy"),
            "description": "Terrain classification grid (topographic)",
            "category": "Topographic"
        }
    ]
    
    success_count = 0
    total_compressed = 0
    total_decompressed = 0
    
    # Group by category for better organization
    categories = {}
    for file_info in files_to_decompress:
        category = file_info["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append(file_info)
    
    # Process each category
    for category, files in categories.items():
        print(f"\n📂 {category.upper()} FILES")
        print("-" * 40)
        
        for file_info in files:
            compressed_path = file_info["compressed"]
            output_path = file_info["output"]
            description = file_info["description"]
            
            print(f"\n🔄 Processing: {description}")
            
            if not compressed_path.exists():
                print(f"   ⚠️ Warning: {compressed_path} not found, skipping...")
                continue
                
            if output_path.exists():
                response = input(f"   ❓ {output_path.name} already exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    print(f"   ⏭️ Skipping {output_path.name}")
                    continue
            
            # Decompress the file
            if decompress_file(compressed_path, output_path):
                success_count += 1
                total_compressed += compressed_path.stat().st_size
                total_decompressed += output_path.stat().st_size
    
    print(f"\n" + "=" * 60)
    print(f"✅ DECOMPRESSION COMPLETE!")
    print(f"📊 Successfully processed: {success_count}/{len(files_to_decompress)} files")
    print(f"📦 Total compressed size: {total_compressed/1024/1024:.1f} MB")
    print(f"📂 Total decompressed size: {total_decompressed/1024/1024:.1f} MB")
    print(f"🗜️ Overall compression ratio: {total_compressed/total_decompressed:.1%}")
    
    print(f"\n🎮 Your Staten Island maps are now ready!")
    print(f"\n📁 ORIGINAL MAP:")
    print(f"   • game_tiles/grid_uint8.npy - Master terrain grid")
    print(f"   • game_tiles/tilemap.csv - Human-readable map data")
    print(f"   • staten_island_osm/buildings.geojson - Building details")
    
    print(f"\n🏔️ TOPOGRAPHIC MAP:")
    print(f"   • game_tiles_topographic/terrain_grid.npy - Terrain types")
    print(f"   • game_tiles_topographic/elevation_grid.npy - Height data")
    print(f"   • game_tiles_topographic/tiles/ - 621 enhanced PNG tiles")
    
    print(f"\n🚀 Both versions ready for game development!")
    
if __name__ == "__main__":
    main()