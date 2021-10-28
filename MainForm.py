import tkinter as tk
from tkinter import*
from tkinter import ttk
import tkinter.font as tkFont
from tkinter.scrolledtext import ScrolledText
from tkinter import filedialog as fd

import matplotlib
import matplotlib.pyplot
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import (key_press_handler, MouseButton)
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors as mplcols
from matplotlib.backend_tools import ToolBase
from matplotlib import style as mplstyle

import numpy as np
from multiprocessing.pool import ThreadPool

from numpy.lib.arraysetops import isin

from DataExtractorH5single import*
from DataExtractorH5multiple import*
from DataExtractorUQtoolsDAT import*

from PostProcessors import*
from Analysis_Cursors import*

from functools import partial

import json
import os

import warnings

class MainForm:
    def __init__(self, dark_mode = False):
        self.root = tk.Tk()
        self.root.wm_title("SQDviz - Data visualisation tool")

        if dark_mode:
            self.root.tk.call('source', 'azure-dark.tcl')
            style = ttk.Style(self.root)
            style.theme_use('azure-dark')
        self.dark_mode = dark_mode

        frame_overall = Frame(master=self.root)
        frame_toolbar = Frame(master=frame_overall)
        
        self.pw_main_LR_UI = PanedWindow(orient =tk.HORIZONTAL, master=frame_overall, sashwidth=3, bg = "#000077", bd = 0)
        self.frame_LHS = Frame(master=self.pw_main_LR_UI)
        self.frame_RHS = Frame(master=self.pw_main_LR_UI)
        self.pw_main_LR_UI.add(self.frame_LHS,stretch='always')
        self.pw_main_LR_UI.add(self.frame_RHS,stretch='always')
        #
        frame_toolbar.rowconfigure(0, weight=1)
        frame_toolbar.grid(row=0, column=0, sticky="news")
        self.pw_main_LR_UI.grid(row=1, column=0, sticky="news")
        #
        frame_overall.rowconfigure(0, weight=0)
        frame_overall.rowconfigure(1, weight=1)
        frame_overall.columnconfigure(0, weight=1)
        frame_overall.pack(fill=BOTH, expand=1)        

        #####################
        #      TOOLBAR
        #####################
        self.icon_openhdf5 = PhotoImage(file = "Icons/OpenSQDToolzHDF5.png")    #Need to store reference for otherwise garbage collection destroys it...
        Button(master=frame_toolbar, image=self.icon_openhdf5, command=self._open_file_hdf5).grid(row=0, column=0)
        self.icon_openhdf5folders = PhotoImage(file = "Icons/OpenSQDToolzHDF5folder.png")    #Need to store reference for otherwise garbage collection destroys it...
        Button(master=frame_toolbar, image=self.icon_openhdf5folders, command=self._open_file_hdf5folders).grid(row=0, column=1)
        self.icon_openDAT = PhotoImage(file = "Icons/OpenSQDToolzDAT.png")    #Need to store reference for otherwise garbage collection destroys it...
        Button(master=frame_toolbar, image=self.icon_openDAT, command=self._open_file_dat).grid(row=0, column=2)
        self.icon_openNext = PhotoImage(file = "Icons/OpenSQDToolzNextfolder.png")    #Need to store reference for otherwise garbage collection destroys it...
        Button(master=frame_toolbar, image=self.icon_openNext, command=self._open_file_next).grid(row=0, column=3)
        #####################

        ###################
        #    LHS FRAME
        ###################
        #
        self.pw_lhs = PanedWindow(orient =tk.VERTICAL, master=self.frame_LHS, sashwidth=3, bg = "#000077", bd = 0)
        #
        ###################
        #MAIN PLOT DISPLAY#
        ###################
        self.plot_main = PlotFrame(self.pw_lhs, self._event_btn_plot_main_update, self._event_btn_plot_main_get_attrs, dark_mode)
        self.pw_lhs.add(self.plot_main.Frame,stretch='always')
        ###################
        #
        #
        #########################
        #PLOT SELECTION CONTROLS#
        #########################
        #
        #Overall frame broken up into columns containing individual frames...
        frame_cursors_all = Frame(master=self.pw_lhs)
        self.pw_lhs.add(frame_cursors_all,stretch='always')
        #
        ################
        #CURSOR DISPLAY#
        ################
        #
        self.frame_cursors = LabelFrame(master=frame_cursors_all, text = "Cursors")
        #
        ################
        #CURSOR LISTBOX#
        self.lstbx_cursors = ListBoxScrollBar(self.frame_cursors)
        self.lstbx_cursors.frame.grid(row=0, column=0, columnspan=2, padx=10, pady=2, sticky="news")
        ################
        #
        ####################
        #ADD/REMOVE BUTTONS#
        self.btn_cursor_add = Button(master=self.frame_cursors, text ="Add cursor", command = lambda: self.plot_main.add_cursor())
        self.btn_cursor_add.grid(row=1, column=0)
        self.btn_cursor_del = Button(master=self.frame_cursors, text ="Delete cursor", command = lambda: self.plot_main.Cursors.pop(self.lstbx_cursors.get_sel_val(True)))
        self.btn_cursor_del.grid(row=1, column=1)
        ####################
        #
        self.frame_cursors.rowconfigure(0, weight=1)
        self.frame_cursors.rowconfigure(1, weight=0)
        self.frame_cursors.columnconfigure(0, weight=1)
        self.frame_cursors.grid(row=0, column=0, sticky='news')
        ################
        #
        #########################
        #ANALYSIS CURSOR DISPLAY#
        #########################
        #
        self.frame_analy_cursors = LabelFrame(master=frame_cursors_all, text = "Analysis cursors")
        #
        ################
        #CURSOR LISTBOX#
        self.lstbx_analy_cursors = MultiColumnListbox(self.frame_analy_cursors, [" ", "  ", "Name", "Type", "Notes"], self._update_analy_cursor_item)
        self.lstbx_analy_cursors.Frame.grid(row=0, column=0, padx=10, pady=2, columnspan=3, sticky="news")
        ################
        #
        ####################
        #ADD/REMOVE BUTTONS#
        self.cmbx_anal_cursors = ComboBoxEx(self.frame_analy_cursors, "")
        self.cmbx_anal_cursors.Frame.grid(row=1, column=0)
        self.btn_analy_cursor_add = Button(master=self.frame_analy_cursors, text ="Add cursor", command = self._event_btn_anal_cursor_add)
        self.btn_analy_cursor_add.grid(row=1, column=1)
        self.btn_analy_cursor_del = Button(master=self.frame_analy_cursors, text ="Delete", command = self._event_btn_anal_cursor_del)
        self.btn_analy_cursor_del.grid(row=1, column=2)
        ####################
        #
        self.frame_analy_cursors.rowconfigure(0, weight=1)
        self.frame_analy_cursors.rowconfigure(1, weight=0)
        self.frame_analy_cursors.columnconfigure(0, weight=1)
        self.frame_analy_cursors.grid(row=0, column=1, sticky='news')
        #########################
        #
        #
        frame_cursors_all.columnconfigure(0, weight=1)
        frame_cursors_all.columnconfigure(1, weight=1)
        frame_cursors_all.rowconfigure(0, weight=1)
        #
        self.pw_lhs.pack(fill=BOTH, expand=1)
        #########################


        ###################
        #    RHS FRAME
        ###################
        #
        frm_plotparams_varslicer = Frame(master=self.frame_RHS, padx=10, pady=2)
        #
        #########################
        #AXIS VARIABLE SELECTION#
        lblfrm_plot_params = LabelFrame(master=frm_plotparams_varslicer, text="Plot Parameters", padx=10, pady=10)
        #
        #Labelled frame container with the radio buttons stored in the variable self.plot_dim_type
        self.plot_dim_type = tk.IntVar()
        lblfrm_axis_sel = LabelFrame(master=lblfrm_plot_params, text="Plot Axes", padx=10, pady=2)
        self.rdbtn_plot_sel_1D = ttk.Radiobutton(lblfrm_axis_sel, text="1D Plot", variable=self.plot_dim_type, value=1, command=self._event_plotsel_changed)
        self.rdbtn_plot_sel_1D.grid(row=0, column=0)
        self.rdbtn_plot_sel_2D = ttk.Radiobutton(lblfrm_axis_sel, text="2D Plot", variable=self.plot_dim_type, value=2, command=self._event_plotsel_changed)
        self.rdbtn_plot_sel_2D.grid(row=1, column=0)
        lblfrm_axis_sel.grid(row=0, column=0, pady=2)
        #
        cmbx_width = 13
        #x-Axis Combobox
        self.cmbx_axis_x = ComboBoxEx(lblfrm_plot_params, "x-axis", width=cmbx_width)
        self.cmbx_axis_x.Frame.grid(row=1, column=0, sticky='se', pady=2)
        #y-Axis Combobox
        self.cmbx_axis_y = ComboBoxEx(lblfrm_plot_params, "y-axis", width=cmbx_width)
        self.cmbx_axis_y.Frame.grid(row=2, column=0, sticky='se', pady=2)
        #Dependent Variables Combobox
        self.cmbx_dep_var = ComboBoxEx(lblfrm_plot_params, "Dep. Var.", width=cmbx_width)
        self.cmbx_dep_var.Frame.grid(row=3, column=0, sticky='se', pady=2)
        #Colour Scheme ComboBox
        self.cmbx_ckey = ComboBoxEx(lblfrm_plot_params, "Scheme", width=cmbx_width)
        self.cmbx_ckey.Frame.grid(row=4, column=0, sticky='se', pady=2)
        self.cmbx_ckey.combobox.bind("<<ComboboxSelected>>", self._event_cmbxCKey_changed)
        #
        self.hist_eq_enabled_var = tk.BooleanVar()
        self.hist_eq_enabled_var.set(False)
        self.chkbx_hist_eq = ttk.Checkbutton(lblfrm_plot_params, text = "Histogram equalisation", var=self.hist_eq_enabled_var, command=self._callback_chkbx_hist_eq_enabled)
        self.chkbx_hist_eq.grid(row=5, column=0, sticky='se', pady=2)
        #
        self.cmbx_update_rate = ComboBoxEx(lblfrm_plot_params, "Update", width=cmbx_width)
        self.cmbx_update_rate.Frame.grid(row=6, column=0, sticky='se', pady=2)
        #
        for m in range(7):
            lblfrm_plot_params.rowconfigure(m, weight=1)
        lblfrm_plot_params.columnconfigure(0, weight=1)
        #
        lblfrm_plot_params.grid(row=0,column=0,sticky='nes')
        #########################
        #
        #
        #################
        #VARIABLE SLICER#
        lblfrm_slice_vars = LabelFrame(master=frm_plotparams_varslicer, text="Parameter slice", padx=10, pady=10)
        self.lstbx_slice_vars = ListBoxScrollBar(lblfrm_slice_vars)
        self.lstbx_slice_vars.frame.grid(row=0, column=0, columnspan=3, sticky="news")
        #
        self.lbl_slice_vars_val = tk.Label(lblfrm_slice_vars, text="Min|Max:")
        self.lbl_slice_vars_val.grid(row=1, column=0, columnspan=3)
        #
        self.sldr_slice_vars_val = ttk.Scale(lblfrm_slice_vars, from_=0, to=1, orient='horizontal', command=self._event_sldr_slice_vars_val_changed)
        self.sldr_slice_vars_val.grid(row=2, column=0, sticky='sew')
        self.btn_slice_vars_val_inc = Button(lblfrm_slice_vars, text="❰", command=self._event_btn_slice_vars_val_dec)
        self.btn_slice_vars_val_dec = Button(lblfrm_slice_vars, text="❱", command=self._event_btn_slice_vars_val_inc)
        self.btn_slice_vars_val_inc.grid(row=2,column=1)
        self.btn_slice_vars_val_dec.grid(row=2,column=2)
        #
        lblfrm_slice_vars.columnconfigure(0, weight=1)
        lblfrm_slice_vars.columnconfigure(1, weight=1)
        lblfrm_slice_vars.columnconfigure(2, weight=1)
        lblfrm_slice_vars.rowconfigure(0, weight=1)
        lblfrm_slice_vars.rowconfigure(1, weight=0)
        lblfrm_slice_vars.rowconfigure(2, weight=0)
        lblfrm_slice_vars.grid(row=0,column=1,sticky='news')
        #################
        #
        frm_plotparams_varslicer.grid(row=0,column=0, sticky='new')
        frm_plotparams_varslicer.columnconfigure(0, weight=0)
        frm_plotparams_varslicer.columnconfigure(1, weight=1)
        frm_plotparams_varslicer.rowconfigure(0, weight=1)
        #
        #
        #################
        #ANALYSIS WINDOW#
        #################
        #
        lblfrm_analysis = LabelFrame(master=self.frame_RHS, text = "Analysis & postprocessing", padx=10, pady=2)
        #
        #####################
        #PROCESSOR SELECTION#
        frm_proc_sel = Frame(master=lblfrm_analysis)
        #
        #List of Post-Processors
        frm_proc_sel_lstbxs_add_btn = Frame(master=frm_proc_sel)
        self.lstbx_procs = ListBoxScrollBar(frm_proc_sel_lstbxs_add_btn)
        self.lstbx_procs.frame.grid(row=0,column=0, sticky='news')
        self.btn_proc_sel_add = Button(frm_proc_sel_lstbxs_add_btn, text="Add Function", command=self._event_btn_post_proc_add)
        self.btn_proc_sel_add.grid(row=1, column=0)
        frm_proc_sel_lstbxs_add_btn.rowconfigure(0, weight=1)
        frm_proc_sel_lstbxs_add_btn.rowconfigure(1, weight=0)
        frm_proc_sel_lstbxs_add_btn.columnconfigure(0, weight=1)
        frm_proc_sel_lstbxs_add_btn.grid(row=0, column=0, sticky='news')
        #
        #Description and Add Button
        frm_proc_sel_desc = Frame(master=frm_proc_sel)
        self.lbl_proc_sel_desc = LabelMultiline(frm_proc_sel_desc)
        self.lbl_proc_sel_desc.Frame.grid(row=0,column=0, sticky='news')
        frm_proc_sel_desc.rowconfigure(0, weight=1)
        frm_proc_sel_desc.columnconfigure(0, weight=1)
        frm_proc_sel_desc.grid(row=0, column=1, sticky='news')
        #
        frm_proc_sel.rowconfigure(0, weight=1)
        frm_proc_sel.columnconfigure(0, weight=0)
        frm_proc_sel.columnconfigure(1, weight=1)
        #
        frm_proc_sel.grid(row=0, column=0, sticky='news')
        #####################
        #
        #####################
        #MAIN ANALYSIS BLOCK#
        #
        frm_proc_construction = Frame(master=lblfrm_analysis)
        #
        ####Process List####
        frm_proc_list = Frame(master=frm_proc_construction)
        self.lstbx_procs_current = ListBoxScrollBar(frm_proc_list)
        self.lstbx_procs_current.frame.grid(row=0, column=0, columnspan=3, sticky="news")
        self.btn_proc_list_up = Button(frm_proc_list, text="▲", command=self._event_btn_post_proc_up)
        self.btn_proc_list_up.grid(row=1, column=0, sticky="ew")
        self.btn_proc_list_down = Button(frm_proc_list, text="▼", command=self._event_btn_post_proc_down)
        self.btn_proc_list_down.grid(row=1, column=1, sticky="ew")
        self.btn_proc_list_del = Button(frm_proc_list, text="❌", command=self._event_btn_post_proc_delete)
        self.btn_proc_list_del.grid(row=1, column=2, sticky="we")
        #
        frm_proc_list.rowconfigure(0, weight=1)
        frm_proc_list.rowconfigure(1, weight=0)
        frm_proc_list.columnconfigure(0, weight=1)
        frm_proc_list.columnconfigure(1, weight=1)
        frm_proc_list.columnconfigure(2, weight=1)
        frm_proc_list.grid(row=0, column=0, sticky="news")
        #
        ####Analysis Display Window####
        self.frm_proc_disp = Frame(master=frm_proc_construction)
        self.frm_proc_disp.columnconfigure(0, weight=0)
        self.frm_proc_disp.columnconfigure(1, weight=1)
        self.frm_proc_disp.grid(row=0, column=1, sticky="news")
        self.frm_proc_disp_children = []    #Tkinter's frame children enumeration is a bit strange...
        #
        #
        frm_proc_construction.rowconfigure(0, weight=1)
        frm_proc_construction.columnconfigure(0, weight=2)
        frm_proc_construction.columnconfigure(1, weight=1)
        frm_proc_construction.grid(row=1, column=0, sticky='news')
        #### ####
        #
        #
        #Space for Error Message
        frm_proc_output_tbx = Frame(master=lblfrm_analysis)
        self.lbl_procs_errors = Label(frm_proc_output_tbx, text = "")
        self.lbl_procs_errors.grid(row=0, column=0)
        #
        frm_proc_output_tbx.grid(row=2, column=0, sticky='news')
        #####################
        #
        lblfrm_analysis.columnconfigure(0, weight=1)
        lblfrm_analysis.rowconfigure(0, weight=1)
        lblfrm_analysis.rowconfigure(1, weight=1)
        lblfrm_analysis.rowconfigure(2, weight=0)
        lblfrm_analysis.grid(row=1, column=0, padx=10, pady=2, sticky='news')
        #
        #################
        #
        self.frame_RHS.rowconfigure(0, weight=0)
        self.frame_RHS.rowconfigure(1, weight=1)
        self.frame_RHS.columnconfigure(0, weight=1)

        #Setup colour maps
        def_col_maps = [('viridis', "Viridis"), ('afmhot', "AFM Hot"), ('hot', "Hot"), ('gnuplot', "GNU-Plot"), ('coolwarm', "Cool-Warm"), ('seismic', "Seismic"), ('rainbow', "Rainbow")]
        self.colour_maps = []
        for cur_col_map in def_col_maps:
            self.colour_maps.append(ColourMap.fromDefault(cur_col_map[0], cur_col_map[1]))
        file_path = 'ColourMaps/'
        json_files = [pos_json for pos_json in os.listdir(file_path) if pos_json.endswith('.json')]
        for cur_json_file in json_files:
            with open(file_path + cur_json_file) as json_file:
                data = json.load(json_file)
                self.colour_maps.append(ColourMap.fromCustom(data, cur_json_file[:-5]))
        #Commit colour maps to ComboBox
        self.cmbx_ckey.update_vals([x.Name for x in self.colour_maps])
        self.plot_main.set_colour_key(self.colour_maps[self.cmbx_ckey.get_sel_val(True)], False)

        self.plot_main.Canvas.mpl_connect("key_press_event", self._event_form_on_key_press)
        self.plot_main.add_cursor('red')

        #Setup analysis cursors
        #Setup a dictionary which maps the cursor name to the cursor class...
        self.possible_cursors = Analysis_Cursor.get_all_analysis_cursors()
        #Setup a dictionary which maps hatching patterns into unicode symbols to fill the table...
        #https://matplotlib.org/devdocs/gallery/shapes_and_collections/hatch_style_reference.html
        #https://www.key-shortcut.com/en/writing-systems/35-symbols/symbols-typography
        self.cursor_hatchings = {
            '//' : '▨',
            '\\\\' : '▧',
            '++' : '▦',
            'xx' : '▩'
        }
        self.cmbx_anal_cursors.update_vals(self.possible_cursors.keys())
        self._update_analy_cursor_table_widths = False

        self.data_thread_pool = ThreadPool(processes=1)
        self.reset_ui()

        #Setup update rates
        self.update_times = [0, 1, 2, 5, 10, 30, 60]
        #Zero is manual updating
        update_strs = ["Manual"] + [f"{x}s" for x in self.update_times[1:]]
        self.cmbx_update_rate.update_vals(update_strs)
        self.man_update_plot = False

        #Setup the slicing variables
        self.dict_var_slices = {}   #They values are given as: (current index, numpy array of values)
        self.cur_slice_var_keys_lstbx = []
        self.lstbx_slice_vars.listbox.bind("<<ListboxSelect>>", self._event_lstbx_slice_vars_changed)

        #Setup available postprocessors
        self.post_procs_all = PostProcessors.get_all_post_processors()
        self.lstbx_procs.update_vals(self.post_procs_all.keys())
        self.lstbx_procs.listbox.bind("<<ListboxSelect>>", self._event_lstbxPPfunction_changed)
        #Currently selected postprocessors
        self.cur_post_procs = []
        self.lstbx_procs_current.listbox.bind("<<ListboxSelect>>", self._event_lstbx_proc_current_changed)
        self.post_procs_enabled_chkbx_var = tk.BooleanVar()
        self.cur_post_proc_output = "dFinal"
        #Setup current post-processing analysis ListBox and select the first entry (the final output entry)
        self._post_procs_fill_current(0)
        #Kick-start the UI elements
        self._event_lstbxPPfunction_changed(None)
        self._event_lstbx_proc_current_changed(None)

        #Initialise UI to then adjust the sashes to make the UI just right
        self.file_path = ""
        self.root.update()
        #Take about 350 pixels for the RHS toolbars...
        cur_width = self.pw_main_LR_UI.winfo_width()
        self.pw_main_LR_UI.sash_place(0, int(cur_width-350), 1)
        #Give about 171 pixels for the bottom cursors
        cur_height = self.pw_lhs.winfo_height()
        self.pw_lhs.sash_place(0, 1, int(cur_height-171))
        #Initial update time-stamp
        self.last_update_time = time.time()

    def main_loop(self):
        import time
        while True:
            start_time = time.time()
            if self.data_extractor:
                if self.data_extractor.data_ready():
                    (indep_params, final_data, dict_rem_slices) = self.data_extractor.get_data()
                    if not self.update_plot_post_proc(indep_params, final_data):
                        #Not post-processed (hence not plotted) - so do so now...
                        cur_var_ind = self.dep_vars.index(self.cmbx_dep_var.get_sel_val())
                        if len(indep_params) == 1:
                            self.plot_main.plot_data_1D(indep_params[0], final_data[cur_var_ind])
                        else:
                            self.plot_main.plot_data_2D(indep_params[0], indep_params[1], final_data[cur_var_ind].T)    #Transposed due to pcolor's indexing requirements...
                    #
                    #Populate the slice candidates
                    #
                    cur_lstbx_vals = []
                    prev_dict = self.dict_var_slices.copy()
                    self.dict_var_slices = {}   #Clear previous dictionary and only leave entries if it had previous slices present...
                    #Gather currently selected value so it stays selected
                    cur_sel = self.lstbx_slice_vars.get_sel_val(True)
                    if cur_sel != -1:
                        cur_var = self.cur_slice_var_keys_lstbx[cur_sel]
                    else:
                        cur_var = ""
                    cur_sel = -1
                    #Update the current list of slicing variables with the new list...
                    self.cur_slice_var_keys_lstbx = []
                    for m, cur_key in enumerate(dict_rem_slices.keys()):
                        #Check if key already exists
                        if cur_key in prev_dict:
                            self.dict_var_slices[cur_key] = (prev_dict[cur_key][0], dict_rem_slices[cur_key])
                        else:
                            self.dict_var_slices[cur_key] = (0, dict_rem_slices[cur_key])
                        cur_lstbx_vals += [self._slice_Var_disp_text(cur_key, self.dict_var_slices[cur_key])]
                        self.cur_slice_var_keys_lstbx += [cur_key]
                        if cur_var == cur_key:
                            cur_sel = m
                    if len(cur_lstbx_vals) > 0 and cur_sel == -1:
                        #In the beginning, it's a good idea to select the element to kick-start the UI elements
                        self.lstbx_slice_vars.update_vals(cur_lstbx_vals, select_index=0, generate_selection_event=True)
                    else:
                        self.lstbx_slice_vars.update_vals(cur_lstbx_vals, select_index=cur_sel, generate_selection_event=False)

                    #Setup next-update time-stamp and clear manual update flag...
                    self.last_update_time = time.time()
                    self.man_update_plot = False

                cursor_changes = self.plot_main.update_cursors()
                #Cursor update
                curse_infos = []
                curse_cols = []
                for cur_curse in self.plot_main.Cursors:
                    curse_infos += [ f"X: {cur_curse.cur_coord[0]}, Y: {cur_curse.cur_coord[1]}" ]
                    curse_cols += [cur_curse.colour]
                self.lstbx_cursors.update_vals(curse_infos, curse_cols)
                #Analysis cursor update
                if self._update_analy_cursor_table_widths or cursor_changes:
                    cur_anal_cursor_table = []
                    for cur_curse in self.plot_main.AnalysisCursors:
                        cur_anal_cursor_table += [(self._update_analy_cursor_item(cur_curse), cur_curse)]
                    self.lstbx_analy_cursors.update_vals(cur_anal_cursor_table, update_widths = self._update_analy_cursor_table_widths)
                    self._update_analy_cursor_table_widths = False

                #Setup new request if no new data is being fetched
                if not self.data_extractor.isFetching:
                    #Get current update time
                    cur_update_time = self.update_times[self.cmbx_update_rate.get_sel_val(True)]
                    cur_elapsed = time.time() - self.last_update_time
                    #Request new data if it's time to update (i.e. comparing the time since last update with a non-zero update time)
                    if self.man_update_plot or (cur_update_time > 0 and cur_elapsed > cur_update_time):
                        xVar = self.cmbx_axis_x.get_sel_val()
                        slice_vars = {}
                        for cur_var in self.dict_var_slices.keys():
                            slice_vars[cur_var] = self.dict_var_slices[cur_var][0]
                        if self.plot_dim_type.get() == 1:
                            self.data_extractor.fetch_data({'axis_vars':[xVar], 'slice_vars':slice_vars})
                        else:
                            yVar = self.cmbx_axis_y.get_sel_val()
                            if xVar != yVar:
                                self.data_extractor.fetch_data({'axis_vars':[xVar, yVar], 'slice_vars':slice_vars})

            #tkinter.mainloop()
            # self.root.update_idletasks()
            try:
                self.root.update()
            except:
                #Application destroyed...
                return
            if time.time() - start_time > 0:
                print("FPS: ", 1.0 / (time.time() - start_time), end='\r') # FPS = 1 / time to process loop
        # If you put root.destroy() here, it will cause an error if the window is
        # closed with the window manager.

    def _event_plotsel_changed(self):
        if self.plot_dim_type.get() == 1:
            #1D Plot
            self.cmbx_axis_y.disable()
            self.cmbx_ckey.disable()
        else:
            #2D Plot
            self.cmbx_axis_y.enable()
            self.cmbx_ckey.enable()

    def _event_btn_plot_main_update(self):
        self.man_update_plot = True

    def _event_btn_plot_main_get_attrs(self):
        clip_str = f"File: {self.file_path}\n"
        self.root.clipboard_clear()
        self.root.clipboard_append(clip_str)

    def _update_analy_cursor_item(self, analy_cursor):
        if analy_cursor.Visible:
            cur_sh_icon = "👁"
        else:
            cur_sh_icon = "⊘"
        return [cur_sh_icon, self.cursor_hatchings[analy_cursor.SymbolFill], analy_cursor.Name, analy_cursor.Type, analy_cursor.Summary]
    def _event_btn_anal_cursor_add(self):
        self._update_analy_cursor_table_widths = True
        cur_sel = self.cmbx_anal_cursors.get_sel_val()

        #Find previous names
        prev_names = []
        for cur_curse in self.plot_main.AnalysisCursors:
            if cur_curse.Type == cur_sel:
                prev_names += [cur_curse.Name]
        #Choose new name
        new_prefix = self.possible_cursors[cur_sel].Prefix
        m = 0
        while f'{new_prefix}{m}' in prev_names:
            m += 1
        new_name = f'{new_prefix}{m}'

        #Get previous symbols
        prev_syms = [x.SymbolFill for x in self.plot_main.AnalysisCursors]
        #Choose new symbol
        new_sym = None
        for cur_sym in self.cursor_hatchings.keys():
            if cur_sym not in prev_syms:
                new_sym = cur_sym
                break
        #Choose random symbol if all are already taken
        if new_sym == None:
            import random
            new_sym = prev_syms[random.randint(0, len(prev_syms)-1)]

        ###ADD NEW ANALYSIS CURSORS HERE###
        if self.dark_mode:
            curse_col = 'white'
        else:
            curse_col = 'black'
        new_obj = self.possible_cursors[cur_sel](new_name, curse_col)
        self.plot_main.AnalysisCursors += [new_obj]
        #
        new_obj.SymbolFill = new_sym
        new_obj.prepare_plot(self.plot_main, self.plot_main.ax)
    def _event_btn_anal_cursor_del(self):
        cur_sel = self.lstbx_analy_cursors.del_sel_val()
        cur_name = cur_sel[2]
        #Presuming that the names across types are unique...
        cur_obj = None
        for ind, cur_curse in enumerate(self.plot_main.AnalysisCursors):
            if cur_curse.Name == cur_name:
                cur_obj = self.plot_main.AnalysisCursors.pop(ind)
                cur_obj.delete_from_plot()

    def _slice_Var_disp_text(self, slice_var_name, cur_slice_var_params):
        '''
        Generates the text to display the summary in the ListBox for slicing variables.

        Input:
            - slice_var_name       - String name of the current slicing variable to display in the ListBox
            - cur_slice_var_params - A tuple given as (current index, numpy array of allowed values)
        
        Returns a string of the text to display - i.e. Name current-val (min-val, max-val).
        '''
        cur_val = cur_slice_var_params[1][cur_slice_var_params[0]]
        return f"{slice_var_name}: {cur_val}"
    def _update_label_slice_var_val(self):
        #Update Label
        cur_var_name = self.cur_slice_var_keys_lstbx[self.lstbx_slice_vars.get_sel_val(True)]
        min_val = np.min(self.dict_var_slices[cur_var_name][1])
        max_val = np.max(self.dict_var_slices[cur_var_name][1])
        self.lbl_slice_vars_val['text'] = f"Range: {min_val}➜{max_val}"
    def _event_lstbx_slice_vars_changed(self, event):
        cur_slice_var = self.dict_var_slices[self.cur_slice_var_keys_lstbx[self.lstbx_slice_vars.get_sel_val(True)]]
        self.sldr_slice_vars_val.configure(to=cur_slice_var[1].size-1)
        self.sldr_slice_vars_val.set(cur_slice_var[0])
        self._update_label_slice_var_val()
    def _event_btn_slice_vars_val_inc(self):
        cur_sel_ind = self.lstbx_slice_vars.get_sel_val(True)
        if cur_sel_ind == -1:
            return
        cur_var_name = self.cur_slice_var_keys_lstbx[cur_sel_ind]
        cur_len = self.dict_var_slices[cur_var_name][1].size
        cur_ind = int(float(self.sldr_slice_vars_val.get()))
        if cur_ind + 1 < cur_len:
            self.sldr_slice_vars_val.set(cur_ind + 1)
    def _event_btn_slice_vars_val_dec(self):
        cur_sel_ind = self.lstbx_slice_vars.get_sel_val(True)
        if cur_sel_ind == -1:
            return
        cur_var_name = self.cur_slice_var_keys_lstbx[cur_sel_ind]
        cur_ind = int(float(self.sldr_slice_vars_val.get()))
        if cur_ind > 0:
            self.sldr_slice_vars_val.set(cur_ind - 1)
    def _event_sldr_slice_vars_val_changed(self, value):
        self._slice_vars_set_val(int(float(value)))
    def _slice_vars_set_val(self, new_index):
        #Calculate the index of the array with the value closest to the proposed value
        cur_sel_ind = self.lstbx_slice_vars.get_sel_val(True)
        if cur_sel_ind == -1:
            return
        cur_var_name = self.cur_slice_var_keys_lstbx[cur_sel_ind]
        if new_index != self.dict_var_slices[cur_var_name][0]:
            #Update the array index
            self.dict_var_slices[cur_var_name] = (new_index, self.dict_var_slices[cur_var_name][1])
            #Update ListBox
            self.lstbx_slice_vars.modify_selected_index(self._slice_Var_disp_text(cur_var_name, self.dict_var_slices[cur_var_name]))
            #Update Label
            self._update_label_slice_var_val()
      

    def _event_form_on_key_press(self,event):
        print("you pressed {}".format(event.key))
        key_press_handler(event, self.plot_main.Canvas, self.plot_main.ToolBar)
    
    def _event_cmbxCKey_changed(self, event):
        self._update_plot_col_map()
    def _callback_chkbx_hist_eq_enabled(self):
        self._update_plot_col_map()
    def _update_plot_col_map(self):
        self.plot_main.set_colour_key(self.colour_maps[self.cmbx_ckey.get_sel_val(True)], self.hist_eq_enabled_var.get())

    def _event_lstbxPPfunction_changed(self, event):
        self.lbl_proc_sel_desc.Label['text'] = "Description: " + self.post_procs_all[self.lstbx_procs.get_sel_val()].get_description()

    def _post_procs_current_disp_text(self, cur_proc):
        '''
        Generates the string shown in each entry in the ListBox of current processes used in the post-processing.

        Inputs:
            cur_proc - Current process to be displayed. It is simply one of the tuples in the array self.cur_post_procs.
        '''
        #Filter to only show the data arguments
        arr_args_in = []
        for ind, cur_arg in enumerate(cur_proc['ProcessObj'].get_input_args()):
            if cur_arg[1] == 'data':
                arr_args_in += [cur_proc['ArgsInput'][ind]]
        arr_args_in = tuple(arr_args_in)
        #
        arr_args_out = []
        for ind, cur_arg in enumerate(cur_proc['ProcessObj'].get_output_args()):
            if cur_arg[1] == 'data':
                arr_args_out += [cur_proc['ArgsOutput'][ind]]
        arr_args_out = tuple(arr_args_out)
        #
        #If all arguments are to be shown, comment the above and uncomment that below:
        # arr_args_in = tuple(cur_proc['ArgsInput'])
        # arr_args_out = tuple(cur_proc['ArgsOutput'])
        #Note that it also has to be changed in callback functions like _callback_tbx_post_procs_disp_callback_Int etc...

        if cur_proc['Enabled']:
            cur_str = ""
        else:
            cur_str = "⊘"
        cur_str += str(arr_args_in)
        cur_str += "→"
        cur_str += cur_proc['ProcessName']
        cur_str += "→"
        cur_str += str(arr_args_out)
        return cur_str.replace('\'','')
    def _post_procs_fill_current(self, sel_index = -1):
        cur_proc_strs = []
        for cur_proc in self.cur_post_procs:
            cur_proc_strs += [self._post_procs_current_disp_text(cur_proc)]
        cur_proc_strs += ["Final Output: "+self.cur_post_proc_output]

        self.lstbx_procs_current.update_vals(cur_proc_strs)
        if sel_index != -1:
            self.lstbx_procs_current.select_index(sel_index)

    def _post_procs_disp_clear(self):
        for cur_child_ui_elem in self.frm_proc_disp_children[::-1]:
            cur_child_ui_elem.grid_forget()
            cur_child_ui_elem.destroy()
        self.frm_proc_disp_children = []

    def is_float(self, val):
        try:
            float(val)
            return True
        except ValueError:
            return False
    def _callback_tbx_post_procs_disp_callback(self, cur_proc, arg_index, strVal):
        cur_proc['ArgsInput'][arg_index] = strVal
        self.lstbx_procs_current.modify_selected_index(self._post_procs_current_disp_text(cur_proc))
        return True
    def _callback_tbx_post_procs_disp_callback_Int(self, cur_proc, arg_index, strVal):
        #Check for positive or negative integers...
        if strVal.isdigit() or (strVal.startswith('-') and strVal[1:].isdigit()):
            cur_proc['ArgsInput'][arg_index] = int(strVal)
            #No need to update the listbox if the non-data arguments are not shown
            # self.lstbx_procs_current.modify_selected_index(self._post_procs_current_disp_text(cur_proc))
            self.root.bell()
            return True
        else:
            return False
    def _callback_tbx_post_procs_disp_callback_Float(self, cur_proc, arg_index, strVal):
        #Check for positive or negative integers...
        if strVal != '' and self.is_float(strVal):
            cur_proc['ArgsInput'][arg_index] = float(strVal)
            #No need to update the listbox if the non-data arguments are not shown
            # self.lstbx_procs_current.modify_selected_index(self._post_procs_current_disp_text(cur_proc))
            self.root.bell()
            return True
        else:
            return False
    def _callback_tbx_post_procs_disp_outputs_callback(self, cur_proc, arg_index, strVal):
        cur_proc['ArgsOutput'][arg_index] = strVal
        self.lstbx_procs_current.modify_selected_index(self._post_procs_current_disp_text(cur_proc))
        return True
    def _callback_chkbx_post_procs_disp_enabled(self, cur_proc):
        cur_proc['Enabled'] = self.post_procs_enabled_chkbx_var.get()
        self.lstbx_procs_current.modify_selected_index(self._post_procs_current_disp_text(cur_proc))
    def _callback_cmbx_post_procs_disp_callback(self, cur_proc, arg_index, event):
        cur_proc['ArgsInput'][arg_index] = event.widget.get()
        self.lstbx_procs_current.modify_selected_index(self._post_procs_current_disp_text(cur_proc))
        return True
    def _callback_cmbx_post_procs_disp_final_output_callback(self, event):
        self.cur_post_proc_output = event.widget.get()
        self.lstbx_procs_current.modify_selected_index("Final Output: "+self.cur_post_proc_output)
        return True
    def _get_post_procs_possible_inputs(self, cur_proc_ind):
        if type(self.dep_vars) is list:
            possible_inputs = self.dep_vars[:]
        else:
            possible_inputs = []
        for prev_ind in range(cur_proc_ind):
            prev_proc = self.cur_post_procs[prev_ind]
            for cur_output in prev_proc['ArgsOutput']:
                if not cur_output in possible_inputs:
                    possible_inputs += [cur_output]
        return possible_inputs
    def _post_procs_disp_activate(self):
        cur_proc_ind = self.lstbx_procs_current.get_sel_val(True)

        #Selected the Final Output entry
        row_off = 0
        if cur_proc_ind == len(self.cur_post_procs):
            lbl_procs = Label(self.frm_proc_disp, text = "Output dataset")
            lbl_procs.grid(row=row_off, column=0)
            self.frm_proc_disp_children.append(lbl_procs)
            #
            cmbx_proc_output = ComboBoxEx(self.frm_proc_disp, "", width=6)
            #Gather all previous output variables...
            possible_inputs = self._get_post_procs_possible_inputs(cur_proc_ind)
            #If the current setting for the input argument is not in the pool of possible inputs, then replace with a default first...
            cmbx_proc_output.combobox.bind("<<ComboboxSelected>>", partial(self._callback_cmbx_post_procs_disp_final_output_callback) )
            sel_ind = 0
            if len(possible_inputs) > 0 and self.cur_post_proc_output in possible_inputs:
                sel_ind = possible_inputs.index(self.cur_post_proc_output)
            cmbx_proc_output.update_vals(possible_inputs, sel_ind)
            #
            cmbx_proc_output.Frame.grid(row=row_off, column=1, sticky='we')
            self.frm_proc_disp_children.append(cmbx_proc_output.combobox)
            return

        #Selected a process in the post-processing chain
        cur_proc = self.cur_post_procs[cur_proc_ind]
        
        row_off = 0
        chkbx_enabled = ttk.Checkbutton(self.frm_proc_disp, text = "Enabled", variable=self.post_procs_enabled_chkbx_var, command=partial(self._callback_chkbx_post_procs_disp_enabled, cur_proc))
        self.post_procs_enabled_chkbx_var.set(cur_proc['Enabled'])
        chkbx_enabled.grid(row=row_off, column=0)
        self.frm_proc_disp_children.append(chkbx_enabled)
        row_off += 1
        #
        for ind, cur_arg in enumerate(cur_proc['ProcessObj'].get_input_args()):
            lbl_procs = Label(self.frm_proc_disp, text = cur_arg[0])
            lbl_procs.grid(row=row_off, column=0)
            self.frm_proc_disp_children.append(lbl_procs)
            if cur_arg[1] == 'data':
                cmbx_proc_output = ComboBoxEx(self.frm_proc_disp, "", width=6)
                #Gather all previous output variables...
                possible_inputs = self._get_post_procs_possible_inputs(cur_proc_ind)
                #If the current setting for the input argument is not in the pool of possible inputs, then replace with a default first...
                cmbx_proc_output.combobox.bind("<<ComboboxSelected>>", partial(self._callback_cmbx_post_procs_disp_callback, cur_proc, ind) )
                sel_ind = 0
                if len(possible_inputs) > 0 and cur_proc['ArgsInput'][ind] in possible_inputs:
                    sel_ind = possible_inputs.index(cur_proc['ArgsInput'][ind])
                cmbx_proc_output.update_vals(possible_inputs, sel_ind)
                #
                cmbx_proc_output.Frame.grid(row=row_off, column=1, sticky='we')
                self.frm_proc_disp_children.append(cmbx_proc_output.combobox)
            else:
                #
                # if cur_arg[1] == 'cursor':
                #     cmbx_proc_output = ComboBoxEx(self.frm_proc_disp, "")
                #     cmbx_proc_output.update_vals([x.Name for x in self.plot_main.AnalysisCursors if x.Type == cur_arg[2]])
                #     cmbx_proc_output.Frame.grid(row=row_off, column=1)
                #     self.frm_proc_disp_children.append(cmbx_proc_output.combobox)
                # else:
                tbx_proc_output = ttk.Entry(self.frm_proc_disp, validate="key", width=8)  #validate can be validate="focusout" as well
                tbx_proc_output.insert(END, cur_proc['ArgsInput'][ind])
                if cur_arg[1] == 'int':
                    tbx_proc_output['validatecommand'] = (tbx_proc_output.register( partial(self._callback_tbx_post_procs_disp_callback_Int, cur_proc, ind) ), "%P")
                elif cur_arg[1] == 'float':
                    tbx_proc_output['validatecommand'] = (tbx_proc_output.register( partial(self._callback_tbx_post_procs_disp_callback_Float, cur_proc, ind) ), "%P")
                else:
                    tbx_proc_output['validatecommand'] = (tbx_proc_output.register( partial(self._callback_tbx_post_procs_disp_callback, cur_proc, ind) ), "%P")
                tbx_proc_output.grid(row=row_off, column=1, sticky='we')
                self.frm_proc_disp_children.append(tbx_proc_output)
            #
            row_off += 1
        lbl_procs = Label(self.frm_proc_disp, text = "Outputs:")
        lbl_procs.grid(row=row_off, column=0)
        self.frm_proc_disp_children.append(lbl_procs)
        row_off += 1
        for ind, cur_arg in enumerate(cur_proc['ProcessObj'].get_output_args()):
            lbl_procs = Label(self.frm_proc_disp, text = cur_arg[0])
            lbl_procs.grid(row=row_off, column=0)
            self.frm_proc_disp_children.append(lbl_procs)
            #
            tbx_proc_output = ttk.Entry(self.frm_proc_disp, validate="key", width=8)  #validate can be validate="focusout" as well
            tbx_proc_output.insert(END, cur_proc['ArgsOutput'][ind])
            #These are data/variable names - thus, they require no validation as they are simply strings...
            tbx_proc_output['validatecommand'] = (tbx_proc_output.register( partial(self._callback_tbx_post_procs_disp_outputs_callback, cur_proc, ind) ), "%P")
            tbx_proc_output.grid(row=row_off, column=1, sticky='we')
            self.frm_proc_disp_children.append(tbx_proc_output)
            #
            row_off += 1

    def _event_btn_post_proc_up(self):
        cur_ind = self.lstbx_procs_current.get_sel_val(True)
        if cur_ind > 0 and cur_ind < len(self.cur_post_procs):  #Shouldn't fail as the button should be otherwise disabled (rather redundant check...)
            cur_val = self.cur_post_procs.pop(cur_ind)
            self.cur_post_procs.insert(cur_ind-1, cur_val)
            self._post_procs_fill_current(cur_ind-1)
    def _event_btn_post_proc_down(self):
        cur_ind = self.lstbx_procs_current.get_sel_val(True)
        if cur_ind < len(self.cur_post_procs)-1:  #Shouldn't fail as the button should be otherwise disabled (rather redundant check...)
            cur_val = self.cur_post_procs.pop(cur_ind)
            self.cur_post_procs.insert(cur_ind+1, cur_val)
            self._post_procs_fill_current(cur_ind+1)
    def _event_btn_post_proc_add(self):
        cur_func = self.lstbx_procs.get_sel_val()
        cur_func_obj = self.post_procs_all[cur_func]
        self.cur_post_procs += [{
            'ArgsInput'   : cur_func_obj.get_default_input_args(),
            'ArgsOutput'  : cur_func_obj.get_default_output_args(),
            'ProcessName' : cur_func,
            'ProcessObj'  : cur_func_obj,
            'Enabled'     : True
        }]
        self._post_procs_fill_current(len(self.cur_post_procs)-1)
    def _event_btn_post_proc_delete(self):
        cur_ind = self.lstbx_procs_current.get_sel_val(True)
        if cur_ind < len(self.cur_post_procs):  #Shouldn't fail as the button should be otherwise disabled (rather redundant check...)
            self.cur_post_procs.pop(cur_ind)
            self._post_procs_fill_current(cur_ind)    #Should at worst select the final output entry...
    def _event_lstbx_proc_current_changed(self, event):
        self._post_procs_disp_clear()
        self._post_procs_disp_activate()
        #Disable the movement arrows if selecting an edge
        cur_ind = self.lstbx_procs_current.get_sel_val(True)
        if cur_ind < len(self.cur_post_procs)-1:
            self.btn_proc_list_down.configure(state='normal')
        else:
            self.btn_proc_list_down.configure(state='disabled')
        if cur_ind == 0 or cur_ind >= len(self.cur_post_procs):
            self.btn_proc_list_up.configure(state='disabled')
        else:
            self.btn_proc_list_up.configure(state='normal')
        #Disable delete button if selecting the final output entry
        if cur_ind == len(self.cur_post_procs):
            self.btn_proc_list_del.configure(state='disabled')
        else:
            self.btn_proc_list_del.configure(state='normal')


    def reset_ui(self):
        self.data_extractor = None
        self.indep_vars = None
        self.dep_vars = None
        #
        self._prev_x_axis = self.cmbx_axis_x.get_sel_val()
        self._prev_y_axis = self.cmbx_axis_y.get_sel_val()
        self.cmbx_axis_x.update_vals([])
        self.cmbx_axis_x.disable()
        self.cmbx_axis_y.update_vals([])
        self.cmbx_axis_y.disable()
        self.cmbx_dep_var.update_vals([])
        self.cmbx_dep_var.disable()
        #
        self.lstbx_cursors.update_vals([], generate_selection_event=False)
        self.lstbx_cursors.disable()
        self.lstbx_slice_vars.update_vals([], generate_selection_event=False)
        self.lstbx_slice_vars.disable()
        self.lbl_slice_vars_val['text'] = "Min|Max"
        #
        self._prev_plot_dim = self.plot_dim_type.get()
        self.plot_dim_type.set(1)
        self.rdbtn_plot_sel_1D.configure(state='disabled')
        self.rdbtn_plot_sel_2D.configure(state='disabled')
        #
        self.btn_cursor_add.configure(state='disabled')
        self.btn_cursor_del.configure(state='disabled')
        self.btn_analy_cursor_add.configure(state='disabled')
        self.btn_analy_cursor_del.configure(state='disabled')
    def init_ui(self):
        self.indep_vars = self.data_extractor.get_independent_vars()
        self.cmbx_axis_x.update_vals(self.indep_vars)
        self.cmbx_axis_y.update_vals(self.indep_vars)
        self.dep_vars = self.data_extractor.get_dependent_vars()
        self.cmbx_dep_var.update_vals(self.dep_vars)
        #
        self.cmbx_axis_x.enable()
        self.cmbx_axis_y.enable()
        self.cmbx_dep_var.enable()
        #
        self.lstbx_cursors.enable()
        self.lstbx_slice_vars.enable()
        #
        self.plot_dim_type.set(self._prev_plot_dim)
        self.rdbtn_plot_sel_1D.configure(state='normal')
        self.rdbtn_plot_sel_2D.configure(state='normal')
        #
        self.btn_cursor_add.configure(state='normal')
        self.btn_cursor_del.configure(state='normal')
        self.btn_analy_cursor_add.configure(state='normal')
        self.btn_analy_cursor_del.configure(state='normal')
        #
        #Select previous axes if available...
        if self._prev_x_axis != None:
            self.cmbx_axis_x.set_sel_val(self._prev_x_axis)
            self._prev_x_axis = None
        if self._prev_y_axis != None:
            self.cmbx_axis_y.set_sel_val(self._prev_y_axis)
            self._prev_y_axis = None

    def _open_file_hdf5(self):
        # file type
        filetypes = (
            ('SQDToolz HDF5', '*.h5'),
            #('TSV Data Files', '*.dat')
            #('All files', '*.*')
        )
        # show the open file dialog
        filename = fd.askopenfile(filetypes=filetypes)
        # read the text file and show its content on the Text
        if filename:
            self.reset_ui()
            self._open_sqdtoolz_hdf5(filename.name)
    def _open_sqdtoolz_hdf5(self, file_path):
        self.file_path = file_path
        #Setup data extraction
        self.data_thread_pool = ThreadPool(processes=1)
        self.data_extractor = DataExtractorH5single(file_path, self.data_thread_pool)
        self.init_ui()

    def _open_file_hdf5folders(self):
        # file type
        filetypes = (
            ('SQDToolz HDF5', '*.h5'),
            #('TSV Data Files', '*.dat')
            #('All files', '*.*')
        )
        # show the open file dialog
        filename = fd.askopenfile(filetypes=filetypes)
        # read the text file and show its content on the Text
        if filename:
            self.reset_ui()
            self._open_sqdtoolz_hdf5folders(filename.name)
    def _open_sqdtoolz_hdf5folders(self, file_path):
        self.file_path = file_path
        #Setup data extraction
        self.data_thread_pool = ThreadPool(processes=1)
        self.data_extractor = DataExtractorH5multiple(file_path, self.data_thread_pool)
        self.init_ui()

    def _open_file_dat(self):
        # file type
        filetypes = (
            ('UQTools DAT', '*.dat'),
            #('TSV Data Files', '*.dat')
            #('All files', '*.*')
        )
        # show the open file dialog
        filename = fd.askopenfile(filetypes=filetypes)
        # read the text file and show its content on the Text
        if filename:
            self.reset_ui()
            self._open_uqtools_dat(filename.name)
    def _open_uqtools_dat(self, file_path):
        self.file_path = file_path
        #Setup data extraction
        self.data_thread_pool = ThreadPool(processes=1)
        self.data_extractor = DataExtractorUQtoolsDAT(file_path, self.data_thread_pool)
        self.init_ui()

    def _open_file_next(self):
        if not isinstance(self.data_extractor, DataExtractorH5single):
            return

        cur_file = self.data_extractor.file_name
        cur_exp_dir = os.path.dirname(cur_file)
        cur_parent_dir = os.path.dirname(cur_exp_dir) + '/'  #Should exist...

        dirs = [x[0] for x in os.walk(cur_parent_dir)]
        cur_ind = dirs.index(cur_exp_dir)
        cur_ind = cur_ind + 1
        filename = ''
        while cur_ind < len(dirs):
            cur_file = dirs[cur_ind]+'/data.h5'
            if os.path.exists(cur_file):
                filename = cur_file
                break
            cur_ind = cur_ind + 1
        if filename == '':
            return

        self.reset_ui()
        self._open_sqdtoolz_hdf5(filename)


    def _event_btn_PPupdate_plot(self):
        self.cmds_to_execute = ""
        #Function declarations
        for cur_key in self.post_procs_all.keys():
            self.cmds_to_execute += f'{cur_key} = self.post_procs_all[\'{cur_key}\']\n'
        #Compile post-processing commands
        self.cmds_to_execute += self.tbx_proc_code.get("1.0", tk.END) + '\n'
        cur_output_var = self.tbx_proc_output.get()
        self.cmds_to_execute += f'global cur_data; cur_data={cur_output_var}'

    def update_plot_post_proc(self, indep_params, dep_params):
        if len(self.cur_post_procs) == 0:
            self.lbl_procs_errors['text'] = f"Add functions to activate postprocessing."
            return False

        #Drop the update if there are non-1D commands enabled...
        if len(indep_params) == 1:
            for ind, cur_proc in enumerate(self.cur_post_procs):
                if not cur_proc['ProcessObj'].supports_1D() and cur_proc['Enabled']:
                    self.lbl_procs_errors['text'] = f"A non-1D plot process has been enabled in step #{ind}."
                    return False

        #Data declarations
        data = {}
        for ind, cur_dep_var in enumerate(self.dep_vars):
            if len(indep_params) == 1:
                data[cur_dep_var] = {'x': indep_params[0], 'data': dep_params[ind]}
            else:
                data[cur_dep_var] = {'x': indep_params[0], 'y': indep_params[1], 'data': dep_params[ind].T}    #Transposed due to pcolor's indexing requirements...

        #Available analysis cursors
        cur_analy_curs_names = [x.Name for x in self.plot_main.AnalysisCursors]

        #Process each command sequentially
        for cur_proc_ind, cur_proc in enumerate(self.cur_post_procs):
            if not cur_proc['Enabled']:
                continue

            #Process input arguments
            cur_args = cur_proc['ArgsInput'][:]
            for ind, cur_arg in enumerate(cur_proc['ProcessObj'].get_input_args()):
                if cur_arg[1] == 'data':
                    if cur_args[ind] in data:
                        cur_args[ind] = data[cur_args[ind]]
                    else:
                        self.lbl_procs_errors['text'] = f"Dataset \'{cur_args[ind]}\' does not exist in step #{cur_proc_ind+1}"
                        return False
                elif cur_arg[1] == 'cursor':
                    the_cursor = None
                    #Find cursor
                    for cur_curse in self.plot_main.AnalysisCursors:
                        if cur_curse.Name == cur_args[ind]:
                            if type(cur_arg[2]) == tuple or type(cur_arg[2]) == list:
                                if cur_curse.Type in cur_arg[2]:
                                    the_cursor = cur_curse
                                    break
                            elif cur_curse.Type == cur_arg[2]:
                                the_cursor = cur_curse
                                break
                    if the_cursor != None:
                        cur_args[ind] = the_cursor
                    else:
                        self.lbl_procs_errors['text'] = f"Cursor \'{cur_args[ind]}\' is not a valid analysis cursor in step #{cur_proc_ind+1}"
                        return False
            #Execute command
            output_tuples = cur_proc['ProcessObj'](*cur_args)
            #Map the outputs into the dictionary
            for ind, cur_arg in enumerate(cur_proc['ProcessObj'].get_output_args()):
                if cur_arg[1] == 'data':
                    data[cur_proc['ArgsOutput'][ind]] = output_tuples[ind]
        
        if self.cur_post_proc_output in data:
            cur_data = data[self.cur_post_proc_output]
        else:
            self.lbl_procs_errors['text'] = f"Dataset \'{self.cur_post_proc_output}\' does not exist"   #It's the final entry - if it doesn't exist yet, it doesn't exist...
            return False

        #No errors - so reset the message...
        self.lbl_procs_errors['text'] = ""

        #Update plots
        if 'data' in cur_data:  #Occurs when the dataset is empty...
            if 'y' in cur_data:
                self.plot_main.plot_data_2D(cur_data['x'], cur_data['y'], cur_data['data'])
            else:
                self.plot_main.plot_data_1D(cur_data['x'], cur_data['data'])
        return True

    def _event_quit():
        root.quit()     # stops mainloop
        root.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    
