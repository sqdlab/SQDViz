import h5py
import os.path
import json
from h5py._hl.files import File
import numpy as np
import itertools

from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.collections
from numpy.core.fromnumeric import argsort
class FileIOWriter:
    def __init__(self, filepath, **kwargs):
        self._filepath = filepath
        self._hf = None
        self.store_timestamps = kwargs.get('store_timestamps', True)

    def _init_hdf5(self, sweep_vars, data_pkt):
        if self._hf == None:
            if os.path.isfile(self._filepath):
                self._hf = h5py.File(self._filepath, 'a', libver='latest')
                self._hf.swmr_mode = True
            else:
                self._hf = h5py.File(self._filepath, 'w', libver='latest')
                
                #Write down the indexing parameters (i.e. independent variables)
                grp_params = self._hf.create_group('parameters')
                #Assumes uniformity - TODO: Look into padding with NaNs if the inner data packets change in shape (e.g. different repetitions etc...)
                for m, cur_param in enumerate(sweep_vars):
                    grp_params.create_dataset(cur_param[0].Name, data=np.hstack([m,cur_param[1]]))
                offset = len(sweep_vars)
                #
                random_dataset = next(iter(data_pkt['data'].values()))
                if np.isscalar(random_dataset):
                    param_sizes = (1,)
                else:
                    param_sizes = random_dataset.shape
                #
                for m, cur_param in enumerate(data_pkt['parameters']):
                    if 'parameter_values' in data_pkt and cur_param in data_pkt['parameter_values']:
                        assert data_pkt['parameter_values'][cur_param].size == param_sizes[m], f"The dataset parameter {cur_param} has {data_pkt['parameter_values'][cur_param].size} values, while the corresponding array index is of size {param_sizes[m]}."
                        grp_params.create_dataset(cur_param, data=np.hstack([m+offset,data_pkt['parameter_values'][cur_param]]))
                    else:
                        grp_params.create_dataset(cur_param, data=np.hstack([m+offset,np.arange(param_sizes[m])]))
                
                #Write down the measurement output channels (i.e. dependent variables)
                grp_meas = self._hf.create_group('measurements')
                self._meas_chs = []
                for m, cur_meas_ch in enumerate(data_pkt['data'].keys()):
                    grp_meas.create_dataset(cur_meas_ch, data=np.hstack([m]))
                    self._meas_chs += [cur_meas_ch]

                if len(param_sizes) == 0:
                    self._datapkt_size = 1
                else:
                    self._datapkt_size = np.prod(list(param_sizes))

                data_array_shape = [x[1].size for x in sweep_vars] + list(param_sizes)
                arr_size = int(np.prod(data_array_shape))
                arr = np.zeros((arr_size, len(data_pkt['data'].keys())))
                arr[:] = np.nan
                self._dset = self._hf.create_dataset("data", data=arr, compression="gzip")
                self._dset_ind = 0
                #Time-stamps (usually length 27 bytes)
                if self.store_timestamps:
                    self._ts_len = len( np.datetime_as_string(np.datetime64(datetime.now()),timezone='UTC').encode('utf-8') )
                    arr = np.array([np.datetime64()]*arr_size, dtype=f'S{self._ts_len}')
                    self._dsetTS = self._hf.create_dataset("timeStamps", data=arr, compression="gzip")
                
                self._hf.swmr_mode = True

    def push_datapkt(self, data_pkt, sweep_vars):
        self._init_hdf5(sweep_vars, data_pkt)

        cur_data = np.vstack([data_pkt['data'][x].flatten() for x in self._meas_chs]).T
        self._dset[self._dset_ind*self._datapkt_size : (self._dset_ind+1)*self._datapkt_size] = cur_data
        if self.store_timestamps:
            #Trick taken from here: https://stackoverflow.com/questions/68443753/datetime-storing-in-hd5-database
            cur_times = [np.datetime64(datetime.now())] * cur_data.shape[0]
            utc_strs = np.array( [np.datetime_as_string(n,timezone='UTC').encode('utf-8') for n in cur_times] )
            self._dsetTS[self._dset_ind*self._datapkt_size : (self._dset_ind+1)*self._datapkt_size] = utc_strs
        self._dset_ind += 1
        self._dset.flush()
    
    def close(self):
        if self._hf:
            self._hf.close()
            self._hf = None

