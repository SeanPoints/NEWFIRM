#!/usr/bin/env python
# coding: utf-8

import shutil
import sys
import os
from glob import glob
from astropy.io import fits
from datetime import datetime

def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)

    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)

    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

workdir = os.getcwd()
swarp_dir = workdir + '/' + 'Skysub/'
logfile = workdir + '/' + 'MakeMasks.log'

if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin MakeMasks.py:", time)
    print("Working directory:", workdir)
    print("SWarp directory:", swarp_dir)
    sys.stdout = sys.__stdout__

filelist = sorted(glob('%s/*.sw.fits' % (swarp_dir)))

for file in filelist:
    maskfile = file.replace("sw.fits", "mask.fits")
    #print(file, maskfile) 
    shutil.copy(file, maskfile)

    ofile = get_last_word_in_path(maskfile)
    with open(logfile, 'a') as f:
        sys.stdout = f
        print(f"Making mask file: {ofile}")
        sys.stdout = sys.__stdout__

    hdul = fits.open(maskfile, mode="update")
    data = hdul[0].data
    data[data < 0] = 1
    data[data > 0] = 1
    hdul.flush()
    hdul.close()

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, 'a') as f:
    sys.stdout = f
    print("End MakeMasks.py:", time)
    sys.stdout = sys.__stdout__
