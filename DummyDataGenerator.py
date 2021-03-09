import h5py
import numpy as np

hf = h5py.File("swmr.h5", 'w', libver='latest')

freq_vals = np.arange(-5,5,0.1)
ampl_vals = np.arange(0.1,10,0.1)

grp_params = hf.create_group('parameters')
grp_params.create_dataset('freq',data=np.hstack([0,freq_vals]))
grp_params.create_dataset('ampl',data=np.hstack([1,ampl_vals]))

sweep_arrays = [freq_vals, ampl_vals]
sweep_grids = np.meshgrid(*sweep_arrays)
sweep_grids = np.array(sweep_grids).T.reshape(-1,len(sweep_arrays))

data_arr = np.stack([(1-np.exp(-sweep_grids[:,1]))/(1+sweep_grids[:,0]**2/sweep_grids[:,1]),
                 -0.5*(1-np.exp(-sweep_grids[:,1]))/(1+sweep_grids[:,0]**2/sweep_grids[:,1])]).T

arr = np.zeros(data_arr.shape)
arr[:] = np.nan
dset = hf.create_dataset("data", data=arr, compression="gzip")#, chunks=(2,)

hf.swmr_mode = True

num_segs = 10
num_rows_per_sample = int(len(data_arr)/num_segs)
# Now it is safe for the reader to open the swmr.h5 file
for i in range(num_segs):
    # new_shape = ((i+1) * len(arr), 2)
    # dset.resize( new_shape )
    dset[i*num_rows_per_sample:(i+1)*num_rows_per_sample] = data_arr[i*num_rows_per_sample:(i+1)*num_rows_per_sample]
    dset.flush()
    a=0
    # Notify the reader process that new data has been written

hf.close()
