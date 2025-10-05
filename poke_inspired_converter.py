#!/usr/bin/env python3
"""
🎮 Poke-Inspired 2D Map Converter
=================================

Converts Staten Island map data into high-quality 2D RPG tiles with classic
game visual style for open-world adventures.

Features:
- Professional 16×16 pixel tiles with texture and detail
- Character-to-tile scale perfect for 2D RPG gameplay
- Multi-tile building structures for authentic city feel
- Terrain variations and visual interest
- Classic RPG color palette and visual patterns
"""

import json
import numpy as np
from PIL import Image, ImageDraw
import random
import os
from pathlib import Path

class PokeInspired2DConverter:
    def __init__(self):
        # Classic 2D RPG colors (inspired by retro games)
        self.colors = {
            'grass_base': '#7CB518',      # Main grass color
            'grass_dark': '#5A9010',      # Dark grass accents
            'grass_light': '#94D82D',     # Light grass highlights
            'water_base': '#4A90E2',      # Water base
            'water_light': '#6BB6FF',     # Water highlights
            'ocean_base': '#1E3A8A',      # Deep ocean
            'sand_base': '#F4E4BC',       # Beach sand
            'road_base': '#8B8B8B',       # Road gray
            'road_line': '#FFFFFF',       # Road markings
            'roof_red': '#DC143C',        # House roof red
            'wall_beige': '#F5DEB3',      # House walls
            'door_brown': '#8B4513',      # Doors
            'window_blue': '#87CEEB',     # Windows
            'tree_trunk': '#8B4513',      # Tree trunks
            'tree_leaves': '#228B22',     # Tree leaves
            'pokecenter_red': '#FF0000',  # Pokémon Center roof
            'pokecenter_white': '#FFFFFF', # Pokémon Center walls
            'shop_blue': '#0066CC',       # Shop roof blue
            'path_tan': '#D2B48C'         # Dirt paths
        }
        
        self.tile_size = 16  # 16×16 pixels (classic 2D RPG standard)
        
    def create_2d_rpg_tileset(self):
        """Create comprehensive 2D RPG-style tileset"""
        
        tiles = {}
        
        # Grass variations (most common terrain)
        tiles['grass_01'] = self.create_grass_tile('basic')
        tiles['grass_02'] = self.create_grass_tile('flowers')
        tiles['grass_03'] = self.create_grass_tile('dark')
        tiles['grass_edge_water'] = self.create_grass_tile('basic')  # Simplified for now
        tiles['grass_edge_sand'] = self.create_grass_tile('basic')   # Simplified for now
        
        # Water tiles
        tiles['water_01'] = self.create_water_tile('calm')
        tiles['water_02'] = self.create_water_tile('sparkles')
        tiles['ocean_01'] = self.create_ocean_tile()
        
        # Sand/Beach tiles
        tiles['sand_01'] = self.create_sand_tile()
        tiles['sand_water_edge'] = self.create_sand_tile()  # Simplified for now
        
        # Road/Path tiles
        tiles['road_horizontal'] = self.create_road_tile('horizontal')
        tiles['road_vertical'] = self.create_road_tile('vertical')
        tiles['road_intersection'] = self.create_road_tile('intersection')
        tiles['path_dirt'] = self.create_path_tile()
        
        # Building tiles (multi-tile structures)
        house_tiles = self.create_house_structure()
        tiles.update(house_tiles)
        
        landmark_tiles = self.create_landmark_structure()
        tiles.update(landmark_tiles)
        
        shop_tiles = self.create_shop_structure()
        tiles.update(shop_tiles)
        
        # Nature tiles  
        tiles['tree_01'] = self.create_tree_tile()
        tiles['bush_01'] = self.create_grass_tile('basic')    # Simplified for now
        tiles['flowers_01'] = self.create_grass_tile('flowers')  # Simplified for now
        
        return tiles
    
    def create_grass_tile(self, variant='basic'):
        """Create detailed grass tiles with classic 2D RPG patterns"""
        tile = Image.new('RGB', (16, 16), self.colors['grass_base'])
        draw = ImageDraw.Draw(tile)
        
        if variant == 'basic':
            # Basic grass with texture dots
            for _ in range(12):
                x, y = random.randint(0, 15), random.randint(0, 15)
                draw.point([x, y], fill=self.colors['grass_dark'])
            
            for _ in range(6):
                x, y = random.randint(0, 15), random.randint(0, 15)
                draw.point([x, y], fill=self.colors['grass_light'])
        
        elif variant == 'flowers':
            # Grass with small flower patches
            self._add_grass_texture(draw)
            
            # Add small flowers (2×2 pixels)
            flower_colors = ['#FF69B4', '#FFB6C1', '#FF1493']
            for _ in range(3):
                x, y = random.randint(0, 14), random.randint(0, 14)
                color = random.choice(flower_colors)
                draw.rectangle([x, y, x+1, y+1], fill=color)
        
        elif variant == 'dark':
            # Darker grass variation
            tile = Image.new('RGB', (16, 16), self.colors['grass_dark'])
            draw = ImageDraw.Draw(tile)
            self._add_grass_texture(draw)
        
        return tile
    
    def create_water_tile(self, variant='calm'):
        """Create water tiles with sparkles and movement"""
        tile = Image.new('RGB', (16, 16), self.colors['water_base'])
        draw = ImageDraw.Draw(tile)
        
        if variant == 'calm':
            # Subtle water texture
            for _ in range(8):
                x, y = random.randint(0, 15), random.randint(0, 15)
                draw.point([x, y], fill=self.colors['water_light'])
        
        elif variant == 'sparkles':
            # Water with sparkles (classic RPG style)
            for _ in range(4):
                x, y = random.randint(2, 13), random.randint(2, 13)
                # Draw + shaped sparkle
                draw.point([x, y], fill='#FFFFFF')
                draw.point([x-1, y], fill='#FFFFFF')
                draw.point([x+1, y], fill='#FFFFFF')
                draw.point([x, y-1], fill='#FFFFFF')
                draw.point([x, y+1], fill='#FFFFFF')
        
        return tile
    
    def create_ocean_tile(self):
        """Create deep ocean tile"""
        tile = Image.new('RGB', (16, 16), self.colors['ocean_base'])
        draw = ImageDraw.Draw(tile)
        
        # Add subtle ocean texture
        for _ in range(6):
            x, y = random.randint(0, 15), random.randint(0, 15)
            draw.point([x, y], fill='#2563EB')  # Slightly lighter blue
        
        return tile
    
    def create_sand_tile(self):
        """Create sand/beach tile"""
        tile = Image.new('RGB', (16, 16), self.colors['sand_base'])
        draw = ImageDraw.Draw(tile)
        
        # Add sand texture
        for _ in range(8):
            x, y = random.randint(0, 15), random.randint(0, 15)
            draw.point([x, y], fill='#E6D3A3')  # Darker sand
        
        for _ in range(4):
            x, y = random.randint(0, 15), random.randint(0, 15)
            draw.point([x, y], fill='#F7F3D0')  # Lighter sand
        
        return tile
    
    def create_path_tile(self):
        """Create dirt path tile"""
        tile = Image.new('RGB', (16, 16), self.colors['path_tan'])
        draw = ImageDraw.Draw(tile)
        
        # Add path texture
        for _ in range(10):
            x, y = random.randint(0, 15), random.randint(0, 15)
            draw.point([x, y], fill='#C19A6B')  # Darker tan
        
        return tile
    
    def create_tree_tile(self):
        """Create tree tile"""
        tile = Image.new('RGB', (16, 16), self.colors['grass_base'])
        draw = ImageDraw.Draw(tile)
        
        # Add grass background first
        self._add_grass_texture(draw)
        
        # Draw tree trunk
        draw.rectangle([7, 10, 8, 15], fill=self.colors['tree_trunk'])
        
        # Draw leaves (circular)
        draw.ellipse([4, 4, 11, 11], fill=self.colors['tree_leaves'])
        
        # Add leaf highlights
        draw.point([6, 6], fill='#32CD32')  # Light green
        draw.point([9, 8], fill='#32CD32')
        
        return tile
    
    def create_road_tile(self, direction='horizontal'):
        """Create road tiles with proper markings"""
        tile = Image.new('RGB', (16, 16), self.colors['road_base'])
        draw = ImageDraw.Draw(tile)
        
        if direction == 'horizontal':
            # Horizontal road with center line
            draw.line([0, 7, 15, 7], fill=self.colors['road_line'])
            draw.line([0, 8, 15, 8], fill=self.colors['road_line'])
        
        elif direction == 'vertical':
            # Vertical road with center line
            draw.line([7, 0, 7, 15], fill=self.colors['road_line'])
            draw.line([8, 0, 8, 15], fill=self.colors['road_line'])
        
        elif direction == 'intersection':
            # Intersection (no center lines)
            pass
        
        return tile
    
    def create_house_structure(self):
        """Create multi-tile house structure (classic 2D RPG style)"""
        house_tiles = {}
        
        # 3×2 house structure (typical 2D RPG house)
        # Row 1: Roof tiles
        house_tiles['house_roof_left'] = self._create_roof_tile('left')
        house_tiles['house_roof_center'] = self._create_roof_tile('center')  
        house_tiles['house_roof_right'] = self._create_roof_tile('right')
        
        # Row 2: Wall tiles
        house_tiles['house_wall_left'] = self._create_wall_tile('left')
        house_tiles['house_wall_door'] = self._create_wall_tile('door')
        house_tiles['house_wall_right'] = self._create_wall_tile('right')
        
        return house_tiles
    
    def create_landmark_structure(self):
        """Create landmark building structure (town hall, community center)"""
        landmark_tiles = {}
        
        # 4×3 landmark building (larger public building)
        # Top row - roof with civic symbol
        landmark_tiles['landmark_roof_left'] = self._create_landmark_roof('left')
        landmark_tiles['landmark_roof_sign'] = self._create_landmark_roof('sign')  # Civic symbol
        landmark_tiles['landmark_roof_center'] = self._create_landmark_roof('center')
        landmark_tiles['landmark_roof_right'] = self._create_landmark_roof('right')
        
        # Middle row - walls
        landmark_tiles['landmark_wall_left'] = self._create_landmark_wall('left')
        landmark_tiles['landmark_wall_center1'] = self._create_landmark_wall('center')
        landmark_tiles['landmark_wall_center2'] = self._create_landmark_wall('center')
        landmark_tiles['landmark_wall_right'] = self._create_landmark_wall('right')
        
        # Bottom row - entrance
        landmark_tiles['landmark_entrance_left'] = self._create_landmark_entrance('left')
        landmark_tiles['landmark_entrance_door'] = self._create_landmark_entrance('door')
        landmark_tiles['landmark_entrance_center'] = self._create_landmark_entrance('center')
        landmark_tiles['landmark_entrance_right'] = self._create_landmark_entrance('right')
        
        return landmark_tiles
    
    def create_shop_structure(self):
        """Create shop building structure"""
        shop_tiles = {}
        
        # Simple 2×2 shop structure
        shop_tiles['shop_roof_left'] = self._create_shop_roof('left')
        shop_tiles['shop_roof_right'] = self._create_shop_roof('right')
        shop_tiles['shop_wall_left'] = self._create_shop_wall('left')
        shop_tiles['shop_wall_right'] = self._create_shop_wall('right')
        
        return shop_tiles
    
    def _create_roof_tile(self, position):
        """Create house roof tile sections"""
        tile = Image.new('RGB', (16, 16), self.colors['roof_red'])
        draw = ImageDraw.Draw(tile)
        
        # Add roof tile pattern
        for y in range(0, 16, 3):
            draw.line([0, y, 15, y], fill='#B91C1C')  # Darker red lines
        
        if position == 'left':
            # Left edge highlight
            draw.line([0, 0, 0, 15], fill='#FF6B6B')
        elif position == 'right':
            # Right edge shadow
            draw.line([15, 0, 15, 15], fill='#8B0000')
        
        return tile
    
    def _create_wall_tile(self, position):
        """Create house wall tile sections"""
        tile = Image.new('RGB', (16, 16), self.colors['wall_beige'])
        draw = ImageDraw.Draw(tile)
        
        if position == 'door':
            # Door in center
            door_rect = [6, 4, 9, 15]
            draw.rectangle(door_rect, fill=self.colors['door_brown'])
            # Door handle
            draw.point([8, 10], fill='#FFD700')
        else:
            # Window
            window_rect = [6, 6, 9, 9]
            draw.rectangle(window_rect, fill=self.colors['window_blue'])
            # Window frame
            draw.rectangle([5, 5, 10, 10], outline='#654321')
        
        return tile
    
    def _create_landmark_roof(self, position):
        """Create landmark building roof tiles"""
        tile = Image.new('RGB', (16, 16), self.colors['pokecenter_red'])
        draw = ImageDraw.Draw(tile)
        
        if position == 'sign':
            # Civic symbol tile (star or shield)
            center = (8, 8)
            # Draw a star symbol
            points = [(8, 4), (9, 7), (12, 7), (10, 9), (11, 12), (8, 10), (5, 12), (6, 9), (4, 7), (7, 7)]
            draw.polygon(points, fill='#FFD700')  # Gold star
            draw.polygon(points, outline='#000000')  # Black outline
        
        return tile
    
    def _create_landmark_wall(self, position):
        """Create landmark building wall tiles"""
        tile = Image.new('RGB', (16, 16), self.colors['pokecenter_white'])
        draw = ImageDraw.Draw(tile)
        
        if position != 'center':
            # Add window
            window_rect = [6, 6, 9, 9]
            draw.rectangle(window_rect, fill=self.colors['window_blue'])
            draw.rectangle([5, 5, 10, 10], outline='#654321')
        
        return tile
    
    def _create_landmark_entrance(self, position):
        """Create landmark building entrance tiles"""
        tile = Image.new('RGB', (16, 16), self.colors['pokecenter_white'])
        draw = ImageDraw.Draw(tile)
        
        if position == 'door':
            # Automatic door
            door_rect = [4, 8, 11, 15]
            draw.rectangle(door_rect, fill='#4169E1')  # Blue door
        
        return tile
    
    def _create_shop_roof(self, position):
        """Create shop roof tiles"""
        tile = Image.new('RGB', (16, 16), self.colors['shop_blue'])
        draw = ImageDraw.Draw(tile)
        
        # Add roof pattern
        for y in range(0, 16, 3):
            draw.line([0, y, 15, y], fill='#003D82')  # Darker blue
        
        return tile
    
    def _create_shop_wall(self, position):
        """Create shop wall tiles"""
        tile = Image.new('RGB', (16, 16), '#E6E6E6')  # Light gray walls
        draw = ImageDraw.Draw(tile)
        
        if position == 'left':
            # Shop sign
            sign_rect = [2, 6, 13, 10]
            draw.rectangle(sign_rect, fill='#FFD700')  # Yellow sign
            draw.rectangle(sign_rect, outline='#000000')
        else:
            # Window
            window_rect = [6, 6, 9, 9] 
            draw.rectangle(window_rect, fill=self.colors['window_blue'])
        
        return tile
    
    def convert_staten_island_data(self):
        """Convert Staten Island data to Pokémon-style tile map"""
        
        print("🏝️ Loading Staten Island data...")
        
        # Load your existing grid data
        try:
            grid_data = np.load('game_tiles/grid_uint8.npy')
            print(f"✅ Loaded grid: {grid_data.shape}")
        except:
            print("⚠️  Grid file not found, creating sample data")
            # Create sample Staten Island-like data for testing
            grid_data = self._create_sample_data()
        
        # Convert terrain IDs to 2D RPG tile names
        rpg_grid = self._convert_terrain_to_2d_rpg(grid_data)
        
        # Generate building structures
        rpg_grid = self._add_building_structures(rpg_grid, grid_data)
        
        return rpg_grid
    
    def _add_building_structures(self, rpg_grid, original_grid):
        """Add multi-tile building structures"""
        # For now, return the grid as-is
        # This would implement logic to replace single building tiles
        # with multi-tile structures
        return rpg_grid
    
    def _create_sample_data(self):
        """Create sample Staten Island-like data for testing"""
        # Create a 100×100 sample grid
        height, width = 100, 100
        grid = np.zeros((height, width), dtype=np.uint8)
        
        # Create Staten Island-like shape
        center_x, center_y = width // 2, height // 2
        
        for y in range(height):
            for x in range(width):
                # Distance from center for island shape
                dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
                
                if dist < 30:  # Inside island
                    if np.random.random() > 0.8:
                        grid[y, x] = 4  # Buildings
                    elif np.random.random() > 0.7:
                        grid[y, x] = 2  # Parks
                    elif np.random.random() > 0.6:
                        grid[y, x] = 1  # Roads
                    else:
                        grid[y, x] = 6  # Land
                elif dist < 35:  # Coastline
                    grid[y, x] = 3 if np.random.random() > 0.5 else 6  # Water or land
                else:
                    grid[y, x] = 0  # Ocean
        
        return grid
    
    def _convert_terrain_to_2d_rpg(self, grid_data):
        """Convert terrain IDs to 2D RPG tile names"""
        
        height, width = grid_data.shape
        rpg_grid = np.empty((height, width), dtype=object)
        
        terrain_mapping = {
            0: 'ocean_01',      # Ocean
            1: 'road_horizontal', # Roads (will be improved with direction detection)
            2: 'grass_02',      # Parks/Green (grass with flowers)
            3: 'water_01',      # Water bodies
            4: 'house_roof_center', # Buildings (will be structured)
            5: 'shop_roof_center',  # Retail (shop structures)
            6: 'grass_01'       # General land
        }
        
        for y in range(height):
            for x in range(width):
                terrain_id = grid_data[y, x]
                
                # Smart tile selection based on neighbors
                tile_name = self._get_contextual_tile(grid_data, x, y, terrain_id, terrain_mapping)
                rpg_grid[y, x] = tile_name
        
        return rpg_grid
    
    def _get_contextual_tile(self, grid_data, x, y, terrain_id, mapping):
        """Get appropriate tile based on surrounding context"""
        
        base_tile = mapping.get(terrain_id, 'grass_01')
        
        # Get neighbors for context
        neighbors = self._get_neighbors(grid_data, x, y)
        
        # Special cases based on terrain type and neighbors
        if terrain_id == 6:  # Land - vary grass types
            # Check if near water for edge tiles
            if any(n in [0, 3] for n in neighbors):  # Near ocean or water
                return random.choice(['grass_edge_water', 'sand_01'])
            else:
                return random.choice(['grass_01', 'grass_02', 'grass_03'])
        
        elif terrain_id == 1:  # Roads - determine direction
            has_horizontal = neighbors['left'] == 1 or neighbors['right'] == 1
            has_vertical = neighbors['up'] == 1 or neighbors['down'] == 1
            
            if has_horizontal and has_vertical:
                return 'road_intersection'
            elif has_horizontal:
                return 'road_horizontal'
            else:
                return 'road_vertical'
        
        return base_tile
    
    def _get_neighbors(self, grid_data, x, y):
        """Get neighboring terrain IDs"""
        height, width = grid_data.shape
        
        neighbors = {
            'up': grid_data[max(0, y-1), x],
            'down': grid_data[min(height-1, y+1), x],
            'left': grid_data[y, max(0, x-1)],
            'right': grid_data[y, min(width-1, x+1)]
        }
        
        return neighbors
    
    def _export_tmx_map(self, pokemon_grid, output_path):
        """Export as TMX file format"""
        print("📄 Exporting TMX map file...")
        
        # Simple TMX export - would need full implementation
        tmx_content = '''<?xml version="1.0" encoding="UTF-8"?>
<map version="1.0" orientation="orthogonal" width="100" height="100" tilewidth="16" tileheight="16">
  <tileset firstgid="1" name="pokemon_tileset" tilewidth="16" tileheight="16">
    <image source="enhanced_pokemon_tileset.png" width="128" height="256"/>
  </tileset>
  <layer name="Terrain" width="100" height="100">
    <data encoding="csv">
'''
        
        # Add simplified tile data
        for y in range(min(100, pokemon_grid.shape[0])):
            row_data = []
            for x in range(min(100, pokemon_grid.shape[1])):
                row_data.append('1')  # Simplified - all grass for now
            tmx_content += ','.join(row_data) + (',' if y < 99 else '') + '\n'
        
        tmx_content += '''    </data>
  </layer>
</map>'''
        
        tmx_path = output_path / 'enhanced_staten_island.tmx'
        with open(tmx_path, 'w') as f:
            f.write(tmx_content)
        
        print(f"✅ TMX file exported: {tmx_path}")
    
    def _create_enhanced_metadata(self, output_path):
        """Create metadata for the enhanced map"""
        
        metadata = {
            "name": "Enhanced Pokémon-Style Staten Island",
            "version": "2.0-enhanced-pokemon",
            "description": "Staten Island with authentic Pokémon Emerald-style 16×16 tiles",
            "tile_specifications": {
                "tile_size_pixels": 16,
                "meters_per_tile": 1.0,
                "character_height_tiles": 1,
                "viewport_recommended": "240×160 or 320×240"
            },
            "visual_improvements": {
                "authentic_colors": "Pokémon Emerald color palette",
                "detailed_tiles": "Texture patterns and visual interest",
                "building_structures": "Multi-tile buildings like Pokémon games",
                "character_scale": "16×16 pixel sprites (1 tile tall)"
            },
            "engine_recommendations": {
                "unity": "Use PixelPerfectCamera with 16 PPU",
                "godot": "Use TileMap with 16×16 cell size",
                "gamemaker": "Set room speed to 60, use sprite scaling",
                "construct": "Use Tilemap object with 16×16 tiles"
            }
        }
        
        metadata_path = output_path / 'enhanced_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Enhanced metadata saved: {metadata_path}")
    
    def export_2d_rpg_map(self, output_dir='poke_inspired_2d_map'):
        """Export the enhanced 2D RPG-style assets"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        print(f"🎨 Creating enhanced 2D RPG-style tileset...")
        
        # Create tileset
        tileset_dict = self.create_2d_rpg_tileset()
        
        # Save individual tile images
        tiles_dir = output_path / 'tiles'
        tiles_dir.mkdir(exist_ok=True)
        
        for tile_name, tile_image in tileset_dict.items():
            tile_path = tiles_dir / f"{tile_name}.png"
            tile_image.save(tile_path)
        
        print(f"✅ Saved {len(tileset_dict)} individual tiles")
        
        # Create combined tileset image (for game engines)
        self._create_combined_tileset(tileset_dict, output_path)
        
        # Convert Staten Island data
        print("🗺️ Converting Staten Island data...")
        rpg_grid = self.convert_staten_island_data()
        
        # Export as TMX
        self._export_tmx_map(rpg_grid, output_path)
        
        # Create metadata
        self._create_enhanced_metadata(output_path)
        
        print(f"🎯 Enhanced 2D RPG-style map exported to: {output_path}")
        
        return output_path
    
    def _create_combined_tileset(self, tileset_dict, output_path):
        """Create a single tileset image for game engines"""
        
        tiles_per_row = 8
        tile_count = len(tileset_dict)
        rows_needed = (tile_count + tiles_per_row - 1) // tiles_per_row
        
        tileset_width = tiles_per_row * self.tile_size
        tileset_height = rows_needed * self.tile_size
        
        combined_tileset = Image.new('RGB', (tileset_width, tileset_height), (255, 0, 255))  # Magenta background
        
        tile_list = list(tileset_dict.items())
        
        for i, (tile_name, tile_image) in enumerate(tile_list):
            row = i // tiles_per_row
            col = i % tiles_per_row
            
            x = col * self.tile_size
            y = row * self.tile_size
            
            combined_tileset.paste(tile_image, (x, y))
        
        tileset_path = output_path / 'enhanced_pokemon_tileset.png'
        combined_tileset.save(tileset_path)
        
        print(f"✅ Combined tileset saved: {tileset_path}")
        
        # Save tile mapping
        tile_mapping = {name: i for i, (name, _) in enumerate(tile_list)}
        mapping_path = output_path / 'tile_mapping.json'
        with open(mapping_path, 'w') as f:
            json.dump(tile_mapping, f, indent=2)
    
    def _add_grass_texture(self, draw):
        """Add grass texture to tiles"""
        for _ in range(10):
            x, y = random.randint(0, 15), random.randint(0, 15)
            draw.point([x, y], fill=self.colors['grass_dark'])
        
        for _ in range(5):
            x, y = random.randint(0, 15), random.randint(0, 15)
            draw.point([x, y], fill=self.colors['grass_light'])

def main():
    """Generate enhanced Pokémon-style Staten Island map"""
    
    print("🎮 ENHANCED POKÉMON STYLE CONVERTER")
    print("=" * 50)
    
    converter = EnhancedPokemonConverter()
    output_dir = converter.export_enhanced_tileset()
    
    print(f"\n🎉 SUCCESS!")
    print(f"📁 Enhanced assets: {output_dir}")
    print(f"🎨 Individual tiles: {output_dir}/tiles/")
    print(f"🖼️  Combined tileset: {output_dir}/enhanced_pokemon_tileset.png")
    print(f"📄 Tile mapping: {output_dir}/tile_mapping.json")
    
    print(f"\n🎮 NEXT STEPS:")
    print(f"1. Import {output_dir}/enhanced_pokemon_tileset.png into your game engine")
    print(f"2. Set sprite size to 16×16 pixels")
    print(f"3. Configure pixel-perfect camera (240×160 or 320×240 viewport)")
    print(f"4. Set character sprite to 16×16 pixels")
    print(f"5. Implement grid-based movement (1 tile = 1 meter)")
    
    return output_dir

if __name__ == "__main__":
    main()