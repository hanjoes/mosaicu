import binascii
import math
import zlib


class ImageProcessor(object):

    def __init__(self, file, output):
        self._headding = bytearray()
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


def _write_idat(updated_data):
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

    # Default size for a IDAT chunk.
    IDAT_CHUNK_SIZE = 9999999999

    # At present, only filter method 0 (adaptive
    # filtering with five basic filter types) is defined.
    # PNG filter method 0 defines five basic filter types:
    FILTER_TYPE_LOOKUP = {
        0: "None",
        1: "Sub",
        2: "Up",
        3: "Average",
        4: "Paeth"
    }

    # Color type determines number samples for each pixel
    # Color    Allowed    Interpretation
    # Type     Bit Depths
    #
    # 0       1,2,4,8,16  Each pixel is a grayscale sample.
    #
    # 2       8,16        Each pixel is an R,G,B triple.
    #
    # 3       1,2,4,8     Each pixel is a palette index;
    #                     a PLTE chunk must appear.
    #
    # 4       8,16        Each pixel is a grayscale sample,
    #                     followed by an alpha sample.
    #
    # 6       8,16        Each pixel is an R,G,B triple,
    #                     followed by an alpha sample.
    COLOR_TYPE_TO_NUM_SAMPLE = {
        0: 1,
        2: 3,
        3: 1,
        4: 2,
        6: 4
    }

    @staticmethod
    def _noop_filter(current, previous, bpp):
        return current

    @staticmethod
    def _noop_reverse_filter(current, previous, bpp):
        return current

    @staticmethod
    def _sub_filter(current, previous, bpp):
        """
        To compute the Sub filter, apply the following formula to each
        byte of the scanline:

        Copy the scanline as we are computing difference between "Raw" bytes.

        Sub(x) = Raw(x) - Raw(x-bpp)

        :param current: byte array representing current scanline.
        :param previous: byte array representing the previous scanline (not used by this filter type)
        :param bpp: bytes per pixel
        :return: filtered byte array
        """
        result = bytearray(len(current))
        for x in range(len(current)):
            if x == 0:
                result[0] = 1
                if current[0] != 1:
                    raise IOError(f'{current[0]} passed to Sub filter')
                continue

            result[x] = (current[x] - (current[x - bpp] if x - bpp > 0 else 0)) % 256
        return result

    @staticmethod
    def _sub_reverse_filter(current, previous, bpp):
        """
        To reverse the effect of the Sub filter after decompression,
        output the following value:

        No need to copy as we are calculating Sub plus Raw and Raw is calculated on the fly.

        Sub(x) + Raw(x-bpp)

        :param current: byte array representing current scanline.
        :param previous: byte array representing the previous scanline (not used by this filter type)
        :param bpp: bytes per pixel
        :return: reverse-filtered byte array
        """
        for x in range(len(current)):
            if x == 0:
                if current[0] != 1:
                    raise IOError(f'{current[0]} passed to Sub reverse filter')
                continue

            current[x] = (current[x] + (current[x - bpp] if x - bpp > 0 else 0)) % 256
        return current

    @staticmethod
    def _up_filter(current, previous, bpp):
        """
        To compute the Up filter, apply the following formula to each byte
        of the scanline:

        Up(x) = Raw(x) - Prior(x)

        :param current: byte array representing current scanline.
        :param previous: byte array representing the previous scanline (not used by this filter type)
        :param bpp: bytes per pixel
        :return: filtered byte array
        """
        result = bytearray(len(current))
        for x in range(len(current)):
            if x == 0:
                result[0] = 2
                if current[0] != 2:
                    raise IOError(f'{current[0]} passed to Up filter')
                continue

            result[x] = (current[x] - previous[x] if previous else 0) % 256
        return result

    @staticmethod
    def _up_reverse_filter(current, previous, bpp):
        """
        To reverse the effect of the Up filter after decompression, output
        the following value:

        Up(x) + Prior(x)

        :param current: byte array representing current scanline.
        :param previous: byte array representing the previous scanline (not used by this filter type)
        :param bpp: bytes per pixel
        :return: reverse-filtered byte array
        """
        for x in range(len(current)):
            if x == 0:
                if current[0] != 2:
                    raise IOError(f'{current[0]} passed to Up reverse filter')
                continue

            current[x] = (current[x] + (previous[x] if previous else 0)) % 256
        return current

    @staticmethod
    def _avg_filter(current, previous, bpp):
        """
        To compute the Average filter, apply the following formula to each
        byte of the scanline:

        Average(x) = Raw(x) - floor((Raw(x-bpp)+Prior(x))/2)

        :param current: byte array representing current scanline.
        :param previous: byte array representing the previous scanline (not used by this filter type)
        :param bpp: bytes per pixel
        :return: filtered byte array
        """
        result = bytearray(len(current))
        for x in range(len(current)):
            if x == 0:
                result[0] = 3
                if current[0] != 3:
                    raise IOError(f'{current[0]} passed to Avg filter')
                continue

            prior = previous[x] if previous else 0
            raw = current[x - bpp] if x - bpp > 0 else 0
            result[x] = (current[x] - math.floor((raw + prior) / 2)) % 256
        return result

    @staticmethod
    def _avg_reverse_filter(current, previous, bpp):
        """
        To reverse the effect of the Average filter after decompression,
        output the following value:

        Average(x) + floor((Raw(x-bpp)+Prior(x))/2)

        :param current: byte array representing current scanline.
        :param previous: byte array representing the previous scanline (not used by this filter type)
        :param bpp: bytes per pixel
        :return: reverse-filtered byte array
        """
        for x in range(len(current)):
            if x == 0:
                if current[0] != 3:
                    raise IOError(f'{current[0]} passed to Avg reverse filter')
                continue

            prior = previous[x] if previous else 0
            raw = current[x - bpp] if x - bpp > 0 else 0
            current[x] = (current[x] + math.floor((raw + prior) / 2)) % 256
        return current

    @staticmethod
    def _paeth_predictor(a, b, c):
        p = a + b - c
        pa = abs(p - a)
        pb = abs(p - b)
        pc = abs(p - c)

        if pa <= pb and pa <= pc:
            return a
        elif pb <= pc:
            return b
        else:
            return c

    @staticmethod
    def _paeth_filter(current, previous, bpp):
        result = bytearray(len(current))
        for x in range(len(current)):
            if x == 0:
                result[0] = 4
                if current[0] != 4:
                    raise IOError(f'{current[0]} passed to Paeth filter')
                continue

            left = current[x - bpp] if x - bpp > 0 else 0
            above = previous[x] if previous else 0
            upper_left = previous[x - bpp] if x - bpp > 0 and previous else 0
            result[x] = (current[x] - PNGProcessor._paeth_predictor(left, above, upper_left)) % 256
        return result

    @staticmethod
    def _paeth_reverse_filter(current, previous, bpp):
        for x in range(len(current)):
            if x == 0:
                if current[0] != 4:
                    raise IOError(f'{current[0]} passed to Paeth reverse filter')
                continue

            left = current[x - bpp] if x - bpp > 0 else 0
            above = previous[x] if previous else 0
            upper_left = previous[x - bpp] if x - bpp > 0 and previous else 0
            current[x] = (current[x] + PNGProcessor._paeth_predictor(left, above, upper_left)) % 256
        return current

    # PNG filter method 0 defines five basic filter types:
    #
    # Type    Name
    #
    # 0       None
    # 1       Sub
    # 2       Up
    # 3       Average
    # 4       Paeth
    FILTER_TYPE_TO_FUNC = {
        0: (_noop_filter.__func__, _noop_reverse_filter.__func__),
        1: (_sub_filter.__func__, _sub_reverse_filter.__func__),
        2: (_up_filter.__func__, _up_reverse_filter.__func__),
        3: (_avg_filter.__func__, _avg_reverse_filter.__func__),
        4: (_paeth_filter.__func__, _paeth_reverse_filter.__func__)
    }

    # Bit depth restrictions for each color type are imposed to
    # simplify implementations and to prohibit combinations that do
    # not compress well.  Decoders must support all legal
    # combinations of bit depth and color type.  The allowed
    # combinations are:
    #
    #    Color    Allowed    Interpretation
    #    Type    Bit Depths
    #
    #    0       1,2,4,8,16  Each pixel is a grayscale sample.
    #
    #    2       8,16        Each pixel is an R,G,B triple.
    #
    #    3       1,2,4,8     Each pixel is a palette index;
    #                        a PLTE chunk must appear.
    #
    #    4       8,16        Each pixel is a grayscale sample,
    #                        followed by an alpha sample.
    #
    #    6       8,16        Each pixel is an R,G,B triple,
    #                        followed by an alpha sample.
    SAMPLE_NUM_LOOKUP = {
        0: 1,
        2: 3,
        3: 1,
        4: 2,
        6: 4
    }

    def _chunk_hist_str_ordered(self):
        result_list = []
        for chunk_name in self._chunk_ordering_list:
            result_list.append(f'{chunk_name}:{self._chunk_hist[chunk_name]["count"]}')
        return ','.join(result_list)

    def _walk_chunks(self, pic_f):
        # skipping the first 8 bytes for header
        self._heading = pic_f.read(8)

        while True:
            raw_data, length, chunk_type, chunk_data, crc = self._read_one_chunk(pic_f)

            if chunk_type == 'IHDR':
                self._analyze_header(chunk_data, length)
            elif chunk_type == 'IDAT':
                # print(f'reading chunk_length = {length}')
                self._data.extend(chunk_data)

            if chunk_type in self._chunk_hist:
                self._chunk_hist[chunk_type]['count'] += 1
            else:
                self._chunk_ordering_list.append(chunk_type)
                self._chunk_hist[chunk_type] = {'raw': raw_data, 'count': 1}

            if chunk_type == 'IEND':
                break

        print(f'{"chunk hist:":20}{self._chunk_hist_str_ordered()}')

        # Deflate-compressed datastreams within PNG are stored in the "zlib"
        # format, which has the structure:
        #
        # Compression method/flags code: 1 byte
        # Additional flags/check bits:   1 byte
        # Compressed data blocks:        n bytes
        # Check value:                   4 bytes
        method_flag = self._data[0]
        additional = self._data[1]
        check = self._data[-4]
        decompressed = zlib.decompress(self._data, wbits=0)
        print(f'{"compression spec:":20}'
              f'method/flag:{method_flag},',
              f'additional:{additional},'
              f'check:{check},'
              f'before deflation:{len(self._data)} bytes,'
              f'after deflation:{len(decompressed)} bytes')

        # Handle scanlines
        # given each scanline is prepended with 1 byte of the filter
        # method before compressing, number of bytes each scanline for
        # the image itself is really:
        #
        # len(decompressed)/height - 1
        #
        # which is equal to:
        #
        # width * number of samples per pixel * bit depth / 8
        bpp = int(self._pixel_size / 8)
        _updated_image = bytearray()
        scanline_len = int(len(decompressed) / self._height)

        # reverse filter scanlines
        previous_line = None
        for i in range(self._height):
            scanline_copy = bytearray(scanline_len)
            scanline_copy[:] = decompressed[i * scanline_len:(i + 1) * scanline_len]
            filter_type = scanline_copy[0]
            scanline_copy = PNGProcessor.FILTER_TYPE_TO_FUNC[filter_type][1](scanline_copy, previous_line, bpp)
            _updated_image.extend(scanline_copy)
            previous_line = scanline_copy

        # filter updated scanlines
        _filtered_image = bytearray()
        for i in range(self._height):
            if i == 0:
                previous_line = None

            _updated_scanline = bytearray(scanline_len)
            _updated_scanline[:] = _updated_image[i * scanline_len:(i + 1) * scanline_len]
            filter_type = _updated_scanline[0]
            previous_line_cache = _updated_scanline
            _updated_scanline = PNGProcessor.FILTER_TYPE_TO_FUNC[filter_type][0](_updated_scanline, previous_line, bpp)
            _filtered_image.extend(_updated_scanline)
            previous_line = previous_line_cache

        if _filtered_image != decompressed:
            for i in range(self._height):
                current_decompressed_row = decompressed[i * scanline_len:(i + 1) * scanline_len]
                _current_updated_row = _filtered_image[i * scanline_len:(i + 1) * scanline_len]
                if current_decompressed_row != _current_updated_row:
                    raise ArithmeticError(f'filtering error happened in row: {i} with filter type '
                                          f'{current_decompressed_row[0]}')

        # compress updated image, the compress method with default parameters seem to work well for PNG standard
        compressed = zlib.compress(_filtered_image)

        self._rebuild_image(compressed)

    def _rebuild_image(self, updated_data):
        with open(self._output, 'wb') as of:
            of.write(self._heading)
            for chunk_name in self._chunk_ordering_list:
                chunk = self._chunk_hist[chunk_name]
                raw = chunk['raw']
                if chunk_name != 'IDAT':
                    of.write(raw)
                else:
                    PNGProcessor._write_idat(of, updated_data)

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
        self._pixel_size = self.COLOR_TYPE_TO_NUM_SAMPLE[self._color_type] * self._bit_depth
        print(f'{"basic spec:":20}'
              f'width:{self._width},'
              f'height:{self._height},'
              f'bit_depth:{self._bit_depth},'
              f'color_type:{self._color_type},'
              f'pixel_size(bit):{self._pixel_size},'
              f'compression:{self._compression_method},'
              f'filter:{PNGProcessor.FILTER_TYPE_LOOKUP[self._filter_method]},'
              f'interlace:{self._interlace_method}')
        self._calculate_pixel_size()

    def _calculate_pixel_size(self):
        sample_count = PNGProcessor.SAMPLE_NUM_LOOKUP[self._color_type]
        return sample_count * self._bit_depth / 8

    @staticmethod
    def _read_one_chunk(pic_f):
        raw_data = bytearray()
        # Length
        # A 4-byte unsigned integer giving the number of bytes in the
        # chunk's data field. The length counts only the data field, not
        # itself, the chunk type code, or the CRC.  Zero is a valid
        # length.  Although encoders and decoders should treat the length
        # as unsigned, its value must not exceed (2^31)-1 bytes.
        chunk_length = pic_f.read(4)
        raw_data.extend(chunk_length)
        length = int.from_bytes(chunk_length, 'big')
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
        raw_data.extend(chunk_type)
        chunk_type_str = chunk_type.decode('utf-8')
        # Chunk Data
        # The data bytes appropriate to the chunk type, if any.  This
        # field can be of zero length.
        chunk_data = pic_f.read(length)
        raw_data.extend(chunk_data)
        # CRC
        # A 4-byte CRC (Cyclic Redundancy Check) calculated on the
        # preceding bytes in the chunk, including the chunk type code and
        # chunk data fields, but not including the length field. The CRC
        # is always present, even for chunks containing no data.  See CRC
        # algorithm (Section 3.4).
        crc = pic_f.read(4)
        raw_data.extend(crc)

        return raw_data, length, chunk_type_str, chunk_data, crc

    @staticmethod
    def _write_idat(of, updated_data):
        leftover_data = updated_data
        end = False
        # There can be multiple IDAT chunks; if so, they must appear
        # consecutively with no other intervening chunks.  The compressed
        # datastream is then the concatenation of the contents of all the
        # IDAT chunks.  The encoder can divide the compressed datastream
        # into IDAT chunks however it wishes.  (Multiple IDAT chunks are
        # allowed so that encoders can work in a fixed amount of memory;
        # typically the chunk size will correspond to the encoder's
        # buffer size.) It is important to emphasize that IDAT chunk
        # boundaries have no semantic significance and can occur at any
        # point in the compressed datastream.  A PNG file in which each
        # IDAT chunk contains only one data byte is legal, though
        # remarkably wasteful of space.  (For that matter, zero-length
        # IDAT chunks are legal, though even more wasteful.)
        while not end:
            if len(leftover_data) > PNGProcessor.IDAT_CHUNK_SIZE:
                current_chunk = leftover_data[0:PNGProcessor.IDAT_CHUNK_SIZE]
                leftover_data = leftover_data[PNGProcessor.IDAT_CHUNK_SIZE:]
            else:
                current_chunk = leftover_data
                end = True

            # print(binascii.hexlify(current_chunk)[0:100])

            chunk_length = len(current_chunk).to_bytes(4, 'big')
            # print(f'chunk_length: {len(current_chunk)}')
            # print(len(current_chunk))
            # print(f'chunk_length: {chunk_length}')
            chunk_type = bytearray('IDAT', 'utf-8')
            chunk_data = current_chunk
            crc = zlib.crc32(current_chunk).to_bytes(4, 'big')
            # crc = CRC32().calculate(current_chunk).to_bytes(4, 'big')
            of.write(chunk_length + chunk_type + chunk_data + crc)

