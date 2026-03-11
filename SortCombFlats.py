#!/usr/bin/env python
# coding: utf-8
    
'''     
CTIO    

SDP: 2025-04-07
            
Synopsis: Read files in a directory and look for files of OBSTYPE 'dflat'.
Sorts flats based on keywords FILTER and DFLAMPVA and writes filenames with
the same value to a list.  Uses list to create mast flat "on" and "off" for 
each filter used.  Creates master flat and master normalized flat.
'''
import os
import sys
from astropy.io import fits
from datetime import datetime
from astropy import wcs
from astropy.nddata import CCDData
import numpy as np
from glob import glob
import ccdproc as ccdp
import shutil
from scipy import stats
from pathlib import Path

def add_leading_zero_fixed_length(integer_value, length):
    str_value = f"{integer_value:0{length}}"
    return str_value

def files_cleanup(file_list_path, destination_directory):
    # Create destination directory if it doesn't exist
    os.makedirs(destination_directory, exist_ok=True)

    # Read file paths from the file into a list
    with open(file_list_path, 'r') as file:
        files_to_move = [line.strip() for line in file.readlines()]

    # Move each file to the destination directory
    for source_file in files_to_move:
        shutil.move(source_file, destination_directory)

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

def write_files_to_ascii_list(directory, output_directory, cal_path, index, logfile):
    files = glob('%s/tc4n_dflat_*.fits' % (directory))
    sorted_files = sorted(files)
    num_dflats = len(sorted_files)

    # Check that no flat lists exist
    # Delete if they do exist
    flatlists = glob('%s/list_flat_*.txt' % (directory))
    num_list = len(flatlists)
    flatlist_index = 0
    #print(flatlists)
    while flatlist_index < num_list:
        os.remove(flatlists[flatlist_index])
        flatlist_index = flatlist_index + 1


    i = 0
    while i < num_dflats:
        obs_file = sorted_files[i]
        with fits.open(obs_file, mode='readonly') as hdul:
            header = hdul[0].header
            pytrim = header.get('PYTRIM', 'False')

        if (pytrim == 'True'):
            base_name = os.path.splitext(obs_file)[0]
            object_file = os.path.basename(obs_file)
            #print(object_file)
            detector = index
            with fits.open(obs_file, mode='readonly') as hdul:
                data = hdul[0].data
                flattened_data = data.flatten()
                header = hdul[0].header
                filter = header['FILTER']
                lamp_intensity = header['DFLAMPVA']
                title = header['OBJECT']
                cal_prefix = 'flat_'
                cal_filter = filter
                if lamp_intensity > 0. :
                    cal_status = 'on'
                else:
                    cal_status = 'off'

        listname = "list_flat_" + filter + "_" + cal_status + ".txt"
        listfile = directory + listname
        
        file_path = Path(listfile)
        if not file_path.exists():
            file_path.touch()  # This creates the file

        with open(logfile, "a") as f:
            sys.stdout = f
            print('Adding', object_file, 'to', listname)
            sys.stdout = sys.__stdout__

        with open(listfile, "a") as f:
            f.write(obs_file + '\n')

        i = i + 1	    

