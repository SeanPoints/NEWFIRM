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
outfile = swarp_dir + 'run_scamp.sh'

files = glob('%s/sfd*.fits' % (swarp_dir))
sorted_files = sorted(files)

with open(outfile, 'w') as fout:

    for fitsfile in sorted_files:
        catfile = fitsfile.replace('fits','cat')
        newcat = get_last_word_in_path(catfile)

        cmd = (
            f"scamp {newcat} -c {wcs_path}default.scamp "
            f"-ASTREF_CATALOG GAIA-EDR3"
            )

        fout.write(cmd + '\n')
        os.chmod(outfile, 0o755)
