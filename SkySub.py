#!/usr/bin/env python
# coding: utf-8

'''
CTIO

SDP 2026-03-13

Synopsis: Uses the summary files to read a FITS file.  

(a) First reads summary table to check if any files has OBSTYPE keyword
with value sky.

(b) If a sky frame is found the program searchs for corresponding object
or standard fields that are with 10 degrees of the sky frame and taken
within 1 hour of the sky frame.  These limits can be changed in the 
program.  Future versions should let these values be set from command 
line arguments.

(c) If all observations have an OBSTYPE of [object, standard] the program 
selects up to nine observations with the same FILTER, EXPTIME, COADDS, 
EXPCOADD, and FSAMPLE that were taken within 30 minutes of the observation,
including the observation itself.

(d) The sky image is scaled to the observation image and subtracted.  
The subtracted data are saved to new directory Skysub.

'''

import os
import shutil
import sys
import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.stats import sigma_clip
from photutils.background import Background2D, MedianBackground
from photutils.segmentation import detect_sources
from photutils.segmentation import make_2dgaussian_kernel
from astropy.convolution import convolve
from datetime import datetime

# ============================================================
# CLEANUP FILES AFTER PROCESSING
# ============================================================

def files_cleanup(ext_dir, save_dir):
    # Create destination directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)

    for filename in os.listdir(ext_dir):
        if filename.startswith("fdtc4n") and filename.endswith(".fits"):
            src = os.path.join(ext_dir, filename)
            dst = os.path.join(save_dir, filename)
            shutil.move(src, dst)

    print("Files moved successfully!")

# ============================================================
# SETUP LOGGING FOR OBJECTS
# ============================================================

def log_sky_usage(obj_file, sky_files, logfile):

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(logfile, "a") as f:

        f.write("\n")
        f.write(f"{time}\n")
        f.write(f"OBJECT: {obj_file}\n")
        f.write(f"NSKY: {len(sky_files)}\n")

        for i, sky in enumerate(sky_files, start=1):
            f.write(f"   SKY{i:03d}: {sky}\n")

# ============================================================
# BUILD SOURCE MASK
# ============================================================

def build_source_mask(image):

    kernel = make_2dgaussian_kernel(3.0, size=5)
    smooth = convolve(image, kernel)

    bkg = Background2D(
        image,
        box_size=(64,64),
        filter_size=(3,3),
        bkg_estimator=MedianBackground()
    )

    threshold = bkg.background + 3*bkg.background_rms

    segm = detect_sources(smooth, threshold, npixels=10)

    if segm is None:
        return np.zeros_like(image, dtype=bool)

    return segm.data > 0


# ============================================================
# SKY MATCHING
# ============================================================

def find_sky_matches(obs_tab):

    coords = SkyCoord(obs_tab["RA"], obs_tab["DEC"], unit="deg")
    times = obs_tab["UT"] * u.hour

    obj_mask = obs_tab["OBSTYPE"] == "object"
    sky_mask = obs_tab["OBSTYPE"] == "sky"

    obj_tab = obs_tab[obj_mask]
    sky_tab = obs_tab[sky_mask]

    obj_coords = coords[obj_mask]
    sky_coords = coords[sky_mask]

    obj_times = times[obj_mask]
    sky_times = times[sky_mask]

    results = {}

    for i, obj in enumerate(obj_tab):

        obj_file = obj["File"]
        obj_coord = obj_coords[i]
        obj_time = obj_times[i]

        sky_matches = []

        for j, sky in enumerate(sky_tab):

            if not (
                sky["FILTER"] == obj["FILTER"] and
                sky["EXPCOADD"] == obj["EXPCOADD"] and
                sky["COADDS"] == obj["COADDS"] and
                sky["FSAMPLE"] == obj["FSAMPLE"]
            ):
                continue

            sep = obj_coord.separation(sky_coords[j])
            dt = abs(obj_time - sky_times[j])

            if sep <= 10*u.deg and dt <= 1*u.hour:
                sky_matches.append(sky["File"])

        if len(sky_matches) > 0:
            results[obj_file] = sky_matches
            continue

        candidates = []

        for j, other in enumerate(obj_tab):

            if not (
                other["FILTER"] == obj["FILTER"] and
                other["EXPCOADD"] == obj["EXPCOADD"] and
                other["COADDS"] == obj["COADDS"] and
                other["FSAMPLE"] == obj["FSAMPLE"]
            ):
                continue

            dt = abs(obj_time - obj_times[j])

            if dt <= 0.5*u.hour:
                candidates.append((dt, other["File"]))

        candidates.sort(key=lambda x: x[0])

        if len(candidates) > 9:
            candidates = candidates[:9]

        results[obj_file] = [c[1] for c in candidates]

    return results


