#!/usr/bin/env python
# coding: utf-8
            
'''
CTIO 

SDP 2025-10-08

Synopsis: Prepare files for reduction

# Prepare for initial object image reductions
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

def process_fits_files_from_list(file_list_path, outfile_path):
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
            exptime = float(hdr['EXPTIME'])
            expcoadd = float(hdr['EXPCOADD'])
            coadds = int(hdr['COADDS'])
            fowler = int(hdr['FSAMPLE'])
            filt = str(hdr['FILTER'])
        line = (fname, obj, obstype, exptime, expcoadd, coadds, fowler, filt)
        data.append(line)
    #print(data)
    colnames = ['File', 'OBJECT', 'OBSTYPE', 'EXPTIME', 'EXPCOADD', 'COADDS', 'FSAMPLE', 'FILTER']
    table = Table(rows=data, names=colnames)
    table.write(outfile_path, format='ascii.fixed_width', overwrite=True)

# 
# Begin 
# 
workdir = os.getcwd() + '/' # Change to your directory 
#print(workdir)

logfile = workdir + "PrepRedx1.log"

if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin PrepRedx1.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

num_detectors = 5
j = 1
while j < num_detectors:
   ext_dir = workdir + str(j) + '/'
   with open(logfile, "a") as f:
       sys.stdout = f
       print("Extension directory:", ext_dir)
       sys.stdout = sys.__stdout__

   #print(ext_dir)

#   focus_files = glob('%s/tc4n_focus*fits' % (ext_dir))
#   sorted_focus_files = sorted(focus_files)
#   out_focus = ext_dir + 'focus.txt'
#   out_focus_sum = out_focus.replace('.txt', '_summary.txt')
#   short_focus = get_last_word_in_path(out_focus)
#   short_focus_sum = get_last_word_in_path(out_focus_sum)

   obj_files = glob('%s/tc4n_object*fits' % (ext_dir))
   sorted_obj_files = sorted(obj_files)
   out_obj = ext_dir + 'object.txt'
   out_obj_sum = out_obj.replace('.txt', '_summary.txt')
   short_obj = get_last_word_in_path(out_obj)
   short_obj_sum = get_last_word_in_path(out_obj_sum)

   dark_files = glob('%s/dark*.fits' % (ext_dir))
   sorted_dark_files = sorted(dark_files)
   out_dark = ext_dir + 'dark.txt'
   dark_sum = out_dark.replace('.txt', '_summary.txt')
   short_dark = get_last_word_in_path(out_dark)
   short_dark_sum = get_last_word_in_path(dark_sum)

   norm_flat_files = glob('%s/nflat*.fits' % (ext_dir))
   sorted_flat_files = sorted(norm_flat_files)
   out_flat = ext_dir + 'flat.txt'
   flat_sum = out_flat.replace('.txt', '_summary.txt')
   short_flat = get_last_word_in_path(out_flat)
   short_flat_sum = get_last_word_in_path(flat_sum)

   with open(logfile, "a") as f:
       sys.stdout = f
       print(f"Writing master dark files to extension directory {short_dark}")
       sys.stdout = sys.__stdout__
   write_to_text(sorted_dark_files, out_dark)
   with open(logfile, "a") as f:
       sys.stdout = f
       print(f"Writing master flat files to extension directory {short_flat}")
       sys.stdout = sys.__stdout__
   write_to_text(sorted_flat_files, out_flat)
   with open(logfile, "a") as f:
       sys.stdout = f
       print(f"Writing object files extension directory {short_obj}")
       sys.stdout = sys.__stdout__
   write_to_text(sorted_obj_files, out_obj)
#   with open(logfile, "a") as f:
#       sys.stdout = f
#       print(f"Writing focus files extension directory {short_focus}")
#       sys.stdout = sys.__stdout__
#   write_to_text(sorted_focus_files, out_focus)

   with open(logfile, "a") as f:
       sys.stdout = f
       print(f"Dark summary table written to extension directory {short_dark_sum}")
       sys.stdout = sys.__stdout__
   process_fits_files_from_list(out_dark, dark_sum)
   with open(logfile, "a") as f:
       sys.stdout = f
       print(f"Flat summary table written to extension directory {short_flat_sum}")
       sys.stdout = sys.__stdout__
   process_fits_files_from_list(out_flat, flat_sum)
   with open(logfile, "a") as f:
       sys.stdout = f
       print(f"Object summary table written to extension directory {short_obj_sum}")
       sys.stdout = sys.__stdout__
   process_fits_files_from_list(out_obj, out_obj_sum)
#   with open(logfile, "a") as f:
#       sys.stdout = f
#       print(f"Focus summary table written to extension directory {short_focus_sum}")
#       sys.stdout = sys.__stdout__
#   process_fits_files_from_list(out_focus, out_focus_sum)

   j = j + 1
time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, "a") as f:
    sys.stdout = f
    print("End PrepRedx1.py:", time)
    sys.stdout = sys.__stdout__
