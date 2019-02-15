import zlib

class ImageProcessor(object):

    def __init__(self, file):
        self._file = file
        self._chunk_hist = {}
        self._data = bytearray(b'')

        self._validate()
        self._analyze()

    def get_metadata(self):
        pass

    def _validate(self):
        pass

    def _analyze(self):
        pass


class PNGProcessor(ImageProcessor):
    """
    Reference: https://tools.ietf.org/html/rfc2083#section-3

    The first eight bytes of a PNG file always contain the following
    values:

        (decimal)              137  80  78  71  13  10  26  10
        (hexadecimal)           89  50  4e  47  0d  0a  1a  0a
        (ASCII C notation)    \211   P   N   G  \r  \n \032 \n

    This signature both identifies the file as a PNG file and provides
    for immediate detection of common file-transfer problems.  The
    first two bytes distinguish PNG files on systems that expect the
    first two bytes to identify the file type uniquely.  The first
    byte is chosen as a non-ASCII value to reduce the probability that
    a text file may be misrecognized as a PNG file; also, it catches
    bad file transfers that clear bit 7.  Bytes two through four name
    the format.  The CR-LF sequence catches bad file transfers that
    alter newline sequences.  The control-Z character stops file
    display under MS-DOS.  The final line feed checks for the inverse
    of the CR-LF translation problem.
    """

    def get_metadata(self):
        print(self._chunk_hist)

    def _walk_chunks(self, pic_f):
        # skipping the first 8 bytes for header
        pic_f.seek(8)

        while True:
            length, chunk_type, chunk_data, crc = self._read_one_chunk(pic_f)

            if chunk_type == 'IHDR':
                self._analyze_header(chunk_data, length)

            if chunk_type == 'IDAT':
                self._data.extend(chunk_data)

            if chunk_type in self._chunk_hist:
                self._chunk_hist[type] += 1
            else:
                self._chunk_hist[type] = 1

            if chunk_type == 'IEND':
                break

        # Deflate-compressed datastreams within PNG are stored in the "zlib"
        # format, which has the structure:
        #
        # Compression method/flags code: 1 byte
        # Additional flags/check bits:   1 byte
        # Compressed data blocks:        n bytes
        # Check value:                   4 bytes
        method_flag = self._data[0]
        print(f'method/flag {method_flag}')
        additional = self._data[1]
        print(f'additional {additional}')
        data = self._data[2:-4]
        print(f'length: {len(data)}')
        check = self._data[-3]
        print(f'check: {check}')
        # zlib.decompress()


    def _validate(self):
        with open(self._file, 'rb') as pic_f:
            b = pic_f.read(8)
            if len(b) != 8 or b != b'\x89PNG\r\n\x1a\n':
                raise IOError(f'Input file: {self._file} does not conform to PNG heading.')

    def _analyze(self):
        with open(self._file, 'rb') as pic_f:
            self._walk_chunks(pic_f)

    def _analyze_header(self, header_bytes, length):
        # The IHDR chunk must appear FIRST.  It contains:
        #
        # Width:              4 bytes
        self._width = 0
        # Height:             4 bytes
        self._height = 0
        # Bit depth:          1 byte
        self._bit_depth = 0
        # Color type:         1 byte (1 is not a valid value)
        self._color_type = 1
        # Compression method: 1 byte (only 0 is a valid value)
        self._compression_method = 0
        # Filter method:      1 byte (only 0 is a valid value)
        self._filter_method = 0
        # Interlace method:   1 byte (0 or 1 are valid values)
        self._interlace_method = -1

        if length != 13:
            raise IOError(f'IHDR chunk must be 13 bytes, {length} found.')

        self._width = int.from_bytes(header_bytes[0:4], 'big')
        self._height = int.from_bytes(header_bytes[4:8], 'big')
        self._bit_depth = int.from_bytes(header_bytes[8:9], 'big')
        self._color_type = int.from_bytes(header_bytes[9:10], 'big')
        self._compression_method = int.from_bytes(header_bytes[10:11], 'big')
        self._filter_method = int.from_bytes(header_bytes[11:12], 'big')
        self._interlace_method = int.from_bytes(header_bytes[12:13], 'big')
        print(f'width:{self._width},'
              f'height:{self._height},'
              f'bit_depth:{self._bit_depth},'
              f'color_type:{self._color_type},'
              f'compression:{self._compression_method},'
              f'filter:{self._filter_method},'
              f'interlace:{self._interlace_method}')

    @staticmethod
    def _read_one_chunk(pic_f):
        # Length
        # A 4-byte unsigned integer giving the number of bytes in the
        # chunk's data field. The length counts only the data field, not
        # itself, the chunk type code, or the CRC.  Zero is a valid
        # length.  Although encoders and decoders should treat the length
        # as unsigned, its value must not exceed (2^31)-1 bytes.
        _chunk_length = pic_f.read(4)
        length = int.from_bytes(_chunk_length, 'big')
        # Chunk Type
        # A 4-byte chunk type code.  For convenience in description and
        # in examining PNG files, type codes are restricted to consist of
        # uppercase and lowercase ASCII letters (A-Z and a-z, or 65-90
        # and 97-122 decimal).  However, encoders and decoders must treat
        # the codes as fixed binary values, not character strings.  For
        # example, it would not be correct to represent the type code
        # IDAT by the EBCDIC equivalents of those letters.  Additional
        # naming conventions for chunk types are discussed in the next
        # section.
        chunk_type = pic_f.read(4)
        chunk_type_str = chunk_type.decode('utf-8')
        # Chunk Data
        # The data bytes appropriate to the chunk type, if any.  This
        # field can be of zero length.
        chunk_data = pic_f.read(length)
        # CRC
        # A 4-byte CRC (Cyclic Redundancy Check) calculated on the
        # preceding bytes in the chunk, including the chunk type code and
        # chunk data fields, but not including the length field. The CRC
        # is always present, even for chunks containing no data.  See CRC
        # algorithm (Section 3.4).
        crc = pic_f.read(4)

        return length, chunk_type_str, chunk_data, crc
