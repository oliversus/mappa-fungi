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

    out_of_lon = ((lon > 5.6) & (lon < 15.6)).sum() == 0
    out_of_lat = ((lat > 47.) & (lat < 55.5)).sum() == 0
    if out_of_lon or out_of_lat:
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
                nc = Dataset(os.path.join(root, file))
                lon = nc["longitude"][:]
                lat = nc["latitude"][:]
                out_of_lon = ((lon > 5.6) & (lon < 15.6)).sum() == 0
                out_of_lat = ((lat > 47.) & (lat < 55.5)).sum() == 0
                too_small = os.stat(os.path.join(root, file)).st_size < 100000
                if out_of_lat or out_of_lon or too_small:
                    os.remove(os.path.join(root, file))
                    print("Deleting " + file + " as criteria not met.")
                    continue
                print("Converting " + file + " to tif format, splitting when necessary.")
                # split data where longitude increment is larger than median increment + 2 standard deviations
                lon_diff = np.diff(lon)
                try:
                    lon_split = int(np.where(lon_diff > (np.median(lon_diff) + 2 * np.std(lon_diff)))[0])
                    split = True
                except:
                    split = False

                soil_moisture = nc["soil_moisture"][:]
                soil_moisture[soil_moisture > 100.] = np.nan
                soil_moisture = ma.masked_invalid(soil_moisture)

                lon_m, lat_m = np.meshgrid(lon, lat)
                if split:
                    create_raster(lon_m, lat_m, soil_moisture, split, lon_split=lon_split, left=True)
                    create_raster(lon_m, lat_m, soil_moisture, split, lon_split=lon_split, left=False)

                else:
                    create_raster(lon_m, lat_m, soil_moisture, split)
                os.remove(os.path.join(root, file))