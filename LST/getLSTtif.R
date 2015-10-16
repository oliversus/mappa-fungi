#set MRT data directory path
Sys.setenv(MRT_DATA_DIR  = "/home/oliver/MRT/MRT/data/")

#MODIS product
product="MOD11A1"

#MODIS tiles
h=18; v=c(3,4)

#get data for last n days, excluding today
n     = 10
dates = as.character(Sys.Date() - seq(n) )
dates = gsub("-", ".", dates)

#path to MRT binary
MRTpath = "/home/oliver/MRT/MRT/bin"

#subset product bands
bands_subset = "1 0 0 0 0 0 0 0 0 0 0 0"

#UTM coordinates of upper left (UL) and lower right (LR) corner of tif to be created
UL = c(217146.2, 6181346.0)
LR = c(965535.1, 5178478.0)

#source MODIS script to download, repproject, and mosaic data
source("/home/oliver/mappa-fungi/LST/ModisDownload.R")

#call MODIS script
ModisDownload(x = product, h = h, v = v, dates = dates,
              MRTpath = MRTpath, mosaic = T, proj = T,
              utm_zone = 32, version = '005', pixel_size = 1000,
              bands_subset = bands_subset, UL = UL, LR = LR, delete = T)
