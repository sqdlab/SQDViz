from PostProcessors import PostProcessor

class PostProcessIQ2AP(PostProcessors):
    def __init__(self):
        pass

    def get_input_requests(self):
        return [
            {name: "I-channel", type: 'channel'}, {name: "Q-channel", type: 'channel'}
        ]
    
    def set_input_requests(self, variable_index):
        raise NotImplementedError()
    
    def get_output_names(self):
        raise NotImplementedError()

    def get_processed_data(self, data_sets):
        raise NotImplementedError()

    def get_description(self):
        raise NotImplementedError()
