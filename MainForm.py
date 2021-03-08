import tkinter as tk
from tkinter import*

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np
from multiprocessing.pool import ThreadPool

from DataExtractorH5single import*

class MainForm:
    def __init__(self):
        self.root = tk.Tk()
        self.root.wm_title("SQDviz - Data visualisation tool")

        self.frame_LHS = Frame(master=self.root)

        ###################
        #MAIN PLOT DISPLAY#
        ###################
        self.pw_plots_main = PanedWindow(orient ='vertical', master=self.frame_LHS)
        self.plot_main = self._generate_plot_frame()
        self.pw_plots_main.add(self.plot_main['frame'],stretch='always')
        self.plot_slice = self._generate_plot_frame()
        self.pw_plots_main.add(self.plot_slice['frame'])
        #
        self.pw_plots_main.grid(row=0,column=0,sticky='nsew')
        ###################

        #########################
        #PLOT SELECTION CONTROLS#
        #########################
        #
        #Overall frame broken up into columns containing individual frames...
        self.frame_plot_sel = LabelFrame(master=self.frame_LHS, text = "Plot Parameters")
        #
        #######################################
        #RADIO BUTTONS FOR PLOT TYPE SELECTION#
        frm_plttyp = Frame(master=self.frame_plot_sel)
        cur_row = 0
        #
        #Labelled frame container with the radio buttons stored in the variable self.plot_dim_type
        lblfrm_plot_type = LabelFrame(frm_plttyp, text = "Plot Type", padx=10, pady=10)
        lblfrm_plot_type.grid(row=cur_row,column=0)
        self.plot_dim_type = tk.IntVar()
        self.plot_dim_type.set(1)
        tk.Radiobutton(lblfrm_plot_type, text="1D Plot", padx = 20, variable=self.plot_dim_type, value=1, command=self._event_plotsel_changed).grid(row=0, column=0)
        tk.Radiobutton(lblfrm_plot_type, text="2D Plot", padx = 20, variable=self.plot_dim_type, value=2, command=self._event_plotsel_changed).grid(row=1, column=0)
        #
        frm_plttyp.grid(row=0,column=0)
        #######################################
        #
        #######################################
        #LISTBOXES FOR AXIS VARIABLE SELECTION#
        frm_lstbxes = Frame(master=self.frame_plot_sel)
        rcOff = (0,0) #Axis listbox row-column offset to make it easier to resposition the listboxes
        #x-Axis column
        lbl_axis_x = Label(frm_lstbxes, text = "x-axis")
        lbl_axis_x.grid(row=rcOff[0], column=rcOff[1], padx=10, pady=2)
        self.lstbx_x = ListBoxScrollBar(frm_lstbxes)
        self.lstbx_x.frame.grid(row=rcOff[0]+1, column=rcOff[1], padx=10, pady=2)
        #y-Axis column
        lbl_axis_y = Label(frm_lstbxes, text = "y-axis")
        lbl_axis_y.grid(row=rcOff[0], column=rcOff[1]+1, padx=10, pady=2)
        self.lstbx_y = ListBoxScrollBar(frm_lstbxes)
        self.lstbx_y.frame.grid(row=rcOff[0]+1, column=rcOff[1]+1, padx=10, pady=2)
        #
        frm_lstbxes.rowconfigure(rcOff[0], weight=0)
        frm_lstbxes.rowconfigure(rcOff[0]+1, weight=1)
        frm_lstbxes.columnconfigure(rcOff[1], weight=0)
        frm_lstbxes.columnconfigure(rcOff[1]+1, weight=0)
        #
        frm_lstbxes.grid(row=0,column=1,sticky='se')
        #######################################
        #
        self.frame_plot_sel.grid(row=1,column=0,sticky='sew')
        #########################

        self.frame_LHS.rowconfigure(0, weight=1)
        self.frame_LHS.rowconfigure(1, weight=0)
        self.frame_LHS.columnconfigure(0, weight=1)

        self.frame_LHS.pack(fill=BOTH, expand=1)

        self.plot_main['canvas'].mpl_connect("key_press_event", self._event_form_on_key_press)

        self.data_thread_pool = ThreadPool(processes=1)

        self.data_extractor = DataExtractorH5single("swmr.h5", self.data_thread_pool)

        indep_vars = self.data_extractor.get_independent_vars()
        self.lstbx_x.update_vals(indep_vars)
        self.lstbx_y.update_vals(indep_vars)

        self.data_extractor.fetch_data({'slice_vars':["freq"]})

    def main_loop(self):
        i = 0
        while True:
            if self.data_extractor.data_ready():
                return_val = self.data_extractor.get_data()  # get the return value from your function.
                i += 0.1
                self.plot_main['ax'].clear()
                # ax.plot(t, 2 * np.sin(2 * np.pi * t+i))
                self.plot_main['ax'].plot(return_val)
                self.plot_main['canvas'].draw()
                self.data_extractor.fetch_data({'slice_vars':["freq"]})

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
        fig = Figure(figsize=(1,1))
        t = np.arange(0, 3, .01)
        ax = fig.gca() #fig.add_subplot(111)
        # ax.plot(t, 2 * np.sin(2 * np.pi * t))

        canvas_frame = Frame(master=self.root)

        canvas = FigureCanvasTkAgg(fig, master = canvas_frame)
        toolbar = NavigationToolbar2Tk(canvas, canvas_frame)
        toolbar.update()
        toolbar.grid_configure(row=0,column=0,sticky='nsew')
        canvas.get_tk_widget().grid(row=1,column=0,sticky='nsew')

        canvas_frame.rowconfigure(0, weight=0)
        canvas_frame.rowconfigure(1, weight=1)
        canvas_frame.columnconfigure(0, weight=1)

        return {'fig':fig, 'ax':ax, 'frame':canvas_frame, 'canvas':canvas, 'toolbar':toolbar}


    def _event_plotsel_changed(self):
        if self.plot_dim_type.get() == 1:
            #1D Plot
            self.lstbx_y.disable()
            #Move the sash in the paned-window to hide the 1D slices
            cur_height = self.pw_plots_main.winfo_height()
            self.pw_plots_main.sash_place(0, 1, int(cur_height-1))
        else:
            #2D Plot
            self.lstbx_y.enable()
            #Move the sash in the paned-window to show the 1D slices
            cur_height = self.pw_plots_main.winfo_height()
            self.pw_plots_main.sash_place(0, 1, int(cur_height*0.8))

    def _event_form_on_key_press(self,event):
        print("you pressed {}".format(event.key))
        key_press_handler(event, self.plot_main['canvas'], self.plot_main['toolbar'])

    def _event_quit():
        root.quit()     # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    
class ListBoxScrollBar:
    def __init__(self, parent_ui_element):
        self.frame = Frame(master=parent_ui_element)

        self.listbox = Listbox(self.frame, exportselection=0)
        self.listbox.pack(side = LEFT, fill = BOTH)
        self.scrollbar = Scrollbar(self.frame)
        self.scrollbar.pack(side = RIGHT, fill = BOTH)

        for values in range(100): 
            self.listbox.insert(END, values)
        
        self.listbox.config(yscrollcommand = self.scrollbar.set)
        self.scrollbar.config(command = self.listbox.yview)

    def update_vals(self, list_vals):
        self.listbox.delete(0,'end')
        for values in list_vals: 
            self.listbox.insert(END, values)

    def enable(self):
        self.listbox.configure(state='normal')
        # self.scrollbar.configure(state='normal')
    def disable(self):
        self.listbox.configure(state='disabled')
        # self.scrollbar.configure(state='disabled')
