import tkinter as tk

import tkinter

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np

import h5py
import time


root = tkinter.Tk()
root.wm_title("Embedding in Tk")

fig = Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
ax = fig.add_subplot(111)
ax.plot(t, 2 * np.sin(2 * np.pi * t))

canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)


def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)


canvas.mpl_connect("key_press_event", on_key_press)


def _quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate


button = tkinter.Button(master=root, text="Quit", command=_quit)
button.pack(side=tkinter.BOTTOM)

def get_plot_data(slice_vars):
    global dset
    dset.id.refresh()
    #Simulate lag...
    time.sleep(5)
    return dset[:,0]

from multiprocessing.pool import ThreadPool
pool = ThreadPool(processes=1)

async_result = pool.apply_async(get_plot_data, ('params',)) # tuple of args

# do some other stuff in the main process

i = 0
f = h5py.File("swmr.h5", 'r', libver='latest', swmr=True)
dset = f["data"]
while True:
    if async_result.ready():
        return_val = async_result.get()  # get the return value from your function.
        i += 0.1
        ax.clear()
        # ax.plot(t, 2 * np.sin(2 * np.pi * t+i))
        ax.plot(return_val)
        canvas.draw()
        async_result = pool.apply_async(get_plot_data, ('params',)) # tuple of args

    #tkinter.mainloop()
    root.update_idletasks()
    root.update()
# If you put root.destroy() here, it will cause an error if the window is
# closed with the window manager.
