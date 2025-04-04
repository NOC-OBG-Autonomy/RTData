def read_cts_datetime(filepath):
    with open(filepath, 'r') as file:
        file_content = file.read()
    datetime_pattern = r'UTC=3D(\d{2}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})'

    match = re.search(datetime_pattern, file_content)
    
    if not match:
        raise ValueError(f"No datetime found in the file : {file_content}")

    date_str = match.group(1)
    time_str = match.group(2)

    # Combine date and time strings
    datetime_str = date_str + ' ' + time_str
    
    # Convert the combined string to a datetime object
    dt = pd.to_datetime(datetime_str, format = '%y-%m-%d %H:%M:%S')
    return(dt)

def read_cts_position(filepath):
    with open(filepath, 'r') as file:
        file_content = file.read()
    
    pattern = r'Lat=3D(?P<lat>\d{2})(?P<lat_min>\d{2}\.\d+)(?P<lat_dir>[NS]) Long=3D(?P<lon>\d{3})(?P<lon_min>\d{2}\.\d+)(?P<lon_dir>[EW])'
    
    match = re.search(pattern, file_content)
    
    if not match:
        raise ValueError("Invalid CTS5 format")
    
    # Extract latitude and longitude parts
    lat_deg = int(match.group('lat'))
    lat_min = float(match.group('lat_min'))
    lat_dir = match.group('lat_dir')
    
    lon_deg = int(match.group('lon'))
    lon_min = float(match.group('lon_min'))
    lon_dir = match.group('lon_dir')
    
    # Convert to decimal degrees
    lat_decimal = convert_to_decimal(lat_deg, lat_min)
    lon_decimal = convert_to_decimal(lon_deg, lon_min)
    
    # Adjust for direction
    if lat_dir == 'S':
        lat_decimal = -lat_decimal
    if lon_dir == 'W':
        lon_decimal = -lon_decimal
    
    return lat_decimal, lon_decimal

def email_to_csv_pos(email_path):
    date = read_cts_datetime(email_path)
    lat, lon  = read_cts_position(email_path)

    position_info = {
    'date': date,
    'lon': lon,
    'lat': lat,
    'platform_type': 'Float',
    'platform_id': email_path[-17:-7]
    }
    position_df = pd.DataFrame([position_info])
    return(position_df)
