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

        #Extract the independent variables (the group "parameters" holds the 1D arrays representing the individual parameter values)
        self._dep_params = [None]*len(self.hdf5_file["measurements"].keys())
        for cur_key in self.hdf5_file["measurements"].keys():
            cur_ind = self.hdf5_file["measurements"][cur_key][0]
            self._dep_params[cur_ind] = cur_key

    def _get_current_data(self, params):
        self.dset.id.refresh()

        self._param_names = [x for x in self.hdf5_file["parameters"].keys()]

        #!!Note that self._param_names will be reordered when figuring out the parameter indices...!!

        dim_plot = len(params['slice_vars'])

        temp_param_names = self._param_names[:]
        self.param_vals = [None]*len(temp_param_names)
        param_slicer = [None]*len(temp_param_names)
        indep_params = [None]*len(params['slice_vars'])
        dict_rem_slices = {}
        for cur_param in temp_param_names:
            cur_ind = int(self.hdf5_file["parameters"][cur_param][0])
            self._param_names[cur_ind] = cur_param
            self.param_vals[cur_ind] = self.hdf5_file["parameters"][cur_param][1:]
            if cur_param in params['slice_vars']:
                param_slicer[cur_ind] = np.s_[0:]
                indep_params[params['slice_vars'].index(cur_param)] = self.param_vals[cur_ind]
            else:
                dict_rem_slices[cur_param] = self.param_vals[cur_ind]
                param_slicer[cur_ind] = np.s_[0]   #TODO: Change appropriately later to actual slicing index...

        cur_shape = [len(x) for x in self.param_vals] + [len(self._dep_params)]
        self.cur_data = self.dset[:].reshape(tuple(x for x in cur_shape))
        # param_slicer += [0]
        # param_slicer = tuple(x for x in param_slicer)

        #Simulate lag...
        time.sleep(1)

        #Extract the data individually and repack them into a list of np-arrays for every dependent variable
        param_slicer = tuple(x for x in param_slicer)
        final_data = []
        for ind in range(len(self._dep_params)):
            if dim_plot == 1:
                final_data.append(self.cur_data[param_slicer][:,ind])
            else:
                final_data.append(self.cur_data[param_slicer][:,:,ind])
        
        if len(final_data[0].shape) == 2:
            #Check if data needs to be transposed
            if self._param_names.index(params['slice_vars'][0]) > self._param_names.index(params['slice_vars'][1]):
                for ind in range(len(self._dep_params)):
                    final_data[ind] = final_data[ind].T       #TODO: Suboptimal? Do this when generating the slices above?
        return (indep_params, final_data, dict_rem_slices)

    def get_independent_vars(self):
        return list(self._param_names)

    def get_dependent_vars(self):
        return list(self._dep_params)