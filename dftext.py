""" DF compressed text file manipulation """

import argparse, struct, sys, zlib

class CompatError(Exception): pass
class ParserError(Exception): pass
class ParserDecodeError(Exception): pass

PY_VERSION = sys.version_info[0]
if PY_VERSION != 2:
    raise CompatError('Python %i not supported' % PY_VERSION)
class ArgParser:
    def __init__(self):
        self.arg_parser = argparse.ArgumentParser()
        self.arg_parser.add_argument('filename',
            help='Filename to read from (defaults to stdin)',
            nargs='?',
            default=None,
        )
        self.arg_parser.add_argument('--index',
            help='Use data/index-style encryption',
            action='store_true',
        )
        self.arg_parser.add_argument('--level',
            help='Compression level (0-9, with 0 being the lowest)',
            type=int,
            default=zlib.Z_DEFAULT_COMPRESSION,
        )
        self.arg_parser.add_argument('--debug',
            help='Enable debug output',
            action='store_true',
        )
    def parse_args(self):
        return self.arg_parser.parse_args()

class Parser:
    def read_file(self, file):
        if file is None:
            file = sys.stdin
        elif isinstance(file, str):
            file = open(file)
        return file.read()

    def index_scramble(self, text):
        text = list(text)
        for i, ch in enumerate(text):
            text[i] = chr(255 - (i % 5) - ord(ch))
        return ''.join(text)

    def decode(self, in_text, index=False):
        decompressed = ''
        chunk_id = 1
        while in_text:
            try:
                chunk_length = struct.unpack('<L', in_text[:4])[0]
            except struct.error:
                raise ParserDecodeError('Could not determine chunk length')
            end = chunk_length + 4
            try:
                decompressed += zlib.decompress(in_text[4:end])
            except zlib.error:
                raise ParserDecodeError('Could not decompress chunk %i' % chunk_id)
            in_text = in_text[end:]
            chunk_id += 1
        try:
            record_count, decompressed = \
                    struct.unpack('<L', decompressed[:4])[0], decompressed[4:]
        except struct.error:
            raise ParserDecodeError('Could not determine record count')
        records = []
        for record_id in range(record_count):
            record_length, record_length_2 = \
                    struct.unpack('<LH', decompressed[:6])
            decompressed = decompressed[6:]
            if record_length != record_length_2:
                raise ParserDecodeError('Record lengths do not match')
            record, decompressed = decompressed[:record_length], decompressed[record_length:]
            if index:
                record = self.index_scramble(record)
            records.append(record)
        return '\n'.join(records) + '\n'

    def decode_file(self, in_file, *args, **kwargs):
        return self.decode(self.read_file(in_file), *args, **kwargs)

    def encode(self, in_text, index=False, level=zlib.Z_DEFAULT_COMPRESSION):
        records = in_text.rstrip('\n').split('\n')
        out_text = ''.join([struct.pack('<LH', len(record), len(record))
                            + (self.index_scramble(record) if index else record)
                            for record in records])
        out_text = struct.pack('<L', len(records)) + out_text
        out_text = zlib.compress(out_text, level)
        out_text = struct.pack('<L', len(out_text)) + out_text
        return out_text

    def encode_file(self, in_file, *args, **kwargs):
        return self.encode(self.read_file(in_file), *args, **kwargs)
