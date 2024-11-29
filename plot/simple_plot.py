import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mplt
from scipy import signal
import soundfile as sf
import os
import hist
from hist import Hist
from mplhep.plot import histplot
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-i', '--infile')

args = parser.parse_args()

music_file = args.infile 

fig = plt.figure()
gs = fig.add_gridspec(2, 2, hspace=0)
ax1, ax2 = gs.subplots(sharex='col')
axes = [ax1, ax2]
data, rate = sf.read(music_file)
t = np.linspace(0, len(data)/rate, len(data))
heights = [0.01, 0.02]
lows = [0.001, 0.01]

hists=[]
signals = []

bin_count = 100

for i in range(2):
    hists.append(Hist(hist.axis.Regular(bins=bin_count, start=-1, stop=1, name=f'ch{i+1}')))
    signals.append(Hist(hist.axis.Regular(bins=bin_count, start=-1, stop=1, name=f'ch{i+1} signal')))
    hists[-1].fill(data[:,i])
    
for ch in range(data.shape[1]):
    peaks, properties = signal.find_peaks(data[:,ch], distance=rate*0.05, height=heights[ch])
    signals[ch].fill(data[:,ch][peaks])
    axes[ch][0].plot(t, data[:,ch])
    axes[ch][0].plot(t[peaks], data[:,ch][peaks], "x")
    hists[ch].plot(ax=axes[ch][1])
    signals[ch].plot(ax=axes[ch][1])
    axes[ch][1].set_yscale("log")
        
#axes[0][0].set_xlabel("time (s)")
#plt.ylabel("V")
plt.show()
plt.clf()

