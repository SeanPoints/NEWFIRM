#!/usr/bin/env python
# coding: utf-8

'''
CTIO

Synopsis: Make bad pixel mask using KXs On and Off master flats
'''
import os
import sys
from astropy.io import fits
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from astropy import units as u
from astropy.nddata import CCDData
import ccdproc as ccdp
from photutils.segmentation import detect_sources
from datetime import datetime

workdir = os.getcwd() + '/'

logfile = workdir + 'MakeBadPixMask.log'

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, "w") as f:
    sys.stdout = f
    print("Begin MakeBadPixMask.py:", time)
    sys.stdout = sys.__stdout__

i = 1
while i < 5:
    ext_dir = workdir + str(i) + '/'
    print('Working in directory', ext_dir)

    # Open the first FITS file
    fits_file1 = fits.open(ext_dir + 'flat_KXs_off_' + str(i) + '.fits')
    ff1 = 'flat_KXs_off_' + str(i) + '.fits'

    # Open the second FITS file
    fits_file2 = fits.open(ext_dir + 'flat_KXs_on_' + str(i) + '.fits')
    ff2 = 'flat_KXs_on_' + str(i) + '.fits'

    with open(logfile, "a") as f:
        sys.stdout = f
        print('Working in directory', ext_dir)
        print('Using file:', ff1)
        print('Using file:', ff2)
        sys.stdout = sys.__stdout__

    # Access the data from the primary HDU of each file
    data1 = fits_file1[0].data
    data2 = fits_file2[0].data

    # Close the input files
    fits_file1.close()
    fits_file2.close()

    # Set certain parts of image to zero before division because they do not
    # get taken care of cleanly with the data mask
    
    #yy, xx = np.ogrid[:data1.shape[0], :data1.shape[1]]

    #if i == 1:
    #    x1 = 343 - 1
    #    y1 = 1265 - 1
    #    r1 = 20 - 1
    #    mask1 = (xx - x1)**2 + (yy - y1)**2 <= r1**2

    #    x2 = 374 - 1
    #    y2 = 1085 - 1
    #    r2 = 13
    #    mask2 = (xx - x2)**2 + (yy - y2)**2 <= r2**2

    #    x3 = 1202 - 1
    #    y3 = 499 - 1
    #    r3 = 10
    #    mask3 = (xx - x3)**2 + (yy - y3)**2 <= r3**2

    #    x4 = 1340 - 1
    #    y4 = 449 - 1
    #    r4 = 13
    #    mask4 = (xx - x4)**2 + (yy - y4)**2 <= r4**2

    #    x5 = 1263 - 1
    #    y5 = 808 - 1
    #    r5 = 10
    #    mask5 = (xx - x5)**2 + (yy - y5)**2 <= r5**2

    #    mask = mask1 + mask2 + mask3 + mask4 + mask5
    #    data1[mask] = 20000
    #    data2[mask] = 1000

    # Perform the division
    np.seterr(divide='ignore',invalid='ignore')
    ratio_data = np.divide(data1, data2)
    # Create a new FITS file to save the ratio data
    new_hdul = fits.PrimaryHDU(ratio_data)
    # Write the new FITS file
    new_hdul.writeto(ext_dir + 'ratio.fits', overwrite=True)
    
    mask = ccdp.ccdmask(ratio_data, ncsig=50, nlsig=50)
    #plt.imshow(mask)
    #plt.show()
    mask_as_ccd = CCDData(data=mask.astype('uint8'), unit=u.dimensionless_unscaled)
    mask_as_ccd.header['imagetyp'] = 'flat mask'
    mask_as_ccd.write(ext_dir + 'bpmask_' + str(i) + '.fits', overwrite=True)

    omask = ext_dir + 'bpmask_' + str(i) + '.fits'
    ofits = fits.open(omask)
    odata = ofits[0].data
    oheader = ofits[0].header
   
    bptmp = ext_dir + 'bpmask_' + str(i) + '.fits'
    hdulist = fits.open(bptmp)
    header = hdulist[0].header
    header['OBJECT'] = 'Bad Pixel Mask'

    inv_odata = 1 - odata
    if i == 3:
        inv_odata[2000:2048, 0:2048] = 0
    #inv_odata[mask] = 0
    imask = ext_dir + 'nf_bp_' + str(i) + '.fits'
    new_hdul = fits.PrimaryHDU(data=inv_odata, header=header)
    new_hdul.writeto(imask, overwrite=True)
    bpf = 'nf_bp_' + str(i) + '.fits'

    with open(logfile, "a") as f:
        sys.stdout = f
        print('Bad pixel file written to:', bpf)
        sys.stdout = sys.__stdout__
    
    #mask_hdul = fits.PrimaryHDU(mask)
    #mask_hdul.writeto(workdir + 'mask.fits', overwrite=True)
    i = i + 1

time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

with open(logfile, "a") as f:
    sys.stdout = f
    print("End MakeBadPixMask.py:", time)
    sys.stdout = sys.__stdout__
    
