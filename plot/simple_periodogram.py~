import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib as mplt
from scipy import signal
from scipy.fft import fft, fftfreq
import os, sys
import argparse
import soundfile as sf

parser = argparse.ArgumentParser()

parser.add_argument('-i', '--infile')

args = parser.parse_args()


def make_spec(framerate, waveform):
    win = signal.windows.hann(2**14,sym=False)
    ef, et, Sxx = signal.spectrogram(waveform, fs=framerate, scaling='spectrum', window=win) #window=win
    fmin = 1e3 # Hz
    fmax = 50e3 # Hz
    freq_slice = np.where((ef >= fmin) & (ef <= fmax))
    # keep only frequencies of interest
    ef   = ef[freq_slice]
    Sxx = Sxx[freq_slice,:][0]
    plt.pcolormesh(et,ef/1e3,np.log10(Sxx),cmap='jet', shading='gouraud') #cmap = 'plasma'
    plt.title(f'Periodogram')
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (kHz)')
    return 0

data, rate = sf.read(args.infile)
if data.shape[1] > 1:
    data = data[:,1]
print(f"rate is {rate}")
make_spec(rate, data)
plt.show()
plt.clf()
