from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtUiTools import QUiLoader
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np
from multiprocessing.pool import ThreadPool
from DataExtractorH5single import DataExtractorH5single
import time
import json

from PostProcessors import*
from functools import partial

from Cursors.Cursor_Cross import Cursor_Cross

class ColourMap:
    def __init__(self):
        pass

    @classmethod
    def fromMatplotlib(cls, cmap_name, display_name):
        retObj = cls()
        retObj._cmap = pg.colormap.getFromMatplotlib(cmap_name)
        retObj._display_name = display_name
        return retObj
    
    @classmethod
    def fromCustom(cls, cm_data, display_name):
        retObj = cls()
        #Assuming uniformly sampled colour maps (i.e. not specifying pos)
        retObj._cmap = pg.ColorMap(pos=None, color=cm_data)
        retObj._display_name = display_name
        return retObj
    
    @property
    def Name(self):
        return self._display_name
    @property
    def CMap(self):
        return self._cmap

class MainWindow:
    def __init__(self, app, win, plot_layout_widget):
        self.plot_layout_widget = plot_layout_widget
        self.win = win
        self.app = app
        self.data_extractor = None

        hour = [1,2,3,4,5,6,7,8,9,10]
        temperature = [30,32,34,32,33,31,29,32,35,45]

        # plot data: x, y values
        self.setup_axes(1)

        self.data_line = self.plt_main.plot(hour, temperature)
        self.plot_type = 1
        self.data_img = None

        self.dep_vars = None

        self.timer = QtCore.QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.update_plot_data)
        self.timer.start()

        win.btn_test.clicked.connect(self.event_btn_OK)

        #Plot Axis Radio Buttons
        self.win.rbtn_plot_1D.toggled.connect(self.event_rbtn_plot_axis)
        self.win.rbtn_plot_2D.toggled.connect(self.event_rbtn_plot_axis)

        #Setup the slicing variables
        self.dict_var_slices = {}   #They values are given as: (currently set slicing index, numpy array of values)
        self.cur_slice_var_keys_lstbx = []
        self.win.lstbx_param_slices.itemSelectionChanged.connect(self._event_slice_var_selection_changed)
        self.win.sldr_param_slices.valueChanged.connect(self._event_sldr_slice_vars_val_changed)

        #Setup available postprocessors
        self.post_procs_all = PostProcessors.get_all_post_processors()
        self.win.lstbx_plot_analy_funcs.addItems(self.post_procs_all.keys())
        self.win.lstbx_plot_analy_funcs.itemSelectionChanged.connect(self._event_lstbxPPfunction_changed)
        self.win.btn_plot_anal_add_func.clicked.connect(self._event_btn_post_proc_add)
        #Currently selected postprocessors
        self.cur_post_procs = []
        self.cur_post_proc_output = "dFinal"
        self.frm_proc_disp_children = []
        self.win.lstbx_cur_post_procs.itemSelectionChanged.connect(self._event_lstbx_proc_current_changed)
        self.win.btn_proc_list_up.clicked.connect(self._event_btn_post_proc_up)
        self.win.btn_proc_list_down.clicked.connect(self._event_btn_post_proc_down)
        self.win.btn_proc_list_del.clicked.connect(self._event_btn_post_proc_delete)
        #Setup current post-processing analysis ListBox and select the first entry (the final output entry)
        self._post_procs_fill_current(0)
        
        #Setup colour maps from Matplotlib
        def_col_maps = [('viridis', "Viridis"), ('afmhot', "AFM Hot"), ('hot', "Hot"), ('gnuplot', "GNU-Plot"), ('coolwarm', "Cool-Warm"), ('seismic', "Seismic"), ('rainbow', "Rainbow")]
        self.colour_maps = []
        for cur_col_map in def_col_maps:
            self.colour_maps.append(ColourMap.fromMatplotlib(cur_col_map[0], cur_col_map[1]))
        #
        file_path = 'ColourMaps/'
        json_files = [pos_json for pos_json in os.listdir(file_path) if pos_json.endswith('.json')]
        for cur_json_file in json_files:
            with open(file_path + cur_json_file) as json_file:
                data = json.load(json_file)
                self.colour_maps.append(ColourMap.fromCustom(np.array(data)*255.0, cur_json_file[:-5]))   #Still specify colour maps from 0 to 1. PyQTgraph just requires it from 0-255
        #Commit colour maps to ComboBox
        self.win.cmbx_ckey.addItems([x.Name for x in self.colour_maps])
        self.win.cmbx_ckey.currentIndexChanged.connect(partial(self._event_cmbx_key_changed) )

        self.analysis_cursors = []

        #Initial update time-stamp
        self.last_update_time = time.time()

    def _event_cmbx_key_changed(self, idx):
        if self.colBarItem != None:
            self.colBarItem.setColorMap(self.colour_maps[self.win.cmbx_ckey.currentIndex()].CMap)

    def clear_plots(self):
        self.plot_layout_widget.clear()
        #
        self.data_line = None
        #
        self.data_img = None
        self.colBarItem = None
        self.plt_curs_x = None
        self.plt_curs_y = None
        self.data_curs_x = None
        self.data_curs_y = None
        #
        self.y_data = None

    def setup_axes(self, plot_dim):
        self.clear_plots()
        if plot_dim == 1:
            self.plt_main = self.plot_layout_widget.addPlot(row=0, col=0)
            self.data_line = self.plt_main.plot([], [])
        else:
            self.plt_main = self.plot_layout_widget.addPlot(row=1, col=1)

            self.plt_curs_x = self.plot_layout_widget.addPlot(row=0, col=1)
            self.data_curs_x = self.plt_curs_x.plot([],[])
            self.plt_curs_x.setXLink(self.plt_main)

            self.plt_curs_y = self.plot_layout_widget.addPlot(row=1, col=0)
            self.data_curs_y = self.plt_curs_y.plot([],[])
            self.plt_curs_y.showAxis('right')
            self.plt_curs_y.hideAxis('left')
            self.plt_curs_y.invertX(True)
            self.plt_curs_y.setYLink(self.plt_main)

            self.data_img = pg.ImageItem()
            self.plt_main.addItem( self.data_img )

            self.cursor = Cursor_Cross(self.plt_main)
            self.plt_main.addItem(self.cursor)
            self.cursor.sigChangedCurX.connect(self.update_cursor_y)
            self.cursor.sigChangedCurY.connect(self.update_cursor_x)
            
            cm = self.colour_maps[self.win.cmbx_ckey.currentIndex()].CMap
            self.colBarItem = pg.ColorBarItem( values= (0, 1), colorMap=cm )
            self.colBarItem.setImageItem( self.data_img, insert_in=self.plt_main )
        self.plot_type = plot_dim

    def event_btn_OK(self):
        print('noice')
        fileName = QtWidgets.QFileDialog.getOpenFileName(self.win, self.app.tr("Open HDF5 File"), "", self.app.tr("HDF5 Files (*.h5)"))
        if fileName[0] != '':
            self.data_thread_pool = ThreadPool(processes=1)
            self.data_extractor = DataExtractorH5single(fileName[0], self.data_thread_pool)
            self.init_ui()

    def trLst(self, lst):
        return [self.app.tr(x) for x in self.indep_vars]

    def init_ui(self):
        self.indep_vars = self.data_extractor.get_independent_vars()
        self.win.cmbx_axis_x.clear()
        self.win.cmbx_axis_x.addItems(self.indep_vars)
        self.win.cmbx_axis_y.clear()
        self.win.cmbx_axis_y.addItems(self.indep_vars)
        self.dep_vars = self.data_extractor.get_dependent_vars()
        self.win.cmbx_dep_var.clear()
        self.win.cmbx_dep_var.addItems(self.dep_vars)

    def event_rbtn_plot_axis(self, value):
        if self.win.rbtn_plot_1D.isChecked():
            self.setup_axes(1)
        else:
            self.setup_axes(2)

    def update_cursor_x(self):
        if not isinstance(self.y_data, np.ndarray):
            return
        #Run the cursors
        cur_x, cur_y = self.cursor.get_value()
        ind = np.argmin(np.abs(cur_y - self.y_data))
        self.data_curs_x.setData(self.x_data, self.z_data[:,ind])

    def update_cursor_y(self):
        if not isinstance(self.y_data, np.ndarray):
            return
        #Run the cursors
        cur_x, cur_y = self.cursor.get_value()
        ind = np.argmin(np.abs(cur_x - self.x_data))
        self.data_curs_y.setData(self.z_data[ind,:], self.y_data)

    def update_plot_data(self):
        if self.data_extractor:
            if self.data_extractor.data_ready():
                (indep_params, final_data, dict_rem_slices) = self.data_extractor.get_data()
                cur_var_ind = self.dep_vars.index(self.win.cmbx_dep_var.currentText())
                if not self.update_plot_post_proc(indep_params, final_data):
                    #Not post-processed (hence not plotted) - so do so now...
                    if self.plot_type == 1 and len(indep_params) == 1:
                        self.data_line.setData(indep_params[0], final_data[cur_var_ind])
                    elif self.plot_type == 2 and len(indep_params) == 2:
                        self.plot_2D(indep_params[0], indep_params[1], final_data[cur_var_ind])
                #   
                #Populate the slice candidates
                #
                cur_lstbx_vals = []
                prev_dict = self.dict_var_slices.copy()
                self.dict_var_slices = {}   #Clear previous dictionary and only leave entries if it had previous slices present...
                #Gather currently selected value so it stays selected
                cur_sel = self.get_listbox_sel_ind(self.win.lstbx_param_slices)
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
                self.listbox_safe_clear(self.win.lstbx_param_slices)
                for ind, cur_val in enumerate(cur_lstbx_vals):
                    cur_item = QtWidgets.QListWidgetItem(cur_val)
                    self.win.lstbx_param_slices.addItem(cur_item)
                    if cur_sel == ind:
                        self.win.lstbx_param_slices.setCurrentItem(cur_item)

            #Setup new request if no new data is being fetched
            if not self.data_extractor.isFetching:
                #Get current update time
                cur_update_time = 1 #self.update_times[self.cmbx_update_rate.get_sel_val(True)]
                cur_elapsed = time.time() - self.last_update_time
                #Request new data if it's time to update (i.e. comparing the time since last update with a non-zero update time)
                if (cur_update_time > 0 and cur_elapsed > cur_update_time): #self.man_update_plot or 
                    xVar = str(self.win.cmbx_axis_x.currentText())
                    slice_vars = {}
                    for cur_var in self.dict_var_slices.keys():
                        slice_vars[cur_var] = self.dict_var_slices[cur_var][0]
                    if self.plot_type == 1:
                        self.data_extractor.fetch_data({'axis_vars':[xVar], 'slice_vars':slice_vars})
                    else:
                        yVar = str(self.win.cmbx_axis_y.currentText())
                        if xVar != yVar:
                            self.data_extractor.fetch_data({'axis_vars':[xVar, yVar], 'slice_vars':slice_vars})

                    self.last_update_time = time.time()

    def listbox_safe_clear(self, listbox):
        for i in range(listbox.count()):
            item = listbox.item(i)
            item.setSelected(False)
        listbox.clear()

    def get_listbox_sel_inds(self, listbox):
        return [x.row() for x in listbox.selectedIndexes()]
    def get_listbox_sel_ind(self, listbox):
        cur_ind = self.get_listbox_sel_inds(listbox)
        if len(cur_ind) == 0:   #i.e. empty
            return -1
        else:
            return cur_ind[0]

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
    def _event_slice_var_selection_changed(self):
        cur_ind = self.get_listbox_sel_ind(self.win.lstbx_param_slices)
        if cur_ind == -1:   #i.e. empty
            return
        cur_slice_var = self.dict_var_slices[self.cur_slice_var_keys_lstbx[cur_ind]]
        self.win.sldr_param_slices.setMinimum(0)
        self.win.sldr_param_slices.setMaximum(cur_slice_var[1].size-1)
        self.win.sldr_param_slices.setValue(cur_slice_var[0])
        self._update_label_slice_var_val(cur_ind)
    def _update_label_slice_var_val(self, var_ind):
        #Update Label (should be safe as the callers have verified that there is a selected index...)
        cur_var_name = self.cur_slice_var_keys_lstbx[var_ind]
        min_val = np.min(self.dict_var_slices[cur_var_name][1])
        max_val = np.max(self.dict_var_slices[cur_var_name][1])
        self.win.lbl_param_slices.setText(f"Range: {min_val}➜{max_val}")
    def _event_sldr_slice_vars_val_changed(self):
        new_index = self.win.sldr_param_slices.value()
        #Calculate the index of the array with the value closest to the proposed value
        cur_sel_ind = self.get_listbox_sel_ind(self.win.lstbx_param_slices)
        if cur_sel_ind == -1:   #i.e. empty
            return
        cur_var_name = self.cur_slice_var_keys_lstbx[cur_sel_ind]
        if new_index != self.dict_var_slices[cur_var_name][0]:
            #Update the array index
            self.dict_var_slices[cur_var_name] = (new_index, self.dict_var_slices[cur_var_name][1])
            #Update ListBox
            item = self.win.lstbx_param_slices.item(cur_sel_ind)
            item.setText(self._slice_Var_disp_text(cur_var_name, self.dict_var_slices[cur_var_name]))
            #Update Label
            self._update_label_slice_var_val(cur_sel_ind)

    
    def _event_lstbxPPfunction_changed(self):
        sel_items = self.win.lstbx_plot_analy_funcs.selectedItems()
        if len(sel_items) == 0:   #i.e. empty - shouldn't happen as it should be safe as it's only populated once; but just in case...
            return
        cur_func = sel_items[0].text()
        self.win.lbl_plot_analy_funcs.setText( "Description: " + self.post_procs_all[cur_func].get_description() )
    def _event_btn_post_proc_add(self):
        sel_items = self.win.lstbx_plot_analy_funcs.selectedItems()
        if len(sel_items) == 0:   #i.e. empty - shouldn't happen as it should be safe as it's only populated once; but just in case...
            return
        cur_func = sel_items[0].text()
        cur_func_obj = self.post_procs_all[cur_func]
        self.cur_post_procs += [{
            'ArgsInput'   : cur_func_obj.get_default_input_args(),
            'ArgsOutput'  : cur_func_obj.get_default_output_args(),
            'ProcessName' : cur_func,
            'ProcessObj'  : cur_func_obj,
            'Enabled'     : True
        }]
        self._post_procs_fill_current(len(self.cur_post_procs)-1)
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

        self.listbox_safe_clear(self.win.lstbx_cur_post_procs)
        self.win.lstbx_cur_post_procs.addItems(cur_proc_strs)
        if sel_index != -1:
            cur_item = self.win.lstbx_cur_post_procs.item(sel_index)
            self.win.lstbx_cur_post_procs.setCurrentItem(cur_item)
    def _event_lstbx_proc_current_changed(self):
        cur_ind = self.get_listbox_sel_ind(self.win.lstbx_cur_post_procs)
        if cur_ind == -1:   #i.e. empty - shouldn't happen as it should be safe as the listbox should be populated with a selected item; but just in case...
            return
        self._post_procs_disp_activate()
        #Disable the movement arrows if selecting an edge
        if cur_ind < len(self.cur_post_procs)-1:
            self.win.btn_proc_list_down.setEnabled(True)
        else:
            self.win.btn_proc_list_down.setEnabled(False)
        if cur_ind == 0 or cur_ind >= len(self.cur_post_procs):
            self.win.btn_proc_list_up.setEnabled(False)
        else:
            self.win.btn_proc_list_up.setEnabled(True)
        #Disable delete button if selecting the final output entry
        if cur_ind == len(self.cur_post_procs):
            self.win.btn_proc_list_del.setEnabled(False)
        else:
            self.win.btn_proc_list_del.setEnabled(True)
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
    def _event_btn_post_proc_up(self):
        cur_ind = self.get_listbox_sel_ind(self.win.lstbx_cur_post_procs)
        if cur_ind == -1:   #i.e. empty - shouldn't happen as it should be safe as the listbox should be populated with a selected item; but just in case...
            return
        if cur_ind > 0 and cur_ind < len(self.cur_post_procs):  #Shouldn't fail as the button should be otherwise disabled (rather redundant check...)
            cur_val = self.cur_post_procs.pop(cur_ind)
            self.cur_post_procs.insert(cur_ind-1, cur_val)
            self._post_procs_fill_current(cur_ind-1)
    def _event_btn_post_proc_down(self):
        cur_ind = self.get_listbox_sel_ind(self.win.lstbx_cur_post_procs)
        if cur_ind == -1:   #i.e. empty - shouldn't happen as it should be safe as the listbox should be populated with a selected item; but just in case...
            return
        if cur_ind < len(self.cur_post_procs)-1:  #Shouldn't fail as the button should be otherwise disabled (rather redundant check...)
            cur_val = self.cur_post_procs.pop(cur_ind)
            self.cur_post_procs.insert(cur_ind+1, cur_val)
            self._post_procs_fill_current(cur_ind+1)
    def _event_btn_post_proc_delete(self):
        cur_ind = self.get_listbox_sel_ind(self.win.lstbx_cur_post_procs)
        if cur_ind == -1:   #i.e. empty - shouldn't happen as it should be safe as the listbox should be populated with a selected item; but just in case...
            return
        if cur_ind < len(self.cur_post_procs):  #Shouldn't fail as the button should be otherwise disabled (rather redundant check...)
            self.cur_post_procs.pop(cur_ind)
            self._post_procs_fill_current(cur_ind)    #Should at worst select the final output entry...
    def _post_procs_disp_activate(self):
        cur_proc_ind = self.get_listbox_sel_ind(self.win.lstbx_cur_post_procs)
        if cur_proc_ind == -1:   #i.e. empty - shouldn't happen as it should be safe as the listbox should be populated with a selected item; but just in case...
            return

        #Clear all widgets
        cur_layout = self.win.lyt_grd_frm_post_proc_details
        cur_frame = self.win.frm_post_procs
        for i in reversed(range(cur_layout.count())): 
            cur_layout.itemAt(i).widget().setParent(None)
        self.frm_proc_disp_children = []
        
        #If selecting the Final Output entry
        row_off = 0
        if cur_proc_ind == len(self.cur_post_procs):
            lbl_procs = QtWidgets.QLabel(cur_frame)
            lbl_procs.setText("Output dataset")
            cur_layout.addWidget(lbl_procs, 0, 0, 1, 1)
            #
            cmbx_proc_output = QtWidgets.QComboBox(cur_frame)
            cmbx_proc_output.currentIndexChanged.connect(partial(self._callback_cmbx_post_procs_disp_final_output_callback, cmbx_proc_output))
            cur_layout.addWidget(cmbx_proc_output, 0, 1, 1, 1)
            #
            possible_inputs = self._get_post_procs_possible_inputs(cur_proc_ind)
            sel_ind = 0
            if len(possible_inputs) > 0 and self.cur_post_proc_output in possible_inputs:
                sel_ind = possible_inputs.index(self.cur_post_proc_output)
            cmbx_proc_output.addItems(possible_inputs)
            cmbx_proc_output.setCurrentIndex(sel_ind)
            #
            self.frm_proc_disp_children += [lbl_procs, cmbx_proc_output]
            return

        #Selected a process in the post-processing chain
        cur_proc = self.cur_post_procs[cur_proc_ind]
        
        row_off = 0
        #
        #Enable checkbox
        lbl_procs = QtWidgets.QLabel(cur_frame)
        lbl_procs.setText("Output dataset")
        cur_layout.addWidget(lbl_procs, row_off, 0, 1, 1)
        chkbx_enabled = QtWidgets.QCheckBox(cur_frame)
        chkbx_enabled.setChecked(cur_proc['Enabled'])
        chkbx_enabled.stateChanged.connect(partial(self._callback_chkbx_post_procs_disp_enabled, cur_proc_ind))
        cur_layout.addWidget(chkbx_enabled, row_off, 1, 1, 1)
        self.frm_proc_disp_children += [lbl_procs, chkbx_enabled]
        row_off += 1
        #
        for ind, cur_arg in enumerate(cur_proc['ProcessObj'].get_input_args()):
            lbl_procs = QtWidgets.QLabel(cur_frame)
            lbl_procs.setText(cur_arg[0])
            cur_layout.addWidget(lbl_procs, row_off, 0, 1, 1)
            self.frm_proc_disp_children += [lbl_procs]
            if cur_arg[1] == 'data':
                cmbx_proc_output = QtWidgets.QComboBox(cur_frame)
                cmbx_proc_output.currentIndexChanged.connect(partial(self._callback_cmbx_post_procs_disp_callback, cur_proc_ind, ind, cmbx_proc_output) )
                cur_layout.addWidget(cmbx_proc_output, row_off, 1, 1, 1)
                self.frm_proc_disp_children += [cmbx_proc_output]
                #
                possible_inputs = self._get_post_procs_possible_inputs(cur_proc_ind)
                sel_ind = 0
                if len(possible_inputs) > 0 and cur_proc['ArgsInput'][ind] in possible_inputs:
                    sel_ind = possible_inputs.index(cur_proc['ArgsInput'][ind])
                cmbx_proc_output.addItems(possible_inputs)
                cmbx_proc_output.setCurrentIndex(sel_ind)
            else:
                #
                # if cur_arg[1] == 'cursor':
                #     cmbx_proc_output = ComboBoxEx(self.frm_proc_disp, "")
                #     cmbx_proc_output.update_vals([x.Name for x in self.plot_main.AnalysisCursors if x.Type == cur_arg[2]])
                #     cmbx_proc_output.Frame.grid(row=row_off, column=1)
                #     self.frm_proc_disp_children.append(cmbx_proc_output.combobox)
                # else:
                tbx_proc_output = QtWidgets.QLineEdit(cur_frame)
                cur_layout.addWidget(tbx_proc_output, row_off, 1, 1, 1)
                tbx_proc_output.setText(str(cur_proc['ArgsInput'][ind]))
                if cur_arg[1] == 'int':
                    tbx_proc_output.setValidator(QtGui.QIntValidator())
                    type_class = int
                elif cur_arg[1] == 'float':
                    tbx_proc_output.setValidator(QtGui.QDoubleValidator())
                    type_class = float
                else:
                    type_class = str
                tbx_proc_output.textChanged.connect(partial(self._callback_tbx_post_procs_disp_callback, cur_proc_ind, ind, type_class) )
                self.frm_proc_disp_children += [tbx_proc_output]
            #
            row_off += 1
        #
        lbl_procs = QtWidgets.QLabel(cur_frame)
        lbl_procs.setText("Outputs:")
        cur_layout.addWidget(lbl_procs, row_off, 0, 1, 1)
        self.frm_proc_disp_children += [lbl_procs]
        row_off += 1
        for ind, cur_arg in enumerate(cur_proc['ProcessObj'].get_output_args()):
            lbl_procs = QtWidgets.QLabel(cur_frame)
            lbl_procs.setText(cur_arg[0])
            cur_layout.addWidget(lbl_procs, row_off, 0, 1, 1)
            #
            tbx_proc_output = QtWidgets.QLineEdit(cur_frame)
            cur_layout.addWidget(tbx_proc_output, row_off, 1, 1, 1)
            tbx_proc_output.setText(str(cur_proc['ArgsOutput'][ind]))
            #These are data/variable names - thus, they require no validation as they are simply strings...
            tbx_proc_output.textChanged.connect(partial(self._callback_tbx_post_procs_disp_outputs_callback, cur_proc_ind, ind) )
            #
            self.frm_proc_disp_children += [lbl_procs, tbx_proc_output]
            row_off += 1
    def _callback_cmbx_post_procs_disp_final_output_callback(self, cmbx, idx):
        self.cur_post_proc_output = str(cmbx.currentText())
        self.win.lstbx_cur_post_procs.item(len(self.cur_post_procs)).setText("Final Output: "+self.cur_post_proc_output)
        return
    def _callback_chkbx_post_procs_disp_enabled(self, sel_index, state):
        self.cur_post_procs[sel_index]['Enabled'] = (state != QtCore.Qt.CheckState.Unchecked)
        self.win.lstbx_cur_post_procs.item(sel_index).setText(self._post_procs_current_disp_text(self.cur_post_procs[sel_index]))
    def _callback_cmbx_post_procs_disp_callback(self, sel_index, arg_index, cmbx, idx):
        self.cur_post_procs[sel_index]['ArgsInput'][arg_index] = str(cmbx.currentText())
        self.win.lstbx_cur_post_procs.item(sel_index).setText(self._post_procs_current_disp_text(self.cur_post_procs[sel_index]))
    def _callback_tbx_post_procs_disp_callback(self, sel_index, arg_index, type_class, the_text):
        #Failed cast (try-except is not working here?!)
        if (type_class == int or type_class == float) and len(the_text) == 1 and (the_text == '-' or the_text == '+'):
            return
        self.cur_post_procs[sel_index]['ArgsInput'][arg_index] = type_class(the_text)
        self.win.lstbx_cur_post_procs.item(sel_index).setText(self._post_procs_current_disp_text(self.cur_post_procs[sel_index]))
    def _callback_tbx_post_procs_disp_outputs_callback(self, sel_index, arg_index, the_text):
        self.cur_post_procs[sel_index]['ArgsOutput'][arg_index] = the_text
        self.win.lstbx_cur_post_procs.item(sel_index).setText(self._post_procs_current_disp_text(self.cur_post_procs[sel_index]))
        return True
    
    def write_statusbar(self, msg):
        self.win.statusbar.showMessage(msg)

    def update_plot_post_proc(self, indep_params, dep_params):
        if len(self.cur_post_procs) == 0:
            self.write_statusbar(f"Add functions to activate postprocessing.")
            return False

        #Drop the update if there are non-1D commands enabled...
        if len(indep_params) == 1:
            for ind, cur_proc in enumerate(self.cur_post_procs):
                if not cur_proc['ProcessObj'].supports_1D() and cur_proc['Enabled']:
                    self.write_statusbar(f"A non-1D plot process has been enabled in step #{ind}.")
                    return False

        #Data declarations
        data = {}
        for ind, cur_dep_var in enumerate(self.dep_vars):
            if len(indep_params) == 1:
                data[cur_dep_var] = {'x': indep_params[0], 'data': dep_params[ind]}
            else:
                data[cur_dep_var] = {'x': indep_params[0], 'y': indep_params[1], 'data': dep_params[ind].T}    #Transposed due to pcolor's indexing requirements...

        #Available analysis cursors
        cur_analy_curs_names = [x.Name for x in self.analysis_cursors]

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
                        self.write_statusbar(f"Dataset \'{cur_args[ind]}\' does not exist in step #{cur_proc_ind+1}")
                        return False
                elif cur_arg[1] == 'cursor':
                    the_cursor = None
                    #Find cursor
                    for cur_curse in self.analysis_cursors:
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
                        self.write_statusbar(f"Cursor \'{cur_args[ind]}\' is not a valid analysis cursor in step #{cur_proc_ind+1}")
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
            self.write_statusbar(f"Dataset \'{self.cur_post_proc_output}\' does not exist")   #It's the final entry - if it doesn't exist yet, it doesn't exist...
            return False

        #No errors - so reset the message...
        self.write_statusbar("")

        #Update plots
        if 'data' in cur_data:  #Occurs when the dataset is empty...
            if 'y' in cur_data:
                self.plot_2D(cur_data['x'], cur_data['y'], cur_data['data'].T)
            else:
                self.data_line.setData(cur_data['x'], cur_data['data'])
        return True
    
    def plot_2D(self, x, y, z):
        dx = (x[-1]-x[0])/(x.size-1)
        dy = (y[-1]-y[0])/(y.size-1)
        xMin = x[0] - dx*0.5
        xMax = x[-1] + dx*0.5
        yMin = y[0] - dy*0.5
        yMax = y[-1] + dy*0.5
        #
        self.x_data = x
        self.y_data = y
        self.z_data = z
        self.data_img.setImage(self.z_data)
        self.data_img.setRect(QtCore.QRectF(xMin, yMin, xMax-xMin, yMax-yMin))
        self.colBarItem.setLevels((self.z_data.min(), self.z_data.max()))


class UiLoader(QUiLoader):
    def createWidget(self, className, parent=None, name=""):
        if className == "GraphicsLayoutWidget":
            self.plot_layout_widget = pg.GraphicsLayoutWidget(parent=parent)
            return self.plot_layout_widget
        return super().createWidget(className, parent, name)

def mainwindow_setup(w):
    w.setWindowTitle("MainWindow Title")

def main():
    loader = UiLoader()
    app = QtWidgets.QApplication(sys.argv)
    window = loader.load("main.ui", None)
    main_win = MainWindow(app, window, loader.plot_layout_widget)
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
