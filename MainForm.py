import tkinter as tk
from tkinter import*
from tkinter import ttk
import tkinter.font as tkFont
from tkinter.scrolledtext import ScrolledText

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.
from matplotlib.backend_bases import (key_press_handler, MouseButton)
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
from matplotlib.colors import LinearSegmentedColormap

import numpy as np
from multiprocessing.pool import ThreadPool

from DataExtractorH5single import*

from PostProcessors import*
from Analysis_Cursors import*

from functools import partial

class MainForm:
    def __init__(self):
        self.root = tk.Tk()
        self.root.wm_title("SQDviz - Data visualisation tool")

        self.pw_main_LR_UI = PanedWindow(orient =tk.HORIZONTAL, master=self.root, sashwidth=3, bg = "#000077", bd = 0)
        self.frame_LHS = Frame(master=self.pw_main_LR_UI)
        self.frame_RHS = Frame(master=self.pw_main_LR_UI)
        self.pw_main_LR_UI.add(self.frame_LHS,stretch='always')
        self.pw_main_LR_UI.add(self.frame_RHS,stretch='always')
        self.pw_main_LR_UI.pack(fill=BOTH, expand=1)

        ###################
        #    LHS FRAME
        ###################
        #
        #
        ###################
        #MAIN PLOT DISPLAY#
        ###################
        # self.pw_plots_main = PanedWindow(orient =tk.VERTICAL, master=self.frame_LHS, sashwidth=3, bg = "#000077", bd = 0)
        self.plot_main = PlotFrame(self.frame_LHS)
        # self.pw_plots_main.add(self.plot_main.Frame,stretch='always')
        # self.plot_slice = PlotFrame(self.pw_plots_main)
        # self.pw_plots_main.add(self.plot_slice.Frame)
        #
        self.plot_main.Frame.grid(row=0,column=0,sticky='nsew')
        ###################
        #
        #
        #########################
        #PLOT SELECTION CONTROLS#
        #########################
        #
        #Overall frame broken up into columns containing individual frames...
        frame_cursors_all = Frame(master=self.frame_LHS)#, text = "Plot Parameters")
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
        tk.Button(master=self.frame_cursors, text ="Add cursor", command = lambda: self.plot_main.add_cursor()).grid(row=1, column=0)
        tk.Button(master=self.frame_cursors, text ="Delete cursor", command = lambda: self.plot_main.Cursors.pop(self.lstbx_cursors.get_sel_val(True))).grid(row=1, column=1)
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
        self.lstbx_analy_cursors = MultiColumnListbox(self.frame_analy_cursors, [" ", "  ", "Name", "Type", "Notes"])
        self.lstbx_analy_cursors.Frame.grid(row=0, column=0, padx=10, pady=2, columnspan=3, sticky="news")
        ################
        #
        ####################
        #ADD/REMOVE BUTTONS#
        self.cmbx_anal_cursors = ComboBoxEx(self.frame_analy_cursors, "")
        self.cmbx_anal_cursors.Frame.grid(row=1, column=0)
        tk.Button(master=self.frame_analy_cursors, text ="Add cursor", command = self._event_btn_anal_cursor_add).grid(row=1, column=1)
        tk.Button(master=self.frame_analy_cursors, text ="Delete").grid(row=1, column=2)
        ####################
        #
        self.frame_analy_cursors.rowconfigure(0, weight=1)
        self.frame_analy_cursors.rowconfigure(1, weight=0)
        self.frame_analy_cursors.columnconfigure(0, weight=1)
        self.frame_analy_cursors.grid(row=0, column=1, sticky='news')
        #########################
        #
        #
        frame_cursors_all.grid(row=1,column=0,sticky='news')
        frame_cursors_all.columnconfigure(0, weight=1)
        frame_cursors_all.columnconfigure(1, weight=1)
        frame_cursors_all.rowconfigure(0, weight=1)
        #
        self.frame_LHS.rowconfigure(0, weight=1)
        self.frame_LHS.rowconfigure(1, weight=0)
        self.frame_LHS.columnconfigure(0, weight=1)
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
        self.plot_dim_type.set(1)
        lblfrm_axis_sel = LabelFrame(master=lblfrm_plot_params, text="Plot Axes", padx=10, pady=2)
        tk.Radiobutton(lblfrm_axis_sel, text="1D Plot", padx = 20, variable=self.plot_dim_type, value=1, command=self._event_plotsel_changed).grid(row=0, column=0)
        tk.Radiobutton(lblfrm_axis_sel, text="2D Plot", padx = 20, variable=self.plot_dim_type, value=2, command=self._event_plotsel_changed).grid(row=1, column=0)
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
        self.chkbx_hist_eq = tk.Checkbutton(lblfrm_plot_params, text = "Histogram equalisation")
        self.chkbx_hist_eq.grid(row=5, column=0, sticky='se', pady=2)
        #
        for m in range(6):
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
        self.lstbx_slice_vars.frame.grid(row=0, column=0, columnspan=3, padx=10, pady=2, sticky="news")
        #
        self.lbl_slice_vars_val = tk.Label(lblfrm_slice_vars, text="Min|Max:")
        self.lbl_slice_vars_val.grid(row=1, column=0, columnspan=3)
        #
        self.sldr_slice_vars_val = ttk.Scale(lblfrm_slice_vars, from_=0, to=1, orient='horizontal', command=self._event_sldr_slice_vars_val_changed)
        self.sldr_slice_vars_val.grid(row=2, column=0, sticky='sew')
        self.btn_slice_vars_val_inc = tk.Button(lblfrm_slice_vars, text="❰", command=self._event_btn_slice_vars_val_dec)
        self.btn_slice_vars_val_dec = tk.Button(lblfrm_slice_vars, text="❱", command=self._event_btn_slice_vars_val_inc)
        self.btn_slice_vars_val_inc.grid(row=2,column=1)
        self.btn_slice_vars_val_dec.grid(row=2,column=2)
        #
        lblfrm_slice_vars.columnconfigure(0, weight=1)
        lblfrm_slice_vars.columnconfigure(1, weight=0)
        lblfrm_slice_vars.columnconfigure(2, weight=0)
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
        frm_proc_sel.grid(row=0, column=0, sticky='ew')
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
        self.frm_proc_disp.grid(row=0, column=1, padx=10, pady=2, sticky="news")
        self.frm_proc_disp_children = []    #Tkinter's frame children enumeration is a bit strange...
        #
        #
        frm_proc_construction.rowconfigure(0, weight=1)
        frm_proc_construction.columnconfigure(0, weight=1)
        frm_proc_construction.columnconfigure(1, weight=0)
        frm_proc_construction.grid(row=1, column=0, sticky='ew')
        #
        #Output Textbox and update button
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
        #Commit colour maps to ComboBox
        self.cmbx_ckey.update_vals([x.Name for x in self.colour_maps])
        self.plot_main.set_colour_key(self.colour_maps[self.cmbx_ckey.get_sel_val(True)])

        self.plot_main.Canvas.mpl_connect("key_press_event", self._event_form_on_key_press)
        self.plot_main.add_cursor('red')

        #Setup data extraction
        self.data_thread_pool = ThreadPool(processes=1)
        self.data_extractor = DataExtractorH5single("swmr.h5", self.data_thread_pool)
        #
        self.indep_vars = self.data_extractor.get_independent_vars()
        self.cmbx_axis_x.update_vals(self.indep_vars)
        self.cmbx_axis_y.update_vals(self.indep_vars)
        self.dep_vars = self.data_extractor.get_dependent_vars()
        self.cmbx_dep_var.update_vals(self.dep_vars)

        #Setup analysis cursors
        #Setup a dictionary which maps the cursor name to the cursor prefix...
        self.possible_cursors = {
            'X-Region' : 'X',
            'Y-Region' : 'Y'
        }        
        self.cmbx_anal_cursors.update_vals(self.possible_cursors.keys())
        self._analysis_cursors = []
        self._update_analy_cursor_table_widths = False

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

    def main_loop(self):
        while True:
            if self.data_extractor.data_ready():
                (indep_params, final_data, dict_rem_slices) = self.data_extractor.get_data()
                cur_var_ind = self.dep_vars.index(self.cmbx_dep_var.get_sel_val())
                if len(indep_params) == 1:
                    self.plot_main.plot_data_1D(indep_params[0], final_data[cur_var_ind])
                    self.update_plot_post_proc()
                else:
                    self.plot_main.plot_data_2D(indep_params[0], indep_params[1], final_data[cur_var_ind].T)    #Transposed due to pcolor's indexing requirements...
                    self.update_plot_post_proc()
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

            self.plot_main.pop_plots_with_cursor_cuts(self.lstbx_cursors)
            self.plot_main.Canvas.draw()
            #Analysis cursor update
            cur_anal_cursor_table = []
            for cur_curse in self._analysis_cursors:
                if cur_curse.Visible:
                    cur_sh_icon = "👁"
                else:
                    cur_sh_icon = "⊘"
                cur_anal_cursor_table += [( cur_sh_icon, 'o', cur_curse.Name, cur_curse.Type, cur_curse.Summary )]
            self.lstbx_analy_cursors.update_vals(cur_anal_cursor_table, update_widths = self._update_analy_cursor_table_widths)
            self._update_analy_cursor_table_widths = False

            #Setup new request if no new data is being fetched
            if not self.data_extractor.isFetching:
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

    def _event_btn_anal_cursor_add(self):
        self._update_analy_cursor_table_widths = True
        cur_sel = self.cmbx_anal_cursors.get_sel_val()

        #Find previous names
        prev_names = []
        for cur_curse in self._analysis_cursors:
            if cur_curse.Type == cur_sel:
                prev_names += [cur_curse.Name]
        #Choose new name
        new_prefix = self.possible_cursors[cur_sel]
        m = 0
        while f'{new_prefix}{m}' in prev_names:
            m += 1
        new_name = f'{new_prefix}{m}'

        if cur_sel == 'X-Region':
            self._analysis_cursors += [AC_Xregion(new_name)]

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
        cur_var_name = self.cur_slice_var_keys_lstbx[self.lstbx_slice_vars.get_sel_val(True)]
        cur_len = self.dict_var_slices[cur_var_name][1].size
        cur_ind = int(float(self.sldr_slice_vars_val.get()))
        if cur_ind + 1 < cur_len:
            self.sldr_slice_vars_val.set(cur_ind + 1)
    def _event_btn_slice_vars_val_dec(self):
        cur_var_name = self.cur_slice_var_keys_lstbx[self.lstbx_slice_vars.get_sel_val(True)]
        cur_ind = int(float(self.sldr_slice_vars_val.get()))
        if cur_ind > 0:
            self.sldr_slice_vars_val.set(cur_ind - 1)
    def _event_sldr_slice_vars_val_changed(self, value):
        self._slice_vars_set_val(int(float(value)))
    def _slice_vars_set_val(self, new_index):
        #Calculate the index of the array with the value closest to the proposed value
        cur_var_name = self.cur_slice_var_keys_lstbx[self.lstbx_slice_vars.get_sel_val(True)]
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
        self.plot_main.set_colour_key(self.colour_maps[self.cmbx_ckey.get_sel_val(True)])

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
    def _callback_tbx_post_procs_disp_outputs_callback(self, cur_proc, arg_index, strVal):
        cur_proc['ArgsOutput'][arg_index] = strVal
        self.lstbx_procs_current.modify_selected_index(self._post_procs_current_disp_text(cur_proc))
        return True
    def _callback_tbx_post_procs_disp_final_output_callback(self, strVal):
        self.cur_post_proc_output = strVal
        self.lstbx_procs_current.modify_selected_index("Final Output: "+self.cur_post_proc_output)
        return True
    def _callback_chkbx_post_procs_disp_enabled(self, cur_proc):
        cur_proc['Enabled'] = self.post_procs_enabled_chkbx_var.get()
        self.lstbx_procs_current.modify_selected_index(self._post_procs_current_disp_text(cur_proc))
    def _post_procs_disp_activate(self):
        cur_ind = self.lstbx_procs_current.get_sel_val(True)

        tbx_width = 9

        #Selected the Final Output entry
        row_off = 0
        if cur_ind == len(self.cur_post_procs):
            lbl_procs = Label(self.frm_proc_disp, text = "Output dataset")
            lbl_procs.grid(row=row_off, column=0)
            self.frm_proc_disp_children.append(lbl_procs)
            #
            tbx_proc_output = ttk.Entry(self.frm_proc_disp, validate="key", width=tbx_width)  #validate can be validate="focusout" as well
            tbx_proc_output.insert(END, self.cur_post_proc_output)
            tbx_proc_output['validatecommand'] = (tbx_proc_output.register( partial(self._callback_tbx_post_procs_disp_final_output_callback) ), "%P")
            tbx_proc_output.grid(row=row_off, column=1)
            self.frm_proc_disp_children.append(tbx_proc_output)
            return

        #Selected a process in the post-processing chain
        cur_proc = self.cur_post_procs[cur_ind]
        
        row_off = 0
        chkbx_enabled = Checkbutton(self.frm_proc_disp, text = "Enabled", variable=self.post_procs_enabled_chkbx_var, command=partial(self._callback_chkbx_post_procs_disp_enabled, cur_proc))
        self.post_procs_enabled_chkbx_var.set(cur_proc['Enabled'])
        chkbx_enabled.grid(row=row_off, column=0)
        self.frm_proc_disp_children.append(chkbx_enabled)
        row_off += 1
        #
        for ind, cur_arg in enumerate(cur_proc['ProcessObj'].get_input_args()):
            lbl_procs = Label(self.frm_proc_disp, text = cur_arg[0])
            lbl_procs.grid(row=row_off, column=0)
            self.frm_proc_disp_children.append(lbl_procs)
            #
            tbx_proc_output = ttk.Entry(self.frm_proc_disp, validate="key", width=tbx_width)  #validate can be validate="focusout" as well
            tbx_proc_output.insert(END, cur_proc['ArgsInput'][ind])
            if cur_arg[1] == 'int':
                tbx_proc_output['validatecommand'] = (tbx_proc_output.register( partial(self._callback_tbx_post_procs_disp_callback_Int, cur_proc, ind) ), "%P")
            else:
                tbx_proc_output['validatecommand'] = (tbx_proc_output.register( partial(self._callback_tbx_post_procs_disp_callback, cur_proc, ind) ), "%P")
            tbx_proc_output.grid(row=row_off, column=1)
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
            tbx_proc_output = ttk.Entry(self.frm_proc_disp, validate="key", width=tbx_width)  #validate can be validate="focusout" as well
            tbx_proc_output.insert(END, cur_proc['ArgsOutput'][ind])
            #These are data/variable names - thus, they require no validation as they are simply strings...
            tbx_proc_output['validatecommand'] = (tbx_proc_output.register( partial(self._callback_tbx_post_procs_disp_outputs_callback, cur_proc, ind) ), "%P")
            tbx_proc_output.grid(row=row_off, column=1)
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

    def _open_file():
        # file type
        filetypes = (
            ('HDF5', '*.h5'),
            ('TSV Data Files', '*.dat')
            #('All files', '*.*')
        )
        # show the open file dialog
        f = fd.askopenfile(filetypes=filetypes)
        # read the text file and show its content on the Text
        text.insert('1.0', f.readlines())

    def _event_btn_PPupdate_plot(self):
        self.cmds_to_execute = ""
        #Function declarations
        for cur_key in self.post_procs_all.keys():
            self.cmds_to_execute += f'{cur_key} = self.post_procs_all[\'{cur_key}\']\n'
        #Compile post-processing commands
        self.cmds_to_execute += self.tbx_proc_code.get("1.0", tk.END) + '\n'
        cur_output_var = self.tbx_proc_output.get()
        self.cmds_to_execute += f'global cur_data; cur_data={cur_output_var}'

    def update_plot_post_proc(self):
        if len(self.cur_post_procs) == 0:
            self.lbl_procs_errors['text'] = f"Add functions to activate postprocessing."
            return

        #Data declarations
        data = {}
        for cur_dep_var in self.dep_vars:
            if len(self.plot_main.curData) == 2:
                data[cur_dep_var] = {'x': self.plot_main.curData[0], 'data': self.plot_main.curData[1]}
            else:
                data[cur_dep_var] = {'x': self.plot_main.curData[0], 'y': self.plot_main.curData[1], 'data': self.plot_main.curData[2]}

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
                        return
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
            return

        #No errors - so reset the message...
        self.lbl_procs_errors['text'] = ""

        #Update plots
        if len(self.plot_main.curData) == 2:
            self.plot_main.plot_data_1D(cur_data['x'], cur_data['data'])
        else:
            self.plot_main.plot_data_2D(cur_data['x'], cur_data['y'], cur_data['data'])

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
        #self.ax = self.fig.gca() #fig.add_subplot(111)
        # ax.plot(t, 2 * np.sin(2 * np.pi * t))

        gs = self.fig.add_gridspec(2, 2,  width_ratios=(7, 2), height_ratios=(2, 7),
                      left=0.1, right=0.9, bottom=0.1, top=0.9,
                      wspace=0.05, hspace=0.05)
        self.ax = self.fig.add_subplot(gs[1, 0])
        self.ax_sX = self.fig.add_subplot(gs[0, 0], sharex=self.ax)
        self.ax_sY = self.fig.add_subplot(gs[1, 1], sharey=self.ax)
        self.ax_sX.tick_params(labelbottom=False, bottom=False)
        self.ax_sY.tick_params(labelleft=False, left=False)

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

    def _plot_1D(self, cur_ax, dataX, dataY, clearAxis=True, colour = None):
        if clearAxis:
            cur_ax.clear()
        if colour != None:
            cur_ax.plot(dataX, dataY, color = colour)
        else:
            cur_ax.plot(dataX, dataY)

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

    def pop_plots_with_cursor_cuts(self, lstbx_cursor_info):
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
                self._plot_1D(self.ax_sX, self.curData[0], self.curData[2][cutY,:], clear_first_plot, cur_curse.colour)
                self._plot_1D(self.ax_sY, self.curData[2][:,cutX], self.curData[1], clear_first_plot, cur_curse.colour)
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

