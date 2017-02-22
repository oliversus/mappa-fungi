import numpy as np

def init():
    global data_dir, work_dir, min_lat, max_lat, centre_lat, min_lon, max_lon, centre_lon, del_lat, del_lon
    data_dir = "/data/osus/geodata/HSAF/" # "/mnt/DATA/geodata/HSAF/"
    work_dir = "/cmsaf/nfshome/osus/mappa-fungi/SWC/HSAF/"     # "/home/osus/Code/mappa-fungi/SWC/HSAF"
    min_lat = 47.
    max_lat = 55.5
    centre_lat = np.mean((min_lat, max_lat))
    min_lon = 5.6
    max_lon = 15.1
    centre_lon = np.mean((min_lon, max_lon))
    del_lat = 0.01
    del_lon = 0.01

