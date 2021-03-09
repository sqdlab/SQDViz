from DataExtractor import DataExtractor
import h5py
import numpy as np
import time

class DataExtractorH5single(DataExtractor):
    def __init__(self, file_name, data_thread_pool):
        super().__init__(data_thread_pool)

        self.hdf5_file = h5py.File(file_name, 'r', libver='latest', swmr=True)
        self.dset = self.hdf5_file["data"]

        #Extract the independent variables (the group "parameters" holds the 1D arrays representing the individual parameter values)
        self._param_names = self.hdf5_file["parameters"].keys()

    def _get_current_data(self, params):
        self.dset.id.refresh()

        self._param_names = [x for x in self.hdf5_file["parameters"].keys()]

        #self._param_names will be reordered when figuring out the parameter indices...

        temp_param_names = self._param_names[:]
        self.param_vals = [None]*len(temp_param_names)
        param_slicer = [None]*len(temp_param_names)
        indep_params = [None]*len(params['slice_vars'])
        for cur_param in temp_param_names:
            cur_ind = int(self.hdf5_file["parameters"][cur_param][0])
            self._param_names[cur_ind] = cur_param
            self.param_vals[cur_ind] = self.hdf5_file["parameters"][cur_param][1:]
            if cur_param in params['slice_vars']:
                param_slicer[cur_ind] = np.s_[0:]
                indep_params[params['slice_vars'].index(cur_param)] = self.param_vals[cur_ind]
            else:
                param_slicer[cur_ind] = np.s_[0]   #TODO: Change appropriately later to actual slicing index...

        cur_shape = [len(x) for x in self.param_vals] + [2]
        self.cur_data = self.dset[:].reshape(tuple(x for x in cur_shape))
        param_slicer += [0]
        param_slicer = tuple(x for x in param_slicer)

        #Simulate lag...
        time.sleep(1)
        final_data = self.cur_data[param_slicer]
        if len(final_data.shape) == 2:
            #Check if data needs to be transposed
            if self._param_names.index(params['slice_vars'][0]) > self._param_names.index(params['slice_vars'][1]):
                final_data = final_data.T
        return (indep_params, final_data)

    def get_independent_vars(self):
        return self._param_names