#!/usr/bin/env python
# coding: utf-8

import os
import sys
from glob import glob

def get_last_word_in_path(file_path):
    # Normalize the path to handle different path separators
    normalized_path = os.path.normpath(file_path)

    # Split the normalized path into individual components
    path_components = normalized_path.split(os.sep)

    # Get the last component (last word in the path)
    last_word = path_components[-1]
    return last_word

workdir = os.getcwd()
swarp_dir = workdir + '/' + 'Skysub/'
wcs_path = '/Users/sean.points/data/NEWFIRM/WCS/'
outfile = swarp_dir + "run_swarp_stack.sh"
outdir = swarp_dir + "Stacked/"

if not os.path.exists(outdir):
    os.mkdir(outdir)

image_files = glob('%s/*.sw.txt' % (swarp_dir))
sorted_files = sorted(image_files)

with open(outfile, "w") as fout:

    for sw_file in sorted_files:

        base = sw_file.replace(".sw.txt", "")
        mask_file = f"{base}.mask.txt"
        new_base = get_last_word_in_path(base)

        # Check if mask file exists
        if not os.path.exists(mask_file):
            print(f"WARNING: {mask_file} does not exist")
            continue

        # Count lines in each file
        with open(sw_file) as f:
            sw_lines = sum(1 for _ in f)

        with open(mask_file) as f:
            mask_lines = sum(1 for _ in f)

        if sw_lines != mask_lines:
            print(f"WARNING: line mismatch for {base}: {sw_lines} vs {mask_lines}")
            continue

        new_sw_file = get_last_word_in_path(sw_file)
        new_mask_file = get_last_word_in_path(mask_file)

        cmd = (
            f"swarp @{new_sw_file} -c {wcs_path}default.swarp "
            f"-IMAGEOUT_NAME Stacked/{new_base}.sw.fits "
            f"-WEIGHTOUT_NAME /dev/null "
            f"-WEIGHT_TYPE MAP_WEIGHT "
            f"-WEIGHT_IMAGE @{new_mask_file}"
        )

        fout.write(cmd + "\n")
        os.chmod(outfile, 0o755)
