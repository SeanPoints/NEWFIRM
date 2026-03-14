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
individual exposures or stack images.  These issues will be addressed in future releases.

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
cd data/UT20260228
CheckDateObs.py
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
MakeBadPixelMask.py
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

## Output

The pipeline produces sky-subtracted images in a subdirectory of the top-level data directory:

data/UTYYYYMMDD/Skysub

Each program produces a log file <Program>.log during execution.  The logs contain details of the
steps perfomred by the program and may be useful to debug any failures.

As mentioned above the individual detectors have are not yet recombined into a single image nor 
is a final astrometric solution applied to the images.  These steps are currently performed using
Emmanuel Bertin's Astromatic software: SExtractor, SCAMP, and SWarp.

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
