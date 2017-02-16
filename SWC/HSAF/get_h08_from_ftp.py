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
# data directory
# data_dir = "/mnt/DATA/geodata/HSAF/"

def main():
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
        datestr = ''.join(col[-1].split("_")[1:3]) #col[-1].split("_")[1] # ' '.join(line.split()[0:2])
        date = time.strptime(datestr, '%Y%m%d%H%M%S')
        datelist.append(date)
        filelist.append(col[-1])

    combo = zip(datelist, filelist)
    who = dict(combo)
    i = 0
    for key in sorted(who.iterkeys(), reverse=True):
        filename = who[key]
        if filename.endswith('.tmp'):
            continue
        print "%s: %s" % (key, who[key])
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
            i += 1
        except ftplib.error_perm:
            print "Error: cannot read file %s" % filename
            os.unlink(filename)
        else:
            print "***Downloaded*** %s " % filename
        if i == 20:
            return

    f.quit()
    return

if __name__ == '__main__':
    globals.init()
    main()