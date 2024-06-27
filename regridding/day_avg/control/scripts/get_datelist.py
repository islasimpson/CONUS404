import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from glob import glob
import os
import datetime
import sys
import argparse

import warnings
warnings.filterwarnings('ignore')

def main():
    parser = argparse.ArgumentParser(description='Argument parser for sorting out dates')
    parser.add_argument('--date_start', type=str, required=True, help='Start date for output')
    parser.add_argument('--date_end', type=str, required=True, help='End date for output')

    args = parser.parse_args()
  
    figure_out_dates(args.date_start, args.date_end)

def figure_out_dates(date_start, date_end):
    date_start = datetime.datetime.strptime(date_start,'%Y%m')
    date_end = datetime.datetime.strptime(date_end,'%Y%m')
    date_start = np.datetime64(date_start,'M')
    date_end = np.datetime64(date_end,'M')

    cur_date = date_start
    while cur_date <= date_end:
        datestring=str(cur_date).split('-')[0]+str(cur_date).split('-')[1]
        cur_date = cur_date + np.timedelta64(1,'M')
        with open("./control/files/datelist.txt",'a') as file:
            file.write(datestring+'\n')

if __name__ == "__main__":
    main()








