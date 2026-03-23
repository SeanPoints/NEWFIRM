#!/usr/bin/env python
# coding: utf-8

import sys
import shutil
import os
import stat
import subprocess
from astropy.io import fits
from datetime import datetime
import numpy as np
from glob import glob

def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)
    
    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)

    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

# directory containing FITS files

workdir = os.getcwd()
swarp_dir = workdir + '/' + 'Skysub/'
wcs_path = '/Users/sean.points/data/NEWFIRM/WCS/'
outfile = swarp_dir + 'run_swarp.sh'

files = glob('%s/sfd*_1.fits' % (swarp_dir))
sorted_files = sorted(files)

with open(outfile, 'w') as fout:

    for fitsfile in sorted_files:
        infile = fitsfile.replace('_1.fits','_*.fits')
        swarpfile = fitsfile.replace('_1.fits','.sw.fits')

        cmd = (
            f"swarp {infile} -c {wcs_path}default.swarp -IMAGEOUT_NAME "
            f"{swarpfile} -WEIGHTOUT_NAME /dev/null"
            )

        fout.write(cmd + '\n')
        os.chmod(outfile, 0o755)
