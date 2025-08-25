import os
import time
import warnings
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import osmnx as ox

warnings.filterwarnings("ignore")

# ---------------- Settings ----------------
PLACE_NAME = "Staten Island, New York, USA"
OUTDIR = "staten_island_osm"
os.makedirs(OUTDIR, exist_ok=True)

# OSMnx Overpass hygiene
ox.settings.timeout = 600              # generous timeout for large queries
ox.settings.overpass_rate_limit = True # auto backoff on rate-limit
ox.settings.use_cache = True
ox.settings.log_console = True

# Helper to write GeoJSON if not empty
def save_gdf(gdf: gpd.GeoDataFrame, path: str):
    if gdf is None or gdf.empty:
        print(f"[skip] {path} (empty)")
        return
    # Ensure WGS84 for GeoJSON
    try:
        gdf = gdf.to_crs(4326)
    except Exception:
        pass
    gdf.to_file(path, driver="GeoJSON")
    print(f"[ok]   wrote {path}  ({len(gdf)} features)")

print(f"[info] Geocoding boundary for: {PLACE_NAME}")
boundary = ox.geocode_to_gdf(PLACE_NAME)  # MultiPolygon boundary
poly = boundary.geometry.iloc[0]
print("[ok]   boundary acquired")

# --------------- BUILDINGS ---------------
# Pull all OSM 'building=*' features overlapping the polygon
print("[info] downloading buildings …")
buildings = ox.features_from_polygon(poly, tags={"building": True})
# Keep only geometries (drop rows with null geometry)
buildings = buildings[~buildings.geometry.is_empty & buildings.geometry.notnull()]
save_gdf(buildings, os.path.join(OUTDIR, "buildings.geojson"))

# Centroids for procedural spawns (houses)
print("[info] computing building centroids …")
buildings_cent = buildings.copy()
buildings_cent["geometry"] = buildings_cent.geometry.centroid
# Minimal columns for spawns
buildings_cent = buildings_cent[["geometry", "building"]].rename(columns={"building":"kind"})
save_gdf(buildings_cent, os.path.join(OUTDIR, "building_centroids.geojson"))

# --------------- SHOPS / COMMERCIAL POIs ---------------
# OSM shop=* (nodes/ways/relations)
print("[info] downloading shops …")
shops = ox.features_from_polygon(poly, tags={"shop": True})
shops = shops[~shops.geometry.is_empty & shops.geometry.notnull()]
save_gdf(shops, os.path.join(OUTDIR, "shops.geojson"))

print("[info] computing shop centroids …")
shops_cent = shops.copy()
shops_cent["geometry"] = shops_cent.geometry.centroid
shops_cent = shops_cent[["geometry", "shop"]].rename(columns={"shop":"kind"})
save_gdf(shops_cent, os.path.join(OUTDIR, "shop_centroids.geojson"))

# --------------- ROADS / HIGHWAYS ---------------
# Grab a rich but reasonable set of roads
print("[info] downloading roads graph …")
G = ox.graph_from_polygon(poly, network_type="drive", simplify=True)

# In OSMnx 2.x this returns just the edges GeoDataFrame (not a tuple)
edges = ox.graph_to_gdfs(G, nodes=False, edges=True)

keep_cols = [c for c in ("highway","name","oneway","maxspeed") if c in edges.columns]
roads = edges[keep_cols + ["geometry"]] if keep_cols else edges[["geometry"]]

save_gdf(roads, os.path.join(OUTDIR, "roads.geojson"))


# --------------- LANDUSE / GREEN ---------------
# Parks, woods, meadows/grass; common urban landuse categories
print("[info] downloading landuse/green …")
land_tags = {
    "leisure": ["park"],
    "natural": ["wood", "scrub", "grassland"],
    "landuse": ["residential", "commercial", "retail", "industrial", "meadow", "grass"]
}
landuse = ox.features_from_polygon(poly, tags=land_tags)
landuse = landuse[~landuse.geometry.is_empty & landuse.geometry.notnull()]
save_gdf(landuse, os.path.join(OUTDIR, "landuse_green.geojson"))

# --------------- WATER ---------------
print("[info] downloading water features …")
water_tags = {
    "natural": ["water", "bay", "strait"],
    "waterway": True,          # rivers, streams, etc.
    "water": True              # lakes/ponds tagged by 'water=*'
}
water = ox.features_from_polygon(poly, tags=water_tags)
water = water[~water.geometry.is_empty & water.geometry.notnull()]
save_gdf(water, os.path.join(OUTDIR, "water.geojson"))

print("\n✅ Done. Files written to:", OUTDIR)
print("   - buildings.geojson")
print("   - building_centroids.geojson  (use for house spawns)")
print("   - shops.geojson")
print("   - shop_centroids.geojson      (use for store spawns)")
print("   - roads.geojson")
print("   - landuse_green.geojson")
print("   - water.geojson")
print("\nNext step: bring these into Godot/Unity and swap polygons/points for your pixel tiles + prefabs.")
