#!/usr/bin/env python
# coding: utf-8

'''
CTIO

SDP: 2025-04-05

Synopsis: Trim FITS image and writes to new file.  Original data saved.

Program starts in a NEWFIRM data directory and performs the following tasks:
(1) Moves to detector subdirectories
(2) Reads FITS file
(3) Removes the overscan region
(4) Writes new FITS file
(5) Updates the FITS header that trimming has been done
(6) Saves original data to new directory

'''
from astropy.io import fits
from astropy import wcs
from astropy.nddata import CCDData
import numpy as np
from glob import glob
import sys
import os
import ccdproc as ccdp
import shutil
from datetime import datetime

def ensure_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")

def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)

    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)

    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

def trim_and_save_fits(input_path, output_path):
#   Open the FITS file
    with fits.open(input_path) as hdu:
        header = hdu[0].header
        data = hdu[0].data
        pytrim = header.get('PYTRIM', 'False')

    if (pytrim != 'True'):

        trimmed_data = data[:, :2048]
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ccdsec_text = "[1:" + str(trimmed_data.shape[0]) + ",1:" + str(trimmed_data.shape[1]) + "]"
        trim_text = time + " Trim is " + ccdsec_text

#       Update the header with new dimensions
        header['NAXIS1'], header['NAXIS2'] = trimmed_data.shape
        header['CCDSEC'] = (ccdsec_text)
        header['TRIM'] = (trim_text)
        header['PYTRIM'] = ('True', 'TrimImage.py Flag')
    
        new_hdu = fits.PrimaryHDU(data=trimmed_data, header=header)

#       Save to new FITS file
        new_hdu.writeto(output_path, overwrite=True)

    else:
        print(f"{input_path} is already trimmed.")
#
# Begin
#
workdir = os.getcwd() + '/' 

logfile = workdir + "TrimImage.log"

if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin TrimImage.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

# Move through individual detector directories 1-4
i = 1
num_detectors = 5
while i < num_detectors:

    ext_dir = workdir + str(i) +'/'

    with open(logfile, "a") as f:
        sys.stdout = f
        print("Trimming images in", ext_dir)
        sys.stdout = sys.__stdout__
    files = glob('%s/c4n*.fits' % (ext_dir))

    sorted_files = sorted(files)
    num_files = len(sorted_files)

    if (num_files > 0):
        j = 0
        while j < num_files:
            infile = sorted_files[j]
            filename = get_last_word_in_path(infile)
            newfilename = 't' + filename
            with open(logfile, "a") as f:
                sys.stdout = f
                print(f"Trimming file {filename}.")
                print(f"Trimmed file is {newfilename}.")
                sys.stdout = sys.__stdout__
            outfile = ext_dir + newfilename
            # Trim original image and save to file
            trim_and_save_fits(infile,outfile)
            # Save original data
            save_dir = ext_dir + 'Raw/'
            ensure_directory_exists(save_dir)
            source_file = infile
            destination_directory = save_dir
            #os.makedirs(destination_directory, exist_ok=True)
            shutil.move(source_file, destination_directory)
        #
            j = j + 1
    else:
        with open(logfile, "a") as f:
            sys.stdout = f
            print(f"No files to trim in {ext_dir}.")
            sys.stdout = sys.__stdout__
    i = i + 1

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, "a") as f:
    sys.stdout = f
    print("End TrimImage.py:", time)
    sys.stdout = sys.__stdout__
