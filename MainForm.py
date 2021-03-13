import tkinter as tk
from tkinter import*
from tkinter import ttk

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import (key_press_handler, MouseButton)
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
from matplotlib.colors import LinearSegmentedColormap

import numpy as np
from multiprocessing.pool import ThreadPool

from DataExtractorH5single import*

class MainForm:
    def __init__(self):
        self.root = tk.Tk()
        self.root.wm_title("SQDviz - Data visualisation tool")

        self.pw_main_LR_UI = PanedWindow(orient =tk.HORIZONTAL, master=self.root)
        self.frame_LHS = Frame(master=self.pw_main_LR_UI)
        self.frame_RHS = Frame(master=self.pw_main_LR_UI)
        self.pw_main_LR_UI.add(self.frame_LHS,stretch='always')
        self.pw_main_LR_UI.add(self.frame_RHS,stretch='always')
        # self.frame_LHS.pack(fill=BOTH, expand=1)
        # self.frame_RHS.pack(fill=BOTH, expand=1)
        self.pw_main_LR_UI.pack(fill=BOTH, expand=1)

        ###################
        #    LHS FRAME
        ###################
        #
        #
        ###################
        #MAIN PLOT DISPLAY#
        ###################
        self.pw_plots_main = PanedWindow(orient =tk.VERTICAL, master=self.frame_LHS)
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
        #########################
        #AXIS VARIABLE SELECTION#
        lblfrm_axis_sel = LabelFrame(master=self.frame_plot_sel, text="Plot Axes", padx=10, pady=10)
        #x-Axis Combobox
        self.cmbx_axis_x = ComboBoxEx(lblfrm_axis_sel, "x-axis")
        self.cmbx_axis_x.Frame.grid(row=0, column=0, sticky='se')
        #y-Axis Combobox
        self.cmbx_axis_y = ComboBoxEx(lblfrm_axis_sel, "y-axis")
        self.cmbx_axis_y.Frame.grid(row=1, column=0, sticky='se')
        #
        lblfrm_axis_sel.rowconfigure(0, weight=1)
        lblfrm_axis_sel.rowconfigure(1, weight=1)
        lblfrm_axis_sel.columnconfigure(0, weight=1)
        #
        lblfrm_axis_sel.grid(row=0,column=1)
        #########################
        #
        ######################
        #COLOUR KEY SELECTION#
        lblfrm_ckey_sel = LabelFrame(master=self.frame_plot_sel, text="Colour key", padx=10, pady=10)
        #x-Axis Combobox
        self.cmbx_ckey = ComboBoxEx(lblfrm_ckey_sel, "Scheme")
        self.cmbx_ckey.Frame.grid(row=0, column=0, sticky='se')
        self.cmbx_ckey.combobox.bind("<<ComboboxSelected>>", self._event_cmbxCKey_changed)
        #
        lblfrm_ckey_sel.grid(row=0,column=2)
        ######################
        #
        self.frame_plot_sel.grid(row=1,column=0,sticky='sew')
        self.frame_plot_sel.rowconfigure(0, weight=1)
        self.frame_plot_sel.columnconfigure(0, weight=1)
        self.frame_plot_sel.columnconfigure(1, weight=1)
        self.frame_plot_sel.columnconfigure(2, weight=1)
        #
        self.frame_LHS.rowconfigure(0, weight=1)
        self.frame_LHS.rowconfigure(1, weight=0)
        self.frame_LHS.columnconfigure(0, weight=1)
        #########################


        ###################
        #    RHS FRAME
        ###################
        #
        self.pw_RHS = PanedWindow(orient=tk.VERTICAL, master=self.frame_RHS)
        #
        ################
        #CURSOR DISPLAY#
        ################
        #
        self.frame_cursors = LabelFrame(master=self.frame_RHS, text = "Cursors")
        self.pw_RHS.add(self.frame_cursors, stretch='always')
        #
        #################
        #CURSOR CUT PLOTS
        self.frame_cursor_plots = Frame(master=self.frame_cursors)
        self.plot_cursorX = PlotFrame(self.frame_cursor_plots)
        self.plot_cursorY = PlotFrame(self.frame_cursor_plots)
        self.plot_cursorX.Frame.grid(row=0, column=0, sticky="news")
        self.plot_cursorY.Frame.grid(row=0, column=1, sticky="news")
        self.frame_cursor_plots.rowconfigure(0, weight=1)
        self.frame_cursor_plots.columnconfigure(0, weight=1)
        self.frame_cursor_plots.columnconfigure(1, weight=1)
        #
        self.frame_cursor_plots.grid(row=0, column=0, columnspan=2, padx=10, pady=2, sticky="news")
        #
        ###############
        #CURSOR LISTBOX
        self.lstbx_cursors = ListBoxScrollBar(self.frame_cursors)
        self.lstbx_cursors.frame.grid(row=1, column=0, columnspan=2, padx=10, pady=2, sticky="ews")
        ################
        #
        ###################
        #ADD/REMOVE BUTTONS
        self.btn_cursor_add = tk.Button(master=self.frame_cursors, text ="Add cursor", command = lambda: self.plot_main.add_cursor())
        self.btn_cursor_add.grid(row=2, column=0)
        self.btn_cursor_add = tk.Button(master=self.frame_cursors, text ="Delete cursor", command = lambda: self.plot_main.Cursors.pop(self.lstbx_cursors.get_sel_val(True)))
        self.btn_cursor_add.grid(row=2, column=1)
        ###################
        #
        self.frame_cursors.rowconfigure(0, weight=1)
        self.frame_cursors.rowconfigure(1, weight=0)
        self.frame_cursors.rowconfigure(2, weight=0)
        self.frame_cursors.columnconfigure(0, weight=1)
        self.frame_cursors.columnconfigure(1, weight=1)
        ################
        #
        #################
        #ANALYSIS WINDOW#
        #################
        #
        self.lblfrm_analysis = LabelFrame(master=self.pw_RHS, text = "Analysis & postprocessing")
        self.pw_RHS.add(self.lblfrm_analysis, stretch='always')
        self.frm_analysis = ScrollBarFrame(self.lblfrm_analysis)
        frm_canvas = self.frm_analysis.FrameMain
        #
        self.lstbx_procs = ListBoxScrollBar(frm_canvas)
        self.lstbx_procs.frame.pack()
        #
        self.frm_analysis.pack(side="left", fill="both", expand=True)
        #
        #################
        #
        self.pw_RHS.grid(row=0,column=0,sticky='nsew')
        self.frame_RHS.rowconfigure(0, weight=1)
        self.frame_RHS.rowconfigure(1, weight=1)
        self.frame_RHS.columnconfigure(0, weight=1)

        def_col_maps = [('viridis', "Viridis"), ('afmhot', "AFM Hot"), ('hot', "Hot"), ('gnuplot', "GNU-Plot"), ('coolwarm', "Cool-Warm"), ('seismic', "Seismic"), ('rainbow', "Rainbow")]
        self.colour_maps = []
        for cur_col_map in def_col_maps:
            self.colour_maps.append(ColourMap.fromDefault(cur_col_map[0], cur_col_map[1]))
        #Commit colour maps to ComboBox
        self.cmbx_ckey.update_vals([x.Name for x in self.colour_maps])
        self.plot_main.set_colour_key(self.colour_maps[self.cmbx_ckey.get_sel_val(True)])

        self.plot_main.Canvas.mpl_connect("key_press_event", self._event_form_on_key_press)
        self.plot_main.add_cursor('red')

        self.data_thread_pool = ThreadPool(processes=1)
        self.data_extractor = DataExtractorH5single("swmr.h5", self.data_thread_pool)
        #
        indep_vars = self.data_extractor.get_independent_vars()
        self.cmbx_axis_x.update_vals(indep_vars)
        self.cmbx_axis_y.update_vals(indep_vars)

    def main_loop(self):
        while True:
            if self.data_extractor.data_ready():
                new_data = self.data_extractor.get_data()
                if len(new_data[0]) == 1:
                    self.plot_main.plot_data_1D(new_data[0][0], new_data[1])
                else:
                    self.plot_main.plot_data_2D(new_data[0][0], new_data[0][1], new_data[1].T)
            
            self.plot_main.Canvas.draw()
            self.plot_main.pop_plots_with_cursor_cuts(self.plot_cursorX, self.plot_cursorY, self.lstbx_cursors)
            self.plot_cursorX.Canvas.draw()
            self.plot_cursorY.Canvas.draw()

            #Setup new request if no new data is being fetched
            if not self.data_extractor.isFetching:
                if self.plot_dim_type.get() == 1:
                    self.data_extractor.fetch_data({'slice_vars':[self.cmbx_axis_x.get_sel_val()]})
                else:
                    xVar = self.cmbx_axis_x.get_sel_val()
                    yVar = self.cmbx_axis_y.get_sel_val()
                    if xVar != yVar:
                        self.data_extractor.fetch_data({'slice_vars':[xVar, yVar]})

            #tkinter.mainloop()
            # self.root.update_idletasks()
            self.root.update()
        # If you put root.destroy() here, it will cause an error if the window is
        # closed with the window manager.

    def _event_plotsel_changed(self):
        if self.plot_dim_type.get() == 1:
            #1D Plot
            self.cmbx_axis_y.disable()
            self.cmbx_ckey.disable()
            #Move the sash in the paned-window to hide the 1D slices
            cur_height = self.pw_plots_main.winfo_height()
            self.pw_plots_main.sash_place(0, 1, int(cur_height-1))
        else:
            #2D Plot
            self.cmbx_axis_y.enable()
            self.cmbx_ckey.enable()
            #Move the sash in the paned-window to show the 1D slices
            cur_height = self.pw_plots_main.winfo_height()
            self.pw_plots_main.sash_place(0, 1, int(cur_height*0.8))

    def _event_form_on_key_press(self,event):
        print("you pressed {}".format(event.key))
        key_press_handler(event, self.plot_main.Canvas, self.plot_main.ToolBar)
    
    def _event_cmbxCKey_changed(self, event):
        self.plot_main.set_colour_key(self.colour_maps[self.cmbx_ckey.get_sel_val(True)])

    def _event_quit():
        root.quit()     # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    
