#!/usr/bin/env python
# coding: utf-8

'''
CTIO

SDP 2025-04-02

Synopsis: Prepare NEWFIRM data directory for reductions

Program starts in a NEWFIRM data directory and performs the following tasks:
(1) Copies all original data to  subdirectory "SAVE"
(2) Sanitizes file list so it will not work on files that have certain 
substrings such as "test", "junk", "temp", etc.
(3) Moves files that pass sanitizing to new filename of form:
c4n_<obstype>_####.fits
(4) For initial reduction purposes (i.e., dark, flat-field) we treat OBSTYPE
of "sky" and "standard" as "object".
(5) Removes any files that didn't pass sanitizing
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

from astropy.io import fits, ascii
from glob import glob
from astropy.table import Table, vstack
from datetime import datetime, timedelta

def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)

    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)

    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

def add_leading_zero(integer_value, fixed_length=7):
    # Convert the integer to a string and prepend zeros to achieve the fixed length
    str_value = f"{integer_value:0{fixed_length}}"
    return str_value

def filter_fits_files(files, keyword="OBJECT"):
    omit_keywords = {"junk", "jnk", "temp", "tmp", "test", "tst", "focus"}
#    omit_keywords = {"junk", "jnk", "temp", "tmp", "test", "tst", "diff"}
#    omit_keywords = {"diff"}
    pass_files = []

    for file in files:
        try:
            with fits.open(file) as hdul:
                header = hdul[0].header  # Read the primary HDU header
                value = header.get(keyword, "").lower()  # Get keyword value (default empty if missing)
                
                if not any(omit_word in value for omit_word in omit_keywords):  
                    pass_files.append(file)  # Keep only clean files

        except Exception as e:
            print(f"Skipping {file} due to error: {e}")  # Handle errors

    return pass_files

def filter_filename(allfiles):
#   omit_keywords = {"junk", "jnk", "temp", "tmp", "test", "tst", "diff", "zp", "focus"}
    omit_keywords = {"diff", "ajunk", "zp", "focus"}

    return [
        f for f in allfiles
        if os.path.isfile(os.path.join(workdir, f))  # Ensure it's a file, not a directory
        and not any(keyword in f.lower() for keyword in omit_keywords) # Filter keywords
        and f.endswith(".fits")
    ]

def remove_unwanted_files(directory):
    for filename in os.listdir(directory):
        if not filename.startswith("c4n") and filename.endswith(".fits"):  # Check if it does NOT start with "c4n"
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):  # Ensure it's a file
                os.remove(file_path)
                with open(logfile, "a") as f:
                    sys.stdout = f
                    print(f"Not processing: {filename}")
                    sys.stdout = sys.__stdout__


def parse_date_obs(date_obs):
    fmt = '%Y-%m-%dT%H:%M:%S.%f'

    try:
        return datetime.strptime(date_obs, fmt)

    except ValueError as e:
        # Check specifically for invalid seconds
        if "second must be in 0..59" in str(e):
            # Split date and time
            date_part, time_part = date_obs.split('T')

            # Separate fractional seconds if present
            if '.' in time_part:
                time_main, frac = time_part.split('.')
                frac = '.' + frac
            else:
                time_main = time_part
                frac = ''

            h, m, s = time_main.split(':')

            if s.startswith('60'):
                # Replace seconds with 59 so it parses
                corrected = f"{date_part}T{h}:{m}:59{frac}"
                dt = datetime.strptime(corrected, fmt)

                # Add one second to roll into next minute
                return dt + timedelta(seconds=1)

        # Re-raise if it's not the specific issue
        raise

#
# Begin
#
#workdir = '/Users/sean.points/data/NEWFIRM/UT20250211/'
workdir = os.getcwd() + '/'

logfile = workdir + "RenameFiles.log"

if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin RenameFiles.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

# Make directory to save raw data after file rename and before processing
savedir = workdir + 'SAVE/'
os.makedirs(savedir, exist_ok=True)

# Get list of all files
files = glob('%s/*.fits' % (workdir))
sorted_files = sorted(files)
#print(sorted_files)
num_files = len(sorted_files)

# Save Raw data
# Check to see if file has been processed or has already been saved
i = 0
while i < num_files:
    filename = sorted_files[i]
    infile = filename
    #print(infile)
    ofile = get_last_word_in_path(infile)
    outfile = savedir + ofile
    #print(outfile)
    if os.path.isfile(infile) and ofile.endswith(".fits"):
        with fits.open(infile) as hdul:
            header = hdul[0].header
            pyrename = header.get('PYRENAME', 'False')
            if (pyrename != 'True') and not os.path.exists(outfile):
                shutil.copy(infile, outfile)
                with open(logfile, "a") as f:
                    sys.stdout = f
                    print(f"Making copy of {infile}.")
                    sys.stdout = sys.__stdout__
            #else:
                #with open(logfile, "a") as f:
                    #sys.stdout = f
                    #print(f"{infile} has already been renamed or saved.")
                    #sys.stdout = sys.__stdout__
    i = i + 1

# Don't process filenames that contain "diff" or "ajunk".  Can add
# additional restrictions 
good_files = filter_filename(sorted_files)
gnum_files = len(good_files)

i = 0
clean_files = good_files
while i < gnum_files:
    filename = good_files[i]
    clean_files[i] = filename
    i = i + 1

i = 0
while i < gnum_files:
    filename = clean_files[i]
    infile = filename
    with fits.open(infile) as hdul:
        header = hdul[0].header
        obstype = header.get('OBSTYPE')
        date_obs = header.get('DATE-OBS', 'T')
        expnum = header.get('EXPNUM', 0)
        sexpnum = add_leading_zero(expnum, fixed_length=7)
        pyrename = header.get('PYRENAME', 'False')
        if ((date_obs != 'T') and (pyrename != 'True')):
            dt = parse_date_obs(date_obs)
            yy = dt.strftime('%y')
            mmdd = dt.strftime('%m%d')
            hhmmss = dt.strftime('%H%M%S')

            if (obstype == "dark"):
                outfile = workdir + 'c4n' + '_' + obstype + '_' + yy + mmdd + '_' + hhmmss + '_' + sexpnum + '.fits'
                with open(logfile, "a") as f:
                    sys.stdout = f
                    print("Moving", infile, "to", outfile)
                    sys.stdout = sys.__stdout__
                shutil.move(infile, outfile)

            if (obstype == "dflat"):
                outfile = workdir + 'c4n' + '_' + obstype + '_' + yy + mmdd + '_' + hhmmss + '_' + sexpnum + '.fits'
                with open(logfile, "a") as f:
                    sys.stdout = f
                    print("Moving", infile, "to", outfile)
                    sys.stdout = sys.__stdout__
                shutil.move(infile, outfile)

            if ((obstype == "Focus") or (obstype == "none")):
                obstype = "focus"
                outfile = workdir + 'c4n' + '_' + obstype + '_' + yy + mmdd + '_' + hhmmss + '_' + sexpnum + '.fits'
                with open(logfile, "a") as f:
                    sys.stdout = f
                    print("Moving", infile, "to", outfile)
                    sys.stdout = sys.__stdout__
                shutil.move(infile,outfile)

            if ((obstype == "object") or (obstype == "sky") or (obstype == "standard")):
                obstype = "object"
                outfile = workdir + 'c4n' + '_' + obstype + '_' + yy + mmdd + '_' + hhmmss + '_' + sexpnum + '.fits'
                with open(logfile, "a") as f:
                    sys.stdout = f
                    print("Moving", infile, "to", outfile)
                    sys.stdout = sys.__stdout__
                shutil.move(infile, outfile)

            origname = get_last_word_in_path(infile)
            newname = get_last_word_in_path(outfile)
            with fits.open(outfile, mode="update") as hdu:
                header = hdu[0].header
                hdu[0].header['ORIGNAME'] = (origname, 'Original name')
                hdu[0].header['PYNAME'] = (newname, 'Processing name')
                hdu[0].header['PYRENAME'] = ('True', 'RenameFiles.py Flag')
                hdu.flush()
        else:
            with open(logfile, "a") as f:
                sys.stdout = f
                print(f"Not processing: {infile}")
                sys.stdout = sys.__stdout__
    i = i + 1

checked_files = glob('%s/c4n*fits' % (workdir))
cnum_files = len(checked_files)

# Removes files in the current directory
# Files had unwanted string in filename or OBJECT keyword
remove_unwanted_files(workdir)
time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(logfile, "a") as f:
    sys.stdout = f
    print("Total number of FITS files:", num_files)
    print("FITS files with proper filenames:", gnum_files)
    print("FITS files with proper OBJECT and OBSTYPE keyword:", cnum_files)
    print("End CheckFiles.py:", time)
    sys.stdout = sys.__stdout__
