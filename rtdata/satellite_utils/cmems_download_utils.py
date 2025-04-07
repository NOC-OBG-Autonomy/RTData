import os
import json
from shapely import wkt
import geopandas as gpd
from math import sqrt
import numpy as np

def save_filenames_to_json(filenames, json_file):
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    existing_data.extend(filenames)

    with open(json_file, 'w') as f:
        json.dump(existing_data, f, indent=4)
    print(f"Filenames saved to {json_file}")

    with open(json_file, 'w') as f:
        json.dump(existing_data, f, indent=4)

def square_bounds(lat, lon, distance=150000 / sqrt(2)):

    gs = gpd.GeoSeries(wkt.loads(f'POINT ({lon} {lat})'), crs='EPSG:4326')
    gdf = gs.to_crs('EPSG:3857')
    buffered = gdf.buffer(distance=distance, cap_style=3)
    buffered_geo = buffered.to_crs('EPSG:4326')
    bounds = buffered_geo.bounds.iloc[0]
    min_lon, min_lat, max_lon, max_lat = bounds['minx'], bounds['miny'], bounds['maxx'], bounds['maxy']

    return min_lon, max_lon, min_lat, max_lat