class ComboBoxEx:
    def __init__(self, parent_ui_element, label):
        self.Frame = Frame(master=parent_ui_element)

        self.lbl_cmbx = Label(self.Frame, text = label)
        self.lbl_cmbx.grid(row=0, column=0, sticky="nes")
        self.combobox = ttk.Combobox(self.Frame)
        self.combobox.grid(row=0, column=1, sticky="news")

        self.Frame.columnconfigure(0, weight=0) #Label is of constant size
        self.Frame.columnconfigure(1, weight=1) #ComboBox is expected to rescale
        self.Frame.rowconfigure(0, weight=1)

        self._vals = []

    def update_vals(self, list_vals):
        #Get current selection if applicable:
        cur_sel = self.get_sel_val(True)

        #Clear combobox
        self._vals = list(list_vals)
        self.combobox['values'] = self._vals
            
        if cur_sel == None or not (cur_sel in self._vals):
            #Select first element by default...
            self.combobox.current(0)
        else:
            #Select the prescribed element from above... Note that cur_sel is still in the new list...
            self.combobox.current(self._vals.index(cur_sel))
        self.combobox.event_generate("<<ComboboxSelected>>")

    def enable(self):
        self.combobox.configure(state='normal')
    def disable(self):
        self.combobox.configure(state='disabled')

    def get_sel_val(self, get_index = False):
        if len(self._vals) == 0:
            return None
        if get_index:
            return self.combobox.current()
        else:
            return self._vals[self.combobox.current()]

