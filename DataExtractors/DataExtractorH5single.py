import re
from DataExtractors.DataExtractor import DataExtractor
from DataExtractors.FileIO import FileIOReader
import h5py
import numpy as np
import time

class DataExtractorH5single(DataExtractor):
    def __init__(self, file_name, data_thread_pool):
        assert data_thread_pool._processes >= 2, "DataExtractorH5single requires 2 processes (an extra one to decouple data-loading)."
        super().__init__(data_thread_pool)

        self.reader = FileIOReader(file_name)
        self._param_names = self.reader.param_names[:]
        self._dep_params = self.reader.dep_params[:]

        self.file_name = file_name

        self.async_load_result = None
        self.loaded_once = False

    def _load_data_from_file(self):
        self.reader.dset.id.refresh()
        return [self.reader.param_names[:],
                [x*1.0 for x in self.reader.param_vals],
                self.reader.dep_params[:],
                self.reader.get_numpy_array()]

    def _get_current_data(self, params):
        if not self.async_load_result:
            #No new thread sent over to load from file - may as well, send one in now...
            #i.e. it might arrive by the time the next time _get_current_data is called...
            self.async_load_result = self.data_thread_pool.apply_async(self._load_data_from_file)

        if not self.loaded_once:
            #Don't have data yet - so one needs to wait...
            while not self.async_load_result.ready():
                pass
            self.loaded_once = True
        
        if self.async_load_result.ready():
            self._param_names, self._param_vals, self._dep_params, self.cur_data = self.async_load_result.get()
            self.async_load_result = None               

        dim_plot = len(params['axis_vars'])

        param_slicer = []
        indep_params = [None]*len(params['axis_vars'])
        dict_rem_slices = {}
        for m, cur_param in enumerate(self._param_names):
            if cur_param in params['axis_vars']:
                indep_params[params['axis_vars'].index(cur_param)] = self._param_vals[m]
                param_slicer += [np.s_[0:]]
            else:
                dict_rem_slices[cur_param] = self._param_vals[m]
                cur_slice_ind = 0
                if cur_param in params['slice_vars']:
                    #Ensure slice index is in range
                    if params['slice_vars'][cur_param] < self._param_vals[m].size:
                        cur_slice_ind = params['slice_vars'][cur_param]
                param_slicer += [np.s_[cur_slice_ind]]

        #Simulate lag...
        # time.sleep(2)

        #Extract the data individually and repack them into a list of nd-arrays for every dependent variable
        param_slicer = tuple(x for x in param_slicer)
        final_data = []
        for ind in range(len(self._dep_params)):
            if dim_plot == 1:
                final_data.append(self.cur_data[param_slicer][:,ind])
            else:
                final_data.append(self.cur_data[param_slicer][:,:,ind])
        
        if len(final_data[0].shape) == 2:
            #Check if data needs to be transposed
            if self._param_names.index(params['axis_vars'][0]) > self._param_names.index(params['axis_vars'][1]):
                for ind in range(len(self._dep_params)):
                    final_data[ind] = final_data[ind].T
        return (indep_params, final_data, dict_rem_slices)

    def get_independent_vars(self):
        return list(self._param_names)

    def get_dependent_vars(self):
        return list(self._dep_params)
    
    def close_file(self):
        self.data_thread_pool.terminate()
        self.reader.release()
