#!/usr/bin/env python
# coding: utf-8

'''
CTIO

SDP 2026-03-01

Synopsis: Reads FITS files in working directory and sorts them 
by increasing DATE-OBS to write a summary file of the observations 
obtained.

The summary file includes keywords:
DATE-OBS
EXPTIME
FILTER
TELFOCUS
TEMPOUT
AITMASS
ZD
AZ
TELRA
TELDEC
SEEING
OBJECT

'''

import os
from astropy.io import fits
from astropy.table import Table
from datetime import datetime

# Directory containing FITS files
workdir = os.getcwd()  # Change to your directory
path_components = workdir.split(os.sep)
last = path_components[-1]

# Output ASCII file
ofile = workdir + '/' + 'Summary.log'
output_file = workdir + '/' + last + '.log'
#output_file = workdir + '/junk.txt'

selected_keywords = ['DATE-OBS', 'EXPTIME', 'FILTER', 'TELFOCUS', 'TEMPOUT', 'AIRMASS', 'ZD', 'AZ', 'TELRA', 'TELDEC', 'SEEING', 'OBJECT']
data = []

#print(workdir, last)

if last.startswith("UT") and len(last) == 10:
    ymd = last[2:]
    odate = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
    #print(odate)
    tmpdate = datetime.strptime(odate, "%Y-%m-%d")
    tdate = tmpdate.date()

for fname in sorted(os.listdir(workdir)):
    if not fname.lower().endswith('.fits'):
        continue

    path = os.path.join(workdir, fname)

    try:
        with fits.open(path) as hdul:
            hdr = hdul[0].header

            date_obs = str(hdr['DATE-OBS'])
            dt = datetime.strptime(date_obs, "%Y-%m-%dT%H:%M:%S.%f")
            caldate = dt.date()
            delta_days = (caldate - tdate).days
            #print(delta_days)
            dec_hour = float((dt.hour + dt.minute / 60 + dt.second / 3600) + (delta_days * 24) + 0.0001)
            #dhour = f"{dec_hour:8.4f}"
            #print(fname, dhour)
            exptime = float(hdr['EXPTIME'])
            filter_ = str(hdr['FILTER'])
            telfocus = int(hdr['TELFOCUS'])
            tempout = float(hdr['TEMPOUT'])
            airmass = float(hdr['AIRMASS'])
            zd = float(hdr['ZD'])
            az = float(hdr['AZ'])
            telra = str(hdr['TELRA'])
            teldec = str(hdr['TELDEC'])
            seeing = float(hdr['SEEING'])
            obj = str(hdr['OBJECT'])

            #print(fname, date_obs, caldate, dec_hour, exptime, filter_, telfocus, airmass, zd, az)

            line = (fname, dec_hour, date_obs, exptime, filter_, telfocus, tempout, airmass, zd, az, telra, teldec, seeing, obj)
            data.append(line)

    except Exception as e:
        print(f"Could not read {fname}: {e}")

colnames = ['File', 'UT', 'DATE-OBS', 'EXPTIME', 'FILTER',
            'TELFOCUS', 'TEMPOUT', 'AIRMASS', 'ZD', 'AZ',
            'TELRA', 'TELDEC', 'SEEING', 'OBJECT']

table = Table(rows=data, names=colnames)
table.sort('UT')

table_no_ut = table.copy()
table_no_ut.remove_column('UT')

table.write(ofile, format='ascii.fixed_width', overwrite=True)
table_no_ut.write(output_file, format='ascii.fixed_width', overwrite=True)