def combine_flats_mode_from_list(on_list, on_output, off_list, off_output, sub_output, norm_output):
    on_frames = []
    off_frames = []
    on_mode_val = []
    on_scale_val = []
    off_mode_val = []
    off_scale_val = []
    mon_frames = []
    moff_frames = []
    files_on = []
    files_off = []

    ###
    ### Flat Lamp=On Block
    ###
    # Collects the flats with Lamps=On for filters
    with open(on_list, 'r') as file_list_on:
        fits_files_list_on = [line.strip() for line in file_list_on.readlines()]

    # Collect data from each flat-on frame
    # Use stats to get mode of each flat
    #

    for fits_file_on in fits_files_list_on:
        #print('=====')
        #print('File on')
        junk = get_last_word_in_path(fits_file_on)
        files_on.append(junk)

        with fits.open(fits_file_on, mode='readonly') as hdul:
            data = hdul[0].data
            z = stats.mode(data, axis=None, keepdims=False)
            on_mode_val.append(z[0])
            on_frames.append(data)

    #print(len(files_on), files_on)

    num_on_flats = len(on_mode_val)
    i = 0
    # Sets first flat in list to be the scale normalization
    norm_on = on_mode_val[0]
    while i < num_on_flats:
        # Calculate scale factor and scales the flats
        on_scale_val.append(norm_on / on_mode_val[i])
        mon_frames.append(on_frames[i] * on_scale_val[i])
        i = i + 1

    #Combine the flat frames (median or mean, depending on your preference)
    combined_flat_on = np.median(mon_frames, axis=0)
    #combined_flat_on = np.mean(mon_frames, axis=0)  

    # Gets the header information for the first record in file 'fits_files_list_on' to use as header of combined flat
    hdulist = fits.open(fits_files_list_on[0])
    header = hdulist[0].header
    # Gets information of images to put into combined header
    header = hdulist[0].header
    old_title = header['OBJECT']
    new_title = 'Combined ' + old_title
    header['OBJECT'] = new_title
    header['PROCTYPE'] = 'MasterCal'
    header['PRODTYPE'] = 'image'
    header['NCOMBINE'] = num_on_flats


    #print(num_on_flats)
    index_comb = 1
    limit_comb = len(files_on) + 1
    fixed_length = 3
    while index_comb < limit_comb:
        comb_suffix = add_leading_zero_fixed_length(index_comb, fixed_length)
        comb_keyword = 'IMCMB' + comb_suffix
        py_index = index_comb - 1
        #print(index_comb, comb_keyword, files_on[py_index])
        header[comb_keyword] = files_on[py_index]
        index_comb = index_comb + 1

    # Create a new HDU with the combined data and updated header
    new_hdu = fits.PrimaryHDU(data=combined_flat_on.data, header=header)

    # Write the new FITS file
    new_hdulist = fits.HDUList([new_hdu])
    new_hdulist.writeto(on_output, overwrite=True)

    hdulist.close()
    new_hdulist.close()

    ### Flat Lamp=Off Block

    # Collect data from each flat-off frame
    with open(off_list, 'r') as file_list_off:
        fits_files_list_off = [line.strip() for line in file_list_off.readlines()]
        #print(fits_files_list)
	
    # Collect data from each flat-off frame
    for fits_file_off in fits_files_list_off:
        #print('=====')
        #print('File off')
        junk = get_last_word_in_path(fits_file_off)
        files_off.append(junk)
        with fits.open(fits_file_off, mode='readonly') as hdul:
            data = hdul[0].data
            y = stats.mode(data, axis=None, keepdims=False)
            off_mode_val.append(y[0])
            off_frames.append(data)

    #print(len(files_off), files_off)

    num_off_flats = len(off_mode_val)
    i = 0
    # Sets first flat in list to be the scale normalization
    norm_off = off_mode_val[0]
    while i < num_off_flats:
        # Calculate scale factor and scales the flats
        off_scale_val.append(norm_off / off_mode_val[i])
        moff_frames.append(off_frames[i] * off_scale_val[i])
        i = i + 1

    #Combine the flat frames (median or mean, depending on your preference)
    combined_flat_off = np.median(moff_frames, axis=0)
    #combined_flat_off = np.mean(moff_frames, axis=0)  
    # Change to np.mean if desired

    # Gets the header information for the first record in file 'fits_files_list_off' to use as header of combined flat
    hdulist = fits.open(fits_files_list_off[0])
    header = hdulist[0].header
    old_title = header['OBJECT']
    new_title = 'Combined ' + old_title
    header['OBJECT'] = new_title
    header['PROCTYPE'] = 'MasterCal'
    header['PRODTYPE'] = 'image'
    header['NCOMBINE'] = num_off_flats

    #print(num_off_flats)
    index_comb = 1
    limit_comb = len(files_off) + 1
    fixed_length = 3
    while index_comb < limit_comb:
        comb_suffix = add_leading_zero_fixed_length(index_comb, fixed_length)
        comb_keyword = 'IMCMB' + comb_suffix
        py_index = index_comb - 1
        #print(index_comb, comb_keyword, files_off[py_index])
        header[comb_keyword] = files_off[py_index]
        index_comb = index_comb + 1

    # Create a new HDU with the combined off data and updated header
    new_hdu = fits.PrimaryHDU(data=combined_flat_off.data, header=header)

    # Write the new FITS file
    new_hdulist = fits.HDUList([new_hdu])
    new_hdulist.writeto(off_output, overwrite=True)

    hdulist.close()
    new_hdulist.close()

    ### Subtract Flat Lamp=Off from Flat Lamp=On (Flat_sub = Flat_on - Flat_off)

    # Open the files
    file1 = fits.open(on_output)
    file2 = fits.open(off_output)

    # Subtract the data arrays
    sub_data = file1[0].data - file2[0].data

    # Get the header from the master flat_on file to copy to the subtracted file
    hdulist = (file1)
    header = hdulist[0].header
    old_title = header['OBJECT']
    tmp_title = old_title[:-3]
    new_title = 'Subtracted ' + tmp_title
    header['OBJECT'] = new_title
    header['FLATINFO'] = 'Difference between on and off domeflat'

    # Create a new FITS HDU with the result data
    new_hdu = fits.PrimaryHDU(data=sub_data.data, header=header)

    # Create a new FITS file and save the result
    new_hdulist = fits.HDUList([new_hdu])
    new_hdulist.writeto(sub_output, overwrite=True)

    # Close the input files
    file1.close()
    file2.close()
    hdulist.close()
    new_hdulist.close()

    ### Normalize the subtracted flat using the media value of the array


    file1 = fits.open(sub_output)
    ndata = file1[0].data
    median = np.median(ndata)
    normalized_data = ndata/median
    formatted_median = f"{median:9.2f}"

    # Get the header information from the subtracted flat to place into the normalized flat
    hdulist = (file1)
    header = hdulist[0].header
    old_title = header['OBJECT']
