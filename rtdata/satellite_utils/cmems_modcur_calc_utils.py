import os
import netCDF4
import xarray as xr
import numpy as np
from datetime import datetime, timedelta
import json

from rtdata import config


def get_filepath_from_json(json_file, match_str):
    """
    Load a filename from a JSON file that contains `match_str`, and return its full path and base name.
    
    Parameters:
        json_file (str): Path to the JSON file storing filenames.
        match_str (str): Substring to match in filenames (e.g., "model_currents.nc").
        base_path (str): Base directory to prepend to the matched filename.
        
    Returns:
        tuple: (full_path, filename_base)
    """

    json_file_loc = os.path.join(config.save_path,json_file)

    with open(json_file_loc, 'r') as f:
        data = json.load(f)
    print(data)
    filename_in_json = next((file for section in data.values() for file in section if match_str in file), None)
    
    if not filename_in_json:
        raise FileNotFoundError(f"No file containing '{match_str}' found in {json_file_loc}")
    
    filepath = os.path.join(filename_in_json)
    filename_base = os.path.basename(filepath)
    
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
    return output_path


def update_json_file(json_path, filenames, category="processed data"):
    """
    Update a JSON file with new filenames under a specified category.
    """

    json_file_loc = os.path.join(config.save_path,json_path)

    # Check if the JSON file exists, if not create an empty structure
    if os.path.exists(json_file_loc):
        with open(json_file_loc, 'r') as f:
            data = json.load(f)
    else:
        data = {}

    # Ensure the category exists in the data structure
    if category not in data:
        data[category] = []

    # Add the new filenames with the full path
    data[category].extend(filenames)

    # Write the updated data back to the JSON file
    with open(json_file_loc, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Updated filenames saved to {json_file_loc}")


def cmems_process_currents(json_file='cmems_prod_config.json', match_str='model_currents.nc'):
    """
    Process CMEMS model current products into 1000m only and depth averaged products.

    """

    filepath, filenamebase = get_filepath_from_json(json_file, match_str)

    ds = xr.open_dataset(filepath)

    # 1. Extract 1000m depth bin
    ds_1000m = extract_depth_bin(ds, var_names=['uo', 'vo'], depth_value=1000)

    # 2. Compute depth-weighted averages
    averaged_ds = compute_weighted_average(ds, var_names=['uo', 'vo'])

    # 3. Save outputs
    filenamebase = os.path.splitext(filenamebase)[0]
    
    # Save datasets and get full paths
    file_1000m = save_dataset(ds_1000m, f'{filenamebase}_1000m.nc', config.save_path)

    file_avg   = save_dataset(averaged_ds, f'{filenamebase}_averaged.nc', config.save_path)

    # 4. Update JSON with full file paths
    update_json_file(json_file, [file_avg, file_1000m])


if __name__ == '__main__':

    process_currents()