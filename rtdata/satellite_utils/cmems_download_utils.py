import os
import json
from shapely import wkt
import geopandas as gpd
from math import sqrt
import numpy as np
import copernicusmarine as cpm
from pathlib import Path
import ast
from datetime import datetime, timedelta, time
import statistics

from rtdata import config
from rtdata.c2_api import api_interface as c2


def save_filenames_to_json(filenames, json_file, category='cmems_files'):
    """
    Save a list of filenames into a new JSON file, storing absolute file paths.

    Parameters:
        filenames (list): List of filenames to save.
        json_file (str): Path to the JSON file.
        category (str): The category under which to store the filenames (default: 'cmems_files').
    """
    # Prepare the data structure to be saved
    data = {category: filenames}

    # Write the new JSON file (this will overwrite any existing file)
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Filenames saved to {json_file} under '{category}'")


def square_bounds(lat, lon, distance=500):

    dist = (distance*1000)/sqrt(2)
    gs = gpd.GeoSeries(wkt.loads(f'POINT ({lon} {lat})'), crs='EPSG:4326')
    gdf = gs.to_crs('EPSG:3857')
    buffered = gdf.buffer(distance=dist, cap_style=3)
    buffered_geo = buffered.to_crs('EPSG:4326')
    bounds = buffered_geo.bounds.iloc[0]
    min_lon, min_lat, max_lon, max_lat = bounds['minx'], bounds['miny'], bounds['maxx'], bounds['maxy']

    return min_lon, max_lon, min_lat, max_lat


def weighted_avg(da, weights):
    weighted_sum = (da * weights).sum(dim='depth')
    total_weights = weights.sum(dim='depth')
    return weighted_sum / total_weights


def cmems_data_download(daysprior=2,distance=500):
    """
    Download CMEMS data.
    
    Parameters:
        timedelta (int): Number of days prior to most recent product to download.
        distance (int): Diagonal distance from 
        
    Returns:
        json_file_details(list): (full_path, filename_base)
    """
    # Format time as YYYY-MM-DD"T"HH:MM:SS for Copernicus Marine Module
    current_day = datetime.combine(datetime.today().date(), time.min)
    end_timelabel = current_day.strftime("%Y%m%d")
    end_time = current_day.strftime("%Y-%m-%dT%H:%M:%S")
    start_day = current_day - timedelta(days=daysprior)
    start_timelabel = start_day.strftime("%Y%m%d")
    start_time = start_day.strftime("%Y-%m-%dT%H:%M:%S")

    ## Location and depths for spatial bounds on data download

    list_lon = []
    list_lat = []

    for unit in config.gliders_units:

        #Get the last position of the glider
        pos = c2.get_positions(config.token, "slocum", unit, test = False)
        lat, lon = c2.get_last_coordinates(pos)
        list_lon.append(lon)
        list_lat.append(lat)

    min_lon, max_lon, min_lat, max_lat = square_bounds(statistics.mean(list_lat),statistics.mean(list_lon),distance)

    min_depth = 0
    max_depth = 1000

    ## List of datasets to extract

    datasets_to_extract = [
        'cmems_obs-mob_glo_phy-cur_nrt_0.25deg_P1D-m',     # currents   (low res, high scope)
        'cmems_mod_glo_phy-cur_anfc_0.083deg_P1D-m']       # currents   (modelled product)

    filenames = []

    ## Download each dataset

    for dataset_to_extract in datasets_to_extract:
        # Dynamically set the output filename based on the dataset name
        if "_mod_" in dataset_to_extract:
            saved_netCDF_as = f"{start_timelabel}_{end_timelabel}_model_currents.nc"
            filepath = os.path.join(config.save_path, saved_netCDF_as)
        if "_obs-" in dataset_to_extract:
            saved_netCDF_as = f"{start_timelabel}_{end_timelabel}_observed_currents.nc"
            filepath = os.path.join(config.save_path, saved_netCDF_as)

        # Remove existing file if it exists to allow overwriting
        if os.path.exists(filepath):
            os.remove(filepath)

        # Perform the data subset operation
        cpm.subset(
            dataset_id=dataset_to_extract,
            minimum_longitude=min_lon,
            maximum_longitude=max_lon,
            minimum_latitude=min_lat,
            maximum_latitude=max_lat,
            start_datetime=start_time,
            end_datetime=end_time,
            minimum_depth=min_depth,
            maximum_depth=max_depth,
            output_filename=saved_netCDF_as,
            output_directory=config.save_path,
            username=config.cpmusername,
            password=config.cpmpassword
        )

        filenames.append(filepath)

    ## Save to json file

    json_file_details = save_filenames_to_json(filenames, os.path.join(config.save_path, 'cmems_prod_config.json'))

    return json_file_details