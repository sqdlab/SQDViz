import tkinter as tk
from tkinter import*

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import (key_press_handler, MouseButton)
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor

import numpy as np
from multiprocessing.pool import ThreadPool

from DataExtractorH5single import*

class MainForm:
    def __init__(self):
        self.root = tk.Tk()
        self.root.wm_title("SQDviz - Data visualisation tool")

        ###################
        #    LHS FRAME
        ###################
        self.frame_LHS = Frame(master=self.root)
        #
        #
        ###################
        #MAIN PLOT DISPLAY#
        ###################
        self.pw_plots_main = PanedWindow(orient ='vertical', master=self.frame_LHS)
        self.plot_main = PlotFrame(self.root)
        self.pw_plots_main.add(self.plot_main.Frame,stretch='always')
        self.plot_slice = PlotFrame(self.root)
        self.pw_plots_main.add(self.plot_slice.Frame)
        #
        self.pw_plots_main.grid(row=0,column=0,sticky='nsew')
        ###################
        #
        #
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
        self.frame_LHS.rowconfigure(0, weight=1)
        self.frame_LHS.rowconfigure(1, weight=0)
        self.frame_LHS.columnconfigure(0, weight=1)
        #########################


        ###################
        #    RHS FRAME
        ###################
        self.frame_RHS = Frame(master=self.root)
        #
        ###################
        #MAIN PLOT DISPLAY#
        ###################
        #self.

        self.pw_main_LR_UI = PanedWindow(orient ='horizontal', master=self.root)
        self.pw_main_LR_UI.add(self.frame_LHS,stretch='always')
        self.pw_main_LR_UI.add(self.frame_RHS,stretch='always')
        self.frame_LHS.pack(fill=BOTH, expand=1)
        self.frame_RHS.pack(fill=BOTH, expand=1)

        self.plot_main.Canvas.mpl_connect("key_press_event", self._event_form_on_key_press)
        self.plot_main.add_cursor()

        self.data_thread_pool = ThreadPool(processes=1)
        self.data_extractor = DataExtractorH5single("swmr.h5", self.data_thread_pool)
        #
        indep_vars = self.data_extractor.get_independent_vars()
        self.lstbx_x.update_vals(indep_vars)
        self.lstbx_y.update_vals(indep_vars)

    def main_loop(self):
        while True:
            if self.data_extractor.data_ready():
                new_data = self.data_extractor.get_data()
                if len(new_data[0]) == 1:
                    self.plot_main.ax.clear()
                    # ax.plot(t, 2 * np.sin(2 * np.pi * t+i))
                    self.plot_main.ax.plot(new_data[0][0], new_data[1])
                    self.plot_main.update()
                else:
                    self.plot_main.ax.clear()
                    # ax.plot(t, 2 * np.sin(2 * np.pi * t+i))
                    self.plot_main.ax.pcolor(new_data[0][0], new_data[0][1], new_data[1].T)
                    self.plot_main.update()
            
            self.plot_main.Canvas.draw()

            if not self.data_extractor.isFetching:
                #Setup new request...
                if self.plot_dim_type.get() == 1:
                    self.data_extractor.fetch_data({'slice_vars':[self.lstbx_x.get_sel_val()]})
                else:
                    xVar = self.lstbx_x.get_sel_val()
                    yVar = self.lstbx_y.get_sel_val()
                    if xVar != yVar:
                        self.data_extractor.fetch_data({'slice_vars':[xVar, yVar]})

            #tkinter.mainloop()
            self.root.update_idletasks()
            self.root.update()
        # If you put root.destroy() here, it will cause an error if the window is
        # closed with the window manager.

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
        key_press_handler(event, self.plot_main.Canvas, self.plot_main.ToolBar)

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
        #Select first element by default...
        self.listbox.select_set(0)
        self.listbox.event_generate("<<ListboxSelect>>")

    def enable(self):
        self.listbox.configure(state='normal')
        # self.scrollbar.configure(state='normal')
    def disable(self):
        self.listbox.configure(state='disabled')
        # self.scrollbar.configure(state='disabled')

    def get_sel_val(self):
        values = [self.listbox.get(m) for m in self.listbox.curselection()]
        return values[0]

class PlotFrame:
    def __init__(self, root_ui):
        self.fig = Figure(figsize=(1,1))
        t = np.arange(0, 3, .01)
        self.ax = self.fig.gca() #fig.add_subplot(111)
        # ax.plot(t, 2 * np.sin(2 * np.pi * t))

        self.Frame = Frame(master=root_ui)

        self.Canvas = FigureCanvasTkAgg(self.fig, master = self.Frame)
        self.ToolBar = NavigationToolbar2Tk(self.Canvas, self.Frame)
        self.ToolBar.update()
        self.ToolBar.grid_configure(row=0,column=0,sticky='nsew')
        self.Canvas.get_tk_widget().grid(row=1,column=0,sticky='nsew')

        self.Frame.rowconfigure(0, weight=0)
        self.Frame.rowconfigure(1, weight=1)
        self.Frame.columnconfigure(0, weight=1)

        self.Cursors = []

    def add_cursor(self):
        new_curse = PlotCursorDrag(self, 'red')
        self.Cursors += [new_curse]
        return new_curse

    def update(self):
        for cur_curse in self.Cursors:
            cur_curse.update()

    def get_axis_size_px(self):
        bbox = self.ax.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
        width, height = bbox.width, bbox.height
        width *= self.fig.dpi
        height *= self.fig.dpi
        return (width, height)

