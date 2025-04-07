import os
import json
from shapely import wkt
import geopandas as gpd
from math import sqrt
import numpy as np

def save_filenames_to_json(filenames, json_file, category='filenames'):
    """
    Save a list of filenames into a structured JSON file under a specified category.

    Parameters:
        filenames (list): List of filenames to save.
        json_file (str): Path to the JSON file.
        category (str): The category under which to store the filenames (default: 'filenames').
    """
    # Load existing JSON if it exists, otherwise start fresh
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            existing_data = json.load(f)
    else:
        existing_data = {}

    # Ensure the category exists in the JSON structure
    if category not in existing_data:
        existing_data[category] = []

    # Append new filenames if they're not already in the list
    for file in filenames:
        if file not in existing_data[category]:
            existing_data[category].append(file)

    # Write updated JSON back to disk
    with open(json_file, 'w') as f:
        json.dump(existing_data, f, indent=4)

    print(f"Filenames saved to {json_file} under '{category}'")

def square_bounds(lat, lon, distance=150000 / sqrt(2)):

    gs = gpd.GeoSeries(wkt.loads(f'POINT ({lon} {lat})'), crs='EPSG:4326')
    gdf = gs.to_crs('EPSG:3857')
    buffered = gdf.buffer(distance=distance, cap_style=3)
    buffered_geo = buffered.to_crs('EPSG:4326')
    bounds = buffered_geo.bounds.iloc[0]
    min_lon, min_lat, max_lon, max_lat = bounds['minx'], bounds['miny'], bounds['maxx'], bounds['maxy']

    return min_lon, max_lon, min_lat, max_lat

def weighted_avg(da, weights):
    weighted_sum = (da * weights).sum(dim='depth')
    total_weights = weights.sum(dim='depth')
    return weighted_sum / total_weights