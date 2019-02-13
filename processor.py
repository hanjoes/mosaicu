class ImageProcessor(object):

    def __init__(self, file):
        self._file = file
        self._detection()

    def spit_meta(self):
        pass

    def _detection(self):
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

    def spit_meta(self):
        with open(self._file, 'rb') as pic_f:
            self._walk_chunks(pic_f)

    @staticmethod
    def _walk_chunks(pic_f):
        # skipping the first 8 bytes for header
        pic_f.seek(8)

        while True:
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
            type = chunk_type.decode('utf-8')
            # Chunk Data
            # The data bytes appropriate to the chunk type, if any.  This
            # field can be of zero length.
            pic_f.seek(length, 1)
            # CRC
            # A 4-byte CRC (Cyclic Redundancy Check) calculated on the
            # preceding bytes in the chunk, including the chunk type code and
            # chunk data fields, but not including the length field. The CRC
            # is always present, even for chunks containing no data.  See CRC
            # algorithm (Section 3.4).
            crc = pic_f.read(4)

            if type == "IEND":
                break

    def _detection(self):
        with open(self._file, 'rb') as pic_f:
            b = pic_f.read(8)
            if len(b) != 8 or b != b'\x89PNG\r\n\x1a\n':
                raise IOError(f'Input file: {self._file} does not conform to PNG heading.')

