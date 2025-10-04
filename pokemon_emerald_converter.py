#!/usr/bin/env python3
"""
🎮 Staten Island → Pokémon Emerald Style Map Converter
====================================================

Converts the massive Staten Island map into a Pokémon Emerald-style 2D RPG map.

Research findings:
- Pokémon Emerald uses 16×16 pixel tiles
- Player sprite is approximately 1 tile tall (16px)
- Overworld scale: 1 tile ≈ 1-2 meters real world equivalent

Current Staten Island map:
- 5 meters per cell
- 5,783 × 6,757 cells
- 28.9km × 33.8km real world
- 621 tiles of 256×256 cells each

Target conversion:
- 1 tile ≈ 1 meter real world (5:1 downscale)
- 16×16 pixel tiles for Pokémon-style gameplay
- Maintain recognizable Staten Island geography
"""

import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import math
from pathlib import Path

class PokemonStyleConverter:
    def __init__(self):
        # Scaling configuration
        self.original_cell_size = 5.0  # meters per cell in original map
        self.target_tile_size = 1.0    # meters per tile in Pokémon-style map
        self.scaling_ratio = self.original_cell_size / self.target_tile_size  # 5:1
        
        # Visual configuration
        self.tile_pixel_size = 16      # 16×16 pixels per tile (Pokémon standard)
        
        # Load original map metadata
        with open('game_tiles_topographic/metadata.json', 'r') as f:
            self.metadata = json.load(f)
        
        print("🎮 Pokémon Emerald Style Converter Initialized")
        print(f"📊 Original: {self.metadata['grid_size'][1]} × {self.metadata['grid_size'][0]} cells")
        print(f"📐 Scaling ratio: {self.scaling_ratio}:1 (5m → 1m per tile)")
        
    def calculate_new_dimensions(self):
        """Calculate the new map dimensions after scaling"""
        original_width = self.metadata['grid_size'][1]  # 5783
        original_height = self.metadata['grid_size'][0]  # 6757
        
        # Downscale by 5:1 ratio
        new_width = int(original_width / self.scaling_ratio)   # ~1157 tiles
        new_height = int(original_height / self.scaling_ratio)  # ~1351 tiles
        
        # Real world coverage remains the same
        real_width_km = self.metadata['real_world_size_km']['width']   # 28.9km
        real_height_km = self.metadata['real_world_size_km']['height'] # 33.8km
        
        return {
            'tile_width': new_width,
            'tile_height': new_height,
            'pixel_width': new_width * self.tile_pixel_size,
            'pixel_height': new_height * self.tile_pixel_size,
            'real_width_km': real_width_km,
            'real_height_km': real_height_km,
            'meters_per_tile': self.target_tile_size
        }
    
    def create_pokemon_tileset(self):
        """Create a Pokémon-style tileset with appropriate colors and patterns"""
        
        # Define Pokémon-style terrain colors (more vibrant and game-like)
        pokemon_colors = {
            'ocean': '#1E3A8A',      # Deep blue ocean
            'water': '#3B82F6',      # Bright blue water  
            'land': '#84CC16',       # Grass green land
            'mountain': '#A3A3A3',   # Gray mountains/high elevation
            'forest': '#16A34A',     # Dark green forests
            'road': '#6B7280',       # Gray roads
            'building': '#DC2626',   # Red buildings/towns
            'beach': '#FEF3C7'       # Sandy beach areas
        }
        
        # Create tileset image (16×16 pixels per tile, 8 tiles in a row)
        tileset_width = 8 * self.tile_pixel_size   # 128 pixels
        tileset_height = 1 * self.tile_pixel_size  # 16 pixels
        tileset = Image.new('RGB', (tileset_width, tileset_height), (0, 0, 0))
        
        # Draw each terrain type tile
        terrain_tiles = [
            ('ocean', pokemon_colors['ocean']),
            ('water', pokemon_colors['water']), 
            ('land', pokemon_colors['land']),
            ('forest', pokemon_colors['forest']),
            ('mountain', pokemon_colors['mountain']),
            ('road', pokemon_colors['road']),
            ('building', pokemon_colors['building']),
            ('beach', pokemon_colors['beach'])
        ]
        
        draw = ImageDraw.Draw(tileset)
        
        for i, (name, color) in enumerate(terrain_tiles):
            x = i * self.tile_pixel_size
            y = 0
            
            # Fill base color
            draw.rectangle([x, y, x + self.tile_pixel_size - 1, y + self.tile_pixel_size - 1], 
                         fill=color)
            
            # Add simple pattern for visual interest
            if name == 'forest':
                # Add tree pattern
                draw.rectangle([x + 2, y + 2, x + 5, y + 5], fill='#15803D')
                draw.rectangle([x + 10, y + 8, x + 13, y + 11], fill='#15803D')
            elif name == 'building':
                # Add building pattern
                draw.rectangle([x + 2, y + 2, x + 13, y + 13], fill='#B91C1C')
                draw.rectangle([x + 4, y + 4, x + 6, y + 7], fill='#FEF3C7')  # window
                draw.rectangle([x + 9, y + 4, x + 11, y + 7], fill='#FEF3C7')  # window
            elif name == 'road':
                # Add road markings
                draw.line([x + 7, y, x + 7, y + 15], fill='#F3F4F6', width=1)
            elif name == 'water':
                # Add water sparkles
                draw.point([x + 3, y + 4], fill='#DBEAFE')
                draw.point([x + 11, y + 9], fill='#DBEAFE')
                draw.point([x + 6, y + 12], fill='#DBEAFE')
        
        return tileset, terrain_tiles
    
    def convert_terrain_to_pokemon_tiles(self):
        """Convert original terrain classification to Pokémon-style tile IDs"""
        
        # Mapping from original terrain types to Pokémon tile IDs
        terrain_mapping = {
            0: 0,  # empty/ocean → ocean
            1: 5,  # road → road  
            2: 3,  # park → forest
            3: 1,  # water → water
            4: 6,  # building → building
            5: 6,  # retail → building
            6: 2   # land → land
        }
        
        return terrain_mapping
    
    def load_and_resample_map(self):
        """Load original map data and resample to Pokémon scale"""
        
        print("📁 Loading original map data...")
        
        # Try to load the numpy grid if available
        grid_path = Path('game_tiles/grid_uint8.npy')
        if grid_path.exists():
            print(f"✅ Loading grid from {grid_path}")
            original_grid = np.load(grid_path)
        else:
            print("⚠️  Grid file not found, using sample data")
            # Create sample data for demonstration
            original_grid = np.random.randint(0, 7, 
                                            (self.metadata['grid_size'][0], 
                                             self.metadata['grid_size'][1]), 
                                            dtype=np.uint8)
        
        print(f"📊 Original grid shape: {original_grid.shape}")
        
        # Calculate new dimensions
        new_dims = self.calculate_new_dimensions()
        
        # Resample using simple downsampling (take every 5th cell)
        print(f"🔄 Resampling from {original_grid.shape} to ({new_dims['tile_height']}, {new_dims['tile_width']})")
        
        # Simple downsampling: take every nth cell where n = scaling_ratio
        step = int(self.scaling_ratio)
        resampled_grid = original_grid[::step, ::step]
        
        # Ensure we get the target dimensions (crop or pad if necessary)
        target_height, target_width = new_dims['tile_height'], new_dims['tile_width']
        
        if resampled_grid.shape[0] > target_height:
            resampled_grid = resampled_grid[:target_height, :]
        if resampled_grid.shape[1] > target_width:
            resampled_grid = resampled_grid[:, :target_width]
            
        print(f"✅ Final resampled grid shape: {resampled_grid.shape}")
        
        return resampled_grid, new_dims
    
    def create_pokemon_map_image(self, resampled_grid, terrain_mapping):
        """Create the final Pokémon-style map image"""
        
        print("🎨 Creating Pokémon-style map image...")
        
        height, width = resampled_grid.shape
        
        # Create the map image
        map_width = width * self.tile_pixel_size
        map_height = height * self.tile_pixel_size
        map_image = Image.new('RGB', (map_width, map_height), (0, 0, 0))
        
        # Load tileset colors
        pokemon_colors = {
            0: '#1E3A8A',  # ocean
            1: '#3B82F6',  # water
            2: '#84CC16',  # land
            3: '#16A34A',  # forest
            4: '#A3A3A3',  # mountain
            5: '#6B7280',  # road
            6: '#DC2626',  # building
            7: '#FEF3C7'   # beach
        }
        
        draw = ImageDraw.Draw(map_image)
        
        # Draw each tile
        for y in range(height):
            for x in range(width):
                original_terrain = resampled_grid[y, x]
                pokemon_tile = terrain_mapping.get(original_terrain, 0)
                
                # Get color for this tile
                color = pokemon_colors.get(pokemon_tile, '#000000')
                
                # Draw the tile
                pixel_x = x * self.tile_pixel_size
                pixel_y = y * self.tile_pixel_size
                
                draw.rectangle([pixel_x, pixel_y, 
                              pixel_x + self.tile_pixel_size - 1, 
                              pixel_y + self.tile_pixel_size - 1], 
                             fill=color)
        
        return map_image
    
    def create_tmx_tilemap(self, resampled_grid, terrain_mapping, dimensions):
        """Create a TMX format tilemap file for game engines"""
        
        print("📄 Creating TMX tilemap...")
        
        height, width = resampled_grid.shape
        
        # Convert terrain data to tile IDs
        tile_data = []
        for y in range(height):
            row = []
            for x in range(width):
                original_terrain = resampled_grid[y, x]
                pokemon_tile = terrain_mapping.get(original_terrain, 0) + 1  # TMX uses 1-based indexing
                row.append(pokemon_tile)
            tile_data.append(row)
        
        # Create TMX XML content
        tmx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.1" orientation="orthogonal" renderorder="right-down" 
     width="{width}" height="{height}" tilewidth="16" tileheight="16" 
     infinite="0" nextlayerid="2" nextobjectid="1">
  
  <tileset firstgid="1" name="pokemon_tileset" tilewidth="16" tileheight="16" tilecount="8" columns="8">
    <image source="pokemon_tileset.png" width="128" height="16"/>
    <tile id="0">
      <properties>
        <property name="name" value="ocean"/>
        <property name="type" value="water"/>
      </properties>
    </tile>
    <tile id="1">
      <properties>
        <property name="name" value="water"/>
        <property name="type" value="water"/>
      </properties>
    </tile>
    <tile id="2">
      <properties>
        <property name="name" value="land"/>
        <property name="type" value="ground"/>
      </properties>
    </tile>
    <tile id="3">
      <properties>
        <property name="name" value="forest"/>
        <property name="type" value="ground"/>
      </properties>
    </tile>
    <tile id="4">
      <properties>
        <property name="name" value="mountain"/>
        <property name="type" value="ground"/>
      </properties>
    </tile>
    <tile id="5">
      <properties>
        <property name="name" value="road"/>
        <property name="type" value="ground"/>
      </properties>
    </tile>
    <tile id="6">
      <properties>
        <property name="name" value="building"/>
        <property name="type" value="ground"/>
      </properties>
    </tile>
    <tile id="7">
      <properties>
        <property name="name" value="beach"/>
        <property name="type" value="ground"/>
      </properties>
    </tile>
  </tileset>

  <layer id="1" name="Terrain" width="{width}" height="{height}">
    <data encoding="csv">
