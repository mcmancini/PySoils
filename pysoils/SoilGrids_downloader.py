'''
SoilGrids data downloader.
==========================

Authors: Mattia Mancini, Mingyuan Chen
Created: 24-October-2023
--------------------------

Script that downlaods and stores soil data retrieved from the SoilGrids dataset.

The SoilGrids dataset can be found at https://www.isric.org/explore/soilgrids;
it was downloaded using the soilgrids 0.1.3 library (https://pypi.org/project/soilgrids/)
Docs at https://www.isric.org/explore/soilgrids/faq-soilgrids and
https://maps.isric.org/

Soil data from SoilGrids requires
to be processed as follows:
    - 1. Compute depth weighted averages of all values: the raw data is
            reported by depth, but we want averages for 0-60cm.
    - 2. Rescale values based on the conversion factors reported at
            https://www.isric.org/explore/soilgrids/faq-soilgrids

'''

# import libraries
import time
from soilgrids import SoilGrids
import xarray as xr
from pyproj import Transformer
import numpy as np
import kwargs
# import os
# import multiprocessing as mp

# create Constants class
class Constants:
    '''Pass all constants as class attributes.'''

    def __init__(self):
        '''Initialize Constants object.'''
        self.soil_vars = ['bdod', 'cec', 'cfvo', 'clay',
                          'nitrogen', 'phh2o', 'sand', 'silt', 'soc', 'ocd', 'ocs']
        self.soil_depth = ['0-5', '5-15',
                           '15-30', '30-60', '60-100', '100-200']