class FileIOReader:
    def __init__(self, filepath):
        self.file_path = filepath
        self.folder_path = os.path.dirname(filepath)
        self.hdf5_file = h5py.File(filepath, 'r', libver='latest', swmr=True)
        self.dset = self.hdf5_file["data"]
        if 'timeStamps' in self.hdf5_file:
            self.dsetTS = self.hdf5_file["timeStamps"]
        else:
            self.dsetTS = None

        #Extract the independent variables (the group "parameters" holds the 1D arrays representing the individual parameter values)
        self.param_names = [x for x in self.hdf5_file["parameters"].keys()]

        #Extract the independent variables (the group "parameters" holds the 1D arrays representing the individual parameter values)
        self.dep_params = [None]*len(self.hdf5_file["measurements"].keys())
        for cur_key in self.hdf5_file["measurements"].keys():
            cur_ind = self.hdf5_file["measurements"][cur_key][0]
            self.dep_params[cur_ind] = cur_key

        temp_param_names = self.param_names[:]
        self.param_vals = [None]*len(temp_param_names) 
        for cur_param in temp_param_names:
            cur_ind = int(self.hdf5_file["parameters"][cur_param][0])
            self.param_names[cur_ind] = cur_param
            self.param_vals[cur_ind] = self.hdf5_file["parameters"][cur_param][1:]

    def get_numpy_array(self):
        if not self.hdf5_file is None:
            cur_shape = [len(x) for x in self.param_vals] + [len(self.dep_params)]
            return self.dset[:].reshape(tuple(x for x in cur_shape))
        else:
            assert False, "The reader has released the file - create a new FileIOReader instance to extract data."
            return np.array([])
    
    def get_time_stamps(self):
        if not self.hdf5_file is None:
            assert not self.dsetTS is None, "There are no time-stamps in this data file. It was probably created before the time-stamp feature was implemented in SQDToolz."
            cur_shape = [len(x) for x in self.param_vals]
            cur_data = self.dsetTS[:]
            cur_data = np.array([np.datetime64(x) for x in cur_data])
            return cur_data.reshape(tuple(x for x in cur_shape))
        else:
            assert False, "The reader has released the file - create a new FileIOReader instance to extract data."
            return np.array([])
    
    def release(self):
        if not self.hdf5_file is None:
            self.dset = None
            self.hdf5_file.close()
            self.file_path = ''
            self.folder_path = ''
            self.hdf5_file = None