class PlotCursorDrag(object):
    def __init__(self, pltFrame, colour):
        #Inspired by: https://stackoverflow.com/questions/35414003/python-how-can-i-display-cursor-on-all-axes-vertically-but-only-on-horizontall
        self.ax = pltFrame.ax
        self.pltFrame = pltFrame
        
        self.colour = colour
        
        xlimts = self.ax.get_xlim()
        ylimts = self.ax.get_ylim()
        self.lx = self.ax.axvline(ymin=ylimts[0],ymax=ylimts[1],color=colour)
        self.ly = self.ax.axhline(xmin=xlimts[0],xmax=xlimts[1],color=colour)
        self.cur_coord = (0.5*(xlimts[0]+xlimts[1]), 0.5*(ylimts[0]+ylimts[1]))
        self.lx.set_xdata(self.cur_coord[0])
        self.ly.set_ydata(self.cur_coord[1])
        self.lx.set_visible(True)
        self.ly.set_visible(True)

        self._is_drag = 'None'  #Can be: inX, inY, inBoth, None

        self.pltFrame.Canvas.mpl_connect('motion_notify_event', self.display_cursor)
        self.pltFrame.Canvas.mpl_connect('button_press_event', self.event_mouse_pressed)
        self.pltFrame.Canvas.mpl_connect('button_release_event', self.event_mouse_released)
        #canvas.mpl_connect('axes_leave_event', cc.hide_y)

    def update(self):
        xlimts = self.ax.get_xlim()
        ylimts = self.ax.get_ylim()
        self.lx = self.ax.axvline(ymin=ylimts[0],ymax=ylimts[1],color=self.colour)
        self.ly = self.ax.axhline(xmin=xlimts[0],xmax=xlimts[1],color=self.colour)

        #Reset coordinate if cursor falls outside the possibly new axis
        if self.cur_coord[0] < xlimts[0] or self.cur_coord[0] > xlimts[1] or self.cur_coord[1] < ylimts[0] or self.cur_coord[1] > ylimts[1]:
            self.cur_coord = (0.5*(xlimts[0]+xlimts[1]), 0.5*(ylimts[0]+ylimts[1]))
        self.lx.set_xdata(self.cur_coord[0])
        self.ly.set_ydata(self.cur_coord[1])

    def display_cursor(self, event):
        if event.inaxes and event.button == MouseButton.LEFT:
            if self._is_drag == 'inBoth':
                self.cur_coord = (event.xdata, event.ydata)
            elif self._is_drag == 'inX':
                self.cur_coord = (event.xdata, self.cur_coord[1])
            elif self._is_drag == 'inY':
                self.cur_coord = (self.cur_coord[0], event.ydata)
            else:
                return

            self.lx.set_xdata(self.cur_coord[0])
            self.ly.set_ydata(self.cur_coord[1])
        else:
            #Give up drag if mouse goes out of the axis...
            self._is_drag = 'None'
        # plt.draw()

    def event_mouse_pressed(self, event):
        if event.inaxes and event.button == MouseButton.LEFT:
            #Adjust threshold appropriately...
            threshold_x, threshold_y = 10, 10

            mouse_coord = (event.xdata, event.ydata)           
            cur_ax_size = self.pltFrame.get_axis_size_px()
            xlimts = self.ax.get_xlim()
            ylimts = self.ax.get_ylim()
            mouse_px_x = (mouse_coord[0]-xlimts[0])/(xlimts[1]-xlimts[0])*cur_ax_size[0]
            mouse_px_y = (mouse_coord[1]-ylimts[0])/(ylimts[1]-ylimts[0])*cur_ax_size[1]
            coord_px_x = (self.cur_coord[0]-xlimts[0])/(xlimts[1]-xlimts[0])*cur_ax_size[0]
            coord_px_y = (self.cur_coord[1]-ylimts[0])/(ylimts[1]-ylimts[0])*cur_ax_size[1]

            thresh_x = abs(coord_px_x-mouse_px_x) < threshold_x
            thresh_y = abs(coord_px_y-mouse_px_y) < threshold_y

            if thresh_x and thresh_y:
                self._is_drag = 'inBoth'
            elif thresh_x:
                self._is_drag = 'inX'
            elif thresh_y:
                self._is_drag = 'inY'
            else:
                self._is_drag = 'None'
                return

    def event_mouse_released(self, event):
        self._is_drag = 'None'