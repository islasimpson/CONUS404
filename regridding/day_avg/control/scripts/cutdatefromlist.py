import xarray as xr
import numpy as np
import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Argument parser for cut variable from log")
    parser.add_argument('--logname', type=str, required=True, help='Location of the file that contains the variable list')
    parser.add_argument('--date', type=str, required=True, help='Date to be cut')

    args = parser.parse_args()

    cutdatefromlist(args.logname, args.date)

def cutdatefromlist(logfile,date):
    try:
        with open(logfile,'r') as file:
            lines = file.readlines()
            newlines = [line for line in lines if line.strip() != date]
            with open(logfile,'w') as file:
                file.writelines(newlines)
    except:
        print(f"Error removing date: {date} from {logfile}")
        sys.exit(1)

if __name__ == "__main__":
    main()
