from DataExtractor import DataExtractor
import csv
import numpy as np
import time

class DataExtractorUQtoolsDAT(DataExtractor):
    def __init__(self, file_name, data_thread_pool):
        super().__init__(data_thread_pool)
        self.csv_file = file_name
        self._process_data_file()

    def _process_data_file(self):
        with open(self.csv_file, 'r' ) as theFile:
            data = []
            header_info = {}
            started_read_col_info = -1
            for line in theFile:
                #Strip in case there are leading spaces/tabs...
                cur_line = line.strip()
                if len(cur_line) == 0:
                    continue
                #Header
                if cur_line[0] == '#':
                    #Strip all whitespace and just split the actual text into an array
                    cur_head = cur_line.lower().split()
                    if "column" in cur_head:
                        num_ind = cur_head.index('column') + 1
                        if len(cur_head) > num_ind:     #If not, then there is no number following the word column...
                            cur_num = cur_head[num_ind].replace(':','').strip()   #Remove the colon and any following characters...
                            if cur_num.isdigit():   #Check that it is indeed an integer...
                                started_read_col_info = int(cur_num)
                                header_info[started_read_col_info] = {}
                    #Note that the name and type will be overwritten if done so twice in the column header...
                    elif ("name" in cur_head or "name:" in cur_head) and started_read_col_info >= 1:
                        #Assume that the colon comes after the 'name' portion...
                        cur_ind = cur_line.index(':') + 1
                        if len(cur_line) > cur_ind:     #If not, then the name is empty after the colon...
                            header_info[started_read_col_info]['name'] = cur_line[cur_ind:].strip()
                        else:
                            header_info[started_read_col_info]['name'] = f'col{started_read_col_info}'
                    elif ("type" in cur_head or "type:" in cur_head) and started_read_col_info >= 1:
                        cur_ind = cur_line.index(':') + 1
                        if len(cur_line) > cur_ind:     #If not, then the name is empty after the colon...
                            header_info[started_read_col_info]['type'] = cur_line[cur_ind:].strip()
                        else:
                            header_info[started_read_col_info]['type'] = f'coordinate'
                else:
                    data += [[float(x) for x in cur_line.split()]]

        self.data = np.array(data)
        self.param_indices = header_info.keys()
        #Column index offset - e.g. SUBTRACT 1 IF THE COLUMNS ARE INDEXED FROM 1
        col_offset = min(self.param_indices)
        self._indep_param_name_inds = [(header_info[x]['name'],x-col_offset) for x in header_info.keys() if header_info[x]['type'].lower() == 'coordinate']
        self._dep_param_name_inds = [(header_info[x]['name'],x-col_offset) for x in header_info.keys() if header_info[x]['type'].lower() == 'value']

    def _get_current_data(self, params):
        self._process_data_file()

        dim_plot = len(params['axis_vars'])

        axis_var = [0]*dim_plot

        #Recalculate the independent parameter ranges
        indep_inds = [x[1] for x in self._indep_param_name_inds]
        param_ranges = [None] * len(self._indep_param_name_inds)
        sliced_rows = np.arange(self.data.shape[0])     #Initially taken to be all
        dict_rem_slices = {}
        for ind,m in enumerate(self._indep_param_name_inds):
            indexes = np.unique(self.data[:,m[1]], return_index=True)[1]
            param_ranges[ind] = np.array([self.data[index,m[1]] for index in sorted(indexes)])

            if m[0] in params['axis_vars']:
                axis_var[params['axis_vars'].index(m[0])] = ind
            else:
                dict_rem_slices[m[0]] = param_ranges[ind]
                cur_slice_ind = 0
                if m[0] in params['slice_vars'] and params['slice_vars'][m[0]] < param_ranges[ind].size:
                    cur_slice_ind = params['slice_vars'][m[0]]
                #Convert slice index into actual value
                slice_val = param_ranges[ind][cur_slice_ind]
                #Make the slicer take all values that equal the requested slicing value...
                sliced_row_indices = np.where(self.data[:,m[1]] == slice_val)[0]
                sliced_rows = np.intersect1d(sliced_rows, sliced_row_indices, assume_unique=True)     #The indices should be unique...

        indep_params = [param_ranges[x] for x in axis_var]

        if dim_plot == 1:
            final_data = []
            for cur_dep in self._dep_param_name_inds:
                final_data += [self.data[sliced_rows, cur_dep[1]]]
        else:
            xVars = indep_params[0]
            yVars = indep_params[1]

            data_all = self.data[sliced_rows, :]
            #Relying on the idea that there is (potentially) no structure and that the elements are somewhat unique...
            #Convert the X and Y columns into indices referencing the indep_params arrays...
            for m in range(len(indep_params)):
                #Convert the X/Y column of values into indices in the indep_params[0] and indep_params[1] arrays...
                cur_col_vals = data_all[:, axis_var[m]]
                sort_idx = indep_params[m].argsort()
                data_all[:, axis_var[m]] = sort_idx[np.searchsorted(indep_params[m], cur_col_vals, sorter = sort_idx)]

            #Run through the rows and fill the array - TODO: this should be vectorised...
            final_data = [np.empty((len(xVars),len(yVars),)) for x in range(len(self._dep_param_name_inds))]    #Using list-multiply just copies the same array instead of instantiating a new one...
            for m in range(len(final_data)):
                final_data[m][:] = np.nan
            for m in range(data_all.shape[0]):
                for ind, cur_dep in enumerate(self._dep_param_name_inds):
                    final_data[ind][ int(data_all[m,axis_var[0]]) , int(data_all[m,axis_var[1]]) ] = data_all[m,cur_dep[1]]
        
        #Simulate lag... Otherwise it lags the UI...
        time.sleep(2)

        return (indep_params, final_data, dict_rem_slices)

    def get_independent_vars(self):
        return [x[0] for x in self._indep_param_name_inds]

    def get_dependent_vars(self):
        return [x[0] for x in self._dep_param_name_inds]
