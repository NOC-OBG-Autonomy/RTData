import requests
import config
import pandas as pd
from datetime import datetime
from glob import glob
import io
import simplekml


def get_positions(token, platform_type, platform_serial, test = False):
    
    if test == False:
        api_url = "https://api.c2.noc.ac.uk/positions/positions" 
    if test == True :
        api_url = "https://api-test.c2.noc.ac.uk/positions/positions" 

    # Headers including the token
    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
    "platform_type": platform_type,
    "platform_serial": platform_serial,
    "from": "2024-05-28T18:57",
    "time_order" : "descending"
    }

    # Making my query
    response = requests.get(api_url, headers=headers, params = params)

    # Check the status code of the response
    if response.status_code == 200:
        # Successful request
        data = response.json()
        return(data[0])
    else:
        # Handle errors
        print(f"Error: {response.status_code}")
        print(response.text)

def convert_positions(json_pos):
    import pandas as pd
    data = pd.DataFrame(json_pos)
    my_pos = data['positions'].iloc[0]
    data_cleaned = pd.DataFrame(my_pos)
    return(data_cleaned)

def get_last_coordinates(data):
    """
    Extract the last latitude and longitude from the JSON response.

    Args:
    data: JSON response in dictionary format.

    Returns:
    Tuple containing the last latitude and longitude.
    """
    # Extract the list of positions
    positions = data['positions']['internal']
    
    # Get the last position
    last_position = positions[0]
    
    # Extract the latitude and longitude
    last_latitude = last_position['latitude']
    last_longitude = last_position['longitude']
    
    return last_latitude, last_longitude

def create_kml_line(json_position, output_file, color):
    kml = simplekml.Kml()

    positions = json_position['positions']['internal']

    positions_list = []
    for coord in positions:
        lon = coord['longitude']
        lat = coord['latitude']

        positions_list.append((lon, lat))
    
    ls = kml.newlinestring(name = "my test", coords = positions_list)

    ls.style.linestyle.width = 3

    ls.style.linestyle.color = color

    #time = coord['time'].replace('T', ' ').replace('Z', '')
    #point.timestamp.when = time

    kml.save(output_file)

def create_kml_point(glider, longitude, latitude, m_water_x, m_water_y, output_file):
    """Create a kml file with points and description of currents

    Args:
        glider (list): A list of glider names
        longitude (list): a list of longitudes, in degrees decimal
        latitude (list): a list of latitudes, in degrees decimal
        m_water_x (list): a list of DAC, u component
        m_water_y (list): a list of DAC, v component
        output_file (string): the path where the kml file will be saved
    """
    kml = simplekml.Kml()

    for i in range(len(glider)):
        glider_temp = glider[i]
        lon_t = longitude[i]
        lat_t = latitude[i]
        u_t = m_water_x[i]
        v_t = m_water_y[i]

        point = kml.newpoint(name = glider_temp, coords = [(lon_t, lat_t)])
        point.description = f"m_water_x : {u_t} \n m_water_y : {v_t}"
    
    kml.save(output_file)



def get_observations(token, platform_type, platform_serial, variables):
    api_url = "https://api.c2.noc.ac.uk/timeseries/observations/csv" 


    # Headers including the token
    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
    "platform_type": platform_type,
    "platform_serial": platform_serial,
    "from": "2024-09-25T18:57",
    "variable": variables
    }

    # Making my query
    response = requests.get(api_url, headers=headers, params = params)

    # Check the status code of the response
    if response.status_code == 200:
        # Successful request
        data = response.content.decode('utf-8')
        df = pd.read_csv(io.StringIO(data))
        return(df)
    else:
        # Handle errors
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == '__main__':

    # test = get_observations(config.token, 'slocum', ['unit_397', 'unit_405', 'unit_398', 'unit_345'], variables = ["m_water_vy", "m_water_vx", "m_lat", "m_lon", "m_time"])
    # test.to_csv('C:/Users/flapet/OneDrive - NOC/Documents/NRT_viz/biocarbon_nrt_data_viz/Data/Gliders/current.csv')

    #DOcumentation : https://api.c2.noc.ac.uk/timeseries/doc
    ts = get_observations(config.token, 'slocum', 'unit_306', variables=["sci_water_pressure", "sci_water_temp",  "sci_water_cond", "m_lon", "m_lat", "sci_flbbcd_chlor_units", "sci_flbbcd_bb_units", "m_time", "sci_oxy4_oxygen"])
    ts.to_csv('C:/Users/flapet/OneDrive - NOC/Documents/NRT_viz/biocarbon_nrt_data_viz/Data/Gliders/glider_ts_306.csv')