#    tmp_title = old_title[:-3]
    new_title = 'Normalized ' + old_title
    header['OBJECT'] = new_title
    header['FLATNORM'] = (formatted_median, 'Flat normalization factor')

    # Create a new FITS file for the normalized flat
    new_hdu = fits.PrimaryHDU(data=normalized_data.data, header=header)
    new_hdulist = fits.HDUList([new_hdu])
    new_hdulist.writeto(norm_output, overwrite=True)
    file1.close()
    hdulist.close()
    new_hdulist.close()


#
# Begin
#

workdir = os.getcwd() + '/'
#workdir = '/Users/sean.points/data/NEWFIRM/UT20250211/'
calpath_root = '/Users/sean.points/data/NEWFIRM/CALS/'

logfile = workdir + 'SortCombFlats.log'

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, "w") as f:
    sys.stdout = f
    print("Begin SortCombFlats.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

    num_detectors = 5
i = 1
while i < num_detectors:
    ext_dir = workdir + str(i) + '/'
    out_dir = ext_dir
    cal_dir = calpath_root + str(i) + '/'
    write_files_to_ascii_list(ext_dir, out_dir, cal_dir, i, logfile)
    i = i + 1


filters = ['JX', 'HX', 'KXs', 'J1', '1066', '1187', '1644', '2096', '2124', '2168']
#print(filters)
num_filters = len(filters)
k = 0
while k < num_filters:
    i = 1
    while i < num_detectors:
        ext_dir = workdir + str(i) + '/'
        #print(ext_dir)
        files_on_list = ext_dir + 'list_flat_' + filters[k] + '_on.txt'
        files_off_list = ext_dir + 'list_flat_' + filters[k] + '_off.txt'
        filename_on = get_last_word_in_path(files_on_list)
        filename_off = get_last_word_in_path(files_off_list)
        #print(files_on_list, files_off_list)
        #print('Working in directory', ext_dir)
        # Gets name of flat list to be combined
        # Strips path information from flat list
        # Strips string 'list_' from file name
        # Changes file extension from '.txt' to '.fits' for combined image
        # Adds FITS extension number to filename, for NEWFIRM [1-4]
        # Adds path to output filename
        # Output FITS filename should be unique
        # Move input files to other directory for safekeeping (TBD)
        if (os.path.exists(files_on_list) and os.path.exists(files_off_list)):
            filename_on = get_last_word_in_path(files_on_list)
            file_on_tmp1 = filename_on.replace('list_','')
            file_on_tmp2 = file_on_tmp1.replace('.txt', '_' + str(i) + '.fits')
            file_on = ext_dir + file_on_tmp2
            filename_off = get_last_word_in_path(files_off_list)
            file_off_tmp1 = filename_off.replace('list_','')
            file_off_tmp2 = file_off_tmp1.replace('.txt', '_' + str(i) + '.fits')
            file_off = ext_dir + file_off_tmp2
            file_sub = file_on.replace('_on','')
            file_norm = file_sub.replace('flat', 'nflat')

            file_sub_tmp = get_last_word_in_path(file_sub)
            file_norm_tmp = get_last_word_in_path(file_norm)

            with open(logfile, "a") as f:
                sys.stdout = f
                print('Combining on flat frames from', filename_on)
                print('Master on flat written to:', file_on_tmp2)
                print('Combining off flat frames from', filename_off)
                print('Master off flat written to:', file_off_tmp2)
                print('Master on-off flat written to:', file_sub_tmp)
                print('Master normalized flat written to:', file_norm_tmp)
                sys.stdout = sys.__stdout__
            combine_flats_mode_from_list(files_on_list, file_on, files_off_list, file_off, file_sub, file_norm)
            all_trimmed_flats = glob('%s/tc4n_dflat*fits' % (ext_dir))
            save_dir = ext_dir + 'Raw/'
            files_cleanup(files_on_list, save_dir)
            files_cleanup(files_off_list, save_dir)
        else:
            with open(logfile, "a") as f:
                sys.stdout = f
                print('Filename(s)', files_on_list, 'and/or', files_off_list, 'do(es) not exist')
                sys.stdout = sys.__stdout__
        i = i + 1
    k = k + 1


time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
with open(logfile, "a") as f:
    sys.stdout = f
    print("End SortCombFlats.py:", time)
    sys.stdout = sys.__stdout__
