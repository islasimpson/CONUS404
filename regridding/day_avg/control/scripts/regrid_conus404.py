import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import xesmf as xe
import argparse

import warnings
warnings.filterwarnings('ignore')

def main():
    parser = argparse.ArgumentParser(description="Argument parser for regridding")
    parser.add_argument('--wgtfile', type=str, required=True, help='Location of temporary dir')
    parser.add_argument('--native_file',type=str, required=True, help='File on native grid')
    parser.add_argument('--grid_res',type=flexible_type, required=True, 
      help="The resolution of the output grid (if float then it's the grid spacing, if string then it's a file containing the grid")
    parser.add_argument('--itype',type=str, required=True, help='Type of interpolation (conservative of bilinear)')
    parser.add_argument('--reuse_wgts', action='store_true', required=False, help='Flag to reuse weights from previous call')
    parser.add_argument('--fileout', type=str, required=True, help='Filename for output')

    args = parser.parse_args()

    regrid_conus404(args.wgtfile, args.native_file, args.grid_res, args.itype, args.reuse_wgts, args.fileout)

def regrid_conus404(wgtfile, native_file, grid_res, itype, reuse_wgts, fileout):

    dat = xr.open_dataset(native_file)

    # Get lons and lats of output
    if isinstance(grid_res, str):
        gridoutvals = xr.open_dataset(grid_res)
        lon_out = gridoutvals.lon
        lat_out = gridoutvals.lat
        # Flipping longitudes to go from -180 to 180 if they go from 0 to 360
        if (lon_out.isel(lon=lon_out.size-1) > lon_out.isel(lon=0)):
            lon_out = fliplon_pos2neg(lon_out)

        # Flipping latitudes if they go from +90 to -90
        if (lat_out[len(lat_out)-1] < lat_out[0]):
            lat_out = lat_out[::-1]

        lon_out = lon_out.sel(lon=slice(-139,-57))
        lat_out = lat_out.sel(lat=slice(17,58))

        lon_out = np.array(lon_out)
        lat_out = np.array(lat_out)
    else:
        lon_out = np.arange(-139,-57, grid_res)
        lat_out = np.arange(17, 58, grid_res)

    if np.any(np.isnan(lon_out)) or np.any(np.isnan(lat_out)):
        raise ValueError("Longitude or latitude arrays contain NaN values.") 


    if (itype == 'conservative'):
        lon_in = dat.XLONG ; lat_in = dat.XLAT
        lon_in_b, lat_in_b = get_bounds(lon_in, lat_in)
        grid_in = construct_grid(lon_in, lat_in, lon_in_b, lat_in_b)

        lon_out_b, lat_out_b = get_bounds(lon_out, lat_out)
        grid_out = construct_grid(lon_out, lat_out, lon_out_b, lat_out_b)

        regridder = xe.Regridder(grid_in, grid_out, 'conservative', reuse_weights=reuse_wgts,
                                 filename=wgtfile)
        dat_rg = regridder(dat)
        lon1d = dat_rg.lon.isel(y=0)
        lat1d = dat_rg.lat.isel(x=0)
        dat_rg = dat_rg.drop_vars(['lon','lat'])
        dat_rg = dat_rg.assign_coords({'x':lon1d, 'y':lat1d})
        dat_rg = dat_rg.rename({'x':'lon', 'y':'lat'})
    elif (itype == 'bilinear'):
        grid_out = {'lon': lon_out,
                    'lat': lat_out
                   }
        regridder = xe.Regridder(dat, grid_out, 'bilinear', reuse_weights=reuse_wgts,
                                 filename=wgtfile)
        dat_rg = regridder(dat)

    dat_rg.to_netcdf(fileout)
        


#---Utilities for dealing with conservative remapping
def get_bounds(lon,lat):
    """ Obtain the longitude and latitude bounds for the xesmf regridder
        (Needed for conservative remapping)
    """

    # Case of a 2D lon/lat array
    if (np.array(lon).ndim == 2):
        nlat = lon[:,0].size
        nlon = lon[0,:].size

        lon_b = np.zeros([nlat + 1, nlon + 1])
        lat_b = np.zeros([nlat + 1, nlon + 1])

        lon_b[1:,1:-1] = (lon[:,1:] - lon[:,0:-1])/2. + lon[:,0:-1]
        lon_b[1:,0] = lon[:,0] - (lon[:,1] - lon[:,0])/2.
        lon_b[1:,-1] = lon[:,-1] + (lon[:,-1] - lon[:,-2])/2.
        lon_b[0,:] = lon_b[1,:]
        lon_b[-1,:] = lon_b[-2,:]

        lat_b[1:-1,1:] = lat[0:-1,:] + (lat[1:,:] - lat[0:-1,:])/2.
        lat_b[0,1:] = lat[0,:] - (lat[1,:] - lat[0,:])/2.
        lat_b[-1,1:] = lat[-1,:] + (lat[-1,:] - lat[-2,:])/2.
        lat_b[:,0] = lat_b[:,1]
        lat_b[:,-1] = lat_b[:,-2]

    else:
        nlat = lat.size
        nlon = lon.size

        lon_b = np.zeros( [nlon+1] )
        lat_b = np.zeros( [nlat+1] )

        lon_b[1:-1] = (lon[1:] - lon[0:-1])/2. + lon[0:-1]
        lon_b[0] = lon[0] - (lon[1]-lon[0])/2.
        lon_b[-1] = lon[-1] + (lon[-1] - lon[-2])/2.
        lon_b = np.tile(lon_b, (nlat+1,1))

        lat_b[1:-1] = lat[0:-1] + (lat[1:] - lat[0:-1])/2.
        lat_b[0] = lat[0] - (lat[1] - lat[0])/2.
        lat_b[-1] = lat[-1] + (lat[-1] - lat[-2])/2.
        lat_b = np.tile(lat_b[:,np.newaxis], (1, nlon+1))   

    return lon_b, lat_b


def construct_grid(lon, lat, lon_b, lat_b):
    """Construct the grid information (lons, lats, and bounds) for input to xesmf when 
       doing conservative remapping"""
    if (np.array(lon).ndim == 2):
        grid = {
            'lat': lat,
            'lon': lon,
            'lat_b': lat_b,
            'lon_b': lon_b
        }
    else:
        lon_2d = np.tile(lon[np.newaxis,:], (len(lat),1))
        lat_2d = np.tile(lat, (len(lon),1)).T
        grid = {
            'lat': lat_2d,
            'lon': lon_2d,
            'lat_b': lat_b,
            'lon_b': lon_b
        }
    return grid

def fliplon_pos2neg(lon):
    """flip longitudes if lon goes from 0 to 360"""
    lonflip = (lon + 180) % 360 - 180
    lonflip['lon'] = lonflip
    return lonflip 

def flexible_type(value):
    try:
        return float(value)
    except ValueError:
        return value 


if __name__ == "__main__":
    main()
