from rtdata.c2_api import api_interface as c2
from rtdata import config

list_lon = []
list_lat = []

for unit in config.gliders_units:
    pos = c2.get_positions(config.token, "slocum", unit, test = False)
    lat, lon = c2.get_last_coordinates(pos)
    list_lon.append(lon)
    list_lat.append(lat)

c2.create_kml_point(config.gliders_names, list_lon, list_lat, [0, 0, 0, 0], [0, 0, 0, 0], save_path + "datapoint.kmz")
