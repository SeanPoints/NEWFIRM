#!/usr/bin/env python
# coding: utf-8

'''
CTIO

Synopsis: Finds appropriate master dark and master flat and applies the 
correction to the object data
'''
import os
import shutil
from glob import glob
from astropy.io import fits
from astropy.table import Table
import sys
from datetime import datetime
from astropy import wcs
from astropy.nddata import CCDData
import numpy as np
import ccdproc as ccdp
import shutil
from scipy import stats
from pathlib import Path

def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)

    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)

    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

def files_cleanup(ext_dir, save_dir):
    # Create destination directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)

    for filename in os.listdir(ext_dir):
        if filename.startswith("tc4n") and filename.endswith(".fits"):
            src = os.path.join(ext_dir, filename)
            dst = os.path.join(save_dir, filename)
            shutil.move(src, dst)


    for filename in os.listdir(ext_dir):
        if filename.startswith("dtc4n") and filename.endswith(".fits"):
            src = os.path.join(ext_dir, filename)
            dst = os.path.join(save_dir, filename)
            shutil.move(src, dst)

    print("Files moved successfully!")


def add_leading_zero_fixed_length(integer_value, length):
    # Convert the integer to a string and prepend zeros to achieve the fixed length
    str_value = f"{integer_value:0{length}}"
    return str_value

def find_matching_dark(obj_row, dark_data, ext_dir, cal_dir, index):
    coadds = obj_row['COADDS']
    expcoadd = obj_row['EXPCOADD']
    fsample = obj_row['FSAMPLE']
    exptime = obj_row['EXPTIME']

    match = dark_data[
        (dark_data['COADDS'] == coadds) &
        (dark_data['EXPCOADD'] == expcoadd) &
        (dark_data['FSAMPLE'] == fsample)
    ]
    if len(match) > 0:
        return ext_dir + match[0]['File'], 1.0

    val1 = int(expcoadd)
    val2 = int(coadds)
    val3 = int(fsample)
    fixed_length = 3
    value1 = add_leading_zero_fixed_length(val1, fixed_length)
    fixed_length = 2
    value2 = add_leading_zero_fixed_length(val2, fixed_length)
    fixed_length = 2
    value3 = add_leading_zero_fixed_length(val3, fixed_length)
    calname = f"dark_{value1}s_{value2}c_{value3}f_{index}.fits"
    #print(cal_dir + calname)
    full_cal = cal_dir + calname

    if os.path.exists(full_cal):
        #print("Match in:", cal_dir)
        #print("Match:", calname)
        return full_cal, 1.0

    subset = dark_data[
        (dark_data['COADDS'] == coadds) &
        (dark_data['FSAMPLE'] == fsample)
        ]
    if len(subset) > 0:
        closest = subset[np.argmin(np.abs(subset['EXPCOADD'] - expcoadd))]
        scale = expcoadd / closest['EXPCOADD']
        return ext_dir + closest['File'], scale

    subset = dark_data[dark_data['FSAMPLE'] == fsample]
    if len(subset) > 0:
        closest = subset[np.argmin(np.abs(subset['EXPCOADD'] - expcoadd))]
        scale = expcoadd / closest['EXPCOADD']
        return ext_dir + closest['File'], scale

    return 'No_match', 0.0   


def find_matching_flat(obj_row, flat_data, ext_dir, cal_dir, index):
    filt = obj_row['FILTER']

    match = flat_data[(flat_data['FILTER'] == filt)]
    if len(match) > 0:
        return ext_dir + match[0]['File']

    calname = f"nflat_{filt}_{index}.fits"
    full_cal = cal_dir + calname
    if os.path.exists(full_cal):
        #print("Match in:", cal_dir)
        #print("Match:", calname)
        return full_cal

    return 'No_match'   

def subtract_dark(obj_file, sub_file, ext_dir, dark_file, scale, bp_file):
    # Open the Object FITS file
    #print(ext_dir + obj_file)
    #print(ext_dir + sub_file)
    #print(dark_file)
    formatted_scale = f"{scale:.2f}"
    with fits.open(ext_dir + obj_file) as obj_hdu:
        obj_header = obj_hdu[0].header
        obj_data = obj_hdu[0].data
        darkcor = obj_header.get('DARKCOR', 'False')
        naxis1 = obj_header.get('NAXIS1', 0)
        naxis2 = obj_header.get('NAXIS2', 0)

    with fits.open(bp_file) as bp_hdu:
        bp_header = bp_hdu[0].header
        bp_data = bp_hdu[0].data

    #print(darkcor)

    if (os.path.exists(dark_file)):
        with fits.open(dark_file) as dark_hdu:
            dark_header = dark_hdu[0].header
            dark_data = dark_hdu[0].data
            scaled_dark_data = dark_data * scale
    else:
        scaled_dark_data = np.zeros((naxis2, naxis1), dtype=int)

    dfile = get_last_word_in_path(dark_file)
    bfile = get_last_word_in_path(bp_file)
    if (darkcor == 'False'):
        with open(logfile, "a") as f:
            sys.stdout = f
            print(f"Subtracting {dfile}*{scale} from {obj_file}.")
            print(f"Performing bad pixel correction with {bfile}.")
            print(f"Dark-subtracted file is {sub_file}.")
            sys.stdout = sys.__stdout__

        sub_data = (obj_data - scaled_dark_data) * bp_data

        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        bp_key = f"{time}; Bad pixel file is {bfile}."
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dark_key = f"{time}; Dark is {dfile}, scale is {formatted_scale}"
        #print(dark_key)
        obj_header['DARKCOR'] = (dark_key)
        obj_header['BADPIX'] = (bp_key)
        obj_header['PYDARK'] = ('True', 'DarkCorrect.py Flag')
    
        sub_hdu = fits.PrimaryHDU(data=sub_data, header=obj_header)
        sub_hdu.writeto(ext_dir + sub_file)
    else:
        with open(logfile, "a") as f:
            sys.stdout = f
            print(f"{obj_file} is already dark corrected.")
            sys.stdout = sys.__stdout__
        
