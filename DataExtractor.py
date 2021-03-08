
class DataExtractor:
    def __init__(self, data_thread_pool):
        self.data_thread_pool = data_thread_pool
    
    def fetch_data(self, dict_params):
        self.async_result = self.data_thread_pool.apply_async(self._get_current_data, (dict_params,)) # tuple of args

    def data_ready(self):
        return self.async_result.ready()

    def get_data(self):
        while not self.async_result.ready():
            pass
        return self.async_result.get()

    def _get_current_data(self, params):
        raise NotImplementedError()

    def get_independent_vars(self):
        raise NotImplementedError()