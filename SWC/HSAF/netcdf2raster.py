#!/usr/bin/python

from __future__ import division, print_function
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
from osgeo import gdal, osr
from pylab import flipud
import os
import globals
from math import radians, cos, sin, asin, sqrt
import pandas as pd
from scipy import spatial
import time

def resample(data, target_grid, max_distance):
    # aim: resample data from orbit projection to regular lat/lon grid
    # grid dimension and resolution is user defined
    # approach: average all pixel values whose centre are within grid box
    target_points = np.asarray(zip(target_grid.lon.ravel(), target_grid.lat.ravel()))
    source_points = np.asarray(zip(data.lon, data.lat))
    print("setting up KDTree")
    start_time = time.time()
    tree = spatial.cKDTree(source_points)
    print("done")
    print("--- %s seconds ---" % (time.time() - start_time))

    # variables to be resampled
    variables = data.keys()
    # reshaping source data
    source_values = np.zeros((np.prod(data.lat.shape), len(variables)))
    for var_i, var in enumerate(variables):
        source_values[:, var_i] = data[var]
    # defining return data
    return_values = np.empty(target_points.shape[0])
    return_values[:] = np.nan
    #return_count = np.zeros((target_points.shape[0], data.shape[1]))
    #target_lon = target_grid.lon.flatten()
    #target_lat = target_grid.lat.flatten()

    i = -1
    print("starting loop over source points")
    for lon, lat in target_points:
        i += 1
        # nn = tree.query((lon, lat), k=1)
        nn = tree.query_ball_point((lon, lat), globals.del_lat)
        if len(nn) > 0:
            # target_index = nn
            # if np.isfinite(source_values[])
            if any(np.isfinite(source_values[nn, 2])):
                return_values[i] = np.nanmean(source_values[nn, 2])

            # """Check with target grid lat/lons, """
            # lon_NN = source_values[target_index,1] #target_lon[target_index]
            # lat_NN = source_values[target_index,0] #target_lat[target_index]
            # """ that the great circle distance between CCI L2 lat/lon and target grid box lat/lon
            # is lower than a threshold value (i.e. L2 pixel is within grid box)."""
            # L2ToBox = greatCircle(lon, lat, lon_NN, lat_NN)
            # if L2ToBox < max_distance:
            #     for var_i, var in enumerate(variables):
            #         """if data are not fill values"""
            #         if np.isfinite(source_values[i, var_i]):
            #             """add value to box and increment counter"""
            #             return_count[target_index, var_i] += 1
            #             return_values[target_index, var_i] += source_values[i, var_i]

        if i % int(target_points.shape[0] / 10) == 0:
            print('{0}\r'.format(round(i / target_points.shape[0] * 100, 1)))

    print("ending loop over source points")

    # return_count_masked = ma.masked_values(return_count, 0.)
    # out = return_values / return_count_masked
    # out = out.reshape(target_grid.lat.shape[0], target_grid.lat.shape[1], len(variables))
    out = return_values.reshape(target_grid.lat.shape[0], target_grid.lat.shape[1])

    return out


def greatCircle(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def get_max_distance():
    """the maximum distance between CCI and a grid box center is given by
        the great circle distance between the grid box center and one of its corners
        which is half of the grid box diagonal, which can be calculated with Pythagoras"""
    """The lat/lon spacing and the grid box longitude/latitude width"""
    boxLonWidth = globals.del_lon * greatCircle(globals.centre_lon, globals.centre_lat, globals.centre_lon + 1., globals.centre_lat)
    boxLatWidth = globals.del_lat * greatCircle(globals.centre_lon, globals.centre_lat, globals.centre_lon, globals.centre_lat + 1.)
    """give the grid box diagonal"""
    boxDiag = (boxLonWidth ** 2 + boxLatWidth ** 2) ** 0.5
    """half of which is the maximum distance of CCI to any grid box center"""
    maxDistance = boxDiag / 2.
    return maxDistance

class lat_lon_grid():
    def __init__(self, minLat, minLon, maxLat, maxLon, delLat=0.1, delLon=0.1):
        self.minLat = minLat
        self.minLon = minLon
        self.maxLat = maxLat
        self.maxLon = maxLon
        self.delLat = delLat
        self.delLon = delLon

    def __repr__(self):
        return "lat/lon grid min/max values: lat = " + str(self.minLat) + "/" + str(self.maxLat) + \
               ", lon = " + str(self.minLon) + "/" + str(self.maxLon)

    def build_grid(self):
        self.latIter = self.buildVector(self.minLat, self.maxLat, self.delLat)
        self.lonIter = self.buildVector(self.minLon, self.maxLon, self.delLon)

        self.latVector = np.fromiter(self.latIter, dtype=np.float)
        self.lonVector = np.fromiter(self.lonIter, dtype=np.float)

        self.lat, self.lon = np.meshgrid(self.latVector, self.lonVector, indexing='xy')

    def buildVector(self, start, end, stepSize):
        val = start
        if end < start:
            end += 360.0
        while val < end + stepSize:
            if (val > 180.0):
                yield val - 360.0
            else:
                yield val
            val += stepSize

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

    not_in_germany = ((lon > globals.min_lon) & (lon < globals.max_lon) & (lat > globals.min_lat) & (lat < globals.max_lat)).sum() == 0
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
                not_in_germany = ((lon_m > globals.min_lon) & (lon_m < globals.max_lon) & (lat_m > globals.min_lat) & (lat_m < globals.max_lat)).sum() == 0
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

                split = False
                soil_moisture = nc["soil_moisture"][:]
                soil_moisture[soil_moisture > 100.] = np.nan
                soil_moisture = ma.masked_invalid(soil_moisture)

                # remap soil moisture on regular lat/lon grid
                data_in = pd.DataFrame({'lat': lat_m.flatten(), 'lon': lon_m.flatten(), 'soil_moisture': soil_moisture.flatten()})
                target_grid = lat_lon_grid(globals.min_lat, globals.min_lon, globals.max_lat, globals.max_lon, delLat=globals.del_lat, delLon=globals.del_lon)
                target_grid.build_grid()
                max_distance = get_max_distance()
                soil_moisture = resample(data_in, target_grid, max_distance)
                print("done")

                if split:
                    create_raster(target_grid.lon, target_grid.lat, soil_moisture, split, lon_split=lon_split, left=True)
                    create_raster(target_grid.lon, target_grid.lat, soil_moisture, split, lon_split=lon_split, left=False)
                else:
                    create_raster(target_grid.lon, target_grid.lat, soil_moisture, split)
                # os.remove(os.path.join(root, file))