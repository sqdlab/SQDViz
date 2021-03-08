from DataExtractor import DataExtractor
import h5py
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
        #Simulate lag...
        time.sleep(5)
        return self.dset[:,0]

    def get_independent_vars(self):
        return self._param_names