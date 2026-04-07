#!/usr/bin/env python
# coding: utf-8

import sys
import os
from glob import glob
from datetime import datetime
from astropy.io import fits
from astropy.table import Table

from astropy.io import fits
from astropy.table import Table

def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)

    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)

    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

def add_leading_zero(integer_value, fixed_length=3):
    # Convert the integer to a string and prepend zeros to achieve the fixed length
    str_value = f"{integer_value:0{fixed_length}}"
    return str_value

# directory containing FITS files

workdir = os.getcwd()
swarp_dir = workdir + '/' + 'Skysub/'

files = glob('%s/sfd*.sw.fits' % (swarp_dir))
sorted_files = sorted(files)

rows = []

for fitsfile in sorted_files:
    try:
        hdr = fits.getheader(fitsfile)
        short_name = get_last_word_in_path(fitsfile)
        rows.append({
            "FILENAME": short_name,
            "OBJECT": hdr.get("OBJECT", "UNKNOWN"),
            "FILTER": hdr.get("FILTER", "UNKNOWN"),
            "EXPTIME": hdr.get("EXPTIME", 0.0),
            "FSAMPLE": hdr.get("FSAMPLE", "UNKNOWN")
        })

    except Exception as e:
        print(f"Skipping {fitsfile}: {e}")

# create astropy table
tab = Table(rows=rows)

print(tab)

grouped = tab.group_by(["OBJECT", "FILTER", "EXPTIME"])

for key, group in zip(grouped.groups.keys, grouped.groups):
    
    obj = key["OBJECT"]
    filt = key["FILTER"]
    expt = key["EXPTIME"]
    int_exp = int(expt)
    sexp = add_leading_zero(int_exp, fixed_length=3)

    filelist = list(group["FILENAME"])

    print(f"\nOBJECT={obj} FILTER={filt} EXPTIME={int_exp}")
    print(filelist)

for key, group in zip(grouped.groups.keys, grouped.groups):

    obj = key["OBJECT"]
    filt = key["FILTER"]
    expt = key["EXPTIME"]
    int_exp = int(expt)
    sexp = add_leading_zero(int_exp, fixed_length=3)

    outfile = swarp_dir + f"{obj}.{filt}.{sexp}.sw.txt".replace(" ", "_")

    with open(outfile, "w") as f:
        for fn in group["FILENAME"]:
            f.write(swarp_dir + fn + "\n")


    maskout = swarp_dir + f"{obj}.{filt}.{sexp}.mask.txt".replace(" ", "_")
    with open(maskout, "w") as f:
        for fn in group["FILENAME"]:
            mfn = fn.replace("sw","mask")
            f.write(swarp_dir + mfn + "\n")
