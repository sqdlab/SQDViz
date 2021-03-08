import tkinter as tk
from tkinter import*

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np
import h5py
from multiprocessing.pool import ThreadPool

import time

class MainForm:
    def __init__(self):
        self.root = tk.Tk()
        self.root.wm_title("SQDviz - Data visualisation tool")

        #Left-hand side (plots and the plot-selection)
        pw_LHS = PanedWindow(orient ='vertical', master=self.root) 
        pw_LHS.pack(fill=BOTH, expand=1)
        self.plot_main = self._generate_plot_frame()
        pw_LHS.add(self.plot_main['frame'],stretch='always')
        # self.plot_slice = self._generate_plot_frame()
        # pw_LHS.add(self.plot_slice['frame'])
        button = tk.Button(master=self.root, text="Quit", command=self._event_quit)
        button.pack(side=tk.BOTTOM)
        pw_LHS.add(button)


        self.plot_main['canvas'].mpl_connect("key_press_event", self._event_form_on_key_press)

        self.data_thread_pool = ThreadPool(processes=1)

        f = h5py.File("swmr.h5", 'r', libver='latest', swmr=True)
        self.dset = f["data"]
        self.async_result = self.data_thread_pool.apply_async(self.get_plot_data, ('params',)) # tuple of args

    def main_loop(self):
        i = 0
        while True:
            if self.async_result.ready():
                return_val = self.async_result.get()  # get the return value from your function.
                i += 0.1
                self.plot_main['ax'].clear()
                # ax.plot(t, 2 * np.sin(2 * np.pi * t+i))
                self.plot_main['ax'].plot(return_val)
                self.plot_main['canvas'].draw()
                self.async_result = self.data_thread_pool.apply_async(self.get_plot_data, ('params',)) # tuple of args

            #tkinter.mainloop()
            self.root.update_idletasks()
            self.root.update()
        # If you put root.destroy() here, it will cause an error if the window is
        # closed with the window manager.

    
    def get_plot_data(self,slice_vars):
        global dset
        self.dset.id.refresh()
        #Simulate lag...
        time.sleep(5)
        return self.dset[:,0]

    def _generate_plot_frame(self):
        fig = Figure()
        t = np.arange(0, 3, .01)
        ax = fig.gca() #fig.add_subplot(111)
        ax.plot(t, 2 * np.sin(2 * np.pi * t))

        canvas_frame = Frame(master=self.root)

        canvas = FigureCanvasTkAgg(fig, master = canvas_frame)
        # canvas.draw()
        toolbar = NavigationToolbar2Tk(canvas, canvas_frame)
        canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=1,anchor=tk.N)
        toolbar.update()
        toolbar.pack_configure(side=tk.TOP, expand=True)

        return {'fig':fig, 'ax':ax, 'frame':canvas_frame, 'canvas':canvas, 'toolbar':toolbar}


    def _event_form_on_key_press(self,event):
        print("you pressed {}".format(event.key))
        key_press_handler(event, self.plot_main['canvas'], self.plot_main['toolbar'])

    def _event_quit():
        root.quit()     # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    