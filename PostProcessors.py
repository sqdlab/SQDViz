
import sys, inspect
import numpy as np
import scipy
import scipy.ndimage

class PostProcessors:
    def get_description(self):
        raise NotImplementedError()

    def get_types(self):
        raise NotImplementedError()

    def get_return_data_names(self):
        raise NotImplementedError()

    def __call__(self, *args):
        raise NotImplementedError()


    @staticmethod
    def get_all_post_processors():
        is_class_member = lambda member: inspect.isclass(member) and member.__module__ == __name__
        clsmembers = inspect.getmembers(sys.modules[__name__], is_class_member)
        #Returns a dictionary of function name and a post-processor object to boot!
        return { x[0][3:]:x[1]() for x in clsmembers if x[0].startswith('PP_') }
        
class PP_IQ2AmpPhase(PostProcessors):
    def get_description(self):
        return "Converts I and Q channel data into Amplitude and Phase (radians) data."

    def get_types(self):
        return ['data', 'data']

    def get_return_data_names(self):
        return ['amp', 'phs']

    def __call__(self, *args):
        assert args[0]['data'].shape == args[1]['data'].shape, "Data has inconsistent shapes"
        
        ret_val_amp = {}
        ret_val_phs = {}
        assert np.array_equal(args[0]['x'], args[1]['x']), "The x-values are not concurrent for I and Q."
        ret_val_amp['x'] = args[0]['x']
        ret_val_phs['x'] = args[0]['x']
        
        if len(args[0]['data'].shape) == 2:
            assert np.array_equal(args[0]['y'], args[1]['y']), "The y-values are not concurrent for I and Q."
            ret_val_amp['y'] = args[0]['y']
            ret_val_phs['y'] = args[0]['y']
        
        ret_val_amp['data'] = np.sqrt(args[0]['data']*args[0]['data'] + args[1]['data']*args[1]['data'])
        ret_val_phs['data'] = np.arctan2(args[1]['data'], args[0]['data'])

        return (ret_val_amp, ret_val_phs)

class PP_MedianFilterX(PostProcessors):
    def get_description(self):
        return "Runs an N-point median filter across the x-axes of the plots. It is good at removing spikes in the data. The ends are kept and thus, the dataset size remains the same."

    def get_types(self):
        return ['data', 'int']

    def get_return_data_names(self):
        return ['datFilt']

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']
        ret_val['y'] = args[0]['y']
        ret_val['data'] = scipy.ndimage.median_filter(args[0]['data'], size=(1, args[1]))
        return ret_val
