from __future__ import division, print_function
from netCDF4 import Dataset
import numpy as np
import numpy.ma as ma
from osgeo import gdal, osr
from pylab import flipud

def create_raster(lon, lat, variable, lon_split, left=True):
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

    output_raster = gdal.GetDriverByName('GTiff').Create(file.replace(".nc", tif_suffix), ncols, nrows, 1,
                                                         gdal.GDT_Float32)  # Open the file
    output_raster.SetGeoTransform(geotransform)  # Specify its coordinates
    srs = osr.SpatialReference()  # Establish its coordinate encoding
    srs.ImportFromEPSG(4326)  # This one specifies WGS84 lat long.
    output_raster.SetProjection(srs.ExportToWkt())  # Exports the coordinate system to the file
    output_raster.GetRasterBand(1).WriteArray(variable)  # Writes my array to the raster

file = "h08_20150928_193600_metopb_15715_ZAMG.nc"
nc = Dataset(file)
lon = nc["longitude"][:]
lat = nc["latitude"][:]
# split data where longitude increment is larger than median increment + 2 standard deviations
lon_diff = np.diff(lon)
lon_split = int(np.where(lon_diff > (np.median(lon_diff) + 2 * np.std(lon_diff)))[0])

soil_moisture = nc["soil_moisture"][:]
soil_moisture[soil_moisture == 1.69999998e+38] = -999.  # np.nan
soil_moisture = ma.masked_invalid(soil_moisture)

lon_m, lat_m = np.meshgrid(lon, lat)
create_raster(lon_m, lat_m, soil_moisture, lon_split, left=True)
create_raster(lon_m, lat_m, soil_moisture, lon_split, left=False)

