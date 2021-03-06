#!/usr/bin/env python3

# usage: wiiu_cdndownload.py <titleid>

import binascii
import os
import struct
import sys
from urllib.request import urlretrieve, urlopen

if len(sys.argv) == 1:
    print("wiiu_cdndownload.py <titleid>")
    print("Only the latest version can be downloaded right now.")
    sys.exit(1)

# things to not try and download cetk for
app_categories = {
    '0000',  # application
    '0002',  # demo
    '000C',  # DLC
}

tid = sys.argv[1].upper()

if len(tid) != 16:
    print("! Title ID is invalid length")
    print("wiiu_cdndownload.py <titleid>")
    print("Only the latest version can be downloaded right now.")
    sys.exit(1)

# http://stackoverflow.com/questions/8866046/python-round-up-integer-to-next-hundred
def roundup(x, base=64):
    return x if x % base == 0 else x + base - x % base

# some things used from
# http://stackoverflow.com/questions/13881092/download-progressbar-for-python-3
blocksize = 10*1024
def download(url, printprogress=False, outfile=None):
    #print(url)
    cn = urlopen(url)
    totalsize = int(cn.headers['content-length'])
    totalread = 0
    if not outfile:
        ct = b""
    while totalsize > totalread:
        toread = min(totalsize - totalread, blocksize)
        co = cn.read(toread)
        totalread += toread
        if printprogress:
            percent = min(totalread * 1e2 / totalsize, 1e2)
            print("\r- %5.1f%% %*d / %d" % (
                  percent, len(str(totalsize)), totalread, totalsize), end='')
        if outfile:
            outfile.write(co)
        else:
            ct += co
    if printprogress:
        print("")
    if not outfile:
        return ct

sysbase = "http://nus.cdn.c.shop.nintendowifi.net/ccs/download/" + tid
appbase = "http://ccs.cdn.c.shop.nintendowifi.net/ccs/download/" + tid

os.makedirs(tid, exist_ok=True)
base = appbase
if tid[4:8] not in app_categories:
    base = sysbase
    print("Downloading CETK...")
    with open(tid + "/title.tik", "wb") as f:
        download(base + "/cetk", False, f)

print("Downloading TMD...")
tmd = download(base + "/tmd")
contents = []
count = struct.unpack(">H", tmd[0x1DE:0x1E0])[0]
print("Contents: {}".format(count))
contentsize = 0
for c in range(count):
    contents.append([
        # content ID
        binascii.hexlify(tmd[0xB04 + (0x30 * c):0xB04 + (0x30 * c) + 0x4]).decode('utf-8'),
        # content type
        struct.unpack(">H", tmd[0xB0A + (0x30 * c):0xB0A + (0x30 * c) + 0x2])[0],
        # content size
        struct.unpack(">Q", tmd[0xB0C + (0x30 * c):0xB0C + (0x30 * c) + 0x8])[0],
    ])
with open(tid + "/title.tmd", "wb") as f:
    f.write(tmd)

for c in contents:
    if os.path.isfile(tid + "/" + c[0] + ".app") and os.path.getsize(tid + "/" + c[0] + ".app") == c[2]:
        print("Skipping {}.app due to existing file with proper size".format(c[0]))
    else:
        print("Downloading: {}...".format(c[0]))
        with open(tid + "/" + c[0] + ".app", "wb") as f:
            download(base + "/" + c[0], True, f)
    if c[1] & 0x2:
        print("Downloading: {}.h3...".format(c[0]))
        with open(tid + "/" + c[0] + ".h3", "wb") as f:
            download(base + "/" + c[0] + ".h3", True, f)
