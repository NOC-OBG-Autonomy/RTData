import os
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
import json
import netCDF4

from rtdata import config


def get_filepath_from_json(json_file, match_str, base_path):
    """
    Load a filename from a JSON file that contains `match_str`, and return its full path and base name.
    
    Parameters:
        json_file (str): Path to the JSON file storing filenames.
        match_str (str): Substring to match in filenames (e.g., "model_currents.nc").
        base_path (str): Base directory to prepend to the matched filename.
        
    Returns:
        tuple: (full_path, filename_base)
    """

    with open(json_file, 'r') as f:
        data = json.load(f)
    print(data)
    filename_in_json = next((file for section in data.values() for file in section if match_str in file), None)
    
    if not filename_in_json:
        raise FileNotFoundError(f"No file containing '{match_str}' found in {json_file}")
    
    filepath = os.path.join(base_path, filename_in_json)
    filename_base = os.path.splitext(filename_in_json)[0]
    
    return filepath, filename_base


def extract_depth_bin(ds, var_names, depth_value):
    """
    Extract variables from a specific depth bin.

    Parameters:
        ds (xarray dataset): xarray dataset with at least one depth dimension.
        var_names (str): Substring to match to variable (e.g., 'uo').
        depth_value (int): Depth value to extract, in meters.
    
    Returns:
        new_ds (xarray dataset): Dataset of variables at desired depth
    """

    depth = ds['depth']
    idx = (depth == depth_value).argmax().item()
    extracted = {var: ds[var].isel(depth=idx) for var in var_names}

    for var in var_names:
        extracted[var].attrs = ds[var].attrs

    new_ds = xr.Dataset(extracted)
    new_ds.attrs = ds.attrs

    return new_ds


def compute_weighted_average(ds, var_names):
    """
    Compute the depth-weighted average for each time step.

    Parameters:
        ds (xarray dataset): Path to the netcdf file with data.
        var_names (str): Substring to match to variable (e.g., 'uo').
    
    Returns:
        averaged_ds (ds): Dataset of depth weighted values.
    """

    depth = ds['depth']
    depth_diff = np.diff(depth, append=depth[-1])
    depth_weights = xr.DataArray(depth_diff, coords={'depth': depth}, dims='depth')
    
    def weighted_avg(var):
        return (var * depth_weights).sum(dim='depth') / depth_weights.sum()
    
    averaged = {
        var: ds[var].groupby('time').map(weighted_avg)
        for var in var_names
    }

    for var in var_names:
        averaged[var].attrs = ds[var].attrs
    averaged_ds = xr.Dataset(averaged)
    averaged_ds.attrs = ds.attrs

    return averaged_ds


def save_dataset(ds, filename, out_dir):
    """
    Save a dataset to NetCDF format.

    """
    output_path = os.path.join(out_dir, filename)
    ds.to_netcdf(output_path)
    print(f"Saved to {output_path}")
    return filename


def update_json_file(json_path, filenames, category="processed data"):
    """
    Update a JSON file with new filenames under a specified category.
    
    """
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            data = json.load(f)
    else:
        data = {}
    print(data)
    if category not in data:
        data[category] = []

    data[category].extend(filenames)

    with open(json_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Updated filenames saved to {json_path}")


def process_currents(json_file, match_str, data_dir):
    """
    Process CMEMS model current products into 1000m only and depth averaged products.
    
    """

    filepath = get_filepath_from_json(json_file, match_str, data_dir)

    ds = xr.open_dataset(filepath[0])

    # 1. Extract 1000m depth bin
    ds_1000m = extract_depth_bin(ds, var_names=['uo', 'vo'], depth_value=1000)

    # 2. Compute depth-weighted averages
    averaged_ds = compute_weighted_average(ds, var_names=['uo', 'vo'])

    # 3. Save outputs
    file_1000m = save_dataset(ds_1000m, f'{filepath[1]}_1000m.nc', data_dir)
    file_avg   = save_dataset(averaged_ds, f'{filepath[1]}_averaged.nc', data_dir)

    # 4. Update JSON
    update_json_file(json_file, [file_avg, file_1000m])


if __name__ == '__main__':

    #filepath = get_filepath_from_json('data/filenames.json','model_currents.nc','data')
    #ds = xr.open_dataset(filepath[0])
    #ds_1000m = extract_depth_bin(ds,['uo','vo'],1000)
    #averaged_ds = compute_weighted_average(ds, var_names=['uo', 'vo'])
    #file_1000m = save_dataset(ds_1000m, f'{filepath[1]}_1000m.nc', 'data/')
    #file_avg   = save_dataset(averaged_ds, f'{filepath[1]}_averaged.nc', 'data/')

    process_currents('data/filenames.json', 'model_currents.nc', 'data/')