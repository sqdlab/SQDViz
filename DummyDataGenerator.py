import h5py
import numpy as np

hf = h5py.File("swmr.h5", 'w', libver='latest')

flux_vals = np.arange(0,3.5,0.1)
freq_vals = np.arange(-5,5,0.1)
ampl_vals = np.arange(0.1,10,0.1)

grp_params = hf.create_group('parameters')
grp_params.create_dataset('flux',data=np.hstack([0,flux_vals]))
grp_params.create_dataset('freq',data=np.hstack([1,freq_vals]))
grp_params.create_dataset('ampl',data=np.hstack([2,ampl_vals]))

grp_meas = hf.create_group('measurements')
grp_meas.create_dataset('I',data=np.hstack([0]))
grp_meas.create_dataset('Q',data=np.hstack([1]))

sweep_arrays = [flux_vals, freq_vals, ampl_vals]
sweep_grids = np.meshgrid(*sweep_arrays, indexing='ij')
sweep_grids = np.vstack([x.flatten() for x in sweep_grids]).T
# sweep_grids = np.array(sweep_grids).T.reshape(-1,len(sweep_arrays))

#data_arr = np.stack([(1-np.exp(-sweep_grids[:,1]))/(1+sweep_grids[:,0]**2/sweep_grids[:,1])]).T
data_arr = np.stack([
                     1.0+0.1*(1-np.exp(-sweep_grids[:,2]))/(1+(sweep_grids[:,1]-sweep_grids[:,0])**2/sweep_grids[:,2]) + 0.01*np.random.rand(sweep_grids.shape[0]),
                     1.0-0.09*(1-np.exp(-sweep_grids[:,2]))/(1+(sweep_grids[:,1]-sweep_grids[:,0])**2/sweep_grids[:,2] + 0.01*np.random.rand(sweep_grids.shape[0]))
                     ]).T
data_arr[-10][0] = 100
data_arr[-20][0] = 100
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
