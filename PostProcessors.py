import enum
import sys, inspect
import numpy as np
import scipy
import scipy.ndimage
import scipy.sparse
import scipy.sparse.linalg
import scipy.signal

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
        assert args[0]['data'].shape == args[1]['data'].shape, "Datasets have inconsistent shapes"
        
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
        return "Performs a line-by-line subtraction of every horizontal line by the average value over a selected x-interval on said line."

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
            temp = ind1
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

class PP_SubRegY(PostProcessors):
    def get_description(self):
        return "Performs a line-by-line subtraction of every vertical line by the average value over a selected y-interval on said line."

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
            temp = ind1
            ind1 = ind2
            ind2 = temp

        ret_val['y'] = args[0]['y']
        means = np.nanmean(args[0]['data'][ind1:(ind2+1),:],axis=0)
        ret_val['data'] = args[0]['data'] - means
        return (ret_val, )

class PP_SubBackRegFiltY(PostProcessors):
    def get_description(self):
        return "Given a y-interval, the average horizontal line is found. Then this line is median-filtered (odd window size) across the x-axis. Then this line is subtracted from every horizontal line."

    def get_input_args(self):
        return [('Input dataset', 'data'), ('Y-interval', 'cursor', 'Y-Region'), ('Filt. Win. Size', 'int', 5)]

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
            temp = ind1
            ind1 = ind2
            ind2 = temp

        ret_val['y'] = args[0]['y']
        means = np.nanmean(args[0]['data'][ind1:(ind2+1),:],axis=0)
        means = scipy.signal.medfilt(means, args[2])
        ret_val['data'] = args[0]['data'] - means
        return (ret_val, )

class PP_SubRegMedianY(PostProcessors):
    def get_description(self):
        return "Performs a line-by-line subtraction of every vertical line by the median value over a selected y-interval on said line."

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
            temp = ind1
            ind1 = ind2
            ind2 = temp

        ret_val['y'] = args[0]['y']
        medians = np.nanmedian(args[0]['data'][ind1:(ind2+1),:],axis=0)
        ret_val['data'] = args[0]['data'] - medians
        return (ret_val, )

class PP_DivRegX(PostProcessors):
    def get_description(self):
        return "Performs a line-by-line division of every horizontal line by the average value over a selected x-interval on said line."

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
            temp = ind1
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

class PP_DivRegY(PostProcessors):
    def get_description(self):
        return "Performs a line-by-line division of every vertical line by the average value over a selected y-interval on said line."

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
            temp = ind1
            ind1 = ind2
            ind2 = temp

        ret_val['y'] = args[0]['y']
        means = np.nanmean(args[0]['data'][ind1:(ind2+1),:],axis=0)
        ret_val['data'] = args[0]['data'] / means
        return (ret_val, )

class PP_Difference(PostProcessors):
    def get_description(self):
        return "Returns the difference between two datasets (input1 - input2)."

    def get_input_args(self):
        return [('Input 1', 'data'), ('Input 2', 'data')]

    def get_output_args(self):
        return [('Difference', 'data', 'diff')]

    def __call__(self, *args):
        assert args[0]['data'].shape == args[1]['data'].shape, "Datasets have inconsistent shapes"
        
        ret_val_diff = {}
        assert np.array_equal(args[0]['x'], args[1]['x']), "The x-values are not concurrent across both datasets."
        ret_val_diff['x'] = args[0]['x']
        
        if len(args[0]['data'].shape) == 2:
            assert np.array_equal(args[0]['y'], args[1]['y']), "The y-values are not concurrent across both datasets."
            ret_val_diff['y'] = args[0]['y']
        
        ret_val_diff['data'] = args[0]['data'] - args[1]['data']

        return (ret_val_diff, )

