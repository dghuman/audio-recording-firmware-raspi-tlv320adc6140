import matplotlib.pyplot as plt
import matplotlib as mplt
import numpy as np
import soundfile as sf
import os
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

for ch in range(data.shape[1]):
    axes[ch].plot(t, data[:,ch])
    
#axes[0][0].set_xlabel("time (s)")
plt.xlabel("time (s)")
plt.show()
plt.clf()

