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
number of coadds, exposure times per coadd, and number of Fowler samples to create sky images that  

Explain:
- what problem the software solves
- what kind of data it works on
- typical workflow

Example:

This repository contains Python programs used to process NIR imaging data.
The pipeline performs sky subtraction, source detection, and photometric
measurements using Astropy and Photutils.

---

## Requirements

List dependencies.

```bash
python >=3.10
numpy
astropy
photutils
matplotlib
```

Or with pip:

```bash
pip install numpy astropy photutils matplotlib
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/username/projectname.git
cd projectname
```

(Optional) create a virtual environment:

```bash
python -m venv env
source env/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

Example command:

```bash
python reduce_image.py input.fits
```

Example with options:

```bash
python reduce_image.py input.fits --sky sky_model.fits --output result.fits
```

---

## Example Workflow

Typical reduction steps:

```
raw images
   ↓
sky model creation
   ↓
sky subtraction
   ↓
source detection
   ↓
photometry catalog
```

---

## Input Data

Expected input format:

- FITS images
- WCS headers recommended
- Example header keywords:

```
DATE-OBS
EXPTIME
FILTER
```

---

## Output

Generated products:

```
output/
   sky_model.fits
   reduced_image.fits
   photometry_catalog.fits
   reduction_log.txt
```

---

## Repository Structure

```
projectname/
│
├── scripts/
│   reduce_image.py
│   make_sky_model.py
│
├── examples/
│   example_data.fits
│
├── docs/
│
└── README.md
```

---

## Contributing

Contributions are welcome.

Typical workflow:

```
main  → stable code
dev   → development branch
```

1. Create a branch from `dev`
2. Make changes
3. Submit a pull request

---

## License

Specify license here.

Example:

MIT License

---

## Author

Name  
Institution  
Contact email
