#!/usr/bin/env python
# coding: utf-8
    
'''     
CTIO    

SDP: 2025-04-07
            
Synopsis: Read files in a directory and look for files of OBSTYPE 'dark'.
Sorts darks based on keywords COADDS and EXPCOADD and writes filenames with
the same value to a list.  Uses list to create master darks.
'''
import os
import sys
from astropy.io import fits
from astropy import wcs
from astropy.nddata import CCDData
import numpy as np
from glob import glob 
import shutil
from datetime import datetime

def add_leading_zero_fixed_length(integer_value, length):
    # Convert the integer to a string and prepend zeros to achieve the fixed length
    str_value = f"{integer_value:0{length}}"
    return str_value

def write_files_to_ascii_list(directory, keyword1, keyword2, keyword3, output_directory, index):

    file_lists = {}
    files = glob('%s/tc4n*fits' % (directory))
    sorted_files = sorted(files)
    for filename in sorted_files:

        with fits.open(filename, mode='readonly') as hdul:
            header = hdul[0].header
            pytrim = header.get('PYTRIM', 'False')
            
        if (pytrim == 'True'):

            #Just sort darks
            obskey = 'OBSTYPE'
            obsval = 'dark'
            if (header[obskey] == obsval):
                #print(file_path)
                # Check if the keywords exist in the header
                if keyword1 in header and keyword2 in header:
                    val1 = int(header[keyword1])
                    val2 = int(header[keyword2])
                    val3 = int(header[keyword3])
                    fixed_length = 3
                    value1 = add_leading_zero_fixed_length(val1, fixed_length)
                    fixed_length = 2
                    value2 = add_leading_zero_fixed_length(val2, fixed_length)
                    fixed_length = 2
                    value3 = add_leading_zero_fixed_length(val3, fixed_length)
                    key = f"list_dark_{value1}s_{value2}c_{value3}f"

                    #print(file_path)
                    file_list = file_lists.get(key, [])
                    file_list.append(filename)
                    file_lists[key] = file_list

    # Write file lists to ASCII text files
    for key, files in file_lists.items():
        output_file_path = os.path.join(output_directory, f"{key}.txt")
        with open(output_file_path, 'w') as output_file:
            for file_path in files:
                fpath = get_last_word_in_path(file_path)
                ofpath = get_last_word_in_path(output_file_path)
		#print("file_path:", file_path)
                #print("output_file_path:", output_file_path) 
                output_file.write(file_path + '\n')
                with open(logfile, "a") as f:
                    sys.stdout = f
                    print(f"{fpath} written to {ofpath}")
                    sys.stdout = sys.__stdout__

def files_cleanup(file_list_path, destination_directory):
    # Create destination directory if it doesn't exist
    os.makedirs(destination_directory, exist_ok=True)

    # Read file paths from the file into a list
    with open(file_list_path, 'r') as file:
        files_to_move = [line.strip() for line in file.readlines()]

    # Move each file to the destination directory
    for source_file in files_to_move:
        shutil.move(source_file, destination_directory)

    print("Files moved successfully!")

def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)

    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)

    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

def combine_dark_frames_from_list(file_list_path, output_filename):
    dark_frames = []
    dark_files = []

    with open(file_list_path, 'r') as file_list:
        fits_files_list = [line.strip() for line in file_list.readlines()]
        #print(fits_files_list)

    # Collect data from each dark frame
    for fits_file in fits_files_list:
        junk = get_last_word_in_path(fits_file)
        dark_files.append(junk)
        with fits.open(fits_file, mode='readonly') as hdul:
            data = hdul[0].data
            dark_frames.append(data)

    #Combine the dark frames (median or mean, depending on your preference)
    combined_dark = np.mean(dark_frames, axis=0)
    #combined_dark = np.median(dark_frames, axis=0)  
    # Change to np.mean if desired

    #print(fits_files_list[0])
    hdulist = fits.open(fits_files_list[0])
    header = hdulist[0].header
    #print(header)

    num_darks = len(dark_files)
    old_title = header['OBJECT']
    new_title = 'Combined ' + old_title
    header['OBJECT'] = new_title
    header['PROCTYPE'] = 'MasterCal'
    header['PRODTYPE'] = 'image'
    header['NCOMBINE'] = num_darks

    index_comb = 1
    limit_comb = num_darks + 1
    fixed_length = 3
    while index_comb < limit_comb:
        comb_suffix = add_leading_zero_fixed_length(index_comb, fixed_length)
        comb_keyword = 'IMCMB' + comb_suffix
        py_index = index_comb - 1
        header[comb_keyword] = dark_files[py_index]
        index_comb = index_comb + 1

    # Create a new HDU with the trimmed data and updated header
    new_hdu = fits.PrimaryHDU(data=combined_dark.data, header=header)

    # Write the new FITS file
    new_hdulist = fits.HDUList([new_hdu])
    new_hdulist.writeto(output_filename, overwrite=True)

    # Write the combined dark frame to a new FITS file
    #hdu = fits.PrimaryHDU(combined_dark)
    #hdul = fits.HDUList([hdu])
    #hdul.writeto(output_filename, overwrite=True)

    hdulist.close()
    new_hdulist.close()

#
# Begin
#
workdir = os.getcwd() + '/'

logfile = workdir + "SortCombDarks.log"

if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin SortCombDarks.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

num_detectors = 5
i = 1
while i < num_detectors:
    ext_dir = workdir + str(i) + '/'

    with open(logfile, "a") as f:
        sys.stdout = f
        print("Working in directory", ext_dir)
        sys.stdout = sys.__stdout__

#   Make output directory the same as the individual detector directory
    out_dir = ext_dir
    keyword1_to_filter = 'EXPCOADD'
    keyword2_to_filter = 'COADDS'
    keyword3_to_filter = 'FSAMPLE'

    write_files_to_ascii_list(ext_dir, keyword1_to_filter, keyword2_to_filter, keyword3_to_filter, out_dir, i)
    i = i + 1

i = 1
while i < num_detectors:
    ext_dir = os.getcwd() + '/' + str(i) + '/'
    files = glob('%s/list_dark*.txt' % (ext_dir))
    sorted_files = sorted(files)
    num_files = len(files)
    j = 0
    print('Working in directory', ext_dir)
    while j < num_files:
        dark_frames_list_file = sorted_files[j]
        # Gets name of dark list to be combined
        # Strips path information from dark list
        # Strips string 'list_' from file name
        # Changes file extension from '.txt' to '.fits' for combined image
        # Adds FITS extension number to filename, for NEWFIRM [1-4]
        # Adds path to output filename
        # Output FITS filename should be unique
        # Move input files to other directory for safekeeping (TBD)
        filename = get_last_word_in_path(dark_frames_list_file)
        outfile_tmp1 = filename.replace('list_','')
        outfile_tmp2 = outfile_tmp1.replace('.txt', '_' + str(i) + '.fits')
        outfile = ext_dir + outfile_tmp2
        with open(logfile, "a") as f:
            sys.stdout = f
            print('Combining dark frames from', './' + str(i) + '/' + filename)
            print('Master dark written to:', './' + str(i) + '/' + outfile_tmp2)
            sys.stdout = sys.__stdout__
        combine_dark_frames_from_list(dark_frames_list_file, outfile)
        save_dir = ext_dir + 'Raw/'
        files_cleanup(dark_frames_list_file, save_dir)
        j = j + 1
    i = i + 1


time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, "a") as f:
    sys.stdout = f
    print("End SortCombDarks.py:", time)
    sys.stdout = sys.__stdout__