class ComboBoxEx:
    def __init__(self, parent_ui_element, label, **kwargs):

        if label == "":
            self.combobox = ttk.Combobox(parent_ui_element, **kwargs)
            self.Frame = self.combobox  #If there is no label, then 'Frame' points to the ComboBox...
        else:
            self.Frame = Frame(master=parent_ui_element)
            self.lbl_cmbx = Label(self.Frame, text = label)
            self.lbl_cmbx.grid(row=0, column=0, sticky="nes")
            self.combobox = ttk.Combobox(self.Frame, **kwargs)
            self.combobox.grid(row=0, column=1, sticky="news")
            self.Frame.columnconfigure(0, weight=0) #Label is of constant size
            self.Frame.columnconfigure(1, weight=1) #ComboBox is expected to rescale
            self.Frame.rowconfigure(0, weight=1)

        self._vals = []

    def update_vals(self, list_vals, set_index = -1):
        #Get current selection if applicable:
        if set_index >= 0:
            cur_sel = set_index
        else:
            cur_sel = self.get_sel_val(True)

        #Clear combobox
        self._vals = list(list_vals)
        self.combobox['values'] = self._vals

        if len(list_vals) == 0:
            return
            
        if cur_sel is None or cur_sel < 0 or cur_sel >= len(self._vals):
            #Select first element by default...
            self.combobox.current(0)
        else:
            #Select the prescribed element from above... Note that cur_sel is still in the new list...
            self.combobox.current(cur_sel)
        self.combobox.event_generate("<<ComboboxSelected>>")

    def enable(self):
        self.lbl_cmbx.configure(state='normal')
        self.combobox.configure(state='normal')
    def disable(self):
        self.lbl_cmbx.configure(state='disabled')
        self.combobox.configure(state='disabled')

    def get_sel_val(self, get_index = False):
        if len(self._vals) == 0:
            return None
        if get_index:
            return self.combobox.current()
        else:
            return self._vals[self.combobox.current()]

    def set_sel_val(self, val):
        if val in self._vals:
            self.combobox.current(self._vals.index(val))

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

    def update_vals(self, list_vals, cols=None, select_index=-1, generate_selection_event=True):
        if select_index == -1:
            #Get current selection if applicable:
            cur_sel = [m for m in self.listbox.curselection()]
            #Select first element by default...
            if len(cur_sel) == 0:
                cur_sel = 0
            else:
                cur_sel = cur_sel[0]
        else:
            cur_sel = select_index

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
        if generate_selection_event:
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
        if len(values) == 0:
            return -1
        else:
            return values[0]

    def select_index(self, index, generate_selection_event = True):
        #Clear selection
        self.listbox.selection_clear(0, END)
        #Select new item
        self.listbox.select_set(index)
        if generate_selection_event:
            self.listbox.event_generate("<<ListboxSelect>>")

    def modify_selected_index(self, new_text, generate_selection_event = False):
        if self.listbox.size() == 0:
            return
        cur_ind = self.get_sel_val(True)
        self.listbox.insert(cur_ind, new_text)
        self.listbox.delete(cur_ind+1)
        self.select_index(cur_ind, generate_selection_event)

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
    def fromCustom(cls, cm_data, display_name):
        retObj = cls()
        retObj._cmap = LinearSegmentedColormap.from_list(display_name, cm_data)
        retObj._display_name = display_name
        return retObj
    
    @property
    def Name(self):
        return self._display_name
    @property
    def CMap(self):
        return self._cmap

