# -*- coding: utf-8 -*-
"""
This script fixes UBC mesh files output by Naser Meqbel's 
3DGrid software. It uses location information gleaned from
a ModEM format data file to edit the UBC mesh so as to ensure
the UBC model ends up in the right location when imported into
3D viewing software.

Currently configured for the UTM zone 55 coordinate system. 
You can edit this to fit the UTM zone of your models.
"""

# import necessary libraries
import os, re, pyproj
import numpy as np
import mtpy.modeling.modem as modem

# UBC mesh file and ModEM data file locations
inmesh = r"D:\your_directory\run3_4_NLCG_026_UBC.mesh"
modem_dat = r"D:\your_directory\run3_4_NLCG_026.dat"

# define output UTM coordinate system
out_sys = 'epsg:28355' # MGA55
'''
Find your coordinate system epsg code at http://spatialreference.org/ref/epsg/
'''

# open mesh file and extract coordinate data to a list
data = []
with open(inmesh,'r') as dat:
    lines = dat.readlines()
    for line in lines:
        line = re.sub("\s+", ",", line.strip())
        data.append(line)

x = map(float,(data[2].split(',')))
y = map(float,(data[3].split(',')))
z = map(float,(data[4].split(',')))

# read ModEM data file, get site coordinates and compute centre point
dat = modem.Data()
dat.read_data_file(modem_dat)
stations = dat.station_locations

stations_x = stations.lon
stations_y = stations.lat

centre_x = np.min(stations_x) + ((np.max(stations_x) - np.min(stations_x))/2)
centre_y = np.min(stations_y) + ((np.max(stations_y) - np.min(stations_y))/2)

# convert centre of dataset into MGA55 coordinates
inproj = pyproj.Proj(init='epsg:4326')
outproj = pyproj.Proj(init=out_sys)
m_east, m_north = pyproj.transform(inproj,outproj,centre_x,centre_y)

# print some details to console/terminal
print 'In WGS84 coordinates data centre point is:', centre_x, 'E, and', centre_y, 'N.'
print 'In MGA55 coordinates data centre point is:', m_east, 'm East, and', m_north, 'm North.'

# calculate mesh southwest corner
e_corner = m_east - (sum(x)/2)
n_corner = m_north - (sum(y)/2)
mesh_line_2 = e_corner,n_corner,0.000
print 'Southwest corner is:', e_corner, 'm East, and', n_corner, 'm North.'

# re-write the old mesh file
with open(inmesh,'w') as out_mesh:
    out_mesh.write(data[0].replace(',','\t'))
    out_mesh.write('\n')
    out_mesh.write('\t'.join(map(str,mesh_line_2)))
    out_mesh.write('\n')
    out_mesh.write(data[2].replace(',','\t'))
    out_mesh.write('\n')
    out_mesh.write(data[3].replace(',','\t'))
    out_mesh.write('\n')
    out_mesh.write(data[4].replace(',','\t'))

# print confirmation
print 'Fixed Naser Meqbel\'s 3DGrid UBC mesh file. Ready for import into viewing software.'
