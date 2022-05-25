from PySide6 import QtWidgets, QtCore
from PySide6.QtUiTools import QUiLoader
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np
from multiprocessing.pool import ThreadPool
from DataExtractorH5single import DataExtractorH5single
import time

from Cursors.Cursor_Cross import Cursor_Cross

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


        # ... init continued ...
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

        #Initial update time-stamp
        self.last_update_time = time.time()

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
            
            cm = pg.colormap.get('CET-L9') # prepare a linear color map
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
                if self.plot_type == 1 and len(indep_params) == 1:
                    self.data_line.setData(indep_params[0], final_data[cur_var_ind])
                elif self.plot_type == 2 and len(indep_params) == 2:
                    #Assuming a uniformly sampled axis, calculate bounds
                    x,y = indep_params[0], indep_params[1]
                    dx = (x[-1]-x[0])/(x.size-1)
                    dy = (y[-1]-y[0])/(y.size-1)
                    xMin = x[0] - dx*0.5
                    xMax = x[-1] + dx*0.5
                    yMin = y[0] - dy*0.5
                    yMax = y[-1] + dy*0.5
                    #
                    self.x_data = x
                    self.y_data = y
                    self.z_data = final_data[cur_var_ind]
                    self.data_img.setImage(self.z_data)
                    self.data_img.setRect(QtCore.QRectF(xMin, yMin, xMax-xMin, yMax-yMin))
                    
                    self.colBarItem.setLevels((self.z_data.min(), self.z_data.max()))

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
