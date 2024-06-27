# CONUS404
Scripts for dealing with CONUS404 data.

<u>Averaging and regridding Scripts</u>

Scripts for averaging and regridding are in ```./regridding/``` and then in sub-directories depending on desired frequency e.g., for daily average the scripts are in ```./regridding/day_avg/```.

How to run:

The averaging and regridding is controlled by ``control_jobs.sh``.  Set up the specifics of your case within the "USER DEFINITIONS" section of ``control_jobs.sh``.  These include

1. ``user``: Your username on CISL machines
2. ``account``: CISL project number
3. ``runname``: Used in the filenames of the output.  Filenames will be of the form ```$runname_$var_$date.nc```.
4. ``datestart``: The start date in the form YYYYMM for the generation of regridded data
5. ``dateend``: The end date in the form of YYYYMM for the generation of regridded data5
7. ``basepath``: Location of conus404 data
8. ``tempdir``: Scratch space for intermediate files (Note, any files in here will be deleted by the scripts)
9. ``outpath``: Output directory for files on the native grid
10. ``outpath\_rg``: Output directory for file containing regridded data
11. ``VARS``: List of variables for processing
12. ``wgtfile``: Location in which to put the weight file for regridding (weight file is generated on first call).
13. ``ITYPE``: List containing interpolation type (conservative or bilinear).   Must be the same size as VARS
14. ``grid_res``: Specifier for grid resolution of regridded output.  If set as a float e.g., 0.1 this will be the grid spacing for the output.  If set as a string, this will be the file that will be read in for the output grid (must contain dimensions ``lon`` and ``lat``.

Make sure the directory ``$output`` exists.  Then execute the script by...

``./control_jobs.sh``

You might want to do this in a screen session.

How it works: 

First it calls the python script ``./control/scripts/get_datelist.py which gets the list of months to be processed.  Then it calls the pbs script get_dailyavg_monthlyfiles.pbs which does the processing.  This loops over months.  For each month it loops over days, runs ``ncra`` to get a daily average and outputs that to a temporary file.  Once the month is complete, it concatenates those daily files into one monthly file that contains all days in the native output directory.  It then calls the python script ./control/regrid_conus404.py to do the regridding and places the regridded data in the regridded output directory.

