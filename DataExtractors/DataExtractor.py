
class DataExtractor:
    def __init__(self, data_thread_pool):
        self.data_thread_pool = data_thread_pool
        self.isFetching = False
        self.async_result = None
    
    def fetch_data(self, dict_params):
        self.isFetching = True
        self.async_result = self.data_thread_pool.apply_async(self._get_current_data, (dict_params,)) # tuple of args

    def data_ready(self):
        if self.async_result:
            return self.async_result.ready()
        else:
            return False

    def get_data(self):
        while not self.async_result.ready():
            pass
        self.isFetching = False
        ret_val = self.async_result.get()
        self.async_result = None
        return ret_val
    
    def close_file(self):
        return
        raise NotImplementedError()

    def _get_current_data(self, params):
        raise NotImplementedError()

    def get_independent_vars(self):
        raise NotImplementedError()

    def get_dependent_vars(self):
        raise NotImplementedError()