class FileIODirectory:
    class plt_object:
        def __init__(self, pc, z_values):
            self.pc = pc
            self.z_values = z_values
            self._called_set_z_array = False
        
        def set_z_array(self, z_array):
            self.pc.set_array(z_array)
            self._called_set_z_array = True

        def add_to_axis(self, ax):
            assert self._called_set_z_array, "Must call set_z_array first."
            ax.add_collection(self.pc)
            ax.autoscale()

    def __init__(self, filepath):
        cur_dir_path = os.path.dirname(filepath)
        dir_name = os.path.basename(cur_dir_path)
        assert dir_name[0:6].isdigit(), "The time-stamp is not present in this folder."

        self._main_dir = os.path.dirname(os.path.dirname(filepath))
        assert os.path.basename(self._main_dir)[0:6].isdigit(), "The time-stamp is not present in the parent folder."
        self._cur_dir_suffix = dir_name[6:]
        self._cur_file_name = os.path.basename(filepath)

        #Collect all relevant similar files...
        cur_dir_files = [x[0] for x in os.walk(self._main_dir)][1:]
        cur_files = []
        self.folders = []
        self.folders_ignored = []
        no_file_index = False
        for cur_folder in cur_dir_files:
            #Check that the suffix of the folder name matches...
            if not os.path.basename(cur_folder).endswith(self._cur_dir_suffix):
                continue

            #Check that the relevant data and attribute files exist...
            filepath = cur_folder +'/' + self._cur_file_name
            if not os.path.isfile(cur_folder +'/' + self._cur_file_name):
                self.folders_ignored += [cur_folder]
                continue
            if not os.path.isfile(cur_folder +'/' + 'experiment_parameters.txt'):
                self.folders_ignored += [cur_folder]
                continue
            if not os.path.isfile(cur_folder +'/' + 'laboratory_parameters.txt'):
                self.folders_ignored += [cur_folder]
                continue

            #Collect the information and add it to a list (note that the giant numpy array is not read in here...)...
            cur_file = FileIOReader(filepath)
            with open(cur_folder +'/' + 'experiment_parameters.txt') as json_file:
                data = json.load(json_file)
                var_names = data['Sweeps']
                if not no_file_index and 'FileIndex' in data:
                    cur_file_index = data['FileIndex']
                else:
                    cur_file_index = 0
                    no_file_index = True
            with open(cur_folder +'/' + 'laboratory_parameters.txt') as json_file:
                data = json.load(json_file)
                var_vals = [data[x]['Value'] for x in var_names]

            cur_files += [(cur_file, var_names, var_vals, cur_file_index, cur_folder)]

        #Correct for the arbitrary nature of the folder order given by: os.walk
        if no_file_index:
            pass
            #print("Running FileIODirectory on files generated in legacy version of SQDToolz may cause the files to load to be in a mixed order.")
        else:
            cur_files = sorted(cur_files, key=lambda x: x[3])
        self.folders = [x[4] for x in cur_files]

        self.non_uniform = False

        #Try to figure out the outer structure...
        cur_param_names_outer = cur_files[0][1]
        cur_param_names_inner = cur_files[0][0].param_names
        cur_param_vals_inner = cur_files[0][0].param_vals
        self.dep_params = cur_files[0][0].dep_params
        same_sweep_vars_outer_loop = True
        for cur_file in cur_files:
            #Check that the outer looping variables are the same
            if cur_file[1] != cur_param_names_outer:
                same_sweep_vars_outer_loop = False
            #Check inner sweeping variables are the same
            #TODO: Investigate whether the demand that the files must be of the same inner parameter order is too stringent.
            assert cur_param_names_inner == cur_file[0].param_names, "The inner parameters are different across files. This is a vary non-uniform set of files and shall not be parsed."
            if len(cur_param_vals_inner) == len(cur_file[0].param_vals):
                for cur_ind in range(len(cur_param_vals_inner)):
                    if not np.array_equal(cur_param_vals_inner[cur_ind], cur_file[0].param_vals[cur_ind]):
                        self.non_uniform = True
                        break
            else:
                self.non_uniform = True
            assert self.dep_params == cur_file[0].dep_params, "The dependent parameters are different across files. This is a vary non-uniform set of files and shall not be parsed."
        if len(cur_param_names_outer) == 0:
            same_sweep_vars_outer_loop = False

        #Settle the outer looping variables if there is some semblance of uniformity of the outer sweeping variables
        if same_sweep_vars_outer_loop:
            sweep_grid = np.vstack([x[2] for x in cur_files])
            unique_vals = []
            num_cols = sweep_grid.shape[1]
            for m in range(num_cols):
                u, ind = np.unique(sweep_grid[:,m], return_index=True)
                unique_vals += [u[np.argsort(ind)]]
            
            sweep_grids = np.meshgrid(*unique_vals)
            sweep_grids = np.array(sweep_grids).T.reshape(-1,num_cols)
            if np.array_equal(sweep_grid, sweep_grids):
                #cur_param_names_outer = cur_param_names_outer
                self._cur_param_vals_outer = unique_vals
            else:
                same_sweep_vars_outer_loop = False
        if not same_sweep_vars_outer_loop:
            cur_param_names_outer = ['DirFileNo']
            self._cur_param_vals_outer = [np.arange(len(cur_files))]

        if not self.non_uniform:
            #The sampling is uniform and thus, one can amalgamate all datasets into one giant numpy array!
            cur_arrays = []
            for cur_file in cur_files:
                cur_arrays += [cur_file[0].get_numpy_array()]
            cur_data = np.concatenate(cur_arrays)

            self.param_names = cur_param_names_outer + cur_param_names_inner
            self.param_vals = self._cur_param_vals_outer + cur_param_vals_inner
            self._cur_data = cur_data.reshape(tuple( [x.size for x in self.param_vals] + [len(self.dep_params)] ))
        else:
            #TIME STAMPS ARE CURRENTLY UNSUPPORTED FOR NON-UNIFORM INDEXING
            #TODO: Give support for time-stamps in non-uniform indexing...
            self._ts_valid = False

            #The dataset is non-uniform, so don't reshape the lists...
            self.param_names = cur_param_names_outer + cur_param_names_inner
            self.param_vals = self._cur_param_vals_outer

            self._cur_data = [{'param_vals':x[0].param_vals, 'data':x[0].get_numpy_array()} for x in cur_files]
            #Setup the indexing to match the outer sweeping parameters...
            self._cur_data = np.array(self._cur_data).reshape(tuple(x.size for x in self.param_vals))

            self.uniform_indices = [True]*len(cur_param_names_outer)
            uniform_inners = []
            for cur_inner_ind in range(len(cur_param_names_inner)):
                param_uniform = True
                for cur_file in cur_files:
                    if not np.array_equal(cur_file[0].param_vals[cur_inner_ind], cur_files[0][0].param_vals[cur_inner_ind]):
                        param_uniform = False
                        break
                uniform_inners += [param_uniform]
            self.uniform_indices += uniform_inners
        
        #Release the HDF5 reader files...
        for cur_file in cur_files:
            cur_file[0].release()

    @classmethod
    def fromReader(cls, obj_FileIOReader):
        return cls(obj_FileIOReader.file_path)

    def get_numpy_array(self):
        return self._cur_data

    def get_var_dict_arrays(self, return_slicing_params = False):
        ret_dict = {}
        array_shape = [x.size for x in self._cur_param_vals_outer]
        array_size = np.prod(array_shape)
        for m, cur_folder in enumerate(self.folders):
            with open(cur_folder +'/' + 'laboratory_parameters.txt') as json_file:
                data = json.load(json_file)
                for cur_var in data.keys():
                    if not cur_var in ret_dict:
                        ret_dict[cur_var] = np.empty((array_size,))
                    ret_dict[cur_var][m] = data[cur_var]['Value']
        for cur_var in ret_dict:
            ret_dict[cur_var] = ret_dict[cur_var].reshape(tuple(array_shape))
        if return_slicing_params:
            return ret_dict, self.param_names[:len(self._cur_param_vals_outer)]
        else:
            return ret_dict

