from DataExtractor import DataExtractor
import h5py
import numpy as np
import time
import os

class DataExtractorH5multiple(DataExtractor):
    def __init__(self, file_name, data_thread_pool):
        super().__init__(data_thread_pool)

        cur_dir_path = os.path.dirname(file_name)
        dir_name = os.path.basename(cur_dir_path)
        assert dir_name[0:6].isdigit(), "The time-stamp is not present in this folder."

        self._main_dir = os.path.dirname(os.path.dirname(file_name))
        assert os.path.basename(self._main_dir)[0:6].isdigit(), "The time-stamp is not present in the parent folder."
        self._cur_dir_suffix = dir_name[6:]
        self._cur_file_name = os.path.basename(file_name)
        
        hdf5_file = h5py.File(file_name, 'r', libver='latest', swmr=True)
        
        #TODO: Add error-checking on this when opening multiple files (i.e. check parameters and measurements...)
        
        #Extract the independent variables (the group "parameters" holds the 1D arrays representing the individual parameter values)
        self.param_names = [x for x in hdf5_file["parameters"].keys()]

        #Extract the independent variables (the group "parameters" holds the 1D arrays representing the individual parameter values)
        self._dep_params = [None]*len(hdf5_file["measurements"].keys())
        for cur_key in hdf5_file["measurements"].keys():
            cur_ind = hdf5_file["measurements"][cur_key][0]
            self._dep_params[cur_ind] = cur_key

        temp_param_names = self.param_names[:]
        self.param_vals = [None]*len(temp_param_names) 
        for cur_param in temp_param_names:
            cur_ind = int(hdf5_file["parameters"][cur_param][0])
            self.param_names[cur_ind] = cur_param
            self.param_vals[cur_ind] = hdf5_file["parameters"][cur_param][1:]
        self.cur_data_shape = [len(x) for x in self.param_vals] + [len(self._dep_params)]

        self.param_names = ['Dir'] + self.param_names
        self.param_vals = [np.array([0])] + self.param_vals

        hdf5_file.close()

        self.cur_data = None

    def _get_current_data(self, params):
        cur_dir_files = [x[0] for x in os.walk(self._main_dir)]
        self.cur_data = None    #TODO: Remove this and use a modified check or rather the last one?
        for cur_folder in cur_dir_files:
            #Check that the suffix of the folder name matches...
            if not os.path.basename(cur_folder).endswith(self._cur_dir_suffix):
                continue
            # #Check that the folder hasn't already been scanned
            # dir_name = os.path.basename(cur_folder)
            # if dir_name in [x[0] for x in self.dsets]:
            #     continue
            #Check that the h5 file exists...
            filepath = cur_folder +'/' + self._cur_file_name
            if not os.path.isfile(cur_folder +'/' + self._cur_file_name):
                continue
            
            hdf5_file = h5py.File(filepath, 'r', libver='latest', swmr=True)
            dset = hdf5_file["data"]
            cur_data = dset[:].reshape(tuple(x for x in self.cur_data_shape))
            if type(self.cur_data) is np.ndarray:
                self.cur_data = np.concatenate([self.cur_data, [cur_data]])
            else:
                self.cur_data = np.array([cur_data])
            hdf5_file.close()

        self.param_vals[0] = np.arange(self.cur_data.shape[0])
        
        dim_plot = len(params['axis_vars'])

        param_slicer = [None]*len(self.param_names)
        dict_rem_slices = {}
        indep_params = [None]*len(params['axis_vars'])
        for cur_ind, cur_param in enumerate(self.param_names):
            if cur_param in params['axis_vars']:
                param_slicer[cur_ind] = np.s_[0:]
                indep_params[params['axis_vars'].index(cur_param)] = self.param_vals[cur_ind]
            else:
                dict_rem_slices[cur_param] = self.param_vals[cur_ind]
                cur_slice_ind = 0
                if cur_param in params['slice_vars']:
                    #Ensure slice index is in range
                    if params['slice_vars'][cur_param] < self.param_vals[cur_ind].size:
                        cur_slice_ind = params['slice_vars'][cur_param]
                param_slicer[cur_ind] = np.s_[cur_slice_ind]

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
            if self.param_names.index(params['axis_vars'][0]) > self.param_names.index(params['axis_vars'][1]):
                for ind in range(len(self._dep_params)):
                    final_data[ind] = final_data[ind].T       #TODO: Suboptimal? Do this when generating the slices above?

        return (indep_params, final_data, dict_rem_slices)

    def get_independent_vars(self):
        return list(self.param_names)

    def get_dependent_vars(self):
        return list(self._dep_params)