class PP_IgnoreReg(PostProcessors):
    def get_description(self):
        return "Ignores a selected region defined via an x or y interval. Y-intervals are ignored in 1D plots."

    def get_input_args(self):
        return [('Input dataset', 'data'), ('X/Y-interval', 'cursor', ['X-Region', 'Y-Region'])]

    def get_output_args(self):
        return [('Filtered data', 'data', 'filtData')]

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']
        ret_val['data'] = args[0]['data']
        
        if args[1].Type == 'X-Region':
            anal_cursorX = args[1]
            ind1 = (np.abs(ret_val['x'] - anal_cursorX.x1)).argmin()
            ind2 = (np.abs(ret_val['x'] - anal_cursorX.x2)).argmin()
            if ind2 < ind1:
                temp = ind1
                ind1 = ind2
                ind2 = temp

            if 'y' in args[0]:
                ret_val['y'] = args[0]['y']
                ret_val['data'][:, ind1:(ind2+1)] = np.nan
            else:
                ret_val['data'][ind1:(ind2+1)] = np.nan
            return (ret_val, )
        elif args[1].Type == 'Y-Region':
            if 'y' in args[0]:
                ret_val['y'] = args[0]['y']
                anal_cursorY = args[1]
                ind1 = (np.abs(ret_val['y'] - anal_cursorY.y1)).argmin()
                ind2 = (np.abs(ret_val['y'] - anal_cursorY.y2)).argmin()
                if ind2 < ind1:
                    temp = ind1
                    ind1 = ind2
                    ind2 = temp
                ret_val['y'] = args[0]['y']
                ret_val['data'] = args[0]['data']
                ret_val['data'][ind1:(ind2+1),:] = np.nan
            return (ret_val, )
        

class PP_Log(PostProcessors):
    def get_description(self):
        return "Returns the multiplier times Log (base 10) of data."

    def get_input_args(self):
        return [('Input', 'data'), ('Multiplier', 'float', 20)]

    def get_output_args(self):
        return [('Output', 'data', 'logData')]

    def __call__(self, *args):
        
        ret_val = {}
        ret_val['x'] = args[0]['x']

        if 'y' in args[0]:
            ret_val['y'] = args[0]['y']
        
        #Make any non-positive values NaN...
        temp_data = args[0]['data'][:]*1.0
        temp_data[temp_data <= 0] = np.nan
        ret_val['data'] = args[1]*np.log10(temp_data)

        return (ret_val, )

class PP_UnwrapPhase(PostProcessors):
    def get_description(self):
        return "Unwraps phase values (in radians)."

    def get_input_args(self):
        return [('Input dataset', 'data')]

    def get_output_args(self):
        return [('Unwrapped Phase', 'data', 'UnwrappedPhase')]

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']

        if 'y' in args[0]:
            ret_val['y'] = args[0]['y']
            ret_val['data'] = np.unwrap(args[0]['data'], axis=1)
        else:
            ret_val['data'] = np.unwrap(args[0]['data'])
        return (ret_val, )

class PP_DetrendX(PostProcessors):
    def get_description(self):
        return "For every horizontal line slice, a fitted nth order polynomial is subtracted."

    def get_input_args(self):
        return [('Input dataset', 'data'), ('Poly. Order', 'int', 1)]

    def get_output_args(self):
        return [('Detrended', 'data', 'DetrendX')]

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']

        if 'y' in args[0]:
            ret_val['y'] = args[0]['y']
            ret_val['data'] = args[0]['data']*1.0

            for m, cur_vals in enumerate(args[0]['data']):
                y_vals = cur_vals
                x_vals = np.arange(y_vals.size)

                #Remove NaNs...
                idx = np.isfinite(y_vals)
                x_vals = x_vals[idx]
                y_vals = y_vals[idx]

                if y_vals.size > 1:
                    p = np.poly1d(np.polyfit(x_vals, y_vals, args[1] ))
                    ret_val['data'][m] = args[0]['data'][m]
                    ret_val['data'][m][idx] -= p(np.arange(y_vals.size))
        else:
            y_vals = args[0]['data']
            x_vals = np.arange(y_vals.size)

            #Remove NaNs...
            idx = np.isfinite(y_vals)
            x_vals = x_vals[idx]
            y_vals = y_vals[idx]

            if y_vals.size > 0:
                p = np.poly1d(np.polyfit(x_vals, y_vals, args[1] ))
                ret_val['data'] = args[0]['data'] - p(np.arange(y_vals.size))
        return (ret_val, )

