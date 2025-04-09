#Mission details

#Gliders
gliders_units = ["unit_306","unit_352", "unit_408", "unit_436"]
gliders_names = ["Zephyr", "OMG-1","Growler", "Stella"]
gliders_ids = [127, 129, 55, 118]

#Floats
wmo = [6990668]

#Credentials for API
token = "your token in the prod env" 
token_test = "your token in the test env"
vpn_access = False #Changing this to True will lead to a request to the broker

#Credentials for Copernicus Marine Service (https://data.marine.copernicus.eu/register)
cpmusername = 'your username for copernicus marine service'
cpmpassword = 'your password for copernicus marine service'

#Saving folders
save_path = "path/to/save/files/"

#broker (usefull if ship position is needed)
broker = "seasystems.noc.soton.ac.uk"
port = 1883
topic = "topic/path"
username = "usrname"
password = "pwd"

