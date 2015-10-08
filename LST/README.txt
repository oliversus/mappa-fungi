Land Surface Temperature data

data source: MODIS...
     - Land Surface Temperature/Emissivity Daily L3 Global 1km (MOD11A1/MYD11A1)
     or
     - Land Surface Temperature/Emissivity 8-Day L3 Global 1km (MOD11A2/MYD11A2)

ideally, retrieve 8-Day product from both Terra and Aqua, but 4 days apart

data access:
     - Daac2Disk_Linux command line tool
     or
     - MODIS_download.R
     (http://spatial-analyst.net/wiki/index.php?title=Download_and_resampling_of_MODIS_images)
     or
     - ModisDownload.R
     (http://r-gis.net/?q=ModisDownload)
     
MODIS tiles: h18v3 and h18v4, so h=18; v=c(3,4)
