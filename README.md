# NEWFIRM Reduction Software

Python tools for reducing near-infrared data obtained with NEWFIRM on the CTIO Blanco 4-m telescope.

---

## Overview

This repository contains Python programs to process NIR imaging data obtained with NEWFIRM on the CTIO
Blanco 4-m telescope.  The pipeline renames the data to a common scheme to facilitate processing, splits
the multi-extension FITS (MEF) data into separate directories, trims the images, combines dark frames, based
upon number of coadds, exposure time per coadd, and number of Fowler samples, combines "on" and "off" 
flat-field images for each filter, creates bad pixel masks, performs the dark subtraction, bad-pixel correction,
and flat-fields the raw object data.  After the raw science data are reduced, images are sorted by filter, 
number of coadds, exposure times per coadd, and number of Fowler samples to create sky images that scaled to 
imdividual images for sky-subtraction.

This pipeline does not, as yet, compute the final astrometric WCS for the images nor does it recombine the 
individual exposures or stack images.  These issues are addressed in some supplementary materials, but are not within
the supported scope of this package.

---

## Requirements

This pipeline has been tested on a MacBook Pro (M3 Pro running Sequoia 15.7.3) and GNU/Linux (Ubuntu 18.04) using
an anaconda environment.

```bash
Python: 3.9.18
NumPy: 1.25.0
SciPy: 1.10.1
Astropy: 5.1.1
Photutils: 1.11.0
Matplotlib: 3.9.2
CCDProc: 2.1.1
```
---

## Installation

Clone the repository:

```bash
cd $HOME/bin
git clone https://github.com/SeanPoints/NEWFIRM.git ./newfirm
```

Place the path in your $PATH environment:

```bash
PATH=$PATH:$HOME/bin/newfirm/
````

Create a conda environment:

```bash
conda create --name newfirm scipy
conda activate newfirm
```

Install dependencies:

```bash
conda install astropy
```

---

## Usage

All programs are run from the command line with no arguments from the top level data directory.  
This top level directory should follow the format of UTYYYYMMDD of the calendar date of the observations. 

```bash
cd data/UTYYYYMMDD
CheckDateObs.py
RenameFiles.py
...
SkySub.py
```
---

## Example Workflow

Typical reduction steps:

```
CheckDateObs.py
   ↓
RenameFiles.py
   ↓
SortFITS.py
   ↓
SplitMef.py
   ↓
TrimImage.py
   ↓
SortCombDarks.py
   ↓
SortCombFlats.py
   ↓
MakeBadPixMask.py
   ↓
Prep4DarkFlatCor.py
   ↓
DarkFlatCorrect.py
   ↓
Prep4SkySub.py
   ↓
