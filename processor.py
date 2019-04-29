

class ImageProcessor(object):

    def __init__(self, file, output):
        self._heading = bytearray()
        self._file = file
        self._output = output
        self._chunk_ordering_list = []
        self._chunk_hist = {}
        self._data = bytearray(b'')
        self._pixel_size = 0

        self._validate()
        self._analyze()

    def get_metadata(self):
        pass

    def _validate(self):
        pass

    def _analyze(self):
        pass


