import matplotlib.pyplot as plt
import matplotlib as mplt
import matplotlib.animation as animation

import numpy as np

'''
A test script to see how streaming a plot/data may look like on python.
'''

def sigGen(fs, length, freq):
    time = np.linspace(0, length, fs*length)
    noise = np.random.normal(0,0.1,length)
    signal = np.sin(2*np.pi*freq*time)
    return signal

class Scope:
    def __init__(self, ax, maxt=2, dt=0.02, channels=1, y):
        self.channels = channels
        self.ax = ax
        self.dt = dt
        self.maxt = maxt
        self.tdata = [0]
        self.ydata = np.zeros((1,channels))
        self.lines = []
        for ch in range(self.channels):
            self.lines.append(mplt.lines.Line2D(self.tdata, self.ydata[:,ch]))
            self.ax.add_line(self.lines[ch])
        self.ax.set_ylim(-1.1, 1.1)
        self.ax.set_xlim(0, self.maxt)

    def update(self, i):
        lastt = self.tdata[-1]
        if lastt >= self.tdata[0] + self.maxt:  # reset the arrays
            self.tdata = [self.tdata[-1]]
            self.ydata = self.ydata[-1,:] 
            self.ax.set_xlim(self.tdata[0], self.tdata[0] + self.maxt)
            self.ax.figure.canvas.draw()

        # This slightly more complex calculation avoids floating-point issues
        # from just repeatedly adding `self.dt` to the previous value.
        t = self.tdata[0] + len(self.tdata) * self.dt

        self.tdata.append(t)
        y_update = np.zeros((1,self.channels))
        y_update[0,:] = y
        np.concatenate((self.ydata, y_update))
        print(self.ydata)
        for ch, line in enumerate(self.lines):
            line.set_data(self.tdata, list(self.ydata[:,ch]))
        return self.lines


if __name__ == '__main__':
    #np.random.seed(19680801 // 10)
    fig, ax = plt.subplots()
    fs = 100 # Hz
    length = 5 # seconds
    data = np.zeros((fs*length, 4))
    data[100:200,0] = sigGen(fs, 1, 10)
    data[300:400,1] = sigGen(fs, 1, 20)
    data[200:300,2] = sigGen(fs, 1, 5)
    data[150:250,3] = sigGen(fs, 1, 15)
    scope = Scope(ax, maxt=2, dt=1/fs, channels=4)
    ani = animation.FuncAnimation(fig, scope.update, interval=50, blit=True, save_count=200, repeat=False)
    plt.show()
