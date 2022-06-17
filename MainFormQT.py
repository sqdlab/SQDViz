from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtUiTools import QUiLoader
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np
from multiprocessing.pool import ThreadPool
from DataExtractors.DataExtractorH5single import DataExtractorH5single
from DataExtractors.DataExtractorH5multiple import DataExtractorH5multiple
from DataExtractors.DataExtractorUQtoolsDAT import DataExtractorUQtoolsDAT
import time
import json
import Icons
import pyqtgraph.exporters as pgExp

from PostProcessors import*
from functools import partial

from Cursors.Cursor_Cross import Cursor_Cross
from Cursors.Analy_Cursors import*

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

        self.analysis_cursors = []
        self.cursors = []   #Holds: (latest x value, latest y value, colour as a 3-vector RGB or character, Cursor_Cross object)
        self.win.btn_cursor_add.clicked.connect(self._event_btn_cursor_add)
        self.win.btn_cursor_del.clicked.connect(self._event_btn_cursor_del)
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

        self.file_path = ""
        self.data_thread_pool = None
        self.default_win_title = self.win.windowTitle()
        win.actionFopenH5.triggered.connect(self._event_btn_open_H5)
        win.actionFopenH5dir.triggered.connect(self._event_btn_open_H5dir)
        win.actionFopenDat.triggered.connect(self._event_btn_open_DAT)
        win.actionresetCursor.triggered.connect(self._event_btn_cursor_reset)
        win.actiongetFileAttributes.triggered.connect(self._event_btn_get_attrs)
        win.actiongetFileFigure.triggered.connect(self._event_btn_get_fig)
        win.actiongotoFilePrev.triggered.connect(self._open_file_prev)
        win.actiongotoFileNext.triggered.connect(self._open_file_next)

        #Plot Axis Radio Buttons
        self.win.rbtn_plot_1D.toggled.connect(self.event_rbtn_plot_axis)
        self.win.rbtn_plot_2D.toggled.connect(self.event_rbtn_plot_axis)

        #Setup the slicing variables
        self.dict_var_slices = {}   #They values are given as: (currently set slicing index, numpy array of values)
        self.cur_slice_var_keys_lstbx = []
        self.win.lstbx_param_slices.itemSelectionChanged.connect(self._event_slice_var_selection_changed)
        self.win.sldr_param_slices.valueChanged.connect(self._event_sldr_slice_vars_val_changed)
        self.win.btn_slice_vars_val_inc.clicked.connect(self._event_btn_slice_vars_val_inc)
        self.win.btn_slice_vars_val_dec.clicked.connect(self._event_btn_slice_vars_val_dec)

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

        win.btn_proc_list_open.clicked.connect(self._event_btn_proc_list_open)
        win.btn_proc_list_save.clicked.connect(self._event_btn_proc_list_save)
        self._post_procs_update_configs_from_file()
        
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

        #Hide the differential cursors...
        self.win.tbl_cursor_diffs.setVisible(False)
        self.win.tbl_cursor_diffs.setColumnCount(6)
        self.win.tbl_cursor_diffs.setHorizontalHeaderLabels(["", "", "Δx", "Δy", "1/Δx", "1/Δy"])
        headerView = self.win.tbl_cursor_diffs.horizontalHeader()
        headerView.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        headerView.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        headerView.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        headerView.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
        headerView.setSectionResizeMode(4, QtWidgets.QHeaderView.ResizeToContents)
        headerView.setSectionResizeMode(5, QtWidgets.QHeaderView.ResizeToContents)

        #Setup analysis cursors
        #Setup a dictionary which maps the cursor name to the cursor class...
        self.possible_cursors = Analy_Cursor.get_all_analysis_cursors()
        self.win.cmbx_anal_cursors.addItems(self.possible_cursors.keys())
        self.win.btn_analy_cursor_add.clicked.connect(self._event_btn_anal_cursor_add)
        self.win.btn_analy_cursor_del.clicked.connect(self._event_btn_anal_cursor_del)
        #
        self.win.tbl_analy_cursors.setColumnCount(4)
        self.win.tbl_analy_cursors.setHorizontalHeaderLabels(["Show", "Name", "Type", "Value"])
        headerView = self.win.tbl_analy_cursors.horizontalHeader()
        headerView.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        headerView.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        headerView.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        headerView.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self._anal_cursor_add_block_event = False
        self.win.tbl_analy_cursors.itemChanged.connect(self._event_chkbx_anal_cursor_show)

        #Initial update time-stamp
        self.last_update_time = time.time()

    def _event_cmbx_key_changed(self, idx):
        if self.colBarItem != None:
            self.colBarItem.setColorMap(self.colour_maps[self.win.cmbx_ckey.currentIndex()].CMap)

    def trLst(self, lst):
        return [self.app.tr(x) for x in self.indep_vars]

    def setup_plot_vars(self):
        self.indep_vars = self.data_extractor.get_independent_vars()
        if self.indep_vars != [self.win.cmbx_axis_x.itemText(x) for x in range(self.win.cmbx_axis_x.count())]:
            cur_sel = self.win.cmbx_axis_x.currentText()
            cur_sel_ind = 0
            if self.win.cmbx_axis_x.currentText() != '' and cur_sel in self.indep_vars:
                cur_sel_ind = self.indep_vars.index(cur_sel)
            self.win.cmbx_axis_x.clear()
            self.win.cmbx_axis_x.addItems(self.indep_vars)
            self.win.cmbx_axis_x.setCurrentIndex(cur_sel_ind)
            #
            cur_sel = self.win.cmbx_axis_y.currentText()
            cur_sel_ind = 0
            if self.win.cmbx_axis_y.currentText() != '' and cur_sel in self.indep_vars:
                cur_sel_ind = self.indep_vars.index(cur_sel)
            self.win.cmbx_axis_y.clear()
            self.win.cmbx_axis_y.addItems(self.indep_vars)
            self.win.cmbx_axis_y.setCurrentIndex(cur_sel_ind)
        self.dep_vars = self.data_extractor.get_dependent_vars()
        if self.dep_vars != [self.win.cmbx_dep_var.itemText(x) for x in range(self.win.cmbx_dep_var.count())]:
            cur_sel = self.win.cmbx_dep_var.currentText()
            cur_sel_ind = 0
            if self.win.cmbx_dep_var.currentText() != '' and cur_sel in self.dep_vars:
                cur_sel_ind = self.dep_vars.index(cur_sel)
            self.win.cmbx_dep_var.clear()
            self.win.cmbx_dep_var.addItems(self.dep_vars)
            self.win.cmbx_dep_var.setCurrentIndex(cur_sel_ind)

    def event_rbtn_plot_axis(self, value):
        if self.win.rbtn_plot_1D.isChecked():
            self.setup_axes(1)
        else:
            self.setup_axes(2)

    def setup_axes(self, plot_dim):
        #Clear plots
        for m in range(len(self.cursors)):
            if self.cursors[m][3] != None:
                # self.cursors[m][3].release_from_plots()
                del self.cursors[m][3]
                self.cursors[m] += [None]
        for cur_anal_curse in self.analysis_cursors:
            cur_anal_curse.release_from_plots()
        self.plot_layout_widget.clear()
        #
        self.data_line = None
        #
        self.plt_main = None
        self.data_img = None
        self.colBarItem = None
        self.plt_curs_x = None
        self.plt_curs_y = None
        self.data_curs_x = []
        self.data_curs_y = []
        self.plt_colhist = None
        self.data_colhist = None
        #
        self.y_data = None

        if plot_dim == 1:
            self.plt_main = self.plot_layout_widget.addPlot(row=0, col=0)
            self.data_line = self.plt_main.plot([], [])
            self.update_all_cursors()
            self.update_all_anal_cursors()
        else:
            self.plt_main = self.plot_layout_widget.addPlot(row=1, col=1)

            self.plt_curs_x = self.plot_layout_widget.addPlot(row=0, col=1)
            self.data_curs_x = [self.plt_curs_x.plot([],[],pen=pg.mkPen(self.cursors[x][2])) for x in range(len(self.cursors))]
            self.plt_curs_x.setXLink(self.plt_main) 

            self.plt_curs_y = self.plot_layout_widget.addPlot(row=1, col=0)
            self.data_curs_y = [self.plt_curs_y.plot([],[],pen=pg.mkPen(self.cursors[x][2])) for x in range(len(self.cursors))]
            self.plt_curs_y.showAxis('right')
            self.plt_curs_y.hideAxis('left')
            self.plt_curs_y.invertX(True)
            self.plt_curs_y.setYLink(self.plt_main)

            self.plt_colhist = self.plot_layout_widget.addPlot(row=0, col=0)
            self.data_colhist = self.plt_colhist.plot([],[])      

            self.data_img = pg.ImageItem()
            self.plt_main.addItem( self.data_img )

            self.update_all_cursors()
            self.update_all_anal_cursors()
            
            cm = self.colour_maps[self.win.cmbx_ckey.currentIndex()].CMap
            self.colBarItem = pg.ColorBarItem( values= (0, 1), colorMap=cm, orientation='horizontal' )
            self.colBarItem.setImageItem( self.data_img, insert_in=self.plt_colhist )

            self.plot_layout_widget.ci.layout.setRowStretchFactor(0, 1)
            self.plot_layout_widget.ci.layout.setRowStretchFactor(1, 4)
            self.plot_layout_widget.ci.layout.setColumnStretchFactor(0, 1)
            self.plot_layout_widget.ci.layout.setColumnStretchFactor(1, 4)
        self.plot_type = plot_dim

    def find_new_colour(self, used_colours):
        col = ''
        col_pool = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
        for cur_cand_col in col_pool:
            if not cur_cand_col in used_colours:
                col = cur_cand_col
                break
        #Just pick random colour if all colours are already taken...
        if col == '':
            import random
            col = col_pool[random.randint(0, len(col_pool)-1)]
        return col
    def get_text_colour(self, col):
        textcol = pg.mkPen(col)
        return QtGui.QColor(textcol.color().red(), textcol.color().green(), textcol.color().blue(), 255)

    def update_cursor_x(self, curse_num, leCursor=None):
        #Run the cursors
        if self.cursors[curse_num][3] == None:
            cur_x, cur_y = self.cursors[curse_num][:2]
        else:
            cur_x, cur_y = self.cursors[curse_num][3].get_value()
        self.cursors[curse_num][1] = cur_y
        self.update_lstbx_cursors()
        if not isinstance(self.y_data, np.ndarray) or len(self.data_curs_x) <= curse_num:
            return
        ind = np.argmin(np.abs(cur_y - self.y_data))
        self.data_curs_x[curse_num].setData(self.x_data, self.z_data[:,ind])
    def update_cursor_y(self, curse_num, leCursor=None):
        #Run the cursors
        if self.cursors[curse_num][3] == None:
            cur_x, cur_y = self.cursors[curse_num][:2]
        else:
            cur_x, cur_y = self.cursors[curse_num][3].get_value()
        self.cursors[curse_num][0] = cur_x
        self.update_lstbx_cursors()
        if not isinstance(self.y_data, np.ndarray) or len(self.data_curs_x) <= curse_num:
            return
        ind = np.argmin(np.abs(cur_x - self.x_data))
        self.data_curs_y[curse_num].setData(self.z_data[ind,:], self.y_data)
    def update_all_cursors(self):
        new_cursors = []
        for m, cur_curse in enumerate(self.cursors):
            new_cursor_obj = Cursor_Cross(cur_curse[0], cur_curse[1], cur_curse[2])  #clear() deletes the C++ object!
            new_cursors += [[cur_curse[0], cur_curse[1], cur_curse[2], new_cursor_obj]]
            new_cursor_obj.connect_plt_to_move_event(self.plt_main)
            self.plt_main.addItem(new_cursor_obj)
            new_cursor_obj.sigChangedCurX.connect(partial(self.update_cursor_y, m))
            new_cursor_obj.sigChangedCurY.connect(partial(self.update_cursor_x, m))
        self.cursors = new_cursors
    def update_lstbx_cursors(self):
        while self.win.lstbx_cursors.count() > len(self.cursors):
            self.win.lstbx_cursors.takeItem(self.win.lstbx_cursors.count()-1)
        while self.win.lstbx_cursors.count() < len(self.cursors):
            self.win.lstbx_cursors.addItem('')
        for m in range(len(self.cursors)):
            cur_x, cur_y, col = self.cursors[m][:3]
            self.win.lstbx_cursors.item(m).setText(f"X: {cur_x}, Y: {cur_y}")
            self.win.lstbx_cursors.item(m).setForeground(QtGui.QBrush(pg.mkBrush(col)))
        #Update differential cursors
        if len(self.cursors) > 1:
            self.win.tbl_cursor_diffs.setVisible(True)

            #Generate combinations to show
            show_combs = []
            for m in range(len(self.cursors)-1):
                for n in range(m+1,len(self.cursors)):
                    show_combs += [(m,n)]

            #Add differences to the table
            cur_table = self.win.tbl_cursor_diffs
            cur_table.setRowCount(len(show_combs))
            for m, cur_comb in enumerate(show_combs):
                textcol = self.get_text_colour(self.cursors[cur_comb[0]][2])
                item = QtWidgets.QTableWidgetItem('■'); item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                item.setForeground(textcol)
                cur_table.setItem(m,0,item)
                #
                textcol = self.get_text_colour(self.cursors[cur_comb[1]][2])
                item = QtWidgets.QTableWidgetItem('■'); item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                item.setForeground(textcol)
                cur_table.setItem(m,1,item)
                #
                dx = self.cursors[cur_comb[0]][0]-self.cursors[cur_comb[1]][0]
                item = QtWidgets.QTableWidgetItem(f'{dx}')
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                cur_table.setItem(m,2,item)
                #
                dy = self.cursors[cur_comb[0]][1]-self.cursors[cur_comb[1]][1]
                item = QtWidgets.QTableWidgetItem(f'{dy}')
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                cur_table.setItem(m,3,item)
                #
                if abs(dx) > 0:
                    item = QtWidgets.QTableWidgetItem(f'{1/dx}')
                else:
                    item = QtWidgets.QTableWidgetItem(f'N/A')
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                cur_table.setItem(m,4,item)
                #
                if abs(dy) > 0:
                    item = QtWidgets.QTableWidgetItem(f'{1/dy}')
                else:
                    item = QtWidgets.QTableWidgetItem(f'N/A')
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
                cur_table.setItem(m,5,item)
        else:
            self.win.tbl_cursor_diffs.setVisible(False)
    def _event_btn_cursor_add(self):
        if self.plt_main != None:
            xRng = self.plt_main.getAxis('bottom').range
            yRng = self.plt_main.getAxis('left').range
            x,y = 0.5*(xRng[0]+xRng[1]), 0.5*(yRng[0]+yRng[1])
        else:
            x,y = 0,0
        #Find new colour
        col = self.find_new_colour([x[2] for x in self.cursors])
        #
        if self.plt_main == None:
            self.cursors += [[x,y, col, None]]
        else:
            obj = Cursor_Cross(x, y, col)
            self.cursors += [[x,y, col, obj]]
            obj.connect_plt_to_move_event(self.plt_main)
            self.plt_main.addItem(obj)
            if self.plot_type == 2:
                self.data_curs_x += [self.plt_curs_x.plot([],[],pen=pg.mkPen(col))]
                self.data_curs_y += [self.plt_curs_y.plot([],[],pen=pg.mkPen(col))]
            m = len(self.cursors) - 1
            obj.sigChangedCurX.connect(partial(self.update_cursor_y, m))
            obj.sigChangedCurY.connect(partial(self.update_cursor_x, m))
        self.update_lstbx_cursors()
    def _event_btn_cursor_del(self):
        sel_ind = self.get_listbox_sel_ind(self.win.lstbx_cursors)
        if sel_ind == -1:
            return
        cur_curse = self.cursors.pop(sel_ind)
        if self.plot_type == 2:
            self.data_curs_x.pop(sel_ind).clear()
            self.data_curs_y.pop(sel_ind).clear()
        self.plt_main.removeItem(cur_curse[3])
        del cur_curse[3]
        self.update_lstbx_cursors()
    def _event_btn_cursor_reset(self):
        if not isinstance(self.x_data, np.ndarray) or not isinstance(self.y_data, np.ndarray):
            return
        xMin = self.x_data.min()
        xMax = self.x_data.max()
        yMin = self.y_data.min()
        yMax = self.y_data.max()
        new_x = 0.5*(xMin+xMax)
        new_y = 0.5*(yMin+yMax)
        for m in range(len(self.cursors)):
            cur_x, cur_y = self.cursors[m][:2]
            if cur_x < xMin or cur_x > xMax:
                x = new_x
            else:
                x = cur_x
            if cur_y < yMin or cur_y > yMax:
                y = new_y
            else:
                y = cur_y
            if self.cursors[m][3] == None:
                self.cursors[m][:2] = x, y
            else:
                self.cursors[m][3].set_value(x, y)

    def update_all_anal_cursors(self):
        for cur_curse in self.analysis_cursors:
            cur_curse.init_cursor(self.plt_main)
    def _event_btn_anal_cursor_add(self):
        cur_sel = self.win.cmbx_anal_cursors.currentText()
        #
        #Find previous names
        prev_names = []
        for cur_curse in self.analysis_cursors:
            if cur_curse.Type == cur_sel:
                prev_names += [cur_curse.Name]
        #Choose new name
        new_prefix = self.possible_cursors[cur_sel].Prefix
        m = 0
        while f'{new_prefix}{m}' in prev_names:
            m += 1
        new_name = f'{new_prefix}{m}'
        #
        #Find new colour
        col = self.find_new_colour([x.Colour for x in self.analysis_cursors])
        #
        new_anal_curse = self.possible_cursors[cur_sel](new_name, col, self._event_anal_cursor_changed)
        self.analysis_cursors += [new_anal_curse]
        new_anal_curse.Visible = True   #Set initial default to show cursor...
        #
        #Add to the table
        cur_table = self.win.tbl_analy_cursors
        num_prev_items = cur_table.rowCount()
        cur_table.setRowCount(num_prev_items+1)
        textcol = self.get_text_colour(col)
        #
        self._anal_cursor_add_block_event = True
        item = QtWidgets.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        if new_anal_curse.Visible:
            item.setCheckState(QtCore.Qt.Checked)
        else:
            item.setCheckState(QtCore.Qt.Unchecked)
        item.setTextAlignment(QtCore.Qt.AlignHCenter)   #TODO: Fix this - it doesn't work as it inserts text next to the check-box...
        cur_table.setItem(num_prev_items,0,item)
        item = QtWidgets.QTableWidgetItem(new_anal_curse.Name)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
        item.setForeground(textcol)
        cur_table.setItem(num_prev_items,1,item)
        item = QtWidgets.QTableWidgetItem(new_anal_curse.Type)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
        item.setForeground(textcol)
        cur_table.setItem(num_prev_items,2,item)
        item = QtWidgets.QTableWidgetItem(new_anal_curse.Summary)
        item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)
        item.setForeground(textcol)
        cur_table.setItem(num_prev_items,3,item)
        self._anal_cursor_add_block_event = False
        #
        #Link to plot if applicable
        if self.plt_main:
            new_anal_curse.init_cursor(self.plt_main)
    def _event_btn_anal_cursor_del(self):
        cur_row = self.win.tbl_analy_cursors.currentRow()
        if cur_row < 0: #It actually returns -1!!!
            return
        del_name = self.win.tbl_analy_cursors.item(cur_row,1).text()
        self.win.tbl_analy_cursors.removeRow(cur_row)
        #Assuming list and table are concurrent!!!
        found_curse = self.analysis_cursors.pop(cur_row)
        found_curse.release_from_plots()
        if self.plt_main:
            self.plt_main.removeItem(found_curse)
        del found_curse
        

    def _event_chkbx_anal_cursor_show(self, item):
        if self._anal_cursor_add_block_event or item.column() != 0:
            return
        self.analysis_cursors[item.row()].Visible = item.checkState() == QtCore.Qt.CheckState.Checked
    def _event_anal_cursor_changed(self, anal_cursor):
        for cur_row in range(self.win.tbl_analy_cursors.rowCount()):
            if anal_cursor.Name == self.win.tbl_analy_cursors.item(cur_row,1).text():
                self.win.tbl_analy_cursors.item(cur_row,3).setText(anal_cursor.Summary)
                return

    def _event_btn_get_attrs(self):
        clip_str = f"File: {self.file_path}\n"
        cb = self.app.clipboard()
        cb.clear(mode=cb.Clipboard )
        cb.setText(clip_str, mode=cb.Clipboard)
    def _event_btn_get_fig(self):
        #Store figure as a temporary image
        exptr = pgExp.ImageExporter( self.plot_layout_widget.scene() )
        exptr.export('tempClipFig.png')
        cb = self.app.clipboard()
        cb.clear(mode=cb.Clipboard )
        cb.setImage(QtGui.QImage('tempClipFig.png'))
        os.remove('tempClipFig.png')

    def update_plot_data(self):
        if self.data_extractor:
            self.setup_plot_vars()  #Mostly relevant for the directory version which may get more variables with time...
            if self.data_extractor.data_ready():
                (indep_params, final_data, dict_rem_slices) = self.data_extractor.get_data()
                cur_var_ind = self.dep_vars.index(self.win.cmbx_dep_var.currentText())
                if not self.update_plot_post_proc(indep_params, final_data):
                    #Not post-processed (hence not plotted) - so do so now...
                    if self.plot_type == 1 and len(indep_params) == 1:
                        self.plot_1D(indep_params[0], final_data[cur_var_ind], self.win.cmbx_dep_var.currentText())
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

    def _reset_thrds_and_files(self):
        if self.data_thread_pool == None:
            self.data_thread_pool = ThreadPool(processes=2)
        if self.data_extractor != None:
            self.data_extractor.close_file()
            self.data_thread_pool = ThreadPool(processes=2)
    def _event_btn_open_H5(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self.win, self.app.tr("Open HDF5 File"), "", self.app.tr("HDF5 Files (*.h5)"))
        if fileName[0] != '':
            self._reset_thrds_and_files()
            self.data_extractor = DataExtractorH5single(fileName[0], self.data_thread_pool)
            win_str = '/'.join(fileName[0].split('/')[-2:]) #Assuming that it'll always have one slash (e.g. drive letter itself)
            self.win.setWindowTitle(f'{self.default_win_title} - HDF5-File: {win_str}')
            self.file_path = fileName[0]
            self.setup_plot_vars()
    def _event_btn_open_H5dir(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self.win, self.app.tr("Open HDF5 File"), "", self.app.tr("HDF5 Files (*.h5)"))
        if fileName[0] != '':
            self._reset_thrds_and_files()
            self.data_extractor = DataExtractorH5multiple(fileName[0], self.data_thread_pool)
            win_str = '/'.join(fileName[0].split('/')[-3:]) #Assuming that it'll always have one slash (e.g. drive letter itself)
            self.win.setWindowTitle(f'{self.default_win_title} - HDF5-Directory: {win_str}')
            self.file_path = fileName[0]
            self.setup_plot_vars()
    def _event_btn_open_DAT(self):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self.win, self.app.tr("Open UQTools DAT File"), "", self.app.tr("UQTools DAT (*.dat)"))
        if fileName[0] != '':
            self._reset_thrds_and_files()
            self.data_extractor = DataExtractorUQtoolsDAT(fileName[0], self.data_thread_pool)
            win_str = '/'.join(fileName[0].split('/')[-2:]) #Assuming that it'll always have one slash (e.g. drive letter itself)
            self.win.setWindowTitle(f'{self.default_win_title} - UQTools DAT-File: {win_str}')
            self.file_path = fileName[0]
            self.setup_plot_vars()
    def _open_file_prev(self):
        if not isinstance(self.data_extractor, DataExtractorH5single):
            return
        cur_file = self.data_extractor.file_name
        cur_exp_dir = os.path.dirname(cur_file)
        cur_parent_dir = os.path.dirname(cur_exp_dir) + '/'  #Should exist...
        #
        dirs = [x[0] for x in os.walk(cur_parent_dir)]
        cur_ind = dirs.index(cur_exp_dir)
        cur_ind = cur_ind - 1
        filename = ''
        while cur_ind > 0:  #Presuming that the first directory is the base path...
            cur_file = dirs[cur_ind]+'/data.h5'
            if os.path.exists(cur_file):
                filename = cur_file
                break
            cur_ind = cur_ind - 1
        if filename == '':
            return
        self._reset_thrds_and_files()
        self.data_extractor = DataExtractorH5single(filename, self.data_thread_pool)
        self.file_path = filename
        self.setup_plot_vars()
    def _open_file_next(self):
        if not isinstance(self.data_extractor, DataExtractorH5single):
            return
        cur_file = self.data_extractor.file_name
        cur_exp_dir = os.path.dirname(cur_file)
        cur_parent_dir = os.path.dirname(cur_exp_dir) + '/'  #Should exist...
        #
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
        self._reset_thrds_and_files()
        self.data_extractor = DataExtractorH5single(filename, self.data_thread_pool)
        self.file_path = filename
        self.setup_plot_vars()

    def _post_procs_update_configs_from_file(self):
        #Create file if it does not exist...
        if not os.path.isfile('config_post_procs.json'):
            with open('config_post_procs.json', 'w') as outfile:
                json.dump({}, outfile, indent=4)
                self._avail_post_proc_configs = {}
                self.listbox_safe_clear(self.win.cmbx_proc_list_open)
            return
        #
        with open('config_post_procs.json', 'r') as outfile:
            self._avail_post_proc_configs = json.load(outfile)
        self.win.cmbx_proc_list_open.clear()
        self.win.cmbx_proc_list_open.addItems(self._avail_post_proc_configs.keys())
    def _event_btn_proc_list_open(self):
        cur_file = str(self.win.cmbx_proc_list_open.currentText())
        if cur_file == '':
            return
        #Transfer the configuration (gathered from the file earlier) into the current list of post-processors
        self.cur_post_procs = self._avail_post_proc_configs[cur_file]
        #Create the post-processor objects appropriately
        for cur_proc in self.cur_post_procs:
            cur_proc['ProcessObj'] = self.post_procs_all[cur_proc['ProcessName']]
        #Select the last post-processor to display...
        self._post_procs_fill_current(len(self.cur_post_procs)-1)
    def _event_btn_proc_list_save(self):
        self._post_procs_update_configs_from_file()
        cur_name = self.win.tbx_proc_list_save.text()
        if cur_name == "":
            return
        self._avail_post_proc_configs[cur_name] = self.cur_post_procs
        with open('config_post_procs.json', 'w') as outfile:
            json.dump(self._avail_post_proc_configs, outfile, indent=4, default=lambda o: '<not serializable>')
        self._post_procs_update_configs_from_file()

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
    def _event_btn_slice_vars_val_inc(self):
        cur_sel_ind = self.get_listbox_sel_ind(self.win.lstbx_param_slices)
        if cur_sel_ind == -1:
            return
        cur_var_name = self.cur_slice_var_keys_lstbx[cur_sel_ind]
        cur_len = self.dict_var_slices[cur_var_name][1].size
        cur_ind = int(float(self.win.sldr_param_slices.value()))
        if cur_ind + 1 < cur_len:
            self.win.sldr_param_slices.setValue(cur_ind + 1)
    def _event_btn_slice_vars_val_dec(self):
        cur_sel_ind = self.get_listbox_sel_ind(self.win.lstbx_param_slices)
        if cur_sel_ind == -1:
            return
        cur_ind = int(float(self.win.sldr_param_slices.value()))
        if cur_ind > 0:
            self.win.sldr_param_slices.setValue(cur_ind - 1)

    
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
        lbl_procs.setText("Enabled")
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
                self.plot_1D(cur_data['x'], cur_data['data'], self.cur_post_proc_output)
        return True
    
    def plot_1D(self, x, y, yLabel):
        if self.data_line == None:
            return
        self.x_data = x
        self.y_data = y
        self.z_data = None
        self.data_line.setData(x, y)
        self.plt_main.getAxis('bottom').setLabel(str(self.win.cmbx_axis_x.currentText()))
        self.plt_main.getAxis('left').setLabel(yLabel)        

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
        #
        zData = self.z_data.flatten()
        zData = zData[~np.isnan(zData)]
        hist_vals, bin_edges = np.histogram(zData, bins=max(int(zData.size*0.01),3), density=True)
        centres = 0.5*(bin_edges[1:]+bin_edges[:-1])
        self.data_colhist.setData(centres, hist_vals)
        #
        z_min, z_max = self.colBarItem.levels()
        zMin, zMax = self.z_data.min(), self.z_data.max()
        if np.abs(zMin - z_min) > 1e-12 or np.abs(zMax - z_max) > 1e-12:
            self.colBarItem.setLevels((zMin, zMax))
        #
        for m, cur_curse in enumerate(self.cursors):
            self.update_cursor_x(m)
            self.update_cursor_y(m)
        #
        self.plt_main.getAxis('bottom').setLabel(str(self.win.cmbx_axis_x.currentText()))
        self.plt_main.getAxis('left').setLabel(str(self.win.cmbx_axis_y.currentText()))


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
