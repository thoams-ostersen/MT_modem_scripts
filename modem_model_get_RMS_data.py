# -*- coding: utf-8 -*-
"""
This script reads ModEM inversion response (.res) files and calculates RMS
values for each component of each site used in listed.

The script outputs a .csv file containing site ID, WGS84 coordinates,
MGA55 coordinates, Total RMS as well as RMS values for the various Z and 
T components.
"""

# import necessary libraries
import numpy as np
import os.path as op
from pyproj import Proj, transform

# set projections for data outputs
wgs84_proj = Proj(init='epsg:4326')    
mga55_proj = Proj(init='epsg:28355')  

# link to response file of interest
res_file=r"D:\Google Drive\university\tas_MT\modelling\3D\KUTh_inversions\no_topo_modelling\inv2\run2_7_NLCG_031.res"
    
# read res file to get column names
f = open(res_file)
f.readline()        # read first line to get past it
line = f.readline() # get the second line
names = line.strip().split()[1:]

# load data into a np array ignoring comment lines starting with > and #
data = np.loadtxt(res_file,comments=[">","#"],dtype = str)

# define some parameters
residuals = data[:,8:10].astype(float)
errors = data[:,10].astype(float)
stations = data[:,1]
station_coords = data[:,1:4]
components = data[:,7]
components_unique = np.unique(components)
totalrms = ((sum((residuals[:,0]/errors)**2) + sum((residuals[:,1]/errors)**2))/(len(data)*2.))**0.5

# empty array to contain rms
rms = np.zeros((len(np.unique(stations)),12),dtype='S10')

# loop through the stations
for i, station in enumerate(np.unique(station_coords,axis=0)):
    cond = stations==station[0]
    stationrms = ((sum((residuals[:,0][cond]/errors[cond])**2) + \
        sum((residuals[:,1][cond]/errors[cond])**2))/(len(data[cond])*2.))**0.5
    rms[i,0] = station[0]
    
    # add WGS84 coordinates
    rms[i,1] = station[1]
    rms[i,2] = station[2]

    # project MGA55 cooridantes and add to rms array
    utm_E, utm_N = transform(wgs84_proj,mga55_proj,station[2],station[1])
    rms[i,3] = utm_E
    rms[i,4] = utm_N

    # add rms data
    rms[i,5] = stationrms
    
    # cycle through components and append rms
    for ii, cpt in enumerate(components_unique):
        # condition to select the correct residuals for the component
        cond1 = cond&(components == cpt)
        try:
            stationrms = ((sum((residuals[:,0][cond1]/errors[cond1])**2) + \
                               sum((residuals[:,1][cond1]/errors[cond1])**2))/(len(data[cond1])*2.))**0.5
            rms[i,ii+6] = stationrms
        except:
            print "couldn't calculate", cpt, "component RMS for site", station[0]

# generate file name and header for output csv 
outfile = open(res_file.replace('.res','_RMS.csv'),'w')
header = 'Station, WGS84_lat, WGS84_lon, MGA55_E, MGA55_N, totalRMS, {}RMS, {}RMS, {}RMS, {}RMS, {}RMS, {}RMS\n'.format(*(list(components_unique)))

# write rms array to output csv
outfile.write(header)
for line in rms:
    outfile.write(','.join(list(line))+'\n')
outfile.close()