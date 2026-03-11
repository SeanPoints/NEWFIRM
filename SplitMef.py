#!/usr/bin/env python
# coding: utf-8

'''
CTIO

SDP 2025-04-03

Synopsis: Splits NEWFIRM MEF into separate files and directories, based upon
extension number.

Program starts in a NEWFIRM data directory and performs the following tasks:
(1) Reads MEF files in directory
(2) Creates subdirectories for each detector, 1-4
(3) Splits MEF files into individual FITS files
(4) Moves split data into corresponding detector directory
(5) Filenames of split data are:
c4n_<obstype>_####_<detector_number>.fits

'''
#
# SplitMef.py
#
import argparse
import os
import sys
import warnings
import re
import shutil
import numpy as np
import timeit
import time
import multiprocessing
import logging
#import astropy.io.fits

from astropy.io import fits, ascii
from glob import glob
from astropy.table import Table, vstack
from datetime import datetime


def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)
    
    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)
    
    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

def remove_file_extension(filename):
    return os.path.splitext(filename)[0]

def ensure_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")

def extract_mef_ext(input_path, output_path, n):

    with fits.open(input_path, mode='update') as hdu:
        primary_header = hdu[0].header
        if not primary_header.get('PYSPLIT', False):
            primary_header['PYSPLIT'] = ('True', 'SplitMef.py Flag')

    with fits.open(input_path, mode='readonly') as hdu:
        primary_header   = hdu[0].header
        extension_data   = hdu[n].data
        extension_header = hdu[n].header
        extension_header += primary_header

    fits.writeto(output_path, extension_data, extension_header,
                            output_verify='fix', overwrite=True)

workdir = os.getcwd() + '/'
file_extension = '.fits'
num_detectors = 5

logfile = workdir + "SplitMef.log"

if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin SplitMef.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

#print(workdir)
#i = 1
all_files = glob('%s/c4n*.fits' % (workdir))
num_all_files = len(all_files)

focus_files = glob('%s/c4n*focus*.fits' % (workdir)) 
n_focus = len(focus_files)
dark_files = glob('%s/c4n*dark*.fits' % (workdir))
n_dark = len(dark_files)
dflat_files = glob('%s/c4n*dflat*.fits' % (workdir))
n_dflat = len(dflat_files)
obj_files = glob('%s/c4n*object*.fits' % (workdir))
n_obj = len(obj_files)

files = dark_files + dflat_files + obj_files
#files = dark_files + dflat_files + obj_files + focus_files

sorted_files = sorted(files)

num_files = len(sorted_files)

j = 0
while j < num_files:
#   print('Splitting MEF file:', sorted_files[j])
#   Just to remove path from filename for output log
    tmpfile = get_last_word_in_path(sorted_files[j])
    with fits.open(sorted_files[j]) as hdul:
        header = hdul[0].header
        object_name = header.get('OBJECT') 
        pysplit = header.get('PYSPLIT', 'False')

    if (pysplit != 'True'):

        with open(logfile, "a") as f:
            sys.stdout = f
            print("Splitting MEF file:", tmpfile, "-", object_name)
            sys.stdout = sys.__stdout__

#   Make this NEWFIRM specific and cycle through extensions 1-4
#   Change num_detectors for other MEF files
        i = 1
        while i < num_detectors:
#   Remove ".fits" from file name    
            tfile = remove_file_extension(sorted_files[j])
#   Remove path from filename
            ttfile = get_last_word_in_path(tfile)
#   Set output directory to be working directory + detector number
            outdir = workdir + str(i) +'/'
#           print(outdir)
#   Set output filename to be original filename + "_<num_detector>"
            outfile = outdir + ttfile + '_' + str(i) + '.fits'
#           print(outfile)
            ensure_directory_exists(outdir)
            extract_mef_ext(sorted_files[j], outfile, i)
            i = i + 1
    else: 
        print(f"{tmpfile} has already been split into its extensions")
    j = j + 1

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, "a") as f:
    sys.stdout = f
    print("===============================================================================")
    print("Total number of FITS files:", num_all_files)
    print("Total number of dark files:", n_dark)
    print("Total number of dflat files:", n_dflat)
    print("Total number of focus files:", n_focus)
    print("Total number of object files:", n_obj)
    print("Focus images not processed.")
    print("Total number of processed images:", num_files)
    print("===============================================================================")
    print("End SplitMef.py:", time)
    sys.stdout = sys.__stdout__
