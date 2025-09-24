# make_map.py
from pathlib import Path
import folium
import geopandas as gpd

# --- 1) Load data ------------------------------------------------------------
DATA_DIR = Path("staten_island_osm")

# Use light-weight layers where possible (points instead of big polys)
bld_centroids = gpd.read_file(DATA_DIR / "building_centroids.geojson")   # points
shops         = gpd.read_file(DATA_DIR / "shop_centroids.geojson")       # points
roads         = gpd.read_file(DATA_DIR / "roads.geojson")                # lines
green         = gpd.read_file(DATA_DIR / "landuse_green.geojson")        # polys
water         = gpd.read_file(DATA_DIR / "water.geojson")                # polys

# --- 2) Ensure WGS84 (EPSG:4326) for web maps --------------------------------
for gdf in (bld_centroids, shops, roads, green, water):
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf.to_crs(4326, inplace=True)

# --- 3) Compute a decent map center ------------------------------------------
# Use total bounds of roads (usually covers the whole place neatly)
minx, miny, maxx, maxy = roads.total_bounds
center_lat = (miny + maxy) / 2
center_lon = (minx + maxx) / 2

m = folium.Map(location=[center_lat, center_lon], zoom_start=12, tiles="CartoDB positron")

# --- 4) Add layers (keep it performant) --------------------------------------
# Roads
folium.GeoJson(
    roads[["geometry"]],
    name="Roads",
    tooltip=None,
    style_function=lambda _: {"weight": 1}
).add_to(m)

# Parks/green
folium.GeoJson(
    green[["geometry"]],
    name="Parks & Green",
    style_function=lambda _: {"fillOpacity": 0.3, "weight": 0.6}
).add_to(m)

# Water
folium.GeoJson(
    water[["geometry"]],
    name="Water",
    style_function=lambda _: {"fillOpacity": 0.3, "weight": 0.6}
).add_to(m)

# Buildings (sample to avoid rendering 142k points)
bld_group = folium.FeatureGroup(name="Building Centroids (sample)")
# every Nth point — tweak step for speed vs detail (e.g., ::100 for faster)
for pt in bld_centroids.geometry.iloc[::50]:
    folium.CircleMarker(
        location=[pt.y, pt.x],
        radius=1,
        fill=True,
        fill_opacity=0.7,
        opacity=0.7
    ).add_to(bld_group)
bld_group.add_to(m)

# Shops (small points, try to show names if present)
shop_group = folium.FeatureGroup(name="Shops")
name_cols = [c for c in shops.columns if c.lower() in {"name", "shop", "brand"}]
for _, row in shops.iterrows():
    lat, lon = row.geometry.y, row.geometry.x
    popup_text = ""
    if name_cols:
        # build a simple popup with whatever name-like field exists
        popup_text = "<br>".join(f"<b>{c}:</b> {row.get(c, '')}" for c in name_cols if row.get(c))
    folium.CircleMarker(
        location=[lat, lon],
        radius=2,
        fill=True,
        fill_opacity=0.9,
        opacity=0.9,
        popup=popup_text or None,
    ).add_to(shop_group)
shop_group.add_to(m)

folium.LayerControl(collapsed=False).add_to(m)

# --- 5) Save ------------------------------------------------------------------
out_file = Path("staten_island_map.html")
m.save(str(out_file))
print(f"✅ Wrote {out_file.resolve()}")