class ListBoxScrollBar:
    def __init__(self, parent_ui_element):
        self.frame = Frame(master=parent_ui_element)

        self.listbox = Listbox(self.frame, exportselection=0)
        self.listbox.grid(row=0, column=0, sticky="news")
        self.scrollbar = Scrollbar(self.frame)
        self.scrollbar.grid(row=0, column=1, sticky="nes")
        self.frame.columnconfigure(0, weight=1) #Listbox horizontally stretches to meet up with the scroll bar...
        self.frame.columnconfigure(1, weight=0) #Scroll bar stays the same size regardless of frame width...
        self.frame.rowconfigure(0, weight=1)

        for values in range(100): 
            self.listbox.insert(END, values)
        
        self.listbox.config(yscrollcommand = self.scrollbar.set)
        self.scrollbar.config(command = self.listbox.yview)

    def update_vals(self, list_vals, cols=None):
        #Get current selection if applicable:
        cur_sel = [m for m in self.listbox.curselection()]
        #Select first element by default...
        if len(cur_sel) == 0:
            cur_sel = 0
        else:
            cur_sel = cur_sel[0]

        #Clear listbox
        self.listbox.delete(0,'end')
        for values in list_vals:
            self.listbox.insert(END, values)
        
        #Colour the values if applicable:
        if cols != None:
            for ind in range(len(list_vals)):
                self.listbox.itemconfig(ind, foreground=cols[ind])
        #Select the prescribed element from above...
        self.listbox.select_set(cur_sel)
        self.listbox.event_generate("<<ListboxSelect>>")

    def enable(self):
        self.listbox.configure(state='normal')
        # self.scrollbar.configure(state='normal')
    def disable(self):
        self.listbox.configure(state='disabled')
        # self.scrollbar.configure(state='disabled')

    def get_sel_val(self, get_index = False):
        if get_index:
            values = [m for m in self.listbox.curselection()]
        else:
            values = [self.listbox.get(m) for m in self.listbox.curselection()]
        return values[0]