class PP_DerivX(PostProcessors):
    def get_description(self):
        return "Derivative across x-axis using a first order finite difference. Note: first point is a copy of the second point."

    def get_input_args(self):
        return [('Input dataset', 'data')]

    def get_output_args(self):
        return [('Deriv-X', 'data', 'DerivX')]

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']

        if 'y' in args[0]:
            ret_val['y'] = args[0]['y']
            ret_val['data'] = args[0]['data']*1.0

            derivX = (ret_val['data'][:,1:] - ret_val['data'][:,:-1]) / (ret_val['x'][1:] - ret_val['x'][:-1])
            ret_val['data'] = np.c_[derivX[:,0], derivX]
        else:
            ret_val['data'] = args[0]['data']*1.0

            derivX = (ret_val['data'][1:] - ret_val['data'][:-1]) / (ret_val['x'][1:] - ret_val['x'][:-1])
            ret_val['data'] = np.concatenate([[derivX[0]], derivX])
        return (ret_val, )

class PP_DerivY(PostProcessors):
    def get_description(self):
        return "Derivative across y-axis using a first order finite difference. Note: first bottom point is a copy of the second point. In addition, 1D plots simply perform a 1D x-derivative."

    def get_input_args(self):
        return [('Input dataset', 'data')]

    def get_output_args(self):
        return [('Deriv-Y', 'data', 'DerivY')]

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']

        if 'y' in args[0]:
            ret_val['y'] = args[0]['y']
            ret_val['data'] = args[0]['data']*1.0

            derivY = (ret_val['data'][1:,:] - ret_val['data'][:-1,:]).T / (ret_val['y'][1:] - ret_val['y'][:-1])
            derivY = derivY.T
            ret_val['data'] = np.r_[[derivY[0,:]], derivY]
        else:
            ret_val['data'] = args[0]['data']*1.0

            derivY = (ret_val['data'][1:] - ret_val['data'][:-1]) / (ret_val['x'][1:] - ret_val['x'][:-1])
            ret_val['data'] = np.concatenate([[derivY[0]], derivY])
        return (ret_val, )

# class PP_SubSplineX(PostProcessors):
#     def get_description(self):
#         return "For every horizontal line, a smoothed spline is fit (Filtered Data) and then subtracted from the data (Subtracted Data) to effectively remove its background."

#     def get_input_args(self):
#         return [('Input dataset', 'data')]

#     def get_output_args(self):
#         return [('Filtered Data', 'data', 'filtData'), ('Subtracted Data', 'data', 'subData')]

#     def __call__(self, *args):
#         ret_val = {}
#         ret_val['x'] = args[0]['x']

#         #https://stackoverflow.com/questions/29156532/python-baseline-correction-library
#         def baseline_als(y, lam, p, niter=10):
#             L = len(y)
#             D = scipy.sparse.csc_matrix(np.diff(np.eye(L), 2))
#             w = np.ones(L)
#             for m in range(niter):
#                 W = scipy.sparse.spdiags(w, 0, L, L)
#                 Z = W + lam * D.dot(D.transpose())
#                 z = scipy.sparse.linalg.spsolve(Z, w*y)
#                 w = p * (y > z) + (1-p) * (y < z)
#             return z

#         if 'y' in args[0]:
#             ret_val['y'] = args[0]['y']
#             ret_val['data'] = args[0]['data']*0.0

#             for m, cur_line in enumerate(args[0]['data']):
#                 ret_val['data'][m] = baseline_als(cur_line, 100, 0.05)
#         else:
#             ret_val['data'] = baseline_als(args[0]['data'], 100, 0.05)
#         return (ret_val, ret_val)

class PP_SubMedianX(PostProcessors):
    def get_description(self):
        return "For every horizontal line, a median filter is applied (Filtered Data) and then subtracted from the data (Subtracted Data) to effectively remove its background."

    def get_input_args(self):
        return [('Input dataset', 'data'), ('Window size', 'int', 3)]

    def get_output_args(self):
        return [('Filtered Data', 'data', 'filtData'), ('Subtracted Data', 'data', 'subData')]

    def __call__(self, *args):
        ret_val = {}
        ret_val['x'] = args[0]['x']
        ret_val_sub = {}
        ret_val_sub['x'] = args[0]['x']

        if 'y' in args[0]:
            ret_val['y'] = args[0]['y']
            ret_val_sub['y'] = args[0]['y']
            ret_val['data'] = scipy.ndimage.median_filter(args[0]['data'], size=(1, args[1]))
        else:
            ret_val['data'] = scipy.ndimage.median_filter(args[0]['data'], size=(args[1]))
        ret_val_sub['data'] = args[0]['data'] - ret_val['data']
        return (ret_val, ret_val_sub)