# ============================================================
# BUILD SKY MODEL
# ============================================================

def build_sky_model(obj_data, sky_files, ext_dir):

    obj_mask = build_source_mask(obj_data)

    obj_med = np.median(obj_data[(obj_data > 0) & (~obj_mask)])

    sky_stack = []

    for sky in sky_files:

        sky_path = os.path.join(ext_dir, sky)

        sky_data = fits.getdata(sky_path)

        sky_mask = build_source_mask(sky_data)

        combined_mask = obj_mask | sky_mask

        sky_med = np.median(sky_data[(sky_data > 0) & (~combined_mask)])

        scale = obj_med / sky_med

        sky_scaled = sky_data * scale

        sky_stack.append(sky_scaled)

    sky_stack = np.array(sky_stack)

    clipped = sigma_clip(sky_stack, sigma=3, axis=0)

    sky_model = np.nanmedian(clipped, axis=0)

    return sky_model


# ============================================================
# SKY SUBTRACTION
# ============================================================

def subtract_sky(obj_file, sky_files, ext_dir, outdir):

    obj_path = os.path.join(ext_dir, obj_file)

    obj_data, hdr = fits.getdata(obj_path, header=True)

    sky_model = build_sky_model(obj_data, sky_files, ext_dir)

#    result = obj_data - sky_model
    result = obj_data - sky_model

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sky_key = f"{time}; Sky-subtracted"
    hdr["SKYCOR"] = sky_key
    hdr["PYSKYSUB"] = ('True', "SkySub.py Flag")
    hdr["NSKY"] = (len(sky_files), "Number of sky frames used")
    for i, sky in enumerate(sky_files, start=1):
        hdr[f"SKY{i:03d}"] = sky


    outfile = os.path.join(
        outdir,
        obj_file.replace("fdtc4n", "sfdtc4n")
    )

    fits.writeto(outfile, result, hdr, overwrite=True)

    print("Wrote:", outfile)


# ============================================================
# MAIN
# ============================================================

workdir = os.getcwd()

logfile = workdir + '/' + 'SkySub.log'


if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin SkySub.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

num_detectors = 5

j = 1
while j < num_detectors:
    ext_dir = workdir + '/' + str(j) + '/'

    outdir = os.path.join(workdir + '/', "Skysub")

    with open(logfile, 'a') as f:
        sys.stdout = f
        print("Extension directory:", ext_dir)
        print("Output directory:", outdir)
        sys.stdout = sys.__stdout__

    os.makedirs(outdir, exist_ok=True)

    obs_tab = Table.read(
        os.path.join(ext_dir, "skysub_summary.txt"),
        format="ascii.fixed_width"
    )

    results = find_sky_matches(obs_tab)

    for obj_file, sky_files in results.items():

        print("\nOBJECT:", obj_file)
        print("Nsky:", len(sky_files))

        log_sky_usage(obj_file, sky_files, logfile)

        subtract_sky(obj_file, sky_files, ext_dir, outdir)
    j = j + 1

#j = 1
#while j < num_detectors:
#    ext_dir = workdir + '/' + str(j) + '/'
#    save_dir = ext_dir + 'Raw/'
#    files_cleanup(ext_dir, save_dir)
#    j = j + 1

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("End SkySub.py:", time)
    sys.stdout = sys.__stdout__
