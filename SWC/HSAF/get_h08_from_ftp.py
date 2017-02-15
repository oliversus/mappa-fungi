import ftplib
import time
import os

HOST = 'ftphsaf.meteoam.it'

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
        datestr = col[-1].split("_")[1] # ' '.join(line.split()[0:2])
        date = time.strptime(datestr, '%Y%m%d')
        datelist.append(date)
        filelist.append(col[-1])

    combo = zip(datelist, filelist)
    who = dict(combo)

    for key in sorted(who.iterkeys(), reverse=True):
        print "%s: %s" % (key, who[key])
        filename = who[key]
        print "file to download is %s" % filename
        try:
            f.retrbinary('RETR %s' % filename, open(filename, 'wb').write)
        except ftplib.error_perm:
            print "Error: cannot read file %s" % filename
            os.unlink(filename)
        else:
            print "***Downloaded*** %s " % filename
        return

    f.quit()
    return

if __name__ == '__main__':
    main()

# ftp = FTP(HOST)
# ftp.login()
# files = ftp.dir()
# ftp.quit()