import h5py
import numpy as np

hf = h5py.File("swmr.h5", 'w', libver='latest')

arr = np.zeros((20,2))
arr[:] = np.nan
dset = hf.create_dataset("data", data=arr, compression="gzip")#, chunks=(2,)

data_arr = np.array([[1,2],[1,4],[3,2],[7,43],[15,64]])

grp_params = hf.create_group('parameters')
grp_params.create_dataset('freq',data=[1,2,3,4,5])
grp_params.create_dataset('ampl',data=np.arange(1,10))

hf.swmr_mode = True
# Now it is safe for the reader to open the swmr.h5 file
for i in range(4):
    # new_shape = ((i+1) * len(arr), 2)
    # dset.resize( new_shape )
    dset[i*len(data_arr):(i+1)*len(data_arr)] = data_arr
    dset.flush()
    a=0
    # Notify the reader process that new data has been written

hf.close()
