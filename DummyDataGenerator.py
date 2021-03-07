import h5py
import numpy as np

hf = h5py.File("swmr.h5", 'w', libver='latest')
arr = np.array([1,2,3,4])
dset = hf.create_dataset("data", chunks=(2,), maxshape=(None,), data=arr, compression="gzip")

grp_params = hf.create_group('parameters')
grp_params.create_dataset('freq',data=[1,2,3,4,5])
grp_params.create_dataset('ampl',data=np.arange(1,10))

hf.swmr_mode = True
# Now it is safe for the reader to open the swmr.h5 file
for i in range(5):
    new_shape = ((i+1) * len(arr), )
    dset.resize( new_shape )
    dset[i*len(arr):] = arr
    dset.flush()
    # Notify the reader process that new data has been written

hf.close()