class NavigationToolbar2TkEx(NavigationToolbar2Tk):
    def __init__(self, canvas, frame, pltfrm):
        self._pltfrm = pltfrm
        super().__init__(canvas, frame)
    
    def home(self, *args):
        super().home(*args)
        self._pltfrm.reset_plot()

    def release_zoom(self, event):
        super().release_zoom(event)
        #Need the plot_2D here as the restore_region doesn't account for the new zoomed extent and won't refresh the pcolor until the next plot update...
        self._pltfrm._plot_2D()

class HistEqNormalize(mplcols.Normalize):
    def __init__(self, data_array, num_bins = 256, clip=False):
        if data_array.size == 0:
            mplcols.Normalize.__init__(self, 0, 1, clip)
        else:
            mplcols.Normalize.__init__(self, np.nanmin(data_array), np.nanmax(data_array), clip)

    def __call__(self, value, clip=None):
        #Note that value is a masked array of all the values to be plotted!
        return np.ma.array(value.argsort().argsort()/(value.size-1))

class PlotFrame:
    def __init__(self, root_ui, update_func = None, get_attr_func = None, dark_mode = False):
        if dark_mode:
            mplstyle.use('dark_background')
        self.fig = Figure(figsize=(1,1))
        t = np.arange(0, 3, .01)
        #self.ax = self.fig.gca() #fig.add_subplot(111)
        # ax.plot(t, 2 * np.sin(2 * np.pi * t))

        gs = self.fig.add_gridspec(2, 2,  width_ratios=(7, 2), height_ratios=(2, 7),
                      left=0.1, right=0.9, bottom=0.1, top=0.9,
                      wspace=0.05, hspace=0.05)
        self.ax = self.fig.add_subplot(gs[1, 0])
        self.ax_sX = self.fig.add_subplot(gs[0, 0])#, sharex=self.ax)
        self.ax_sY = self.fig.add_subplot(gs[1, 1])#, sharey=self.ax)
        self.ax_sX.tick_params(labelbottom=False, bottom=False)
        self.ax_sY.tick_params(labelleft=False, left=False)

        self.ax_cB = self.fig.add_subplot(gs[0, 1])

        self.Frame = Frame(master=root_ui)

        self.Canvas = FigureCanvasTkAgg(self.fig, master = self.Frame)
        self.ToolBar = NavigationToolbar2TkEx(self.Canvas, self.Frame, self)
        if update_func != None:
            self.icon_update = PhotoImage(file = "Icons/UpdatePlots.png")    #Need to store reference for otherwise garbage collection destroys it...
            btn_update = Button(master=self.ToolBar, image=self.icon_update, command=update_func)
            btn_update.pack(side="left")
        self.icon_get_attrs = PhotoImage(file = "Icons/GetAttr.png")    #Need to store reference for otherwise garbage collection destroys it...
        btn_getattrs = Button(master=self.ToolBar, image=self.icon_get_attrs, command=get_attr_func)
        btn_getattrs.pack(side="left")

        self.ToolBar.update()
        self.ToolBar.grid_configure(row=0,column=0,sticky='nsew')
        self.Canvas.get_tk_widget().grid(row=1,column=0,sticky='nsew')

        self.Frame.rowconfigure(0, weight=0)
        self.Frame.rowconfigure(1, weight=1)
        self.Frame.columnconfigure(0, weight=1)

        self.curData = []
        self.Cursors = []
        self.AnalysisCursors = []
        self._cur_col_key = 'viridis'
        self._cur_2D = False
        self._replot_cuts = False
        #
        self.hist_eq = None
        self.hist_eq_enabled = False

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

    def get_axis_size_px(self):
        bbox = self.ax.get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
        width, height = bbox.width, bbox.height
        width *= self.fig.dpi
        height *= self.fig.dpi
        return (width, height)

    def plot_data_1D(self, dataX, dataY):
        if len(self.curData) != 2:
            replot = True
        else:
            extent = [x for x in self.ax.axis()]
            xlimts = self.ax.get_xlim()
            xpct = (extent[1] - extent[0])/(np.max(self.curData[0]) - np.min(self.curData[0]))
            ylimts = self.ax.get_ylim()
            with warnings.catch_warnings(): #To suppress: "RuntimeWarning: All-NaN slice encountered"
                warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
                ypct = (extent[3] - extent[2])/(np.nanmax(self.curData[1]) - np.nanmin(self.curData[1]))
            replot =  xpct > 0.99 and ypct > 0.99
        
        self.curData = (dataX, dataY)
        self._cur_2D = False

        if not replot:
            extent = [x for x in self.ax.axis()]
            a = min(self.curData[0])
            if extent[0] < a: extent[0] = a
            a = max(self.curData[0])
            if extent[1] > a: extent[1] = a
            a = min(self.curData[1])
            if extent[2] < a: extent[2] = a
            a = max(self.curData[1])
            if extent[3] > a: extent[3] = a
            
        self.ax.clear()
        self.ax.plot(self.curData[0], self.curData[1])
        self.ax.set_xlim([np.min(self.curData[0]), np.max(self.curData[0])])
        #Check if the y-axis bounds are sensible...
        with warnings.catch_warnings(): #To suppress: "RuntimeWarning: All-NaN slice encountered"
            warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
            yBnds = np.isnan([np.nanmin(self.curData[1]), np.nanmax(self.curData[1])])
        if not yBnds[0] and not yBnds[1]:   #Technically it's always only False/False or True/True? Doesn't really matter...
            self.ax.set_ylim(yBnds)

        if not replot:
            self.ax.axis(extent)
        self.fig.canvas.draw()
        self.bg = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
        self._reset_cursors()
        self.update_cursors(False)

    def _plot_1D(self, cur_ax, dataX, dataY, clearAxis=True, colour = None):
        if clearAxis:
            cur_ax.clear()
        if colour != None:
            cur_ax.plot(dataX, dataY, color = colour)
        else:
            cur_ax.plot(dataX, dataY)
        # self.bg = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)

    def plot_data_2D(self, dataX, dataY, dataZ):
        #Figure out if the plot is to rescale its extent
        if len(self.curData) < 3:
            replot = True
        else:
            extent = [x for x in self.ax.axis()]
            xlimts = self.ax.get_xlim()
            xpct = (extent[1] - extent[0])/(np.max(self.curData[0]) - np.min(self.curData[0]))
            ylimts = self.ax.get_ylim()
            ypct = (extent[3] - extent[2])/(np.max(self.curData[1]) - np.min(self.curData[1]))
            replot =  xpct > 0.99 and ypct > 0.99

        self.curData = (dataX, dataY, dataZ)
        self._cur_2D = True
        self._plot_2D(replot)

    def set_colour_key(self, new_col_key, hist_eq_enabled):
        self._cur_col_key = new_col_key
        self.hist_eq_enabled = hist_eq_enabled
        self._plot_2D()

    def reset_plot(self):
        if self._cur_2D:
            extent = (np.nanmin(self.curData[0]), np.nanmax(self.curData[0]), np.nanmin(self.curData[1]), np.nanmax(self.curData[1]))
            self.ax.axis(extent)
            #Need the plot_2D here as the restore_region doesn't account for the new extent and won't refresh the pcolor until the next plot update...
            self._plot_2D()
        else:
            extent = (np.nanmin(self.curData[0]), np.nanmax(self.curData[0]), np.nanmin(self.curData[1]), np.nanmax(self.curData[1]))
            self.ax.axis(extent)
            #Need the plot_2D here as the restore_region doesn't account for the new extent and won't refresh the pcolor until the next plot update...
            self.plot_data_1D(self.curData[0], self.curData[1])

    def _plot_2D(self, replot = False):
        if self._cur_2D:
            if not replot:
                extent = [x for x in self.ax.axis()]
                a = min(self.curData[0])
                if extent[0] < a: extent[0] = a
                a = max(self.curData[0])
                if extent[1] > a: extent[1] = a
                a = min(self.curData[1])
                if extent[2] < a: extent[2] = a
                a = max(self.curData[1])
                if extent[3] > a: extent[3] = a
            
            self.ax.clear()
            self.ax_cB.clear()

            if self.hist_eq_enabled:
                if self.hist_eq != None:
                    del self.hist_eq
                self.hist_eq = HistEqNormalize(self.curData[2])
                self.ax.pcolor(self.curData[0], self.curData[1], self.curData[2], norm=self.hist_eq, shading='nearest', cmap=self._cur_col_key.CMap)
                #Good reference: https://stackoverflow.com/questions/30608731/how-to-add-colorbar-to-a-histogram
                if isinstance(self._cur_col_key.CMap, str):
                    cmap = matplotlib.pyplot.cm.get_cmap(self._cur_col_key.CMap)
                else:
                    cmap = self._cur_col_key.CMap
                matplotlib.colorbar.ColorbarBase(self.ax_cB, cmap=cmap, norm=self.hist_eq, orientation='horizontal')
                self.ax_cB.xaxis.set_ticks_position('top')
            else:
                self.ax.pcolor(self.curData[0], self.curData[1], self.curData[2], shading='nearest', cmap=self._cur_col_key.CMap)
                norm=matplotlib.colors.Normalize(vmin=np.nanmin(self.curData[2]), vmax=np.nanmax(self.curData[2]))
                if isinstance(self._cur_col_key.CMap, str):
                    cmap = matplotlib.pyplot.cm.get_cmap(self._cur_col_key.CMap)
                else:
                    cmap = self._cur_col_key.CMap
                matplotlib.colorbar.ColorbarBase(self.ax_cB, cmap=cmap, norm=norm, orientation='horizontal')
                self.ax_cB.xaxis.set_ticks_position('top')

            if not replot:
                self.ax.axis(extent)
            self.fig.canvas.draw()
            self.bg = self.ax.figure.canvas.copy_from_bbox(self.ax.bbox)
            self._reset_cursors()
            self.update_cursors(False)

    def get_data_limits(self):
        if len(self.curData) > 1:
            #Note that the y-axes can be multi-dimensional if it has switched from 1D/2D plotting, but it's usually transient and doesn't matter for cursors (so np.max/np.min is fine...)
            with warnings.catch_warnings(): #To suppress: "RuntimeWarning: All-NaN slice encountered"
                warnings.filterwarnings('ignore', r'All-NaN (slice|axis) encountered')
                ret_val = [np.min(self.curData[0]), np.max(self.curData[0]), np.nanmin(self.curData[1]), np.nanmax(self.curData[1])]
            if np.isnan(ret_val[2]) or np.isnan(ret_val[3]):    #Should be NaN on both cases, but just use 'or' for now...
                ret_val[2] = 0
                ret_val[3] = 0
            return ret_val
        else:
            return (0,1,0,1)

    def _reset_cursors(self):
        for cur_curse in self.Cursors:
            cur_curse.update()
        for cur_curse in self.AnalysisCursors:
            cur_curse.reset_cursor()

    def update_cursors(self, reset_plots=True):
        for cur_curse in self.Cursors:
            cur_curse.update()
        #Check if a cursor has moved...
        if reset_plots:
            #If lstbx_cursor_info is None, then it's an internal call to redraw the cursors (e.g. new plot, zoom or home-button has been hit)
            no_changes = True
            for cur_curse in self.Cursors:
                if cur_curse.has_changed:
                    no_changes = False
                    break
            for cur_curse in self.AnalysisCursors:
                if cur_curse.has_changed:
                    no_changes = False
                    break
            if no_changes:
                #Basically plot in the next frame that's free without any cursor changes...
                if self._replot_cuts:
                    clear_first_plot = True
                    for cur_curse in self.Cursors:
                        if len(self.curData) < 3:
                            return np.array([])
                        else:
                            cutX = int((np.abs(self.curData[0] - cur_curse.cur_coord[0])).argmin())
                            cutY = int((np.abs(self.curData[1] - cur_curse.cur_coord[1])).argmin())
                            xlimts = self.ax.get_xlim()
                            ylimts = self.ax.get_ylim()
                            self._plot_1D(self.ax_sX, self.curData[0], self.curData[2][cutY,:], clear_first_plot, cur_curse.colour)
                            self._plot_1D(self.ax_sY, self.curData[2][:,cutX], self.curData[1], clear_first_plot, cur_curse.colour)
                            self.ax_sX.set_xlim(*xlimts)
                            self.ax_sY.set_ylim(*ylimts)
                            clear_first_plot = False
                    self._replot_cuts = False
                return
        else:
            self._replot_cuts = True
        
        #Plot each cursor's cut...
        clear_first_plot = True
        #Reset plot background
        self.ax.figure.canvas.restore_region(self.bg)
        #Main cursors
        for cur_curse in self.Cursors:
            #Update main plot
            self.ax.draw_artist(cur_curse.lx)
            self.ax.draw_artist(cur_curse.ly)
            clear_first_plot = False
            cur_curse.has_changed = False
        #Analysis cursors
        changes = False
        for cur_curse in self.AnalysisCursors:
            if cur_curse.has_changed:
                changes = True
            cur_curse.has_changed = False
            if cur_curse.Visible:
                cur_curse.render_blit()
        self.ax.figure.canvas.blit(self.ax.bbox)
        return changes

    def event_mouse_pressed(self, event):
        #Pick first cursor that can be picked by the mouse if applicable
        for cur_curse in self.Cursors:
            cur_curse.event_mouse_pressed(event)
            if cur_curse._is_drag != 'None':
                return
        #Check analysis cursors too:
        for cur_curse in self.AnalysisCursors:
            cur_curse.event_mouse_pressed(event)
            if cur_curse.Dragging:
                return

