# -*- coding: utf-8 -*-
"""
This script reads ModEM .rho and .dat files in order to generate
UTM projected depth slice grids as geotiffs.

ModEM .rho files must have consistent dimensions in X and Y 
directions. Must input correct number of padding cells and 
define top of model.

Currently configured to output grids in MGA55. This may need
tweaking for your UTM zone.

Requirements:
    - MTpy
    - GDAL_TRANSLATE executable from windows cmd

"""

# import necessary libraries
import os, subprocess
import numpy as np
import pandas as pd
import mtpy.modeling.modem as modem 

# define ModEM model and data files from which grids will be generated
modem_rho = r"D:\run2_7_NLCG_031.rho"
modem_dat = r"D:\run2_7_NLCG_031.dat"

# set some key model parameters
y_pad_cells = 15    # input number of x padding cells
x_pad_cells = 15    # input number of y padding cells
model_top = 0       # input elevation of model top in metres, negative above sea level

# generate an output directory in data directory
outdir = os.path.join(os.path.dirname(modem_rho),'geotiff_slices')
if not os.path.exists(outdir):  # check to see if outdir already exists
    os.mkdir(outdir)            # if not, make outdir

# read data and model files using MTpy.ModEM and extract cell size
data = modem.Data()
data.read_data_file(data_fn=modem_dat)
model = modem.Model()
model.read_model_file(model_fn=modem_rho)
cell_size = model.cell_size_east    # assuming cells are the same dimensions in x and y here

# print some details to console/terminal
print 'Model cell size is:', cell_size
print 'Number of padding cells in x direction:', x_pad_cells
print 'Number of padding cells in y direction:', y_pad_cells

# get centre position of model grid in UTM coordinates from data file 
x0, y0 = [np.median(data.station_locations.station_locations[dd] 
        - data.station_locations.station_locations['rel_' + dd]) 
        for dd in ['east', 'north']]

# save a GOCAD sgrid file to same directory as rho and dat file
sgrid_out = modem_rho.replace('.rho','_sgrid')
model.write_gocad_sgrid_file(fn=sgrid_out,origin=[x0,y0,model_top])

# print some details to console/terminal
print '\n','GOCAD Sgrid file saved as:','\n','\t',sgrid_out,'\n'

# read newly saved sgrid as a pandas data frame and make a list of unique z values for slicing
sgrid = os.path.join(os.path.dirname(sgrid_out),(os.path.basename(sgrid_out) + '__ascii@@'))
sgrid_df = pd.read_csv(sgrid,sep='\s+',skiprows=[0,1,2],
            names=['x','y','z','rho'],usecols=[0,1,2,3])

unique_values = pd.Series({i: sgrid_df[i].unique() for i in sgrid_df})
depth_list = unique_values['z']

# loop through depth list and generate depth-specific data frames from the sgrid data frame
for z in depth_list[:-1]: # skip last depth slice as it has nonsense rho values
    depth_slice = sgrid_df.loc[sgrid_df['z'] == z]  # extract a depth-specific data frame
    depth_slice = depth_slice.drop('z',1)           # drop unnecessary z values
    
    # read x and y columns to make easting and northing padding cell lists
    unique_val = pd.Series({i: depth_slice[i].unique() for i in depth_slice})

    x_cells = unique_val['x']
    xpadding = np.append((x_cells[np.argsort(x_cells)[:x_pad_cells]]),
            (x_cells[np.argsort(x_cells)[-x_pad_cells:]]))
    
    y_cells = unique_val['y']
    ypadding = np.append((y_cells[np.argsort(y_cells)[:y_pad_cells]]),
                (y_cells[np.argsort(y_cells)[-y_pad_cells:]]))

    # loop through padding cell lists to remove padding cells from depth slice data frame
    for k in xpadding:
        depth_slice = depth_slice[depth_slice.x !=k]
    for l in ypadding:
        depth_slice = depth_slice[depth_slice.y !=l]

    # sort data frame so can be read by GDAL_TRANSLATE
    depth_slice = depth_slice.sort_values(['y','x'],ascending=[False,True])

    # make x and y values whole numbers 
    depth_slice['x'] = depth_slice['x'].round(0)
    depth_slice['y'] = depth_slice['y'].round(0)

    # save depth slice as csv file in out directory
    slice_suffix = str(round((z)/1000,2)) + '_km.csv'           # generate suffix for csv files
    out_csv = os.path.join(outdir,('slice_' + slice_suffix))
    depth_slice.to_csv(path_or_buf=out_csv,sep=',',index=False) # save csv file for specific depth

    # print some details to console/terminal
    print '\n','csv for',z/1000,'km depth slice saved as:','\n','\t',out_csv
    
    # run GDAL_TRANSLATE on csv files as a subprocess to generate ESRI ASCII grids
    gdal_asci_cmd = 'gdal_translate -a_srs "EPSG:28355" -of AAIGrid %s %s' %(out_csv,out_csv.replace('.csv','_grid.asc'))
    subprocess.call(gdal_asci_cmd,cwd=outdir,shell=True)

    # run GDAL_TRANSLATE on ESRI ASCII grids to generate geotiffs
    gdal_geotiff_cmd = 'gdal_translate -of "GTiff" -a_srs "EPSG:28355" %s %s' %(out_csv.replace('.csv','_grid.asc'),out_csv.replace('.csv','_grid.tiff'))
    subprocess.call(gdal_geotiff_cmd,cwd=outdir,shell=True)
    
    # clean up directroy by deleting all csv, proj and asci grid files
    subprocess.call('del *.asc',cwd=outdir,shell=True)
    subprocess.call('del *.prj',cwd=outdir,shell=True)
    subprocess.call('del *.csv',cwd=outdir,shell=True)
