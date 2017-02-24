#!/usr/bin/python

import ftplib
import time
import os
import gzip
import shutil
from subprocess import Popen, PIPE, call
import globals

# ftp host address
HOST = 'ftphsaf.meteoam.it'
# compression file suffix
compression_suffix = '.gz'
bufr_suffix = '.buf'
# h08 data have the format h08_20170224_121200_metopb_23027_ZAMG + suffix, so split at ZAMG to get basename
# cannot use splitext, as there are multiple extensions
h08_identifier = 'ZAMG'

def main():
    now = time.localtime()
    try:
        f = ftplib.FTP(HOST)
    except (ftplib.socket.error, ftplib.socket.gaierror), e:
        print 'cannot reach to %s' % HOST
        return
    print "Connect to ftp server"

    try:
        f.login(user='osus79@gmail.com', passwd='winter')
    except ftplib.error_perm:
        print 'cannot login'
        f.quit()
        return
    print "logged on to the ftp server"

    f.cwd('/h08/h08_cur_mon_buf')
    data = []
    f.dir(data.append)
    datelist = []
    filelist = []
    for line in data:
        col = line.split()
        datestr = ''.join(col[-1].split("_")[1:3])
        date = time.strptime(datestr, '%Y%m%d%H%M%S')
        datelist.append(date)
        filelist.append(col[-1])
    file_dict = dict(zip(datelist, filelist))

    for file_date, filename in sorted(file_dict.iteritems(), reverse=True):
        if filename.endswith('.tmp'):
            continue
        # calculate time difference between now and file_date
        time_difference = (time.mktime(now) - time.mktime(file_date)) / 60 / 60
        # check here if remote file to be downloaded already exists locally, regardless of suffix
        filename.strip(bufr_suffix + compression_suffix)
        h08_basename = filename.split(h08_identifier)[0] + h08_identifier
        local_files = os.listdir(globals.data_dir)
        if any(h08_basename in string for string in local_files):
            print("File " + h08_basename + " already exists locally - skipping.")
        # only get data from within the last 72 h
        elif time_difference > 72.:
             return
        else:
            print "%s: %s" % (file_date, filename)
            print "file to download is %s" % filename
            try:
                f.retrbinary('RETR %s' % filename, open(filename, 'wb').write)
                # unzip
                compressed_file = gzip.open(filename, 'rb')
                filename_decompressed = filename.strip('.gz')
                decompressed_file = open(filename_decompressed, 'wb')
                decompressed_file.write(compressed_file.read())
                compressed_file.close(); decompressed_file.close()
                os.remove(filename)
                shutil.move(filename_decompressed, globals.data_dir + filename_decompressed)
                call(["./bufr2netcdf", globals.data_dir + filename_decompressed])
                os.remove(globals.data_dir + filename_decompressed)
            except ftplib.error_perm:
                print "Error: cannot read file %s" % filename
                os.unlink(filename)
            else:
                print "***Downloaded*** %s " % filename

    f.quit()
    return

if __name__ == '__main__':
    globals.init()
    main()