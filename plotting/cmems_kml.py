from rtdata.satellite_utils import cmems_download_utils as cmems_dl
from rtdata.satellite_utils import cmems_modcur_calc_utils as cmems_cur_pro
from rtdata.satellite_utils import cmems_kml_file_creation_utils as cmems_kml

cmems_dl.cmems_data_download()
cmems_cur_pro.cmems_process_currents()
cmems_kml.cmems_produce_kmz()