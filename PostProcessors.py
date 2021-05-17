import sys, inspect
import numpy as np
import scipy
import scipy.ndimage

class PostProcessors:
    def get_description(self):
        raise NotImplementedError()

    def get_input_args(self):
        raise NotImplementedError()

    def get_output_args(self):
        raise NotImplementedError()

    def __call__(self, *args):
        raise NotImplementedError()

    def _process_default_args(self, leArgs, use_default_data_names = False):
        cur_args = leArgs
        ret_vals = []
        m = 0
        for cur_arg in cur_args:
            if cur_arg[1] == 'int':
                ret_vals.append(cur_arg[2])
            elif cur_arg[1] == 'data':
                if use_default_data_names:
                    ret_vals.append(cur_arg[2])
                else:
                    ret_vals.append(f'd{m}')
                m += 1
            elif cur_arg[1] == 'float' or cur_arg[1] == 'cursor':
                ret_vals.append(cur_arg[2])
            else:
                assert False, "There appears to be an unhandled data-type: " + cur_arg
        return ret_vals

    def get_default_input_args(self):
        return self._process_default_args(self.get_input_args())

    def get_default_output_args(self):
        return self._process_default_args(self.get_output_args(), True)

    def supports_1D(self):
        return True

    @staticmethod
    def get_all_post_processors():
        is_class_member = lambda member: inspect.isclass(member) and member.__module__ == __name__
        clsmembers = inspect.getmembers(sys.modules[__name__], is_class_member)
        #Returns a dictionary of function name and a post-processor object to boot!
        return { x[0][3:]:x[1]() for x in clsmembers if x[0].startswith('PP_') }
        
class PP_IQ2AmpPhase(PostProcessors):
    def get_description(self):
        return "Converts I and Q channel data into Amplitude and Phase (radians) data."

    def get_input_args(self):
        return [('I-channel', 'data'), ('Q-channel', 'data')]

    def get_output_args(self):
        return [('Amplitude', 'data', 'amp'), ('Phase', 'data', 'phs')]

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

    def get_input_args(self):
        return [('Input dataset', 'data'), ('Window size', 'int', 3)]

    def get_output_args(self):
        return [('Filtered data', 'data', 'filtData')]

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']

        if 'y' in args[0]:
            ret_val['y'] = args[0]['y']
            ret_val['data'] = scipy.ndimage.median_filter(args[0]['data'], size=(1, args[1]))
        else:
            ret_val['data'] = scipy.ndimage.median_filter(args[0]['data'], size=(args[1]))
        return (ret_val, )

class PP_SubRegX(PostProcessors):
    def get_description(self):
        return "Performs a line-by-line subtraction of every line by the average value over a selected x-interval on said line."

    def get_input_args(self):
        return [('Input dataset', 'data'), ('X-interval', 'cursor', 'X-Region')]

    def get_output_args(self):
        return [('Filtered data', 'data', 'filtData')]

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']
        
        anal_cursorX = args[1]
        ind1 = (np.abs(ret_val['x'] - anal_cursorX.x1)).argmin()
        ind2 = (np.abs(ret_val['x'] - anal_cursorX.x2)).argmin()
        if ind2 < ind1:
            temp = ind2
            ind1 = ind2
            ind2 = temp

        if 'y' in args[0]:
            ret_val['y'] = args[0]['y']
            means = np.nanmean(args[0]['data'][:, ind1:(ind2+1)], axis=1)
            ret_val['data'] = (args[0]['data'].T - means).T
        else:
            means = np.nanmean(args[0]['data'][ind1:(ind2+1)])
            ret_val['data'] = args[0]['data'] - means
        return (ret_val, )

class PP_DivRegX(PostProcessors):
    def get_description(self):
        return "Performs a line-by-line division of every line by the average value over a selected x-interval on said line."

    def get_input_args(self):
        return [('Input dataset', 'data'), ('X-interval', 'cursor', 'X-Region')]

    def get_output_args(self):
        return [('Filtered data', 'data', 'filtData')]

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']
        
        anal_cursorX = args[1]
        ind1 = (np.abs(ret_val['x'] - anal_cursorX.x1)).argmin()
        ind2 = (np.abs(ret_val['x'] - anal_cursorX.x2)).argmin()
        if ind2 < ind1:
            temp = ind2
            ind1 = ind2
            ind2 = temp

        if 'y' in args[0]:
            ret_val['y'] = args[0]['y']
            means = np.nanmean(args[0]['data'][:, ind1:(ind2+1)], axis=1)
            ret_val['data'] = (args[0]['data'].T / means).T
        else:
            means = np.nanmean(args[0]['data'][ind1:(ind2+1)])
            ret_val['data'] = args[0]['data'] / means
        return (ret_val, )

class PP_SubRegY(PostProcessors):
    def get_description(self):
        return "Performs a line-by-line subtraction of every line by the average value over a selected x-interval on said line."

    def get_input_args(self):
        return [('Input dataset', 'data'), ('Y-interval', 'cursor', 'Y-Region')]

    def get_output_args(self):
        return [('Filtered data', 'data', 'filtData')]

    def supports_1D(self):
        return False

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']
        ret_val['y'] = args[0]['y']
        
        anal_cursorY = args[1]
        ind1 = (np.abs(ret_val['y'] - anal_cursorY.y1)).argmin()
        ind2 = (np.abs(ret_val['y'] - anal_cursorY.y2)).argmin()
        if ind2 < ind1:
            temp = ind2
            ind1 = ind2
            ind2 = temp

        ret_val['y'] = args[0]['y']
        means = np.nanmean(args[0]['data'][ind1:(ind2+1),:],axis=0)
        ret_val['data'] = args[0]['data'] - means
        return (ret_val, )

class PP_Difference(PostProcessors):
    def get_description(self):
        return "Returns the difference of the two data"

    def get_input_args(self):
        return [('input1', 'data'), ('input2', 'data')]

    def get_output_args(self):
        return [('Difference', 'data', 'diff')]

    def __call__(self, *args):
        assert args[0]['data'].shape == args[1]['data'].shape, "Data has inconsistent shapes"
        
        ret_val_diff = {}
        assert np.array_equal(args[0]['x'], args[1]['x']), "The x-values are not concurrent for I and Q."
        ret_val_diff['x'] = args[0]['x']
        
        if len(args[0]['data'].shape) == 2:
            assert np.array_equal(args[0]['y'], args[1]['y']), "The y-values are not concurrent for I and Q."
            ret_val_diff['y'] = args[0]['y']
        
        ret_val_diff['data'] = args[0]['data'] - args[1]['data']

        return (ret_val_diff, )