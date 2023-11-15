# README: SoilGrids dataset downloader

## Introduction

This is a downloader for the Soil data. We will start with the [SoilGrids dataset](https://www.isric.org/explore/soilgrids). \
It was downloaded using the [soilgrids 0.1.3 library](https://pypi.org/project/soilgrids/). Docs can be found [here](https://www.isric.org/explore/soilgrids/faq-soilgrids).

The idea here is to have two functionalities implemented:

- on-demand download through geographic querying (e.g., passing a lon-lat pair, or an OS grid code for the UK) the relevant soil data from the SoilGrids API. Data in this case is not saved to disk.
- Bulk download of soil data from a geographic area defined with a bounding box to be saved on disk in .netCDF format.

## Authors, affiliation and licence

**Mattia Mancini**: Land, Environment, Economics and Policy Institute (LEEP), University of Exeter, Exeter EX4 4PU, United Kingdom. Email: <m.c.mancini@exeter.ac.uk>

**Mingyuan Chen**: Land, Environment, Economics and Policy Institute (LEEP), University of Exeter, Exeter EX4 4PU, United Kingdom. Email: <M.Chen2@exeter.ac.uk>

This work is licensed under.

## Table of contents

- [README: SoilGrids dataset downloader](#readme-soilgrids-dataset-downloader)
  - [Introduction](#introduction)
  - [Authors, affiliation and licence](#authors-affiliation-and-licence)
  - [Table of contents](#table-of-contents)
  - [Package installation](#package-installation)
  - [Usage](#usage)
  - [Test](#test)
  - [References](#references)

## Package installation

## Usage

- We create a SoilApp object, which the user needs to initialise as follows: `soil_app = SoilApp()`
- This object contains two methods: `download()` and `bulk_download()`
- `download()` takes as only argument a dictionary containing either {'lon': longitude, 'lat': latitude} coordinates or {'OS_code': os_grid_code}
- `bulk_download()` which requires the coordinates defining the rectangular bounding box of the area of interest and the path in which the downloaded data will be stored as follows:
  - `xmin` = the longitude of the left corners of the bounding box of interest;
  - `xmax` = the longitude of the right corners of the bounding box of interest;
  - `ymin` = the latitude of the bottom corners of the bounding box of interest;
  - `ymax` = the latitude of the top corners of the bounding box of interest;
  - `save_path` = the directory in which the downloaded data will be stored.

At a later stage, we will add the possibility of downloading data also from the [World Harmonized Soil Database](https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v12/en/).

## Test

## References
