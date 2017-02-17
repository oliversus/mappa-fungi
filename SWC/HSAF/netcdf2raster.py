#!/usr/bin/python

from __future__ import division, print_function
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
from osgeo import gdal, osr
from pylab import flipud
import os
import globals

def create_raster(lon, lat, variable, split, lon_split=None, left=None):
    if split:
        if left:
            lon = lon[:, 0:lon_split]
            lat = lat[:, 0:lon_split]
            variable = flipud(variable[:, 0:lon_split])
            tif_suffix = "_left.tif"
        else:
            lon_split += 1
            lon = lon[:, lon_split:-1]
            lat = lat[:, lon_split:-1]
            variable = flipud(variable[:, lon_split:-1])
            tif_suffix = "_right.tif"
    else:
        variable = flipud(variable)
        tif_suffix = ".tif"

    not_in_germany = ((lon > 5.6) & (lon < 15.1) & (lat > 47.) & (lat < 55.5)).sum() == 0
    if not_in_germany:
        return

    # For each pixel I know it's latitude and longitude.
    # As you'll see below you only really need the coordinates of
    # one corner, and the resolution of the file.
    # That's (top left x, w-e pixel resolution, rotation (0 if North is up),
    #         top left y, rotation (0 if North is up), n-s pixel resolution)
    xmin, ymin, xmax, ymax = [lon.min(), lat.min(), lon.max(), lat.max()]
    nrows, ncols = np.shape(variable)
    xres = (xmax - xmin) / float(ncols)
    yres = (ymax - ymin) / float(nrows)
    geotransform = (xmin, xres, 0, ymax, 0, -yres)

    output_raster = gdal.GetDriverByName('GTiff').Create(os.path.join(root, file.replace(".nc", tif_suffix)), ncols, nrows, 1,
                                                         gdal.GDT_Float32)  # Open the file
    output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
    srs = osr.SpatialReference()  # Establish its coordinate encoding
    srs.ImportFromEPSG(4326)  # This one specifies WGS84 lat long.
    output_raster.SetProjection(srs.ExportToWkt())  # Exports the coordinate system to the file
    output_raster.GetRasterBand(1).WriteArray(variable)  # Writes my array to the raster

if __name__ == '__main__':
    globals.init()
    for root, dirs, filenames in os.walk(globals.data_dir):
        for file in filenames:
            if file.endswith('.nc'):
                # open NetDF input file
                nc = Dataset(os.path.join(root, file))
                # get lat/lon
                lon = nc["longitude"][:]
                lat = nc["latitude"][:]
                # build lat/lon grid
                lon_m, lat_m = np.meshgrid(lon, lat)
                # check whether there are no data in Germany
                not_in_germany = ((lon_m > 5.6) & (lon_m < 15.1) & (lat_m > 47.) & (lat_m < 55.5)).sum() == 0
                # or file size too small
                too_small = os.stat(os.path.join(root, file)).st_size < 100000
                # if so, remove input file and skip
                if not_in_germany or too_small:
                    os.remove(os.path.join(root, file))
                    print("Deleting " + file + " as criteria not met.")
                    continue
                # else, convert files
                print("Converting " + file + " to tif format, splitting when necessary.")
                # split data where longitude increment is larger than median increment + 2 standard deviations
                lon_diff = np.diff(lon)
                # files are not always split, so check whether discontinuity in lon exists
                try:
                    lon_split = int(np.where(lon_diff > (np.median(lon_diff) + 2 * np.std(lon_diff)))[0])
                    split = True
                # if not, don't split
                except:
                    split = False
                
                soil_moisture = nc["soil_moisture"][:]
                soil_moisture[soil_moisture > 100.] = np.nan
                soil_moisture = ma.masked_invalid(soil_moisture)

                if split:
                    create_raster(lon_m, lat_m, soil_moisture, split, lon_split=lon_split, left=True)
                    create_raster(lon_m, lat_m, soil_moisture, split, lon_split=lon_split, left=False)
                else:
                    create_raster(lon_m, lat_m, soil_moisture, split)
                os.remove(os.path.join(root, file))