#!/usr/bin/env python3

'''
CTIO

SDP 2026-03-01

Synopsis: Checks that FITS keyword DATE-OBS is valid.

Program reads FITS files in current working directory and checks that
keyword DATE-OBS is valid.  Program was written because some values 
for DATE-OBS had a seconds part of 60.n.  This would cause an error when
trying to rename the file based on DATE-OBS.
'''

import sys
import os
from glob import glob
from astropy.io import fits
from datetime import datetime, timedelta
from pathlib import Path

workdir = os.getcwd() + '/'

logfile = workdir + 'CheckDateObs.log'

if os.path.exists(logfile):
    logfile_flag = "a"
else:
    logfile_flag = "w"

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, logfile_flag) as f:
    sys.stdout = f
    print("Begin CheckDateObs.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__

files = glob('%s/*.fits' % (workdir))
sorted_files = sorted(files)
num_files = len(sorted_files)

for filename in sorted_files:
    fname = os.path.basename(filename)

    with open(logfile, 'a') as f:
        sys.stdout = f
        print(f"Processing {fname}")
        sys.stdout = sys.__stdout__

    with fits.open(filename, mode="update") as hdul:

        modified = False

        for hdu in hdul:

            hdr = hdu.header

            date_obs = hdr["DATE-OBS"]

            if date_obs is None or "T" not in date_obs:
                continue

            date_part, time_part = date_obs.split("T")

            if "." in time_part:
                base_time, frac = time_part.split(".", 1)
                frac = "." + frac
            else:
                base_time = time_part
                frac = ""

            h, m, s = base_time.split(":")

            # Only fix leap-second case
            if int(s) == 60:

                print(f"  Fixing leap second: {date_obs}")

                # replace 60 -> 59 so datetime can parse
                corrected = f"{date_part}T{h}:{m}:59"

                dt = datetime.strptime(corrected, "%Y-%m-%dT%H:%M:%S")

                # add 1 second → rolls minute/hour/day if needed
                dt += timedelta(seconds=1)

                new_date_obs = dt.strftime("%Y-%m-%dT%H:%M:%S") + frac

                hdr["DATE-OBS"] = new_date_obs

                with open(logfile, 'a') as f:
                    sys.stdout = f
                    print(f"{fname}: {date_obs} -> {new_date_obs}")
                    sys.stdout = sys.__stdout__
                modified = True

        if modified:
            hdul.flush()
            with open(logfile, 'a') as f:
                sys.stdout = f
                print(f"{fname} updated")
                sys.stdout = sys.__stdout__
        else:
            with open(logfile, 'a') as f:
                sys.stdout = f
                print(f"{fname} unchanged")
                sys.stdout = sys.__stdout__

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, 'a') as f:
    sys.stdout = f
    print("Begin CheckDateObs.py:", time)
    print("Working directory:", workdir)
    sys.stdout = sys.__stdout__
