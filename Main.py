import tkinter as tk

from tkinter import*

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np

import h5py
import time


root = tk.Tk()
root.wm_title("Embedding in Tk")

# panedwindow object 
pw = PanedWindow(orient ='vertical', master=root) 
pw.pack(fill=BOTH, expand=1)

fig = Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
ax = fig.add_subplot(111)
ax.plot(t, 2 * np.sin(2 * np.pi * t))

# canvas = FigureCanvasTkAgg(fig, master=pw)  # A tk.DrawingArea.
# canvas.draw()
# canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
# # This will add button widget to the panedwindow 
# pw.add(canvas.get_tk_widget())

canvas_frame = Frame(root)
canvas = FigureCanvasTkAgg(fig, master = canvas_frame)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
toolbar = NavigationToolbar2Tk(canvas, canvas_frame)
toolbar.update()
toolbar.pack_configure(expand=True)
pw.add(canvas_frame)



# toolbar = NavigationToolbar2Tk(canvas, root)
# toolbar.update()
# canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


def on_key_press(event):
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)


canvas.mpl_connect("key_press_event", on_key_press)


def _quit():
    root.quit()     # stops mainloop
    root.destroy()  # this is necessary on Windows to prevent
                    # Fatal Python Error: PyEval_RestoreThread: NULL tstate


button = tk.Button(master=root, text="Quit", command=_quit)
button.pack(side=tk.BOTTOM)
pw.add(button)

def get_plot_data(slice_vars):
    global dset
    dset.id.refresh()
    #Simulate lag...
    time.sleep(5)
    return dset[:,0]

from multiprocessing.pool import ThreadPool
pool = ThreadPool(processes=1)

i = 0
f = h5py.File("swmr.h5", 'r', libver='latest', swmr=True)
dset = f["data"]
async_result = pool.apply_async(get_plot_data, ('params',)) # tuple of args
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
