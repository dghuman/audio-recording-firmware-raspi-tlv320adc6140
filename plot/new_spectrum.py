import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib as mplt
from scipy import signal
import os, sys
import argparse
import soundfile as sf

def make_spec(framerate, waveform, figure, axis):
    win = signal.windows.hann(2**12,sym=False)
    N = len(waveform)
    SFT = signal.ShortTimeFFT(win=win, hop=int(len(win)/2), fs=framerate, mfft=int(len(win)*2), scale_to='magnitude')
    #Sx = SFT.stft(waveform)
    Sx = SFT.spectrogram(waveform)
    t_lo, t_hi = SFT.extent(N)[:2]
#    fmin = 30e3 # Hz
#    fmax = 50e3 # Hz
    #freq_slice = np.where((SFT.f >= fmin) & (SFT.f <= fmax))
    # keep only frequencies of interest
    #ef   = ef[freq_slice]    
    #Sx = Sx[freq_slice,:][0]
    Sx_dB = 20*np.log10(np.fmax(Sx,1e-12)) #1e-12 works well
    im1 = axis.imshow(Sx_dB, origin='lower', aspect='auto', extent=SFT.extent(N), cmap='viridis')
    figure.colorbar(im1, label=r"dB $20\log_{10}|S_{x}(t, f)|$")
    axis.set_title('Spectrogram')
    axis.set(xlabel='Time (s)', ylabel='Frequency (Hz)')
    return 0

def cut_data(framerate, waveform, t_start, t_end):
    sample_start = int(framerate*t_start)
    sample_end = int(framerate*t_end)
    return waveform[sample_start:sample_end + 1]

def main():    
    data, rate = sf.read(args.infile)
    if data.shape[1] > 1:
        data = data[:,1]
    fig1, ax1 = plt.subplots(figsize=(6., 4.))
    t_start = 0
    t_end = 30
    new_data = cut_data(framerate=rate, waveform=data, t_start=t_start, t_end=t_end)
    make_spec(rate, new_data, fig1, ax1)
    fig1.tight_layout()
    plt.show()
    plt.clf()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--infile')
    args = parser.parse_args()
    main()
