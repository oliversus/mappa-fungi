from __future__ import division, print_function
from netCDF4 import Dataset
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.basemap import Basemap
from numpy.ma import masked_invalid

nc = Dataset("h08_20170214_090000_metopb_22883_ZAMG.nc", "r")

lon = nc.variables['longitude'][:]
lat = nc.variables['latitude'][:]
soil_moisture = nc.variables['soil_moisture'][:]
# set fill values, which are 66% of data
soil_moisture[soil_moisture == 1.7e+38] = np.nan
soil_moisture = masked_invalid(soil_moisture)

# create 2D lon/lat arrays
lon_m, lat_m = np.meshgrid(lon, lat)
brd = np.where(((lat_m < 55) & (lat_m > 47) & (lon_m < 15.2) & (lon_m > 5.8)))

scale = 0.3
width = 2500000 * scale; height = 3500000 * scale
lat_0 = 52.
lon_0 = 10.
map = Basemap(width = width, height = height, resolution='l',
              projection = 'stere', lat_ts = lat_0, lat_0 = lat_0, lon_0 = lon_0)

fig1 = plt.figure(figsize=(10, 20))
ax = fig1.add_subplot(1, 1, 1)

# draw coasts and fill continents
map.drawcoastlines(linewidth=0.5)
map.drawcountries(linewidth=1.0)
fillContinents = map.fillcontinents(color='#C0C0C0', lake_color='#7093DB', zorder=0)

# choose colourbar, fill_values are grey
cmap = mpl.cm.bwr
cmap.set_bad('grey')
# plot data
forColorbar = map.pcolormesh(lon_m[brd], lat_m[brd], soil_moisture[brd], latlon=True, cmap=cmap)

# add colorbar
cb = map.colorbar(forColorbar, "right")

# draw grid lines
gridSpacingLat = 5.
gridSpacingLon = 5.
map.drawparallels(np.arange(45, 60, gridSpacingLat),color = 'black',
                  linewidth = 0.5,labels=[True, False, False, False])
map.drawmeridians(np.arange(5., 15., gridSpacingLon),color = '0.25',
                  linewidth = 0.5,labels=[False, False, False, True])


# lon2=c(NaN,lon)
# lonSplit = which((lon-lon2[1:length(lon)])>1)
#
# clon=lon[1:(lonSplit-1)]
# cdata=data[1:(lonSplit-1),]
#
# cdata[cdata>10000]=NaN
#
# raster = raster(t(cdata),xmn=min(clon),xmx=max(clon),ymn=min(lat),ymx=max(lat))
# raster = flip(raster, 2)
#
# writeRaster(raster, "out.tif")
#
# plot(raster)
# plot(coastsCoarse,add=T,col="black")