class PlotCursorDrag(object):
    def __init__(self, pltFrame, colour):
        #Inspired by: https://stackoverflow.com/questions/35414003/python-how-can-i-display-cursor-on-all-axes-vertically-but-only-on-horizontall
        self.ax = pltFrame.ax
        self.pltFrame = pltFrame
        
        self.colour = colour
        
        lims = self.pltFrame.get_data_limits()
        xlimts = lims[0:2]
        ylimts = lims[2:4]
        #Note that the xmin/ymin/xmax/ymax are normalized coordinates (0 to 1 across the axes...)
        self.lx = self.ax.axvline(ymin=0.0,ymax=1.0,color=self.colour)
        self.ly = self.ax.axhline(xmin=0.0,xmax=1.0,color=self.colour)
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
        lims = self.pltFrame.get_data_limits()
        xlimts = lims[0:2]
        ylimts = lims[2:4]

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

class LabelMultiline:
    def __init__(self, parent_ui_element):
        self.Frame = Frame(master=parent_ui_element)
        self.Label = tk.Label(self.Frame, text="Sample Text", anchor="w", justify=LEFT)
        self.Label.pack(side="left", fill="x")
        self.Label.bind('<Configure>', lambda e: self.Label.config(wraplength=self.Frame.winfo_width()))

