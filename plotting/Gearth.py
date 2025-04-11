from rtdata.c2_api import api_interface as c2
from rtdata.satellite_utils import cmems_download_utils as cmems_dl
from rtdata.satellite_utils import cmems_modcur_calc_utils as cmems_cur_pro
from rtdata.satellite_utils import cmems_kml_file_creation_utils as cmems_kml

from rtdata import config

list_lon = []
list_lat = []

v_list = []
u_list = []


for unit in config.gliders_units:

    #Get the last position of the glider
    pos = c2.get_positions(config.token, "slocum", unit, test = False)
    lat, lon = c2.get_last_coordinates(pos)
    list_lon.append(lon)
    list_lat.append(lat)

    print(f"Downloading {unit} currents data")
    #Get the last current value (TODO : add a dynamic date limit, toward the end of the mission this code will download millions lines just for one observation)
    currents = c2.get_observations(config.token, 'slocum', unit, variables = ["m_water_vy", "m_water_vx", "m_lat", "m_lon", "m_time"])

    #last V value
    v = currents[currents['variable'] == 'm_water_vy']
    last_time = v["timestamp"].max()
    v = v['value'].iloc[-1]
    v_list.append(v)

    #Last U value
    u = currents[currents['variable'] == 'm_water_vx']
    last_time = u["timestamp"].max()
    u = u['value'].iloc[-1]
    u_list.append(u)

    c2.create_kml_line(pos, config.save_path + unit + "_line.kmz", "990000ff")
    print("Done")



c2.create_kml_point(config.gliders_names, list_lon, list_lat, u_list,  v_list, config.save_path + "datapoint.kmz")

cmems_dl.cmems_data_download()
cmems_cur_pro.cmems_process_currents()
cmems_kml.cmems_produce_kmz()