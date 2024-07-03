#!/bin/bash

#----------------------USER DEFINITIONS------------------------

#--User
user=islas

#--Account Key
account=P04010022

#--Output name
runname='CONUS404'

#--Start and End year for analysis
datestart=198001
dateend=202112


#--Location of conus404 data. 
basepath="/glade/campaign/collections/rda/data/ds559.0/"

#--Scratch space for intermediate files (Note, any files that are in here will get deleted by the scripts)
tempdir="/glade/derecho/scratch/islas/temp/conus404/"

#--Outpath for the time series files
outpath="/glade/campaign/cgd/cas/islas/DATASETS/CONUS404/daily/native/"

#--Outpath for the regridded files
outpath_rg="/glade/campaign/cgd/cas/islas/DATASETS/CONUS404/daily/regridded_onto_era5/"

#--Specify variables
VARS=( 'Q2' )

#--Weight file for regridding
wgtfile="/glade/derecho/scratch/islas/temp/conus404/wgts/wgt.nc"

#--Interpolation type
ITYPE=( 'bilinear' )

#--Output grid resolution (float to specify grid spacing, string to specify file containing input grid)
grid_res="./grids/era5.nc"

#--sumvar specifies whether to average the variable over the hours of the day (False) or whether to sum it (True)
sumvar=( 'False' )

#--------------------END USER DEFINITIONS-------------------------

#------Make needed directories
if [ ! -d $outpath_rg ] ; then
    mkdir $outpath_rg
fi

if [ ! -d ./control/files ] ; then
    mkdir ./control/files
fi
if [ ! -d ./logs ] ; then
    mkdir ./logs
fi
if [ ! -d ./pbsfiles ] ; then
    mkdir ./pbsfiles
fi

#------Clean UP
if [ -f ./control/files/datelist.txt ] ; then
    rm ./control/files/datelist.txt
fi
if [ -f ./control/COMPLETE ] ; then
    rm ./control/COMPLETE
fi
if [ -f ./logs/progress.txt ] ; then
    rm ./logs/progress.txt
fi
if [ -f ./pbsfiles/output.log ] ; then 
    rm ./pbsfiles/output.log
fi

module load conda
conda activate npl-2024a

nvars=${#VARS[@]}
for ivar in `seq 0 $(($nvars-1))` ; do

  ivar=${VARS[ivar]}
  itype=${ITYPE[ivar]}
  isumvar=${sumvar[ivar]}
  
  # Use a python script to get the list of dates to process.
  # This list is places in ./control/files/datelist.txt
  python "./control/scripts/get_datelist.py" --date_start=$datestart --date_end=$dateend
  
  if [ ! -d $outpath/$ivar ] ; then
      mkdir $outpath/$ivar
  fi
  if [ ! -d $outpath_rg/$ivar ] ; then
      mkdir $outpath_rg/$ivar
  fi
  
  outpath_var=$outpath/$ivar
  outpath_rg_var=$outpath_rg/$ivar
  
  
  while [[ -s "./control/files/datelist.txt" ]] ; do
  
     #---remove any tmp files that exist from previous call
     if ls $outpath/*.tmp 1 > /dev/null 2>&1 ; then
         rm $outpath/*.tmp
     fi
     if ls $tempdir/*.nc 1 > /dev/null 2>&1 ; then 
         rm $tempdir/*.nc
     fi
     if ls $tempdir/*.tmp 1 > /dev/null 2>&1 ; then
         rm $tempdir/*.tmp
     fi
  
     datecontinue=$(head -n 1 ./control/files/datelist.txt)
     echo "Continuation at date="$datecontinue >> ./logs/progress.txt
  
     qsub -A $account -v runname=$runname,basepath=$basepath,outpath=$outpath_var,var=$ivar,tempdir=$tempdir,wgtfile=$wgtfile,itype=$itype,grid_res=$grid_res,outpath_rg=$outpath_rg_var,sumvar=$isumvar get_dailyavg_monthlyfiles.pbs 
  
     while [[ ! -f ./control/COMPLETE ]] ; do
        echo "Job is still running..."$(date) >> ./logs/progress.txt
        sleep 60
     done
     rm ./control/COMPLETE
  
  done
  
done