class MultiColumnListbox(object):
    def __init__(self, parent_ui_element, column_headings, item_updater=None):
        #Inspired by: https://stackoverflow.com/questions/5286093/display-listbox-with-columns-using-tkinter   
        self.tree = None

        self.Frame = ttk.Frame(parent_ui_element)

        #Setup the TreeView and the columns
        self.column_headings = column_headings
        self.tree = ttk.Treeview(columns=self.column_headings, show="headings")

        #Create scrollbars
        vsb = ttk.Scrollbar(orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(column=0, row=0, sticky='nsew', in_=self.Frame)
        vsb.grid(column=1, row=0, sticky='ns', in_=self.Frame)
        hsb.grid(column=0, row=1, sticky='ew', in_=self.Frame)
        self.Frame.grid_columnconfigure(0, weight=1)
        self.Frame.grid_rowconfigure(0, weight=1)

        #Bind the column-sort command and adjust the column's width to the header string
        for col in self.column_headings:
            self.tree.heading(col, text=col, command=lambda c=col: self._sortby(self.tree, c, 0))
            self.tree.column(col, width=tkFont.Font().measure(col))

        self._item_updater = item_updater

    def update_vals(self, update_rows, select_index=-1, update_widths = False):
        self.tree.unbind_all("<ButtonPress-1>")
        self.tree.delete(*self.tree.get_children())
        for row in update_rows:
            item = self.tree.insert('', 'end', values=row[0], tags= (f"i{row}", ))   #Add a unique ID (initial row number on a freshly created list) into the list of tags
            self.tree.tag_bind(f"i{row}", '<ButtonRelease-1>', partial(self._on_click, row[1], item) )    #event
            if update_widths:
                # adjust column's width if necessary to fit each value
                for ix, val in enumerate(row[0]):
                    col_w = tkFont.Font().measure(val)
                    self.tree.column(self.column_headings[ix], width=int(np.ceil(col_w*1.2)))

    def get_sel_val(self, get_index = False):
        if get_index:
            values = [m for m in self.tree.selection()]
        else:
            values = [self.tree.item(m)['values'] for m in self.tree.selection()]
        if len(values) == 0:
            return -1
        else:
            return values[0]

    def del_sel_val(self):
        items = [m for m in self.tree.selection()]
        if len(items) == 0:
            return -1
        values = self.tree.item(items[0])['values']
        self.tree.delete(items[0])
        if len(values) == 0:
            return -1
        else:
            return values

    def _sortby(tree, col, descending):
        """sort tree contents when a column header is clicked on"""
        # grab values to sort
        data = [(tree.set(child, col), child) \
            for child in tree.get_children('')]
        # if the data to be sorted is numeric change to float
        #data =  change_numeric(data)
        # now sort the data in place
        data.sort(reverse=descending)
        for ix, item in enumerate(data):
            tree.move(item[1], '', ix)
        # switch the heading so it will sort in the opposite direction
        tree.heading(col, command=lambda col=col: sortby(tree, col, \
            int(not descending)))

    def _on_click(self, obj, item, event):
        """Handle click on items."""
        if self.tree.identify_row(event.y) == item:
            cur_col_id = self.tree.identify_column(event.x)
            if cur_col_id == '#1':    #First column is the Visible checkbox (they are enumerated as #1, #2 etc...)
                obj.Visible = not obj.Visible   #Hard-coded object toggle...
                if self._item_updater:
                    self.tree.item(item, values=self._item_updater(obj))