class LabelMultiline:
    def __init__(self, parent_ui_element):
        self.Frame = Frame(master=parent_ui_element)
        self.Label = tk.Label(self.Frame, text="Sample Text", anchor="w", justify=LEFT)
        self.Label.pack(side="left", fill="x")
        self.Label.bind('<Configure>', lambda e: self.Label.config(wraplength=self.Frame.winfo_width()))

class MultiColumnListbox(object):
    """use a ttk.TreeView as a multicolumn ListBox"""

    def __init__(self, parent_ui_element, column_headings):
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

    def update_vals(self, update_rows, select_index=-1, update_widths = False):
        self.tree.delete(*self.tree.get_children())
        for item in update_rows:
            self.tree.insert('', 'end', values=item)
            if update_widths:
                # adjust column's width if necessary to fit each value
                for ix, val in enumerate(item):
                    col_w = tkFont.Font().measure(val)
                    self.tree.column(self.column_headings[ix], width=int(np.ceil(col_w*1.2)))
                    # if self.tree.column(self.column_headings[ix],width=None)<col_w:
                    #     self.tree.column(self.column_headings[ix], width=col_w)
                    # if self.tree.column(self.column_headings[ix],width=None)>1.2*col_w:
                    #     self.tree.column(self.column_headings[ix], width=int(np.round(col_w*1.2)))

    def get_sel_val(self, get_index = False):
        if get_index:
            values = [m for m in self.tree.selection()]
        else:
            values = [self.tree.get(m) for m in self.tree.selection()]
        if len(values) == 0:
            return -1
        else:
            return values[0]

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
