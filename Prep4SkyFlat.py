#!/usr/bin/env python
# coding: utf-8
            
'''
CTIO 

SDP 2025-10-08

Synopsis: Prepare files for sky-flat reduction

# Prepare for object image reductions
# Read object files in data directory and print to list with FITS keywords
# EXPTIME, EXPCOADD, COADDS, FILTER
# Read combined darks and select same FITS keywords as above and write 
# output to ascii file
# Read combined, normalized flats, select same FITS keywords, and write 
# output to ascii file
'''

import sys
import warnings
import re
import os
import shutil
import numpy as np
import timeit
import time
import multiprocessing
import logging

from astropy.io import fits
from glob import glob
from astropy.table import Table
from datetime import datetime
            
def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)

    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)

    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

def write_to_text(file_paths, output_file):
    with open(output_file, 'w') as file:
        for path in file_paths:
            file.write(path + '\n')

def process_fits_files_from_list(tdate, file_list_path, outfile_path):
    #print(file_list_path)
    #print(outfile_path)
    data = []
    with open(file_list_path, 'r') as file_list:
        fits_file_list = [line.strip() for line in file_list.readlines()]
        #print(len(fits_file_list))
        #print(fits_file_list)
    for fits_file in fits_file_list:
        fname = get_last_word_in_path(fits_file)
        #print(fits_file)
        #print(fname)
        with fits.open(fits_file) as hdul:
            hdr = hdul[0].header
            obj = str(hdr['OBJECT'])
            obstype = str(hdr['OBSTYPE'])
            if (obstype == "standard"):
                obstype == "object"
#            if (obstype == "focus"):
#                obstype == "object"
            exptime = float(hdr['EXPTIME'])
            expcoadd = float(hdr['EXPCOADD'])
            coadds = int(hdr['COADDS'])
            fowler = int(hdr['FSAMPLE'])
            filt = str(hdr['FILTER'])
            ra = float(hdr['CRVAL1'])
            dec = float(hdr['CRVAL2'])
            date_obs = str(hdr['DATE-OBS'])
            dt = datetime.strptime(date_obs, "%Y-%m-%dT%H:%M:%S.%f")
            caldate = dt.date()
            delta_days = (caldate - tdate).days
            tdec_hour = float((dt.hour + dt.minute / 60. + dt.second / 3600.) + (delta_days * 24) )
            dec_hour = round(tdec_hour, 6)
        line = (fname, obj, obstype, exptime, expcoadd, coadds, fowler, filt, date_obs, dec_hour, ra, dec)
        data.append(line)
    #print(data)
    colnames = ['File', 'OBJECT', 'OBSTYPE', 'EXPTIME', 'EXPCOADD', 'COADDS', 'FSAMPLE', 'FILTER', 'DATE-OBS', 'UT', 'RA', 'DEC']
    table = Table(rows=data, names=colnames)
    table.sort('UT')
    table.write(outfile_path, format='ascii.fixed_width', overwrite=True)

# 
# Begin 
# 
workdir = os.getcwd() # Change to your directory 
path_components = workdir.split(os.sep)
last = path_components[-1]
#print(workdir)

logfile = workdir + '/' + 'Prep4SkyFlat.log'

if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin Prep4SkyFlat.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

if last.startswith("UT") and len(last) == 10:
    ymd = last[2:]
    odate = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
    #print(odate)
    tmpdate = datetime.strptime(odate, "%Y-%m-%d")
    tdate = tmpdate.date()

num_detectors = 5
j = 1
while j < num_detectors:
   ext_dir = workdir + '/' + str(j) + '/'
   with open(logfile, "a") as f:
       sys.stdout = f
       print("Extension directory:", ext_dir)
       sys.stdout = sys.__stdout__

   #print(ext_dir)

#   obj_files = glob('%s/fdtc4n_object*fits' % (ext_dir))
   obj_files = glob('%s/fdtc4n_*.fits' % (ext_dir))
   sorted_obj_files = sorted(obj_files)
   out_obj = ext_dir + 'sky_object.txt'
   out_obj_sum = out_obj.replace('.txt', '_summary.txt')
   short_obj = get_last_word_in_path(out_obj)
   short_obj_sum = get_last_word_in_path(out_obj_sum)

   with open(logfile, "a") as f:
       sys.stdout = f
       print(f"Writing object files for sky in extension directory {short_obj}")
       sys.stdout = sys.__stdout__

   write_to_text(sorted_obj_files, out_obj)

   with open(logfile, "a") as f:
       sys.stdout = f
       print(f"Object summary table written to extension directory {short_obj_sum}")
       sys.stdout = sys.__stdout__
   process_fits_files_from_list(tdate, out_obj, out_obj_sum)

   j = j + 1
time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, "a") as f:
    sys.stdout = f
    print("End Prep4SkyFlat.py:", time)
    sys.stdout = sys.__stdout__
