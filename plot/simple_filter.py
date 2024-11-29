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
gs = fig.add_gridspec(2, 1, hspace=0)
axes = gs.subplots(sharex='col')
data, rate = sf.read(music_file)
t = np.linspace(0, len(data)/rate, len(data))

def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = signal.butter(N=order, Wn=[lowcut, highcut] , btype='band', fs=fs)
    y = signal.lfilter(b, a, data)
    return y

for ch in range(data.shape[1]):
    filtered_data = butter_bandpass_filter(data=data[:,ch], lowcut=10000, highcut=40000, fs=rate)
    axes[ch].plot(t, filtered_data)
    
        
#axes[0][0].set_xlabel("time (s)")
#plt.ylabel("V")
plt.show()
plt.clf()