def flat_correct(obj_file, fcor_file, ext_dir, flat_file):
    # Open the object FITS file
    with fits.open(ext_dir + obj_file) as obj_hdu:
        obj_header = obj_hdu[0].header
        obj_data = obj_hdu[0].data
        flatcor = obj_header.get('FLATCOR', 'False')

    # Open the flat FITS file
    with fits.open(flat_file) as flat_hdu:
        flat_header = flat_hdu[0].header
        flat_data = flat_hdu[0].data

    ffile = get_last_word_in_path(flat_file)
    if (flatcor == 'False'):
        with open(logfile, "a") as f:
            sys.stdout = f
            print(f"Flat-fielding {obj_file} with {ffile}.")
            print(f"Flat-fielded file is {fcor_file}.")
            sys.stdout = sys.__stdout__
    
        with np.errstate(divide='ignore', invalid='ignore'):
            fcor_data = obj_data / flat_data
            fcor_data[~np.isfinite(fcor_data)] = 0
        
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        flat_key = f"{time}; Flat is {ffile}."
        obj_header['FLATCOR'] = (flat_key)
        obj_header['PYFLAT'] = ('True', 'FlatCorrect.py Flag')

        fcor_hdu = fits.PrimaryHDU(data=fcor_data, header=obj_header)
        fcor_hdu.writeto(ext_dir + fcor_file)
    else:
        with open(logfile, "a") as f:
            sys.stdout = f
            print(f"{obj_file} is already flat-fielded.")
            sys.stdout = sys.__stdout__

###
# Start main program
###
workdir = os.getcwd() + '/'
calpath_root = '/Users/sean.points/data/NEWFIRM/CALS/'

logfile = workdir + 'DarkFlatCorrect.log'

if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin DarkFlatCorrect.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

num_detectors = 5
j = 1
while j < num_detectors:
    ext_dir =  workdir + str(j) + '/'
    cal_dir = calpath_root + str(j) + '/'
    
    with open(logfile, "a") as f:
        sys.stdout = f
        print("Extension directory:", ext_dir)
        print("Backup calibration directory:", cal_dir)
        sys.stdout = sys.__stdout__

    obj_tab = ext_dir + 'object_summary.txt'
    obj_data_tab = Table.read(obj_tab, format='ascii.fixed_width')
    objects = obj_data_tab[
        (obj_data_tab['OBSTYPE'] == 'object') |
        (obj_data_tab['OBSTYPE'] == 'sky') |
        (obj_data_tab['OBSTYPE'] == 'standard') 
        ]

    dark_tab = ext_dir + 'dark_summary.txt'
    dark_data_tab = Table.read(dark_tab, format='ascii.fixed_width')

    flat_tab = ext_dir + 'flat_summary.txt'
    flat_data_tab = Table.read(flat_tab, format='ascii.fixed_width')

    dark_results = []
    for obj in objects:
        #with open(logfile, "a") as f:
            #fname = obj['File']
            #sys.stdout = f
            #print("Looking for a dark to match with", fname)
            #sys.stdout = sys.__stdout__
        #print(obj)
        dark_file, scale = find_matching_dark(obj, dark_data_tab, ext_dir, cal_dir, j) 

        fname = obj['File']
        sname = fname.replace('tc4n', 'dtc4n')
        bpfile = ext_dir + 'nf_bp_' + str(j) + '.fits'
        subtract_dark(fname, sname, ext_dir, dark_file, scale, bpfile)

        dark_results.append({
            'File': obj['File'],
            'OBJECT': obj['OBJECT'],
            'DARKFILE': dark_file,
            'SCALE': scale
            })
    dark_table = Table(rows=dark_results)
    dark_table.write(ext_dir + 'dark_match.txt', format='ascii.fixed_width', overwrite=True)

    with open(logfile, "a") as f:
        sys.stdout = f
        print(f"Best match darks written to {ext_dir}dark_match.txt")
        sys.stdout = sys.__stdout__

    flat_results = []
    for obj in objects:
        #with open(logfile, "a") as f:
            #fname = obj['File']
            #sys.stdout = f
            #print("Looking for a dome flat to match with", fname)
            #sys.stdout = sys.__stdout__
        flat_file = find_matching_flat(obj, flat_data_tab, ext_dir, cal_dir, j)

        fname = obj['File']
        new_fname = fname.replace('tc4n', 'dtc4n')
        fcor_name = new_fname.replace('dtc4n', 'fdtc4n')
        flat_correct(new_fname, fcor_name, ext_dir, flat_file)

        flat_results.append({
            'File': obj['File'],
            'OBJECT': obj['OBJECT'],
            'FLATFILE': flat_file
            })
    flat_table = Table(rows=flat_results)
    flat_table.write(ext_dir + 'flat_match.txt', format='ascii.fixed_width', overwrite=True)

    with open(logfile, "a") as f:
        sys.stdout = f
        print(f"Best match flats written to {ext_dir}dark_match.txt")
        sys.stdout = sys.__stdout__

    save_dir = ext_dir + 'Raw/'

    files_cleanup(ext_dir, save_dir)

    j = j + 1

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, "a") as f:
    sys.stdout = f
    print("End DarkFlatCorrect.py:", time)
    sys.stdout = sys.__stdout__