class ColourMap:
    def __init__(self):
        pass

    @classmethod
    def fromDefault(cls, cmap_name, display_name):
        retObj = cls()
        retObj._cmap = cmap_name
        retObj._display_name = display_name
        return retObj
    
    @classmethod
    def fromCustom(cls, cdict, display_name, num_interpol=256):
        retObj = cls()
        retObj._cmap = LinearSegmentedColormap(display_name, segmentdata=cdict, N=num_interpol)
        retObj._display_name = display_name
        return retObj
    
    @property
    def Name(self):
        return self._display_name
    @property
    def CMap(self):
        return self._cmap

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

        self.curData = []
        self.Cursors = []
        self._cur_col_key = 'viridis'
        self._cur_2D = False

        self.Canvas.mpl_connect('button_press_event', self.event_mouse_pressed)

    def add_cursor(self, col=''):
        if col == '':
            col_pool = ['red', 'blue', 'green', 'magenta', 'cyan']
            cur_cols = [x.colour for x in self.Cursors]
            for cur_cand_col in col_pool:
                if not cur_cand_col in cur_cols:
                    col = cur_cand_col
                    break
            #Just pick random colour if all colours are already taken...
            if col == '':
                import random
                col = col_pool[random.randint(0, len(col_pool)-1)]
        
        new_curse = PlotCursorDrag(self, col)
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

    def plot_data_1D(self, dataX, dataY, clearAxis=True, colour = None):
        self.curData = (dataX, dataY)
        if clearAxis:
            self.ax.clear()
        if colour != None:
            self.ax.plot(self.curData[0], self.curData[1], color = colour)
        else:
            self.ax.plot(self.curData[0], self.curData[1])
        self._cur_2D = False
        self.update()

    def plot_data_2D(self, dataX, dataY, dataZ):
        self.curData = (dataX, dataY, dataZ)
        self._cur_2D = True
        self._plot_2D()

    def set_colour_key(self, new_col_key):
        self._cur_col_key = new_col_key
        self._plot_2D()

    def _plot_2D(self):
        if self._cur_2D:
            self.ax.clear()
            self.ax.pcolor(self.curData[0], self.curData[1], self.curData[2], shading='nearest', cmap=self._cur_col_key.CMap)
            self.update()


    def find_nearest(array, value):
        return idx

    def pop_plots_with_cursor_cuts(self, plot_cursor_x, plot_cursor_y, lstbx_cursor_info):
        #Check if a cursor has moved...
        no_changes = True
        for cur_curse in self.Cursors:
            if cur_curse.has_changed:
                no_changes = False
                break
        if no_changes:
            return
        
        #Plot each cursor's cut...
        curse_infos = []
        curse_cols = []
        clear_first_plot = True
        for cur_curse in self.Cursors:
            if len(self.curData) == 2:
                return np.array([])
            else:
                curse_infos += [ f"X: {cur_curse.cur_coord[0]}, Y: {cur_curse.cur_coord[1]}" ]
                curse_cols += [cur_curse.colour]
                cutX = int((np.abs(self.curData[0] - cur_curse.cur_coord[0])).argmin())
                cutY = int((np.abs(self.curData[1] - cur_curse.cur_coord[1])).argmin())
                plot_cursor_x.plot_data_1D(self.curData[0], self.curData[2][cutY,:], clear_first_plot, cur_curse.colour)
                plot_cursor_y.plot_data_1D(self.curData[1], self.curData[2][:,cutX], clear_first_plot, cur_curse.colour)
                clear_first_plot = False
        lstbx_cursor_info.update_vals(curse_infos, curse_cols)

    def event_mouse_pressed(self, event):
        #Pick first cursor that can be picked by the mouse if applicable
        for cur_curse in self.Cursors:
            cur_curse.event_mouse_pressed(event)
            if cur_curse._is_drag != 'None':
                return

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
        self.pltFrame.Canvas.mpl_connect('button_release_event', self.event_mouse_released)
        #canvas.mpl_connect('axes_leave_event', cc.hide_y)

        self.has_changed = False

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
        self.has_changed = True

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
            self.has_changed = True
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

class ScrollBarFrame(ttk.Frame):
    def __init__(self, container, *args, **kwargs):
        #Inspired by: https://www.tecladocode.com/tkinter-scrollable-frames/
        super().__init__(container, *args, **kwargs)
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.FrameMain = ttk.Frame(canvas)

        self.FrameMain.bind("<Configure>",lambda e: canvas.configure( scrollregion=canvas.bbox("all") ))

        canvas.create_window((0, 0), window=self.FrameMain, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")