SkySub.py
```

---

## Input Data

Expected input format:

- Multi-extension FITS images with 4 extensions
- WCS headers recommended
- Example header keywords:

```
DATE-OBS
EXPTIME
EXPCOADD
COADDS
FILTER
FSAMPLE
```

---

## Software Description

This software assumes that the top level directory for the data is called "UTYYYYMMDD" that corresponds to the calendar date for the
start of the night.  

**CheckDateObs.py** - This program reads FITS files in the current working directory and checks the header keyword DATE-OBS.  The program is implemented because 
the TCS sometimes sends a DATE-OBS of YYYY-MM-DDTHH:MM:SS.S where it reports SS.S as 60.n.  This causes an error when trying to rename the files in the next 
step.  In cases where the SS.S is 60.n, the minute in incremented by 1 and the seconds are reported as 00.n.

**RenameFiles.py** - This program is executed from the top level NEWFIRM data directory, UTYYYYMMDD, and performs the following tasks: 
- Copies all original data to a subdirectory "SAVE"
- Sanitizes the file list so that it will not work on files that have filenames that include certain strings, such as "test", "junk", "temp", "focus", etc
- Sanitizes files based on the FITS header "OBJECT" keyword to not process files where the "OBJECT" keyword contains certain strings, such as "test", "junk", etc;
- Moves files that pass the previous steps to a new filename of the format "c4n_obstype_YYMMDD_HHMMSS_expnum.fits where the values for obstype, YYMMDD, HHMMSS, and expnum are taken from the FITS header.  For this purpose, files with an OBSTYPE of "sky" or "standard" are treated as "object".
- Removes any files from the top level data directory that don't pass the sanitization steps.  The strings used to sanitize the files can be modified by the user.  

**SortFITS.py** - This program creates a time-sorted log for the night that includes the following FITS keywords: DATE-OBS, EXPTIME, FILTER, TELFOCUS, TEMPOUT, AIRMASS, ZD, AZ, TELRA, TELDEC, SEEING, and OBJECT. 

**SplitMef.py** - This program reads the MEF files in the current directory and splits the extensions into a subdirectory.  The primary
header information is copied to each extension header.

**TrimImage.py** - This program reads the individual detector images in their directory and trims the image, removing the overscan region.

**SortCombDarks.py** - This programs reads the files in the directory and finds those that have OBSTYPE="dark".  For those dark frames, it reads the FITS header keywords for the exposure time per coadd (EXPCOADD), the number of coadds (COADDS), and the number of Fowler samples (FSAMPLE).  The program then combines dark frames with same values of the aforementioned keywords.  The output files are called dark_[EXPCOADD]s_[COADDS]c_[FSAMPLE]f_[CCD].fits, providing a unique name for each dark.

**SortCombFlats.py** - This program reads the files in the directory and finds those that have OBSTYPE="dflat".  It sorts the flats based on the FITS keyword headers FILTER.  The program reads the FITS keyword DFLAMPVA to determine if the dome flats are "on" or "off".  The programs scales the individual flat sby the mode and median combines them. The "off" flats are then subtracted from the "on" flats, producing a master flat for the filter.  The master flat is normalized by the median value to produce a normalized flat.  The normalized flat files are called nflat_[FILTER]_[CCD].fits.  The intermediate processed flats, .i.e. the combined "on" and "off" flats for each filter and the master flats in each filter, are also saved to disk. 

**MakeBadPixMask.py** - This program reads the data directory and looks for the master "on" and "off" KXs flats.  It uses the ratio between the "on" and "off" flats to create bad pixel masks for each detector.  Additionally, the top 48 rows of detector 3 are masked to remove the effects of the bad pixel located there.

**Prep4DarkFlatCor.py** - Searches the reduction directory for the master darks, normalized flats, and object files.  Writes summary files in the data directory listing OBSTYPE, EXPTIME, EXPCOADD, COADDS, FSAMPLE, and FILTER for FITS files.

**DarkFlatCorrect.py** - This program reads the summary files produced in the previous step.  The object observations are flat-fielded and dark corrected based on the values of the keywords in the summary file.  If no correcsponding dark frame exists, the programs tries to scale one for use.  The software contains a variable called "calpath_root".  This can be set to a local repository of calibration frames, i.e., dark, flats, and bad-pixel masks.  If a calibration frame is not found in the local working directory, the software will look in the local calibration repository.  **The user will have to set the path of the local repository for this to work.** 

**Prep4SkySub.py** - This program looks for data that have been flat-fielded and dark-subtracted.  The program then creates a summary file of the images to be sky corrected.

**SkySub.py** - This program performs the sky subtraction for individual images.  The program examines the files in the reduction directory to determine if there are any with a value of OBSTYPE="sky".  Images with an OBSTYPE="sky" are taken only to perform sky-subtraction in crowded fields or for extended objects.  If "sky" images are found, the program attenpts to find the corresponding "object" images.  The corresponding "object" images are currently selected to within 10 degrees of the "sky" frame and taken within 1 hour of the sky image.  These limits are set in the code.  Future versions may have the ability to set the limits on the command line.  In the normal mode of operation, the program finds "object" or "standard" images that have the same observing parameters (i.e., FILTER, EXPTIME, COADDS, EXPCOADD, FSAMPLE) and selects up to the nine images closest in time. Once "sky" images are selected, they are scaled to the object frame and median combined.  The combined "sky" image is then subtracted from the "object" image.  The sky-subtracted images for all detectors are placed in the directory /data/UTYYYYMMDD/Skysub. 

---

## Output

The pipeline produces sky-subtracted images in a subdirectory of the top-level data directory:

data/UTYYYYMMDD/Skysub

Each program produces a log file Program.log during execution.  The logs contain details of the
steps performed by the program and may be useful to debug any failures.

After the data have been sky-subtracted, one will need to place an astrometric solution on the individual 
images before stacking.  All of these steps can be performed using Emmanuel Bertin's Astromatic software: 
SExtractor, SCAMP, and SWarp (https://github.com/astromatic).  

Astrometric solutions can also be obtained by using the Astrometry.net software at https://astrometry.net.

---

## Astrometry files

The default pipeline does not perform an astrometric solution for the data. After the data have been sky-subtracted, 
one will need to place an astrometric solution on the individual images before stacking.  All of these steps can be 
performed using Emmanuel Bertin's Astromatic software: SExtractor, SCAMP, and SWarp (https://github.com/astromatic).  

Astrometric solutions can also be obtained by using the Astrometry.net software at https://astrometry.net.

Some additional programs have been written to allow one to use the Astromatic software.  These are:

```
SetupSextractor.py
SetupScamp.py
SetupSwarp.py
MakeSwarpMasks.py
SetupSwarpStack.py
NF_Swarp_Stack.py
WCS/default.nnw
WCS/default.param
WCS/default.scamp
WCS/default.sex
WCS/default.swarp
WCS/gauss_2.5_5x5.conv
```

The WCS directory contains the default configuration files that I use to obtain the astrometric solutions for images and to 
stack images based on OBJECT, FILTER, and EXPTIME.  If used, one should place these files in a directory where one is reducing 
the NEWFIRM data.  One will need to edit WCS/default.sex to update the paths for:
PARAMETERS_NAME, FILTER_NAME, and STARNNW_NAME.

Furthermore, the variable "wcs_path" will need to be modified in SetupSextractor.py, SetupScamp.py, SetupSwarp.py, and
NF_Swarp_Stack.py.

---

## Astrometry and Stacking ##

This section contains some notes on how to use Emmanuel Bertin's Astromatic software to put astrometric solutions on NEWFIRM data and stack the images.  This in not explicitly supported.

**Getting Started:** The basic files necessary to run the Astromatic software are listed above and included in this repository.  As mentioned one needs to edit the default.sex file and update the path information for PARAMETERS_NAME, FILTER_NAME, and STARNNW_NAME to reflect the location of those files on your system.  The programs Setup_sextractor.py, SetupScamp.py, SetupSwarp.py, and NF_Swarp_Stack.py need to be edited to change the variable "wcs_path" to reflect the location of the Astromatic configuration files on your system.

**SetupSextractor.py** - This program creates an executable script, "run_sextractor.sh", in the data/UTYYYYMMDD/Skysub directory.  Once the script is created, you can run it from the command line.  

**SetupScamp.py** - This program contains an executable script, "run_scamp.sh", in the data/UTYYYYMMDD directory.  It uses the FITS_LDAC catalogs created by "run_sextractor.sh" and finds an astrometric solution using the GAIA-EDR3 catalog.  Sometimes Scamp can fail because the connection to the database times out.

**SetupSwarp.py** - This program

---

## Contributions or comments

Contributions are welcome as are coments to improve the code to provide additional
functionality.

---

## Author

Sean Points  
NSFs National Optical-Infrared Astronomy Research Laboratory (NOIRLab)<br>
Cerro Tololo Inter-American Observatory (CTIO)</br>
sean.points@noirlab.edu
