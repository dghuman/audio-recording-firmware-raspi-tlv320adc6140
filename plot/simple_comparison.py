import numpy as np

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.ticker import (MultipleLocator, AutoMinorLocator)

import pickle
import time
import os,sys
import soundfile as sf
from scipy.signal import butter, lfilter, freqz, find_peaks

f_12 = '/home/dilraj/Programs/ocean_test/data/SAANICH/BOAT_COMPATT/COMPATT_ch1-ch2_1_20240502_113407.flac'
f_34 = '/home/dilraj/Programs/ocean_test/data/SAANICH/BOAT_COMPATT/COMPATT_ch3-ch4_1_20240502_113243.flac'
data_12, rate_12 = sf.read(f_12)
data_34, rate_34 = sf.read(f_34)

# make one dataset
rate = np.concatenate((np.repeat(rate_12, 2), np.repeat(rate_34, 2)))
data = np.concatenate((data_12, data_34), axis=1)

fig = plt.figure(figsize=(8,8))
gs = mpl.gridspec.GridSpec(4,1)
gs.update(wspace=0., hspace=0.)

ax3 = plt.subplot(gs[(3)])
ax2 = plt.subplot(gs[(2)], sharex=ax3)#, sharey=ax3)
ax1 = plt.subplot(gs[(1)], sharex=ax3)#, sharey=ax3)
ax0 = plt.subplot(gs[(0)], sharex=ax3)#, sharey=ax3)
axs = [ax0, ax1, ax2, ax3]

heights = [0.025, 0.01, 0.03, 0.15]

for i in range(4):
    ax = axs[i]
    # get time axis
    ts   = 1e3 # from sec to x
    time = np.arange(0, len(data[:,i])) / rate[i] * ts
    # synchronize data sets manually
    if i <= 1:
        time += 0.20675*ts
        ax.text(0.01, 0.01, 'time-corrected', 
                ha='left', va='bottom', fontsize=8,
                transform = ax.transAxes)
    # raw data plot
    ax.plot(time, data[:,i], label='Ch %i - raw' %(i+1))
    # find peaks
    #peaks, properties = find_peaks(data[:,i], distance=rate_12*0.8, height=heights[i])
    #ax.plot(time[peaks], data[:,i][peaks], linestyle='', marker='x')
    # formatting
    ax.set_ylabel('Amplitude [V]')
    ax.legend(loc='upper right')
    # ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.grid(which='major', alpha=0.3)
    ax.grid(which='minor', alpha=0.05)
    if i < 3:
        ax.tick_params(axis='x', labelbottom=False)
    
#ax.set_xlim(14.02*ts, 14.07*ts)
ax.set_xlabel('Time [ms]')
fig.suptitle('Raw data, selected pulse')
plt.tight_layout()
plt.show()