'''
        
        # Add tile data
        for y, row in enumerate(tile_data):
            line = ",".join(map(str, row))
            if y < len(tile_data) - 1:
                line += ","
            tmx_content += f"{line}\n"
        
        tmx_content += '''    </data>
  </layer>
</map>'''
        
        return tmx_content
    
    def generate_metadata(self, dimensions, terrain_mapping):
        """Generate metadata for the new Pokémon-style map"""
        
        metadata = {
            "name": "Staten Island - Pokémon Emerald Style",
            "version": "1.0-pokemon-style",
            "description": "Staten Island converted to Pokémon Emerald style 2D RPG map",
            "conversion_date": "2024",
            "original_source": "Staten Island OpenStreetMap data",
            
            "map_dimensions": {
                "width_tiles": dimensions['tile_width'],
                "height_tiles": dimensions['tile_height'],
                "width_pixels": dimensions['pixel_width'],
                "height_pixels": dimensions['pixel_height']
            },
            
            "real_world": {
                "width_km": dimensions['real_width_km'],
                "height_km": dimensions['real_height_km'],
                "meters_per_tile": dimensions['meters_per_tile']
            },
            
            "tile_specifications": {
                "tile_size_pixels": self.tile_pixel_size,
                "tileset_file": "pokemon_tileset.png",
                "tilemap_file": "staten_island_pokemon.tmx"
            },
            
            "terrain_types": {
                "0": {"name": "ocean", "color": "#1E3A8A", "walkable": False},
                "1": {"name": "water", "color": "#3B82F6", "walkable": False},
                "2": {"name": "land", "color": "#84CC16", "walkable": True},
                "3": {"name": "forest", "color": "#16A34A", "walkable": True},
                "4": {"name": "mountain", "color": "#A3A3A3", "walkable": True},
                "5": {"name": "road", "color": "#6B7280", "walkable": True},
                "6": {"name": "building", "color": "#DC2626", "walkable": False},
                "7": {"name": "beach", "color": "#FEF3C7", "walkable": True}
            },
            
            "conversion_info": {
                "original_cell_size_meters": self.original_cell_size,
                "scaling_ratio": f"{self.scaling_ratio}:1",
                "original_dimensions": [self.metadata['grid_size'][0], self.metadata['grid_size'][1]],
                "terrain_mapping": terrain_mapping
            },
            
            "game_engine_compatibility": {
                "tiled_map_editor": "TMX format supported",
                "godot": "Import TMX file directly",
                "unity": "Use TMX importer package",
                "gamemaker": "Import tileset and use CSV layer data",
                "construct": "Import tileset PNG and TMX"
            }
        }
        
        return metadata

def main():
    """Main conversion function"""
    
    print("🎮 STATEN ISLAND → POKÉMON EMERALD STYLE CONVERTER")
    print("=" * 60)
    
    # Initialize converter
    converter = PokemonStyleConverter()
    
    # Calculate scaling
    dimensions = converter.calculate_new_dimensions()
    print(f"📊 New map dimensions: {dimensions['tile_width']} × {dimensions['tile_height']} tiles")
    print(f"🖼️  Pixel dimensions: {dimensions['pixel_width']} × {dimensions['pixel_height']} px")
    print(f"🌍 Real world coverage: {dimensions['real_width_km']:.1f} × {dimensions['real_height_km']:.1f} km")
    
    # Create output directory
    output_dir = Path('game_ready_map')
    output_dir.mkdir(exist_ok=True)
    print(f"📁 Output directory: {output_dir}")
    
    # Load and resample original map
    resampled_grid, new_dims = converter.load_and_resample_map()
    
    # Create terrain mapping
    terrain_mapping = converter.convert_terrain_to_pokemon_tiles()
    
    # Generate Pokémon-style tileset
    tileset, terrain_info = converter.create_pokemon_tileset()
    tileset_path = output_dir / 'pokemon_tileset.png'
    tileset.save(tileset_path)
    print(f"✅ Tileset saved: {tileset_path}")
    
    # Create map image
    map_image = converter.create_pokemon_map_image(resampled_grid, terrain_mapping)
    map_path = output_dir / 'staten_island_pokemon_preview.png'
    map_image.save(map_path)
    print(f"✅ Map preview saved: {map_path}")
    
    # Create TMX tilemap
    tmx_content = converter.create_tmx_tilemap(resampled_grid, terrain_mapping, new_dims)
    tmx_path = output_dir / 'staten_island_pokemon.tmx'
    with open(tmx_path, 'w') as f:
        f.write(tmx_content)
    print(f"✅ TMX tilemap saved: {tmx_path}")
    
    # Generate metadata
    metadata = converter.generate_metadata(new_dims, terrain_mapping)
    metadata_path = output_dir / 'pokemon_metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"✅ Metadata saved: {metadata_path}")
    
    # Save numpy grid for further processing
    grid_path = output_dir / 'pokemon_grid.npy'
    np.save(grid_path, resampled_grid)
    print(f"✅ Grid data saved: {grid_path}")
    
    print("\n" + "=" * 60)
    print("🎉 CONVERSION COMPLETE!")
    print(f"📁 All files saved to: {output_dir}")
    print(f"🎮 Map size: {new_dims['tile_width']} × {new_dims['tile_height']} tiles")
    print(f"🖼️  Preview image: {map_path}")
    print(f"🗺️  TMX file: {tmx_path}")
    print(f"🎨 Tileset: {tileset_path}")
    
    return output_dir, new_dims

if __name__ == "__main__":
    main()