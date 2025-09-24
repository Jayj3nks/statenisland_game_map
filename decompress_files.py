#!/usr/bin/env python3
"""
🗜️ Staten Island Map Decompression Tool
========================================

This script decompresses the large files that were compressed for GitHub compatibility.
Run this after cloning the repository to restore the original large files.

Usage:
    python3 decompress_files.py

This will extract:
- buildings.geojson.gz (12.7MB) → buildings.geojson (557MB)
- tilemap.csv.gz (1.0MB) → tilemap.csv (75MB)  
- grid_uint8.npy.gz (0.8MB) → grid_uint8.npy (38MB)
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
    print("🎮 STATEN ISLAND MAP - FILE DECOMPRESSION")
    print("=" * 50)
    print("This will restore the original large files from their compressed versions.")
    print("Make sure you have enough disk space (~670MB total).\n")
    
    # Check if we're in the right directory
    if not Path("game_tiles_compressed").exists():
        print("❌ Error: game_tiles_compressed/ directory not found!")
        print("   Make sure you're running this from the project root directory.")
        sys.exit(1)
    
    # Create directories if needed
    Path("game_tiles").mkdir(exist_ok=True)
    Path("staten_island_osm").mkdir(exist_ok=True)
    
    # Files to decompress
    files_to_decompress = [
        {
            "compressed": Path("game_tiles_compressed/buildings.geojson.gz"),
            "output": Path("staten_island_osm/buildings.geojson"),
            "description": "Building data (OpenStreetMap)"
        },
        {
            "compressed": Path("game_tiles_compressed/tilemap.csv.gz"), 
            "output": Path("game_tiles/tilemap.csv"),
            "description": "Full tilemap CSV"
        },
        {
            "compressed": Path("game_tiles_compressed/grid_uint8.npy.gz"),
            "output": Path("game_tiles/grid_uint8.npy"),
            "description": "Master grid NumPy array"
        }
    ]
    
    success_count = 0
    total_compressed = 0
    total_decompressed = 0
    
    for file_info in files_to_decompress:
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
    
    print(f"\n" + "=" * 50)
    print(f"✅ DECOMPRESSION COMPLETE!")
    print(f"📊 Successfully processed: {success_count}/{len(files_to_decompress)} files")
    print(f"📦 Total compressed size: {total_compressed/1024/1024:.1f} MB")
    print(f"📂 Total decompressed size: {total_decompressed/1024/1024:.1f} MB")
    print(f"🗜️ Overall compression ratio: {total_compressed/total_decompressed:.1%}")
    
    print(f"\n🎮 Your Staten Island map is now ready for use!")
    print(f"   • Load grid_uint8.npy for direct NumPy access")
    print(f"   • Use tilemap.csv for debugging/inspection")
    print(f"   • Reference buildings.geojson for detailed building data")
    
if __name__ == "__main__":
    main()