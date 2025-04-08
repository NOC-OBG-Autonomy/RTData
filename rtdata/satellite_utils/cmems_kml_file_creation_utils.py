from simplekml import (Kml, OverlayXY, ScreenXY, Units, RotationXY,
                       AltitudeMode, Camera)
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os
import xarray as xr
from datetime import datetime
import matplotlib.colors as colors
import json
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.colors import Normalize

from rtdata import config

def load_json_config(json_path):
    with open(json_path, 'r') as f:
        config = json.load(f)
    return config["cmems_files"][0], config["processed data"]


def get_day_indices(time_array):
    days = np.unique(time_array.dt.floor('D'))
    return [(time_array.dt.floor('D') == day).values.nonzero()[0] for day in days], days


def gearth_fig(llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat, pixels=1024):
    aspect = np.cos(np.mean([llcrnrlat, urcrnrlat]) * np.pi/180.0)
    xsize = np.ptp([urcrnrlon, llcrnrlon]) * aspect
    ysize = np.ptp([urcrnrlat, llcrnrlat])
    aspect = ysize / xsize

    if aspect > 1.0:
        figsize = (10.0 / aspect, 10.0)
    else:
        figsize = (10.0, 10.0 * aspect)

    fig = plt.figure(figsize=figsize, frameon=False, dpi=pixels//10)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(llcrnrlon, urcrnrlon)
    ax.set_ylim(llcrnrlat, urcrnrlat)
    return fig, ax


def compute_current_speed(u, v):
    """Compute current speed from U and V components."""
    return np.sqrt(u**2 + v**2)


def generate_quiver_plot(x, y, u, v, speed, region_bounds, output_path, cmap='spring', scale=2, norm=None):
    """Generate and save a quiver plot as PNG."""
    lon_min, lat_min, lon_max, lat_max = region_bounds
    pixels = 1024 * 10
    
    fig, ax = gearth_fig(llcrnrlon=lon_min, llcrnrlat=lat_min,
                         urcrnrlon=lon_max, urcrnrlat=lat_max,
                         pixels=pixels)
    
    im = ax.quiver(x, y, u, v, speed,
                   angles='xy', scale_units='xy',
                   cmap=cmap, width=0.002, scale=scale,
                   norm=norm)
    
    ax.quiverkey(im, 0.86, 0.45, 0.2, "0.2 m s$^{-1}$", labelpos='W')
    ax.set_axis_off()

    fig.savefig(output_path, transparent=False, format='png')
    plt.clf()
    plt.close()
    return im


def generate_colorbar(im, output_path):
    """Generate and save a colorbar as PNG."""
    fig = plt.figure(figsize=(1.0, 4.0), facecolor=None, frameon=False)
    ax = fig.add_axes([0.0, 0.05, 0.2, 0.9])
    cb = fig.colorbar(im, cax=ax)
    cb.set_label(f'Current velocity [m s$^{-1}$]', rotation=-90, color='k', labelpad=20)

    fig.savefig(output_path, transparent=False, format='png')
    plt.clf()
    plt.close()


def make_kml(llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat,
             figs, colorbar=None, **kw):
    kml = Kml()
    altitude = kw.pop('altitude', 2e7)
    roll = kw.pop('roll', 0)
    tilt = kw.pop('tilt', 0)
    altitudemode = kw.pop('altitudemode', AltitudeMode.relativetoground)
    camera = Camera(latitude=np.mean([urcrnrlat, llcrnrlat]),
                    longitude=np.mean([urcrnrlon, llcrnrlon]),
                    altitude=altitude, roll=roll, tilt=tilt,
                    altitudemode=altitudemode)

    kml.document.camera = camera
    draworder = 0
    for fig in figs:
        draworder += 1
        ground = kml.newgroundoverlay(name='GroundOverlay')
        ground.draworder = draworder
        ground.visibility = kw.pop('visibility', 1)
        ground.name = kw.pop('name', 'overlay')
        ground.color = kw.pop('color', '9effffff')
        ground.atomauthor = kw.pop('author', 'ocefpaf')
        ground.latlonbox.rotation = kw.pop('rotation', 0)
        ground.description = kw.pop('description', 'Matplotlib figure')
        ground.gxaltitudemode = kw.pop('gxaltitudemode', 'clampToSeaFloor')
        ground.icon.href = fig
        ground.latlonbox.east = llcrnrlon
        ground.latlonbox.south = llcrnrlat
        ground.latlonbox.north = urcrnrlat
        ground.latlonbox.west = urcrnrlon

    if colorbar:
        screen = kml.newscreenoverlay(name='ScreenOverlay')
        screen.icon.href = colorbar
        screen.overlayxy = OverlayXY(x=0, y=0,
                                     xunits=Units.fraction,
                                     yunits=Units.fraction)
        screen.screenxy = ScreenXY(x=0.015, y=0.075,
                                   xunits=Units.fraction,
                                   yunits=Units.fraction)
        screen.rotationXY = RotationXY(x=0.5, y=0.5,
                                       xunits=Units.fraction,
                                       yunits=Units.fraction)
        screen.size.x = 0
        screen.size.y = 0
        screen.size.xunits = Units.fraction
        screen.size.yunits = Units.fraction
        screen.visibility = 1

    kmzfile = kw.pop('kmzfile', 'overlay.kmz')
    kml.savekmz(kmzfile)


def generate_kmz(image_path, colorbar_path, region_bounds, kmz_path):
    """Create KMZ using image and colorbar."""
    lon_min, lat_min, lon_max, lat_max = region_bounds
    make_kml(lon_min, lat_min, lon_max, lat_max,
             [image_path], colorbar=colorbar_path,
             kmzfile=kmz_path)
    print(f"KMZ file created: {kmz_path}")


def create_current_vector_kmz(subsampled_longitudes, subsampled_latitudes,
                               subsampled_ugos, subsampled_vgos,
                               var_category, date_of_plot, kmz_dir,
                               region_bounds, norm=None):
    """Full pipeline to generate quiver KMZ and colorbar."""
    x = subsampled_longitudes
    y = subsampled_latitudes
    u = subsampled_ugos
    v = subsampled_vgos

    speed = compute_current_speed(u, v)

    image_name = f"{var_category}_mean.png"
    image_path = os.path.join(kmz_dir, image_name)
    
    im = generate_quiver_plot(x, y, u, v, speed, region_bounds, image_path, norm=norm)

    colorbar_path = os.path.join(kmz_dir, 'colorbar.png')
    generate_colorbar(im, colorbar_path)

    kmz_name = f"{var_category}_{date_of_plot}_mean.kmz"
    kmz_path = os.path.join(kmz_dir, kmz_name)
    
    generate_kmz(image_path, colorbar_path, region_bounds, kmz_path)


def process_and_plot_day(ds, time_idx, output_dir, var_category, date_of_plot):

    daily_ds = ds.isel(time=time_idx)

    u_var = 'ugos' if 'ugos' in ds else 'uo'
    v_var = 'vgos' if 'vgos' in ds else 'vo'

    u = daily_ds[u_var].mean(dim='time')
    v = daily_ds[v_var].mean(dim='time')

    x = daily_ds['longitude']
    y = daily_ds['latitude']

    speed = np.sqrt(u**2 + v**2)

    fig, ax = gearth_fig(llcrnrlon=float(x.min()),
                         llcrnrlat=float(y.min()),
                         urcrnrlon=float(x.max()),
                         urcrnrlat=float(y.max()),
                         pixels=10240)

    norm = Normalize(vmin=0, vmax=0.5)

    im = ax.quiver(x, y, u, v, speed,
                   angles='xy', scale_units='xy', 
                   cmap='spring', width=0.002, scale=2,
                   norm=norm)
    ax.quiverkey(im, 0.86, 0.45, 0.2, "0.2 m s$^{-1}$", labelpos='W')
    ax.set_axis_off()

    image_name = f"{var_category}_{date_of_plot}.png"
    image_path = os.path.join(output_dir, image_name)
    fig.savefig(image_path, transparent=False)
    plt.clf()
    plt.close()

    fig = plt.figure(figsize=(1.0, 4.0))
    ax = fig.add_axes([0.0, 0.05, 0.2, 0.9])
    cb = fig.colorbar(im, cax=ax)
    cb.set_label('Current velocity [m s$^{-1}$]', rotation=-90, color='k', labelpad=20)

    colorbar_path = os.path.join(output_dir, f"{var_category}_{date_of_plot}_colorbar.png")
    fig.savefig(colorbar_path, transparent=False)
    plt.clf()
    plt.close()

    # KMZ
    kmz_subdir = os.path.join(output_dir, 'kmz')
    os.makedirs(kmz_subdir, exist_ok=True)  # create 'kmz' folder if it doesn't exist
    kmz_name = f"{var_category}_{date_of_plot}.kmz"
    kmz_path = os.path.join(kmz_subdir, kmz_name)
    make_kml(float(x.min()), float(y.min()), float(x.max()), float(y.max()),
             [image_path], colorbar=colorbar_path, kmzfile=kmz_path)
    print(f"KMZ file created: {kmz_path}")

    for f in [image_path, colorbar_path]:
        if os.path.exists(f):
            os.remove(f)


def cmems_produce_kmz(json_path = os.path.join(config.save_path,'cmems_prod_config.json')):
    obs_file, processed_files = load_json_config(json_path)
    all_files = [obs_file] + processed_files
   
    for nc_file in all_files:
        ds = xr.open_dataset(nc_file)
        time_indices_by_day, unique_days = get_day_indices(ds['time'])

        file_tag = os.path.splitext(os.path.basename(nc_file))[0]
        for time_indices, day in zip(time_indices_by_day, unique_days):
            date_str = np.datetime_as_string(day, unit='D')
            process_and_plot_day(ds, time_indices, config.save_path, file_tag, date_str)