library(ncdf)
library(raster)
library(rworldmap)

nc=open.ncdf("h08_20151005_090300_metopb_15808_ZAMG_classic.nc")

data=get.var.ncdf(nc,var="soil_moisture")
lon=get.var.ncdf(nc,var="longitude")
lat=get.var.ncdf(nc,var="latitude")
lon2=c(NaN,lon)
lonSplit = which((lon-lon2[1:length(lon)])>1)

clon=lon[1:(lonSplit-1)]
cdata=data[1:(lonSplit-1),]

cdata[cdata>10000]=NaN

raster = raster(t(cdata),xmn=min(clon),xmx=max(clon),ymn=min(lat),ymx=max(lat))
raster = flip(raster, 2)

writeRaster(raster, "out.tif")

plot(raster)
plot(coastsCoarse,add=T,col="black")