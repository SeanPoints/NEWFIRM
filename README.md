This repository contains tools developed to reduce a set of NEWFIRM images obtained at the CTIO Blanco 4-m telescope.

To use these tools this directory should be placed in both PATH and PYTHONPATH

# Project Name

Short one-sentence description of what the code does.

Example:
Python tools for reducing and analyzing near-infrared astronomical images.

---

## Overview

Brief description of the project.

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