# create SoilApp class
class SoilApp:
    '''Create a SoilApp object.'''
    @staticmethod
    def mult_hundred(x: float):
        '''Multiply by 100.'''
        return x*100

    @staticmethod
    def mult_ten(x: float):
        '''Multiply by 10.'''
        return x*10

    @staticmethod
    def div_ten(x: float):
        '''Divide by 10.'''
        return x/10

    @staticmethod
    def div_hundred(x: float):
        '''Divide by 100.'''
        return x/100

    @staticmethod
    def NoConversion(x: float):
        '''No conversion.'''
        return x

    def __init__(self):
        '''Initialize SoilApp object.'''

        self._obs_conversions = {
            "bdod": self.mult_hundred,
            "cec": self.div_ten,
            "cfvo": self.div_ten,
            "clay": self.div_ten,
            "nitrogen": self.div_hundred,
            "phh2o": self.div_ten,
            "sand": self.div_ten,
            "silt": self.div_ten,
            "soc": self.div_ten,
            "ocd": self.div_ten,
            "ocs": self.mult_ten
        }

    def on_demand_download(self, geo_type: str, geo_code0: float, geo_code1: float):
        '''On-demand download SoilGrids data for a given geo-code.'''

        if geo_type == 'CRS':
            west, east, south, north = geo_code0 - 0.5e6, geo_code0 + \
                0.5e6, geo_code1 - 0.8e6, geo_code1 + 0.8e6
            transformer = Transformer.from_crs(27700, 4326, always_xy=True)
            bl = transformer.transform(west, south)
            br = transformer.transform(east, south)
            tl = transformer.transform(west, north)
            tr = transformer.transform(east, north)
        elif geo_type == 'lat-lon':
            transformer = Transformer.from_crs(4326, 27700, always_xy=True)
            x1, y1 = transformer.transform(geo_code0, geo_code1)
            west, east, south, north = x1 - 0.5e6, x1 + 0.5e6, y1 - 0.8e6, y1 + 0.8e6
            transformer = Transformer.from_crs(27700, 4326, always_xy=True)
            bl = transformer.transform(west, south)
            br = transformer.transform(east, south)
            tl = transformer.transform(west, north)
            tr = transformer.transform(east, north)
        else:
            print('Invalid geo_type. Please enter a valid geo_type("CRS" or "lat-lon").')
            return

        # get soil data
        soil_grids = SoilGrids()

        soilvars = Constants().soil_vars
        soil_depths = Constants().soil_depth

        counter = 1
        soil_data = xr.Dataset()

        for var in soilvars:
            print(
                f'Processing variable {counter} of {len(soilvars)}: \'{var}\'')
            soil_chunk = xr.Dataset()
            if var == 'ocs':
                while True:  # required because the server sometimes returns a 500 error
                    depth = '0-30'
                    try:
                        soil_data[var] = soil_grids.get_coverage_data(service_id=var, coverage_id=f'{var}_{depth}cm_mean',
                                                                      west=bl[0], south=bl[1], east=br[0], north=tr[1],
                                                                      width=4000, height=6400,
                                                                      crs='urn:ogc:def:crs:EPSG::4326', output='tmp.tif')
                        # conversion to conventional units
                        func = self._obs_conversions[var]
                        soil_data[var] = func(soil_data[var])
                    except:
                        print("get_coverage_data failed. Retrying in 60 seconds...")
                        time.sleep(60)
                        continue
                    break
            else:
                for depth in soil_depths:
                    while True:
                        try:
                            soil_chunk[depth] = soil_grids.get_coverage_data(service_id=var, coverage_id=f'{var}_{depth}cm_mean',
                                                                             west=bl[0], south=bl[1], east=br[0], north=tr[1],
                                                                             width=4000, height=6400,
                                                                             crs='urn:ogc:def:crs:EPSG::4326', output=('tmp.tif'))
                            # conversion to conventional units
                            func = self._obs_conversions[var]
                            soil_chunk[depth] = func(soil_chunk[depth])
                        except:
                            print(
                                "get_coverage_data failed. Retrying in 60 seconds...")
                            time.sleep(60)
                            continue
                        break

                # Weighted average of soil variables for depths up to 60cm
                weight_factor = {
                    '0-5': 1,
                    '5-15': 2,
                    '15-30': 3,
                    '30-60': 6
                }

                # (i.e. xr.DataArray()) because dimensions cannot change for in-place operations
                soil_data[var] = soil_chunk[depth] * 0

                for key in weight_factor.keys():
                    df = soil_chunk[key] * weight_factor[key]
                    soil_data[var] += df

                soil_data[var] = soil_data[var] / 12
                soil_data[var] = soil_data[var].where(
                    soil_data[var] != 0, np.nan)
                counter += 1
                time.sleep(60)

        return soil_data

    def bulk_download(self, xmin: float, xmax: float, ymin: float, ymax: float):
        '''bulk download SoilGrids data for a given boundary.'''

        # get soil data
        soil_grids = SoilGrids()

        soilvars = Constants().soil_vars
        soil_depths = Constants().soil_depth

        counter = 1
        soil_data = xr.Dataset()
        for var in soilvars:
            print(
                f'Processing variable {counter} of {len(soilvars)}: \'{var}\'')
            soil_chunk = xr.Dataset()
            if var == 'ocs':
                while True:  # required because the server sometimes returns a 500 error
                    depth = '0-30'
                    try:
                        soil_data[var] = soil_grids.get_coverage_data(service_id=var, coverage_id=f'{var}_{depth}cm_mean',
                                                                      west=xmin, south=ymin, east=xmax, north=ymax,
                                                                      width=4000, height=6400,
                                                                      crs='urn:ogc:def:crs:EPSG::4326', output=('tmp.tif'))
                        # conversion to conventional units
                        func = self._obs_conversions[var]
                        soil_data[var] = func(soil_data[var])
                    except:
                        print("get_coverage_data failed. Retrying in 60 seconds...")
                        time.sleep(60)
                        continue
                    break
            else:
                for depth in soil_depths:
                    import requests.exceptions
                    while True:
                        try:
                            soil_chunk[depth] = soil_grids.get_coverage_data(service_id=var, coverage_id=f'{var}_{depth}cm_mean',
                                                                             west=xmin, south=ymin, east=xmax, north=ymax,
                                                                             width=4000, height=6400,
                                                                             crs='urn:ogc:def:crs:EPSG::4326', output=('tmp.tif'))
                            # conversion to conventional units
                            func = self._obs_conversions[var]
                            soil_chunk[depth] = func(soil_chunk[depth])
                        except:
                            print(
                                "get_coverage_data failed. Retrying in 60 seconds...")
                            time.sleep(60)
                            continue
                        break

                # Weighted average of soil variables for depths up to 60cm
                weight_factor = {
                    '0-5': 1,
                    '5-15': 2,
                    '15-30': 3,
                    '30-60': 6
                }
                # empty array to store the weighted average. Can't be an empty object
                # (i.e. xr.DataArray()) because dimensions cannot change for in-place operations
                soil_data[var] = soil_chunk[depth] * 0

                for key in weight_factor.keys():
                    df = soil_chunk[key] * weight_factor[key]
                    soil_data[var] += df

                soil_data[var] = soil_data[var] / 12
                soil_data[var] = soil_data[var].where(
                    soil_data[var] != 0, np.nan)
                counter += 1
                time.sleep(60)

        soil_data.to_netcdf('GB_soil_data.nc')
        return soil_data
