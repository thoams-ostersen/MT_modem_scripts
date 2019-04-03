# -*- coding: utf-8 -*-
"""
A basic script to visualise how your ModEM inversions have
progressed by plotting RMS against iteration.

Simply point the script to a log file and get a lovely plot.
You may need to concatenate logfiles from a series of 
inversion steps.
"""

# import necessary libraries
import os, re
import pandas as pd
import matplotlib.pyplot as plt

# define plot title
plot_title = 'RMS Decay Curve for Inversion 2'

# link logfile and make output filename
log_fn = r"D:\run27_grids\inv2.log"
outfn = log_fn.replace('.log','_RMS_vs_iter.csv')

# read log file lines and append to list
text = []
with open(log_fn,'r') as log:
    lines = log.readlines()
    for line in lines:
        text.append(line.strip('\n'))

# make list of iteration values
iteration_rms = []
for idx,i in enumerate(text):
    if idx == 2: # extract line 2 for starting RMS
        iteration_rms.append(re.split('\s+',i)[5:6])         
    if i.find('with:') != -1:
        iteration_rms.append(re.split('\s+',i)[5:6])
iteration_rms = map(''.join, iteration_rms)

# convert list to pandas data frame
df = pd.DataFrame.from_dict(iteration_rms)
df = df.rename(columns = {0:'RMS'})
df = df.astype(float)
df['iter'] = df.index 
df = df[['iter','RMS']]

# write output csv file for later plotting
df.to_csv(outfn,sep=',',index=False)

# make plot of RMS vs iteration
df.plot(x='iter',y='RMS',linewidth=5.0,solid_capstyle='round')
plt.xlabel('Iteration')
plt.ylabel('Global RMS')
plt.legend().set_visible(False)
plt.title(plot_title)

# save plot to pdf file and show
figname = log_fn.replace('.log','_RMS_vs_iter.pdf')
plt.savefig(figname,dpi=300)
plt.show()





